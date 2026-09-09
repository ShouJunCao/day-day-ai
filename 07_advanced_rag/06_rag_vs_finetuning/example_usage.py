"""
example_usage.py — RAG 与微调选择策略完整演示
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag_vs_finetuning import (
    RagVsFinetuningAdvisor,
    Scenario,
    SCENARIOS,
    simple_recommendation,
)


def demo_all_scenarios():
    """演示所有预定义场景的推荐"""
    print("=" * 60)
    print("  预定义场景分析")
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
        print(f"\n  🎯 推荐: {rec.primary_approach}")
        print(f"  📊 置信度: {rec.confidence:.0%}")
        print(f"  💡 原因:")
        for r in rec.reasons:
            print(f"    • {r}")


def demo_custom_scenario():
    """演示自定义场景分析"""
    print("\n" + "=" * 60)
    print("  自定义场景分析")
    print("=" * 60)

    custom = Scenario(
        name="企业内部知识助手",
        description="帮助员工查询公司内部政策和流程",
        data_volume="large",
        update_frequency="frequent",
        accuracy_requirement="high",
        latency_requirement="medium",
        budget="medium",
    )

    advisor = RagVsFinetuningAdvisor()
    rec = advisor.analyze(custom)

    print(f"\n场景: {custom.name}")
    print(f"描述: {custom.description}")
    print(f"推荐: {rec.primary_approach}")
    print(f"置信度: {rec.confidence:.0%}")
    for r in rec.reasons:
        print(f"  • {r}")


def demo_comparison():
    """对比 RAG 和微调"""
    print("\n" + "=" * 60)
    print("  RAG vs 微调 全面对比")
    print("=" * 60)

    print(f"\n{'维度':<20s} {'RAG':<25s} {'微调':<25s}")
    print("-" * 70)
    print(f"{'知识更新':<20s} {'即时更新（秒级）':<25s} {'需重新训练（小时级）':<25s}")
    print(f"{'知识来源':<20s} {'可追溯':<25s} {'内化到模型':<25s}")
    print(f"{'幻觉风险':<20s} {'低（有来源支持）':<25s} {'中（可能编造）':<25s}")
    print(f"{'延迟':<20s} {'较高（检索+生成）':<25s} {'较低（仅生成）':<25s}")
    print(f"{'训练成本':<20s} {'无':<25s} {'高（GPU 资源）':<25s}")
    print(f"{'数据隐私':<20s} {'数据在外部存储':<25s} {'数据需用于训练':<25s}")
    print(f"{'最佳场景':<20s} {'知识密集型':<25s} {'风格/技能型':<25s}")


def demo_mixed_approach():
    """演示混合方案"""
    print("\n" + "=" * 60)
    print("  RAG + 微调混合方案")
    print("=" * 60)

    print("""
混合方案的优势：
1. RAG 处理动态知识：政策、产品更新等频繁变化的内容
2. 微调处理稳定技能：领域语言风格、专业术语理解等
3. 两者互补：RAG 提供最新事实，微调提升理解和表达

典型架构：
用户问题 → 微调模型（理解意图） → RAG（检索最新知识）
         → 微调模型（生成回答，基于检索结果）
""")


if __name__ == "__main__":
    demo_all_scenarios()
    demo_custom_scenario()
    demo_comparison()
    demo_mixed_approach()
