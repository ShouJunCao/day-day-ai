"""
example_usage.py — AI 编码 Agent 演示
演示 Agent 对比、推荐和任务模拟。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_coding_agents import (
    AgentComparator,
    CodeAgentSimulator,
    AGENTS_DB,
)


def demo_overview():
    print("=" * 60)
    print("  AI 编码 Agent 概览")
    print("=" * 60)
    
    comparator = AgentComparator()
    
    print("\n  全部 Agent:")
    for agent in comparator.get_all():
        print(f"    {agent['name']} ({agent['vendor']})")
        print(f"      类型: {agent['type']} | 价格: {agent['price']}")
        print(f"      功能: {', '.join(agent['features'])}")
        print(f"      最佳: {agent['best_for']}")
        print()


def demo_comparison():
    print("=" * 60)
    print("  Agent 功能对比")
    print("=" * 60)
    
    comparator = AgentComparator()
    
    features = ["终端交互", "文件读写", "Git 操作", "安全沙箱", "免费"]
    for feature in features:
        results = comparator.compare_by_feature(feature)
        has_count = sum(1 for r in results if r["has_feature"])
        print(f"\n  {feature} ({has_count}/{len(results)} 个 Agent 支持):")
        for r in results:
            icon = "✅" if r["has_feature"] else "❌"
            print(f"    {icon} {r['name']}")


def demo_recommendations():
    print("\n" + "=" * 60)
    print("  用例推荐")
    print("=" * 60)
    
    comparator = AgentComparator()
    
    cases = ["终端驱动", "安全编码", "自定义流程", "Specs 驱动", "免费", "多模型"]
    print("\n  推荐结果:")
    for case in cases:
        rec = comparator.recommend(case)
        print(f"    {case:10s} → {rec['recommended']:20s} ({rec['price']})")


def demo_task_simulation():
    print("\n" + "=" * 60)
    print("  任务模拟")
    print("=" * 60)
    
    sim = CodeAgentSimulator()
    
    for task_type in ["create_api", "refactor", "debug"]:
        print(f"\n  任务: {task_type}")
        task = sim.simulate_task(task_type)
        print(f"    {task[:150]}...")


def demo_feature_matrix():
    print("\n" + "=" * 60)
    print("  功能矩阵")
    print("=" * 60)
    
    comparator = AgentComparator()
    features = ["终端交互", "文件读写", "Git 操作", "安全沙箱", "自定义规则", "免费"]
    
    print(f"    {'Agent':25s}", end="")
    for f in features:
        print(f" {f[:6]:8s}", end="")
    print()
    print("    " + "-" * 70)
    
    for agent in AGENTS_DB:
        print(f"    {agent.name:25s}", end="")
        for f in features:
            has = "✅" if comparator.has_feature(agent, f) else "❌"
            print(f" {has:8s}", end="")
        print()


if __name__ == "__main__":
    demo_overview()
    demo_comparison()
    demo_recommendations()
    demo_task_simulation()
    demo_feature_matrix()
