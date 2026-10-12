"""
example_usage.py — ReAct Agent 演示
演示 Agent 工具注册、安全计算和 ReAct 循环的概念。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_react import (
    ReActAgent,
    ToolRegistry,
    AgentTool,
    calculator,
    get_weather,
)


def demo_tool_registry():
    """演示工具注册系统"""
    print("=" * 60)
    print("  工具注册系统")
    print("=" * 60)
    
    registry = ToolRegistry()
    registry.register(AgentTool(
        name="calculator",
        description="计算数学表达式",
        func=calculator,
        input_schema={"expression": "string"}
    ))
    registry.register(AgentTool(
        name="get_weather",
        description="查询城市天气",
        func=get_weather,
        input_schema={"city": "string"}
    ))
    
    print(f"\n  已注册工具: {len(registry.tools)} 个")
    for tool in registry.get_tools_description():
        print(f"    • {tool['name']}: {tool['description']}")


def demo_tool_execution():
    """演示工具执行"""
    print("\n" + "=" * 60)
    print("  工具执行")
    print("=" * 60)
    
    registry = ToolRegistry()
    registry.register(AgentTool(
        name="calculator", description="计算",
        func=calculator, input_schema={"expression": "string"}
    ))
    registry.register(AgentTool(
        name="get_weather", description="天气",
        func=get_weather, input_schema={"city": "string"}
    ))
    
    # 计算器
    print("\n  计算器:")
    result = registry.execute("calculator", {"expression": "25 * 4 + 10"})
    print(f"    25 * 4 + 10 = {result}")
    
    result = registry.execute("calculator", {"expression": "(100 + 50) / 3"})
    print(f"    (100 + 50) / 3 = {result}")
    
    # 天气
    print("\n  天气查询:")
    result = registry.execute("get_weather", {"city": "北京"})
    print(f"    {result}")
    
    result = registry.execute("get_weather", {"city": "上海"})
    print(f"    {result}")
    
    # 未知工具
    print("\n  未知工具:")
    result = registry.execute("unknown_tool", {})
    print(f"    {result}")


def demo_agent_architecture():
    """演示 Agent 架构"""
    print("\n" + "=" * 60)
    print("  Agent 架构组件")
    print("=" * 60)
    
    print("""
    ReAct Agent 由以下核心组件构成：

    1. 大脑（LLM）
       - 负责推理和决策
       - 生成 Thought（思考）和 Action（行动）
       - 理解工具描述和任务要求

    2. 工具系统（Tools）
       - ToolRegistry: 工具注册表
       - 每个工具包含名称、描述、函数、参数 Schema
       - 支持动态注册和调用

    3. 记忆（Memory）
       - 短期记忆：对话历史和执行轨迹
       - 长期记忆：跨会话的知识存储
       - trace 列表记录每一步的 Thought/Action/Observation

    4. 循环控制（Loop）
       - max_iterations 限制最大迭代次数
       - 每轮循环：Thought → Action → Observation
       - 终止条件：Final Answer 或达到最大迭代

    ReAct 核心循环：
    ┌─────────────┐
    │  用户问题    │
    └──────┬──────┘
           │
    ┌──────▼──────┐     ┌──────────────┐     ┌──────────────┐
    │  LLM 思考    │────▶│  选择工具     │────▶│  执行工具     │
    │ (Thought)   │     │ (Action)     │     │ (Tool Call)  │
    └────────────┘     └──────────────     └──────┬───────
           │                                         │
    ┌──────▼──────┐                         ┌────────▼──────┐
    │  最终答案    │◀────────────────────────│  观察结果      │
    │(Final Answer)│      (循环)              │ (Observation) │
    └─────────────┘                         ───────────────┘
    """)


def demo_react_flow():
    """演示 ReAct 流程（不使用 LLM 调用，模拟流程）"""
    print("\n" + "=" * 60)
    print("  ReAct 流程模拟")
    print("=" * 60)
    
    print("""
    用户问题：北京今天天气如何？计算 25 * 4 + 10 等于多少？

    ─ 第 1 轮 ─────────────────────────────┐
    │ Thought: 我需要查询北京的天气，然后   │
    │          计算一个数学表达式。         │
    │ Action: get_weather                   │
    │ Input: {"city": "北京"}               │
    │ Observation: 北京 天气：晴，25°C        │
    ───────────────────────────────────────┘

    ┌─ 第 2 轮 ─────────────────────────────┐
    │ Thought: 天气查询完成。现在需要计算   │
    │          数学表达式。                 │
    │ Action: calculator                    │
    │ Input: {"expression": "25 * 4 + 10"} │
    │ Observation: 110                      │
    └───────────────────────────────────────┘

    ┌─ 第 3 轮 ─────────────────────────────┐
    │ Thought: 所有信息已收集，可以回答。    │
    │ Final Answer: 北京今天天气晴，25°C。   │
    │              25 * 4 + 10 = 110        │
    └───────────────────────────────────────┘
    """)
    
    # 实际工具调用
    print("  实际工具调用结果：")
    registry = ToolRegistry()
    registry.register(AgentTool(
        name="calculator", description="计算",
        func=calculator, input_schema={"expression": "string"}
    ))
    registry.register(AgentTool(
        name="get_weather", description="天气",
        func=get_weather, input_schema={"city": "string"}
    ))
    
    obs1 = registry.execute("get_weather", {"city": "北京"})
    print(f"  🌤️ get_weather(北京) → {obs1}")
    
    obs2 = registry.execute("calculator", {"expression": "25 * 4 + 10"})
    print(f"  🧮 calculator(25 * 4 + 10) → {obs2}")
    
    print(f"\n  Final Answer: 北京今天天气晴，25°C。25 * 4 + 10 = {obs2}")


if __name__ == "__main__":
    demo_tool_registry()
    demo_tool_execution()
    demo_agent_architecture()
    demo_react_flow()
