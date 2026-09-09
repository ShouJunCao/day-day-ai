"""
example_usage.py — 单工具调用与多工具编排演示
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tool_orchestration import (
    SimpleToolRegistry,
    SingleToolCaller,
    ToolOrchestrator,
    OrchestrationPlan,
    OrchestrationMode,
    get_weather,
    get_forecast,
    format_weather,
    send_notification,
)


def demo_single_call():
    """演示单工具调用"""
    print("=" * 60)
    print("  单工具调用")
    print("=" * 60)

    registry = SimpleToolRegistry()
    registry.register("get_weather", get_weather)
    caller = SingleToolCaller(registry)

    call = caller.call("get_weather", {"city": "北京"})
    print(f"\n  get_weather(北京) = {call.result}")
    print(f"  成功: {call.success}")


def demo_sequential():
    """顺序编排"""
    print("\n" + "=" * 60)
    print("  顺序编排（获取天气 → 格式化 → 通知）")
    print("=" * 60)

    registry = SimpleToolRegistry()
    registry.register("get_weather", get_weather)
    registry.register("format_weather", format_weather)
    registry.register("send_notification", send_notification)

    orchestrator = ToolOrchestrator(registry)

    plan = OrchestrationPlan(
        mode=OrchestrationMode.SEQUENTIAL,
        description="获取天气并发送通知",
        steps=[
            {"tool": "get_weather", "args": {"city": "上海"}},
            {"tool": "format_weather", "args": {"data": "${step_1}"}},
            {"tool": "send_notification", "args": {
                "message": "${step_2}",
                "channel": "email",
            }},
        ]
    )

    result = orchestrator.execute_plan(plan)
    for k, v in result["results"].items():
        print(f"  {k}: {v['tool']} → {str(v['result'])[:60]}...")


def demo_parallel():
    """并行编排"""
    print("\n" + "=" * 60)
    print("  并行编排（同时查询多个城市）")
    print("=" * 60)

    registry = SimpleToolRegistry()
    registry.register("get_weather", get_weather)

    orchestrator = ToolOrchestrator(registry)

    plan = OrchestrationPlan(
        mode=OrchestrationMode.PARALLEL,
        description="并行查询多个城市",
        steps=[
            {"tool": "get_weather", "args": {"city": "北京"}},
            {"tool": "get_weather", "args": {"city": "上海"}},
            {"tool": "get_weather", "args": {"city": "广州"}},
        ]
    )

    result = orchestrator.execute_plan(plan)
    for k, v in result["results"].items():
        print(f"  {k}: {v['args']['city']} → {str(v['result'])[:50]}...")


def demo_chained():
    """链式编排"""
    print("\n" + "=" * 60)
    print("  链式编排（数据流水线）")
    print("=" * 60)

    registry = SimpleToolRegistry()
    registry.register("get_weather", get_weather)
    registry.register("format_weather", format_weather)

    orchestrator = ToolOrchestrator(registry)

    plan = OrchestrationPlan(
        mode=OrchestrationMode.CHAINED,
        description="链式处理天气数据",
        steps=[
            {"tool": "get_weather", "args": {"city": "广州"}},
            {"tool": "format_weather", "args": {"data": "${step_1}"}},
        ]
    )

    result = orchestrator.execute_plan(plan)
    for k, v in result["results"].items():
        print(f"  {k}: {v['tool']} → {v['result']}")


def demo_comparison():
    """对比表"""
    print("\n" + "=" * 60)
    print("  编排模式对比")
    print("=" * 60)
    print(f"{'模式':<15s} {'特点':<30s} {'适用场景':<20s}")
    print("-" * 65)
    print(f"{'顺序':<15s} {'步骤依次执行':<30s} {'有依赖的多步任务':<20s}")
    print(f"{'并行':<15s} {'步骤同时执行':<30s} {'独立的多路查询':<20s}")
    print(f"{'链式':<15s} {'输出传给下一步':<30s} {'数据流水线处理':<20s}")
    print(f"{'条件':<15s} {'按条件选择执行':<30s} {'分支决策场景':<20s}")


if __name__ == "__main__":
    demo_single_call()
    demo_sequential()
    demo_parallel()
    demo_chained()
    demo_comparison()
