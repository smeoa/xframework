"""工具注册系统"""

import time
import json
import logging
import importlib
from dataclasses import dataclass
from typing import Callable, Awaitable, Any

logger = logging.getLogger(__name__)


@dataclass
class CallableItem:
    name: str
    description: str
    parameters: dict
    handler: Callable[..., Awaitable[Any]]


class BaseRegistry:
    """单例注册器基类，子类直接继承即可获得独立单例"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._items = {}
        return cls._instance

    def register(self, item: CallableItem):
        self._items[item.name] = item

    def get(self, name: str):
        return self._items.get(name)

    def list(self):
        return list(self._items.values())

    def __len__(self):
        return len(self._items)

    def unregister(self, name: str):
        if name in self._items:
            del self._items[name]

    def _format_as_tool(self, item: CallableItem) -> dict:
        return {
            "type": "function",
            "function": {
                "name": item.name,
                "description": item.description,
                "parameters": item.parameters,
            },
        }

    def get_tools_schema(self):
        return [self._format_as_tool(item) for item in self._items.values()]


class AgentTool(CallableItem):
    pass


class ToolRegistry(BaseRegistry):
    pass


def tool(name: str, description: str, parameters: dict):
    def decorator(handler):
        t = AgentTool(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler,
        )
        tool_registry.register(t)
        return handler
    return decorator


tool_registry = ToolRegistry()


async def load_tools_from_db():
    """从数据库加载工具配置并动态导入 handler

    工具名称 = handler 函数名
    模块文件名通过尝试导入确定（支持同一模块多个工具）
    """
    from admin.models import ToolModel
    from framework.core.config import config

    tool_model = ToolModel()
    tools = await tool_model.get_available()

    if not tools:
        logger.warning("数据库中没有启用的工具")
        return

    handler_path = config.get("tool.handler_path", "framework.agent.tools")
    loaded_count = 0

    # 模块缓存，避免重复导入
    module_cache = {}

    for tool_info in tools:
        tool_name = tool_info["name"]

        # 尝试直接导入与工具同名的模块
        module_path = f"{handler_path}.{tool_name}"
        handler = None

        try:
            # 尝试直接导入
            if module_path not in module_cache:
                module_cache[module_path] = importlib.import_module(module_path)
            module = module_cache[module_path]
            handler = getattr(module, tool_name)
        except ModuleNotFoundError:
            # 尝试从已知模块导入
            known_modules = ["document_summary", "image_understanding"]
            for mod_name in known_modules:
                try:
                    alt_module_path = f"{handler_path}.{mod_name}"
                    if alt_module_path not in module_cache:
                        module_cache[alt_module_path] = importlib.import_module(alt_module_path)
                    module = module_cache[alt_module_path]
                    handler = getattr(module, tool_name)
                    break
                except (ModuleNotFoundError, AttributeError):
                    continue

        if handler is None:
            logger.error(f"工具 {tool_name} 的 handler 未找到")
            continue

        try:
            # 解析参数定义
            parameters = tool_info.get("parameters", "{}")
            if isinstance(parameters, str):
                parameters = json.loads(parameters)

            # 创建 AgentTool 并注册
            t = AgentTool(
                name=tool_name,
                description=tool_info["description"],
                parameters=parameters,
                handler=handler,
            )
            tool_registry.register(t)
            loaded_count += 1
            logger.info(f"加载工具: {tool_name}")

        except Exception as e:
            logger.error(f"加载工具 {tool_name} 失败: {e}")

    logger.info(f"从数据库加载了 {loaded_count} 个工具")


async def _log_tool_invocation(
    tool_name: str,
    input_params: dict,
    result: Any,
    duration_ms: int,
    success: bool,
    error_message: str = None,
    role_id: int = None,
    conversation_id: int = None
):
    """记录工具调用日志"""
    try:
        from admin.models import ToolInvocationLogModel
        log_model = ToolInvocationLogModel()
        await log_model.log(
            tool_name=tool_name,
            role_id=role_id,
            conversation_id=conversation_id,
            input_params=input_params,
            output_result=result if isinstance(result, dict) else {"result": str(result)},
            success=success,
            error_message=error_message,
            duration_ms=duration_ms
        )
    except Exception as e:
        logger.warning(f"记录工具调用日志失败: {e}")


def to_pydantic_tool(item: CallableItem, role_id: int = None, conversation_id: int = None):
    """将 CallableItem 转换为 pydantic_ai Tool 对象

    Args:
        item: CallableItem 实例，包含 name, description, parameters, handler
        role_id: 角色ID（可选，用于日志记录）
        conversation_id: 会话ID（可选，用于日志记录）

    Returns:
        pydantic_ai Tool 对象，可用于 pydantic_ai Agent 的 tools 参数
    """
    from pydantic import create_model
    from pydantic_ai import Tool as PydanticAITool

    # 从 parameters 的 properties 中构建 Pydantic model 字段
    fields = {}
    properties = (item.parameters or {}).get("properties", {})
    required = (item.parameters or {}).get("required", [])
    type_map = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "array": list,
        "object": dict,
    }

    for name, prop in properties.items():
        py_type = type_map.get(prop.get("type", "string"), str)
        if name in required:
            fields[name] = (py_type, ...)
        else:
            fields[name] = (py_type, None)

    InputModel = create_model(f"{item.name}_input", **fields)

    async def tool_func(input_data: InputModel) -> str:
        start_time = time.time()
        input_params = input_data.model_dump()
        result = None
        success = True
        error_message = None

        try:
            result = await item.handler(**input_params)
            return result if isinstance(result, str) else str(result)
        except Exception as e:
            success = False
            error_message = str(e)
            logger.error(f"工具 {item.name} 执行失败: {e}")
            raise
        finally:
            duration_ms = int((time.time() - start_time) * 1000)
            # 异步记录日志，不阻塞工具返回
            import asyncio
            asyncio.create_task(_log_tool_invocation(
                tool_name=item.name,
                input_params=input_params,
                result=result,
                duration_ms=duration_ms,
                success=success,
                error_message=error_message,
                role_id=role_id,
                conversation_id=conversation_id
            ))

    return PydanticAITool(
        tool_func,
        name=item.name,
        description=item.description,
    )
