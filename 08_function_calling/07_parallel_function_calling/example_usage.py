"""
example_usage.py — Parallel Function Calling 并行工具调用演示
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parallel_function_calling import (
    SimpleToolRegistry,
    ParallelToolExecutor,
    FrameworkParallelSupport,
    get_weather,
    get_news,
    get_stock,
    get_exchange,
)


def demo_parallel():
    """并行调用演示"""
    print("=" * 60)
    print("  并行工具调用")
    print("=" * 60)

    registry = SimpleToolRegistry()
    registry.register("get_weather", get_weather)
    registry.register("get_news", get_news)
    registry.register("get_stock", get_stock)
    registry.register("get_exchange", get_exchange)

    executor = ParallelToolExecutor(registry)

    calls = [
        {"tool_name": "get_weather", "arguments": {"city": "北京"}},
        {"tool_name": "get_news", "arguments": {"category": "科技"}},
        {"tool_name": "get_stock", "arguments": {"symbol": "AAPL"}},
        {"tool_name": "get_exchange", "arguments": {"from_currency": "USD", "to_currency": "CNY"}},
    ]

    # 并行
    print("\n🚀 并行执行:")
    parallel_result = executor.execute_parallel(calls, use_threads=True)
    print(f"  总耗时: {parallel_result.total_time:.2f}s")
    for call in parallel_result.calls:
        print(f"  {'✅' if call.success else '❌'} {call.tool_name} → {(call.result or '')[:50]}...")

    # 顺序
    print("\n🐌 顺序执行:")
    sequential_result = executor.execute_parallel(calls, use_threads=False)
    print(f"  总耗时: {sequential_result.total_time:.2f}s")
    for call in sequential_result.calls:
        print(f"  {'✅' if call.success else '❌'} {call.tool_name} → {(call.result or '')[:50]}...")

    speedup = sequential_result.total_time / parallel_result.total_time if parallel_result.total_time > 0 else 0
    print(f"\n⚡ 加速比: {speedup:.1f}x")


def demo_framework_support():
    """框架支持对比"""
    print("\n" + "=" * 60)
    print("  各框架并行支持")
    print("=" * 60)
    info = FrameworkParallelSupport.get_support_info()
    print(f"{'框架':<12s} {'并行':<8s} {'最大数':<8s} {'备注':<25s}")
    print("-" * 53)
    for item in info:
        print(f"{item['framework']:<12s} {'✅' if item['parallel_support'] else '❌':<8s} "
              f"{item['max_parallel']:<8d} {item['notes']:<25s}")


if __name__ == "__main__":
    demo_parallel()
    demo_framework_support()
