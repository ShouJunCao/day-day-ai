"""
example_usage.py — 检索优化策略完整演示
演示 Query 改写、HyDE、Multi-Query、Step-back 四种优化策略。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from query_optimization import (
    QueryRewriter,
    HyDERetriever,
    MultiQueryRetriever,
    StepBackRetriever,
    QueryOptimizationScheduler,
)


def demo_query_rewriting():
    """演示 Query 改写"""
    print("=" * 60)
    print("  Query 改写 — Query Rewriting 演示")
    print("=" * 60)

    rewriter = QueryRewriter()

    test_queries = [
        "AI 是什么？",
        "Transformer 原理",
        "RAG 系统如何优化检索",
        "LLM 的幻觉问题",
    ]

    print(f"\n{'原始查询':<25s} {'改写后查询':<50s}")
    print("-" * 75)
    for query in test_queries:
        rewritten = rewriter.rewrite(query)
        print(f"{query:<25s} {rewritten:<50s}")


def demo_hyde():
    """演示 HyDE 检索"""
    print("\n" + "=" * 60)
    print("  HyDE 检索 — Hypothetical Document Embeddings")
    print("=" * 60)

    def mock_embedding(text):
        """模拟向量编码"""
        return [0.1] * 768

    retriever = HyDERetriever(embedding_fn=mock_embedding)

    test_queries = [
        "如何提高 RAG 系统的检索准确率？",
        "Transformer 中的注意力机制是什么？",
    ]

    for query in test_queries:
        print(f"\n查询: {query}")
        print("-" * 50)
        results = retriever.retrieve(query, top_k=3)
        print(f"检索到 {len(results)} 个结果")
        for i, r in enumerate(results, 1):
            print(f"  [{i}] 得分: {r['score']:.3f}")


def demo_multi_query():
    """演示 Multi-Query 检索"""
    print("\n" + "=" * 60)
    print("  Multi-Query 检索 — 多角度查询")
    print("=" * 60)

    retriever = MultiQueryRetriever(num_queries=3)

    test_queries = [
        "深度学习",
        "自然语言处理",
    ]

    for query in test_queries:
        print(f"\n原始查询: {query}")
        print("-" * 50)
        queries = retriever._generate_queries(query)
        print(f"生成的 {len(queries)} 个查询:")
        for i, q in enumerate(queries, 1):
            print(f"  {i}. {q}")


def demo_step_back():
    """演示 Step-back 检索"""
    print("\n" + "=" * 60)
    print("  Step-back 检索 — 后退一步")
    print("=" * 60)

    retriever = StepBackRetriever()

    test_queries = [
        "Transformer 注意力机制如何实现？",
        "BERT 和 GPT 有什么区别？",
    ]

    for query in test_queries:
        print(f"\n原问题: {query}")
        print("-" * 50)
        step_back = retriever._generate_step_back(query)
        print(f"后退问题: {step_back}")
        print("\n策略说明:")
        print("  → 用后退问题检索基本原理")
        print("  → 用原问题检索具体实例")
        print("  → 合并两者提供全面回答")


def demo_strategy_comparison():
    """对比所有策略"""
    print("\n" + "=" * 60)
    print("  检索优化策略对比")
    print("=" * 60)

    print(f"\n{'策略':<15s} {'LLM调用':<10s} {'检索次数':<10s} {'优势':<25s}")
    print("-" * 65)
    print(f"{'Query改写':<15s} {'1次':<10s} {'1次':<10s} {'改善模糊查询'}")
    print(f"{'HyDE':<15s} {'1次':<10s} {'1次':<10s} {'缩小查询 - 文档差距'}")
    print(f"{'Multi-Query':<15s} {'1次':<10s} {'3-5次':<10s} {'多角度覆盖'}")
    print(f"{'Step-back':<15s} {'1次':<10s} {'2次':<10s} {'原理 + 实例'}")


if __name__ == "__main__":
    demo_query_rewriting()
    demo_hyde()
    demo_multi_query()
    demo_step_back()
    demo_strategy_comparison()
