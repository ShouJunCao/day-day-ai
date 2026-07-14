"""
限流器使用示例

演示令牌桶和滑动窗口限流器
"""

import asyncio
import time
from reliability import TokenBucket, SlidingWindow, RateLimitExceeded


# 示例1: 令牌桶基础用法
async def example_token_bucket_basic():
    """令牌桶基础用法"""
    print("=" * 50)
    print("示例1: 令牌桶基础用法")
    print("=" * 50)
    
    # 创建令牌桶：容量10，每秒补充2个
    bucket = TokenBucket(capacity=10, refill_rate=2.0)
    
    print(f"初始令牌数: {bucket.tokens}")
    
    # 快速消费令牌
    for i in range(12):
        try:
            bucket.acquire()
            print(f"  请求 {i+1}: 成功 (剩余令牌: {bucket.tokens:.1f})")
        except RateLimitExceeded as e:
            print(f"  请求 {i+1}: 被限流 - {e}")
            break
    
    # 等待令牌补充
    print("\n等待3秒让令牌补充...")
    await asyncio.sleep(3)
    print(f"等待后令牌数: {bucket.tokens:.1f}")
    
    # 再次请求
    try:
        bucket.acquire()
        print(f"  请求: 成功 (剩余令牌: {bucket.tokens:.1f})")
    except RateLimitExceeded as e:
        print(f"  请求: 被限流 - {e}")
    
    print()


# 示例2: 令牌桶与异步等待
async def example_token_bucket_wait():
    """令牌桶异步等待"""
    print("=" * 50)
    print("示例2: 令牌桶异步等待")
    print("=" * 50)
    
    # 创建令牌桶：容量5，每秒补充1个
    bucket = TokenBucket(capacity=5, refill_rate=1.0)
    
    print("发送10个请求（容量只有5）:")
    
    for i in range(10):
        start_time = time.time()
        
        try:
            # 使用acquire_or_wait等待令牌
            await bucket.acquire_or_wait(timeout=5.0)
            elapsed = time.time() - start_time
            print(f"  请求 {i+1}: 成功 (等待 {elapsed:.2f}s, 剩余: {bucket.tokens:.1f})")
        except RateLimitExceeded as e:
            print(f"  请求 {i+1}: 超时 - {e}")
            break
    
    print()


# 示例3: 滑动窗口基础用法
async def example_sliding_window_basic():
    """滑动窗口基础用法"""
    print("=" * 50)
    print("示例3: 滑动窗口基础用法")
    print("=" * 50)
    
    # 创建滑动窗口：10秒内最多5个请求
    window = SlidingWindow(max_requests=5, window_size=10.0)
    
    print("在2秒内发送8个请求（限制：10秒内5个）:")
    
    for i in range(8):
        try:
            remaining = window.acquire()
            print(f"  请求 {i+1}: 成功 (剩余配额: {remaining})")
        except RateLimitExceeded as e:
            print(f"  请求 {i+1}: 被限流 - {e}")
            break
    
    print()


# 示例4: 滑动窗口与时间推移
async def example_sliding_window_time():
    """滑动窗口时间推移"""
    print("=" * 50)
    print("示例4: 滑动窗口时间推移")
    print("=" * 50)
    
    # 创建滑动窗口：3秒内最多3个请求
    window = SlidingWindow(max_requests=3, window_size=3.0)
    
    # 第一阶段：快速发送3个请求
    print("阶段1: 快速发送3个请求")
    for i in range(3):
        try:
            remaining = window.acquire()
            print(f"  请求 {i+1}: 成功 (剩余: {remaining})")
        except RateLimitExceeded as e:
            print(f"  请求 {i+1}: 被限流")
    
    # 尝试第4个请求
    try:
        window.acquire()
        print("  请求 4: 成功")
    except RateLimitExceeded:
        print("  请求 4: 被限流（符合预期）")
    
    # 等待窗口滑动
    print("\n等待3秒让窗口滑动...")
    await asyncio.sleep(3)
    
    # 第二阶段：窗口已滑动，可以再次请求
    print("\n阶段2: 窗口滑动后的请求")
    for i in range(3):
        try:
            remaining = window.acquire()
            print(f"  请求 {i+1}: 成功 (剩余: {remaining})")
        except RateLimitExceeded as e:
            print(f"  请求 {i+1}: 被限流")
    
    print()


# 示例5: 组合限流器
async def example_combined_limiters():
    """组合限流器示例"""
    print("=" * 50)
    print("示例5: 组合限流器（令牌桶 + 滑动窗口）")
    print("=" * 50)
    
    # 令牌桶：控制突发流量（容量5，每秒补充2个）
    bucket = TokenBucket(capacity=5, refill_rate=2.0)
    
    # 滑动窗口：控制持续流量（10秒内最多8个）
    window = SlidingWindow(max_requests=8, window_size=10.0)
    
    print("发送10个请求（受两个限流器约束）:")
    
    for i in range(10):
        try:
            # 必须同时通过两个限流器
            bucket.acquire()
            window.acquire()
            print(f"  请求 {i+1}: 成功 (桶: {bucket.tokens:.1f}, 窗口: {window.current_count}/{window.max_requests})")
        except RateLimitExceeded as e:
            print(f"  请求 {i+1}: 被限流 - {e}")
            # 等待后重试
            await asyncio.sleep(0.5)
    
    print()


# 示例6: 动态调整限流参数
async def example_dynamic_adjustment():
    """动态调整限流参数"""
    print("=" * 50)
    print("示例6: 动态调整限流参数")
    print("=" * 50)
    
    # 创建初始限流器
    bucket = TokenBucket(capacity=10, refill_rate=2.0)
    
    print(f"初始配置: 容量={bucket.capacity}, 补充速率={bucket.refill_rate}/s")
    
    # 发送5个请求
    print("\n发送5个请求:")
    for i in range(5):
        bucket.acquire()
        print(f"  请求 {i+1}: 成功 (剩余: {bucket.tokens:.1f})")
    
    # 动态调整参数（模拟负载增加）
    print("\n检测到高负载，调整限流参数...")
    bucket.capacity = 5  # 降低容量
    bucket.refill_rate = 1.0  # 降低补充速率
    print(f"新配置: 容量={bucket.capacity}, 补充速率={bucket.refill_rate}/s")
    
    # 继续发送请求
    print("\n继续发送5个请求:")
    for i in range(5):
        try:
            bucket.acquire()
            print(f"  请求 {i+1}: 成功 (剩余: {bucket.tokens:.1f})")
        except RateLimitExceeded:
            print(f"  请求 {i+1}: 被限流")
    
    print()


async def main():
    """运行所有示例"""
    print("\n" + "=" * 50)
    print("限流器使用示例")
    print("=" * 50 + "\n")
    
    await example_token_bucket_basic()
    await example_token_bucket_wait()
    await example_sliding_window_basic()
    await example_sliding_window_time()
    await example_combined_limiters()
    await example_dynamic_adjustment()
    
    print("=" * 50)
    print("所有示例执行完毕")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
