"""
example_usage.py — 4.5 对话质量评估指标 使用示例
"""
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dialogue_metrics import DialogueSession, DialogueMetricsCollector, SatisfactionScore
from quality_analyzer import QualityAnalyzer


def demo_metrics_collection():
    """演示指标收集"""
    print("=" * 60)
    print("  对话质量评估指标 — 数据收集演示")
    print("=" * 60)

    collector = DialogueMetricsCollector()

    # 模拟 10 个对话会话
    sessions_data = [
        # (session_id, turns, completed, satisfaction, fallback, escalation, resp_ms)
        ("S001", 4, True, SatisfactionScore.EXCELLENT, 0, 0, 320),
        ("S002", 6, True, SatisfactionScore.GOOD, 0, 0, 450),
        ("S003", 3, True, SatisfactionScore.GOOD, 0, 0, 280),
        ("S004", 8, False, SatisfactionScore.NEUTRAL, 2, 0, 1200),
        ("S005", 5, True, SatisfactionScore.EXCELLENT, 0, 0, 350),
        ("S006", 12, False, SatisfactionScore.BAD, 3, 1, 2500),
        ("S007", 3, True, SatisfactionScore.GOOD, 0, 0, 290),
        ("S008", 7, True, SatisfactionScore.GOOD, 1, 0, 600),
        ("S009", 4, True, SatisfactionScore.EXCELLENT, 0, 0, 310),
        ("S010", 9, False, SatisfactionScore.NEUTRAL, 2, 0, 1800),
    ]

    base_time = datetime(2026, 7, 18, 9, 0)

    for i, (sid, turns, completed, sat, fb, esc, resp) in enumerate(sessions_data):
        session = DialogueSession(
            session_id=sid,
            start_time=base_time + timedelta(minutes=i * 5),
            total_turns=turns,
            completed=completed,
            satisfaction=sat,
            fallback_count=fb,
            escalation_count=esc,
        )
        session.record_response(resp)
        session.close(completed=completed)
        collector.add_session(session)

    # 打印汇总报告
    report = collector.get_summary_report()
    print("\n📊 评估报告摘要:")
    for key, value in report.items():
        labels = {
            "total_sessions": "总会话数",
            "task_completion_rate": "任务完成率",
            "avg_turns": "平均轮次",
            "avg_duration_sec": "平均时长(秒)",
            "fallback_rate": "兜底率",
            "escalation_rate": "转人工率",
            "avg_first_response_ms": "平均首响(ms)",
            "avg_satisfaction": "平均满意度",
        }
        label = labels.get(key, key)
        if "rate" in key:
            value = f"{value:.1%}"
        print(f"  {label}: {value}")


def demo_quality_analysis():
    """演示质量分析"""
    print("\n" + "=" * 60)
    print("  对话质量分析器 — 诊断报告演示")
    print("=" * 60)

    collector = DialogueMetricsCollector()

    # 模拟一组有问题的数据（低完成率、高兜底率）
    problem_sessions = [
        ("P001", 11, False, SatisfactionScore.BAD, 3, 1, 3000),
        ("P002", 8, False, SatisfactionScore.NEUTRAL, 2, 0, 2500),
        ("P003", 15, False, SatisfactionScore.VERY_BAD, 4, 1, 4000),
        ("P004", 5, True, SatisfactionScore.GOOD, 0, 0, 500),
        ("P005", 10, False, SatisfactionScore.NEUTRAL, 3, 1, 3500),
        ("P006", 6, True, SatisfactionScore.GOOD, 0, 0, 600),
        ("P007", 13, False, SatisfactionScore.BAD, 3, 1, 2800),
        ("P008", 4, True, SatisfactionScore.EXCELLENT, 0, 0, 400),
        ("P009", 9, False, SatisfactionScore.NEUTRAL, 2, 0, 2200),
        ("P010", 7, True, SatisfactionScore.GOOD, 1, 0, 800),
    ]

    base_time = datetime(2026, 7, 19, 10, 0)
    for i, (sid, turns, completed, sat, fb, esc, resp) in enumerate(problem_sessions):
        session = DialogueSession(
            session_id=sid,
            start_time=base_time + timedelta(minutes=i * 3),
            total_turns=turns,
            completed=completed,
            satisfaction=sat,
            fallback_count=fb,
            escalation_count=esc,
        )
        session.record_response(resp)
        session.close(completed=completed)
        collector.add_session(session)

    # 执行分析
    analyzer = QualityAnalyzer(collector=collector)
    issues = analyzer.analyze()

    print(f"\n系统健康度: {analyzer.get_health_score()}/100")
    print(f"发现问题: {len(issues)} 个\n")

    severity_icons = {"critical": "🔴", "warning": "🟡", "info": "🔵"}
    for issue in issues:
        icon = severity_icons.get(issue.severity, "⚪")
        print(f"  {icon} [{issue.severity}] {issue.description}")
        print(f"     指标: {issue.metric_name} = {issue.current_value:.3f} "
              f"(阈值: {issue.threshold:.3f})")
        print(f"     建议: {issue.suggestion}")
        print()


if __name__ == "__main__":
    demo_metrics_collection()
    demo_quality_analysis()
