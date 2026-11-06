"""对话记忆管理"""

from .response import extract_response, get_content
from .prompt import SystemPrompts


class ConversationMemory:
    def __init__(self, conversation_id: str, max_recent: int = 5, max_total: int = 10):
        self.conversation_id = conversation_id
        self.max_recent = max_recent
        self.max_total = max_total
        self._messages: list = []

    def add_message(self, role: str, content: str):
        self._messages.append({"role": role, "content": content})

    @staticmethod
    def _is_pair(a: dict, b: dict) -> bool:
        return a["role"] == "user" and b["role"] == "assistant"

    def _count_rounds_in_direction(self, start: int, end: int, step: int) -> int:
        rounds = 0
        i = start
        while step > 0 and i < end - 1 or step < 0 and i >= end + 1:
            if self._is_pair(self._messages[i], self._messages[i + step]):
                rounds += 1
                i += step * 2
            else:
                i += step
        return rounds

    def _count_rounds(self) -> int:
        return self._count_rounds_in_direction(0, len(self._messages), 1)

    def _truncate_index(self, keep_rounds: int) -> int:
        n = len(self._messages)
        rounds = 0
        i = n - 1
        while i >= 1 and rounds < keep_rounds:
            if self._is_pair(self._messages[i - 1], self._messages[i]):
                rounds += 1
                i -= 2
            else:
                i -= 1
        return i + 1

    async def compress(self, agent=None, model: str = "qwen3.5:9b"):
        """压缩对话历史（简化实现）"""
        if self._count_rounds() <= self.max_total:
            return
        split = self._truncate_index(self.max_recent)
        if split <= 0:
            return
        
        history_to_compress = self._messages[:split]
        recent_messages = self._messages[split:]
        
        if agent:
            text = "\n".join(f"{m['role']}: {m['content']}" for m in history_to_compress)
            prompt = SystemPrompts.MESSAGE_COMPRESSION.format(text=text)
            result = await agent.chat(
                system_prompt="",
                context=[],
                user_prompt=prompt,
            )
            summary = result.content or ""
            self._messages = [{"role": "system", "content": summary}] + recent_messages
        else:
            # 如果没有 agent，直接截断
            self._messages = recent_messages

    async def get_messages(self, agent=None, model: str = "qwen3.5:9b"):
        if agent and self._count_rounds() > self.max_total:
            await self.compress(agent, model)
        return list(self._messages)

    def clear(self):
        self._messages = []
