"""
评估指标与聚合逻辑
计算基准分数、方差分析、分布统计与回归检测。
"""
from __future__ import annotations
import math
import statistics
from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True)
class MetricSummary:
    metric_name: str
    mean: float
    median: float
    std_dev: float
    min_val: float
    max_val: float
    p5: float
    p95: float
    sample_size: int

    def __str__(self) -> str:
        return (
            f"{self.metric_name}: μ={self.mean:.1f} σ={self.std_dev:.1f} "
            f"[{self.min_val:.1f}–{self.max_val:.1f}] n={self.sample_size}"
        )

@dataclass
class EvaluationSummary:
    summaries: list[MetricSummary]
    regression_detected: bool
    regression_metrics: list[str]

def compute_summary(metric_name: str, scores: Iterable[float]) -> MetricSummary:
    values = list(scores)
    if not values:
        return MetricSummary(metric_name, 0, 0, 0, 0, 0, 0, 0, 0)
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    mean = statistics.mean(sorted_vals)
    median = statistics.median(sorted_vals)
    std_dev = statistics.stdev(sorted_vals) if n > 1 else 0.0
    p5 = sorted_vals[max(0, int(n * 0.05))]
    p95 = sorted_vals[min(n - 1, int(n * 0.95))]
    return MetricSummary(
        metric_name, mean, median, std_dev,
        sorted_vals[0], sorted_vals[-1], p5, p95, n
    )

def detect_regressions(
    current: list[MetricSummary],
    baseline: dict[str, float],
    threshold: float = 5.0
) -> EvaluationSummary:
    """
    对比当前评估结果与基线，检测是否存在显著退化。
    """
    regressions: list[str] = []
    for summary in current:
        base_score = baseline.get(summary.metric_name)
        if base_score is not None:
            if summary.mean < (base_score - threshold):
                regressions.append(summary.metric_name)
    return EvaluationSummary(
        summaries=current,
        regression_detected=bool(regressions),
        regression_metrics=regressions
    )

def aggregate_scores(
    results: list[dict[str, float]],
    baseline: dict[str, float] | None = None
) -> EvaluationSummary:
    """将多次评估结果聚合为统计摘要"""
    if not results:
        return EvaluationSummary([], False, [])
    metric_names = set()
    for r in results:
        metric_names.update(r.keys())
    summaries: list[MetricSummary] = []
    for name in metric_names:
        scores = [r[name] for r in results if name in r]
        summaries.append(compute_summary(name, scores))
    baseline = baseline or {}
    return detect_regressions(summaries, baseline)
