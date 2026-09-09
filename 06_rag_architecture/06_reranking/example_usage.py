"""
example_usage.py — 重排序技术完整演示
演示 Cross-Encoder、BGE-Reranker、Cohere Rerank 三种重排序策略。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reranking import (
    CrossEncoderReranker,
    BGEReranker,
    CohereReranker,
    RerankingScheduler,
    RerankResult,
)


def demo_strategy_comparison():
    """对比三种重排序策略"""
    print("=" * 60)
    print("  重排序策略对比")
    print("=" * 60)

    print(f"\n{'策略':<20s} {'精度':<10s} {'速度':<12s} {'部署':<10s} {'中文效果':<10s}")
    print("-" * 65)
    print(f"{'Cross-Encoder':<20s} {'高':<10s} {'慢':<12s} {'本地':<10s} {'中':<10s}")
    print(f"{'BGE-Reranker':<20s} {'最高':<10s} {'中等':<12s} {'本地':<10s} {'优':<10s}")
    print(f"{'Cohere Rerank':<20s} {'高':<10s} {'快（云端）':<12s} {'云端':<10s} {'良':<10s}")

    print("\n各策略详解:")
    print("\n1. Cross-Encoder:")
    print("   • 查询和文档深度交互，精度高")
    print("   • 每对查询 - 文档都需要一次推理，速度慢")
    print("   • 适合 Top-K 精排（K < 50）")

    print("\n2. BGE-Reranker:")
    print("   • 专门优化的中文重排序模型")
    print("   • 支持多语言，V2 版本效果更佳")
    print("   • 模型体积适中，易于部署")

    print("\n3. Cohere Rerank:")
    print("   • 云端服务，无需本地模型")
    print("   • 按量付费，适合快速原型")
    print("   • 多语言支持，响应速度快")


def demo_two_stage_pipeline():
    """演示两阶段检索流程"""
    print("\n" + "=" * 60)
    print("  两阶段检索流程演示")
    print("=" * 60)

    # 模拟向量检索的初筛结果
    initial_results = [
        ("doc_1", "Transformer 是一种基于自注意力机制的神经网络架构"),
        ("doc_2", "BERT 是基于 Transformer Encoder 的预训练模型"),
        ("doc_3", "GPT 是基于 Transformer Decoder 的生成模型"),
        ("doc_4", "注意力机制是 Transformer 的核心组件"),
        ("doc_5", "卷积神经网络主要用于图像处理任务"),
    ]

    query = "Transformer 的原理是什么？"

    print(f"\n查询: {query}")
    print(f"\n阶段 1：向量检索（初筛 {len(initial_results)} 个候选）")
    for i, (doc_id, text) in enumerate(initial_results, 1):
        print(f"  [{i}] {doc_id}: {text}")

    print(f"\n阶段 2：重排序精排")
    print("  使用 Cross-Encoder 对候选文档打分")
    print("  按相关性分数重新排序")

    print(f"\n精排后结果（模拟）:")
    reranked = [
        ("doc_1", 0.95, "Transformer 是一种基于自注意力机制的神经网络架构"),
        ("doc_4", 0.88, "注意力机制是 Transformer 的核心组件"),
        ("doc_2", 0.75, "BERT 是基于 Transformer Encoder 的预训练模型"),
        ("doc_3", 0.60, "GPT 是基于 Transformer Decoder 的生成模型"),
        ("doc_5", 0.10, "卷积神经网络主要用于图像处理任务"),
    ]

    for i, (doc_id, score, text) in enumerate(reranked, 1):
        change = "↑" if i == 1 else ("↓" if i == 4 else "—")
        print(f"  [{i}] {doc_id} (分数:{score:.2f}) {change} {text[:30]}...")


def demo_scheduler():
    """演示统一调度器"""
    print("\n" + "=" * 60)
    print("  统一重排序调度器 — RerankingScheduler")
    print("=" * 60)

    # 创建调度器
    scheduler = RerankingScheduler(strategy="bge_reranker", top_k=3)

    print(f"\n当前策略: {scheduler.strategy}")
    print(f"返回结果数: {scheduler.top_k}")

    print("\n可用策略:")
    for name in scheduler.STRATEGIES:
        print(f"  • {name}")

    print("\n使用方式:")
    print("  scheduler = RerankingScheduler(strategy='bge_reranker')")
    print("  results = scheduler.rerank(query, candidates)")


if __name__ == "__main__":
    demo_strategy_comparison()
    demo_two_stage_pipeline()
    demo_scheduler()
