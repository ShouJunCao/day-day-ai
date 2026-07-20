"""
摘要压缩引擎 (Summary Compressor)
当对话历史过长时, 用 LLM 将旧消息压缩为一段摘要。
"""
from __future__ import annotations
import os
import httpx
from dataclasses import dataclass


@dataclass
class CompressorConfig:
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"  # 使用廉价小模型做压缩
    max_summary_tokens: int = 150
    timeout: int = 30

    def __post_init__(self):
        if not self.api_key:
            self.api_key = os.getenv("API_KEY", "")


class SummaryCompressor:
    """
    摘要压缩器

    工作流程:
    1. 接收一组旧消息 (通常是最早的 N 条)
    2. 调用 LLM 将其压缩为一段摘要
    3. 返回摘要字符串, 可替换回 System Prompt 或插入上下文开头
    """

    def __init__(self, config: CompressorConfig | None = None):
        self.config = config or CompressorConfig()

    async def compress(self, old_messages: list[dict]) -> str:
        """将旧对话压缩为摘要"""
        if not old_messages:
            return ""

        # 构建压缩 Prompt
        history_text = "\n".join(
            f"[{m.get('role', 'user')}] {m.get('content', '')}"
            for m in old_messages
        )

        system_prompt = (
            "你是一名对话摘要助手。请将以下对话历史压缩为简洁的摘要, "
            "保留用户的核心意图、已解决的问题和关键结论。"
            "用中文输出, 不超过 150 字。"
        )

        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            resp = await client.post(
                f"{self.config.base_url}/chat/completions",
                json={
                    "model": self.config.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": history_text},
                    ],
                    "max_tokens": self.config.max_summary_tokens,
                },
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    def build_context_with_summary(
        self, summary: str, recent_messages: list[dict]
    ) -> list[dict]:
        """将摘要 + 最近消息合并为完整的上下文"""
        return [
            {"role": "system", "content": f"以下是之前对话的摘要:\n{summary}"},
            *recent_messages,
        ]
