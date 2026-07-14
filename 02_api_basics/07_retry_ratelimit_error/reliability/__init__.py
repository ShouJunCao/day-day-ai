"""
API可靠性工具包

提供重试、限流、错误处理等最佳实践
"""

__version__ = "1.0.0"

from .retry import RetryPolicy, RetryableError, with_retry
from .ratelimit import RateLimiter, TokenBucket, SlidingWindow
from .errors import (
    APIError,
    RateLimitError,
    TimeoutError,
    AuthenticationError,
    NetworkError,
    ServerError,
)

__all__ = [
    "RetryPolicy",
    "RetryableError",
    "with_retry",
    "RateLimiter",
    "TokenBucket",
    "SlidingWindow",
    "APIError",
    "RateLimitError",
    "TimeoutError",
    "AuthenticationError",
    "NetworkError",
    "ServerError",
]
