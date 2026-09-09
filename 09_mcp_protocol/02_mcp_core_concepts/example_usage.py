"""
example_usage.py — MCP 核心概念演示
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_core_concepts import (
    MCPClient,
    MCPServer,
    MCPTool,
    MCPResource,
    MCPPrompt,
    MCPTransport,
    WeatherTool,
)


def demo_server_client():
    """演示 Server 和 Client 的交互"""
    print("=" * 60)
    print("  Server 和 Client 交互")
    print("=" * 60)

    # 创建服务器
    server = MCPServer(
        name="weather-server",
        version="1.0.0",
        description="天气数据服务"
    )

    # 注册能力
    server.register_tool(
        name="get_weather",
        description="获取指定城市天气",
        input_schema={
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        }
    )
    server.register_resource(
        uri="file:///data/weather.json",
        name="天气数据",
        mime_type="application/json"
    )
    server.register_prompt(
        name="weather_report",
        description="生成天气报告",
        arguments=[{"name": "city", "description": "城市名"}]
    )

    # 创建客户端
    client = MCPClient(
        name="weather-client",
        version="1.0.0",
        transport=MCPTransport.STDIO
    )

    # 建立连接
    server_info = {
        "capabilities": server.get_capabilities(),
        "serverInfo": server.get_server_info(),
    }
    client.connect(server_info)

    print(f"\n  服务器: {server.name} v{server.version}")
    print(f"  客户端: {client.name} v{client.version}")
    print(f"  连接状态: {client.connected}")
    print(f"  能力: {list(client.server_capabilities.keys())}")

    # 断开连接
    client.disconnect()
    print(f"  断开后: {client.connected}")


def demo_tool():
    """演示 Tool 的使用"""
    print("\n" + "=" * 60)
    print("  Tool 工具使用")
    print("=" * 60)

    # 创建工具
    tool = MCPTool(
        name="get_weather",
        description="获取指定城市天气",
        input_schema={
            "type": "object",
            "properties": {"city": {"type": "string", "description": "城市名称"}},
            "required": ["city"],
        }
    )

    # 验证输入
    valid = {"city": "北京"}
    invalid = {"temperature": 25}

    print(f"\n  工具: {tool.name}")
    print(f"  描述: {tool.description}")
    print(f"  有效输入: {tool.validate_input(valid)}")
    print(f"  无效输入: {tool.validate_input(invalid)}")


def demo_resource():
    """演示 Resource 的使用"""
    print("\n" + "=" * 60)
    print("  Resource 资源使用")
    print("=" * 60)

    resource = MCPResource(
        uri="file:///docs/guide.md",
        name="用户指南",
        description="MCP 用户使用指南",
        mime_type="text/markdown",
        content="# MCP 用户指南\n\n欢迎使用 MCP 协议..."
    )

    data = resource.read()
    print(f"\n  URI: {data['uri']}")
    print(f"  MIME: {data['mimeType']}")
    print(f"  内容: {data['text'][:30]}...")


def demo_prompt():
    """演示 Prompt 的使用"""
    print("\n" + "=" * 60)
    print("  Prompt 模板使用")
    print("=" * 60)

    prompt = MCPPrompt(
        name="code_review",
        description="代码审查 Prompt",
        arguments=[{"name": "language", "description": "编程语言"}],
        template="请审查以下{language}代码的质量和规范"
    )

    data = prompt.get({"language": "Python"})
    print(f"\n  Prompt: {prompt.name}")
    print(f"  生成: {data['messages'][0]['content']['text']}")


if __name__ == "__main__":
    demo_server_client()
    demo_tool()
    demo_resource()
    demo_prompt()
