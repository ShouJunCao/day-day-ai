"""
预算控制器 - 防止API调用费用超支

在生产环境中，大模型API的费用可能因以下原因失控：
    - 恶意用户发送超长prompt
    - 代码bug导致无限循环调用
    - 并发量激增超出预期
    - 用户滥用免费额度

本模块实现多层预算控制机制，确保费用在可控范围内。

控制层级：
    1. 单次请求：限制单条prompt的最大token数
    2. 用户级别：每个用户每日/每月预算上限
    3. 全局级别：系统总预算上限
    4. 速率限制：每分钟最大请求数
"""

import time
import logging
from typing import Dict, Optional
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class BudgetConfig:
    """预算配置

    Attributes:
        max_tokens_per_request: 单次请求最大token数
        daily_budget_per_user: 每用户每日预算（美元）
        monthly_budget_per_user: 每用户每月预算（美元）
        global_daily_budget: 系统每日总预算（美元）
        max_requests_per_minute: 每分钟最大请求数（限流）
    """

    max_tokens_per_request: int = 4000
    daily_budget_per_user: float = 5.0
    monthly_budget_per_user: float = 50.0
    global_daily_budget: float = 100.0
    max_requests_per_minute: int = 60


class BudgetExceededError(Exception):
    """预算超限异常

    Attributes:
        reason: 超限原因描述
        current_usage: 当前用量
        limit: 限额
    """

    def __init__(self, reason: str, current_usage: float, limit: float):
        self.reason = reason
        self.current_usage = current_usage
        self.limit = limit
        super().__init__(
            f"预算超限: {reason} "
            f"(当前: ${current_usage:.4f}, 限额: ${limit:.4f})"
        )


