"""
rag_evaluation.py — RAG 评估体系实现
基于 RAGAS 框架的核心评估指标。
"""
import os
import math
from typing import Optional, List, Dict
from dataclasses import dataclass, field


# ============================================================
# 模块：评估结果数据结构
# ============================================================

@dataclass
class EvaluationResult:
    """
    评估结果。

    属性：
    - metric_name (str): 指标名称
    - score (float): 得分 (0-1)
    - details (dict): 详细信息
    """
    metric_name: str
    score: float
    details: dict = field(default_factory=dict)


@dataclass
class RAGEvaluation:
    """
    RAG 评估数据集。

    属性：
    - questions (list[str]): 问题列表
    - contexts (list[list[str]]): 每个问题对应的上下文
    - ground_truths (list[str]): 真实答案
    - answers (list[str]): LLM 生成的回答
    """
    questions: List[str]
    contexts: List[List[str]]
    ground_truths: List[str]
    answers: List[str]


# ============================================================
# 指标 1：上下文精确度（Context Precision）
# ============================================================

class ContextPrecision:
    """
    上下文精确度：评估检索到的上下文是否相关。

    原理：
    1. 对每个检索到的文档，判断其是否包含回答所需信息
    2. 计算相关文档占所有检索文档的比例
    3. 分数越高，说明检索到的上下文越精确
    """

    def __init__(self):
        pass

    def compute(self, questions: List[str], contexts: List[List[str]],
                ground_truths: List[str]) -> float:
        """
        计算上下文精确度。

        参数：
        - questions (list[str]): 问题列表
        - contexts (list[list[str]]): 每个问题的检索上下文
        - ground_truths (list[str]): 真实答案

        返回：
        - float: 上下文精确度 (0-1)
        """
        scores = []
        for q, ctx_list, gt in zip(questions, contexts, ground_truths):
            if not ctx_list:
                scores.append(0.0)
                continue

            # 评估每个上下文的相关性
            precision_sum = 0.0
            relevant_count = 0
            for i, ctx in enumerate(ctx_list):
                is_relevant = self._is_relevant(q, ctx, gt)
                if is_relevant:
                    relevant_count += 1
                    precision_sum += relevant_count / (i + 1)

            precision = precision_sum / len(ctx_list) if ctx_list else 0.0
            scores.append(precision)

        return sum(scores) / len(scores) if scores else 0.0

    def _is_relevant(self, question: str, context: str, ground_truth: str) -> bool:
        """判断上下文是否与问题和答案相关（简化版）"""
        # 实际项目中应该使用 LLM 或交叉编码器判断
        # 简化实现：检查是否包含关键词
        gt_words = set(ground_truth.replace(" ", ""))
        ctx_words = set(context.replace(" ", ""))
        overlap = len(gt_words & ctx_words) / max(len(gt_words), 1)
        return overlap > 0.3


# ============================================================
# 指标 2：上下文召回率（Context Recall）
# ============================================================

class ContextRecall:
    """
    上下文召回率：评估检索到的上下文是否覆盖了真实答案的所有信息。

    原理：
    1. 从真实答案中提取关键主张（claims）
    2. 检查每个主张是否能在检索到的上下文中找到支持
    3. 召回率 = 被支持的主张数 / 总主张数
    """

    def __init__(self):
        pass

    def compute(self, contexts: List[List[str]],
                ground_truths: List[str]) -> float:
        """
        计算上下文召回率。

        参数：
        - contexts (list[list[str]]): 检索到的上下文
        - ground_truths (list[str]): 真实答案

        返回：
        - float: 上下文召回率 (0-1)
        """
        scores = []
        for ctx_list, gt in zip(contexts, ground_truths):
            if not ctx_list:
                scores.append(0.0)
                continue

            # 合并所有上下文
            combined_ctx = " ".join(ctx_list)

            # 简化实现：基于关键词覆盖度
            gt_words = set(gt.replace(" ", ""))
            ctx_words = set(combined_ctx.replace(" ", ""))
            recall = len(gt_words & ctx_words) / max(len(gt_words), 1)
            scores.append(min(recall, 1.0))

        return sum(scores) / len(scores) if scores else 0.0


# ============================================================
# 指标 3：答案忠实度（Faithfulness）
# ============================================================

class Faithfulness:
    """
    答案忠实度：评估 LLM 生成的回答是否基于检索到的上下文，而非编造信息。

    原理：
    1. 从回答中提取主张（claims）
    2. 检查每个主张是否能在上下文中找到支持
    3. 忠实度 = 被支持的主张数 / 总主张数
    """

    def __init__(self):
        pass

    def compute(self, contexts: List[List[str]],
                answers: List[str]) -> float:
        """
        计算答案忠实度。

        参数：
        - contexts (list[list[str]]): 检索到的上下文
        - answers (list[str]): LLM 生成的回答

        返回：
        - float: 忠实度 (0-1)
        """
        scores = []
        for ctx_list, answer in zip(contexts, answers):
            if not ctx_list:
                scores.append(0.0)
                continue

            combined_ctx = " ".join(ctx_list)
            # 简化实现：检查回答中的关键词是否都在上下文中
            answer_words = set(answer.replace(" ", ""))
            ctx_words = set(combined_ctx.replace(" ", ""))
            faithfulness = len(answer_words & ctx_words) / max(len(answer_words), 1)
            scores.append(min(faithfulness, 1.0))

        return sum(scores) / len(scores) if scores else 0.0


