"""
重试策略模块

实现指数退避重试、抖动策略、错误分类等
"""

import asyncio
import random
import time
import logging
from typing import Callable, TypeVar, Type, Tuple, Optional, Any, Awaitable
from functools import wraps
from dataclasses import dataclass, field

from .errors import (
    RetryableError,
    NetworkError,
    TimeoutError,
    RateLimitError,
    ServerError,
    APIError,
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class RetryPolicy:
    """重试策略配置
    
    Attributes:
        max_retries: 最大重试次数
        base_delay: 基础延迟时间（秒）
        max_delay: 最大延迟时间（秒）
        backoff_factor: 退避因子（每次重试的延迟倍数）
        jitter: 是否添加随机抖动（防止惊群效应）
        retryable_exceptions: 可重试的异常类型元组
        retry_on_status_codes: 可重试的HTTP状态码集合
    """
    
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    jitter: bool = True
    retryable_exceptions: Tuple[Type[Exception], ...] = (
        NetworkError,
        TimeoutError,
        RateLimitError,
        ServerError,
    )
    retry_on_status_codes: set = field(default_factory=lambda: {429, 500, 502, 503, 504})
    
    def calculate_delay(self, attempt: int) -> float:
        """计算第attempt次重试的延迟时间
        
        使用指数退避公式：delay = base_delay * (backoff_factor ^ attempt)
        
        Args:
            attempt: 当前重试次数（从0开始）
            
        Returns:
            延迟时间（秒）
        """
        # 指数退避
        delay = self.base_delay * (self.backoff_factor ** attempt)
        
        # 限制最大延迟
        delay = min(delay, self.max_delay)
        
        # 添加随机抖动（0.5x ~ 1.5x）
        if self.jitter:
            jitter_factor = random.uniform(0.5, 1.5)
            delay *= jitter_factor
        
        return delay
    
    def should_retry(self, error: Exception, attempt: int) -> bool:
        """判断是否应该重试
        
        Args:
            error: 捕获的异常
            attempt: 当前重试次数
            
        Returns:
            True 表示应该重试，False 表示不应该重试
        """
        # 超过最大重试次数
        if attempt >= self.max_retries:
            return False
        
        # 检查异常类型
        if isinstance(error, self.retryable_exceptions):
            return True
        
        # 检查HTTP状态码
        if isinstance(error, APIError) and error.status_code in self.retry_on_status_codes:
            return True
        
        return False


def with_retry(
    policy: Optional[RetryPolicy] = None,
    on_retry: Optional[Callable[[int, Exception, float], None]] = None,
):
    """重试装饰器
    
    为函数添加自动重试能力
    
    Args:
        policy: 重试策略，不传则使用默认策略
        on_retry: 重试时的回调函数，接收 (attempt, error, delay) 参数
        
    Example:
        @with_retry(RetryPolicy(max_retries=5))
        async def call_api():
            # API调用逻辑
            pass
    """
    if policy is None:
        policy = RetryPolicy()
    
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_error = None
            
            for attempt in range(policy.max_retries + 1):
                try:
                    # 执行函数
                    result = await func(*args, **kwargs)
                    
                    # 成功则返回
                    if attempt > 0:
                        logger.info(f"第 {attempt + 1} 次尝试成功")
                    
                    return result
                
                except Exception as e:
                    last_error = e
                    
                    # 判断是否应该重试
                    if not policy.should_retry(e, attempt):
                        logger.warning(f"不可重试的错误: {e}")
                        raise
                    
                    # 计算延迟时间
                    delay = policy.calculate_delay(attempt)
                    
                    # 对于限流错误，优先使用服务器返回的retry_after
                    if isinstance(e, RateLimitError) and e.retry_after:
                        delay = max(delay, e.retry_after)
                    
                    # 记录重试日志
                    logger.warning(
                        f"第 {attempt + 1} 次尝试失败: {e}，"
                        f"{delay:.2f}秒后重试..."
                    )
                    
                    # 调用回调函数
                    if on_retry:
                        on_retry(attempt + 1, e, delay)
                    
                    # 等待
                    await asyncio.sleep(delay)
            
            # 所有重试都失败
            logger.error(f"重试 {policy.max_retries} 次后仍然失败")
            raise RetryableError(last_error, policy.max_retries + 1)
        
        return wrapper
    
    return decorator


class RetryManager:
    """重试管理器
    
    提供更灵活的重试控制，支持动态调整策略
    """
    
    def __init__(self, policy: Optional[RetryPolicy] = None):
        self.policy = policy or RetryPolicy()
        self.stats = {
            "total_attempts": 0,
            "successful_attempts": 0,
            "failed_attempts": 0,
            "retries": 0,
        }
    
    async def execute(
        self,
        func: Callable[..., Awaitable[T]],
        *args,
        **kwargs
    ) -> T:
        """执行函数并自动重试
        
        Args:
            func: 要执行的异步函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            函数返回值
            
        Raises:
            RetryableError: 重试次数耗尽
        """
        self.stats["total_attempts"] += 1
        last_error = None
        
        for attempt in range(self.policy.max_retries + 1):
            try:
                result = await func(*args, **kwargs)
                self.stats["successful_attempts"] += 1
                return result
            
            except Exception as e:
                last_error = e
                
                if not self.policy.should_retry(e, attempt):
                    self.stats["failed_attempts"] += 1
                    raise
                
                delay = self.policy.calculate_delay(attempt)
                
                if isinstance(e, RateLimitError) and e.retry_after:
                    delay = max(delay, e.retry_after)
                
                logger.warning(
                    f"尝试 {attempt + 1}/{self.policy.max_retries + 1} 失败: {e}，"
                    f"{delay:.2f}秒后重试"
                )
                
                self.stats["retries"] += 1
                await asyncio.sleep(delay)
        
        self.stats["failed_attempts"] += 1
        raise RetryableError(last_error, self.policy.max_retries + 1)
    
    def get_stats(self) -> dict:
        """获取重试统计信息
        
        Returns:
            统计字典
        """
        return self.stats.copy()
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "total_attempts": 0,
            "successful_attempts": 0,
            "failed_attempts": 0,
            "retries": 0,
        }
