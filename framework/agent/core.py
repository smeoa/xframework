"""基于 PydanticAI 的 Agent 核心模块

完全基于 PydanticAI 实现，提供稳定的工具调用能力。
"""

import json
import logging
from typing import Dict, List, Optional, Any, Set

from pydantic import BaseModel, Field
from pydantic_ai import Agent as PydanticAgent, Tool
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.output import PromptedOutput
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.messages import ModelRequest, ModelResponse, SystemPromptPart, UserPromptPart, TextPart, ImageUrl, TextContent

from framework.core.config import config

logger = logging.getLogger("agent")
logger.setLevel(logging.DEBUG)


def _to_pydantic_content(content_item: Any) -> Any:
    """将 dict 格式的内容项转换为 PydanticAI 的 Content 类型"""
    if isinstance(content_item, dict):
        item_type = content_item.get("type", "")
        if item_type == "image_url":
            url = content_item.get("image_url", {}).get("url", "")
            return ImageUrl(url=url)
        elif item_type == "text":
            return TextContent(content=content_item.get("text", ""))
    return content_item


def _dict_to_model_message(msg: dict) -> Any:
    """将普通 dict 消息转换为 PydanticAI 的 ModelMessage 格式"""
    role = msg.get("role", "user")
    content = msg.get("content", "")
    
    if role == "system":
        return ModelRequest(
            parts=[SystemPromptPart(content=content)],
            instructions=content,
            conversation_id=None,
        )
    elif role == "user":
        if isinstance(content, list):
            parts = [_to_pydantic_content(item) for item in content]
            return ModelRequest(
                parts=[UserPromptPart(content=parts)],
                conversation_id=None,
            )
        return ModelRequest(
            parts=[UserPromptPart(content=content)],
            conversation_id=None,
        )
    elif role == "assistant":
        return ModelResponse(
            parts=[TextPart(content=content)],
            conversation_id=None,
        )
    else:
        return ModelRequest(
            parts=[UserPromptPart(content=content)],
            conversation_id=None,
        )


def _is_tool_choice_unsupported(error: Exception) -> bool:
    """判断是否为「模型不支持 tool_choice」的错误

    部分「思考模式」模型（如 deepseek-flash）不支持强制工具调用，
    而 PydanticAI 的结构化输出默认就是用 tool_choice 实现的，会返回 400。
    """
    text = str(error)
    return "tool_choice" in text or "tool choice" in text.lower()


# 已知不支持 tool_choice 的模型名（首次 400 后记住，后续直接走 prompted 结构化输出）
# 这些模型每次结构化调用都先发一次注定失败的请求，记住后可省掉一半无效往返
_TOOL_CHOICE_UNSUPPORTED_MODELS: Set[str] = set()


class ChatMessage(BaseModel):
    """Agent.chat() 默认输出"""

    content: str = Field(default="", description="响应文本内容")
    tool_calls: list = Field(default=[], description="工具调用列表")
    tool_results: list = Field(default=[], description="工具执行结果列表")
    data: Optional[Dict[str, Any]] = Field(
        default=None, description="结构化输出数据（当 output_schema 生效时）"
    )


