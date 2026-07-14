"""
限流器模块

实现令牌桶算法和滑动窗口算法进行请求限流
"""

import time
import asyncio
from collections import deque
from dataclasses import dataclass
from typing import Optional


@dataclass
class RateLimitResult:
    """限流检查结果"""
    allowed: bool
    remaining: int
    retry_after: Optional[float] = None


class TokenBucket:
    """令牌桶限流器
    
    工作原理：
    - 桶中有固定数量的令牌
    - 每个请求消耗一个令牌
    - 令牌以固定速率补充
    - 桶满时不再补充
    
    Attributes:
        capacity: 桶容量（最大令牌数）
        refill_rate: 补充速率（令牌/秒）
    """
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Args:
            capacity: 桶容量
            refill_rate: 补充速率（每秒补充的令牌数）
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1) -> RateLimitResult:
        """尝试获取令牌
        
        Args:
            tokens: 需要的令牌数量
            
        Returns:
            RateLimitResult: 包含是否允许和剩余令牌数
        """
        async with self._lock:
            # 补充令牌
            now = time.time()
            elapsed = now - self.last_refill
            new_tokens = elapsed * self.refill_rate
            self.tokens = min(self.capacity, self.tokens + new_tokens)
            self.last_refill = now
            
            # 检查是否有足够令牌
            if self.tokens >= tokens:
                self.tokens -= tokens
                return RateLimitResult(
                    allowed=True,
                    remaining=int(self.tokens)
                )
            else:
                # 计算需要等待的时间
                needed = tokens - self.tokens
                retry_after = needed / self.refill_rate
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    retry_after=retry_after
                )
    
    async def wait_and_acquire(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """等待并获取令牌
        
        Args:
            tokens: 需要的令牌数量
            timeout: 最大等待时间（秒）
            
        Returns:
            bool: 是否成功获取
        """
        start_time = time.time()
        
        while True:
            result = await self.acquire(tokens)
            
            if result.allowed:
                return True
            
            # 检查超时
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return False
            
            # 等待
            wait_time = min(result.retry_after or 1.0, 1.0)
            await asyncio.sleep(wait_time)


class SlidingWindow:
    """滑动窗口限流器
    
    工作原理：
    - 在固定时间窗口内限制请求数
    - 使用双端队列记录请求时间戳
    - 移除过期记录后检查是否超限
    
    Attributes:
        max_requests: 窗口内最大请求数
        window_size: 窗口大小（秒）
    """
    
    def __init__(self, max_requests: int, window_size: float):
        """
        Args:
            max_requests: 窗口内最大请求数
            window_size: 窗口大小（秒）
        """
        self.max_requests = max_requests
        self.window_size = window_size
        self.requests = deque()
        self._lock = asyncio.Lock()
    
    async def check(self) -> RateLimitResult:
        """检查是否允许请求
        
        Returns:
            RateLimitResult: 包含是否允许和剩余请求数
        """
        async with self._lock:
            now = time.time()
            window_start = now - self.window_size
            
            # 移除过期记录
            while self.requests and self.requests[0] < window_start:
                self.requests.popleft()
            
            # 检查是否超限
            current_count = len(self.requests)
            
            if current_count < self.max_requests:
                self.requests.append(now)
                remaining = self.max_requests - current_count - 1
                return RateLimitResult(
                    allowed=True,
                    remaining=remaining
                )
            else:
                # 计算需要等待的时间
                if self.requests:
                    retry_after = self.requests[0] + self.window_size - now
                else:
                    retry_after = 0.0
                
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    retry_after=max(0.0, retry_after)
                )
    
    async def wait_and_check(self, timeout: Optional[float] = None) -> bool:
        """等待直到允许请求
        
        Args:
            timeout: 最大等待时间（秒）
            
        Returns:
            bool: 是否成功通过检查
        """
        start_time = time.time()
        
        while True:
            result = await self.check()
            
            if result.allowed:
                return True
            
            # 检查超时
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return False
            
            # 等待
            wait_time = min(result.retry_after or 1.0, 1.0)
            await asyncio.sleep(wait_time)


class RateLimiter:
    """组合限流器
    
    支持同时使用多种限流策略
    """
    
    def __init__(self):
        self.token_buckets = {}
        self.sliding_windows = {}
    
    def add_token_bucket(self, name: str, capacity: int, refill_rate: float):
        """添加令牌桶限流器
        
        Args:
            name: 限流器名称
            capacity: 桶容量
            refill_rate: 补充速率
        """
        self.token_buckets[name] = TokenBucket(capacity, refill_rate)
    
    def add_sliding_window(self, name: str, max_requests: int, window_size: float):
        """添加滑动窗口限流器
        
        Args:
            name: 限流器名称
            max_requests: 最大请求数
            window_size: 窗口大小
        """
        self.sliding_windows[name] = SlidingWindow(max_requests, window_size)
    
    async def check_all(self) -> RateLimitResult:
        """检查所有限流器
        
        Returns:
            RateLimitResult: 最严格的限流结果
        """
        results = []
        
        # 检查所有令牌桶
        for bucket in self.token_buckets.values():
            result = await bucket.acquire()
            results.append(result)
        
        # 检查所有滑动窗口
        for window in self.sliding_windows.values():
            result = await window.check()
            results.append(result)
        
        # 返回最严格的结果
        if not results:
            return RateLimitResult(allowed=True, remaining=999)
        
        # 找到第一个不允许的结果
        for result in results:
            if not result.allowed:
                return result
        
        # 都允许，返回最小剩余
        min_remaining = min(r.remaining for r in results)
        return RateLimitResult(allowed=True, remaining=min_remaining)
