"""
Token 预算控制 (Token Budget Controller)
精确计算输入 Token 数量, 防止超出模型上下文限制。
"""
from __future__ import annotations
import os


class TokenBudgetError(Exception):
    """Token 预算超限异常"""
    pass


class TokenBudgetController:
    """
    Token 预算控制器

    功能:
    1. 精确计算消息列表的 Token 总量
    2. 在发送前检查是否超出预算
    3. 提供自动裁剪建议

    生产环境建议: 使用 tiktoken 库替代此处的粗略估算
    """

    def __init__(self, limit: int = 8192, model: str = "gpt-4o"):
        """
        Args:
            limit: Token 上限 (默认 8K)
            model: 模型名称 (用于选择合适的编码方式)
        """
        self.limit = limit
        self.model = model

    def count_tokens(self, messages: list[dict]) -> int:
        """计算消息列表的 Token 总量"""
        total = 0
        for msg in messages:
            content = msg.get("content", "")
            total += self._estimate_tokens(content)
            # 每条消息额外增加角色 overhead
            total += 4
        # 增加系统级 overhead
        total += 3
        return total

    def _estimate_tokens(self, text: str) -> int:
        """
        粗略估算 Token 数。
        生产环境请使用: import tiktoken; enc = tiktoken.encoding_for_model(self.model)
        """
        if not text:
            return 0
        cn_count = sum(1 for c in text if ord(c) > 127)
        en_count = len(text) - cn_count
        return int(cn_count / 1.5) + int(en_count / 4)

    def check(self, messages: list[dict]) -> dict:
        """
        检查 Token 预算

        Returns:
            {"ok": bool, "used": int, "remaining": int, "over_by": int}
        """
        used = self.count_tokens(messages)
        remaining = max(0, self.limit - used)
        over_by = max(0, used - self.limit)

        return {
            "ok": used <= self.limit,
            "used": used,
            "remaining": remaining,
            "over_by": over_by,
        }

    def trim_to_fit(self, messages: list[dict]) -> list[dict]:
        """
        自动裁剪消息直到符合预算
        策略: 保留 System Prompt, 从最旧的用户消息开始删除
        """
        result = list(messages)
        while self.count_tokens(result) > self.limit and len(result) > 1:
            # 保护第一条 (通常是 System Prompt)
            idx = 1 if result[0].get("role") == "system" else 0
            result.pop(idx)
        return result


# ---- 使用示例 ----
if __name__ == "__main__":
    controller = TokenBudgetController(limit=500)

    test_messages = [
        {"role": "system", "content": "你是一个编程助手。"},
        {"role": "user", "content": "Python 如何实现装饰器?" * 20},
        {"role": "assistant", "content": "装饰器是一种设计模式..." * 15},
        {"role": "user", "content": "能举个例子吗?" * 10},
    ]

    result = controller.check(test_messages)
    print(f"Token 使用: {result['used']}/{controller.limit}")
    print(f"剩余: {result['remaining']}")

    if not result["ok"]:
        print(f"⚠️ 超出 {result['over_by']} tokens, 正在裁剪...")
        trimmed = controller.trim_to_fit(test_messages)
        new_result = controller.check(trimmed)
        print(f"裁剪后: {new_result['used']}/{controller.limit} (删除了 {len(test_messages) - len(trimmed)} 条消息)")
