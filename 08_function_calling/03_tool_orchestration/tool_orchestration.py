"""
tool_orchestration.py — 单工具调用与多工具编排实现
"""
import os
import re
import json
from typing import Optional, List, Dict, Callable, Any
from dataclasses import dataclass, field
from enum import Enum


# ============================================================
# 模块：数据结构
# ============================================================

class OrchestrationMode(Enum):
    """编排模式"""
    SEQUENTIAL = "sequential"       # 顺序执行
    PARALLEL = "parallel"           # 并行执行
    CONDITIONAL = "conditional"     # 条件分支
    CHAINED = "chained"             # 链式传递


@dataclass
class ToolCall:
    """工具调用"""
    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[str] = None
    success: bool = True
    error: str = ""


@dataclass
class OrchestrationPlan:
    """编排计划"""
    mode: OrchestrationMode
    steps: List[Dict[str, Any]]
    description: str = ""


# ============================================================
# 模块：工具注册表
# ============================================================

class SimpleToolRegistry:
    """简易工具注册表"""

    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.schemas: Dict[str, dict] = {}

    def register(self, name: str, func: Callable, schema: Optional[dict] = None):
        self.tools[name] = func
        self.schemas[name] = schema or {}

    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        if tool_name not in self.tools:
            return f"错误: 未知工具 '{tool_name}'"
        try:
            result = self.tools[tool_name](**arguments)
            return json.dumps(result, ensure_ascii=False) if isinstance(result, (dict, list)) else str(result)
        except Exception as e:
            return f"错误: {str(e)}"


# ============================================================
# 模块：单工具调用
# ============================================================

class SingleToolCaller:
    """
    单工具调用：执行单个工具调用并返回结果。
    """

    def __init__(self, registry: SimpleToolRegistry):
        self.registry = registry

    def call(self, tool_name: str, arguments: Dict[str, Any]) -> ToolCall:
        """执行单个工具调用"""
        result = self.registry.execute(tool_name, arguments)
        success = not result.startswith("错误:")
        return ToolCall(
            tool_name=tool_name,
            arguments=arguments,
            result=result,
            success=success,
            error="" if success else result,
        )


# ============================================================
# 模块：多工具编排
# ============================================================

