"""
example_usage.py — RAG 评估体系完整演示
演示 RAGAS 框架的五大核心指标。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag_evaluation import (
    RAGEvaluation,
    RAGAS,
    ContextPrecision,
    ContextRecall,
    Faithfulness,
    AnswerRelevancy,
    AnswerCorrectness,
)


def demo_individual_metrics():
    """演示各独立指标"""
    print("=" * 60)
    print("  RAGAS 核心指标演示")
    print("=" * 60)

    # 模拟数据
    questions = ["Transformer 的核心组件是什么？"]
    contexts = [["Transformer 是一种基于自注意力机制的架构。"]]
    ground_truths = ["Transformer 的核心是自注意力机制。"]
    answers = ["Transformer 的核心组件是自注意力机制。"]

    # 上下文精确度
    print(f"\n1. 上下文精确度 (Context Precision)")
    cp = ContextPrecision()
    score = cp.compute(questions, contexts, ground_truths)
    print(f"   得分: {score:.3f}")
    print(f"   含义: 检索到的上下文中相关内容的比例")

    # 上下文召回率
    print(f"\n2. 上下文召回率 (Context Recall)")
    cr = ContextRecall()
    score = cr.compute(contexts, ground_truths)
    print(f"   得分: {score:.3f}")
    print(f"   含义: 真实答案中的信息在上下文中被覆盖的比例")

    # 答案忠实度
    print(f"\n3. 答案忠实度 (Faithfulness)")
    f = Faithfulness()
    score = f.compute(contexts, answers)
    print(f"   得分: {score:.3f}")
    print(f"   含义: 回答内容基于检索上下文的程度（无编造）")

    # 答案相关性
    print(f"\n4. 答案相关性 (Answer Relevancy)")
    ar = AnswerRelevancy()
    score = ar.compute(questions, answers)
    print(f"   得分: {score:.3f}")
    print(f"   含义: 回答直接回答问题的程度")

    # 答案正确性
    print(f"\n5. 答案正确性 (Answer Correctness)")
    ac = AnswerCorrectness()
    score = ac.compute(answers, ground_truths)
    print(f"   得分: {score:.3f}")
    print(f"   含义: 回答与真实答案的一致程度")


def demo_full_evaluation():
    """演示完整评估流程"""
    print("\n" + "=" * 60)
    print("  完整 RAG 评估流程")
    print("=" * 60)

    # 准备评估数据
    eval_data = RAGEvaluation(
        questions=[
            "Transformer 的核心组件是什么？",
            "BERT 和 GPT 有什么区别？",
        ],
        contexts=[
            ["Transformer 是一种基于自注意力机制的架构，由编码器和解码器组成。"],
            ["BERT 基于 Transformer Encoder，GPT 基于 Transformer Decoder。"],
        ],
        ground_truths=[
            "Transformer 的核心组件是自注意力机制、编码器和解码器。",
            "BERT 基于 Encoder 用于理解，GPT 基于 Decoder 用于生成。",
        ],
        answers=[
            "Transformer 的核心组件是自注意力机制，包含编码器和解码器两部分。",
            "BERT 基于 Transformer Encoder，GPT 基于 Transformer Decoder。",
        ],
    )

    print(f"\n评估数据:")
    print(f"  问题数: {len(eval_data.questions)}")
    print(f"  每个问题上下文数: {[len(c) for c in eval_data.contexts]}")

    # 执行评估
    ragas = RAGAS()
    results = ragas.evaluate(eval_data)

    print(f"\n评估结果:")
    print(f"{'指标':<25s} {'得分':>8s} {'状态':>8s}")
    print("-" * 45)

    metric_names = {
        "context_precision": "上下文精确度",
        "context_recall": "上下文召回率",
        "faithfulness": "答案忠实度",
        "answer_relevancy": "答案相关性",
        "answer_correctness": "答案正确性",
        "overall_score": "综合分数",
    }

    for key, name in metric_names.items():
        score = results.get(key, 0.0)
        status = "✅ 优秀" if score >= 0.8 else ("⚠️ 一般" if score >= 0.6 else "❌ 需改进")
        print(f"{name:<25s} {score:>8.3f} {status:>8s}")


def demo_metric_comparison():
    """对比不同指标"""
    print("\n" + "=" * 60)
    print("  RAGAS 指标对比")
    print("=" * 60)

    print(f"\n{'指标':<25s} {'评估对象':<20s} {'理想值':>8s}")
    print("-" * 55)
    print(f"{'上下文精确度':<25s} {'检索到的上下文':<20s} {'> 0.8':>8s}")
    print(f"{'上下文召回率':<25s} {'真实答案覆盖率':<20s} {'> 0.8':>8s}")
    print(f"{'答案忠实度':<25s} {'回答与上下文一致性':<20s} {'> 0.9':>8s}")
    print(f"{'答案相关性':<25s} {'回答与问题相关性':<20s} {'> 0.8':>8s}")
    print(f"{'答案正确性':<25s} {'回答与真实答案':<20s} {'> 0.8':>8s}")


if __name__ == "__main__":
    demo_individual_metrics()
    demo_full_evaluation()
    demo_metric_comparison()
