"""重试策略单元测试"""

import asyncio
import pytest
from reliability import RetryPolicy, RetryableError
from reliability.retry import retry_with_policy


@pytest.mark.asyncio
async def test_retry_success_on_first_attempt():
    """测试第一次尝试就成功"""
    attempt_count = 0
    
    async def success_func():
        nonlocal attempt_count
        attempt_count += 1
        return "success"
    
    policy = RetryPolicy(max_attempts=3)
    retryable = retry_with_policy(policy)(success_func)
    
    result = await retryable()
    assert result == "success"
    assert attempt_count == 1


@pytest.mark.asyncio
async def test_retry_success_after_failures():
    """测试失败后重试成功"""
    attempt_count = 0
    
    async def flaky_func():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise ConnectionError("网络错误")
        return "success"
    
    policy = RetryPolicy(
        max_attempts=5,
        base_delay=0.1,
        retryable_exceptions=(ConnectionError,),
    )
    retryable = retry_with_policy(policy)(flaky_func)
    
    result = await retryable()
    assert result == "success"
    assert attempt_count == 3


@pytest.mark.asyncio
async def test_retry_exhausted():
    """测试重试次数耗尽"""
    attempt_count = 0
    
    async def always_fail():
        nonlocal attempt_count
        attempt_count += 1
        raise ConnectionError("总是失败")
    
    policy = RetryPolicy(
        max_attempts=3,
        base_delay=0.1,
        retryable_exceptions=(ConnectionError,),
    )
    retryable = retry_with_policy(policy)(always_fail)
    
    with pytest.raises(RetryableError):
        await retryable()
    
    assert attempt_count == 3


@pytest.mark.asyncio
async def test_retry_non_retryable_exception():
    """测试不可重试的异常"""
    attempt_count = 0
    
    async def value_error_func():
        nonlocal attempt_count
        attempt_count += 1
        raise ValueError("参数错误")
    
    policy = RetryPolicy(
        max_attempts=3,
        retryable_exceptions=(ConnectionError,),
    )
    retryable = retry_with_policy(policy)(value_error_func)
    
    with pytest.raises(ValueError):
        await retryable()
    
    assert attempt_count == 1  # 不重试


def test_retry_policy_delay_calculation():
    """测试延迟时间计算"""
    policy = RetryPolicy(
        base_delay=1.0,
        backoff_multiplier=2.0,
        jitter=False,
    )
    
    assert policy.calculate_delay(0) == 1.0
    assert policy.calculate_delay(1) == 2.0
    assert policy.calculate_delay(2) == 4.0
    assert policy.calculate_delay(3) == 8.0


def test_retry_policy_max_delay():
    """测试最大延迟限制"""
    policy = RetryPolicy(
        base_delay=1.0,
        backoff_multiplier=2.0,
        max_delay=5.0,
        jitter=False,
    )
    
    assert policy.calculate_delay(10) == 5.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
