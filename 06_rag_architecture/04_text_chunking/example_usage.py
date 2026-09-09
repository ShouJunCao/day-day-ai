"""
example_usage.py — 文本分块策略完整演示
演示固定长度、语义、递归、Sentence Window 四种分块策略。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from text_chunking import (
    FixedSizeChunker,
    SemanticChunker,
    RecursiveChunker,
    SentenceWindowChunker,
    ChunkingScheduler,
    Chunk,
)

# 示例文本
SAMPLE_TEXT = """
人工智能是计算机科学的一个分支，致力于开发能够模拟人类智能行为的系统。机器学习是 AI 的核心技术之一，通过从数据中学习来实现智能决策。

深度学习是机器学习的子领域，使用多层神经网络来学习数据的复杂表示。Transformer 架构是近年来最重要的深度学习突破之一。

自然语言处理是 AI 的重要应用方向，涉及文本理解、情感分析、机器翻译等任务。大语言模型的出现极大推动了 NLP 的发展。

在 RAG 系统中，文本分块是关键的预处理步骤。分块质量直接影响 Embedding 的效果和检索的准确性。不同的分块策略适用于不同的场景。

固定长度分块实现简单但不考虑语义边界。语义分块在语义转折点切分。递归分块按层次结构逐步细化。Sentence Window 保留核心句子的上下文。
"""


def demo_fixed_size():
    """演示固定长度分块"""
    print("=" * 60)
    print("  固定长度分块 — Fixed Size Chunking")
    print("=" * 60)

    chunker = FixedSizeChunker(chunk_size=100, overlap=20)
    chunks = chunker.chunk(SAMPLE_TEXT.strip())

    print(f"\n参数: chunk_size={chunker.chunk_size}, overlap={chunker.overlap}")
    print(f"块数: {len(chunks)}")

    for i, chunk in enumerate(chunks[:3]):
        print(f"\n块 {i}: [{chunk.char_count} 字符]")
        print(f"  {chunk.text[:60]}...")


def demo_semantic():
    """演示语义分块"""
    print("\n" + "=" * 60)
    print("  语义分块 — Semantic Chunking")
    print("=" * 60)

    chunker = SemanticChunker(chunk_size=100, overlap=20)
    chunks = chunker.chunk(SAMPLE_TEXT.strip())

    print(f"\n参数: chunk_size={chunker.chunk_size}, overlap={chunker.overlap}")
    print(f"块数: {len(chunks)}")

    for i, chunk in enumerate(chunks[:3]):
        print(f"\n块 {i}: [{chunk.char_count} 字符, {chunk.metadata.get('num_sentences', 0)} 句]")
        print(f"  {chunk.text[:60]}...")


def demo_recursive():
    """演示递归分块"""
    print("\n" + "=" * 60)
    print("  递归分块 — Recursive Chunking")
    print("=" * 60)

    chunker = RecursiveChunker(chunk_size=100, overlap=20)
    chunks = chunker.chunk(SAMPLE_TEXT.strip())

    print(f"\n参数: chunk_size={chunker.chunk_size}, overlap={chunker.overlap}")
    print(f"块数: {len(chunks)}")

    for i, chunk in enumerate(chunks[:3]):
        sep = chunk.metadata.get("separator", "N/A")
        print(f"\n块 {i}: [{chunk.char_count} 字符, 分隔符: {sep}]")
        print(f"  {chunk.text[:60]}...")


def demo_sentence_window():
    """演示 Sentence Window 分块"""
    print("\n" + "=" * 60)
    print("  Sentence Window 分块")
    print("=" * 60)

    chunker = SentenceWindowChunker(window_size=2)
    chunks = chunker.chunk(SAMPLE_TEXT.strip())

    print(f"\n参数: window_size={chunker.window_size}")
    print(f"块数: {len(chunks)}")

    # 显示前 3 个块
    for i, chunk in enumerate(chunks[:3]):
        core = chunk.metadata.get("core_sentence", "")[:30]
        print(f"\n块 {i}: 核心句={core}...")
        print(f"  上下文: {chunk.text[:60]}...")


def demo_comparison():
    """对比所有分块策略"""
    print("\n" + "=" * 60)
    print("  分块策略对比")
    print("=" * 60)

    results = ChunkingScheduler.compare_strategies(SAMPLE_TEXT.strip(), chunk_size=100)

    print(f"\n{'策略':<20s} {'块数':>6s} {'平均长度':>10s} {'最小':>6s} {'最大':>6s}")
    print("-" * 55)
    for name, stats in results.items():
        print(f"{name:<20s} {stats['num_chunks']:>6d} {stats['avg_length']:>10.1f} "
              f"{stats['min_length']:>6d} {stats['max_length']:>6d}")


if __name__ == "__main__":
    demo_fixed_size()
    demo_semantic()
    demo_recursive()
    demo_sentence_window()
    demo_comparison()
