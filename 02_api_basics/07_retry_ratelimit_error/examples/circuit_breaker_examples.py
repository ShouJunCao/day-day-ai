"""
熔断器使用示例

演示熔断器的三种状态转换
"""

import asyncio
import random
from reliability import CircuitBreaker, CircuitState, CircuitBreakerOpenError


# 示例1: 基础熔断器用法
async def example_basic_circuit_breaker():
    """基础熔断器用法"""
    print("=" * 50)
    print("示例1: 基础熔断器用法")
    print("=" * 50)
    
    # 创建熔断器：3次失败后打开，5秒后尝试半开
    breaker = CircuitBreaker(
        failure_threshold=3,
        recovery_timeout=5.0,
        expected_exception=ConnectionError,
    )
    
    async def unreliable_service():
        """模拟不稳定的服务"""
        # 50%概率失败
        if random.random() < 0.5:
            raise ConnectionError("服务不可用")
        return "成功响应"
    
    print("发送10个请求:")
    
    for i in range(10):
        try:
            result = await breaker.call(unreliable_service)
            print(f"  请求 {i+1}: {result} (状态: {breaker.state.value})")
        except CircuitBreakerOpenError as e:
            print(f"  请求 {i+1}: 熔断器打开 - {e} (状态: {breaker.state.value})")
        except ConnectionError as e:
            print(f"  请求 {i+1}: 服务失败 - {e} (状态: {breaker.state.value})")
    
    print(f"\n熔断器统计: {breaker.stats}")
    print()


# 示例2: 状态转换观察
async def example_state_transitions():
    """观察熔断器状态转换"""
    print("=" * 50)
    print("示例2: 熔断器状态转换")
    print("=" * 50)
    
    # 创建熔断器：2次失败后打开，3秒后半开，1次成功后关闭
    breaker = CircuitBreaker(
        failure_threshold=2,
        recovery_timeout=3.0,
        success_threshold=1,
        expected_exception=ConnectionError,
    )
    
    # 阶段1: 触发熔断
    print("阶段1: 触发连续失败")
    
    async def always_fail():
        raise ConnectionError("故意失败")
    
    for i in range(4):
        try:
            await breaker.call(always_fail)
        except CircuitBreakerOpenError as e:
            print(f"  请求 {i+1}: 熔断器打开 (状态: {breaker.state.value})")
        except ConnectionError as e:
            print(f"  请求 {i+1}: 服务失败 (状态: {breaker.state.value})")
    
    print(f"\n当前状态: {breaker.state.value}")
    
    # 阶段2: 等待恢复
    print("\n阶段2: 等待恢复时间...")
    await asyncio.sleep(3.5)
    print(f"等待后状态: {breaker.state.value}")
    
    # 阶段3: 半开状态测试
    print("\n阶段3: 半开状态测试")
    
    async def always_succeed():
        return "服务恢复"
    
    try:
        result = await breaker.call(always_succeed)
        print(f"  请求: {result} (状态: {breaker.state.value})")
    except Exception as e:
        print(f"  请求失败: {e} (状态: {breaker.state.value})")
    
    # 阶段4: 继续验证关闭状态
    print("\n阶段4: 验证关闭状态")
    for i in range(3):
        try:
            result = await breaker.call(always_succeed)
            print(f"  请求 {i+1}: {result} (状态: {breaker.state.value})")
        except Exception as e:
            print(f"  请求 {i+1}: 失败 - {e} (状态: {breaker.state.value})")
    
    print()


# 示例3: 多种异常类型
async def example_multiple_exceptions():
    """处理多种异常类型"""
    print("=" * 50)
    print("示例3: 处理多种异常类型")
    print("=" * 50)
    
    # 只对特定异常熔断
    breaker = CircuitBreaker(
        failure_threshold=2,
        recovery_timeout=3.0,
        expected_exception=(ConnectionError, TimeoutError),
    )
    
    async def service_with_different_errors(error_type):
        if error_type == "connection":
            raise ConnectionError("连接失败")
        elif error_type == "timeout":
            raise TimeoutError("请求超时")
        elif error_type == "value":
            raise ValueError("参数错误")  # 不触发熔断
        return "成功"
    
    # 测试连接错误（触发熔断）
    print("测试连接错误（会触发熔断）:")
    for i in range(3):
        try:
            result = await breaker.call(service_with_different_errors, "connection")
            print(f"  请求 {i+1}: {result} (状态: {breaker.state.value})")
        except CircuitBreakerOpenError:
            print(f"  请求 {i+1}: 熔断器打开 (状态: {breaker.state.value})")
        except Exception as e:
            print(f"  请求 {i+1}: {type(e).__name__} (状态: {breaker.state.value})")
    
    # 重置熔断器
    breaker.reset()
    
    # 测试值错误（不触发熔断）
    print("\n测试值错误（不触发熔断）:")
    for i in range(5):
        try:
            result = await breaker.call(service_with_different_errors, "value")
            print(f"  请求 {i+1}: {result} (状态: {breaker.state.value})")
        except ValueError as e:
            print(f"  请求 {i+1}: 值错误 (状态: {breaker.state.value})")
    
    print(f"\n最终统计: {breaker.stats}")
    print()


