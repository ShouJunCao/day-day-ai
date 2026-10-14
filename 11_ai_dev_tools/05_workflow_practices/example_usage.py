"""
example_usage.py — AI 开发工作流最佳实践演示
演示工作流管理、代码质量检查和最佳实践。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from workflow_best_practices import (
    WorkflowEngine,
    CodeQualityChecker,
    WORKFLOW_STAGES,
)


def demo_workflow():
    print("=" * 60)
    print("  工作流阶段演示")
    print("=" * 60)
    
    engine = WorkflowEngine()
    
    print("\n  全部工作流阶段:")
    for i, stage in enumerate(engine.stages):
        print(f"\n    {i+1}. {stage.name}")
        print(f"       描述: {stage.description}")
        print(f"       AI 工具: {', '.join(stage.ai_tools)}")
        print(f"       人工任务: {', '.join(stage.human_tasks)}")
        print(f"       交付物: {', '.join(stage.deliverables)}")


def demo_progress():
    print("\n" + "=" * 60)
    print("  进度跟踪演示")
    print("=" * 60)
    
    engine = WorkflowEngine()
    
    print(f"\n  初始: {engine.get_progress()}")
    
    for _ in range(3):
        engine.advance()
        print(f"  推进后: {engine.get_progress()}")


def demo_quality():
    print("\n" + "=" * 60)
    print("  代码质量检查演示")
    print("=" * 60)
    
    checker = CodeQualityChecker()
    
    codes = [
        ("优质代码", '''
def calculate_average(numbers: list[float]) -> float:
    """计算列表平均值"""
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)
'''),
        ("劣质代码", '''
def calc(n):
    return sum(n)/len(n)
'''),
    ]
    
    for name, code in codes:
        print(f"\n  {name}:")
        results = checker.check(code)
        passed = sum(1 for r in results.values() if r["passed"])
        total = len(results)
        print(f"    通过率: {passed}/{total}")
        for rule, result in results.items():
            icon = "✅" if result["passed"] else "❌"
            print(f"    {icon} {rule}")


def demo_practices():
    print("\n" + "=" * 60)
    print("  AI 开发最佳实践")
    print("=" * 60)
    
    practices = [
        "需求驱动：先明确需求再开始编码",
        "AI 辅助编码：使用 Copilot/Cursor 补全代码",
        "代码审查：AI + 人工双重审查",
        "测试先行：先写测试再写实现",
        "小步提交：频繁提交，快速集成",
        "持续集成：自动化构建和测试",
        "可观测性：日志、监控、告警",
        "文档同步：代码和文档同步更新",
    ]
    
    print("\n  核心实践:")
    for i, p in enumerate(practices, 1):
        print(f"    {i}. {p}")


if __name__ == "__main__":
    demo_workflow()
    demo_progress()
    demo_quality()
    demo_practices()
