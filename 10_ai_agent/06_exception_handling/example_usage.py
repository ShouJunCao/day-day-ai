"""
example_usage.py — Agent 异常处理、超时与恢复机制演示
演示异常处理器、熔断器、恢复策略的使用。
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from exception_handling import (
    ExceptionHandler,
    TimeoutController,
    CircuitBreaker,
    RecoveryStrategy,
    AgentTimeoutError,
    AgentRetryExhaustedError,
)


def demo_exception_handler():
    """演示异常处理器"""
    print("=" * 60)
    print("  异常处理器")
    print("=" * 60)
    
    print("""
    异常处理器提供以下功能：
    • 自动重试：当指定异常发生时自动重试
    • 指数退避：重试间隔逐渐增加
    • 回退逻辑：重试耗尽时执行备用方案
    • 熔断触发：连续失败时触发熔断保护
    """)
    
    # 演示：模拟不稳定的 API 调用
    call_count = [0]
    def unstable_api_call():
        call_count[0] += 1
        if call_count[0] < 3:
            raise ValueError(f"API 临时故障 (第 {call_count[0]} 次)")
        return "API 响应正常"
    
    handler = ExceptionHandler(
        exception_type=ValueError,
        max_retries=3,
        retry_delay=0.5,
        fallback_action=lambda e: f"回退结果: {e}"
    )
    
    print("  场景: 不稳定的 API 调用")
    call_count[0] = 0
    result = handler.handle(unstable_api_call)
    print(f"    最终结果: {result}")
    
    print("\n  场景: 回退逻辑")
    call_count[0] = 0
    def always_failing():
        raise ValueError("一直失败")
    
    handler_with_fallback = ExceptionHandler(
        exception_type=ValueError,
        max_retries=1,
        retry_delay=0.1,
        fallback_action=lambda e: f"使用缓存数据代替"
    )
    result = handler_with_fallback.handle(always_failing)
    print(f"    回退结果: {result}")


def demo_timeout_controller():
    """演示超时控制器"""
    print("\n" + "=" * 60)
    print("  超时控制器")
    print("=" * 60)
    
    print("""
    超时控制器提供以下功能：
    • 上下文管理器：with 语句自动检测超时
    • 主动检查：在循环中定期检查是否超时
    • 灵活配置：可设置不同的超时时间
    """)
    
    print("  场景: 正常执行（未超时）")
    with TimeoutController(timeout_seconds=5.0) as tc:
        time.sleep(0.1)
        print(f"    执行耗时: 0.1s < 5.0s ✅")
        tc.check_timeout()
    print("    完成")
    
    print("\n  场景: 超时检测")
    try:
        with TimeoutController(timeout_seconds=0.5) as tc:
            time.sleep(0.6)
            tc.check_timeout()
    except AgentTimeoutError as e:
        print(f"    捕获超时: {e}")


def demo_circuit_breaker():
    """演示熔断器"""
    print("\n" + "=" * 60)
    print("  熔断器")
    print("=" * 60)
    
    print("""
    熔断器提供以下功能：
    • 失败计数：记录连续失败次数
    • 状态转换：closed → open → half_open → closed
    • 自动恢复：冷却期后自动试探恢复
    • 快速失败：熔断时立即拒绝请求
    """)
    
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0)
    
    fail_counter = [0]
    def service():
        fail_counter[0] += 1
        if fail_counter[0] <= 3:
            raise ConnectionError("服务不可用")
        return "服务正常"
    
    print("  场景: 连续失败 → 熔断 → 恢复")
    for i in range(7):
        try:
            result = cb.call(service)
            print(f"    调用 {i+1}: ✅ {result} (状态: {cb.state})")
        except Exception as e:
            print(f"    调用 {i+1}: ❌ {e}")
    
    print(f"\n  最终状态: {cb.state}")


def demo_recovery_strategy():
    """演示恢复策略"""
    print("\n" + "=" * 60)
    print("  恢复策略")
    print("=" * 60)
    
    print("  可用恢复策略:")
    for err_type in ["network_error", "timeout", "rate_limit", "invalid_input", "service_unavailable"]:
        strategy = RecoveryStrategy.get_strategy(err_type)
        print(f"    {err_type}: {strategy['action']} - {strategy['description']}")
    
    print("\n  策略映射:")
    print("    network_error → retry (指数退避)")
    print("    timeout → reduce_complexity (降低复杂度)")
    print("    rate_limit → wait (等待)")
    print("    invalid_input → fallback (回退)")
    print("    service_unavailable → circuit_break (熔断)")


if __name__ == "__main__":
    demo_exception_handler()
    demo_timeout_controller()
    demo_circuit_breaker()
    demo_recovery_strategy()
