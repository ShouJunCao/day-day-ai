"""
example_usage.py — 企业知识库问答系统完整演示
演示文档导入、分块、检索、重排序、上下文管理和问答的完整流程。
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from knowledge_base_qa import (
    DocumentParser,
    TextChunker,
    KnowledgeBaseQA,
    simple_embedding,
)


def demo_document_parser():
    """演示文档解析"""
    print("=" * 60)
    print("  步骤 1：文档解析")
    print("=" * 60)

    # 创建测试文件
    fd, path = tempfile.mkstemp(suffix=".md")
    content = """# RAG 技术指南

## 什么是 RAG

RAG（检索增强生成）是一种结合检索和生成的技术。

## RAG 的优势

1. 减少幻觉：基于真实数据生成
2. 实时更新：无需重新训练模型
3. 可溯源：每个回答都可以追溯到来源

> RAG 是当前最实用的 LLM 应用架构。
"""
    os.write(fd, content.encode("utf-8"))
    os.close(fd)

    doc = DocumentParser.parse(path)
    if doc:
        print(f"\n文件: {os.path.basename(path)}")
        print(f"格式: {doc.metadata['format']}")
        print(f"长度: {doc.metadata['length']} 字符")
        print(f"\n解析后的文本:")
        print(f"  {doc.text[:100]}...")

    os.unlink(path)


def demo_text_chunking():
    """演示文本分块"""
    print("\n" + "=" * 60)
    print("  步骤 2：文本分块")
    print("=" * 60)

    from knowledge_base_qa import Document

    doc = Document(
        doc_id="test_doc",
        text="RAG 是一种结合检索和生成的技术。"
             "它首先从知识库中检索相关文档。"
             "然后将检索到的文档作为上下文提供给 LLM。"
             "最后 LLM 基于上下文生成回答。"
             "这种方法可以有效减少 LLM 的幻觉问题。",
        source="test.txt",
    )

    chunker = TextChunker(chunk_size=50, overlap=10)
    chunks = chunker.chunk(doc)

    print(f"\n原始文本: {len(doc.text)} 字符")
    print(f"分块数: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"  块 {i}: [{len(chunk.text)} 字符] {chunk.text[:30]}...")


def demo_full_system():
    """演示完整系统"""
    print("\n" + "=" * 60)
    print("  步骤 3：完整知识库问答系统")
    print("=" * 60)

    # 创建测试文档
    test_docs = []
    test_data = [
        ("doc_1.txt", "Transformer 是一种基于自注意力机制的深度学习架构。它由编码器和解码器组成，能够捕捉序列中的长程依赖关系。"),
        ("doc_2.md", "# BERT 模型\n\nBERT 是基于 Transformer Encoder 的预训练语言模型。它通过 MLM 和 NSP 任务进行预训练。"),
        ("doc_3.txt", "GPT 是基于 Transformer Decoder 的自回归语言模型。它能够生成连贯的文本。"),
    ]

    for name, content in test_data:
        fd, path = tempfile.mkstemp(suffix=f".{name.split('.')[1]}")
        os.write(fd, content.encode("utf-8"))
        os.close(fd)
        test_docs.append(path)

    # 初始化系统
    kb = KnowledgeBaseQA(embedding_fn=simple_embedding)

    # 导入文档
    kb.ingest(test_docs)

    # 查询
    questions = [
        "Transformer 的架构是什么？",
        "BERT 是什么？",
        "GPT 能做什么？",
    ]

    for q in questions:
        print(f"\n{'-' * 40}")
        print(f"问题: {q}")
        answer = kb.query(q)
        print(f"回答: {answer}")

    # 统计信息
    stats = kb.get_stats()
    print(f"\n{'=' * 40}")
    print(f"知识库统计:")
    print(f"  文档数: {stats['documents']}")
    print(f"  文本块数: {stats['chunks']}")
    print(f"  总字符数: {stats['total_chars']}")

    # 清理
    for path in test_docs:
        os.unlink(path)


if __name__ == "__main__":
    demo_document_parser()
    demo_text_chunking()
    demo_full_system()