class ToolOrchestrator:
    """
    多工具编排器：支持多种编排模式。

    编排模式：
    - SEQUENTIAL: 顺序执行，每个步骤依赖前一步骤
    - PARALLEL: 并行执行，所有步骤同时执行
    - CONDITIONAL: 条件分支，根据前一步结果选择下一步
    - CHAINED: 链式传递，前一步输出作为下一步输入
    """

    def __init__(self, registry: SimpleToolRegistry):
        self.registry = registry
        self.caller = SingleToolCaller(registry)

    def execute_plan(self, plan: OrchestrationPlan, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行编排计划"""
        context = context or {}
        results = {}

        if plan.mode == OrchestrationMode.SEQUENTIAL:
            results = self._run_sequential(plan.steps, context)
        elif plan.mode == OrchestrationMode.PARALLEL:
            results = self._run_parallel(plan.steps, context)
        elif plan.mode == OrchestrationMode.CHAINED:
            results = self._run_chained(plan.steps, context)
        elif plan.mode == OrchestrationMode.CONDITIONAL:
            results = self._run_conditional(plan.steps, context)

        return {
            "mode": plan.mode.value,
            "description": plan.description,
            "results": results,
        }

    def _run_sequential(self, steps: List[Dict], context: Dict) -> Dict:
        """顺序执行"""
        results = {}
        for i, step in enumerate(steps):
            tool_name = step["tool"]
            args = self._resolve_args(step.get("args", {}), context, results)
            call = self.caller.call(tool_name, args)
            results[f"step_{i+1}"] = {
                "tool": tool_name,
                "args": args,
                "result": call.result,
                "success": call.success,
            }
            if not call.success:
                results[f"step_{i+1}"]["error"] = call.error
                break
        return results

    def _run_parallel(self, steps: List[Dict], context: Dict) -> Dict:
        """并行执行（简化版，实际应使用线程池）"""
        results = {}
        for i, step in enumerate(steps):
            tool_name = step["tool"]
            args = self._resolve_args(step.get("args", {}), context, results)
            call = self.caller.call(tool_name, args)
            results[f"step_{i+1}"] = {
                "tool": tool_name,
                "args": args,
                "result": call.result,
                "success": call.success,
            }
        return results

    def _run_chained(self, steps: List[Dict], context: Dict) -> Dict:
        """链式传递：前一步输出作为下一步输入"""
        results = {}
        chain_input = {}

        for i, step in enumerate(steps):
            tool_name = step["tool"]
            args = self._resolve_args(step.get("args", {}), context, results)
            # 不自动合并所有字段，只使用步骤中显式声明的参数

            call = self.caller.call(tool_name, args)
            results[f"step_{i+1}"] = {
                "tool": tool_name,
                "args": args,
                "result": call.result,
                "success": call.success,
            }

            if call.success:
                try:
                    parsed = json.loads(call.result) if isinstance(call.result, str) else call.result
                    if isinstance(parsed, dict):
                        chain_input = parsed
                    else:
                        chain_input = {"output": call.result}
                except (json.JSONDecodeError, TypeError):
                    chain_input = {"output": str(call.result)}

            if not call.success:
                results[f"step_{i+1}"]["error"] = call.error
                break

        return results

    def _run_conditional(self, steps: List[Dict], context: Dict) -> Dict:
        """条件分支：根据条件选择执行路径"""
        results = {}
        for i, step in enumerate(steps):
            # 检查条件
            condition = step.get("condition")
            if condition:
                # 简化条件评估：检查上下文中是否存在指定键
                cond_key = condition.get("key", "")
                cond_value = condition.get("value")
                actual = context.get(cond_key)
                if actual != cond_value:
                    results[f"step_{i+1}"] = {"skipped": True, "reason": f"条件不满足: {condition}"}
                    continue

            tool_name = step["tool"]
            args = self._resolve_args(step.get("args", {}), context, results)
            call = self.caller.call(tool_name, args)
            results[f"step_{i+1}"] = {
                "tool": tool_name,
                "args": args,
                "result": call.result,
                "success": call.success,
            }
            if not call.success:
                results[f"step_{i+1}"]["error"] = call.error
                break

        return results

    def _resolve_args(self, args: Dict, context: Dict, results: Dict) -> Dict:
        """解析参数中的变量引用"""
        resolved = {}
        for key, value in args.items():
            if isinstance(value, str):
                # 替换 ${step_N} 引用
                for rkey, rval in results.items():
                    placeholder = f"${{{rkey}}}"
                    if placeholder in value and isinstance(rval, dict):
                        value = value.replace(placeholder, str(rval.get("result", "")))
                # 替换 ${context.key} 引用
                for ckey, cval in context.items():
                    placeholder = f"${{context.{ckey}}}"
                    if placeholder in value:
                        value = value.replace(placeholder, str(cval))
            resolved[key] = value
        return resolved


# ============================================================
# 模块：示例工具
# ============================================================

def get_weather(city: str) -> dict:
    return {"city": city, "weather": "晴", "temp": 25, "unit": "°C"}


def get_forecast(city: str, days: int = 3) -> dict:
    return {"city": city, "days": days, "forecast": ["晴", "多云", "小雨"][:days]}


def format_weather(data: str) -> dict:
    try:
        info = json.loads(data) if isinstance(data, str) else data
        return {"formatted": f"{info.get('city', '?')} 天气: {info.get('weather', '?')}，{info.get('temp', '?')}°C"}
    except Exception:
        return {"formatted": f"原始数据: {data}"}


def send_notification(message: str, channel: str = "email") -> dict:
    return {"sent": True, "channel": channel, "message": message}


# ============================================================
# 模块：入口
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  单工具调用与多工具编排演示")
    print("=" * 60)

    # 注册工具
    registry = SimpleToolRegistry()
    registry.register("get_weather", get_weather)
    registry.register("get_forecast", get_forecast)
    registry.register("format_weather", format_weather)
    registry.register("send_notification", send_notification)

    orchestrator = ToolOrchestrator(registry)

    # 1. 单工具调用
    print("\n📌 单工具调用:")
    caller = SingleToolCaller(registry)
    call = caller.call("get_weather", {"city": "北京"})
    print(f"  get_weather(北京) = {call.result}")
    print(f"  成功: {call.success}")

    # 2. 顺序编排
    print("\n📌 顺序编排（获取天气 → 格式化 → 发送通知）:")
    seq_plan = OrchestrationPlan(
        mode=OrchestrationMode.SEQUENTIAL,
        description="获取天气并发送通知",
        steps=[
            {"tool": "get_weather", "args": {"city": "上海"}},
            {"tool": "format_weather", "args": {"data": "${step_1}"}},
            {"tool": "send_notification", "args": {
                "message": "${step_2}",
                "channel": "email",
            }},
        ]
    )
    result = orchestrator.execute_plan(seq_plan)
    for k, v in result["results"].items():
        print(f"  {k}: {v['tool']} → {v['result'][:60]}...")

    # 3. 链式编排
    print("\n📌 链式编排（天气数据 → 格式化 → 通知）:")
    chain_plan = OrchestrationPlan(
        mode=OrchestrationMode.CHAINED,
        description="链式处理天气数据",
        steps=[
            {"tool": "get_weather", "args": {"city": "广州"}},
            {"tool": "format_weather", "args": {"data": "${step_1}"}},
        ]
    )
    result = orchestrator.execute_plan(chain_plan)
    for k, v in result["results"].items():
        print(f"  {k}: {v['tool']} → {v['result']}")

    # 4. 并行编排
    print("\n📌 并行编排（同时查询多个城市天气）:")
    parallel_plan = OrchestrationPlan(
        mode=OrchestrationMode.PARALLEL,
        description="并行查询多个城市",
        steps=[
            {"tool": "get_weather", "args": {"city": "北京"}},
            {"tool": "get_weather", "args": {"city": "上海"}},
            {"tool": "get_weather", "args": {"city": "广州"}},
        ]
    )
    result = orchestrator.execute_plan(parallel_plan)
    for k, v in result["results"].items():
        print(f"  {k}: {v['args']['city']} → {v['result'][:50]}...")

    print("\n" + "=" * 60)
    print("  编排模式对比总结")
    print("=" * 60)
    print(f"{'模式':<15s} {'特点':<30s} {'适用场景':<20s}")
    print("-" * 65)
    print(f"{'顺序':<15s} {'步骤依次执行':<30s} {'有依赖的多步任务':<20s}")
    print(f"{'并行':<15s} {'步骤同时执行':<30s} {'独立的多路查询':<20s}")
    print(f"{'链式':<15s} {'输出传给下一步':<30s} {'数据流水线处理':<20s}")
    print(f"{'条件':<15s} {'按条件选择执行':<30s} {'分支决策场景':<20s}")
