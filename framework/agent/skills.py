"""技能系统：比工具更高层的抽象，可声明依赖的工具"""

import json
import logging
import importlib
from dataclasses import dataclass, field
from typing import List, Set

from .tool_system import CallableItem, BaseRegistry

logger = logging.getLogger(__name__)


@dataclass
class AgentSkill(CallableItem):
    requires_tools: List[str] = field(default_factory=list)
    instructions: str = ""  # 自然语言执行指令


class SkillRegistry(BaseRegistry):
    def get_available_skills(self, registered_tool_names: Set[str] = None):
        if registered_tool_names is None:
            from .tool_system import tool_registry

            registered_tool_names = {t.name for t in tool_registry.list()}
        return [
            s
            for s in self._items.values()
            if set(s.requires_tools).issubset(registered_tool_names)
        ]

    def get_tools_schema(self):
        return [self._format_as_tool(s) for s in self.get_available_skills()]


def skill(
    name: str, description: str, parameters: dict, requires_tools: List[str] = None
):
    def decorator(handler):
        s = AgentSkill(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler,
            requires_tools=requires_tools or [],
        )
        skill_registry.register(s)
        return handler

    return decorator


skill_registry = SkillRegistry()


async def load_skills_from_db():
    """从数据库加载技能配置并动态导入 handler

    技能名称 = handler 函数名
    模块文件名通过尝试导入确定
    """
    from admin.models import SkillModel
    from framework.core.config import config

    skill_model = SkillModel()
    skills = await skill_model.get_available()

    if not skills:
        logger.warning("数据库中没有启用的技能")
        return

    handler_path = config.get("skill.handler_path", "framework.agent.skills")
    loaded_count = 0

    # 模块缓存
    module_cache = {}

    for skill_info in skills:
        skill_name = skill_info["name"]

        # 尝试导入 handler
        module_path = f"{handler_path}.{skill_name}"
        handler = None

        try:
            if module_path not in module_cache:
                module_cache[module_path] = importlib.import_module(module_path)
            module = module_cache[module_path]
            handler = getattr(module, skill_name)
        except (ModuleNotFoundError, AttributeError):
            # 技能可能没有独立 handler（依赖工具组合实现）
            pass

        try:
            # 解析参数定义
            parameters = skill_info.get("parameters", "{}")
            if isinstance(parameters, str):
                parameters = json.loads(parameters)

            # 解析依赖工具
            requires_tools = skill_info.get("requires_tools", "[]")
            if isinstance(requires_tools, str):
                requires_tools = json.loads(requires_tools)

            # 创建 AgentSkill 并注册
            s = AgentSkill(
                name=skill_name,
                description=skill_info["description"],
                parameters=parameters,
                handler=handler,
                requires_tools=requires_tools or [],
                instructions=skill_info.get("instructions", ""),
            )
            skill_registry.register(s)
            loaded_count += 1
            logger.info(f"加载技能: {skill_name}")

        except Exception as e:
            logger.error(f"加载技能 {skill_name} 失败: {e}")

    logger.info(f"从数据库加载了 {loaded_count} 个技能")
