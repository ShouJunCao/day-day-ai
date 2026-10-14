"""
exception_handling.py — Agent 异常处理、超时与恢复机制
演示 Agent 在遇到错误、超时等异常情况时的处理和恢复策略。
"""
import os
import re
import json
import time
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field


# ============================================================
# 模块：异常定义
# ============================================================

class AgentTimeoutError(Exception):
    """Agent 执行超时异常"""
    pass

class AgentRetryExhaustedError(Exception):
    """重试次数耗尽异常"""
    pass

class AgentToolError(Exception):
    """Agent 工具执行异常"""
    pass

# ============================================================
# 模块：异常处理器
# ============================================================

@dataclass
class ExceptionHandler:
    """异常处理器"""
    exception_type: type
    max_retries: int = 3
    retry_delay: float = 1.0
    fallback_action: Optional[Callable] = None
    should_circuit_break: bool = False
    
    def handle(self, func: Callable, *args, **kwargs) -> Any:
        """执行带异常处理的函数"""
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except self.exception_type as e:
                last_error = e
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** attempt)
                    print(f"    ⚠️ 重试 {attempt + 1}/{self.max_retries} (等待 {delay:.1f}s)")
                    time.sleep(delay)
                else:
                    print(f"    ❌ 重试次数耗尽")
                    
            except Exception as e:
                raise e
        
        if self.fallback_action:
            print(f"     执行回退逻辑")
            return self.fallback_action(last_error)
        
        if self.should_circuit_break:
            raise AgentRetryExhaustedError(f"熔断触发: {last_error}") from last_error
        raise last_error

# ============================================================
# 模块：超时控制器
# ============================================================

class TimeoutController:
    """超时控制器"""
    
    def __init__(self, timeout_seconds: float = 30.0):
        self.timeout = timeout_seconds
        self.start_time: Optional[float] = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            elapsed = time.time() - self.start_time
            if elapsed > self.timeout:
                raise AgentTimeoutError(f"执行超时: {elapsed:.1f}s > {self.timeout}s")
        return False
    
    def check_timeout(self):
        """检查是否超时"""
        if self.start_time is None:
            return False
        elapsed = time.time() - self.start_time
        if elapsed > self.timeout:
            raise AgentTimeoutError(f"执行超时: {elapsed:.1f}s > {self.timeout}s")
        return False

# ============================================================
# 模块：熔断器
# ============================================================

class CircuitBreaker:
    """熔断器"""
    
    STATE_CLOSED = "closed"
    STATE_OPEN = "open"
    STATE_HALF_OPEN = "half_open"
    
    def __init__(self, failure_threshold: int = 5, 
                 recovery_timeout: float = 60.0,
                 half_open_max_calls: int = 1):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.state = self.STATE_CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.half_open_calls = 0
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """执行带熔断保护的调用"""
        if self.state == self.STATE_OPEN:
            if self.last_failure_time is not None and time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = self.STATE_HALF_OPEN
                self.half_open_calls = 0
                print(f"    🔓 熔断器半开")
            else:
                raise AgentRetryExhaustedError("熔断器已打开，请求被拒绝")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        if self.state == self.STATE_HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.half_open_max_calls:
                self.state = self.STATE_CLOSED
                self.failure_count = 0
                print(f"    ✅ 熔断器关闭")
        else:
            self.failure_count = 0
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == self.STATE_HALF_OPEN:
            self.state = self.STATE_OPEN
            print(f"    🔒 熔断器打开（半开试探失败）")
        elif self.failure_count >= self.failure_threshold:
            self.state = self.STATE_OPEN
            print(f"    🔒 熔断器打开（失败次数: {self.failure_count}）")

# ============================================================
# 模块：恢复策略
# ============================================================

class RecoveryStrategy:
    """恢复策略"""
    
    STRATEGIES = {
        "network_error": {
            "action": "retry", "max_retries": 5, "delay": 2.0,
            "description": "网络错误：指数退避重试"
        },
        "timeout": {
            "action": "reduce_complexity",
            "description": "超时：降低任务复杂度后重试"
        },
        "rate_limit": {
            "action": "wait", "delay": 60.0,
            "description": "速率限制：等待后重试"
        },
        "invalid_input": {
            "action": "fallback",
            "description": "输入无效：使用默认值或回退逻辑"
        },
        "service_unavailable": {
            "action": "circuit_break",
            "description": "服务不可用：触发熔断"
        }
    }
    
    @classmethod
    def get_strategy(cls, error_type: str) -> Dict[str, Any]:
        return cls.STRATEGIES.get(error_type, {
            "action": "abort",
            "description": "未知错误：中止执行"
        })

# ============================================================
# 模块：入口
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  Agent 异常处理演示")
    print("=" * 60)
    
    # 1. 异常处理器
    print("\n 1. 异常处理器")
    handler = ExceptionHandler(
        exception_type=ValueError,
        max_retries=2,
        retry_delay=0.5
    )
    
    attempt_count = [0]
    def flaky_func():
        attempt_count[0] += 1
        if attempt_count[0] < 3:
            raise ValueError(f"临时错误 (尝试 {attempt_count[0]})")
        return "成功"
    
    try:
        result = handler.handle(flaky_func)
        print(f"    结果: {result}")
    except Exception as e:
        print(f"    最终失败: {e}")
    
    # 2. 熔断器
    print("\n🔌 2. 熔断器")
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=2.0)
    
    failure_count = [0]
    def unstable_service():
        failure_count[0] += 1
        if failure_count[0] <= 3:
            raise ConnectionError("服务不可用")
        return "服务正常"
    
    for i in range(5):
        try:
            result = cb.call(unstable_service)
            print(f"    调用 {i+1}: {result}")
        except Exception as e:
            print(f"    调用 {i+1}: 失败 - {e}")
    
    # 3. 恢复策略
    print("\n🔄 3. 恢复策略")
    for err_type in ["network_error", "timeout", "rate_limit", "invalid_input"]:
        strategy = RecoveryStrategy.get_strategy(err_type)
        print(f"    {err_type}: {strategy['action']} - {strategy['description']}")
    
    print("\n" + "=" * 60)
    print("  演示完成")
    print("=" * 60)
