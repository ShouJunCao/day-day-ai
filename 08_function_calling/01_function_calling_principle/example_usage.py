"""
example_usage.py — Function Calling 原理与完整流程演示
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from function_calling import (
    ToolRegistry,
    FunctionCallingEngine,
    get_weather,
    search_knowledge,
    calculate,
)


def demo_tool_registry():
    """演示工具注册"""
    print("=" * 60)
    print("  工具注册表示例")
    print("=" * 60)

    registry = ToolRegistry()

    # 注册天气工具
    registry.register(
        name="get_weather",
        description="获取指定城市的天气信息",
        parameters={
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称"},
            },
            "required": ["city"],
        },
        func=get_weather,
    )

    # 注册搜索工具
    registry.register(
        name="search_knowledge",
        description="搜索内部知识库",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"},
            },
            "required": ["query"],
        },
        func=search_knowledge,
    )

    # 注册计算工具
    registry.register(
        name="calculate",
        description="计算数学表达式",
        parameters={
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "数学表达式"},
            },
            "required": ["expression"],
        },
        func=calculate,
    )

    # 查看注册的工具
    print(f"\n已注册 {len(registry.definitions)} 个工具:")
    for d in registry.definitions:
        print(f"  • {d.name}: {d.description}")

    # 查看工具定义（发送给 LLM 的格式）
    print(f"\n工具定义 (JSON Schema):")
    for td in registry.get_definitions():
        fn = td["function"]
        print(f"  {fn['name']}: {fn['description']}")
        print(f"    参数: {fn['parameters']}")

    # 执行工具调用
    print(f"\n工具执行:")
    result = registry.execute("get_weather", {"city": "北京"})
    print(f"  get_weather(北京) = {result}")

    result = registry.execute("calculate", {"expression": "2 + 3 * 4"})
    print(f"  calculate(2 + 3 * 4) = {result}")


def demo_full_flow():
    """演示完整 Function Calling 流程"""
    print("\n" + "=" * 60)
    print("  Function Calling 完整流程")
    print("=" * 60)

    registry = ToolRegistry()
    registry.register("get_weather", "获取天气", {
        "type": "object",
        "properties": {"city": {"type": "string", "description": "城市名"}},
        "required": ["city"],
    }, func=get_weather)

    registry.register("search_knowledge", "搜索知识库", {
        "type": "object",
        "properties": {"query": {"type": "string", "description": "关键词"}},
        "required": ["query"],
    }, func=search_knowledge)

    engine = FunctionCallingEngine(registry)

    queries = [
        "北京今天天气怎么样？",
        "帮我搜索一下 Function Calling 的相关资料",
        "你好",
    ]

    for q in queries:
        print(f"\n{'=' * 40}")
        print(f"用户: {q}")
        result = engine.execute(q)
        if result.tool_calls_made:
            print("🔧 工具调用:")
            for tc in result.tool_calls_made:
                print(f"  → {tc.tool_name}({tc.arguments}) = {tc.result}")
        print(f"🤖 助手: {result.final_answer}")


def demo_comparison():
    """对比有无 Function Calling"""
    print("\n" + "=" * 60)
    print("  有无 Function Calling 对比")
    print("=" * 60)

    print(f"\n{'维度':<20s} {'无 Function Calling':<25s} {'有 Function Calling':<25s}")
    print("-" * 70)
    print(f"{'实时数据获取':<20s} {'无法获取':<25s} {'可调用 API/数据库':<25s}")
    print(f"{'外部工具使用':<20s} {'不支持':<25s} {'支持多种工具':<25s}")
    print(f"{'计算能力':<20s} {'LLM 估算':<25s} {'精确计算工具':<25s}")
    print(f"{'幻觉风险':<20s} {'较高':<25s} {'较低（有来源）':<25s}")
    print(f"{'适用场景':<20s} {'通用对话':<25s} {'任务执行/工具编排':<25s}")


if __name__ == "__main__":
    demo_tool_registry()
    demo_full_flow()
    demo_comparison()
