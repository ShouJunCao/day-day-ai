"""
example_usage.py — 数据分析 Agent 演示
展示如何构建和运行完整的数据分析 Agent。
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_analysis_agent import (
    DataAnalysisAgent,
    DataAnalysisTools,
    DataAnalysisTracer,
    DataAnalysisExceptionHandler,
)


def demo_tools():
    """演示数据分析工具"""
    print("=" * 60)
    print("  数据分析工具集")
    print("=" * 60)
    
    print("\n  1. 查询数据:")
    data = DataAnalysisTools.query_data("sales")
    import json
    records = json.loads(data)
    print(f"    返回记录数: {len(records)}")
    
    print("\n  2. 计算指标:")
    sample_data = DataAnalysisTools.query_data("sales", {"地区": "华南"})
    metrics = DataAnalysisTools.calculate_metrics(sample_data, "销售额")
    print(f"    华南地区销售额指标: {metrics}")
    
    print("\n  3. 分组聚合:")
    all_data = DataAnalysisTools.query_data("sales")
    grouped = DataAnalysisTools.group_by(all_data, "产品", "利润", "sum")
    print(f"    按产品分组利润: {grouped}")
    
    print("\n  4. 生成报告:")
    report = DataAnalysisTools.generate_report(all_data, "销售数据总览")
    print(f"    报告预览: {report[:100]}...")


def demo_tracer():
    """演示追踪器"""
    print("\n" + "=" * 60)
    print("  追踪器")
    print("=" * 60)
    
    tracer = DataAnalysisTracer()
    
    tracer.start_trace("数据分析任务")
    tracer.start_trace("查询数据")
    time.sleep(0.05)
    tracer.end_trace("success", {"records": 12})
    
    tracer.start_trace("计算指标")
    time.sleep(0.03)
    tracer.end_trace("success")
    
    tracer.start_trace("生成报告")
    time.sleep(0.02)
    tracer.end_trace("success")
    
    tracer.end_trace("success")
    
    print(f"  会话 ID: {tracer.session_id}")
    print(f"  追踪摘要:")
    print(tracer.export_summary())


def demo_exception_handler():
    """演示异常处理"""
    print("\n" + "=" * 60)
    print("  异常处理器")
    print("=" * 60)
    
    handler = DataAnalysisExceptionHandler(max_retries=2, retry_delay=0.1)
    
    call_count = [0]
    def unstable_analysis():
        call_count[0] += 1
        if call_count[0] < 3:
            raise ValueError(f"临时错误 (尝试 {call_count[0]})")
        return "分析完成"
    
    print("  场景: 不稳定的分析函数")
    call_count[0] = 0
    result = handler.handle(unstable_analysis)
    print(f"    最终结果: {result}")


def demo_full_agent():
    """演示完整 Agent"""
    print("\n" + "=" * 60)
    print("  完整数据分析 Agent")
    print("=" * 60)
    
    agent = DataAnalysisAgent()
    
    print("\n  任务: 查询销售数据并生成分析报告")
    print("  说明: Agent 将自动规划步骤、调用工具、处理异常")
    
    print("\n  可用工具:")
    for name in DataAnalysisAgent.TOOLS:
        print(f"    • {name}")
    
    print("\n  Agent 架构:")
    print("    ├── ReAct 循环 (规划-执行-观察)")
    print("    ├── 工具层 (query/calculate/group/report)")
    print("    ├── 异常处理 (自动重试)")
    print("    └── 可观测性 (追踪 + 指标)")


if __name__ == "__main__":
    demo_tools()
    demo_tracer()
    demo_exception_handler()
    demo_full_agent()
