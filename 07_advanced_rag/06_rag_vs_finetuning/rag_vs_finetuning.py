"""
rag_vs_finetuning.py — RAG 与微调的选择策略实现
帮助在不同场景下做出最优的技术决策。
"""
import os
from typing import Optional, List, Dict
from dataclasses import dataclass, field


# ============================================================
# 模块：数据结构
# ============================================================

@dataclass
class Scenario:
    """场景描述"""
    name: str
    description: str
    data_volume: str       # "small", "medium", "large"
    update_frequency: str  # "rare", "occasional", "frequent"
    accuracy_requirement: str  # "low", "medium", "high"
    latency_requirement: str   # "low", "medium", "high"
    budget: str                # "low", "medium", "high"


@dataclass
class Recommendation:
    """推荐结果"""
    primary_approach: str
    confidence: float
    reasons: List[str]
    alternatives: List[str]


# ============================================================
# 模块：决策引擎
# ============================================================

class RagVsFinetuningAdvisor:
    """
    RAG 与微调选择顾问：根据场景特征推荐最优方案。

    决策维度：
    1. 数据量：小数据集适合微调，大数据集适合 RAG
    2. 更新频率：频繁更新适合 RAG，极少更新适合微调
    3. 精度要求：高精度场景适合 RAG（可追溯来源）
    4. 延迟要求：低延迟场景适合微调（无检索开销）
    5. 预算限制：低预算场景适合 RAG（无需训练成本）
    """

    def analyze(self, scenario: Scenario) -> Recommendation:
        """分析场景并给出推荐"""
        rag_score = 0
        ft_score = 0
        reasons = []

        # 数据量评估
        if scenario.data_volume == "small":
            ft_score += 2
            reasons.append("数据量小，适合微调学习")
        elif scenario.data_volume == "large":
            rag_score += 2
            reasons.append("数据量大，RAG 更适合处理海量知识")

        # 更新频率评估
        if scenario.update_frequency == "frequent":
            rag_score += 3
            reasons.append("知识更新频繁，RAG 的即时更新优势明显")
        elif scenario.update_frequency == "rare":
            ft_score += 2
            reasons.append("知识稳定，微调一次性学习即可")

        # 精度要求评估
        if scenario.accuracy_requirement == "high":
            rag_score += 2
            reasons.append("高精度要求，RAG 可追溯来源且支持事实核查")

        # 延迟要求评估
        if scenario.latency_requirement == "high":
            ft_score += 2
            reasons.append("低延迟要求，微调无检索开销")

        # 预算评估
        if scenario.budget == "low":
            rag_score += 2
            reasons.append("预算有限，RAG 无需训练成本")
        elif scenario.budget == "high":
            ft_score += 1
            reasons.append("预算充足，可考虑微调优化")

        # 生成推荐
        if rag_score > ft_score:
            primary = "RAG（检索增强生成）"
            confidence = min(0.5 + (rag_score - ft_score) * 0.1, 0.95)
            alternatives = ["微调", "RAG + 微调结合"]
        elif ft_score > rag_score:
            primary = "模型微调"
            confidence = min(0.5 + (ft_score - rag_score) * 0.1, 0.95)
            alternatives = ["RAG", "RAG + 微调结合"]
        else:
            primary = "RAG + 微调结合"
            confidence = 0.8
            alternatives = ["仅 RAG", "仅微调"]

        return Recommendation(
            primary_approach=primary,
            confidence=confidence,
            reasons=reasons,
            alternatives=alternatives,
        )


# ============================================================
# 模块：常见场景模板
# ============================================================

SCENARIOS = {
    "customer_support": Scenario(
        name="智能客服",
        description="回答客户关于产品、政策的问题",
        data_volume="large",
        update_frequency="frequent",
        accuracy_requirement="high",
        latency_requirement="medium",
        budget="medium",
    ),
    "code_assistant": Scenario(
        name="代码助手",
        description="帮助开发者编写和调试代码",
        data_volume="medium",
        update_frequency="occasional",
        accuracy_requirement="high",
        latency_requirement="medium",
        budget="medium",
    ),
    "domain_expert": Scenario(
        name="领域专家",
        description="在特定领域（如医疗、法律）提供专业建议",
        data_volume="medium",
        update_frequency="rare",
        accuracy_requirement="high",
        latency_requirement="low",
        budget="high",
    ),
    "creative_writing": Scenario(
        name="创意写作",
        description="生成故事、诗歌、营销文案等创意内容",
        data_volume="small",
        update_frequency="rare",
        accuracy_requirement="low",
        latency_requirement="low",
        budget="low",
    ),
}


def simple_recommendation(scenario_name: str) -> Recommendation:
    """快捷推荐函数"""
    if scenario_name not in SCENARIOS:
        raise ValueError(f"未知场景: {scenario_name}")
    advisor = RagVsFinetuningAdvisor()
    return advisor.analyze(SCENARIOS[scenario_name])


if __name__ == "__main__":
    print("=" * 60)
    print("  RAG 与微调选择顾问")
    print("=" * 60)

    advisor = RagVsFinetuningAdvisor()

    for name, scenario in SCENARIOS.items():
        print(f"\n{'=' * 50}")
        print(f"  场景: {scenario.name}")
        print(f"  描述: {scenario.description}")
        print(f"  特征: 数据量={scenario.data_volume}, "
              f"更新={scenario.update_frequency}, "
              f"精度={scenario.accuracy_requirement}")

        rec = advisor.analyze(scenario)
        print(f"\n  推荐: {rec.primary_approach}")
        print(f"  置信度: {rec.confidence:.0%}")
        print(f"  原因:")
        for r in rec.reasons:
            print(f"    • {r}")
