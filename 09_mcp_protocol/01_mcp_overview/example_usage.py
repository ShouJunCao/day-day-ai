"""
example_usage.py — MCP 协议概述演示
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_protocol import (
    MCPProtocolHandler,
    MCPServerInfo,
)


def demo_lifecycle():
    """演示 MCP 生命周期"""
    print("=" * 60)
    print("  MCP 协议生命周期演示")
    print("=" * 60)

    server = MCPProtocolHandler(
        MCPServerInfo(name="weather-server", version="1.0.0")
    )

    # 注册能力
    server.register_tool(
        name="get_weather",
        description="获取天气",
        input_schema={
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    )
    server.register_resource(
        uri="file:///data/weather.json",
        name="天气数据",
    )
    server.register_prompt(
        name="weather_report",
        description="生成天气报告",
        arguments=[{"name": "city", "description": "城市名"}],
    )

    # 1. Initialize
    print("\n🔌 1. Initialize 握手")
    resp = server.handle_message(json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                   "clientInfo": {"name": "client", "version": "1.0"}},
    }))
    if resp:
        print(f"  协议版本: {resp.result['protocolVersion']}")
        print(f"  服务器: {resp.result['serverInfo']['name']}")

    # 2. Initialized 通知
    print("\n📢 2. Initialized 通知")
    server.handle_message(json.dumps({
        "jsonrpc": "2.0", "method": "notifications/initialized"
    }))
    print(f"  服务器状态: initialized={server.initialized}")

    # 3. 能力交互
    print("\n🔧 3. 能力交互")
    resp = server.handle_message(json.dumps({
        "jsonrpc": "2.0", "id": 2, "method": "tools/list"
    }))
    if resp:
        caps = resp.result.get("capabilities", {})
        tools = caps.get("tools", {})
        print(f"  工具: {[t['name'] for t in resp.result.get('tools', [])]}")

    resp = server.handle_message(json.dumps({
        "jsonrpc": "2.0", "id": 3, "method": "resources/list"
    }))
    if resp:
        print(f"  资源: {[r['name'] for r in resp.result.get('resources', [])]}")

    resp = server.handle_message(json.dumps({
        "jsonrpc": "2.0", "id": 4, "method": "prompts/list"
    }))
    if resp:
        print(f"  Prompts: {[p['name'] for p in resp.result.get('prompts', [])]}")


def demo_tool_call():
    """演示工具调用"""
    print("\n" + "=" * 60)
    print("  MCP 工具调用")
    print("=" * 60)

    server = MCPProtocolHandler(MCPServerInfo(name="demo", version="1.0"))
    server.register_tool("get_weather", "获取天气", {
        "type": "object",
        "properties": {"city": {"type": "string"}},
        "required": ["city"],
    })
    server.initialized = True

    resp = server.handle_message(json.dumps({
        "jsonrpc": "2.0", "id": 10, "method": "tools/call",
        "params": {"name": "get_weather", "arguments": {"city": "北京"}},
    }))
    if resp and resp.result:
        print(f"  工具: get_weather")
        print(f"  参数: 北京")
        print(f"  结果: {resp.result['content'][0]['text']}")


def demo_error_handling():
    """演示错误处理"""
    print("\n" + "=" * 60)
    print("  MCP 错误处理")
    print("=" * 60)

    server = MCPProtocolHandler(MCPServerInfo(name="demo", version="1.0"))

    # 方法不存在
    resp = server.handle_message(json.dumps({
        "jsonrpc": "2.0", "id": 20, "method": "unknown/method"
    }))
    if resp and resp.error:
        print(f"  错误: {resp.error['message']} (code: {resp.error['code']})")

    # 解析错误
    resp = server.handle_message("invalid json")
    if resp and resp.error:
        print(f"  解析错误: {resp.error['message']} (code: {resp.error['code']})")


if __name__ == "__main__":
    demo_lifecycle()
    demo_tool_call()
    demo_error_handling()
