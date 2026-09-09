"""
example_usage.py — Tool 定义规范演示
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tool_definition_spec import (
    ToolSchemaBuilder,
    ToolLibrary,
    SchemaValidator,
)


def demo_builder():
    """演示构建器用法"""
    print("=" * 60)
    print("  ToolSchemaBuilder 链式调用")
    print("=" * 60)

    import json
    tool = ToolSchemaBuilder("send_email", "发送邮件到指定收件人") \
        .add_param("to", "string", "收件人邮箱地址", required=True) \
        .add_param("subject", "string", "邮件主题", required=True) \
        .add_param("body", "string", "邮件正文内容", required=True) \
        .add_param("cc", "string", "抄送人邮箱地址", required=False) \
        .add_param("priority", "string", "优先级", required=False,
                   enum=["low", "normal", "high"], default="normal") \
        .build()

    print(f"\n工具名称: {tool.name}")
    print(f"工具描述: {tool.description}")
    print(f"\nJSON Schema:\n{json.dumps(tool.to_openai_format(), indent=2, ensure_ascii=False)}")


def demo_library():
    """演示预定义工具库"""
    print("\n" + "=" * 60)
    print("  预定义工具库")
    print("=" * 60)

    import json
    tools = [ToolLibrary.weather(), ToolLibrary.search(), ToolLibrary.calculator()]
    for t in tools:
        params = ", ".join([f"{p.name} ({p.type})" for p in t.parameters])
        print(f"\n  📦 {t.name}: {t.description}")
        print(f"     参数: {params}")
        print(f"     Schema: {json.dumps(t.to_openai_format(), ensure_ascii=False)[:100]}...")


def demo_validation():
    """演示验证"""
    print("\n" + "=" * 60)
    print("  SchemaValidator 验证")
    print("=" * 60)

    validator = SchemaValidator()

    # 合规工具
    weather = ToolLibrary.weather()
    errors = validator.validate(weather)
    print(f"\n  ✅ get_weather: {'通过' if not errors else ', '.join(errors)}")

    # 不合规工具
    from tool_definition_spec import ToolSchema, ParamDef
    bad = ToolSchema(name="", description="")
    bad.parameters.append(ParamDef(name="", type="invalid", description=""))
    errors = validator.validate(bad)
    print(f"\n  ❌ 不合规工具:")
    for e in errors:
        print(f"     - {e}")


if __name__ == "__main__":
    demo_builder()
    demo_library()
    demo_validation()
