"""
example_usage.py — CRAG 与 Self-RAG 完整演示
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from corrective_rag import (
    RelevanceEvaluator,
    CorrectiveRAG,
    SelfRAG,
)


def demo_crag():
    """演示 CRAG 流程"""
    print("=" * 60)
    print("  CRAG（Corrective RAG）演示")
    print("=" * 60)

    evaluator = RelevanceEvaluator(threshold=0.3)
    crag = CorrectiveRAG(evaluator)

    docs = [
        "今天天气不错",
        "Python 是一门编程语言",
        "北京是中国的首都",
    ]

    result = crag.query("Transformer 架构原理", docs)

    print(f"\n查询: {result.query}")
    print(f"最终置信度: {result.confidence:.2f}")
    print(f"\n执行步骤:")
    for step in result.steps_taken:
        print(f"  → {step}")
    print(f"\n回答: {result.final_answer}")


def demo_self_rag():
    """演示 Self-RAG 流程"""
    print("\n" + "=" * 60)
    print("  Self-RAG 演示")
    print("=" * 60)

    evaluator = RelevanceEvaluator(threshold=0.3)
    self_rag = SelfRAG(evaluator)

    docs = [
        "Transformer 基于自注意力机制",
        "自注意力允许模型关注输入的不同部分",
        "Transformer 由编码器和解码器组成",
    ]

    result = self_rag.query("Transformer 的核心机制是什么？", docs)

    print(f"\n查询: {result.query}")
    print(f"最佳回答置信度: {result.confidence:.2f}")
    print(f"\n候选评估:")
    for step in result.steps_taken:
        print(f"  → {step}")
    print(f"\n最佳回答: {result.final_answer}")


def demo_comparison():
    """对比两种方法"""
    print("\n" + "=" * 60)
    print("  CRAG vs Self-RAG 全面对比")
    print("=" * 60)

    print(f"\n{'维度':<18s} {'CRAG':<28s} {'Self-RAG':<28s}")
    print("-" * 74)
    print(f"{'纠正时机':<18s} {'检索后、生成前':<28s} {'生成后':<28s}")
    print(f"{'纠正方式':<18s} {'修正查询 + 重新检索':<28s} {'多候选生成 + 评估选择':<28s}")
    print(f"{'评估对象':<18s} {'检索结果质量':<28s} {'生成回答质量':<28s}")
    print(f"{'计算成本':<18s} {'中（可能多次检索）':<28s} {'高（多次生成+评估）':<28s}")
    print(f"{'适用场景':<18s} {'检索质量不稳定':<28s} {'生成质量不稳定':<28s}")
    print(f"{'延迟影响':<18s} {'增加检索延迟':<28s} {'增加生成延迟':<28s}")


if __name__ == "__main__":
    demo_crag()
    demo_self_rag()
    demo_comparison()
