"""
framework_comparison.py — 主流 Function Calling 框架对比
"""
import os
import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


# ============================================================
# 模块：数据结构
# ============================================================

class FrameworkName(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    QWEN = "qwen"
    GEMINI = "gemini"


@dataclass
class ToolCapability:
    """工具能力"""
    name: str
    supports_parallel: bool = False
    supports_nesting: bool = False
    max_tools_per_call: int = 1
    json_schema_support: str = "partial"  # full/partial/none


@dataclass
class FrameworkInfo:
    """框架信息"""
    name: FrameworkName
    display_name: str
    tool_format: str
    parallel_support: bool
    max_tools_per_call: int
    streaming: bool
    function_calling_api: str
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)


# ============================================================
# 模块：框架注册表
# ============================================================

class FrameworkRegistry:
    """框架注册表"""

    def __init__(self):
        self.frameworks: Dict[FrameworkName, FrameworkInfo] = {}
        self._register_all()

    def _register_all(self):
        """注册所有框架"""
        self.frameworks[FrameworkName.OPENAI] = FrameworkInfo(
            name=FrameworkName.OPENAI,
            display_name="OpenAI",
            tool_format="function (OpenAI 格式)",
            parallel_support=True,
            max_tools_per_call=128,
            streaming=True,
            function_calling_api="chat.completions (tools 参数)",
            strengths=[
                "工具调用生态最成熟",
                "支持并行工具调用",
                "strict mode 确保 JSON Schema 合规",
                "丰富的第三方工具集成",
            ],
            weaknesses=[
                "闭源，无法本地部署",
                "API 成本较高",
                "嵌套工具调用支持有限",
            ],
        )

        self.frameworks[FrameworkName.ANTHROPIC] = FrameworkInfo(
            name=FrameworkName.ANTHROPIC,
            display_name="Anthropic",
            tool_format="tool_use (Claude 格式)",
            parallel_support=False,
            max_tools_per_call=1,
            streaming=True,
            function_calling_api="messages (tools 参数)",
            strengths=[
                "工具描述更自然",
                "支持 tool_use 格式（结构化）",
                "上下文窗口大（200K）",
                "安全对齐优秀",
            ],
            weaknesses=[
                "早期不支持并行工具调用",
                "工具调用稳定性待提升",
                "闭源，无法本地部署",
            ],
        )

        self.frameworks[FrameworkName.QWEN] = FrameworkInfo(
            name=FrameworkName.QWEN,
            display_name="Qwen（通义千问）",
            tool_format="function_call (OpenAI 兼容)",
            parallel_support=True,
            max_tools_per_call=10,
            streaming=True,
            function_calling_api="chat.completions (tools 参数)",
            strengths=[
                "OpenAI API 兼容",
                "支持并行工具调用",
                "中文理解能力强",
                "可本地部署（开源模型）",
            ],
            weaknesses=[
                "工具调用生态不如 OpenAI 成熟",
                "部分工具描述不够精确",
                "第三方集成较少",
            ],
        )

        self.frameworks[FrameworkName.GEMINI] = FrameworkInfo(
            name=FrameworkName.GEMINI,
            display_name="Gemini（Google）",
            tool_format="function_declarations (Google 格式)",
            parallel_support=True,
            max_tools_per_call=64,
            streaming=True,
            function_calling_api="generateContent (tools 参数)",
            strengths=[
                "原生多模态能力",
                "支持并行工具调用",
                "Google 生态集成",
                "免费额度高",
            ],
            weaknesses=[
                "工具调用格式与 OpenAI 不兼容",
                "部分版本工具调用不稳定",
                "中文支持不如 Qwen",
            ],
        )

    def get_framework(self, name: FrameworkName) -> FrameworkInfo:
        return self.frameworks[name]

    def list_all(self) -> List[FrameworkInfo]:
        return list(self.frameworks.values())

    def compare(self, frameworks: List[FrameworkName]) -> Dict[str, Any]:
        """对比多个框架"""
        result = {}
        for fw in frameworks:
            info = self.frameworks[fw]
            result[info.display_name] = {
                "tool_format": info.tool_format,
                "parallel_support": info.parallel_support,
                "max_tools": info.max_tools_per_call,
                "streaming": info.streaming,
                "api": info.function_calling_api,
                "strengths": info.strengths,
                "weaknesses": info.weaknesses,
            }
        return result


# ============================================================
# 模块：工具调用格式转换器
# ============================================================

class ToolFormatConverter:
    """工具调用格式转换器"""

    @staticmethod
    def to_openai(name: str, description: str, parameters: dict) -> dict:
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            }
        }

    @staticmethod
    def to_anthropic(name: str, description: str, parameters: dict) -> dict:
        return {
            "name": name,
            "description": description,
            "input_schema": parameters,
        }

    @staticmethod
    def to_gemini(name: str, description: str, parameters: dict) -> dict:
        return {
            "name": name,
            "description": description,
            "parameters": parameters,
        }

    @staticmethod
    def to_qwen(name: str, description: str, parameters: dict) -> dict:
        # Qwen 兼容 OpenAI 格式
        return ToolFormatConverter.to_openai(name, description, parameters)


# ============================================================
# 模块：入口
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  主流 Function Calling 框架对比")
    print("=" * 60)

    registry = FrameworkRegistry()
    frameworks = registry.list_all()

    # 对比表
    print(f"\n{'框架':<12s} {'工具格式':<25s} {'并行':<6s} {'最大工具数':<10s}")
    print("-" * 53)
    for fw in frameworks:
        print(f"{fw.display_name:<12s} {fw.tool_format:<25s} "
              f"{'是' if fw.parallel_support else '否':<6s} "
              f"{fw.max_tools_per_call:<10s}")

    # 格式转换示例
    print("\n" + "=" * 60)
    print("  工具定义格式转换")
    print("=" * 60)

    tool_def = {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "城市名称"}
        },
        "required": ["city"],
    }

    print("\n🔵 OpenAI 格式:")
    print(json.dumps(ToolFormatConverter.to_openai(
        "get_weather", "获取天气", tool_def), indent=2, ensure_ascii=False))

    print("\n🟣 Anthropic 格式:")
    print(json.dumps(ToolFormatConverter.to_anthropic(
        "get_weather", "获取天气", tool_def), indent=2, ensure_ascii=False))

    print("\n🟢 Gemini 格式:")
    print(json.dumps(ToolFormatConverter.to_gemini(
        "get_weather", "获取天气", tool_def), indent=2, ensure_ascii=False))

    print("\n🟡 Qwen 格式（兼容 OpenAI）:")
    print(json.dumps(ToolFormatConverter.to_qwen(
        "get_weather", "获取天气", tool_def), indent=2, ensure_ascii=False))
