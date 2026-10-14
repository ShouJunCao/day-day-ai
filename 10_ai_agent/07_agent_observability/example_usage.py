"""
example_usage.py — Agent 可观测性演示
演示追踪器、指标收集器、评估器的使用。
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_observability import (
    AgentTracer,
    MetricsCollector,
    AgentEvaluator,
)


def demo_tracer():
    """演示追踪器"""
    print("=" * 60)
    print("  追踪器 (Tracer)")
    print("=" * 60)
    
    print("""
    追踪器提供以下功能：
    • 嵌套跨度：记录 Agent 执行的完整调用链
    • 时间戳：记录每个步骤的开始和结束时间
    • 元数据：关联工具参数、LLM 输出等上下文信息
    • 导出：生成 JSON 格式的追踪数据，用于后续分析
    """)
    
    tracer = AgentTracer()
    
    tracer.start_trace("分析用户请求")
    tracer.start_trace("调用 LLM")
    time.sleep(0.1)
    tracer.end_trace("success", {"tokens": 150, "model": "qwen3.7-max"})
    
    tracer.start_trace("执行工具调用")
    tracer.start_trace("数据库查询")
    time.sleep(0.05)
    tracer.end_trace("success", {"rows": 10})
    tracer.end_trace("success")
    
    tracer.end_trace("success")
    
    print(f"  会话 ID: {tracer.session_id}")
    print(f"  追踪跨度数: {len(tracer.traces)}")
    
    export_data = tracer.export_traces()
    print(f"  导出数据: {export_data}")


def demo_metrics():
    """演示指标收集器"""
    print("\n" + "=" * 60)
    print("  指标收集器 (Metrics Collector)")
    print("=" * 60)
    
    print("""
    指标收集器跟踪以下关键指标：
    • 请求数：总请求、成功、失败
    • 延迟：平均响应时间
    • Token：输入和输出 token 消耗
    • 成本：累计 API 调用成本
    • 成功率：请求成功比例
    """)
    
    collector = MetricsCollector()
    
    for i in range(10):
        success = i < 8
        collector.record_request(
            latency=0.5 + i * 0.1,
            input_tokens=100 + i * 10,
            output_tokens=50 + i * 5,
            cost=0.001 + i * 0.0001,
            success=success
        )
    
    summary = collector.get_summary()
    print(f"  总请求数: {summary['total_requests']}")
    print(f"  成功率: {summary['success_rate']:.1%}")
    print(f"  平均延迟: {summary['avg_latency']:.2f}s")
    print(f"  总成本: ${summary['total_cost']:.4f}")


def demo_evaluator():
    """演示评估器"""
    print("\n" + "=" * 60)
    print("  评估器 (Evaluator)")
    print("=" * 60)
    
    print("""
    评估器支持以下评估维度：
    • accuracy（准确性）：回答是否正确
    • relevance（相关性）：回答是否与问题相关
    • completeness（完整性）：回答是否全面
    • safety（安全性）：回答是否安全无害
    """)
    
    evaluator = AgentEvaluator()
    
    test_cases = [
        ("什么是 Python?", "Python 是一种高级编程语言..."),
        ("解释 Transformer", "Transformer 是一种基于自注意力机制的模型..."),
    ]
    
    for query, response in test_cases:
        print(f"\n  问题: {query}")
        scores = evaluator.evaluate_response(query, response)
        for criterion, score in scores.items():
            bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
            print(f"    {criterion}: [{bar}] {score:.2f}")


if __name__ == "__main__":
    demo_tracer()
    demo_metrics()
    demo_evaluator()
