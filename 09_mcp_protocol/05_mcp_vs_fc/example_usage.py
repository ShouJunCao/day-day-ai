"""
example_usage.py — MCP 与 Function Calling 关系演示
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_vs_fc import (
    MCPTool,
    MCPToFCAdapter,
    get_weather,
    search_database,
    read_file,
)


def demo_adapter():
    """演示 MCP 到 FC 适配器"""
    print("=" * 60)
    print("  MCP 到 Function Calling 适配器")
    print("=" * 60)

    adapter = MCPToFCAdapter()

    # 注册工具
    tools = [
        MCPTool("get_weather", "获取天气", {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        }),
        MCPTool("search_db", "搜索数据库", {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        }),
        MCPTool("read_file", "读取文件", {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        }),
    ]

    handlers = {
        "get_weather": get_weather,
        "search_db": search_database,
        "read_file": read_file,
    }

    for tool in tools:
        adapter.register_tool(tool, handlers[tool.name])

    # 转换为 FC 格式
    print("\n🔄 MCP 工具 → Function Calling 格式:")
    fc_tools = adapter.get_fc_tools()
    for tool in fc_tools:
        print(f"  • {tool['function']['name']}: {tool['function']['description']}")

    # 模拟调用
    print("\n📞 模拟工具调用:")
    mock_call = {
        "id": "call_123",
        "function": {"name": "get_weather", "arguments": '{"city": "北京"}'}
    }
    result = adapter.execute_tool_call(mock_call)
    print(f"  get_weather(北京) → {result.content}")

    mock_call2 = {
        "id": "call_456",
        "function": {"name": "search_db", "arguments": '{"query": "用户"}'}
    }
    result2 = adapter.execute_tool_call(mock_call2)
    print(f"  search_db(用户) → {result2.content}")


def demo_comparison():
    """演示对比"""
    print("\n" + "=" * 60)
    print("  MCP vs Function Calling 对比")
    print("=" * 60)
    print("  MCP: 协议层 — 负责工具发现、连接管理、数据传输")
    print("  FC: 能力层 — 负责工具选择、参数生成、结果整合")
    print("  关系: MCP 是 FC 的基础设施，FC 是 MCP 的使用方式")


if __name__ == "__main__":
    demo_adapter()
    demo_comparison()
