"""
中间件模块

提供请求日志、限流、预算控制等横切关注点。
"""

import time
import logging
from typing import Dict, Callable
from collections import defaultdict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from .config import BudgetConfig

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件
    
    记录每个请求的基本信息：
    - 请求方法、路径
    - 响应状态码
    - 处理耗时
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # 执行请求
        response = await call_next(request)
        
        # 计算耗时
        duration = time.time() - start_time
        
        # 记录日志
        logger.info(
            f"{request.method} {request.url.path} "
            f"- {response.status_code} "
            f"- {duration:.3f}s"
        )
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """速率限制中间件
    
    基于滑动窗口算法限制每个用户的请求频率。
    """
    
    def __init__(self, app, rate_limit: int):
        """初始化限流中间件
        
        Args:
            app: FastAPI应用实例
            rate_limit: 每分钟最大请求数
        """
        super().__init__(app)
        self.rate_limit = rate_limit
        self.request_timestamps: Dict[str, list] = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 获取用户标识（这里简化为IP地址）
        user_id = request.client.host if request.client else "unknown"
        
        # 检查限流
        if not self._check_rate_limit(user_id):
            logger.warning(f"用户 {user_id} 请求频率超限")
            return Response(
                content='{"error": "Rate limit exceeded"}',
                status_code=429,
                media_type="application/json"
            )
        
        # 执行请求
        response = await call_next(request)
        
        return response
    
    def _check_rate_limit(self, user_id: str) -> bool:
        """检查是否超过限流阈值
        
        Args:
            user_id: 用户标识
            
        Returns:
            True表示未超限，False表示已超限
        """
        now = time.time()
        window_start = now - 60  # 60秒窗口
        
        # 清理过期记录
        self.request_timestamps[user_id] = [
            ts for ts in self.request_timestamps[user_id]
            if ts > window_start
        ]
        
        # 检查当前窗口内的请求数
        current_count = len(self.request_timestamps[user_id])
        if current_count >= self.rate_limit:
            return False
        
        # 记录本次请求
        self.request_timestamps[user_id].append(now)
        
        return True


class BudgetMiddleware(BaseHTTPMiddleware):
    """预算控制中间件
    
    跟踪全局和用户级别的费用，超限时拒绝请求。
    """
    
    def __init__(self, app, budget_config: BudgetConfig):
        """初始化预算中间件
        
        Args:
            app: FastAPI应用实例
            budget_config: 预算配置
        """
        super().__init__(app)
        self.config = budget_config
        self.global_daily_cost: float = 0.0
        self.user_daily_costs: Dict[str, float] = defaultdict(float)
        self.day_start = time.time()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 检查是否需要重置每日预算
        self._check_day_reset()
        
        # 获取用户标识
        user_id = request.client.host if request.client else "unknown"
        
        # 检查预算（这里简化，实际应该从请求体中预估token数）
        # 在生产环境中，需要先解析请求体，计算预估token，然后检查预算
        
        # 执行请求
        response = await call_next(request)
        
        # 从响应中获取实际费用（如果有的话）
        # 在生产环境中，应该从response中提取usage信息并记录费用
        
        return response
    
    def record_cost(self, user_id: str, cost: float) -> None:
        """记录实际费用
        
        Args:
            user_id: 用户标识
            cost: 本次请求的费用
        """
        self._check_day_reset()
        
        self.global_daily_cost += cost
        self.user_daily_costs[user_id] += cost
        
        logger.info(
            f"记录费用: 用户={user_id}, 费用=${cost:.6f}, "
            f"今日总费用=${self.global_daily_cost:.4f}"
        )
    
    def check_budget(self, user_id: str, estimated_cost: float) -> bool:
        """检查预算是否充足
        
        Args:
            user_id: 用户标识
            estimated_cost: 预估费用
            
        Returns:
            True表示预算充足，False表示预算不足
        """
        self._check_day_reset()
        
        # 检查全局预算
        if self.global_daily_cost + estimated_cost > self.config.global_daily_limit:
            logger.warning(
                f"全局预算超限: 当前=${self.global_daily_cost:.4f}, "
                f"预估=${estimated_cost:.6f}, "
                f"限额=${self.config.global_daily_limit:.2f}"
            )
            return False
        
        # 检查用户预算
        user_cost = self.user_daily_costs[user_id]
        if user_cost + estimated_cost > self.config.user_daily_limit:
            logger.warning(
                f"用户预算超限: 用户={user_id}, "
                f"当前=${user_cost:.4f}, "
                f"预估=${estimated_cost:.6f}, "
                f"限额=${self.config.user_daily_limit:.2f}"
            )
            return False
        
        return True
    
    def _check_day_reset(self) -> None:
        """检查是否需要重置每日预算（每24小时重置）"""
        now = time.time()
        if now - self.day_start > 86400:  # 24小时
            logger.info("重置每日预算")
            self.global_daily_cost = 0.0
            self.user_daily_costs.clear()
            self.day_start = now
