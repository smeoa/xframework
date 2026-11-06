"""Flow DAG工作流引擎单元测试"""
import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock

from framework.agent.flow import Flow, DagNodeConfig, TaskActionPlan


class TestFlowBasic:
    """Flow 基础功能测试"""

    def test_flow_init(self):
        """测试 Flow 初始化"""
        flow = Flow()
        assert flow._planner_agent is None

    @patch("framework.agent.flow.Agent")
    def test_flow_init_with_agent(self, mock_agent_class):
        """测试带 Agent 的初始化"""
        mock_agent = MagicMock()
        flow = Flow(agent=mock_agent)
        assert flow._planner_agent is mock_agent


class TestTaskActionPlan:
    """TaskActionPlan 测试"""

    def test_create_error_output(self):
        """测试创建错误输出"""
        error = TaskActionPlan.create_error_output(
            "TEST_ERROR", "测试错误信息", ["param1"]
        )
        assert error["error_code"] == "TEST_ERROR"
        assert error["error_message"] == "测试错误信息"
        assert error["missing_params"] == ["param1"]

    def test_create_empty_plan(self):
        """测试创建空计划"""
        plan = TaskActionPlan.create_empty_plan()
        assert plan["task_overview"]["total_tasks"] == 0
        assert plan["task_details"] == []
        assert plan["global_execution_flow"]["execution_mode"] == "全串行"


class TestDagNodeConfig:
    """DAG 节点配置测试"""

    def test_dag_node_config_valid(self):
        """测试有效配置"""
        config = DagNodeConfig(
            step_id="T001",
            schema_unique_id="T001_schema",
            sys_prompt="测试提示词",
            output_fields={"result": ["str", {"description": "测试结果"}]}
        )
        assert config.step_id == "T001"
        assert config.depends_on == []
        assert config.temp == 0.0
        assert config.retries == 2
        assert config.input_template == "{raw_text}"

    def test_dag_node_config_with_dependencies(self):
        """测试带依赖配置"""
        config = DagNodeConfig(
            step_id="T002",
            schema_unique_id="T002_schema",
            sys_prompt="测试提示词",
            depends_on=["T001"],
            output_fields={"result": ["str", {"description": "测试结果"}]}
        )
        assert config.depends_on == ["T001"]


class TestFlowPlanConversion:
    """Flow 计划转换测试"""

    def test_plan_to_flow_empty(self):
        """测试空计划转换"""
        flow = Flow()
        result = flow._plan_to_flow({})
        assert result["nodes"] == []
        assert result["parallel"] is False

    def test_plan_to_flow_single_task(self):
        """测试单个任务转换"""
        flow = Flow()
        plan = {
            "task_details": [
                {
                    "task_id": "T001",
                    "task_name": "测试任务",
                    "task_goal": "完成测试",
                    "dependency": []
                }
            ]
        }
        result = flow._plan_to_flow(plan)
        assert len(result["nodes"]) == 1
        node = result["nodes"][0]
        assert node["step_id"] == "T001"
        assert node["schema_unique_id"] == "T001_schema"
        assert "完成测试" in node["sys_prompt"]
        assert "严格输出要求" in node["sys_prompt"]
        assert node["depends_on"] == []

    def test_plan_to_flow_multiple_tasks(self):
        """测试多个任务转换"""
        flow = Flow()
        plan = {
            "task_details": [
                {"task_id": "T001", "task_name": "任务1", "task_goal": "目标1", "dependency": []},
                {"task_id": "T002", "task_name": "任务2", "task_goal": "目标2", "dependency": ["T001"]},
            ]
        }
        result = flow._plan_to_flow(plan)
        assert len(result["nodes"]) == 2
        assert result["nodes"][1]["depends_on"] == ["T001"]

    def test_plan_to_flow_parallel_mode(self):
        """测试并行模式识别"""
        flow = Flow()
        plan = {
            "global_execution_flow": {
                "execution_mode": "全并行"
            },
            "task_details": []
        }
        result = flow._plan_to_flow(plan)
        assert result["parallel"] is True

    def test_plan_to_flow_serial_mode(self):
        """测试串行模式识别"""
        flow = Flow()
        plan = {
            "global_execution_flow": {
                "execution_mode": "全串行"
            },
            "task_details": []
        }
        result = flow._plan_to_flow(plan)
        assert result["parallel"] is False


