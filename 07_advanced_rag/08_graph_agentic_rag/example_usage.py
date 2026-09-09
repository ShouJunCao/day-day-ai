"""
example_usage.py — Graph + Agentic RAG 综合实战演示
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph_agentic_rag import (
    KnowledgeGraph, Entity, Relation,
    AgentRouter,
    VectorIndex, Document,
    GraphAgenticRAG,
    simple_embedding,
)


def demo_full_system():
    """演示完整系统"""
    print("=" * 60)
    print("  Graph + Agentic RAG 综合实战演示")
    print("=" * 60)

    # 1. 知识图谱
    graph = KnowledgeGraph()
    graph.add_entity(Entity("e1", "Transformer", "technology", "深度学习架构"))
    graph.add_entity(Entity("e2", "BERT", "model", "预训练语言模型"))
    graph.add_entity(Entity("e3", "GPT", "model", "生成式预训练模型"))
    graph.add_entity(Entity("e4", "自注意力", "concept", "核心机制"))
    graph.add_entity(Entity("e5", "RNN", "technology", "循环神经网络"))
    graph.add_relation(Relation("e2", "e4", "使用"))
    graph.add_relation(Relation("e3", "e4", "使用"))
    graph.add_relation(Relation("e2", "e1", "基于"))
    graph.add_relation(Relation("e3", "e1", "基于"))
    graph.add_relation(Relation("e1", "e5", "替代"))

    print("\n📊 知识图谱:")
    print(f"  实体数: {len(graph.entities)}")
    print(f"  关系数: {len(graph.relations)}")

    # 2. 向量索引
    vector_index = VectorIndex(simple_embedding)
    docs = [
        Document("d1", "Transformer 是一种基于自注意力的深度学习架构"),
        Document("d2", "BERT 是基于 Transformer 的预训练模型"),
        Document("d3", "GPT 是生成式预训练模型"),
    ]
    for doc in docs:
        vector_index.add_document(doc)

    print(f"\n📚 向量索引: {len(vector_index.documents)} 个文档")

    # 3. Agent 路由
    router = AgentRouter()

    # 4. 综合系统
    system = GraphAgenticRAG(graph, vector_index, router)

    # 5. 测试查询
    questions = [
        "什么是 Transformer？",
        "BERT 和 GPT 的区别是什么？",
        "Transformer 和自注意力的关系是什么？",
        "如何训练 BERT 模型？",
    ]

    print("\n" + "-" * 60)
    for q in questions:
        result = system.query(q)
        print(f"\n❓ 问题: {q}")
        print(f"  路由: {result['route']}")
        print(f"  类型: {result['query_type']}")
        print(f"  来源数: {len(result['results'])}")
        print(f"  回答: {result['answer']}")


def demo_graph_traversal():
    """演示图谱遍历"""
    print("\n" + "=" * 60)
    print("  知识图谱遍历演示")
    print("=" * 60)

    graph = KnowledgeGraph()
    graph.add_entity(Entity("e1", "Transformer", "technology", ""))
    graph.add_entity(Entity("e2", "BERT", "model", ""))
    graph.add_entity(Entity("e3", "GPT", "model", ""))
    graph.add_entity(Entity("e4", "自注意力", "concept", ""))
    graph.add_relation(Relation("e2", "e4", "使用"))
    graph.add_relation(Relation("e3", "e4", "使用"))
    graph.add_relation(Relation("e2", "e1", "基于"))
    graph.add_relation(Relation("e3", "e1", "基于"))

    # 查找路径
    paths = graph.find_path("e2", "e3")
    print(f"\nBERT → GPT 的路径:")
    for i, path in enumerate(paths):
        names = [graph.entities[e].name for e in path if e in graph.entities]
        print(f"  路径 {i+1}: {' → '.join(names)}")


def demo_router():
    """演示路由分类"""
    print("\n" + "=" * 60)
    print("  Agent 路由分类演示")
    print("=" * 60)

    router = AgentRouter()

    queries = [
        "什么是 Transformer？",
        "BERT 和 GPT 有什么区别？",
        "Transformer 和自注意力的关系？",
        "如何微调 BERT 模型？",
    ]

    print(f"\n{'问题':<35s} {'分类':<15s} {'策略':<20s}")
    print("-" * 70)
    for q in queries:
        qtype = router.classify_query(q)
        route = router.route(q)
        print(f"{q:<35s} {qtype:<15s} {route.split('→')[0].strip():<20s}")


def demo_summary():
    """总结"""
    print("\n" + "=" * 60)
    print("  系统架构总结")
    print("=" * 60)

    print("""
组件                 | 功能
---------------------|--------------------------------------
KnowledgeGraph       | 存储实体和关系，支持图谱遍历
AgentRouter          | 根据问题类型选择检索策略
VectorIndex          | 向量存储和相似度检索
GraphAgenticRAG      | 综合系统：路由 + 多源检索 + 融合
""")


if __name__ == "__main__":
    demo_full_system()
    demo_graph_traversal()
    demo_router()
    demo_summary()
