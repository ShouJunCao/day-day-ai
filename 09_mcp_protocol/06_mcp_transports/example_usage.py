"""
example_usage.py — MCP 传输层演示
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_transports import create_transport
import asyncio


async def demo_stdio():
    """演示 stdio 传输层"""
    print("=" * 60)
    print("  stdio 传输层演示")
    print("=" * 60)

    stdio = create_transport("stdio")
    print(f"\n  传输层: {stdio.name}")
    
    await stdio.connect()
    print(f"  连接状态: {stdio.connected}")
    
    await stdio.send({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    await stdio.disconnect()
    print(f"  断开后: {stdio.connected}")


async def demo_sse():
    """演示 SSE 传输层"""
    print("\n" + "=" * 60)
    print("  SSE 传输层演示")
    print("=" * 60)

    sse = create_transport("sse", "http://remote-server:8080")
    print(f"\n  传输层: {sse.name}")
    print(f"  服务器: {sse.server_url}")
    
    await sse.connect()
    await sse.send({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    await sse.disconnect()


async def demo_http():
    """演示 HTTP 传输层"""
    print("\n" + "=" * 60)
    print("  HTTP (Streamable) 传输层演示")
    print("=" * 60)

    http = create_transport("http", "http://streaming-server:8080")
    print(f"\n  传输层: {http.name}")
    print(f"  服务器: {http.server_url}")
    
    await http.connect()
    await http.send({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    await http.disconnect()


async def demo_comparison():
    """演示传输层对比"""
    print("\n" + "=" * 60)
    print("  传输层对比")
    print("=" * 60)
    print("  stdio: 本地进程间通信，简单高效")
    print("  SSE: 远程通信，兼容性好，需两个端点")
    print("  HTTP: 远程通信，最新标准，双向流式")


async def main():
    await demo_stdio()
    await demo_sse()
    await demo_http()
    await demo_comparison()


if __name__ == "__main__":
    asyncio.run(main())
