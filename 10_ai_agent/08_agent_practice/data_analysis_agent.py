"""
data_analysis_agent.py — 实战：构建完整的数据分析 Agent
综合运用 ReAct 循环、任务规划、异常处理、可观测性等核心技术，
构建一个能执行数据分析全流程的智能 Agent。
"""
import os
import re
import json
import time
import uuid
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from openai import OpenAI

# 阿里云 DashScope 配置
DASHSCOPE_API_KEY = os.getenv("API_KEY", "sk-492...81ff")
DASHSCOPE_BASE_URL = os.getenv("BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
DASHSCOPE_MODEL = os.getenv("MODEL_NAME", "qwen3.7-max")

client = OpenAI(
    api_key=DASHSCOPE_API_KEY,
    base_url=DASHSCOPE_BASE_URL,
)

# ============================================================
# 模块：模拟数据源
# ============================================================

MOCK_SALES_DATA = """
日期,产品,地区,销售额,成本,利润
2026-01-05,A,华北,15000,9000,6000
2026-01-12,B,华东,22000,13200,8800
2026-01-19,A,华南,18000,10800,7200
2026-01-26,C,华北,9000,6300,2700
2026-02-02,B,华南,25000,15000,10000
2026-02-09,A,华东,20000,12000,8000
2026-02-16,C,华南,11000,7700,3300
2026-02-23,B,华北,19000,11400,7600
2026-03-02,A,华南,17000,10200,6800
2026-03-09,C,华东,13000,9100,3900
2026-03-16,B,华南,28000,16800,11200
2026-03-23,A,华北,16000,9600,6400
"""

# ============================================================
# 模块：数据分析工具
# ============================================================

class DataAnalysisTools:
    """数据分析工具集"""
    
    @staticmethod
    def query_data(dataset: str, filters: Optional[Dict[str, Any]] = None) -> str:
        """查询数据集"""
        if dataset == "sales":
            import csv
            import io
            reader = csv.DictReader(io.StringIO(MOCK_SALES_DATA.strip()))
            rows = list(reader)
            
            if filters:
                filtered = []
                for row in rows:
                    match = True
                    for key, value in filters.items():
                        if row.get(key) != str(value):
                            match = False
                            break
                    if match:
                        filtered.append(row)
                rows = filtered
            
            return json.dumps(rows, ensure_ascii=False)
        return "未知数据集"
    
    @staticmethod
    def calculate_metrics(data_json: str, metric: str) -> str:
        """计算指标"""
        try:
            data = json.loads(data_json)
            values = [float(row.get(metric, 0)) for row in data]
            if not values:
                return "无数据"
            
            results = {
                "count": len(values),
                "sum": sum(values),
                "avg": sum(values) / len(values),
                "max": max(values),
                "min": min(values)
            }
            return json.dumps(results, ensure_ascii=False)
        except Exception as e:
            return f"计算错误: {e}"
    
    @staticmethod
    def group_by(data_json: str, group_key: str, agg_key: str, agg_func: str) -> str:
        """分组聚合"""
        try:
            data = json.loads(data_json)
            groups = {}
            for row in data:
                key = row.get(group_key, "Unknown")
                if key not in groups:
                    groups[key] = []
                groups[key].append(float(row.get(agg_key, 0)))
            
            result = {}
            for key, values in groups.items():
                if agg_func == "sum":
                    result[key] = sum(values)
                elif agg_func == "avg":
                    result[key] = sum(values) / len(values)
                elif agg_func == "count":
                    result[key] = len(values)
                elif agg_func == "max":
                    result[key] = max(values)
                elif agg_func == "min":
                    result[key] = min(values)
            
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return f"分组错误: {e}"
    
    @staticmethod
    def generate_report(data_json: str, title: str) -> str:
        """生成分析报告"""
        try:
            data = json.loads(data_json)
            if not data:
                return f"报告: {title}\n无数据可分析"
            
            numeric_cols = ["销售额", "成本", "利润"]
            stats = {}
            for col in numeric_cols:
                values = [float(row.get(col, 0)) for row in data if row.get(col)]
                if values:
                    stats[col] = {
                        "总计": sum(values),
                        "平均": sum(values) / len(values),
                        "最高": max(values),
                        "最低": min(values)
                    }
            
            report = f"【{title}】\n"
            report += f"数据记录数: {len(data)}\n\n"
            for col, s in stats.items():
                report += f"{col}:\n"
                for k, v in s.items():
                    report += f"  {k}: ¥{v:,.0f}\n"
            
            return report
        except Exception as e:
            return f"报告生成错误: {e}"

# ============================================================
# 模块：可观测性追踪
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

class DataAnalysisTracer:
    """数据分析 Agent 追踪器"""
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.span_stack: List[TraceSpan] = []
        self.traces: List[TraceSpan] = []

    def start_trace(self, name: str) -> TraceSpan:
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
        if self.span_stack:
            span = self.span_stack.pop()
            span.end_time = time.time()
            span.duration = span.end_time - span.start_time
            span.status = status
            if metadata:
                span.metadata.update(metadata)
            if not self.span_stack:
                self.traces.append(span)

    def export_summary(self) -> str:
        """导出追踪摘要"""
        lines = [f"Session: {self.session_id}", f"Total Spans: {len(self.traces)}"]
        for trace in self.traces:
            duration = f"{trace.duration:.2f}s" if trace.duration else "N/A"
            lines.append(f"  {trace.name}: {trace.status} ({duration})")
            for child in trace.children:
                c_duration = f"{child.duration:.2f}s" if child.duration else "N/A"
                lines.append(f"    ─ {child.name}: {child.status} ({c_duration})")
        return "\n".join(lines)

# ============================================================
# 模块：异常处理
# ============================================================

class DataAnalysisExceptionHandler:
    """数据分析异常处理器"""
    
    def __init__(self, max_retries: int = 2, retry_delay: float = 0.5):
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def handle(self, func: Callable, *args, **kwargs) -> Any:
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** attempt)
                    print(f"    ⚠️ 重试 {attempt + 1}/{self.max_retries} (等待 {delay:.1f}s)")
                    time.sleep(delay)
        return {"error": str(last_error)}

