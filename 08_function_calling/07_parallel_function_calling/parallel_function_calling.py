"""
parallel_function_calling.py — Parallel Function Calling 并行工具调用
"""
import os
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, List, Dict, Callable, Any
from dataclasses import dataclass, field


# ============================================================
# 模块：数据结构
# ============================================================

@dataclass
class ParallelToolCall:
    """并行工具调用"""
    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[str] = None
    success: bool = False
    error: str = ""
    execution_time: float = 0.0


@dataclass
class ParallelResult:
    """并行调用结果"""
    calls: List[ParallelToolCall]
    total_time: float = 0.0
    success_count: int = 0
    failure_count: int = 0


# ============================================================
# 模块：简易工具注册表
# ============================================================

class SimpleToolRegistry:
    """简易工具注册表"""

    def __init__(self):
        self.tools: Dict[str, Callable] = {}

    def register(self, name: str, func: Callable):
        self.tools[name] = func

    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        if tool_name not in self.tools:
            return f"错误: 未知工具 '{tool_name}'"
        return self.tools[tool_name](**arguments)


# ============================================================
# 模块：模拟工具
# ============================================================

def get_weather(city: str) -> str:
    """模拟天气查询（慢）"""
    time.sleep(0.5)
    return json.dumps({"city": city, "weather": "晴", "temp": 25})


def get_news(category: str) -> str:
    """模拟新闻查询（慢）"""
    time.sleep(0.3)
    return json.dumps({"category": category, "count": 10})


def get_stock(symbol: str) -> str:
    """模拟股票查询（慢）"""
    time.sleep(0.4)
    return json.dumps({"symbol": symbol, "price": 150.5})


def get_exchange(from_currency: str, to_currency: str) -> str:
    """模拟汇率查询"""
    return json.dumps({"from": from_currency, "to": to_currency, "rate": 7.2})


# ============================================================
# 模块：并行调用执行器
# ============================================================

class ParallelToolExecutor:
    """
    并行工具调用执行器。

    支持两种模式：
    - 真并行：使用线程池同时执行多个工具调用
    - 模拟并行：依次执行但记录总时间（用于演示）
    """

    def __init__(self, registry: SimpleToolRegistry, max_workers: int = 5):
        self.registry = registry
        self.max_workers = max_workers

    def execute_parallel(self, calls: List[Dict[str, Any]],
                         use_threads: bool = True) -> ParallelResult:
        """并行执行多个工具调用"""
        start_time = time.time()
        results = []

        if use_threads:
            # 真并行
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {}
                for call_spec in calls:
                    future = executor.submit(
                        self._execute_single,
                        call_spec["tool_name"],
                        call_spec.get("arguments", {}),
                    )
                    futures[future] = call_spec

                for future in as_completed(futures):
                    call_spec = futures[future]
                    tool_result = future.result()
                    results.append(tool_result)
        else:
            # 顺序执行（用于对比）
            for call_spec in calls:
                result = self._execute_single(
                    call_spec["tool_name"],
                    call_spec.get("arguments", {}),
                )
                results.append(result)

        total_time = time.time() - start_time
        success_count = sum(1 for r in results if r.success)
        failure_count = len(results) - success_count

        return ParallelResult(
            calls=results,
            total_time=total_time,
            success_count=success_count,
            failure_count=failure_count,
        )

    def _execute_single(self, tool_name: str, arguments: Dict) -> ParallelToolCall:
        """执行单个工具调用（带计时）"""
        start = time.time()
        try:
            result = self.registry.execute(tool_name, arguments)
            elapsed = time.time() - start
            return ParallelToolCall(
                tool_name=tool_name,
                arguments=arguments,
                result=result,
                success=True,
                execution_time=elapsed,
            )
        except Exception as e:
            elapsed = time.time() - start
            return ParallelToolCall(
                tool_name=tool_name,
                arguments=arguments,
                error=str(e),
                success=False,
                execution_time=elapsed,
            )


# ============================================================
# 模块：框架并行支持对比
# ============================================================

class FrameworkParallelSupport:
    """各框架并行工具调用支持情况"""

    @staticmethod
    def get_support_info() -> List[Dict[str, Any]]:
        return [
            {
                "framework": "OpenAI",
                "parallel_support": True,
                "max_parallel": 128,
                "api_param": "tool_choice: 'auto'",
                "notes": "自动并行调用多个工具",
            },
            {
                "framework": "Anthropic",
                "parallel_support": False,
                "max_parallel": 1,
                "api_param": "不支持",
                "notes": "早期版本不支持并行",
            },
            {
                "framework": "Qwen",
                "parallel_support": True,
                "max_parallel": 10,
                "api_param": "tool_choice: 'auto'",
                "notes": "兼容 OpenAI 格式",
            },
            {
                "framework": "Gemini",
                "parallel_support": True,
                "max_parallel": 64,
                "api_param": "function_declarations",
                "notes": "支持并行 function calls",
            },
        ]


# ============================================================
# 模块：入口
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  Parallel Function Calling 并行工具调用演示")
    print("=" * 60)

    # 1. 注册工具
    registry = SimpleToolRegistry()
    registry.register("get_weather", get_weather)
    registry.register("get_news", get_news)
    registry.register("get_stock", get_stock)
    registry.register("get_exchange", get_exchange)

    executor = ParallelToolExecutor(registry)

    # 2. 定义并行调用
    calls = [
        {"tool_name": "get_weather", "arguments": {"city": "北京"}},
        {"tool_name": "get_news", "arguments": {"category": "科技"}},
        {"tool_name": "get_stock", "arguments": {"symbol": "AAPL"}},
        {"tool_name": "get_exchange", "arguments": {"from_currency": "USD", "to_currency": "CNY"}},
    ]

    # 3. 并行执行
    print("\n🚀 并行执行（线程池）:")
    parallel_result = executor.execute_parallel(calls, use_threads=True)
    print(f"  总耗时: {parallel_result.total_time:.2f}s")
    print(f"  成功: {parallel_result.success_count}, 失败: {parallel_result.failure_count}")
    for call in parallel_result.calls:
        status = "✅" if call.success else "❌"
        print(f"  {status} {call.tool_name}({call.arguments}) → {(call.result or '')[:50]}... ({call.execution_time:.3f}s)")

    # 4. 顺序执行（对比）
    print("\n🐌 顺序执行（对比）:")
    sequential_result = executor.execute_parallel(calls, use_threads=False)
    print(f"  总耗时: {sequential_result.total_time:.2f}s")
    print(f"  成功: {sequential_result.success_count}, 失败: {sequential_result.failure_count}")
    for call in sequential_result.calls:
        status = "✅" if call.success else "❌"
        print(f"  {status} {call.tool_name}({call.arguments}) → {(call.result or '')[:50]}... ({call.execution_time:.3f}s)")

    # 5. 加速比
    speedup = sequential_result.total_time / parallel_result.total_time if parallel_result.total_time > 0 else 0
    print(f"\n⚡ 加速比: {speedup:.1f}x")

    # 6. 框架支持对比
    print("\n" + "=" * 60)
    print("  各框架并行工具调用支持")
    print("=" * 60)
    info = FrameworkParallelSupport.get_support_info()
    print(f"{'框架':<12s} {'并行支持':<10s} {'最大并行数':<12s} {'备注':<25s}")
    print("-" * 59)
    for item in info:
        print(f"{item['framework']:<12s} {'✅' if item['parallel_support'] else '❌':<10s} "
              f"{item['max_parallel']:<12s} {item['notes']:<25s}")
