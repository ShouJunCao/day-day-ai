"""
上下文窗口管理模块 (Context Window Management)
实现固定窗口 (Fixed Window) 和滑动窗口 (Sliding Window) 策略。
"""
from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import Optional


class TokenEstimator:
    """Token 估算器 - 生产环境推荐替换为 tiktoken"""

    @staticmethod
    def estimate(text: str) -> int:
        """
        粗略估算 Token 数量。
        英文约 4 字符/token，中文约 1.5 字/token。
        """
        if not text:
            return 0
        cn_count = sum(1 for c in text if ord(c) > 127)
        en_count = len(text) - cn_count
        return max(1, int(cn_count / 1.5) + int(en_count / 4))


@dataclass(frozen=True)
class Message:
    """不可变消息对象"""
    role: str
    content: str
    token_count: int = 0

    def __post_init__(self):
        if self.token_count == 0:
            object.__setattr__(self, "token_count", TokenEstimator.estimate(self.content))


@dataclass
class SlidingWindowContext:
    """
    滑动窗口管理器 (Sliding Window Manager)

    核心逻辑:
    1. 始终保留 System Prompt (index 0)
    2. 当 Token 总量超过 max_tokens 时, 从最旧消息开始裁剪
    3. 当消息条数超过 max_turns 时, 同样裁剪最旧消息
    """
    max_turns: int = 10
    max_tokens: int = 4000
    messages: list[Message] = field(default_factory=list)

    def add(self, role: str, content: str) -> None:
        """添加新消息并触发自动裁剪"""
        msg = Message(role=role, content=content)
        self.messages.append(msg)
        self._trim()

    def _trim(self) -> None:
        # 优先级 1: Token 预算检查
        while self._current_tokens > self.max_tokens and len(self.messages) > 2:
            self._pop_oldest()

        # 优先级 2: Turn 数量检查
        while len(self.messages) > self.max_turns:
            self._pop_oldest()

    def _pop_oldest(self) -> None:
        """删除最旧的非 System 消息"""
        if not self.messages:
            return
        if self.messages[0].role == "system" and len(self.messages) > 1:
            self.messages.pop(1)
        elif self.messages[0].role != "system":
            self.messages.pop(0)

    @property
    def _current_tokens(self) -> int:
        return sum(m.token_count for m in self.messages)

    def get_context(self) -> list[dict[str, str]]:
        """获取可发送给 LLM 的上下文列表"""
        return [{"role": m.role, "content": m.content} for m in self.messages]

    def __len__(self) -> int:
        return len(self.messages)

    @property
    def token_usage(self) -> str:
        return f"{self._current_tokens}/{self.max_tokens}"
