"""
dialogue_metrics.py — 对话质量评估指标
实现对话系统的核心评估指标：任务完成率、用户满意度、
平均轮次、首次响应时间、兜底率等。
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timedelta
from enum import Enum


class SatisfactionScore(Enum):
    """用户满意度评分（1-5 星）"""
    VERY_BAD = 1
    BAD = 2
    NEUTRAL = 3
    GOOD = 4
    EXCELLENT = 5


@dataclass
class DialogueSession:
    """单次对话会话的完整记录"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_turns: int = 0
    intent: Optional[str] = None
    completed: bool = False
    satisfaction: Optional[SatisfactionScore] = None
    fallback_count: int = 0
    escalation_count: int = 0
    first_response_ms: float = 0.0
    avg_response_ms: float = 0.0
    _response_times: list[float] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        """对话总时长（秒）"""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    def record_response(self, response_ms: float):
        """记录一次响应时间"""
        self._response_times.append(response_ms)
        if self.first_response_ms == 0.0:
            self.first_response_ms = response_ms

    @property
    def avg_response(self) -> float:
        """平均响应时间"""
        if not self._response_times:
            return 0.0
        return sum(self._response_times) / len(self._response_times)

    def close(self, completed: bool = False):
        """结束对话会话"""
        self.end_time = datetime.now()
        self.completed = completed


@dataclass
class DialogueMetricsCollector:
    """
    对话质量指标收集器：聚合多个对话会话的数据，
    计算系统级的质量指标。
    """

    sessions: list[DialogueSession] = field(default_factory=list)

    def add_session(self, session: DialogueSession):
        """添加一个对话会话"""
        self.sessions.append(session)

    @property
    def total_sessions(self) -> int:
        """总会话数"""
        return len(self.sessions)

    @property
    def task_completion_rate(self) -> float:
        """
        任务完成率：成功完成任务的会话占比。
        核心指标，反映系统是否"有用"。
        """
        if not self.sessions:
            return 0.0
        completed = sum(1 for s in self.sessions if s.completed)
        return completed / len(self.sessions)

    @property
    def avg_turns(self) -> float:
        """
        平均对话轮次：每个会话的平均消息数。
        过高说明流程冗长，过低可能说明用户容易放弃。
        """
        if not self.sessions:
            return 0.0
        total = sum(s.total_turns for s in self.sessions)
        return total / len(self.sessions)

    @property
    def avg_duration(self) -> float:
        """平均对话时长（秒）"""
        durations = [s.duration_seconds for s in self.sessions if s.end_time]
        if not durations:
            return 0.0
        return sum(durations) / len(durations)

    @property
    def fallback_rate(self) -> float:
        """
        兜底率：触发了兜底策略的会话占比。
        超过 20% 说明意图识别或槽位填充有严重问题。
        """
        if not self.sessions:
            return 0.0
        with_fallback = sum(1 for s in self.sessions if s.fallback_count > 0)
        return with_fallback / len(self.sessions)

    @property
    def escalation_rate(self) -> float:
        """转人工率：触发人工转接的会话占比"""
        if not self.sessions:
            return 0.0
        with_escalation = sum(1 for s in self.sessions if s.escalation_count > 0)
        return with_escalation / len(self.sessions)

    @property
    def avg_first_response_ms(self) -> float:
        """平均首次响应时间（毫秒）"""
        times = [s.first_response_ms for s in self.sessions if s.first_response_ms > 0]
        if not times:
            return 0.0
        return sum(times) / len(times)

    @property
    def avg_satisfaction(self) -> float:
        """平均用户满意度（1-5 分）"""
        scores = [s.satisfaction.value for s in self.sessions if s.satisfaction]
        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    def get_summary_report(self) -> dict:
        """生成完整的评估报告"""
        return {
            "total_sessions": self.total_sessions,
            "task_completion_rate": round(self.task_completion_rate, 3),
            "avg_turns": round(self.avg_turns, 2),
            "avg_duration_sec": round(self.avg_duration, 1),
            "fallback_rate": round(self.fallback_rate, 3),
            "escalation_rate": round(self.escalation_rate, 3),
            "avg_first_response_ms": round(self.avg_first_response_ms, 1),
            "avg_satisfaction": round(self.avg_satisfaction, 2),
        }
