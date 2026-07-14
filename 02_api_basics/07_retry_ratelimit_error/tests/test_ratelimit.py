"""限流器单元测试"""

import asyncio
import pytest
from reliability import TokenBucket, SlidingWindow, RateLimitExceeded


@pytest.mark.asyncio
async def test_token_bucket_acquire():
    """测试令牌桶获取令牌"""
    bucket = TokenBucket(capacity=5, refill_rate=1.0)
    
    # 获取5个令牌应该成功
    for _ in range(5):
        bucket.acquire()
    
    # 第6个应该失败
    with pytest.raises(RateLimitExceeded):
        bucket.acquire()


@pytest.mark.asyncio
async def test_token_bucket_refill():
    """测试令牌桶补充"""
    bucket = TokenBucket(capacity=5, refill_rate=10.0)
    
    # 消耗所有令牌
    for _ in range(5):
        bucket.acquire()
    
    # 等待补充
    await asyncio.sleep(0.5)
    
    # 应该可以再次获取
    bucket.acquire()


@pytest.mark.asyncio
async def test_token_bucket_acquire_or_wait():
    """测试令牌桶等待获取"""
    bucket = TokenBucket(capacity=2, refill_rate=10.0)
    
    # 消耗所有令牌
    bucket.acquire()
    bucket.acquire()
    
    # 等待并获取
    await bucket.acquire_or_wait(timeout=1.0)
    
    # 验证获取成功
    assert bucket.tokens < 2


@pytest.mark.asyncio
async def test_sliding_window_acquire():
    """测试滑动窗口获取"""
    window = SlidingWindow(max_requests=3, window_size=10.0)
    
    # 获取3个请求应该成功
    for _ in range(3):
        window.acquire()
    
    # 第4个应该失败
    with pytest.raises(RateLimitExceeded):
        window.acquire()


@pytest.mark.asyncio
async def test_sliding_window_expiry():
    """测试滑动窗口过期"""
    window = SlidingWindow(max_requests=2, window_size=0.5)
    
    # 消耗配额
    window.acquire()
    window.acquire()
    
    # 应该失败
    with pytest.raises(RateLimitExceeded):
        window.acquire()
    
    # 等待窗口过期
    await asyncio.sleep(0.6)
    
    # 应该可以再次获取
    window.acquire()


def test_token_bucket_initial_state():
    """测试令牌桶初始状态"""
    bucket = TokenBucket(capacity=10, refill_rate=2.0)
    
    assert bucket.capacity == 10
    assert bucket.refill_rate == 2.0
    assert bucket.tokens == 10


def test_sliding_window_initial_state():
    """测试滑动窗口初始状态"""
    window = SlidingWindow(max_requests=100, window_size=60.0)
    
    assert window.max_requests == 100
    assert window.window_size == 60.0
    assert window.current_count == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
