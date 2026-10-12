"""
example_usage.py — MCP 生态与社区工具演示
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_ecosystem import MCPHub, Smithery


def demo_hub():
    """演示 MCP Hub"""
    print("=" * 60)
    print("  MCP Hub 演示")
    print("=" * 60)

    hub = MCPHub()

    # 发现所有服务器
    print("\n📦 所有可用服务器:")
    all_servers = hub.discover()
    print(f"  共 {len(all_servers)} 个")
    for s in all_servers[:5]:
        print(f"  • {s.name}: {s.description}")

    # 搜索
    print("\n🔍 搜索 '数据库':")
    results = hub.discover("数据库")
    for s in results:
        print(f"  • {s.name}: {s.description}")

    # 安装
    print("\n️  安装 github-mcp-server:")
    hub.install("github-mcp-server")


def demo_smithery():
    """演示 Smithery"""
    print("\n" + "=" * 60)
    print("  Smithery 演示")
    print("=" * 60)

    smithery = Smithery()

    # 列出已托管
    print("\n 已托管服务器:")
    hosted = smithery.list_hosted()
    for s in hosted:
        print(f"  • {s['name']} ({s['region']}): {s['status']}")

    # 部署
    print("\n 部署新服务器:")
    smithery.deploy("my-custom-mcp", "ap-east-1")


def demo_comparison():
    """演示对比"""
    print("\n" + "=" * 60)
    print("  MCP Hub vs Smithery 对比")
    print("=" * 60)
    print("  MCP Hub: 服务器发现和管理（类似 npm/PyPI）")
    print("  Smithery: 服务器托管和部署（类似 Vercel/Netlify）")


if __name__ == "__main__":
    demo_hub()
    demo_smithery()
    demo_comparison()