# ============================================================
# 指标 4：答案相关性（Answer Relevancy）
# ============================================================

class AnswerRelevancy:
    """
    答案相关性：评估生成的回答是否直接回答了用户的问题。

    原理：
    1. 从回答中提取关键信息
    2. 评估这些信息与问题的相关程度
    3. 生成反向问题，检查是否与原问题一致
    """

    def __init__(self):
        pass

    def compute(self, questions: List[str],
                answers: List[str]) -> float:
        """
        计算答案相关性。

        参数：
        - questions (list[str]): 问题列表
        - answers (list[str]): LLM 生成的回答

        返回：
        - float: 答案相关性 (0-1)
        """
        scores = []
        for q, a in zip(questions, answers):
            if not a:
                scores.append(0.0)
                continue

            # 简化实现：计算问题和回答的关键词重叠度
            q_words = set(q.replace(" ", ""))
            a_words = set(a.replace(" ", ""))
            overlap = len(q_words & a_words) / max(len(q_words), 1)
            scores.append(min(overlap * 2, 1.0))

        return sum(scores) / len(scores) if scores else 0.0


# ============================================================
# 指标 5：答案正确性（Answer Correctness）
# ============================================================

class AnswerCorrectness:
    """
    答案正确性：评估生成的回答与真实答案的一致程度。

    原理：
    1. 比较生成答案和真实答案的语义相似度
    2. 综合考虑答案的准确性和完整性
    """

    def __init__(self, weight_faithfulness: float = 0.5,
                 weight_relevancy: float = 0.5):
        """
        初始化正确性评估器。

        参数：
        - weight_faithfulness (float): 忠实度权重
        - weight_relevancy (float): 相关性权重
        """
        self.weight_faithfulness = weight_faithfulness
        self.weight_relevancy = weight_relevancy

    def compute(self, answers: List[str],
                ground_truths: List[str]) -> float:
        """
        计算答案正确性。

        参数：
        - answers (list[str]): LLM 生成的回答
        - ground_truths (list[str]): 真实答案

        返回：
        - float: 答案正确性 (0-1)
        """
        scores = []
        for answer, gt in zip(answers, ground_truths):
            if not answer or not gt:
                scores.append(0.0)
                continue

            # 简化实现：计算答案和真实答案的相似度
            a_words = set(answer.replace(" ", ""))
            gt_words = set(gt.replace(" ", ""))
            similarity = len(a_words & gt_words) / max(len(a_words | gt_words), 1)
            scores.append(min(similarity * 2, 1.0))

        return sum(scores) / len(scores) if scores else 0.0


# ============================================================
# 模块：RAGAS 评估器（综合）
# ============================================================

class RAGAS:
    """
    RAGAS 评估器：综合评估 RAG 系统的质量。

    核心指标：
    - context_precision: 上下文精确度
    - context_recall: 上下文召回率
    - faithfulness: 答案忠实度
    - answer_relevancy: 答案相关性
    - answer_correctness: 答案正确性
    """

    def __init__(self):
        self.context_precision = ContextPrecision()
        self.context_recall = ContextRecall()
        self.faithfulness = Faithfulness()
        self.answer_relevancy = AnswerRelevancy()
        self.answer_correctness = AnswerCorrectness()

    def evaluate(self, evaluation_data: RAGEvaluation) -> Dict[str, float]:
        """
        执行全面评估。

        参数：
        - evaluation_data (RAGEvaluation): 评估数据

        返回：
        - dict: 各项指标得分
        """
        results = {}

        results["context_precision"] = self.context_precision.compute(
            evaluation_data.questions,
            evaluation_data.contexts,
            evaluation_data.ground_truths,
        )

        results["context_recall"] = self.context_recall.compute(
            evaluation_data.contexts,
            evaluation_data.ground_truths,
        )

        results["faithfulness"] = self.faithfulness.compute(
            evaluation_data.contexts,
            evaluation_data.answers,
        )

        results["answer_relevancy"] = self.answer_relevancy.compute(
            evaluation_data.questions,
            evaluation_data.answers,
        )

        results["answer_correctness"] = self.answer_correctness.compute(
            evaluation_data.answers,
            evaluation_data.ground_truths,
        )

        # 综合分数
        results["overall_score"] = (
            results["context_precision"] * 0.2 +
            results["context_recall"] * 0.2 +
            results["faithfulness"] * 0.2 +
            results["answer_relevancy"] * 0.2 +
            results["answer_correctness"] * 0.2
        )

        return results


if __name__ == "__main__":
    print("=" * 60)
    print("  RAG 评估体系演示")
    print("=" * 60)

    # 模拟评估数据
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

    # 执行评估
    ragas = RAGAS()
    results = ragas.evaluate(eval_data)

    print(f"\n{'指标':<25s} {'得分':>8s}")
    print("-" * 35)
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
        print(f"{name:<25s} {score:>8.3f}")
