"""
example_usage.py — 多模态 RAG 完整演示
演示图片、表格、代码块的解析、提取和检索。
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from multimodal_rag import (
    MarkdownMultimodalParser,
    ImageContentExtractor,
    TableContentExtractor,
    MultimodalRetriever,
    MultimodalChunk,
    MultimodalContent,
    simple_embedding,
)


def demo_markdown_parser():
    """演示 Markdown 多模态解析"""
    print("=" * 60)
    print("  Markdown 多模态解析演示")
    print("=" * 60)

    parser = MarkdownMultimodalParser()

    test_md = """# 技术文档

## 概述

Transformer 架构由 Google 在 2017 年提出。

## 架构图

![Transformer 架构](https://example.com/transformer.png)

## 模型对比

| 模型 | 参数量 | 训练数据 | 用途 |
|------|--------|----------|------|
| BERT | 340M | Wikipedia | 理解 |
| GPT-3 | 175B | 网页数据 | 生成 |

## 示例代码

```python
import transformers

model = transformers.AutoModel.from_pretrained("bert-base")
```
"""

    fd, path = tempfile.mkstemp(suffix=".md")
    os.write(fd, test_md.encode("utf-8"))
    os.close(fd)

    text, multimodal = parser.parse(path)

    print(f"\n纯文本长度: {len(text)} 字符")
    print(f"多模态内容数: {len(multimodal)}")

    for content in multimodal:
        print(f"\n  [{content.content_type}] {content.content_id}")
        print(f"    内容: {content.content[:50]}...")
        if content.metadata:
            print(f"    元数据: {content.metadata}")

    os.unlink(path)


def demo_image_extraction():
    """演示图片内容提取"""
    print("\n" + "=" * 60)
    print("  图片内容提取演示")
    print("=" * 60)

    extractor = ImageContentExtractor()

    image_paths = [
        "/docs/images/transformer_architecture.png",
        "/docs/images/bert_fine_tuning.jpg",
    ]

    for img_path in image_paths:
        result = extractor.extract(img_path)
        print(f"\n图片: {os.path.basename(img_path)}")
        print(f"  OCR 文本: {result['ocr_text']}")
        print(f"  描述: {result['description']}")


def demo_table_extraction():
    """演示表格内容提取"""
    print("\n" + "=" * 60)
    print("  表格内容提取演示")
    print("=" * 60)

    extractor = TableContentExtractor()

    table_md = """| 模型 | 参数量 | 训练数据 | 用途 |
|------|--------|----------|------|
| BERT | 340M | Wikipedia | 理解 |
| GPT-3 | 175B | 网页数据 | 生成 |
| T5 | 11B | C4 | 多任务 |"""

    result = extractor.extract(table_md)

    print(f"\n表头: {result['headers']}")
    print(f"数据行数: {len(result['data'])}")
    print(f"摘要: {result['summary']}")
    print(f"\n数据:")
    for row in result['data']:
        print(f"  {row}")


def demo_multimodal_retrieval():
    """演示多模态检索"""
    print("\n" + "=" * 60)
    print("  多模态检索演示")
    print("=" * 60)

    parser = MarkdownMultimodalParser()
    retriever = MultimodalRetriever(embedding_fn=simple_embedding)

    test_docs = [
        """# Transformer 架构

Transformer 基于自注意力机制。

![注意力机制](attn.png)

| 组件 | 功能 |
|------|------|
| 自注意力 | 捕捉依赖关系 |
| 前馈网络 | 非线性变换 |

```python
class Transformer(nn.Module):
    pass
```
""",
        """# BERT 模型

BERT 基于 Transformer Encoder。

| 模型 | 参数量 |
|------|--------|
| BERT-base | 110M |
| BERT-large | 340M |
""",
    ]

    for i, md_content in enumerate(test_docs):
        fd, path = tempfile.mkstemp(suffix=".md")
        os.write(fd, md_content.encode("utf-8"))
        os.close(fd)

        text, multimodal = parser.parse(path)

        chunk = MultimodalChunk(
            chunk_id=f"doc_{i}",
            text=text,
            multimodal_contents=multimodal,
        )
        retriever.add_chunk(chunk)

        os.unlink(path)

    queries = [
        "Transformer 的组件有哪些？",
        "BERT 的参数量是多少？",
    ]

    for query in queries:
        print(f"\n查询: {query}")
        results = retriever.search(query, top_k=2)

        for r in results:
            print(f"  分数: {r.score:.3f}")
            print(f"  文本: {r.text[:50]}...")
            if r.images:
                print(f"  图片: {r.images}")
            if r.tables:
                print(f"  表格: {r.tables[0][:60]}...")
            if r.codes:
                print(f"  代码: {r.codes[0][:60]}...")


def demo_summary():
    """多模态 RAG 总结"""
    print("\n" + "=" * 60)
    print("  多模态 RAG 总结")
    print("=" * 60)

    print(f"\n{'内容类型':<15s} {'提取方法':<20s} {'检索方式':<20s}")
    print("-" * 55)
    print(f"{'图片':<15s} {'OCR + 视觉描述':<20s} {'描述文本向量':<20s}")
    print(f"{'表格':<15s} {'结构解析 + 摘要':<20s} {'摘要文本向量':<20s}")
    print(f"{'代码块':<15s} {'语言识别 + 内容':<20s} {'代码文本向量':<20s}")
    print(f"{'纯文本':<15s} {'Markdown 清理':<20s} {'文本向量':<20s}")


if __name__ == "__main__":
    demo_markdown_parser()
    demo_image_extraction()
    demo_table_extraction()
    demo_multimodal_retrieval()
    demo_summary()
