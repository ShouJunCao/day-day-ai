"""
重试策略使用示例

演示如何使用不同的重试策略
"""

import asyncio
import random
from reliability import RetryPolicy, RetryableError
from reliability.retry import retry_with_policy, RetryManager


# 示例1: 基础重试
async def example_basic_retry():
    """基础重试示例"""
    print("=" * 50)
    print("示例1: 基础重试")
    print("=" * 50)
    
    attempt_count = 0
    
    async def unstable_api_call():
        nonlocal attempt_count
        attempt_count += 1
        print(f"  尝试 #{attempt_count}")
        
        # 模拟不稳定的API调用
        if attempt_count < 3:
            raise ConnectionError("网络连接失败")
        
        return {"status": "success", "data": "Hello World"}
    
    # 使用装饰器添加重试
    retry_policy = RetryPolicy(
        max_attempts=5,
        base_delay=1.0,
        max_delay=10.0,
        backoff_multiplier=2.0,
        jitter=True,
    )
    
    retryable_func = retry_with_policy(retry_policy)(unstable_api_call)
    
    try:
        result = await retryable_func()
        print(f"  结果: {result}")
        print(f"  总尝试次数: {attempt_count}\n")
    except RetryableError as e:
        print(f"  重试失败: {e}\n")


# 示例2: 自定义重试条件
async def example_custom_retry_condition():
    """自定义重试条件示例"""
    print("=" * 50)
    print("示例2: 自定义重试条件")
    print("=" * 50)
    
    attempt_count = 0
    
    async def api_with_specific_errors():
        nonlocal attempt_count
        attempt_count += 1
        print(f"  尝试 #{attempt_count}")
        
        # 模拟特定错误
        if attempt_count == 1:
            raise ValueError("400 Bad Request")  # 不重试
        elif attempt_count == 2:
            raise ConnectionError("503 Service Unavailable")  # 重试
        elif attempt_count == 3:
            raise TimeoutError("408 Request Timeout")  # 重试
        
        return {"status": "success"}
    
    # 只对特定错误重试
    retry_policy = RetryPolicy(
        max_attempts=5,
        base_delay=0.5,
        retryable_exceptions=(ConnectionError, TimeoutError),
    )
    
    retryable_func = retry_with_policy(retry_policy)(api_with_specific_errors)
    
    try:
        result = await retryable_func()
        print(f"  结果: {result}")
        print(f"  总尝试次数: {attempt_count}\n")
    except RetryableError as e:
        print(f"  重试失败: {e}\n")
    except ValueError as e:
        print(f"  不可重试的错误: {e}\n")


# 示例3: 指数退避
async def example_exponential_backoff():
    """指数退避示例"""
    print("=" * 50)
    print("示例3: 指数退避")
    print("=" * 50)
    
    attempt_count = 0
    
    async def slow_recovering_service():
        nonlocal attempt_count
        attempt_count += 1
        print(f"  尝试 #{attempt_count}")
        
        # 模拟服务恢复
        if attempt_count < 4:
            raise ConnectionError("服务暂时不可用")
        
        return {"status": "recovered"}
    
    # 使用指数退避
    retry_policy = RetryPolicy(
        max_attempts=6,
        base_delay=1.0,
        max_delay=30.0,
        backoff_multiplier=2.0,
        jitter=False,  # 禁用随机抖动以观察退避模式
    )
    
    retryable_func = retry_with_policy(retry_policy)(slow_recovering_service)
    
    try:
        result = await retryable_func()
        print(f"  结果: {result}")
        print(f"  总尝试次数: {attempt_count}\n")
    except RetryableError as e:
        print(f"  重试失败: {e}\n")


# 示例4: 重试管理器
async def example_retry_manager():
    """重试管理器示例"""
    print("=" * 50)
    print("示例4: 重试管理器")
    print("=" * 50)
    
    attempt_count = 0
    
    async def unreliable_service():
        nonlocal attempt_count
        attempt_count += 1
        print(f"  尝试 #{attempt_count}")
        
        # 模拟不稳定服务
        if attempt_count < 3:
            raise ConnectionError("连接超时")
        
        return {"status": "success", "attempt": attempt_count}
    
    # 创建重试管理器
    manager = RetryManager(
        max_attempts=5,
        base_delay=0.5,
        max_delay=5.0,
        backoff_multiplier=2.0,
    )
    
    try:
        result = await manager.execute(unreliable_service)
        print(f"  结果: {result}")
        print(f"  统计信息: {manager.stats}\n")
    except RetryableError as e:
        print(f"  重试失败: {e}")
        print(f"  统计信息: {manager.stats}\n")


# 示例5: 并发请求的重试
async def example_concurrent_retry():
    """并发请求重试示例"""
    print("=" * 50)
    print("示例5: 并发请求的重试")
    print("=" * 50)
    
    counters = {i: 0 for i in range(3)}
    
    async def make_request(request_id):
        counters[request_id] += 1
        attempt = counters[request_id]
        print(f"  请求 {request_id} 尝试 #{attempt}")
        
        # 模拟不同请求的失败模式
        if request_id == 0 and attempt < 2:
            raise ConnectionError("请求0失败")
        elif request_id == 1 and attempt < 3:
            raise TimeoutError("请求1超时")
        # 请求2立即成功
        
        return {"request_id": request_id, "attempt": attempt}
    
    retry_policy = RetryPolicy(
        max_attempts=4,
        base_delay=0.3,
        backoff_multiplier=2.0,
    )
    
    # 并发执行多个重试请求
    tasks = [
        retry_with_policy(retry_policy)(make_request)(i)
        for i in range(3)
    ]
    
    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        print("  结果:")
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"    请求 {i}: 失败 - {result}")
            else:
                print(f"    请求 {i}: 成功 - {result}")
        print()
    except Exception as e:
        print(f"  并发执行失败: {e}\n")


# 示例6: 带状态的重试
async def example_stateful_retry():
    """带状态的重试示例"""
    print("=" * 50)
    print("示例6: 带状态的重试")
    print("=" * 50)
    
    state = {"progress": 0}
    
    async def stateful_operation():
        print(f"  当前进度: {state['progress']}%")
        
        # 模拟部分成功
        if state["progress"] < 60:
            state["progress"] += 20
            if state["progress"] < 40:
                raise ConnectionError("连接中断，需要重试")
        
        return {"status": "completed", "progress": state["progress"]}
    
    retry_policy = RetryPolicy(
        max_attempts=5,
        base_delay=0.5,
        retryable_exceptions=(ConnectionError,),
    )
    
    retryable_func = retry_with_policy(retry_policy)(stateful_operation)
    
    try:
        result = await retryable_func()
        print(f"  结果: {result}\n")
    except RetryableError as e:
        print(f"  重试失败: {e}")
        print(f"  最终进度: {state['progress']}%\n")


async def main():
    """运行所有示例"""
    print("\n" + "=" * 50)
    print("重试策略使用示例")
    print("=" * 50 + "\n")
    
    await example_basic_retry()
    await example_custom_retry_condition()
    await example_exponential_backoff()
    await example_retry_manager()
    await example_concurrent_retry()
    await example_stateful_retry()
    
    print("=" * 50)
    print("所有示例执行完毕")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
