"""
example_usage.py — ReAct 框架深度解析演示
演示高级工具注册、上下文管理和框架对比。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from react_framework import (
    AdvancedReActAgent,
    AdvancedToolRegistry,
    AdvancedTool,
    AgentContext,
    search_database,
    calculate,
    send_notification,
)


def demo_tool_registry():
    """演示高级工具注册表"""
    print("=" * 60)
    print("  高级工具注册表")
    print("=" * 60)
    
    registry = AdvancedToolRegistry()
    registry.register(AdvancedTool(
        name="search_database",
        description="搜索数据库获取信息",
        func=search_database,
        input_schema={"query": "搜索关键词"},
        max_retries=2,
    ))
    registry.register(AdvancedTool(
        name="calculate",
        description="计算数学表达式",
        func=calculate,
        input_schema={"expression": "数学表达式"},
        max_retries=1,
    ))
    registry.register(AdvancedTool(
        name="send_notification",
        description="发送通知消息",
        func=send_notification,
        input_schema={"message": "消息内容", "channel": "发送渠道"},
        max_retries=3,
    ))
    
    print(f"\n  已注册工具: {len(registry.tools)} 个")
    print(f"\n  工具描述:\n{registry.get_tools_description()}")
    
    print("\n  工具执行:")
    result = registry.execute_with_retry("search_database", {"query": "用户"})
    print(f"    search_database: {result}")
    
    result = registry.execute_with_retry("calculate", {"expression": "100 * 2 + 50"})
    print(f"    calculate: {result}")


def demo_context():
    """演示上下文管理器"""
    print("\n" + "=" * 60)
    print("  上下文管理器")
    print("=" * 60)
    
    ctx = AgentContext()
    ctx.add_thought("首先需要查询数据库获取用户信息")
    ctx.add_action("search_database", '{"query": "用户"}')
    ctx.add_observation("Alice (admin), Bob (editor)")
    ctx.add_thought("现在需要计算统计数据")
    ctx.add_action("calculate", '{"expression": "10 + 20"}')
    ctx.add_observation("30")
    ctx.add_final_answer("用户总数 2 人，计算结果 30")
    
    print("\n  上下文历史:")
    for entry in ctx.history:
        print(f"    [{entry['role']}] {entry.get('content', entry.get('action', ''))}")
    
    print("\n  上下文摘要:")
    print(ctx.get_context_summary())


def demo_agent():
    """演示高级 Agent"""
    print("\n" + "=" * 60)
    print("  高级 ReAct Agent")
    print("=" * 60)
    
    registry = AdvancedToolRegistry()
    registry.register(AdvancedTool(
        name="search_database",
        description="搜索数据库获取信息",
        func=search_database,
        input_schema={"query": "搜索关键词"},
        max_retries=2,
    ))
    registry.register(AdvancedTool(
        name="calculate",
        description="计算数学表达式",
        func=calculate,
        input_schema={"expression": "数学表达式"},
        max_retries=1,
    ))
    
    agent = AdvancedReActAgent(registry)
    print(f"\n  Agent 配置: 最大迭代 {agent.max_iterations} 次")
    print(f"  可用工具: {len(registry.tools)} 个")


def demo_comparison():
    """演示 ReAct vs 传统方法对比"""
    print("\n" + "=" * 60)
    print("  ReAct vs 传统方法")
    print("=" * 60)
    print("""
    传统方法（单步推理）:
    ┌──────────────┐
    │  用户问题     │
    └──────┬───────┘
           │
    ┌──────▼───────┐
    │  LLM 直接回答 │
    └──────┬───────┘
           │
    ┌──────▼───────┐
    │   最终答案    │
    └──────────────┘
    
    ReAct 方法（多步推理 + 行动）:
    ┌──────────────┐
    │  用户问题     │
    ──────┬───────┘
           │
    ┌──────▼───────     ┌───────────┐     ┌───────────┐
    │  Thought 1   │────▶│ Action 1  │────▶│Observation│
    └──────────────┘     └───────────     └─────┬─────┘
           │                                       │
    ┌──────▼───────┐     ┌───────────     ┌──────▼─────┐
    │  Thought 2   │────▶│ Action 2  │────▶│Observation │
    └──────────────┘     └───────────┘     └─────┬─────┘
           │                                       │
    ──────▼───────┐                              │
    │  Final Answer│◀──────────────────────────────┘
    └──────────────┘
    
    优势:
    • 可解释性: 每一步都有明确的思考过程
    • 灵活性: 可以根据观察结果动态调整策略
    • 准确性: 通过工具获取实时信息，减少幻觉
    """)


if __name__ == "__main__":
    demo_tool_registry()
    demo_context()
    demo_agent()
    demo_comparison()
