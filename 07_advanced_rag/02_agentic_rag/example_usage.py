"""
example_usage.py — Agentic RAG 完整演示
演示 ReAct Agent 和 Routing Agent 的工作流程。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agentic_rag import (
    ReActAgent,
    RoutingAgent,
    vector_search,
    rerank,
    verify,
    generate,
)


def demo_react_agent():
    """演示 ReAct Agent 工作流程"""
    print("=" * 60)
    print("  ReAct Agent 工作流演示")
    print("=" * 60)

    # 定义可用工具
    tools = [vector_search, rerank, verify, generate]

    # 创建 Agent
    agent = ReActAgent(tools=tools, max_steps=4)

    # 执行查询
    question = "Transformer 和 BERT 的关系是什么？"
    result = agent.execute(question)

    print(f"\n问题: {question}")
    print(f"\nAgent 自主推理过程 ({len(result.steps)} 步):")
    print("-" * 50)
    for step in result.steps:
        print(f"\n步骤 {step.step_number}:")
        print(f"  💭 Thought: {step.action.thought}")
        print(f"  🔧 Action: {step.action.action_name}")
        print(f"  👁️ Observation: {step.action.action_result[:60]}...")

    print(f"\n{'=' * 50}")
    print(f"最终答案: {result.answer}")
    print(f"置信度: {result.confidence:.2f}")
    print(f"执行路径: {' → '.join(result.route_taken)}")


def demo_routing_agent():
    """演示路由 Agent"""
    print("\n" + "=" * 60)
    print("  路由 Agent 演示")
    print("=" * 60)

    router = RoutingAgent()

    test_questions = [
        "什么是 Transformer？",
        "BERT 和 GPT 有什么区别？",
        "Transformer 和注意力机制的关系是什么？",
        "如何优化 RAG 系统的检索效果？",
    ]

    print(f"\n{'问题':<35s} {'选择策略':<18s} {'策略名称':<15s}")
    print("-" * 70)
    for q in test_questions:
        result = router.execute_routed_query(q)
        print(f"{q:<35s} {result['selected_strategy']:<18s} {result['strategy_name']:<15s}")


def demo_strategy_comparison():
    """对比不同 Agent 策略"""
    print("\n" + "=" * 60)
    print("  Agentic RAG vs 传统 RAG 对比")
    print("=" * 60)

    print(f"\n{'维度':<20s} {'传统 RAG':<25s} {'Agentic RAG':<25s}")
    print("-" * 70)
    print(f"{'检索方式':<20s} {'固定流程':<25s} {'自主决策':<25s}")
    print(f"{'工具使用':<20s} {'单一检索':<25s} {'多工具组合':<25s}")
    print(f"{'推理能力':<20s} {'无':<25s} {'有（ReAct/Plan）':<25s}")
    print(f"{'适应性':<20s} {'低':<25s} {'高':<25s}")
    print(f"{'复杂度':<20s} {'低':<25s} {'高':<25s}")
    print(f"{'适用场景':<20s} {'简单问答':<25s} {'复杂多步推理':<25s}")


if __name__ == "__main__":
    demo_react_agent()
    demo_routing_agent()
    demo_strategy_comparison()
