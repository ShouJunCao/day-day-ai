"""
example_usage.py — 工具调用错误处理、重试与超时演示
"""
import os
import sys
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from error_handling import (
    SimpleToolRegistry,
    ErrorHandler,
    reliable_weather,
    flaky_api,
    slow_api,
    fallback_search,
)


def demo_successful_call():
    """成功调用"""
    print("=" * 60)
    print("  成功调用（无错误）")
    print("=" * 60)

    registry = SimpleToolRegistry()
    registry.register("weather", reliable_weather)
    handler = ErrorHandler(registry)

    result = handler.call_with_handling("weather", {"city": "北京"})
    print(f"\n  weather(北京) → 成功={result.success}, 重试={result.retries}")
    print(f"  结果: {result.result}")


def demo_retry():
    """重试演示"""
    print("\n" + "=" * 60)
    print("  重试演示（不稳定 API）")
    print("=" * 60)

    registry = SimpleToolRegistry()
    registry.register("search", flaky_api)
    handler = ErrorHandler(registry)
    handler.set_retry_config(max_retries=5, base_delay=0.1, jitter=False)

    for attempt in range(3):
        random.seed(attempt * 10 + 5)
        result = handler.call_with_handling("search", {"query": "AI"})
        print(f"\n  第 {attempt+1} 次调用:")
        print(f"    成功={result.success}, 重试={result.retries}")
        print(f"    降级={result.used_fallback}")
        if result.result:
            print(f"    结果: {result.result[:50]}...")


def demo_fallback():
    """降级演示"""
    print("\n" + "=" * 60)
    print("  降级演示（主 API 不可用）")
    print("=" * 60)

    registry = SimpleToolRegistry()
    registry.register("search", flaky_api)
    handler = ErrorHandler(registry)
    handler.set_retry_config(max_retries=1, base_delay=0.1, jitter=False)
    handler.register_fallback("search", fallback_search)

    random.seed(0)  # 确保失败
    result = handler.call_with_handling("search", {"query": "RAG"})
    print(f"\n  search(RAG) → 成功={result.success}")
    print(f"  重试={result.retries}, 降级={result.used_fallback}")
    print(f"  结果: {result.result}")


def demo_timeout():
    """超时演示"""
    print("\n" + "=" * 60)
    print("  超时演示")
    print("=" * 60)

    registry = SimpleToolRegistry()
    registry.register("slow", slow_api)
    handler = ErrorHandler(registry)
    handler.set_retry_config(max_retries=1, base_delay=0.1, jitter=False)

    try:
        result = handler.call_with_handling("slow", {"data": "test"})
        print(f"\n  slow(test) → 成功={result.success}")
        print(f"  超时={result.timed_out}")
    except TimeoutError:
        print(f"\n  slow(test) → 超时异常（演示模式）")


def demo_strategies():
    """策略对比"""
    print("\n" + "=" * 60)
    print("  错误处理策略对比")
    print("=" * 60)
    print(f"{'策略':<15s} {'行为':<30s} {'适用场景':<20s}")
    print("-" * 65)
    print(f"{'重试 RETRY':<15s} {'指数退避重试':<30s} {'临时网络故障':<20s}")
    print(f"{'降级 FALLBACK':<15s} {'使用备用方案':<30s} {'主服务不可用':<20s}")
    print(f"{'跳过 SKIP':<15s} {'忽略错误继续':<30s} {'非关键步骤':<20s}")
    print(f"{'中止 ABORT':<15s} {'立即停止':<30s} {'致命错误':<20s}")


if __name__ == "__main__":
    demo_successful_call()
    demo_retry()
    demo_fallback()
    demo_timeout()
    demo_strategies()
