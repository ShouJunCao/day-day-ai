"""
Prompt优化工具 - 减少不必要的token消耗

Token费用的优化不仅限于选择便宜的模型，
还可以通过优化prompt本身来降低成本。

常见浪费：
    - 过长的system prompt（每次都计费）
    - 重复的历史消息（多轮对话累积）
    - 不必要的格式化指令
    - 冗余的few-shot示例

本模块提供：
    1. Prompt压缩（去除冗余内容）
    2. 对话历史裁剪（保留关键上下文）
    3. 成本预估（发送前计算费用）
"""

from typing import List, Dict, Optional, Tuple


class PromptOptimizer:
    """Prompt优化工具

    功能：
    1. 对话历史裁剪：在token预算内保留最重要的消息
    2. System prompt压缩：去除冗余描述
    3. 费用预估：发送前估算本次调用成本

    Example:
        optimizer = PromptOptimizer(max_context_tokens=3000)
        trimmed = optimizer.trim_history(
            messages=long_history,
            token_counter=count_fn,
        )
    """

    def __init__(self, max_context_tokens: int = 4000):
        """初始化优化器

        Args:
            max_context_tokens: 上下文最大token数（包含system+history+user）
        """
        self.max_context_tokens = max_context_tokens

    def trim_history(
        self,
        messages: List[Dict[str, str]],
        token_counter,
        reserved_for_output: int = 500,
    ) -> List[Dict[str, str]]:
        """裁剪对话历史，在token预算内保留最近的消息

        策略：
        1. 始终保留system消息（第一条）
        2. 从最新消息开始保留，直到达到token上限
        3. 超出部分被裁剪（最早的对话先被移除）

        Args:
            messages: 完整的对话历史
            token_counter: token计数函数 (text: str) -> int
            reserved_for_output: 为输出预留的token数

        Returns:
            裁剪后的消息列表
        """
        if not messages:
            return messages

        available = self.max_context_tokens - reserved_for_output

        # 始终保留system消息
        result = []
        system_msg = None

        if messages[0]["role"] == "system":
            system_msg = messages[0]
            system_tokens = token_counter(system_msg["content"])
            available -= system_tokens
            messages_to_process = messages[1:]
        else:
            messages_to_process = messages

        # 从最新消息开始，向前保留
        kept_messages = []
        used_tokens = 0

        for msg in reversed(messages_to_process):
            msg_tokens = token_counter(msg["content"]) + 3  # 格式开销

            if used_tokens + msg_tokens > available:
                break

            kept_messages.insert(0, msg)
            used_tokens += msg_tokens

        # 组装结果
        if system_msg:
            result = [system_msg] + kept_messages
        else:
            result = kept_messages

        return result

    def compress_system_prompt(
        self,
        system_prompt: str,
        token_counter,
        max_tokens: int = 200,
    ) -> str:
        """压缩system prompt（简单策略：截断+去重行）

        生产环境中可以使用LLM来智能压缩，
        这里实现简单的规则压缩：
        1. 去除空行
        2. 去除重复的描述行
        3. 超出token上限时截断

        Args:
            system_prompt: 原始system prompt
            token_counter: token计数函数
            max_tokens: 目标最大token数

        Returns:
            压缩后的system prompt
        """
        # 去空行和重复行
        lines = system_prompt.strip().split("\n")
        seen = set()
        unique_lines = []

        for line in lines:
            stripped = line.strip()
            if stripped and stripped not in seen:
                seen.add(stripped)
                unique_lines.append(stripped)

        compressed = "\n".join(unique_lines)

        # 如果仍超出token限制，逐行截断
        while token_counter(compressed) > max_tokens and len(unique_lines) > 1:
            unique_lines.pop()  # 移除最后一行
            compressed = "\n".join(unique_lines)

        return compressed

    def estimate_request_cost(
        self,
        messages: List[Dict[str, str]],
        token_counter,
        price_per_million_input: float,
        price_per_million_output: float,
        expected_output_tokens: int = 500,
    ) -> Dict:
        """预估本次请求的完整费用

        Args:
            messages: 消息列表
            token_counter: token计数函数
            price_per_million_input: 输入价格（每百万token）
            price_per_million_output: 输出价格（每百万token）
            expected_output_tokens: 预期输出token数

        Returns:
            费用预估字典
        """
        # 计算输入token
        input_tokens = sum(
            token_counter(msg["content"]) + 3  # 格式开销
            for msg in messages
        )
        input_tokens += 3  # 回复预填充

        # 计算费用
        input_cost = (input_tokens / 1_000_000) * price_per_million_input
        output_cost = (expected_output_tokens / 1_000_000) * price_per_million_output

        return {
            "input_tokens": input_tokens,
            "output_tokens": expected_output_tokens,
            "total_tokens": input_tokens + expected_output_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": input_cost + output_cost,
        }


# --- 使用示例 ---
if __name__ == "__main__":
    # 简单的token计数函数（模拟）
    def simple_counter(text: str) -> int:
        """简单计数：中文1字=1.5token，英文1词=1token"""
        cn = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        en = len(text.split()) - cn
        return int(cn * 1.5 + en)

    optimizer = PromptOptimizer(max_context_tokens=2000)

    # 模拟一个很长的对话历史
    long_history = [
        {"role": "system", "content": "你是一个Python编程助手，帮助用户解答编程问题。"},
    ]
    for i in range(20):
        long_history.append({"role": "user", "content": f"这是第{i+1}轮的问题内容..."})
        long_history.append({"role": "assistant", "content": f"这是第{i+1}轮的回答内容..."})

    print(f"原始消息数: {len(long_history)}")
    total_tokens = sum(simple_counter(m["content"]) for m in long_history)
    print(f"原始总token: {total_tokens}")

    # 裁剪
    trimmed = optimizer.trim_history(long_history, simple_counter)
    trimmed_tokens = sum(simple_counter(m["content"]) for m in trimmed)
    print(f"\n裁剪后消息数: {len(trimmed)}")
    print(f"裁剪后总token: {trimmed_tokens}")
    print(f"节省token: {total_tokens - trimmed_tokens} ({(1-trimmed_tokens/total_tokens)*100:.0f}%)")
