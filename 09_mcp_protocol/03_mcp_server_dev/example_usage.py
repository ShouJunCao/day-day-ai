"""
example_usage.py — MCP Server 开发演示
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_server_dev import server


def demo_server_info():
    """演示 Server 信息"""
    print("=" * 60)
    print("  Server 信息")
    print("=" * 60)
    print(f"\n  名称: {server.name}")
    print(f"  版本: {server.version}")
    print(f"  描述: {server.description}")


def demo_tools():
    """演示工具注册和调用"""
    print("\n" + "=" * 60)
    print("  工具演示")
    print("=" * 60)

    print(f"\n  注册的工具 ({len(server.tools)} 个):")
    for name, info in server.tools.items():
        print(f"  • {name}: {info['description']}")

    # 模拟工具调用
    print("\n  工具调用:")
    result = server.handle_request("tools/call", {
        "name": "get_weather",
        "arguments": {"city": "北京"}
    })
    print(f"  get_weather(北京): {result['content'][0]['text']}")

    result = server.handle_request("tools/call", {
        "name": "get_forecast",
        "arguments": {"city": "上海", "days": 3}
    })
    print(f"  get_forecast(上海, 3): {result['content'][0]['text'][:50]}...")

    result = server.handle_request("tools/call", {
        "name": "get_air_quality",
        "arguments": {"city": "广州"}
    })
    print(f"  get_air_quality(广州): {result['content'][0]['text'][:50]}...")


def demo_resources():
    """演示资源注册和读取"""
    print("\n" + "=" * 60)
    print("  资源演示")
    print("=" * 60)

    print(f"\n  注册的资源 ({len(server.resources)} 个):")
    for uri, info in server.resources.items():
        print(f"  • {info['name']}: {info['description']}")

    result = server.handle_request("resources/read", {
        "uri": "file:///docs/guide.md"
    })
    print(f"\n  读取用户指南: {len(result['contents'][0]['text'])} 字符")

    result = server.handle_request("resources/read", {
        "uri": "file:///data/weather.json"
    })
    print(f"  读取天气数据: {len(result['contents'][0]['text'])} 字符")


def demo_prompts():
    """演示 Prompt 注册和获取"""
    print("\n" + "=" * 60)
    print("  Prompt 演示")
    print("=" * 60)

    print(f"\n  注册的 Prompts ({len(server.prompts)} 个):")
    for name, info in server.prompts.items():
        print(f"  • {name}: {info['description']}")

    result = server.handle_request("prompts/get", {
        "name": "weather_report",
        "arguments": {"city": "广州", "days": 5}
    })
    print(f"\n  天气报告 Prompt: {result['messages'][0]['content']['text'][:50]}...")

    result = server.handle_request("prompts/get", {
        "name": "code_review",
        "arguments": {"language": "Python", "focus": "代码质量"}
    })
    print(f"  代码审查 Prompt: {result['messages'][0]['content']['text'][:50]}...")


def demo_capabilities():
    """演示能力获取"""
    print("\n" + "=" * 60)
    print("  能力获取")
    print("=" * 60)

    caps = server.handle_request("initialize", {})
    print(f"\n  协议版本: {caps['protocolVersion']}")
    print(f"  服务器: {caps['serverInfo']['name']} v{caps['serverInfo']['version']}")
    print(f"  能力: {list(caps['capabilities'].keys())}")


if __name__ == "__main__":
    demo_server_info()
    demo_tools()
    demo_resources()
    demo_prompts()
    demo_capabilities()
