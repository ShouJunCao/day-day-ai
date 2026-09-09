"""
example_usage.py — 上下文管理技术完整演示
演示上下文压缩、过滤、Lost in the Middle 处理。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from context_management import (
    Context,
    ContextCompressor,
    ContextFilter,
    LostInTheMiddleHandler,
    ContextManager,
)


def demo_context_compression():
    """演示上下文压缩"""
    print("=" * 60)
    print("  上下文压缩 — Context Compression")
    print("=" * 60)

    compressor = ContextCompressor(compression_ratio=0.5)

    docs = [
        "Transformer 是一种基于自注意力机制的深度学习架构，由 Vaswani 等人在 2017 年提出。它由编码器和解码器组成，通过多头自注意力机制捕捉序列中的长程依赖关系。",
        "BERT 是 Google 在 2018 年提出的预训练语言模型，基于 Transformer Encoder。它通过 MLM 和 NSP 两个任务进行预训练，在多个 NLP 下游任务上取得了 SOTA 结果。",
        "自然语言处理是人工智能的重要分支，涉及文本理解、情感分析、机器翻译、文本生成等任务。近年来，随着大语言模型的发展，NLP 技术取得了突破性进展。",
    ]

    query = "BERT 模型的特点是什么？"
    context = Context(documents=docs, query=query)

    compressed = compressor.compress(context)

    print(f"\n原始文档数: {len(docs)}")
    print(f"压缩后文档数: {len(compressed.documents)}")
    print(f"压缩率: {compressor.compression_ratio}")

    print(f"\n压缩后的文档:")
    for i, doc in enumerate(compressed.documents, 1):
        print(f"  [{i}] {doc}")


def demo_context_filtering():
    """演示上下文过滤"""
    print("\n" + "=" * 60)
    print("  上下文过滤 — Context Filtering")
    print("=" * 60)

    filter = ContextFilter(threshold=0.6)

    docs = [
        "Transformer 是一种基于自注意力机制的深度学习架构",
        "BERT 是基于 Transformer Encoder 的预训练语言模型",
        "GPT 是基于 Transformer Decoder 的自回归语言模型",
        "卷积神经网络主要用于图像处理",
    ]

    scores = [0.9, 0.85, 0.7, 0.2]
    context = Context(documents=docs, query="Transformer 相关模型")

    filtered = filter.filter(context, scores)

    print(f"\n原始文档数: {len(docs)}")
    print(f"阈值: {filter.threshold}")
    print(f"过滤后文档数: {len(filtered.documents)}")

    print(f"\n保留的文档:")
    for i, doc in enumerate(filtered.documents, 1):
        print(f"  [{i}] {doc}")


def demo_lost_in_the_middle():
    """演示 Lost in the Middle 处理"""
    print("\n" + "=" * 60)
    print("  Lost in the Middle 处理")
    print("=" * 60)

    docs = [
        "文档 A（最相关）：Transformer 架构详解",
        "文档 B（较相关）：BERT 预训练方法",
        "文档 C（一般相关）：GPT 生成模型",
        "文档 D（不相关）：CNN 图像处理",
        "文档 E（较相关）：注意力机制原理",
    ]

    scores = [0.95, 0.8, 0.6, 0.1, 0.75]
    query = "Transformer 和注意力机制"
    context = Context(documents=docs, query=query)

    # 策略 1：重新排序
    reorder_handler = LostInTheMiddleHandler(strategy="reorder")
    reordered = reorder_handler.handle(context, scores)

    print(f"\n原始顺序:")
    for i, doc in enumerate(docs, 1):
        print(f"  [{i}] {doc} (分数:{scores[i-1]:.2f})")

    print(f"\n重排序后（最相关放首尾）:")
    for i, doc in enumerate(reordered.documents, 1):
        print(f"  [{i}] {doc}")


def demo_full_pipeline():
    """演示完整流水线"""
    print("\n" + "=" * 60)
    print("  完整上下文管理流水线")
    print("=" * 60)

    docs = [
        "Transformer 是一种基于自注意力机制的深度学习架构。它由编码器和解码器组成，通过多头自注意力机制捕捉序列中的长程依赖关系。",
        "BERT 是基于 Transformer Encoder 的预训练语言模型。它通过 MLM 和 NSP 两个任务进行预训练。",
        "GPT 是基于 Transformer Decoder 的自回归语言模型。",
        "自然语言处理是人工智能的重要分支，涉及文本理解等任务。",
        "卷积神经网络主要用于图像处理任务。",
    ]

    scores = [0.9, 0.85, 0.7, 0.3, 0.1]
    query = "Transformer 和 BERT 的关系是什么？"
    context = Context(documents=docs, query=query)

    print(f"\n原始文档数: {len(docs)}")
    print(f"查询: {query}")

    manager = ContextManager(compress=True, filter=True, handle_litm=True)
    result = manager.process(context, scores)

    print(f"\n处理后文档数: {len(result.documents)}")
    print(f"\n处理后的上下文:")
    for i, doc in enumerate(result.documents, 1):
        print(f"  [{i}] {doc[:60]}...")


if __name__ == "__main__":
    demo_context_compression()
    demo_context_filtering()
    demo_lost_in_the_middle()
    demo_full_pipeline()
