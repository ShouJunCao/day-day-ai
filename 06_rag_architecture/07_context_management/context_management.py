"""
context_management.py — 上下文管理技术实现
包含上下文压缩、上下文过滤、Lost in the Middle 处理。
"""
import os
import math
from typing import Optional, List, Tuple
from dataclasses import dataclass, field


# ============================================================
# 模块：上下文数据结构
# ============================================================

@dataclass
class Context:
    """
    上下文数据结构。

    属性：
    - documents (list[str]): 检索到的文档列表
    - query (str): 用户查询
    - max_tokens (int): 最大 Token 数
    """
    documents: List[str]
    query: str
    max_tokens: int = 4096


# ============================================================
# 策略 1：上下文压缩（LLMLingua 简化版）
# ============================================================

class ContextCompressor:
    """
    上下文压缩器：使用语言模型 perplexity 或启发式方法压缩上下文。

    原理：
    1. 计算每个文档/句子的信息量（perplexity 或 TF-IDF）
    2. 保留高信息量内容，删除冗余和低价值内容
    3. 在保持语义完整性的同时减少 Token 数
    """

    def __init__(self, compression_ratio: float = 0.5):
        """
        初始化压缩器。

        参数：
        - compression_ratio (float): 压缩比例（0.5 表示保留 50%）
        """
        self.compression_ratio = compression_ratio

    def compress(self, context: Context) -> Context:
        """
        压缩上下文。

        参数：
        - context (Context): 原始上下文

        返回：
        - Context: 压缩后的上下文
        """
        compressed_docs = []
        for doc in context.documents:
            # 简化实现：按句子分割，保留重要句子
            sentences = self._split_sentences(doc)
            important_sentences = self._select_important_sentences(
                sentences, context.query
            )
            compressed_docs.append(" ".join(important_sentences))

        return Context(
            documents=compressed_docs,
            query=context.query,
            max_tokens=context.max_tokens,
        )

    def _split_sentences(self, text: str) -> List[str]:
        """将文本分割为句子"""
        import re
        return re.split(r'(?<=[。！？.!?])\s*', text)

    def _select_important_sentences(self, sentences: List[str], query: str) -> List[str]:
        """选择重要句子（简化版：基于关键词匹配）"""
        if not sentences:
            return []

        query_words = set(query.replace(" ", ""))
        scored_sentences = []

        for sent in sentences:
            sent_words = set(sent.replace(" ", ""))
            # 计算与查询的重叠度
            overlap = len(query_words & sent_words) / max(len(query_words), 1)
            scored_sentences.append((sent, overlap))

        # 按分数排序，保留 top 比例
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        keep_count = max(1, int(len(sentences) * self.compression_ratio))

        # 恢复原始顺序
        selected = [s for s, _ in scored_sentences[:keep_count]]
        # 简单排序：按原文档顺序
        return [s for s in sentences if s in selected]


# ============================================================
# 策略 2：上下文过滤
# ============================================================

class ContextFilter:
    """
    上下文过滤器：基于相关性阈值过滤检索结果。

    原理：
    1. 计算每个文档与查询的相关性分数
    2. 过滤掉低于阈值的文档
    3. 只保留高相关性文档进入 Prompt
    """

    def __init__(self, threshold: float = 0.6):
        """
        初始化过滤器。

        参数：
        - threshold (float): 相关性阈值
        """
        self.threshold = threshold

    def filter(self, context: Context, scores: List[float]) -> Context:
        """
        过滤上下文。

        参数：
        - context (Context): 原始上下文
        - scores (list[float]): 每个文档的相关性分数

        返回：
        - Context: 过滤后的上下文
        """
        filtered_docs = []
        for doc, score in zip(context.documents, scores):
            if score >= self.threshold:
                filtered_docs.append(doc)

        return Context(
            documents=filtered_docs,
            query=context.query,
            max_tokens=context.max_tokens,
        )


# ============================================================
# 策略 3：Lost in the Middle 处理
# ============================================================