class TestFlowInputValidation:
    """Flow 输入验证测试"""

    def test_validate_input_missing_role(self):
        """测试缺少角色"""
        flow = Flow()
        input_data = {"人设": "test", "任务描述": "test"}
        result = flow._validate_input(input_data)
        assert result is not None
        assert "缺少必填参数" in result["error_message"]

    def test_validate_input_missing_persona(self):
        """测试缺少人设"""
        flow = Flow()
        input_data = {"角色": "test", "任务描述": "test"}
        result = flow._validate_input(input_data)
        assert result is not None
        assert "缺少必填参数" in result["error_message"]

    def test_validate_input_missing_task(self):
        """测试缺少任务描述"""
        flow = Flow()
        input_data = {"角色": "test", "人设": "test"}
        result = flow._validate_input(input_data)
        assert result is not None
        assert "缺少必填参数" in result["error_message"]

    def test_validate_input_valid(self):
        """测试有效输入"""
        flow = Flow()
        input_data = {"角色": "test", "人设": "test", "任务描述": "test"}
        result = flow._validate_input(input_data)
        assert result is None


class TestFlowInputConversion:
    """Flow 输入转换测试"""

    def test_convert_input_standard_format(self):
        """测试标准格式输入"""
        flow = Flow()
        input_data = {"角色": "a", "人设": "b", "任务描述": "c"}
        result = flow._convert_input(input_data)
        assert result == input_data

    def test_convert_input_minimal_format(self):
        """测试最小格式输入"""
        flow = Flow()
        input_data = {"content": "test task"}
        result = flow._convert_input(input_data)
        assert result["角色"] == "智能助手Agent"
        assert result["人设"] == "专业智能助手"
        assert result["任务描述"] == "test task"


class TestFlowExecute:
    """Flow.execute() 测试"""

    @pytest.mark.asyncio
    async def test_execute_without_flow_config(self):
        """测试不传 flow_config """
        flow = Flow()

        # 字符串输入
        result = await flow.execute("test input")
        assert result["success"] is True
        assert result["text"] == "test input"
        assert result["knowledge"] == ""

    @pytest.mark.asyncio
    async def test_execute_with_dict_input(self):
        """测试字典输入"""
        flow = Flow()
        user_input = {
            "text": "用户问题",
            "knowledge": [{"id": "1", "content": "文档内容"}]
        }
        result = await flow.execute(user_input)
        assert result["success"] is True
        assert result["text"] == "用户问题"
        assert result["knowledge"] == json.dumps(user_input["knowledge"], ensure_ascii=False)

    @pytest.mark.asyncio
    async def test_execute_with_string_knowledge(self):
        """测试字符串知识库"""
        flow = Flow()
        user_input = {
            "text": "用户问题",
            "knowledge": '[{"id": "1"}]'
        }
        result = await flow.execute(user_input)
        assert result["success"] is True
        assert result["knowledge"] == '[{"id": "1"}]'


class TestFlowBuildPrompt:
    """Flow 提示词构建测试"""

    def test_build_prompt_basic(self):
        """测试基础提示词构建"""
        flow = Flow()
        input_data = {
            "角色": "测试角色",
            "人设": "测试人设",
            "任务描述": "测试任务"
        }
        prompt = flow._build_prompt(input_data)
        assert "测试角色" in prompt
        assert "测试人设" in prompt
        assert "测试任务" in prompt

    def test_build_prompt_with_tools(self):
        """测试带工具的提示词"""
        flow = Flow()
        input_data = {
            "角色": "测试角色",
            "人设": "测试人设",
            "任务描述": "测试任务",
            "工具列表": [
                {"工具名称": "搜索", "工具功能": "搜索信息"}
            ]
        }
        prompt = flow._build_prompt(input_data)
        assert "搜索" in prompt

    def test_build_prompt_with_skills(self):
        """测试带技能的提示词"""
        flow = Flow()
        input_data = {
            "角色": "测试角色",
            "人设": "测试人设",
            "任务描述": "测试任务",
            "技能列表": [
                {"技能名称": "写作", "技能能力": "写作能力"}
            ]
        }
        prompt = flow._build_prompt(input_data)
        assert "写作" in prompt


class TestFlowRun:
    """Flow.run() 集成测试"""

    @pytest.mark.asyncio
    async def test_run_missing_params(self):
        """测试缺少必填参数"""
        flow = Flow()
        result = await flow.run({})
        assert result["success"] is False
        assert "缺少必填参数" in result["error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
