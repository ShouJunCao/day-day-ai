"""
example_usage.py — 混合检索完整演示
包含 BM25 检索、元数据过滤、混合排序的完整流程。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hybrid_search import BM25Search, HybridSearcher, SearchResult


def demo_bm25():
    """演示 BM25 全文检索"""
    print("=" * 60)
    print("  BM25 全文检索 — BM25 Full-Text Search")
    print("=" * 60)

    # 创建检索器
    bm25 = BM25Search(k1=1.5, b=0.75)

    # 添加文档（假设已分词）
    documents = {
        "doc_001": ["人工", "智能", "在", "医疗", "领域", "的", "应用"],
        "doc_002": ["深度", "学习", "与", "神经", "网络", "的", "原理"],
        "doc_003": ["人工", "智能", "和", "深度", "学习", "的", "区别"],
        "doc_004": ["医疗", "影像", "分析", "中", "的", "深度", "学习"],
        "doc_005": ["自然", "语言", "处理", "技术", "最新", "进展"],
    }

    print("\n文档库:")
    for doc_id, tokens in documents.items():
        print(f"  {doc_id}: {' '.join(tokens)}")

    # 建立索引
    for doc_id, tokens in documents.items():
        bm25.add_document(doc_id, tokens)

    # 搜索
    print("\n--- 搜索：'人工 智能' ---")
    results = bm25.search(["人工", "智能"], top_k=3)
    for doc_id, score in results:
        print(f"  {doc_id:10s}  BM25 分数: {score:.4f}")

    print("\n--- 搜索：'深度 学习' ---")
    results = bm25.search(["深度", "学习"], top_k=3)
    for doc_id, score in results:
        print(f"  {doc_id:10s}  BM25 分数: {score:.4f}")

    print("\n--- 搜索：'医疗 深度' ---")
    results = bm25.search(["医疗", "深度"], top_k=3)
    for doc_id, score in results:
        print(f"  {doc_id:10s}  BM25 分数: {score:.4f}")


def demo_hybrid_search():
    """演示混合检索流程"""
    print("\n" + "=" * 60)
    print("  混合检索 — Hybrid Search (Vector + BM25)")
    print("=" * 60)

    searcher = HybridSearcher(alpha=0.7)  # 向量权重 70%

    # 添加带元数据的文档
    docs = [
        ("doc_001", ["人工", "智能", "医疗"], [0.8, 0.6, 0.2], {"category": "科技", "date": "2024-01"}),
        ("doc_002", ["深度", "学习", "原理"], [0.7, 0.7, 0.1], {"category": "科技", "date": "2024-02"}),
        ("doc_003", ["人工", "智能", "教育"], [0.6, 0.5, 0.6], {"category": "教育", "date": "2024-03"}),
        ("doc_004", ["医疗", "影像", "分析"], [0.3, 0.8, 0.5], {"category": "医疗", "date": "2024-01"}),
        ("doc_005", ["自然", "语言", "处理"], [0.9, 0.3, 0.4], {"category": "科技", "date": "2024-04"}),
    ]

    for doc_id, tokens, vector, meta in docs:
        searcher.add_document(doc_id, tokens, vector, meta)

    print("\n文档库（带元数据）:")
    for doc_id, tokens, vector, meta in docs:
        print(f"  {doc_id}: {' '.join(tokens)} | {meta}")

    # 无过滤搜索
    print("\n--- 混合搜索：'人工 智能'（无过滤）---")
    # 注意：实际搜索需要向量数据库支持，此处展示流程

    # 元数据过滤示例
    print("\n--- 元数据过滤：category='科技' ---")
    print("  过滤前: 5 篇文档")
    print("  过滤后: 3 篇文档 (doc_001, doc_002, doc_005)")

    print("\n混合检索流程:")
    print("  1. 向量检索：找到语义相似的 Top-K")
    print("  2. BM25 检索：找到关键词匹配的 Top-K")
    print("  3. 分数归一化：将两种分数映射到 [0, 1]")
    print("  4. 加权融合：hybrid = 0.7 × vector + 0.3 × bm25")
    print("  5. 元数据过滤：按条件筛除不匹配的文档")
    print("  6. 排序返回：按混合分数降序排列")


def demo_comparison():
    """对比纯向量、纯 BM25 和混合检索"""
    print("\n" + "=" * 60)
    print("  检索方法对比 — Search Method Comparison")
    print("=" * 60)

    print("\n{:<10s} {:<15s} {:<15s} {:<15s}".format("场景", "纯向量检索", "纯 BM25", "混合检索"))
    print("-" * 60)
    print("{:<10s} {:<15s} {:<15s} {:<15s}".format(
        "语义查询", "✅ 优秀", "❌ 差", "✅ 优秀"))
    print("{:<10s} {:<15s} {:<15s} {:<15s}".format(
        "关键词查询", "⚠️ 一般", "✅ 优秀", "✅ 优秀"))
    print("{:<10s} {:<15s} {:<15s} {:<15s}".format(
        "专有名词", "⚠️ 一般", "✅ 优秀", "✅ 优秀"))
    print("{:<10s} {:<15s} {:<15s} {:<15s}".format(
        "多义词", "✅ 优秀", "❌ 差", "✅ 优秀"))
    print("{:<10s} {:<15s} {:<15s} {:<15s}".format(
        "精确匹配", "⚠️ 一般", "✅ 优秀", "✅ 优秀"))

    print("\n权重建议:")
    print("  • 语义为主场景: alpha=0.8-0.9（向量权重 80-90%）")
    print("  • 关键词为主场景: alpha=0.3-0.5（BM25 权重 50-70%）")
    print("  • 均衡场景: alpha=0.6-0.7（向量权重 60-70%）")


if __name__ == "__main__":
    demo_bm25()
    demo_hybrid_search()
    demo_comparison()
