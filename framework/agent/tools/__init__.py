"""工具模块

工具通过数据库配置动态加载：
- 数据库 tool 表存储工具配置（name, description, parameters）
- 工具名称 = handler 函数名 = 模块文件名
- 应用启动时调用 load_tools_from_db() 从数据库加载并注册

如需手动注册工具，可使用 @tool 装饰器：
    from framework.agent.tool_system import tool

    @tool(name="my_tool", description="...", parameters={...})
    async def my_tool(...):
        ...

内置工具在导入本包时通过 @tool 装饰器自动完成注册，
因此 `framework.agent` 被导入后即可从 tool_registry 取到这些工具。
"""
