"""
用量监控与告警 - 实时追踪API消费情况

生产环境需要持续监控API使用情况，及时发现异常：
    - 费用突然飙升（可能是代码bug或恶意攻击）
    - 某用户消费远超其他人（需要限流）
    - 接近预算上限（需要提前告警）

本模块实现轻量级的用量监控系统，支持：
    1. 实时用量统计
    2. 多维度聚合分析
    3. 阈值告警（回调通知）
    4. 用量报告导出
"""

import time
import logging
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class AlertRule:
    """告警规则

    Attributes:
        name: 规则名称
        condition: 触发条件描述
        threshold: 阈值
        callback: 触发时的回调函数
        last_triggered: 上次触发时间（避免频繁告警）
        cooldown_seconds: 冷却时间（秒）
    """

    name: str
    condition: str
    threshold: float
    callback: Callable
    last_triggered: float = 0.0
    cooldown_seconds: float = 300.0  # 5分钟冷却


@dataclass
class UsageSnapshot:
    """用量快照

    Attributes:
        timestamp: 记录时间
        model: 模型名称
        user_id: 用户标识
        input_tokens: 输入token数
        output_tokens: 输出token数
        cost: 费用
    """

    timestamp: str
    model: str
    user_id: str
    input_tokens: int
    output_tokens: int
    cost: float


class UsageMonitor:
    """用量监控器

    功能：
    1. 记录每次API调用的用量
    2. 支持多维度的统计聚合（按用户、按模型、按时间）
    3. 自定义告警规则，超过阈值时触发回调

    Example:
        monitor = UsageMonitor()

        # 添加告警规则
        monitor.add_alert(
            name="单日费用超10美元",
            threshold=10.0,
            callback=lambda msg: send_email(msg),
        )

        # 记录用量
        monitor.record("user_123", "gpt-4o-mini", 500, 200, 0.001)
    """

    def __init__(self):
        """初始化用量监控器"""
        self.snapshots: List[UsageSnapshot] = []
        self.alerts: List[AlertRule] = []

        # 聚合缓存
        self.daily_cost_by_user: Dict[str, float] = defaultdict(float)
        self.daily_cost_by_model: Dict[str, float] = defaultdict(float)
        self.total_cost: float = 0.0

    def record(
        self,
        user_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost: float,
    ) -> None:
        """记录一次API调用的用量

        Args:
            user_id: 用户标识
            model: 使用的模型
            input_tokens: 输入token数
            output_tokens: 输出token数
            cost: 本次调用费用
        """
        snapshot = UsageSnapshot(
            timestamp=datetime.now().isoformat(),
            model=model,
            user_id=user_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
        )

        self.snapshots.append(snapshot)

        # 更新聚合数据
        self.daily_cost_by_user[user_id] += cost
        self.daily_cost_by_model[model] += cost
        self.total_cost += cost

        # 检查告警规则
        self._check_alerts()

    def add_alert(
        self,
        name: str,
        threshold: float,
        callback: Callable,
        cooldown_seconds: float = 300.0,
    ) -> None:
        """添加告警规则

        Args:
            name: 告警规则名称
            threshold: 触发阈值（总费用超过此值时触发）
            callback: 触发时调用的函数（接收告警消息参数）
            cooldown_seconds: 两次告警之间的最小间隔
        """
        alert = AlertRule(
            name=name,
            condition=f"总费用 > ${threshold}",
            threshold=threshold,
            callback=callback,
            cooldown_seconds=cooldown_seconds,
        )
        self.alerts.append(alert)

    def _check_alerts(self) -> None:
        """检查所有告警规则是否触发"""
        now = time.time()

        for alert in self.alerts:
            # 检查冷却时间
            if now - alert.last_triggered < alert.cooldown_seconds:
                continue

            # 检查阈值
            if self.total_cost > alert.threshold:
                message = (
                    f"⚠️ 告警触发: {alert.name}\n"
                    f"当前总费用: ${self.total_cost:.4f}\n"
                    f"阈值: ${alert.threshold:.4f}"
                )
                logger.warning(message)

                # 调用回调
                try:
                    alert.callback(message)
                except Exception as e:
                    logger.error(f"告警回调失败: {e}")

                alert.last_triggered = now

    def get_summary(self) -> Dict:
        """获取用量摘要报告

        Returns:
            包含多维度统计信息的字典
        """
        total_requests = len(self.snapshots)
        total_input = sum(s.input_tokens for s in self.snapshots)
        total_output = sum(s.output_tokens for s in self.snapshots)

        return {
            "total_requests": total_requests,
            "total_cost": round(self.total_cost, 6),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "cost_by_user": dict(self.daily_cost_by_user),
            "cost_by_model": dict(self.daily_cost_by_model),
            "avg_cost_per_request": (
                round(self.total_cost / total_requests, 6)
                if total_requests > 0 else 0
            ),
        }

    def get_top_users(self, top_n: int = 5) -> List[Dict]:
        """获取消费最高的用户

        Args:
            top_n: 返回的用户数量

        Returns:
            按消费从高到低排序的用户列表
        """
        sorted_users = sorted(
            self.daily_cost_by_user.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        return [
            {"user_id": uid, "cost": round(cost, 6)}
            for uid, cost in sorted_users[:top_n]
        ]


# --- 使用示例 ---
if __name__ == "__main__":
    monitor = UsageMonitor()

    # 添加告警规则
    def on_alert(message: str):
        print(f"\n🚨 告警通知:\n{message}\n")

    monitor.add_alert(
        name="总费用超过0.1美元",
        threshold=0.1,
        callback=on_alert,
        cooldown_seconds=10,
    )

    # 模拟API调用
    print("=" * 50)
    print("模拟API调用与监控")
    print("=" * 50)

    models = ["gpt-4o-mini", "deepseek-chat", "qwen-turbo"]
    users = ["user_001", "user_002", "user_003"]

    for i in range(20):
        user = users[i % len(users)]
        model = models[i % len(models)]
        input_t = 500 + i * 10
        output_t = 200 + i * 5
        cost = (input_t * 0.15 + output_t * 0.60) / 1_000_000

        monitor.record(user, model, input_t, output_t, cost)

    # 打印用量摘要
    print(f"\n{'=' * 50}")
    print("用量摘要")
    print(f"{'=' * 50}")
    summary = monitor.get_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

    print(f"\n消费最高的用户:")
    for user in monitor.get_top_users(3):
        print(f"  {user['user_id']}: ${user['cost']}")
