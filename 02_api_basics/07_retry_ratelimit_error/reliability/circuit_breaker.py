"""
熔断器模块

实现熔断器模式，防止故障服务拖垮整个系统
"""

import time
import asyncio
import logging
from enum import Enum
from dataclasses import dataclass
from typing import Callable, Awaitable, TypeVar, Optional

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"      # 关闭状态：正常通过
    OPEN = "open"          # 打开状态：拒绝所有请求
    HALF_OPEN = "half_open"  # 半开状态：允许少量请求测试


@dataclass
class CircuitBreakerStats:
    """熔断器统计信息"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rejected_requests: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None


class CircuitBreakerError(Exception):
    """熔断器打开时抛出的异常"""
    pass


class CircuitBreaker:
    """熔断器
    
    工作原理：
    1. 关闭状态（CLOSED）：正常处理请求，记录失败次数
    2. 打开状态（OPEN）：失败次数超过阈值，拒绝所有请求
    3. 半开状态（HALF_OPEN）：经过恢复时间后，允许少量请求测试
    
    Attributes:
        failure_threshold: 失败次数阈值
        recovery_timeout: 恢复等待时间（秒）
        success_threshold: 半开状态成功次数阈值
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        success_threshold: int = 2,
    ):
        """
        Args:
            failure_threshold: 连续失败次数阈值
            recovery_timeout: 从打开到半开的等待时间
            success_threshold: 半开状态需要成功的次数
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.open_time = None
        
        self.stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()
    
    async def call(
        self,
        func: Callable[..., Awaitable[T]],
        *args,
        **kwargs
    ) -> T:
        """通过熔断器调用函数
        
        Args:
            func: 要调用的异步函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            函数返回值
            
        Raises:
            CircuitBreakerError: 熔断器处于打开状态
        """
        async with self._lock:
            self.stats.total_requests += 1
            
            # 检查是否需要从打开状态转为半开状态
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._transition_to_half_open()
                else:
                    self.stats.rejected_requests += 1
                    raise CircuitBreakerError(
                        f"熔断器已打开，拒绝请求。"
                        f"失败次数: {self.failure_count}"
                    )
        
        # 执行函数
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """判断是否应该尝试重置
        
        Returns:
            bool: 是否应该进入半开状态
        """
        if self.open_time is None:
            return False
        
        elapsed = time.time() - self.open_time
        return elapsed >= self.recovery_timeout
    
    def _transition_to_half_open(self):
        """转换为半开状态"""
        logger.info(f"熔断器从打开转为半开状态")
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
    
    def _transition_to_open(self):
        """转换为打开状态"""
        logger.warning(f"熔断器从 {self.state.value} 转为打开状态")
        self.state = CircuitState.OPEN
        self.open_time = time.time()
    
    def _transition_to_closed(self):
        """转换为关闭状态"""
        logger.info(f"熔断器从半开转为关闭状态")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.open_time = None
    
    async def _on_success(self):
        """请求成功时的处理"""
        async with self._lock:
            self.stats.successful_requests += 1
            self.stats.last_success_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                
                if self.success_count >= self.success_threshold:
                    self._transition_to_closed()
            
            elif self.state == CircuitState.CLOSED:
                # 成功时重置失败计数
                self.failure_count = 0
    
    async def _on_failure(self):
        """请求失败时的处理"""
        async with self._lock:
            self.stats.failed_requests += 1
            self.stats.last_failure_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                # 半开状态失败，立即打开
                self._transition_to_open()
            
            elif self.state == CircuitState.CLOSED:
                self.failure_count += 1
                
                if self.failure_count >= self.failure_threshold:
                    self._transition_to_open()
    
    def get_state(self) -> CircuitState:
        """获取当前状态"""
        return self.state
    
    def get_stats(self) -> CircuitBreakerStats:
        """获取统计信息"""
        return self.stats
    
    def reset(self):
        """重置熔断器"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.open_time = None
        self.stats = CircuitBreakerStats()


class CircuitBreakerRegistry:
    """熔断器注册表
    
    管理多个熔断器实例
    """
    
    def __init__(self):
        self.circuit_breakers = {}
    
    def get_or_create(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        success_threshold: int = 2,
    ) -> CircuitBreaker:
        """获取或创建熔断器
        
        Args:
            name: 熔断器名称
            failure_threshold: 失败阈值
            recovery_timeout: 恢复时间
            success_threshold: 成功阈值
            
        Returns:
            CircuitBreaker: 熔断器实例
        """
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                success_threshold=success_threshold,
            )
        
        return self.circuit_breakers[name]
    
    def get(self, name: str) -> Optional[CircuitBreaker]:
        """获取熔断器
        
        Args:
            name: 熔断器名称
            
        Returns:
            CircuitBreaker or None
        """
        return self.circuit_breakers.get(name)
    
    def get_all_stats(self) -> dict:
        """获取所有熔断器的统计信息
        
        Returns:
            dict: 名称到统计的映射
        """
        return {
            name: cb.get_stats()
            for name, cb in self.circuit_breakers.items()
        }
    
    def reset_all(self):
        """重置所有熔断器"""
        for cb in self.circuit_breakers.values():
            cb.reset()
