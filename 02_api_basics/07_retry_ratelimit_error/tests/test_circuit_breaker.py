"""熔断器单元测试"""

import asyncio
import pytest
from reliability import CircuitBreaker, CircuitBreakerOpenError, CircuitState


@pytest.mark.asyncio
async def test_circuit_breaker_closed_state():
    """测试熔断器关闭状态"""
    breaker = CircuitBreaker(failure_threshold=3)
    
    async def success_func():
        return "success"
    
    result = await breaker.call(success_func)
    assert result == "success"
    assert breaker.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_failures():
    """测试熔断器在失败后打开"""
    breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=10.0)
    
    async def fail_func():
        raise ConnectionError("失败")
    
    # 触发3次失败
    for _ in range(3):
        with pytest.raises(ConnectionError):
            await breaker.call(fail_func)
    
    # 熔断器应该打开
    assert breaker.state == CircuitState.OPEN
    
    # 下一次调用应该被拒绝
    with pytest.raises(CircuitBreakerOpenError):
        await breaker.call(fail_func)


@pytest.mark.asyncio
async def test_circuit_breaker_half_open():
    """测试熔断器半开状态"""
    breaker = CircuitBreaker(
        failure_threshold=2,
        recovery_timeout=0.5,
        success_threshold=1,
    )
    
    async def fail_func():
        raise ConnectionError("失败")
    
    async def success_func():
        return "success"
    
    # 触发失败打开熔断器
    for _ in range(2):
        with pytest.raises(ConnectionError):
            await breaker.call(fail_func)
    
    assert breaker.state == CircuitState.OPEN
    
    # 等待恢复时间
    await asyncio.sleep(0.6)
    
    # 应该进入半开状态
    assert breaker.state == CircuitState.HALF_OPEN
    
    # 成功调用应该关闭熔断器
    result = await breaker.call(success_func)
    assert result == "success"
    assert breaker.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_circuit_breaker_half_open_failure():
    """测试熔断器半开状态失败"""
    breaker = CircuitBreaker(
        failure_threshold=2,
        recovery_timeout=0.5,
        success_threshold=2,
    )
    
    async def fail_func():
        raise ConnectionError("失败")
    
    # 触发失败打开熔断器
    for _ in range(2):
        with pytest.raises(ConnectionError):
            await breaker.call(fail_func)
    
    # 等待恢复时间
    await asyncio.sleep(0.6)
    
    # 半开状态失败应该重新打开
    with pytest.raises(ConnectionError):
        await breaker.call(fail_func)
    
    assert breaker.state == CircuitState.OPEN


@pytest.mark.asyncio
async def test_circuit_breaker_reset():
    """测试熔断器重置"""
    breaker = CircuitBreaker(failure_threshold=2)
    
    async def fail_func():
        raise ConnectionError("失败")
    
    # 触发失败打开熔断器
    for _ in range(2):
        with pytest.raises(ConnectionError):
            await breaker.call(fail_func)
    
    assert breaker.state == CircuitState.OPEN
    
    # 重置熔断器
    breaker.reset()
    
    assert breaker.state == CircuitState.CLOSED
    assert breaker.failure_count == 0


def test_circuit_breaker_stats():
    """测试熔断器统计"""
    breaker = CircuitBreaker(failure_threshold=3)
    
    stats = breaker.stats
    assert stats.total_calls == 0
    assert stats.successful_calls == 0
    assert stats.failed_calls == 0
    assert stats.rejected_calls == 0


@pytest.mark.asyncio
async def test_circuit_breaker_expected_exception():
    """测试熔断器期望异常"""
    breaker = CircuitBreaker(
        failure_threshold=2,
        expected_exception=(ConnectionError,),
    )
    
    async def value_error_func():
        raise ValueError("参数错误")
    
    async def connection_error_func():
        raise ConnectionError("连接错误")
    
    # ValueError不应该触发熔断
    with pytest.raises(ValueError):
        await breaker.call(value_error_func)
    
    assert breaker.state == CircuitState.CLOSED
    
    # ConnectionError应该触发熔断
    for _ in range(2):
        with pytest.raises(ConnectionError):
            await breaker.call(connection_error_func)
    
    assert breaker.state == CircuitState.OPEN


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
