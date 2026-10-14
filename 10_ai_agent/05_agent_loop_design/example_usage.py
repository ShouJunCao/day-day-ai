"""
example_usage.py — Agent Loop 设计演示
演示 ReAct、Plan-and-Execute、Reflexion 三种循环模式。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_loop_design import (
    ReActLoop,
    PlanAndExecuteLoop,
    ReflexionLoop,
)


def demo_react_loop():
    """演示 ReAct 循环"""
    print("=" * 60)
    print("  ReAct 循环")
    print("=" * 60)
    
    print("""
    核心逻辑: Thought -> Action -> Observation -> ... -> Final Answer
    
    特点:
    • 简单直接，交替进行思考和行动
    • 每一步都基于前一步的观察结果
    • 适合中等复杂度、需要多步推理的任务
    
    适用场景:
    • 问答系统（需要搜索 + 推理）
    • 数据查询（需要多次调用 API）
    • 代码调试（需要执行 + 观察 + 修正）
    """)
    
    # 模拟 ReAct 流程
    print("  ReAct 流程示例:")
    print("    问题: 北京今天天气如何？")
    print("    Thought: 我需要查询北京的天气")
    print("    Action: get_weather")
    print("    Action Input: {'city': '北京'}")
    print("    Observation: 北京 天气：晴，25°C")
    print("    Final Answer: 北京今天天气晴，25°C")


def demo_plan_and_execute():
    """演示 Plan-and-Execute 循环"""
    print("\n" + "=" * 60)
    print("  Plan-and-Execute 循环")
    print("=" * 60)
    
    print("""
    核心逻辑: Plan（制定完整计划） -> Execute（按步骤执行）
    
    特点:
    • 先制定完整计划，再逐步执行
    • 执行过程可控，便于监控和干预
    • 适合长程任务，需要多步骤协调的场景
    
    适用场景:
    • 数据分析流水线
    • 复杂报告生成
    • 多步骤自动化任务
    """)
    
    # 模拟 Plan-and-Execute 流程
    print("  Plan-and-Execute 流程示例:")
    print("    目标: 生成销售分析报告")
    print("    [Plan Phase]")
    print("      Step 1: 收集销售数据")
    print("      Step 2: 数据清洗")
    print("      Step 3: 统计分析")
    print("      Step 4: 生成图表")
    print("      Step 5: 撰写报告")
    print("    [Execute Phase]")
    print("      执行 Step 1... 完成")
    print("      执行 Step 2... 完成")
    print("      ...")
    print("      执行 Step 5... 完成")


def demo_reflexion():
    """演示 Reflexion 循环"""
    print("\n" + "=" * 60)
    print("  Reflexion 循环")
    print("=" * 60)
    
    print("""
    核心逻辑: Execute -> Reflect（反思） -> Modify（修正） -> Execute...
    
    特点:
    • 具有自我反思和纠错能力
    • 通过 LLM 评估输出质量并生成改进建议
    • 适合高准确率要求的任务
    
    适用场景:
    • 代码生成与调试
    • 文章写作与润色
    • 数学推理与验证
    """)
    
    # 模拟 Reflexion 流程
    print("  Reflexion 流程示例:")
    print("    目标: 写一篇关于 AI 的文章")
    print("    [Iteration 1]")
    print("      Execute: 生成初稿")
    print("      Reflect: 文章结构不完整，缺少结论部分")
    print("    [Iteration 2]")
    print("      Execute: 补充结论部分")
    print("      Reflect: 语言不够流畅，需要润色")
    print("    [Iteration 3]")
    print("      Execute: 润色语言")
    print("      Reflect: 质量达标 ✓")
    print("      Final: 完成")


def demo_comparison():
    """对比三种循环模式"""
    print("\n" + "=" * 60)
    print("  三种循环模式对比")
    print("=" * 60)
    
    print("""
    ┌─────────────────┬───────────┬───────────────┬───────────┐
    │     维度        │  ReAct    │ Plan-and-Exec │ Reflexion │
    ├─────────────────┼───────────┼──────────────────────────┤
    │ 规划方式        │ 即时规划   │ 预先规划       │ 迭代规划   │
    │ 执行控制        │ 低         │ 高             │ 中         │
    │ 自适应能力      │ 中         │ 低             │ 高         │
    │ 适用任务复杂度  │ 中         │ 高             │ 高         │
    │ LLM 调用次数    │ 多         │ 中             │ 多         │
    │ 实现难度        │ 低         │ 中             │ 高         │
    └─────────────────┴───────────┴──────────────────────────┘
    """)


if __name__ == "__main__":
    demo_react_loop()
    demo_plan_and_execute()
    demo_reflexion()
    demo_comparison()
