"""
agent_observability.py — Agent 可观测性（LangSmith、LangFuse、Phoenix）
演示如何构建 Agent 的追踪、监控和评估系统。
"""
import os
import re
import json
import time
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


# ============================================================
# 模块：追踪器 (Tracer)
# ============================================================

@dataclass
class TraceSpan:
    """追踪跨度"""
    span_id: str
    name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    status: str = "pending"
    metadata: Dict[str, Any] = field(default_factory=dict)
    children: List['TraceSpan'] = field(default_factory=list)
    parent_id: Optional[str] = None


class AgentTracer:
    """Agent 追踪器"""
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.span_stack: List[TraceSpan] = []
        self.traces: List[TraceSpan] = []

    def start_trace(self, name: str) -> TraceSpan:
        """开始新的追踪"""
        parent_id = self.span_stack[-1].span_id if self.span_stack else None
        span = TraceSpan(
            span_id=str(uuid.uuid4()),
            name=name,
            start_time=time.time(),
            parent_id=parent_id
        )
        if self.span_stack:
            self.span_stack[-1].children.append(span)
        self.span_stack.append(span)
        return span

    def end_trace(self, status: str = "success", metadata: Optional[Dict[str, Any]] = None):
        """结束当前追踪"""
        if self.span_stack:
            span = self.span_stack.pop()
            span.end_time = time.time()
            span.duration = span.end_time - span.start_time
            span.status = status
            if metadata:
                span.metadata.update(metadata)
            if not self.span_stack:  # Root span
                self.traces.append(span)

    def export_traces(self) -> Dict[str, Any]:
        """导出追踪数据"""
        def serialize_span(span: TraceSpan) -> Dict[str, Any]:
            return {
                "span_id": span.span_id,
                "name": span.name,
                "start_time": datetime.fromtimestamp(span.start_time).isoformat(),
                "duration_ms": round(span.duration * 1000, 2) if span.duration else None,
                "status": span.status,
                "metadata": span.metadata,
                "children": [serialize_span(c) for c in span.children]
            }
        
        return {
            "session_id": self.session_id,
            "root_spans": [serialize_span(s) for s in self.traces],
            "total_spans": len(self.traces)
        }


# ============================================================
# 模块：指标收集器 (Metrics Collector)
# ============================================================

class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_latency": 0.0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost": 0.0
        }

    def record_request(self, latency: float, input_tokens: int,
                       output_tokens: int, cost: float, success: bool):
        """记录单次请求指标"""
        self.metrics["total_requests"] += 1
        if success:
            self.metrics["successful_requests"] += 1
        else:
            self.metrics["failed_requests"] += 1
        
        self.metrics["total_latency"] += latency
        self.metrics["total_input_tokens"] += input_tokens
        self.metrics["total_output_tokens"] += output_tokens
        self.metrics["total_cost"] += cost

    def get_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        total = self.metrics["total_requests"]
        if total == 0:
            return self.metrics
        
        return {
            **self.metrics,
            "avg_latency": self.metrics["total_latency"] / total,
            "success_rate": self.metrics["successful_requests"] / total,
            "avg_cost_per_request": self.metrics["total_cost"] / total
        }


# ============================================================
# 模块：评估器 (Evaluator)
# ============================================================

class AgentEvaluator:
    """Agent 评估器"""
    
    EVALUATION_CRITERIA = {
        "accuracy": "回答是否准确无误？",
        "relevance": "回答是否与问题高度相关？",
        "completeness": "回答是否完整覆盖了所有要点？",
        "safety": "回答是否安全，无有害内容？"
    }

    def evaluate_response(self, query: str, response: str,
                          criteria: Optional[List[str]] = None) -> Dict[str, float]:
        """评估响应质量（模拟评分）"""
        if criteria is None:
            criteria = list(self.EVALUATION_CRITERIA.keys())
        
        scores = {}
        for criterion in criteria:
            base_score = 0.85
            variation = (hash(query + criterion) % 20 - 10) / 100.0
            scores[criterion] = min(1.0, max(0.0, base_score + variation))
        
        return scores


# ============================================================
# 模块：入口
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  Agent 可观测性演示")
    print("=" * 60)

    # 1. 追踪器演示
    print("\n 1. 追踪器 (Tracer)")
    tracer = AgentTracer()
    
    tracer.start_trace("分析用户请求")
    tracer.start_trace("调用 LLM")
    time.sleep(0.1)
    tracer.end_trace("success", {"tokens": 150})
    
    tracer.start_trace("执行工具调用")
    tracer.start_trace("数据库查询")
    time.sleep(0.05)
    tracer.end_trace("success", {"rows": 10})
    tracer.end_trace("success")
    
    tracer.end_trace("success")
    
    print(f"  会话 ID: {tracer.session_id}")
    print(f"  追踪跨度数: {len(tracer.traces)}")
    
    export_data = tracer.export_traces()
    print(f"  导出数据: {json.dumps(export_data, ensure_ascii=False, indent=2)[:200]}...")

    # 2. 指标收集器演示
    print("\n 2. 指标收集器 (Metrics Collector)")
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

    # 3. 评估器演示
    print("\n⭐ 3. 评估器 (Evaluator)")
    evaluator = AgentEvaluator()
    
    query = "解释什么是 Transformer 模型？"
    response = "Transformer 是一种基于自注意力机制的深度学习模型..."
    
    scores = evaluator.evaluate_response(query, response)
    print(f"  评估结果:")
    for criterion, score in scores.items():
        print(f"    {criterion}: {score:.2f}")

    print("\n" + "=" * 60)
    print("  演示完成")
    print("=" * 60)
