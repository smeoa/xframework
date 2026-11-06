"""测试 Agent.chat() 的参数映射"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from framework.agent.core import Agent, _dict_to_model_message
from pydantic_ai.messages import ModelRequest


class TestChatParameterMapping:
    """测试 chat() 方法参数映射"""

    def test_user_prompt_maps_to_user_prompt(self):
        """user_prompt 参数直接映射到 user_prompt"""
        agent = Agent(model_name="test")
        agent._pydantic_agent = MagicMock()
        agent._pydantic_agent.run = AsyncMock(return_value="test response")

        import asyncio
        asyncio.run(agent.chat(user_prompt="你好"))

        agent._pydantic_agent.run.assert_called_once()
        call_kwargs = agent._pydantic_agent.run.call_args[1]
        assert call_kwargs["user_prompt"] == "你好"

    def test_system_prompt_added_to_message_history(self):
        """system_prompt 添加到 message_history 前面"""
        agent = Agent(model_name="test")
        agent._pydantic_agent = MagicMock()
        agent._pydantic_agent.run = AsyncMock(return_value="test response")

        import asyncio
        asyncio.run(agent.chat(system_prompt="你是助手", user_prompt="你好"))

        agent._pydantic_agent.run.assert_called_once()
        call_kwargs = agent._pydantic_agent.run.call_args[1]
        assert "message_history" in call_kwargs
        message_history = call_kwargs["message_history"]
        assert len(message_history) == 1
        assert isinstance(message_history[0], ModelRequest)
        assert "你是助手" in str(message_history[0])

    def test_context_maps_to_message_history(self):
        """context 参数映射到 message_history"""
        agent = Agent(model_name="test")
        agent._pydantic_agent = MagicMock()
        agent._pydantic_agent.run = AsyncMock(return_value="test response")

        context = [{"role": "user", "content": "之前的消息"}]

        import asyncio
        asyncio.run(agent.chat(context=context, user_prompt="你好"))

        agent._pydantic_agent.run.assert_called_once()
        call_kwargs = agent._pydantic_agent.run.call_args[1]
        assert "message_history" in call_kwargs
        message_history = call_kwargs["message_history"]
        assert len(message_history) == 1
        assert isinstance(message_history[0], ModelRequest)

    def test_system_prompt_and_context_combined_to_message_history(self):
        """system_prompt 和 context 一起添加到 message_history"""
        agent = Agent(model_name="test")
        agent._pydantic_agent = MagicMock()
        agent._pydantic_agent.run = AsyncMock(return_value="test response")

        context = [{"role": "user", "content": "之前的消息"}]

        import asyncio
        asyncio.run(agent.chat(system_prompt="你是助手", context=context, user_prompt="你好"))

        agent._pydantic_agent.run.assert_called_once()
        call_kwargs = agent._pydantic_agent.run.call_args[1]
        assert "message_history" in call_kwargs
        message_history = call_kwargs["message_history"]
        assert len(message_history) == 2
        assert isinstance(message_history[0], ModelRequest)
        assert isinstance(message_history[1], ModelRequest)

    def test_empty_system_prompt_and_context_not_passed(self):
        """空 system_prompt 和 context 不传递 message_history"""
        agent = Agent(model_name="test")
        agent._pydantic_agent = MagicMock()
        agent._pydantic_agent.run = AsyncMock(return_value="test response")

        import asyncio
        asyncio.run(agent.chat(user_prompt="你好"))

        agent._pydantic_agent.run.assert_called_once()
        call_kwargs = agent._pydantic_agent.run.call_args[1]
        assert "message_history" not in call_kwargs

    def test_full_scenario(self):
        """完整场景：system_prompt + context + user_prompt"""
        agent = Agent(model_name="test")
        agent._pydantic_agent = MagicMock()
        agent._pydantic_agent.run = AsyncMock(return_value="test response")

        context = [
            {"role": "user", "content": "帮我推荐一部科幻电影"},
            {"role": "assistant", "content": "推荐《星际穿越》"},
        ]

        import asyncio
        asyncio.run(agent.chat(
            system_prompt="你是小学老师，回答简单通俗",
            context=context,
            user_prompt="那它导演是谁？"
        ))

        agent._pydantic_agent.run.assert_called_once()
        call_kwargs = agent._pydantic_agent.run.call_args[1]
        assert call_kwargs["user_prompt"] == "那它导演是谁？"
        assert "message_history" in call_kwargs
        message_history = call_kwargs["message_history"]
        assert len(message_history) == 3


class TestDictToModelMessage:
    """测试 _dict_to_model_message 函数"""

    def test_system_message(self):
        """转换系统消息"""
        msg = _dict_to_model_message({"role": "system", "content": "你是助手"})
        assert isinstance(msg, ModelRequest)
        assert "你是助手" in str(msg)

    def test_user_message(self):
        """转换用户消息"""
        msg = _dict_to_model_message({"role": "user", "content": "你好"})
        assert isinstance(msg, ModelRequest)
        assert "你好" in str(msg)

    def test_assistant_message(self):
        """转换助手消息"""
        from pydantic_ai.messages import ModelResponse
        msg = _dict_to_model_message({"role": "assistant", "content": "我是助手"})
        assert isinstance(msg, ModelResponse)
        assert "我是助手" in str(msg)

    def test_default_role(self):
        """默认角色为 user"""
        msg = _dict_to_model_message({"content": "你好"})
        assert isinstance(msg, ModelRequest)
