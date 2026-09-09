"""
example_usage.py — 主流框架对比演示
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from framework_comparison import (
    FrameworkRegistry,
    ToolFormatConverter,
    FrameworkName,
)


def demo_comparison():
    """框架对比"""
    print("=" * 60)
    print("  主流 Function Calling 框架对比")
    print("=" * 60)

    registry = FrameworkRegistry()
    frameworks = registry.list_all()

    print(f"\n{'框架':<12s} {'工具格式':<25s} {'并行':<6s} {'最大工具数':<10s}")
    print("-" * 53)
    for fw in frameworks:
        print(f"{fw.display_name:<12s} {fw.tool_format:<25s} "
              f"{'是' if fw.parallel_support else '否':<6s} "
              f"{fw.max_tools_per_call:<10d}")

    print(f"\n{'框架':<12s} {'Streaming':<10s} {'API 端点':<25s}")
    print("-" * 47)
    for fw in frameworks:
        print(f"{fw.display_name:<12s} {'✅' if fw.streaming else '❌':<10s} "
              f"{fw.function_calling_api:<25s}")


def demo_format_conversion():
    """格式转换"""
    print("\n" + "=" * 60)
    print("  工具定义格式转换")
    print("=" * 60)

    tool_def = {
        "type": "object",
        "properties": {"city": {"type": "string", "description": "城市名称"}},
        "required": ["city"],
    }

    for name, converter in [
        ("OpenAI", ToolFormatConverter.to_openai),
        ("Anthropic", ToolFormatConverter.to_anthropic),
        ("Gemini", ToolFormatConverter.to_gemini),
        ("Qwen", ToolFormatConverter.to_qwen),
    ]:
        result = converter("get_weather", "获取天气", tool_def)
        print(f"\n📦 {name} 格式:")
        print(f"  {json.dumps(result, ensure_ascii=False)[:80]}...")


def demo_strengths_weaknesses():
    """优势劣势"""
    print("\n" + "=" * 60)
    print("  各框架优势与劣势")
    print("=" * 60)

    registry = FrameworkRegistry()
    for fw in registry.list_all():
        print(f"\n🔵 {fw.display_name}:")
        print(f"  ✅ 优势:")
        for s in fw.strengths:
            print(f"    • {s}")
        print(f"  ❌ 劣势:")
        for w in fw.weaknesses:
            print(f"    • {w}")


def demo_selection():
    """选型建议"""
    print("\n" + "=" * 60)
    print("  选型建议")
    print("=" * 60)
    print(f"{'需求':<20s} {'推荐框架':<15s} {'理由':<30s}")
    print("-" * 65)
    print(f"{'最完善生态':<20s} {'OpenAI':<15s} {'工具生态最成熟':<30s}")
    print(f"{'安全+长上下文':<20s} {'Anthropic':<15s} {'200K 上下文，安全对齐':<30s}")
    print(f"{'本地部署+中文':<20s} {'Qwen':<15s} {'开源可本地部署':<30s}")
    print(f"{'多模态+低成本':<20s} {'Gemini':<15s} {'原生多模态，免费额度高':<30s}")


if __name__ == "__main__":
    demo_comparison()
    demo_format_conversion()
    demo_strengths_weaknesses()
    demo_selection()
