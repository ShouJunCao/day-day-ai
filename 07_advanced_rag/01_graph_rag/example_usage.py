"""
example_usage.py — Graph RAG 完整演示
演示知识图谱构建、社区检测和 Graph RAG 查询流程。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph_rag import (
    KnowledgeGraphBuilder,
    GraphRAGQueryEngine,
    GraphRAGResult,
    Entity,
    Relationship,
    Community,
)


def demo_graph_building():
    """演示知识图谱构建"""
    print("=" * 60)
    print("  知识图谱构建演示")
    print("=" * 60)

    builder = KnowledgeGraphBuilder()

    documents = [
        "Transformer 是一种基于自注意力机制的深度学习架构。Google 提出了 Transformer 模型。",
        "BERT 是基于 Transformer Encoder 的预训练模型。Google 开发了 BERT。",
        "GPT 是基于 Transformer Decoder 的模型。OpenAI 开发了 GPT 系列。",
        "RAG 结合了检索和生成。Microsoft 提出了 Graph RAG。",
        "注意力机制是 Transformer 的核心组件。自注意力机制能够捕捉长程依赖。",
    ]

    stats = builder.build(documents)

    print(f"\n构建结果:")
    print(f"  实体: {stats['num_entities']} 个")
    print(f"  关系: {stats['num_relationships']} 个")
    print(f"  社区: {stats['num_communities']} 个")
    print(f"  节点: {stats['num_nodes']} 个")
    print(f"  边: {stats['num_edges']} 条")

    print(f"\n提取的实体:")
    for name, entity in builder.entities.items():
        print(f"  • {name} ({entity.entity_type})")

    print(f"\n提取的关系 (前 5 个):")
    for rel in builder.relationships[:5]:
        print(f"  • {rel.source} ↔ {rel.target}: {rel.description}")


def demo_community_detection():
    """演示社区检测"""
    print("\n" + "=" * 60)
    print("  社区检测演示")
    print("=" * 60)

    builder = KnowledgeGraphBuilder()
    builder.build([
        "Transformer 是 Google 提出的架构。",
        "BERT 是 Google 开发的预训练模型。",
        "GPT 是 OpenAI 开发的生成模型。",
        "RAG 是 Microsoft 提出的检索增强生成框架。",
        "注意力机制是 Transformer 的核心。",
    ])

    print(f"\n社区检测结果:")
    for comm in builder.communities:
        print(f"  社区 {comm.community_id}: {comm.summary}")
        print(f"    实体: {', '.join(comm.entities)}")


def demo_query_engine():
    """演示 Graph RAG 查询"""
    print("\n" + "=" * 60)
    print("  Graph RAG 查询引擎演示")
    print("=" * 60)

    builder = KnowledgeGraphBuilder()
    builder.build([
        "Transformer 是一种基于自注意力机制的深度学习架构。Google 提出了 Transformer 模型。",
        "BERT 是基于 Transformer Encoder 的预训练模型。Google 开发了 BERT。",
        "GPT 是基于 Transformer Decoder 的模型。OpenAI 开发了 GPT 系列。",
        "RAG 结合了检索和生成。Microsoft 提出了 Graph RAG。",
        "注意力机制是 Transformer 的核心组件。自注意力机制能够捕捉长程依赖。",
    ])

    engine = GraphRAGQueryEngine(builder)

    questions = [
        "Transformer 和 BERT 的关系是什么？",
        "GPT 是谁开发的？",
        "Graph RAG 是什么？",
    ]

    for q in questions:
        result = engine.query(q)
        print(f"\n查询: {q}")
        print(f"  相关实体: {result.entities_used}")
        print(f"  相关社区: {result.communities_used}")
        print(f"  置信度: {result.confidence:.2f}")
        print(f"  回答: {result.answer}")


def demo_comparison():
    """对比 Graph RAG 与传统 RAG"""
    print("\n" + "=" * 60)
    print("  Graph RAG vs 传统 RAG")
    print("=" * 60)

    print(f"\n{'维度':<20s} {'传统 RAG':<20s} {'Graph RAG':<20s}")
    print("-" * 60)
    print(f"{'检索方式':<20s} {'向量相似度':<20s} {'图谱遍历+向量'}")
    print(f"{'上下文构建':<20s} {'Top-K 文档':<20s} {'实体+关系+社区'}")
    print(f"{'全局理解':<20s} {'弱（局部匹配）':<20s} {'强（全局结构）'}")
    print(f"{'复杂查询':<20s} {'一般':<20s} {'优秀'}")
    print(f"{'计算开销':<20s} {'低':<20s} {'高（图谱构建）'}")
    print(f"{'适用场景':<20s} {'文档问答':<20s} {'综合分析/摘要'}")


if __name__ == "__main__":
    demo_graph_building()
    demo_community_detection()
    demo_query_engine()
    demo_comparison()
