"""
example_usage.py — Agent 框架对比演示
演示框架特性对比、代码复杂度评估和 LLM 推荐。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from framework_comparison import (
    FRAMEWORKS,
    FrameworkAdvisor,
    CodeComplexityAnalyzer,
)


def demo_overview():
    """演示框架概览"""
    print("=" * 60)
    print("  五大框架概览")
    print("=" * 60)
    
    for fw in FRAMEWORKS:
        print(f"\n {fw.name}")
        print(f"   Agent 循环: {fw.agent_loop}")
        print(f"   多 Agent: {'支持' if fw.multi_agent else '不支持'}")
        print(f"   图编排: {'支持' if fw.graph_support else '不支持'}")
        print(f"   复杂度: {fw.code_complexity}")
        print(f"   学习曲线: {fw.learning_curve}")
        print(f"   最佳场景: {fw.best_for}")


def demo_complexity():
    """演示代码复杂度估算"""
    print("\n" + "=" * 60)
    print("  代码复杂度估算")
    print("=" * 60)
    
    analyzer = CodeComplexityAnalyzer()
    
    tasks = [
        "简单问答助手",
        "多步骤数据分析 Agent",
        "多 Agent 协作编码"
    ]
    
    for task in tasks:
        print(f"\n 任务: {task}")
        for fw in FRAMEWORKS:
            lines = analyzer.estimate_lines(fw.name, task)
            bar = "█" * (lines // 5)
            print(f"   {fw.name:25s} 约 {lines:3d} 行  {bar}")


def demo_advisor():
    """演示框架推荐助手"""
    print("\n" + "=" * 60)
    print("  框架推荐助手（基于 LLM）")
    print("=" * 60)
    
    advisor = FrameworkAdvisor()
    
    scenarios = [
        "我需要构建一个企业级的复杂工作流，需要精细控制每个步骤的状态转换。",
        "我想让多个 AI 角色互相讨论，共同解决一个编程问题。",
        "我们团队没有太多编程经验，希望用拖拽的方式构建 AI 应用。",
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n--- 场景 {i} ---")
        print(f"需求: {scenario}")
        result = advisor.recommend(scenario)
        if "error" not in result:
            print(f"  推荐: {result.get('framework', 'N/A')}")
            print(f"  理由: {result.get('reason', 'N/A')[:80]}")
        else:
            print(f"  错误: {result['error']}")


def demo_comparison_table():
    """演示对比表格数据"""
    print("\n" + "=" * 60)
    print("  对比表格数据")
    print("=" * 60)
    
    # 表头
    print(f"  {'框架':<25s} {'多Agent':<8s} {'图编排':<8s} {'复杂度':<8s} {'学习曲线':<8s}")
    print(f"  {'─' * 55}")
    
    for fw in FRAMEWORKS:
        multi = "✅" if fw.multi_agent else ""
        graph = "✅" if fw.graph_support else "❌"
        print(f"  {fw.name:<25s} {multi:<8s} {graph:<8s} {fw.code_complexity:<8s} {fw.learning_curve:<8s}")


if __name__ == "__main__":
    demo_overview()
    demo_complexity()
    demo_advisor()
    demo_comparison_table()
