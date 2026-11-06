"""动态可配置PydanticAI-DAG工作流引擎

基于PydanticAI实现的无固定任务类型、全动态配置的AI多步骤DAG编排引擎。
通过 framework.agent.core.Agent 类统一实现大模型调用。

核心功能：
1. 任务识别：基于用户输入生成行动方案
2. 配置转换：将行动方案转换为DAG配置
3. 流程执行：执行DAG工作流并返回结果
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, List, Type, Optional

from pydantic import BaseModel, create_model, Field

from framework.agent.core import Agent
from framework.agent.prompt import TaskPrompts
from framework.core.config import config

logger = logging.getLogger(__name__)

_DYNAMIC_MODELS: Dict[str, Type[BaseModel]] = {}


class DagExecutionError(Exception):
    """DAG执行错误"""

    pass


class CircularDependencyError(Exception):
    """循环依赖错误"""

    pass


class DagNodeConfig(BaseModel):
    """DAG节点配置模型"""

    step_id: str = Field(..., description="节点唯一标识")
    schema_unique_id: str = Field(..., description="输出模型唯一标识")
    sys_prompt: str = Field(..., description="系统提示词")
    depends_on: List[str] = Field(
        default_factory=list, description="依赖的前置节点ID列表"
    )
    output_fields: Dict[str, List[Any]] = Field(..., description="输出字段定义")
    temp: float = Field(default=0.0, description="温度参数")
    retries: int = Field(default=2, description="重试次数")
    input_template: str = Field(default="{raw_text}", description="输入模板")


class TaskActionPlan(BaseModel):
    """任务行动方案数据模型"""

    @staticmethod
    def create_error_output(
        error_code: str, error_message: str, missing_params: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """创建错误输出"""
        return {
            "error_code": error_code,
            "error_message": error_message,
            "missing_params": missing_params or [],
        }

    @staticmethod
    def create_empty_plan() -> Dict[str, Any]:
        """创建空的行动方案模板"""
        return {
            "task_overview": {
                "total_tasks": 0,
                "priority_order": [],
                "global_dependency": None,
            },
            "task_details": [],
            "global_execution_flow": {
                "execution_mode": "全串行",
                "parallel_tasks": [],
                "data_flow": [],
            },
        }


class Flow:
    """统一的Flow工作流引擎类

    核心功能：
    1. 任务识别：基于用户输入生成行动方案
    2. 配置转换：将行动方案转换为DAG配置
    3. 流程执行：执行DAG工作流并返回结果

    通过 framework.agent.core.Agent 类实现大模型调用。
    """

    class _DagNode:
        """内部DAG节点类"""

        def __init__(
            self,
            config: DagNodeConfig,
            agent: Agent = None,
            tools: list = None,
            skills: list = None,
        ):
            self.step_id = config.step_id
            self.schema_unique_id = config.schema_unique_id
            self.sys_prompt = config.sys_prompt
            self.depends_on = config.depends_on
            self.output_fields = config.output_fields
            self.temp = config.temp
            self.retries = config.retries
            self.input_template = config.input_template

            self._agent: Optional[Agent] = agent
            self._tools = tools or []
            self._skills = skills or []
            self._output_model: Optional[Type[BaseModel]] = None

        def _build_output_model(self) -> Type[BaseModel]:
            """动态构建输出校验模型（带缓存）"""
            if self.schema_unique_id in _DYNAMIC_MODELS:
                self._output_model = _DYNAMIC_MODELS[self.schema_unique_id]
                return self._output_model

            fields = {}
            for field_name, field_spec in self.output_fields.items():
                if isinstance(field_spec, list) and len(field_spec) >= 1:
                    type_str = field_spec[0]
                    kwargs = field_spec[1] if len(field_spec) > 1 else {}
                    python_type = self._map_type(type_str)
                    fields[field_name] = (
                        python_type,
                        Field(description=kwargs.get("description", "")),
                    )

            model = create_model(f"DynamicModel_{self.schema_unique_id}", **fields)
            _DYNAMIC_MODELS[self.schema_unique_id] = model
            self._output_model = model
            return model

        def _initialize_agent(self):
            """使用Agent类初始化AI代理（优先使用传入的Agent，否则创建默认Agent）"""
            if self._agent is None:
                self._agent = Agent(
                    system_prompt=self.sys_prompt,
                    tools=self._tools,
                    skills=self._skills,
                )

        @staticmethod
        def _map_type(type_str: str) -> type:
            """类型字符串到Python类型的映射"""
            type_mapping = {
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list[str]": List[str],
                "list[int]": List[int],
                "list[float]": List[float],
                "list[bool]": List[bool],
                "dict": Dict[str, Any],
                "Any": Any,
            }
            return type_mapping.get(type_str, str)

        def _render_input(
            self, raw_text: str, upstream_results: Dict[str, Any], knowledge: str = ""
        ) -> str:
            """渲染输入模板"""
            rendered = self.input_template.replace("{raw_text}", raw_text)
            for step_id, result in upstream_results.items():
                rendered = rendered.replace(
                    f"{{prev.{step_id}}}", json.dumps(result, ensure_ascii=False)
                )
            if knowledge:
                rendered = rendered.replace("{knowledge}", knowledge)
            return rendered

        async def execute(
            self, raw_text: str, upstream_results: Dict[str, Any], knowledge: str = ""
        ) -> Dict[str, Any]:
            """执行节点（基础重试 + 输出验证）"""
            node_start = time.time()
            logger.info(f"[Flow][Node] ====== 开始执行节点: {self.step_id} ======")

            if not self._agent or not self._output_model:
                raise DagExecutionError(f"节点 {self.step_id} 未初始化")

            input_text = self._render_input(raw_text, upstream_results, knowledge)
            logger.info(
                f"[Flow][Node] {self.step_id} 渲染后输入: {input_text[:150]}{'...' if len(input_text) > 150 else ''}"
            )

            last_exception = None
            for attempt in range(self.retries + 1):
                try:
                    logger.info(
                        f"[Flow][Node] {self.step_id} 第{attempt+1}次调用AI模型"
                    )
                    chat_result = await self._agent.chat(
                        system_prompt=self.sys_prompt,
                        context=[],
                        user_prompt=input_text,
                        output_schema=self._output_model,
                        temperature=self.temp,
                        max_tokens=2000,
                    )
                    # 使用 chat_result.data 获取 PydanticAI 返回的结构化数据
                    parsed_data = chat_result.data
                    if parsed_data is None:
                        parsed_data = {"result": chat_result.content}
                    node_time = time.time() - node_start
                    output_preview = f"{str(parsed_data)[:150]}{'...' if len(str(parsed_data)) > 150 else ''}"
                    logger.info(
                        f"[Flow][Node] {self.step_id} 执行成功 | 耗时: {node_time:.2f}s | 输出: {output_preview}"
                    )
                    return parsed_data
                except Exception as e:
                    last_exception = e
                    if attempt < self.retries:
                        logger.warning(
                            f"[Flow][Node] {self.step_id} 第{attempt+1}次执行失败，0.5s后重试: {e}"
                        )
                        await asyncio.sleep(0.5)

            node_time = time.time() - node_start
            logger.error(
                f"[Flow][Node] {self.step_id} 执行失败, 耗时: {node_time:.2f}s"
            )
            raise DagExecutionError(f"节点 {self.step_id} 执行失败: {last_exception}")

    class _DagEngine:
        """内部DAG工作流引擎"""

        def __init__(
            self,
            flow_config: List[Dict[str, Any]],
            agent: Agent = None,
            tools: list = None,
            skills: list = None,
        ):
            self._flow_config = flow_config
            self._agent = agent
            self._tools = tools or []
            self._skills = skills or []
            self._nodes: Dict[str, Flow._DagNode] = {}
            self._executed: Dict[str, bool] = {}
            self._results: Dict[str, Any] = {}

        def _detect_circular_dependency(self) -> bool:
            """检测循环依赖（DFS算法）"""
            visited, rec_stack = set(), set()

            def dfs(node_id: str) -> bool:
                visited.add(node_id)
                rec_stack.add(node_id)
                node = self._nodes.get(node_id)
                if node:
                    for dep in node.depends_on:
                        if dep not in visited:
                            if dfs(dep):
                                return True
                        elif dep in rec_stack:
                            return True
                rec_stack.discard(node_id)
                return False

            return any(dfs(node_id) for node_id in self._nodes)

        def _build_nodes(self):
            """构建所有节点"""
            logger.info(f"[Flow][DAG] 开始构建节点, 数量: {len(self._flow_config)}")
            for cfg in self._flow_config:
                try:
                    step_id = cfg.get("step_id", "unknown")
                    node = Flow._DagNode(
                        DagNodeConfig(**cfg),
                        agent=self._agent,
                        tools=self._tools,
                        skills=self._skills,
                    )
                    node._build_output_model()
                    node._initialize_agent()
                    self._nodes[node.step_id] = node
                    self._executed[node.step_id] = False
                except Exception as e:
                    logger.error(
                        f"[Flow][DAG] 节点 {cfg.get('step_id', 'unknown')} 初始化失败: {e}"
                    )
                    raise

            logger.info(
                f"[Flow][DAG] 节点构建完成（共 {len(self._nodes)} 个），检测循环依赖..."
            )
            if self._detect_circular_dependency():
                raise CircularDependencyError("检测到循环依赖")

        def _get_ready_nodes(self) -> List[str]:
            """获取就绪节点（依赖已满足）"""
            return [
                step_id
                for step_id, node in self._nodes.items()
                if not self._executed[step_id]
                and all(self._executed.get(dep, False) for dep in node.depends_on)
            ]

        async def _execute_node(
            self, step_id: str, user_input: str, knowledge: str = ""
        ):
            """执行单个节点"""
            node = self._nodes[step_id]
            upstream_results = {
                dep: self._results.get(dep, {}) for dep in node.depends_on
            }
            self._results[step_id] = await node.execute(
                user_input, upstream_results, knowledge
            )
            self._executed[step_id] = True

        async def execute(
            self, user_input: str, parallel: bool = False, knowledge: str = ""
        ) -> Dict[str, Any]:
            """执行完整DAG流程"""
            exec_start = time.time()
            input_preview = (
                f"{user_input[:100]}{'...' if len(user_input) > 100 else ''}"
            )
            kb_info = f" | 知识库: {len(knowledge)} 字符" if knowledge else ""
            logger.info(f"[Flow][DAG] 开始执行 | 输入: {input_preview}{kb_info}")

            self._build_nodes()

            nodes_info = ", ".join(
                f"{nid}(dep={self._nodes[nid].depends_on})" for nid in self._nodes
            )
            logger.info(f"[Flow][DAG] 节点: {nodes_info}")

            iteration = 0
            while ready_nodes := self._get_ready_nodes():
                iteration += 1
                mode = "并行" if parallel and len(ready_nodes) > 1 else "串行"
                logger.info(f"[Flow][DAG] 迭代{iteration} [{mode}]: {ready_nodes}")

                if parallel and len(ready_nodes) > 1:
                    await asyncio.gather(
                        *[
                            self._execute_node(nid, user_input, knowledge)
                            for nid in ready_nodes
                        ]
                    )
                else:
                    for step_id in ready_nodes:
                        await self._execute_node(step_id, user_input, knowledge)

            exec_time = time.time() - exec_start
            logger.info(f"[Flow][DAG] 执行完成, 耗时: {exec_time:.2f}s")

            if not_executed := [k for k, v in self._executed.items() if not v]:
                raise DagExecutionError(f"未执行节点: {not_executed}")

            return self._results

    def __init__(self, agent: Agent = None, tools: list = None, skills: list = None):
        """初始化Flow工作流引擎

        Args:
            agent: 可选，用于任务规划的大模型 Agent 实例，不传则使用配置文件创建
            tools: 可选，工具列表（AgentTool 实例），不传则从 tool_registry 获取
            skills: 可选，技能列表（AgentSkill 实例），不传则从 skill_registry 获取可用技能
        """
        self._planner_agent = agent
        if tools is not None:
            self._tools = list(tools)
        else:
            from framework.agent.tool_system import tool_registry

            self._tools = tool_registry.list()
        if skills is not None:
            self._skills = list(skills)
        else:
            from framework.agent.skills import skill_registry

            self._skills = skill_registry.get_available_skills(
                {t.name for t in self._tools}
            )
        logger.info(
            f"[Flow] 初始化成功 | tools={len(self._tools)} | skills={len(self._skills)}"
        )

    @staticmethod
    def _build_prompt(input_data: Dict[str, Any]) -> str:
        """构建任务规划提示词"""
        tools_desc = "\n".join(
            [
                f"- {t.get('工具名称')}: {t.get('工具功能', '')}"
                for t in input_data.get("工具列表", [])
            ]
        )

        skills_desc = "\n".join(
            [
                f"- {s.get('技能名称')}: {s.get('技能能力', '')}"
                for s in input_data.get("技能列表", [])
            ]
        )

        # 构建知识库摘要（只传标题+摘要，避免规划时 token 过长）
        knowledge_desc = ""
        knowledge_data = input_data.get("knowledge", [])
        if knowledge_data and isinstance(knowledge_data, list):
            parts = []
            for k in knowledge_data:
                title = k.get("title") or k.get("filename", "")
                summary = k.get("summary", "")
                if title:
                    line = f"- {title}"
                    if summary:
                        line += f": {summary[:200]}"
                    parts.append(line)
            if parts:
                knowledge_desc = "\n".join(parts)

        return TaskPrompts.task_planner(
            role=input_data.get("角色", ""),
            persona=input_data.get("人设", ""),
            task_description=input_data.get("任务描述", ""),
            tools_desc=tools_desc,
            skills_desc=skills_desc,
            knowledge_desc=knowledge_desc,
        )

    @staticmethod
    def _convert_input(input_data: Dict[str, Any]) -> Dict[str, Any]:
        """转换输入数据为标准格式"""
        if all(k in input_data for k in ["角色", "人设", "任务描述"]):
            return input_data

        return {
            "角色": config.get_str("DOUBAO_DEFAULT_ROLE", "智能助手Agent"),
            "人设": config.get_str("DOUBAO_DEFAULT_PERSONA", "专业智能助手"),
            "任务描述": input_data.get("任务描述", input_data.get("content", "")),
            "工具列表": input_data.get("工具列表", []),
            "技能列表": input_data.get("技能列表", []),
        }

    @staticmethod
    def _validate_input(input_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """验证输入参数"""
        missing = [p for p in ["角色", "人设", "任务描述"] if not input_data.get(p)]
        input_data.setdefault("工具列表", [])
        input_data.setdefault("技能列表", [])

        if missing:
            return TaskActionPlan.create_error_output(
                "INPUT_MISSING", f"缺少必填参数: {', '.join(missing)}", missing
            )
        return None

    async def _generate_plan(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """调用Agent生成任务行动方案（基础重试）"""
        if self._planner_agent:
            agent = self._planner_agent
        else:
            agent = Agent()

        prompt = self._build_prompt(input_data)

        last_exception = None
        for attempt in range(3):
            try:
                result = await agent.chat(
                    system_prompt="",
                    context=[],
                    user_prompt=prompt,
                    temperature=0.1,
                )
                return json.loads(result.content)
            except Exception as e:
                last_exception = e
                if attempt < 2:
                    logger.warning(f"任务规划第{attempt+1}次失败，0.5s后重试: {e}")
                    await asyncio.sleep(0.5)

        return TaskActionPlan.create_error_output("PLAN_FAILED", str(last_exception))

    def _plan_to_flow(self, plan_result: Dict[str, Any]) -> Dict[str, Any]:
        """将任务识别结果转换为DAG配置

        每个节点配置包含：
        - sys_prompt: 任务说明 + JSON 输出要求
        - output_fields: 字段定义（用于构建 Pydantic model）
        """
        nodes = []
        for task in plan_result.get("task_details", []):
            task_name = task.get("task_name", "")
            task_goal = task.get("task_goal", "") or task.get("task_name", "")
            task_id = task.get("task_id", "")

            # 构建 sys_prompt，要求 LLM 输出 JSON
            sys_prompt = TaskPrompts.task_executor(
                task_name=task_name, task_goal=task_goal
            )

            nodes.append(
                {
                    "step_id": task_id,
                    "schema_unique_id": task_id + "_schema",
                    "sys_prompt": sys_prompt,
                    "depends_on": task.get("dependency", []),
                    "output_fields": {
                        "result": ["str", {"description": "任务执行结果（字符串）"}]
                    },
                    "temp": 0.0,
                    "retries": 2,
                    "input_template": "{raw_text}\n\n【参考知识库】\n{knowledge}",
                }
            )

        # 从执行模式中提取是否并行
        execution_flow = plan_result.get("global_execution_flow", {})
        execution_mode = execution_flow.get("execution_mode", "")
        parallel = "并行" in execution_mode

        return {"nodes": nodes, "parallel": parallel}

    async def plan(self, input_data: Dict[str, Any]) -> dict:
        """
        生成任务行动方案

        Args:
            input_data: 输入数据字典，包含角色、人设、任务描述等

        Returns:
            dict: {"success": bool, "result": dict, "error": str}
        """
        if not isinstance(input_data, dict):
            return {"success": False, "error": "输入数据必须是字典类型"}

        input_data = self._convert_input(input_data)
        if error := self._validate_input(input_data):
            return {
                "success": False,
                "error": error["error_message"],
                "fallback": error,
            }

        try:
            result = await self._generate_plan(input_data)
            if "error_code" in result:
                return {
                    "success": False,
                    "error": result["error_message"],
                    "fallback": result,
                }
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"任务规划失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback": TaskActionPlan.create_empty_plan(),
            }

    async def execute(
        self,
        user_input: Any,
        flow_config: List[Dict[str, Any]] = None,
        parallel: bool = False,
        tools: list = None,
        skills: list = None,
    ) -> dict:
        """
        执行DAG工作流

        Args:
            user_input: 用户输入（str 或 dict）
                - str: 纯文本输入
                - dict: {"text": str, "knowledge": Any}
            flow_config: DAG配置数组（可选，不传则只返回格式化输入）
            parallel: 是否启用并行执行
            tools: 可选，工具列表，覆盖 Flow 初始化时传入的工具
            skills: 可选，技能列表，覆盖 Flow 初始化时传入的技能

        Returns:
            dict: {"success": bool, "result": dict, "error": str, "code": str}
        """
        text = ""
        knowledge = ""

        if isinstance(user_input, dict):
            text = user_input.get("text", user_input.get("任务描述", ""))
            knowledge_raw = user_input.get("knowledge")
            if isinstance(knowledge_raw, list):
                knowledge = json.dumps(knowledge_raw, ensure_ascii=False)
            elif knowledge_raw:
                knowledge = str(knowledge_raw)
        else:
            text = str(user_input)

        if flow_config is None:
            return {"success": True, "text": text, "knowledge": knowledge}

        try:
            engine_tools = tools if tools is not None else self._tools
            engine_skills = skills if skills is not None else self._skills
            engine = self._DagEngine(
                flow_config,
                agent=self._planner_agent,
                tools=engine_tools,
                skills=engine_skills,
            )
            result = await engine.execute(text, parallel, knowledge)
            return {"success": True, "result": result}
        except CircularDependencyError as e:
            return {"success": False, "error": str(e), "code": "CIRCULAR_DEPENDENCY"}
        except DagExecutionError as e:
            return {"success": False, "error": str(e), "code": "DAG_EXECUTION_ERROR"}
        except Exception as e:
            logger.error(f"DAG执行异常: {e}", exc_info=True)
            return {"success": False, "error": str(e), "code": "UNKNOWN_ERROR"}

    async def run(
        self, input_data: Dict[str, Any], tools: list = None, skills: list = None
    ) -> dict:
        """
        完整流程：任务识别 → 配置转换 → 流程执行

        Args:
            input_data: 输入数据字典
                - 任务描述: "任务描述" 或 "content"
                - 知识库: "knowledge" (str 或 list[dict])
                - 角色: "角色"
                - 人设: "人设"
            tools: 可选，工具列表，覆盖 Flow 初始化时传入的工具
            skills: 可选，技能列表，覆盖 Flow 初始化时传入的技能

        Returns:
            dict: {"success": bool, "result": dict, "error": str}
        """
        start_time = time.time()

        task_desc = input_data.get("任务描述", input_data.get("content", ""))
        logger.info(f"[Flow] 开始流程 | 任务: {task_desc[:60]}...")

        knowledge_text = input_data.get("knowledge")

        plan_result = await self.plan(input_data)
        if not plan_result.get("success"):
            logger.error(f"[Flow] 规划失败: {plan_result.get('error', '')}")
            return plan_result

        flow_data = self._plan_to_flow(plan_result["result"])
        flow_config = flow_data.get("nodes", [])
        parallel = flow_data.get("parallel", False)

        if not flow_config:
            return {"success": False, "error": "任务识别未生成任何任务"}

        logger.info(
            f"[Flow] 执行配置: {len(flow_config)} 节点, 并行={'是' if parallel else '否'}"
        )

        user_input = {
            "text": task_desc,
            "knowledge": knowledge_text,
        }

        exec_result = await self.execute(
            user_input, flow_config, parallel, tools=tools, skills=skills
        )

        logger.info(f"[Flow] 流程完成, 总耗时: {time.time() - start_time:.2f}s")
        return exec_result
