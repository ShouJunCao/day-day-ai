"""
example_usage.py — RAG 管道完整演示
包含文档加载、分块、Prompt 构建、查询流程的演示。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag_pipeline import RAGPipeline, DocumentChunker, Document


def demo_chunking():
    """演示文档分块策略"""
    print("=" * 60)
    print("  文档分块 — Document Chunking 演示")
    print("=" * 60)

    # 创建分块器
    chunker = DocumentChunker(chunk_size=100, overlap=20)

    # 准备文档
    long_text = (
        "人工智能是计算机科学的一个分支，"
        "致力于开发能够模拟人类智能行为的系统。"
        "机器学习是 AI 的核心技术之一，"
        "通过从数据中学习来实现智能决策。"
        "深度学习是机器学习的子领域，"
        "使用多层神经网络来学习数据的复杂表示。"
        "自然语言处理是 AI 的重要应用方向，"
        "涉及文本理解、情感分析、机器翻译等任务。"
        "大语言模型的出现极大推动了 NLP 的发展。"
    )

    doc = Document(text=long_text, metadata={"source": "demo"}, doc_id="demo_001")
    chunks = chunker.chunk_document(doc)

    print(f"\n原始文档长度: {len(long_text)} 字符")
    print(f"分块参数: chunk_size={chunker.chunk_size}, overlap={chunker.overlap}")
    print(f"切分为 {len(chunks)} 个文本块\n")

    for i, chunk in enumerate(chunks):
        print(f"块 {i}: [{len(chunk.text)} 字符] {chunk.text[:40]}...")
        print(f"     元数据: {chunk.metadata}")


def demo_rag_pipeline():
    """演示完整 RAG 查询流程"""
    print("\n" + "=" * 60)
    print("  RAG 管道 — RAG Pipeline 演示")
    print("=" * 60)

    # 创建管道
    pipeline = RAGPipeline(chunk_size=150, chunk_overlap=20, top_k=2)

    # 加载文档
    docs = [
        "人工智能（AI）是计算机科学的一个分支，致力于开发能够模拟人类智能行为的系统。机器学习是 AI 的核心技术之一。",
        "深度学习是机器学习的子领域，使用多层神经网络来学习数据的复杂表示。Transformer 架构是重要突破。",
        "自然语言处理（NLP）是 AI 的重要应用方向，涉及文本理解、情感分析、机器翻译等任务。",
        "大语言模型（LLM）如 GPT、BERT 等，通过在大规模文本上预训练，学会了理解和生成自然语言。",
    ]
    metadata = [
        {"category": "AI基础"},
        {"category": "深度学习"},
        {"category": "NLP"},
        {"category": "LLM"},
    ]

    pipeline.load_documents(docs, metadata)

    print(f"\n加载了 {len(pipeline._documents)} 篇文档")
    print(f"切分为 {len(pipeline._chunks)} 个文本块")

    # 查询
    queries = ["什么是深度学习？", "AI 有哪些应用？"]

    for query in queries:
        print(f"\n{'=' * 40}")
        print(f"查询: {query}")
        print(f"{'=' * 40}")

        result = pipeline.query(query)
        print(f"检索到 {result['num_docs_retrieved']} 篇相关文档")
        print(f"\n检索到的上下文:")
        for i, ctx in enumerate(result["context"]):
            print(f"  [{i+1}] {ctx[:50]}...")

        print(f"\nPrompt 长度: {len(result['prompt'])} 字符")


def demo_comparison():
    """对比不同分块参数的效果"""
    print("\n" + "=" * 60)
    print("  分块参数对比 — Chunk Size Comparison")
    print("=" * 60)

    text = "这是一段测试文本。" * 20  # 200 字符

    print(f"\n{'分块大小':<12s} {'重叠':<8s} {'块数':<8s} {'平均每块':<12s}")
    print("-" * 45)

    configs = [
        (100, 0),
        (100, 20),
        (200, 0),
        (200, 40),
        (50, 10),
    ]

    for chunk_size, overlap in configs:
        chunker = DocumentChunker(chunk_size, overlap)
        doc = Document(text=text, doc_id="test")
        chunks = chunker.chunk_document(doc)
        avg_len = sum(len(c.text) for c in chunks) / len(chunks)
        print(f"{chunk_size:<12d} {overlap:<8d} {len(chunks):<8d} {avg_len:<12.1f}")


if __name__ == "__main__":
    demo_chunking()
    demo_rag_pipeline()
    demo_comparison()
