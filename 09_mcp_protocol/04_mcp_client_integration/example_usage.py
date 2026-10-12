"""
example_usage.py — MCP Client 集成与多 Server 编排演示
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_client_integration import MCPClient, MCPOrchestrator


def demo_client():
    """演示 Client 集成"""
    print("=" * 60)
    print("  Client 集成演示")
    print("=" * 60)

    # 创建 Client
    client = MCPClient(name="my-app", version="1.0.0")
    print(f"\n  客户端: {client.name} v{client.version}")

    # 连接多个 Server
    client.connect_server("weather-server", {"name": "weather", "version": "1.0"})
    client.connect_server("db-server", {"name": "db", "version": "1.0"})
    client.connect_server("file-server", {"name": "file", "version": "1.0"})
    print(f"  已连接: {list(client.servers.keys())}")

    # 获取能力
    caps = client.get_capabilities()
    print(f"\n  能力摘要:")
    for name, cap in caps.items():
        print(f"  • {name}: {cap['tools']} 工具, {cap['resources']} 资源")

    # 列出所有工具
    tools = client.list_all_tools()
    print(f"\n  所有工具 ({len(tools)} 个):")
    for tool in tools:
        print(f"  • [{tool['_server']}] {tool['name']}: {tool['description']}")

    # 调用工具
    result = client.call_tool("weather-server", "get_weather", {"city": "北京"})
    print(f"\n  调用: {result['content'][0]['text']}")

    # 断开
    for name in list(client.servers.keys()):
        client.disconnect_server(name)
    print(f"\n  断开后: {client.connected}")


def demo_orchestrator():
    """演示多 Server 编排"""
    print("\n" + "=" * 60)
    print("  多 Server 编排演示")
    print("=" * 60)

    client = MCPClient(name="orchestrator-app", version="1.0.0")
    client.connect_server("weather-server", {"name": "weather", "version": "1.0"})
    client.connect_server("file-server", {"name": "file", "version": "1.0"})

    orchestrator = MCPOrchestrator(client)

    # 查找工具
    info = orchestrator.find_tool("get_weather")
    if info:
        print(f"\n  查找 get_weather: 在 {info['server']} 中找到")

    # 执行工作流
    workflow = [
        {"server": "weather-server", "tool": "get_weather", "arguments": {"city": "北京"}},
        {"server": "file-server", "tool": "write_file", "arguments": {
            "path": "/reports/weather.txt",
            "content": "北京天气: {{result_1}}"
        }},
    ]
    results = orchestrator.execute_workflow(workflow)
    print(f"  工作流: {len(results)} 步")
    for i, r in enumerate(results):
        print(f"    步骤 {i+1}: {r['step']['tool']} → 成功")

    for name in list(client.servers.keys()):
        client.disconnect_server(name)


if __name__ == "__main__":
    demo_client()
    demo_orchestrator()
