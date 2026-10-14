"""
example_usage.py — AI 编码工具演示
演示工具对比、推荐和代码生成。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_coding_tools import (
    ToolComparator,
    CodeGenerator,
    TOOLS_DB,
)


def demo_overview():
    """演示工具概览"""
    print("=" * 60)
    print("  AI 编码工具概览")
    print("=" * 60)
    
    comparator = ToolComparator()
    
    print("\n  全部工具:")
    for tool in comparator.get_all():
        print(f"    {tool['name']} ({tool['vendor']})")
        print(f"      类型: {tool['type']} | 价格: {tool['price']}")
        print(f"      功能: {', '.join(tool['features'])}")
        print(f"      最佳: {tool['best_for']}")
        print()


def demo_comparison():
    """演示工具对比"""
    print("=" * 60)
    print("  工具功能对比")
    print("=" * 60)
    
    comparator = ToolComparator()
    
    features = ["Agent 模式", "代码补全", "对话", "CLI", "免费"]
    for feature in features:
        results = comparator.compare_by_feature(feature)
        has_count = sum(1 for r in results if r["has_feature"])
        print(f"\n  {feature} ({has_count}/{len(results)} 个工具支持):")
        for r in results:
            icon = "✅" if r["has_feature"] else "❌"
            print(f"    {icon} {r['name']}")


def demo_recommendations():
    """演示推荐"""
    print("\n" + "=" * 60)
    print("  用例推荐")
    print("=" * 60)
    
    comparator = ToolComparator()
    
    cases = ["补全", "IDE 集成", "代码库理解", "自主编码", "企业级", "免费", "多模型"]
    print("\n  推荐结果:")
    for case in cases:
        rec = comparator.recommend(case)
        print(f"    {case:10s} → {rec['recommended']:30s} ({rec['price']})")


def demo_code_generation():
    """演示代码生成"""
    print("\n" + "=" * 60)
    print("  代码生成示例")
    print("=" * 60)
    
    gen = CodeGenerator()
    
    print("\n  可用模板:")
    for name in gen.TEMPLATES:
        code = gen.TEMPLATES[name]
        lines = code.count('\n') + 1
        print(f"    • {name}: {lines} 行")
    
    print("\n  示例: dataclass 模板")
    print("-" * 40)
    print(gen.TEMPLATES["dataclass"])
    print("-" * 40)
    
    print("\n  示例: decorator 模板")
    print("-" * 40)
    print(gen.TEMPLATES["decorator"])
    print("-" * 40)


def demo_feature_matrix():
    """演示功能矩阵"""
    print("\n" + "=" * 60)
    print("  功能矩阵")
    print("=" * 60)
    
    comparator = ToolComparator()
    features = ["代码补全", "对话", "Agent 模式", "CLI", "代码库索引", "免费"]
    
    print(f"    {'工具':30s}", end="")
    for f in features:
        print(f" {f[:6]:8s}", end="")
    print()
    print("    " + "-" * 70)
    
    for tool in TOOLS_DB:
        print(f"    {tool.name:30s}", end="")
        for f in features:
            has = "✅" if comparator.has_feature(tool, f) else "❌"
            print(f" {has:8s}", end="")
        print()


if __name__ == "__main__":
    demo_overview()
    demo_comparison()
    demo_recommendations()
    demo_code_generation()
    demo_feature_matrix()
