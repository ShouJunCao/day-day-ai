"""
error_handling.py — 工具调用的错误处理、重试与超时实现
"""
import os
import time
import json
import random
from typing import Optional, List, Dict, Callable, Any
from dataclasses import dataclass, field
from enum import Enum


# ============================================================
# 模块：数据结构
# ============================================================

class ErrorStrategy(Enum):
    """错误处理策略"""
    RETRY = "retry"                    # 重试
    FALLBACK = "fallback"              # 降级
    SKIP = "skip"                      # 跳过
    ABORT = "abort"                    # 中止


@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True


@dataclass
class TimeoutConfig:
    """超时配置"""
    timeout_seconds: float = 10.0


@dataclass
class ToolResult:
    """工具调用结果"""
    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[str] = None
    success: bool = True
    error: str = ""
    retries: int = 0
    used_fallback: bool = False
    timed_out: bool = False


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
# 模块：错误处理器
# ============================================================

class ErrorHandler:
    """
    错误处理器：管理工具调用的错误处理、重试与超时。
    """

    def __init__(self, registry: SimpleToolRegistry):
        self.registry = registry
        self.retry_config = RetryConfig()
        self.timeout_config = TimeoutConfig()
        self.fallbacks: Dict[str, Callable] = {}
        self.error_log: List[Dict[str, Any]] = []

    def set_retry_config(self, max_retries: int = 3, base_delay: float = 1.0,
                         max_delay: float = 30.0, exponential_base: float = 2.0,
                         jitter: bool = True):
        """设置重试配置"""
        self.retry_config = RetryConfig(
            max_retries=max_retries,
            base_delay=base_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
        )

    def register_fallback(self, tool_name: str, fallback_func: Callable):
        """注册降级函数"""
        self.fallbacks[tool_name] = fallback_func

    def call_with_handling(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """
        带错误处理的工具调用。
        流程：调用 → 超时检测 → 失败重试 → 降级处理
        """
        result = ToolResult(tool_name=tool_name, arguments=arguments)

        # 1. 尝试调用（带重试）
        last_error = None
        for attempt in range(self.retry_config.max_retries + 1):
            result.retries = attempt
            try:
                output = self._execute_with_timeout(tool_name, arguments)
                if output.startswith("超时:"):
                    result.timed_out = True
                    last_error = output
                    self._wait_before_retry(attempt)
                    continue

                if output.startswith("错误:"):
                    last_error = output
                    self._wait_before_retry(attempt)
                    continue

                # 成功
                result.result = output
                result.success = True
                return result

            except Exception as e:
                last_error = str(e)
                result.error = last_error
                self._wait_before_retry(attempt)

        # 2. 重试耗尽，尝试降级
        result.success = False
        result.error = f"重试 {self.retry_config.max_retries} 次后失败: {last_error}"
        self._log_error(tool_name, arguments, result.error)

        if tool_name in self.fallbacks:
            try:
                fallback_result = self.fallbacks[tool_name](**arguments)
                result.result = str(fallback_result)
                result.used_fallback = True
                result.success = True
                result.error = f"{result.error}（已使用降级方案）"
            except Exception as e:
                result.error = f"{result.error}，降级也失败: {str(e)}"

        return result

    def _execute_with_timeout(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """带超时检测的工具执行（简化版，实际应使用线程/async）"""
        try:
            return self.registry.execute(tool_name, arguments)
        except Exception as e:
            return f"错误: {str(e)}"

    def _wait_before_retry(self, attempt: int):
        """计算重试等待时间（指数退避 + 抖动）"""
        delay = self.retry_config.base_delay * (
            self.retry_config.exponential_base ** attempt
        )
        delay = min(delay, self.retry_config.max_delay)

        if self.retry_config.jitter:
            delay *= (0.5 + random.random() * 0.5)

        # 演示模式：不实际等待
        if attempt < self.retry_config.max_retries:
            pass  # time.sleep(delay)  # 实际使用时取消注释

    def _log_error(self, tool_name: str, arguments: Dict, error: str):
        """记录错误日志"""
        self.error_log.append({
            "tool": tool_name,
            "arguments": arguments,
            "error": error,
            "timestamp": time.time(),
        })

    def get_error_stats(self) -> Dict[str, Any]:
        """获取错误统计"""
        return {
            "total_errors": len(self.error_log),
            "recent_errors": self.error_log[-5:],
        }


# ============================================================
# 模块：示例工具（含失败场景）
# ============================================================

def reliable_weather(city: str) -> str:
    """可靠的天气查询"""
    return json.dumps({"city": city, "weather": "晴", "temp": 25})


def flaky_api(query: str) -> str:
    """不稳定的 API（模拟随机失败）"""
    if random.random() < 0.7:  # 70% 失败率
        raise ConnectionError("API 连接超时")
    return json.dumps({"query": query, "results": 5})


def slow_api(data: str) -> str:
    """慢速 API（模拟超时）"""
    # 实际使用时：time.sleep(15)
    raise TimeoutError("操作超时")


def fallback_search(query: str) -> str:
    """降级搜索（当主 API 失败时使用）"""
    return f"[降级方案] 关于 '{query}' 的本地缓存结果"


# ============================================================
# 模块：入口
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  工具调用错误处理、重试与超时演示")
    print("=" * 60)

    # 设置随机种子以便复现
    random.seed(42)

    registry = SimpleToolRegistry()
    registry.register("weather", reliable_weather)
    registry.register("search", flaky_api)
    registry.register("slow", slow_api)

    handler = ErrorHandler(registry)
    handler.set_retry_config(max_retries=3, base_delay=0.1, jitter=False)
    handler.register_fallback("search", fallback_search)

    # 1. 成功调用
    print("\n📌 成功调用:")
    result = handler.call_with_handling("weather", {"city": "北京"})
    print(f"  weather(北京) → 成功={result.success}, 结果={result.result}")

    # 2. 不稳定 API（重试后成功）
    print("\n📌 不稳定 API（重试直到成功）:")
    random.seed(100)  # 确保重试后能成功
    result = handler.call_with_handling("search", {"query": "AI"})
    print(f"  search(AI) → 成功={result.success}, 重试={result.retries}, 降级={result.used_fallback}")
    print(f"  结果: {result.result[:60]}...")
    print(f"  错误: {result.error[:60]}...")

    # 3. 超时 + 降级
    print("\n📌 超时 + 降级:")
    try:
        result = handler.call_with_handling("slow", {"data": "test"})
        print(f"  slow(test) → 成功={result.success}")
        print(f"  超时={result.timed_out}, 重试={result.retries}")
        print(f"  降级={result.used_fallback}")
        if result.result:
            print(f"  结果: {result.result}")
    except TimeoutError:
        print(f"  slow(test) → 超时（演示模式直接抛出）")

    # 4. 错误统计
    print("\n📊 错误统计:")
    stats = handler.get_error_stats()
    print(f"  总错误数: {stats['total_errors']}")

    # 5. 策略对比
    print("\n" + "=" * 60)
    print("  错误处理策略对比")
    print("=" * 60)
    print(f"{'策略':<15s} {'行为':<30s} {'适用场景':<20s}")
    print("-" * 65)
    print(f"{'重试 RETRY':<15s} {'指数退避重试':<30s} {'临时网络故障':<20s}")
    print(f"{'降级 FALLBACK':<15s} {'使用备用方案':<30s} {'主服务不可用':<20s}")
    print(f"{'跳过 SKIP':<15s} {'忽略错误继续':<30s} {'非关键步骤':<20s}")
    print(f"{'中止 ABORT':<15s} {'立即停止':<30s} {'致命错误':<20s}")