class BudgetController:
    """预算控制器

    实现多层预算控制，在每次API调用前检查预算状态，
    超限时抛出异常阻止调用。

    Example:
        config = BudgetConfig(daily_budget_per_user=2.0)
        controller = BudgetController(config)

        # 调用前检查
        controller.check_budget(user_id="user_123", estimated_cost=0.01)

        # 记录实际消费
        controller.record_cost(user_id="user_123", cost=0.008)
    """

    def __init__(self, config: Optional[BudgetConfig] = None):
        """初始化预算控制器

        Args:
            config: 预算配置，不传则使用默认配置
        """
        self.config = config or BudgetConfig()

        # 用量追踪（内存存储，生产环境应使用Redis/DB）
        self.daily_usage: Dict[str, float] = defaultdict(float)
        self.monthly_usage: Dict[str, float] = defaultdict(float)
        self.global_daily_usage: float = 0.0

        # 速率限制追踪
        self.request_timestamps: Dict[str, list] = defaultdict(list)

    def check_request_size(self, token_count: int) -> None:
        """检查单次请求的token数是否超限

        Args:
            token_count: 请求的token数

        Raises:
            BudgetExceededError: token数超过限制
        """
        if token_count > self.config.max_tokens_per_request:
            raise BudgetExceededError(
                reason="单次请求token数超限",
                current_usage=token_count,
                limit=self.config.max_tokens_per_request,
            )

    def check_rate_limit(self, user_id: str) -> None:
        """检查用户请求频率是否超限

        使用滑动窗口算法：统计最近60秒内的请求数。

        Args:
            user_id: 用户标识

        Raises:
            BudgetExceededError: 请求频率超限
        """
        now = time.time()
        window_start = now - 60  # 60秒滑动窗口

        # 清理过期记录
        self.request_timestamps[user_id] = [
            ts for ts in self.request_timestamps[user_id]
            if ts > window_start
        ]

        current_count = len(self.request_timestamps[user_id])

        if current_count >= self.config.max_requests_per_minute:
            raise BudgetExceededError(
                reason="请求频率超限（每分钟）",
                current_usage=current_count,
                limit=self.config.max_requests_per_minute,
            )

        # 记录本次请求时间
        self.request_timestamps[user_id].append(now)

    def check_budget(self, user_id: str, estimated_cost: float) -> None:
        """检查用户预算是否充足

        在执行API调用前，检查：
        1. 用户每日预算
        2. 用户每月预算
        3. 系统全局每日预算

        Args:
            user_id: 用户标识
            estimated_cost: 预估本次调用费用

        Raises:
            BudgetExceededError: 预算不足
        """
        # 检查用户每日预算
        daily_used = self.daily_usage[user_id]
        if daily_used + estimated_cost > self.config.daily_budget_per_user:
            raise BudgetExceededError(
                reason=f"用户 {user_id} 每日预算超限",
                current_usage=daily_used,
                limit=self.config.daily_budget_per_user,
            )

        # 检查用户每月预算
        monthly_used = self.monthly_usage[user_id]
        if monthly_used + estimated_cost > self.config.monthly_budget_per_user:
            raise BudgetExceededError(
                reason=f"用户 {user_id} 每月预算超限",
                current_usage=monthly_used,
                limit=self.config.monthly_budget_per_user,
            )

        # 检查全局每日预算
        if self.global_daily_usage + estimated_cost > self.config.global_daily_budget:
            raise BudgetExceededError(
                reason="系统全局每日预算超限",
                current_usage=self.global_daily_usage,
                limit=self.config.global_daily_budget,
            )

    def record_cost(self, user_id: str, cost: float) -> None:
        """记录实际消费

        API调用完成后，将实际费用计入各层级预算。

        Args:
            user_id: 用户标识
            cost: 实际费用（美元）
        """
        self.daily_usage[user_id] += cost
        self.monthly_usage[user_id] += cost
        self.global_daily_usage += cost

        logger.info(
            f"用户 {user_id} 消费 ${cost:.6f} | "
            f"今日: ${self.daily_usage[user_id]:.4f} | "
            f"本月: ${self.monthly_usage[user_id]:.4f}"
        )

    def get_usage_report(self, user_id: str) -> Dict:
        """获取用户用量报告

        Args:
            user_id: 用户标识

        Returns:
            用量统计信息字典
        """
        return {
            "user_id": user_id,
            "daily_used": self.daily_usage[user_id],
            "daily_limit": self.config.daily_budget_per_user,
            "daily_remaining": max(
                0,
                self.config.daily_budget_per_user - self.daily_usage[user_id]
            ),
            "monthly_used": self.monthly_usage[user_id],
            "monthly_limit": self.config.monthly_budget_per_user,
            "monthly_remaining": max(
                0,
                self.config.monthly_budget_per_user - self.monthly_usage[user_id]
            ),
            "global_daily_used": self.global_daily_usage,
            "global_daily_limit": self.config.global_daily_budget,
        }


# --- 使用示例 ---
if __name__ == "__main__":
    # 配置预算限制
    config = BudgetConfig(
        max_tokens_per_request=2000,
        daily_budget_per_user=1.0,
        monthly_budget_per_user=10.0,
        global_daily_budget=50.0,
        max_requests_per_minute=10,
    )

    controller = BudgetController(config)

    # 模拟正常调用
    print("=" * 50)
    print("模拟API调用")
    print("=" * 50)

    for i in range(5):
        try:
            user = "user_001"
            controller.check_rate_limit(user)
            controller.check_budget(user, estimated_cost=0.15)
            controller.record_cost(user, cost=0.12)
            print(f"✅ 第 {i+1} 次调用成功")
        except BudgetExceededError as e:
            print(f"❌ 第 {i+1} 次调用被拦截: {e.reason}")

    # 打印用量报告
    print(f"\n{'=' * 50}")
    print("用量报告")
    print(f"{'=' * 50}")
    report = controller.get_usage_report("user_001")
    for key, value in report.items():
        if isinstance(value, float):
            print(f"  {key}: ${value:.4f}")
        else:
            print(f"  {key}: {value}")