class Agent:
    """基于 PydanticAI 的智能代理类"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: str = "",
        system_prompt: str = "",
        tools: list = None,
        skills: list = None,
    ):
        """初始化 Agent

        Args:
            base_url: LLM API 基础 URL，不传则使用 DEFAULT_MODEL_BASE_URL 配置
            api_key: API 密钥，不传则使用 DEFAULT_MODEL_API_KEY 配置
            model_name: 模型名称，不传则使用 DEFAULT_MODEL_NAME 配置
            system_prompt: 系统提示词
            tools: 自定义工具列表
            skills: 技能列表
        """
        self.base_url = (
            base_url
            or config.get_str("DEFAULT_MODEL_BASE_URL", "http://localhost:11434/v1")
        ).rstrip("/")
        self.api_key = api_key or config.get_str("DEFAULT_MODEL_API_KEY", "ollama")
        self.model_name = model_name or config.get_str(
            "DEFAULT_MODEL_NAME", "qwen3.5:9b"
        )
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.skills = skills or []

        self._pydantic_agent = self._init_pydantic_agent()
        logger.info(
            f"[Agent] 初始化成功 | model={self.model_name} | base_url={self.base_url}"
        )

    def _init_pydantic_agent(self) -> PydanticAgent:
        """创建 PydanticAI Agent 实例"""
        provider = OpenAIProvider(
            base_url=self.base_url,
            api_key=self.api_key,
        )
        model = OpenAIChatModel(self.model_name, provider=provider)

        pyd_tools = []
        for tool_item in self.tools:
            try:
                pyd_tool = self._to_pydantic_tool(tool_item)
                pyd_tools.append(pyd_tool)
                logger.debug(f"[Agent] 加载工具: {tool_item.name}")
            except Exception as e:
                logger.warning(f"[Agent] 工具转换失败: {tool_item.name} - {e}")

        for skill_item in self.skills:
            try:
                pyd_tool = self._to_pydantic_tool(skill_item)
                pyd_tools.append(pyd_tool)
                logger.debug(f"[Agent] 加载技能: {skill_item.name}")
            except Exception as e:
                logger.warning(f"[Agent] 技能转换失败: {skill_item.name} - {e}")

        return PydanticAgent(
            model=model,
            tools=pyd_tools,
        )

    def _to_pydantic_tool(self, tool_item) -> Tool:
        """将工具项转换为 PydanticAI Tool"""
        from pydantic import create_model

        if hasattr(tool_item, "parameters") and tool_item.parameters:
            properties = tool_item.parameters.get("properties", {})
            required = tool_item.parameters.get("required", [])
            type_map = {
                "string": str,
                "integer": int,
                "number": float,
                "boolean": bool,
                "array": list,
                "object": dict,
            }

            fields = {}
            for name, prop in properties.items():
                py_type = type_map.get(prop.get("type", "string"), str)
                if name in required:
                    fields[name] = (py_type, ...)
                else:
                    fields[name] = (py_type, None)

            InputModel = create_model(f"{tool_item.name}_input", **fields)

            async def tool_func(input_data: InputModel) -> str:
                result = await tool_item.handler(**input_data.model_dump())
                return result if isinstance(result, str) else str(result)

            return Tool(
                tool_func,
                name=tool_item.name,
                description=tool_item.description,
            )
        elif hasattr(tool_item, "function"):
            return tool_item
        else:
            raise ValueError(f"无法转换工具: {tool_item.name}")

    async def chat(
        self,
        system_prompt: str = "",
        context: list = None,
        user_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        output_schema: Optional[BaseModel] = None,
        disable_thinking: bool = False,
    ) -> ChatMessage:
        """执行聊天，支持 JSON 结构化输出

        Args:
            system_prompt: 系统提示词
            context: 对话上下文列表，包含 user/assistant 消息
            user_prompt: 用户输入提示词
            temperature: 温度参数
            max_tokens: 最大 token 数
            output_schema: 输出 Pydantic 模型（可选）。传递后使用 PydanticAI 内置的
                          output_type 机制，强制 LLM 返回符合 schema 的 JSON。
            disable_thinking: 是否关闭模型思考模式。思考模式与强制工具调用（结构化输出）
                          互斥，开启思考时传 tool_choice 会返回 400
                          Thinking mode does not support this tool_choice；
                          置真时在请求体注入 thinking={"type": "disabled"}，可直接走原生
                          结构化输出，并避免 reasoning token 挤占 max_tokens。

        Returns:
            ChatMessage 实例（含 content/tool_calls/tool_results 字段）。
            当 output_schema 不为 None 时，content 为 JSON 字符串，data 字段包含解析后的 dict。
        """
        try:
            run_kwargs = {
                "user_prompt": user_prompt,
            }

            message_history = []
            if system_prompt:
                message_history.append(_dict_to_model_message({"role": "system", "content": system_prompt}))
            if context:
                message_history.extend([_dict_to_model_message(msg) for msg in context])

            if message_history:
                run_kwargs["message_history"] = message_history

            model_settings: Dict[str, Any] = {}
            if temperature != 0.7 or max_tokens != 2000:
                model_settings["temperature"] = temperature
                model_settings["max_tokens"] = max_tokens
            if disable_thinking:
                # DeepSeek 等思考模式模型：思考模式下不支持强制工具调用（tool_choice），
                # 否则返回 400 Thinking mode does not support this tool_choice；
                # 显式关闭思考后可直接走原生结构化输出，也避免 reasoning token 挤占 max_tokens
                model_settings["extra_body"] = {"thinking": {"type": "disabled"}}
            if model_settings:
                run_kwargs["model_settings"] = model_settings

            if output_schema is not None:
                if self.model_name in _TOOL_CHOICE_UNSUPPORTED_MODELS:
                    # 该模型此前已证实不支持 tool_choice，直接走 prompted 输出，避免白跑一次 400
                    run_kwargs["output_type"] = PromptedOutput(output_schema)
                else:
                    run_kwargs["output_type"] = output_schema

            logger.debug(
                f"[Agent.chat] 调用 PydanticAI | output_type={output_schema.__name__ if output_schema else None} | prompt={str(run_kwargs['user_prompt'])[:50]}..."
            )

            try:
                result = await self._pydantic_agent.run(**run_kwargs)
            except Exception as e:
                # 思考模式模型不支持 tool_choice 时，自动改用 prompted 结构化输出重试
                if output_schema is None or not _is_tool_choice_unsupported(e):
                    raise
                logger.warning(
                    f"[Agent.chat] 模型不支持 tool_choice，改用 prompted 结构化输出重试: {e}"
                )
                _TOOL_CHOICE_UNSUPPORTED_MODELS.add(self.model_name)
                run_kwargs["output_type"] = PromptedOutput(output_schema)
                result = await self._pydantic_agent.run(**run_kwargs)

            # PydanticAI 1.x 的 AgentRunResult 用 output 暴露结构化结果（旧版本为 data）
            data = getattr(result, "output", None)
            if data is None:
                data = getattr(result, "data", None)
            if isinstance(data, BaseModel):
                return ChatMessage(
                    content=data.model_dump_json(), data=data.model_dump()
                )
            if isinstance(data, dict):
                return ChatMessage(content=json.dumps(data, ensure_ascii=False), data=data)
            if data is not None:
                return ChatMessage(content=str(data))
            return ChatMessage(content=str(result))

        except Exception as e:
            logger.error(f"Agent.chat 执行失败: {e}", exc_info=True)
            return ChatMessage(content=f"AI服务调用失败: {str(e)}")

    async def check_health(self) -> dict:
        """检查健康状态"""
        try:
            result = await self._pydantic_agent.run("hello")
            return {"ok": True, "reason": "正常"}
        except Exception as e:
            return {"ok": False, "reason": str(e)}
