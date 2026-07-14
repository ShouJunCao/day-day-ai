"""
多模型网关 - 统一管理和路由多个大模型API

提供生产级的多模型网关服务，支持：
- 统一API接口（OpenAI兼容）
- 智能路由策略（成本优先、质量优先、轮询）
- 预算控制和限流
- 自动故障转移
- 请求日志和监控
"""

__version__ = "1.0.0"
__author__ = "AI Gateway Team"

from .config import GatewayConfig, ModelConfig
from .registry import ModelRegistry
from .router import ModelRouter
from .middleware import BudgetMiddleware, RateLimitMiddleware, LoggingMiddleware

__all__ = [
    "GatewayConfig",
    "ModelConfig",
    "ModelRegistry",
    "ModelRouter",
    "BudgetMiddleware",
    "RateLimitMiddleware",
    "LoggingMiddleware",
]