# 示例4: 与重试结合
async def example_with_retry():
    """熔断器与重试策略结合"""
    print("=" * 50)
    print("示例4: 熔断器与重试结合")
    print("=" * 50)
    
    from reliability import RetryPolicy, retry_with_policy
    
    # 创建熔断器
    breaker = CircuitBreaker(
        failure_threshold=3,
        recovery_timeout=2.0,
        expected_exception=ConnectionError,
    )
    
    # 创建重试策略
    retry_policy = RetryPolicy(
        max_attempts=3,
        base_delay=0.5,
        backoff_multiplier=2.0,
        retryable_exceptions=(ConnectionError,),
    )
    
    attempt_counter = {"count": 0}
    
    async def flaky_service():
        attempt_counter["count"] += 1
        # 前5次失败，之后成功
        if attempt_counter["count"] <= 5:
            raise ConnectionError(f"尝试 {attempt_counter['count']} 失败")
        return "最终成功"
    
    # 包装函数：先重试，再通过熔断器
    retryable_func = retry_with_policy(retry_policy)(flaky_service)
    
    print("发送5个请求（每个请求最多重试3次）:")
    
    for i in range(5):
        attempt_counter["count"] = 0  # 重置计数器
        
        try:
            result = await breaker.call(retryable_func)
            print(f"  请求 {i+1}: {result} (状态: {breaker.state.value})")
        except CircuitBreakerOpenError as e:
            print(f"  请求 {i+1}: 熔断器打开 (状态: {breaker.state.value})")
        except Exception as e:
            print(f"  请求 {i+1}: 失败 - {type(e).__name__} (状态: {breaker.state.value})")
    
    print(f"\n统计: {breaker.stats}")
    print()


# 示例5: 熔断器与限流器结合
async def example_with_rate_limiter():
    """熔断器与限流器结合"""
    print("=" * 50)
    print("示例5: 熔断器与限流器结合")
    print("=" * 50)
    
    from reliability import TokenBucket
    
    # 创建限流器：容量5，每秒补充2个
    bucket = TokenBucket(capacity=5, refill_rate=2.0)
    
    # 创建熔断器：2次失败后打开
    breaker = CircuitBreaker(
        failure_threshold=2,
        recovery_timeout=2.0,
        expected_exception=ConnectionError,
    )
    
    failure_count = {"count": 0}
    
    async def service():
        failure_count["count"] += 1
        if failure_count["count"] <= 3:
            raise ConnectionError("服务失败")
        return "服务正常"
    
    print("发送8个请求（受限流器和熔断器双重保护）:")
    
    for i in range(8):
        try:
            # 先检查限流
            bucket.acquire()
            
            # 再通过熔断器
            result = await breaker.call(service)
            print(f"  请求 {i+1}: {result} (桶: {bucket.tokens:.1f}, 状态: {breaker.state.value})")
            
        except CircuitBreakerOpenError:
            print(f"  请求 {i+1}: 熔断器打开 (桶: {bucket.tokens:.1f}, 状态: {breaker.state.value})")
        except Exception as e:
            print(f"  请求 {i+1}: {type(e).__name__} (桶: {bucket.tokens:.1f}, 状态: {breaker.state.value})")
            await asyncio.sleep(0.3)
    
    print()


async def main():
    """运行所有示例"""
    print("\n" + "=" * 50)
    print("熔断器使用示例")
    print("=" * 50 + "\n")
    
    await example_basic_circuit_breaker()
    await example_state_transitions()
    await example_multiple_exceptions()
    await example_with_retry()
    await example_with_rate_limiter()
    
    print("=" * 50)
    print("所有示例执行完毕")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