class LostInTheMiddleHandler:
    """
    Lost in the Middle 处理器：解决长上下文中部信息丢失问题。

    原理：
    研究表明，LLM 在处理长上下文时，容易忽略中间部分的信息。
    解决策略：
    1. 重新排序文档：将最相关的文档放在开头和结尾
    2. 分段摘要：对中间部分生成摘要
    3. 分块处理：将长上下文拆分为多个块分别处理
    """

    def __init__(self, strategy: str = "reorder"):
        """
        初始化处理器。

        参数：
        - strategy (str): 处理策略
            - "reorder": 重新排序（最相关放首尾）
            - "summarize": 分段摘要
            - "chunk": 分块处理
        """
        self.strategy = strategy

    def handle(self, context: Context, relevance_scores: List[float]) -> Context:
        """
        处理 Lost in the Middle 问题。

        参数：
        - context (Context): 原始上下文
        - relevance_scores (list[float]): 相关性分数

        返回：
        - Context: 处理后的上下文
        """
        if self.strategy == "reorder":
            return self._reorder(context, relevance_scores)
        elif self.strategy == "summarize":
            return self._summarize(context)
        elif self.strategy == "chunk":
            return self._chunk(context)
        else:
            return context

    def _reorder(self, context: Context, scores: List[float]) -> Context:
        """重新排序：将最相关的文档放在开头和结尾"""
        if not context.documents:
            return context

        # 按相关性排序
        paired = list(zip(context.documents, scores))
        paired.sort(key=lambda x: x[1], reverse=True)

        # 交错放置：高相关性放两端
        reordered_docs = []
        left, right = 0, len(paired) - 1
        while left <= right:
            if left == right:
                reordered_docs.append(paired[left][0])
            else:
                reordered_docs.append(paired[left][0])
                reordered_docs.append(paired[right][0])
            left += 1
            right -= 1

        return Context(
            documents=reordered_docs,
            query=context.query,
            max_tokens=context.max_tokens,
        )

    def _summarize(self, context: Context) -> Context:
        """分段摘要（占位实现）"""
        summarized = []
        for doc in context.documents:
            # 实际项目中调用 LLM 生成摘要
            summarized.append(f"[摘要] {doc[:50]}...")
        return Context(
            documents=summarized,
            query=context.query,
            max_tokens=context.max_tokens,
        )

    def _chunk(self, context: Context) -> Context:
        """分块处理（占位实现）"""
        return context


# ============================================================
# 模块：统一上下文管理调度器
# ============================================================

class ContextManager:
    """
    统一上下文管理调度器：组合压缩、过滤、Lost in the Middle 处理。
    """

    def __init__(
        self,
        compress: bool = True,
        filter: bool = True,
        handle_litm: bool = True,
    ):
        self.compressor = ContextCompressor() if compress else None
        self.filter = ContextFilter() if filter else None
        self.litm_handler = LostInTheMiddleHandler() if handle_litm else None

    def process(self, context: Context, scores: Optional[List[float]] = None) -> Context:
        """
        处理上下文。

        参数：
        - context (Context): 原始上下文
        - scores (list[float]): 相关性分数（用于过滤和重排序）

        返回：
        - Context: 处理后的上下文
        """
        if scores is None:
            scores = [0.5] * len(context.documents)

        # 1. 过滤
        if self.filter:
            context = self.filter.filter(context, scores)

        # 2. 压缩
        if self.compressor:
            context = self.compressor.compress(context)

        # 3. 处理 Lost in the Middle
        if self.litm_handler:
            context = self.litm_handler.handle(context, scores)

        return context


if __name__ == "__main__":
    print("=" * 60)
    print("  上下文管理技术演示")
    print("=" * 60)

    # 模拟上下文
    docs = [
        "Transformer 是一种基于自注意力机制的深度学习架构。它由编码器和解码器组成。",
        "BERT 是基于 Transformer Encoder 的预训练语言模型。它在多个 NLP 任务上取得了 SOTA。",
        "GPT 系列模型是基于 Transformer Decoder 的自回归语言模型。",
        "自然语言处理是人工智能的重要分支，涉及文本理解、生成、翻译等任务。",
        "卷积神经网络主要用于图像处理和计算机视觉任务，如目标检测和图像分类。",
    ]

    scores = [0.9, 0.8, 0.7, 0.4, 0.2]
    query = "Transformer 和 BERT 的关系是什么？"
    context = Context(documents=docs, query=query)

    manager = ContextManager(compress=True, filter=True, handle_litm=True)
    result = manager.process(context, scores)

    print(f"\n原始文档数: {len(docs)}")
    print(f"过滤 + 压缩 + 重排序后文档数: {len(result.documents)}")
    print(f"\n处理后的上下文:")
    for i, doc in enumerate(result.documents, 1):
        print(f"  [{i}] {doc}")
