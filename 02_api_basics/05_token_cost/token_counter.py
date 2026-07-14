"""
Token计数工具 - 使用tiktoken精确计算token数量

在大模型API中，计费的基本单位是token而非字符。
不同的模型使用不同的tokenizer，本模块封装了tiktoken库，
支持多种模型的token计数。

核心概念：
    - 1个中文汉字 ≈ 1-2个token（取决于模型和tokenizer）
    - 1个英文单词 ≈ 1-1.5个token
    - 不同模型的tokenizer不同，同一段文字的token数可能不同

用法：
    counter = TokenCounter()
    count = counter.count_tokens("你好，世界", model="gpt-4o")
    print(f"Token数: {count}")
"""

import tiktoken
from typing import List, Dict, Optional


class TokenCounter:
    """Token计数器 - 支持多种模型的token计数

    封装tiktoken库，提供：
    1. 单条文本的token计数
    2. 消息列表的token计数（包含角色标记的额外开销）
    3. 中英文混合文本的token分析

    Attributes:
        encoders: 缓存的tokenizer实例（避免重复加载）
    """

    # 模型到tokenizer编码的映射
    MODEL_ENCODINGS: Dict[str, str] = {
        "gpt-4o": "o200k_base",
        "gpt-4o-mini": "o200k_base",
        "gpt-4": "cl100k_base",
        "gpt-4-turbo": "cl100k_base",
        "gpt-3.5-turbo": "cl100k_base",
        "deepseek-chat": "cl100k_base",  # 近似使用cl100k
        "qwen-plus": "cl100k_base",      # 近似使用cl100k
    }

    def __init__(self):
        """初始化Token计数器"""
        self.encoders: Dict[str, tiktoken.Encoding] = {}

    def _get_encoder(self, model: str) -> tiktoken.Encoding:
        """获取或创建指定模型的tokenizer

        使用缓存避免重复加载tokenizer（加载操作较慢）。

        Args:
            model: 模型名称

        Returns:
            tiktoken编码器实例
        """
        # 检查缓存
        if model in self.encoders:
            return self.encoders[model]

        # 查找对应的encoding名称
        encoding_name = self.MODEL_ENCODINGS.get(model, "cl100k_base")

        # 创建并缓存
        encoder = tiktoken.get_encoding(encoding_name)
        self.encoders[model] = encoder
        return encoder

    def count_tokens(
        self,
        text: str,
        model: str = "gpt-4o-mini",
    ) -> int:
        """计算文本的token数量

        Args:
            text: 待计数的文本
            model: 模型名称（不同模型tokenizer不同）

        Returns:
            token数量
        """
        encoder = self._get_encoder(model)
        tokens = encoder.encode(text)
        return len(tokens)

    def count_messages(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o-mini",
    ) -> int:
        """计算消息列表的token数量（包含格式开销）

        OpenAI API的消息格式会额外消耗token：
        - 每条消息约3个token（角色标记 + 分隔符）
        - 系统提示词额外消耗
        - 回复预填充约3个token

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            model: 模型名称

        Returns:
            总token数量（包含格式开销）
        """
        encoder = self._get_encoder(model)

        # 每条消息的格式开销（role标记 + 分隔符）
        tokens_per_message = 3
        tokens_per_name = 1

        total = 0
        for message in messages:
            # 消息格式开销
            total += tokens_per_message

            # 角色名
            total += len(encoder.encode(message["role"]))

            # 消息内容
            total += len(encoder.encode(message["content"]))

            # 如果有name字段
            if "name" in message:
                total += tokens_per_name
                total += len(encoder.encode(message["name"]))

        # 回复预填充
        total += 3

        return total

    def analyze_text(self, text: str, model: str = "gpt-4o-mini") -> Dict:
        """分析文本的token构成

        返回详细的token统计信息，包括：
        - 总token数
        - 字符数
        - 平均每个token对应的字符数

        Args:
            text: 待分析的文本
            model: 模型名称

        Returns:
            包含统计信息的字典
        """
        token_count = self.count_tokens(text, model)
        char_count = len(text)
        chinese_count = sum(
            1 for c in text if '\u4e00' <= c <= '\u9fff'
        )

        return {
            "token_count": token_count,
            "char_count": char_count,
            "chinese_char_count": chinese_count,
            "chars_per_token": round(char_count / max(token_count, 1), 2),
            "model": model,
        }


# --- 使用示例 ---
if __name__ == "__main__":
    counter = TokenCounter()

    # 示例1：中英文token计数对比
    texts = [
        "Hello, how are you?",
        "你好，最近怎么样？",
        "The quick brown fox jumps over the lazy dog.",
        "人工智能正在改变我们的生活方式。",
    ]

    print("=" * 50)
    print("Token计数对比")
    print("=" * 50)

    for text in texts:
        result = counter.analyze_text(text, model="gpt-4o-mini")
        print(f"\n文本: {text}")
        print(f"  Token数: {result['token_count']}")
        print(f"  字符数: {result['char_count']}")
        print(f"  中文字符: {result['chinese_char_count']}")
        print(f"  字符/Token比: {result['chars_per_token']}")

    # 示例2：消息列表token计数
    messages = [
        {"role": "system", "content": "你是一个专业的Python编程助手。"},
        {"role": "user", "content": "什么是装饰器？"},
    ]

    total = counter.count_messages(messages, model="gpt-4o-mini")
    print(f"\n\n消息列表总Token数: {total}")
