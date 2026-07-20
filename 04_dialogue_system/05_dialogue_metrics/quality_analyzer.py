"""
quality_analyzer.py — 对话质量分析器
对收集到的指标数据进行深度分析，识别薄弱环节、
发现趋势，并生成改进建议。
"""
from dataclasses import dataclass, field
from typing import Optional
from dialogue_metrics import DialogueMetricsCollector, DialogueSession


@dataclass
class IssueReport:
    """单个问题报告"""
    issue_type: str
    severity: str              # critical / warning / info
    description: str
    metric_name: str
    current_value: float
    threshold: float
    suggestion: str


@dataclass
class QualityAnalyzer:
    """
    对话质量分析器：基于指标数据生成诊断报告和改进建议。
    """

    collector: DialogueMetricsCollector
    thresholds: dict = field(default_factory=dict)
    issues: list[IssueReport] = field(default_factory=list)

    def __post_init__(self):
        self._init_default_thresholds()

    def _init_default_thresholds(self):
        """初始化默认告警阈值"""
        self.thresholds = {
            "task_completion_rate": 0.7,    # 低于 70% 告警
            "avg_turns": 10,                # 超过 10 轮告警
            "fallback_rate": 0.2,           # 超过 20% 告警
            "escalation_rate": 0.1,         # 超过 10% 告警
            "avg_first_response_ms": 2000,  # 超过 2 秒告警
            "avg_satisfaction": 3.0,        # 低于 3 分告警
        }

    def analyze(self) -> list[IssueReport]:
        """执行全面分析，返回问题列表"""
        self.issues.clear()

        self._check_completion_rate()
        self._check_avg_turns()
        self._check_fallback_rate()
        self._check_escalation_rate()
        self._check_response_time()
        self._check_satisfaction()

        return self.issues

    def _check_completion_rate(self):
        """检查任务完成率"""
        rate = self.collector.task_completion_rate
        threshold = self.thresholds["task_completion_rate"]
        if rate < threshold:
            self.issues.append(IssueReport(
                issue_type="low_completion_rate",
                severity="critical",
                description="任务完成率低于阈值",
                metric_name="task_completion_rate",
                current_value=rate,
                threshold=threshold,
                suggestion=(
                    "检查意图识别准确率，优化槽位收集流程，"
                    "增加快捷选项降低用户输入负担"
                ),
            ))

    def _check_avg_turns(self):
        """检查平均对话轮次"""
        turns = self.collector.avg_turns
        threshold = self.thresholds["avg_turns"]
        if turns > threshold:
            self.issues.append(IssueReport(
                issue_type="high_turn_count",
                severity="warning",
                description="平均对话轮次过高",
                metric_name="avg_turns",
                current_value=turns,
                threshold=threshold,
                suggestion=(
                    "优化槽位收集效率，支持一次提供多个信息，"
                    "考虑使用表单或按钮替代多轮追问"
                ),
            ))

    def _check_fallback_rate(self):
        """检查兜底率"""
        rate = self.collector.fallback_rate
        threshold = self.thresholds["fallback_rate"]
        if rate > threshold:
            self.issues.append(IssueReport(
                issue_type="high_fallback_rate",
                severity="critical",
                description="兜底率超过阈值",
                metric_name="fallback_rate",
                current_value=rate,
                threshold=threshold,
                suggestion=(
                    "扩展意图覆盖范围，增加训练样本，"
                    "优化澄清引擎的歧义消除策略"
                ),
            ))

    def _check_escalation_rate(self):
        """检查转人工率"""
        rate = self.collector.escalation_rate
        threshold = self.thresholds["escalation_rate"]
        if rate > threshold:
            self.issues.append(IssueReport(
                issue_type="high_escalation_rate",
                severity="critical",
                description="转人工率超过阈值",
                metric_name="escalation_rate",
                current_value=rate,
                threshold=threshold,
                suggestion=(
                    "分析转人工前的最后几轮对话，"
                    "识别系统能力的盲区，优先补充高频需求"
                ),
            ))

    def _check_response_time(self):
        """检查响应时间"""
        ms = self.collector.avg_first_response_ms
        threshold = self.thresholds["avg_first_response_ms"]
        if ms > threshold:
            self.issues.append(IssueReport(
                issue_type="slow_response",
                severity="warning",
                description="平均首次响应时间过长",
                metric_name="avg_first_response_ms",
                current_value=ms,
                threshold=threshold,
                suggestion=(
                    "优化 LLM 调用延迟，增加缓存策略，"
                    "对高频意图使用预生成话术"
                ),
            ))

    def _check_satisfaction(self):
        """检查用户满意度"""
        score = self.collector.avg_satisfaction
        threshold = self.thresholds["avg_satisfaction"]
        if score < threshold and score > 0:
            self.issues.append(IssueReport(
                issue_type="low_satisfaction",
                severity="warning",
                description="用户满意度低于预期",
                metric_name="avg_satisfaction",
                current_value=score,
                threshold=threshold,
                suggestion=(
                    "收集低分会话的反馈，分析用户不满原因，"
                    "针对性优化话术和流程"
                ),
            ))

    def get_health_score(self) -> float:
        """
        计算系统健康度评分（0-100）。
        基于多个指标的加权综合评分。
        """
        weights = {
            "task_completion_rate": 0.30,
            "avg_turns": 0.15,
            "fallback_rate": 0.20,
            "escalation_rate": 0.15,
            "avg_satisfaction": 0.20,
        }

        score = 0.0

        # 任务完成率：越高越好
        score += weights["task_completion_rate"] * self.collector.task_completion_rate * 100

        # 平均轮次：越低越好（上限 15 轮为满分）
        turns_score = max(0, 1 - self.collector.avg_turns / 15)
        score += weights["avg_turns"] * turns_score * 100

        # 兜底率：越低越好
        fallback_score = max(0, 1 - self.collector.fallback_rate)
        score += weights["fallback_rate"] * fallback_score * 100

        # 转人工率：越低越好
        escalation_score = max(0, 1 - self.collector.escalation_rate)
        score += weights["escalation_rate"] * escalation_score * 100

        # 满意度：越高越好（满分 5 分）
        if self.collector.avg_satisfaction > 0:
            sat_score = self.collector.avg_satisfaction / 5
            score += weights["avg_satisfaction"] * sat_score * 100

        return round(score, 1)