# ============================================================
# 模块：数据分析 Agent
# ============================================================

class DataAnalysisAgent:
    """
    数据分析 Agent
    
    综合运用 ReAct 循环、任务规划、工具调用、异常处理和可观测性，
    构建完整的数据分析流水线。
    """
    
    TOOLS = {
        "query_data": DataAnalysisTools.query_data,
        "calculate_metrics": DataAnalysisTools.calculate_metrics,
        "group_by": DataAnalysisTools.group_by,
        "generate_report": DataAnalysisTools.generate_report
    }
    
    TOOL_DESCRIPTIONS = """
可用工具：
- query_data: 查询数据集 (参数: dataset, filters)
- calculate_metrics: 计算统计指标 (参数: data_json, metric)
- group_by: 分组聚合 (参数: data_json, group_key, agg_key, agg_func)
- generate_report: 生成分析报告 (参数: data_json, title)
"""

    def __init__(self):
        self.tracer = DataAnalysisTracer()
        self.exception_handler = DataAnalysisExceptionHandler()
        self.metrics: Dict[str, Any] = {"total_steps": 0, "success_steps": 0, "total_time": 0.0}

    def _call_llm(self, prompt: str) -> str:
        try:
            response = client.chat.completions.create(
                model=DASHSCOPE_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            content = response.choices[0].message.content
            if content is None:
                return ""
            return content.strip()
        except Exception as e:
            return f"LLM Error: {e}"

    def _parse_action(self, response: str) -> Dict[str, Any]:
        action_match = re.search(r"Action:\s*(\w+)", response)
        input_match = re.search(r"Action Input:\s*(.*)", response)
        final_match = re.search(r"Final Answer:\s*(.*)", response, re.DOTALL)
        
        result: Dict[str, Any] = {"action": None, "input": {}, "final_answer": None}
        if action_match:
            result["action"] = action_match.group(1).strip()
        if input_match:
            try:
                result["input"] = json.loads(input_match.group(1).strip())
            except json.JSONDecodeError:
                result["input"] = {}
        if final_match:
            result["final_answer"] = final_match.group(1).strip()
        return result

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """执行工具（带异常处理）"""
        func = self.TOOLS.get(tool_name)
        if not func:
            return {"error": f"未知工具: {tool_name}"}
        
        def wrapper():
            return func(**arguments)
        
        return self.exception_handler.handle(wrapper)

    def analyze(self, task: str) -> Dict[str, Any]:
        """执行数据分析任务"""
        start_time = time.time()
        self.tracer.start_trace(task)
        
        prompt = f"""你是一个专业数据分析 Agent。请完成以下分析任务：

任务：{task}

{self.TOOL_DESCRIPTIONS}

回答格式：
Thought: <思考过程>
Action: <工具名>
Action Input: <JSON 参数>
Observation: <自动填充>
...
Final Answer: <最终分析报告>

请开始分析："""

        max_steps = 8
        observations: List[str] = []
        
        for step in range(max_steps):
            self.metrics["total_steps"] += 1
            step_span = self.tracer.start_trace(f"Step {step + 1}")
            step_start = time.time()
            
            response = self._call_llm(prompt + "\n\n" + "\n".join(observations))
            
            action_data = self._parse_action(response)
            
            if action_data.get("final_answer"):
                self.tracer.end_trace("success", {"answer": action_data["final_answer"]})
                self.metrics["success_steps"] += 1
                self.metrics["total_time"] = time.time() - start_time
                return {
                    "success": True,
                    "answer": action_data["final_answer"],
                    "steps": step + 1,
                    "metrics": self.metrics,
                    "trace": self.tracer.export_summary()
                }
            
            if action_data.get("action"):
                tool_name = action_data["action"]
                arguments = action_data.get("input", {})
                
                tool_span = self.tracer.start_trace(f"Tool: {tool_name}")
                result = self.execute_tool(tool_name, arguments)
                obs_text = str(result)
                self.tracer.end_trace("success", {"tool": tool_name})
                
                observations.append(f"Observation: {obs_text[:500]}")
                self.metrics["success_steps"] += 1
                
                step_span.duration = time.time() - step_start
                self.tracer.end_trace("success")
            else:
                observations.append("Observation: 请指定 Action")
                self.tracer.end_trace("pending")
        
        self.tracer.end_trace("timeout")
        self.metrics["total_time"] = time.time() - start_time
        return {
            "success": False,
            "error": "达到最大步骤限制",
            "metrics": self.metrics,
            "trace": self.tracer.export_summary()
        }

# ============================================================
# 模块：入口
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  数据分析 Agent 实战演示")
    print("=" * 60)

    agent = DataAnalysisAgent()
    
    tasks = [
        "查询销售数据集，计算销售额的总计和平均值，生成分析报告",
        "查询销售数据，按产品分组计算利润总和，比较各产品表现",
        "查询华南地区销售数据，分析该地区各产品的销售情况"
    ]
    
    for i, task in enumerate(tasks, 1):
        print(f"\n{'='*50}")
        print(f"  任务 {i}: {task}")
        print(f"{'='*50}")
        
        result = agent.analyze(task)
        
        print(f"\n  执行状态: {'成功' if result['success'] else '失败'}")
        print(f"  执行步数: {result.get('steps', 'N/A')}")
        print(f"  总耗时: {result.get('metrics', {}).get('total_time', 0):.2f}s")
        print(f"\n  分析报告:")
        print(f"  {result.get('answer', 'N/A')}")
        
        print(f"\n  可观测性摘要:")
        print(f"  {result.get('trace', 'N/A')}")

    print("\n" + "=" * 60)
    print("  实战演示完成")
    print("=" * 60)
