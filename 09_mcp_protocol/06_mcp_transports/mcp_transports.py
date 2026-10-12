"""
mcp_transports.py — MCP 传输层（stdio、SSE、HTTP Streaming）
演示不同传输层的实现方式和适用场景。
"""
import os
import json
import sys
import asyncio
from typing import Optional, Dict, Any


# ============================================================
# 模块：传输层核心类
# ============================================================

class MCPTransport:
    """MCP 传输层基类"""
    
    def __init__(self, name: str):
        self.name = name
        self.connected = False

    async def connect(self):
        raise NotImplementedError

    async def disconnect(self):
        raise NotImplementedError

    async def send(self, message: Dict[str, Any]) -> Optional[str]:
        raise NotImplementedError

    async def receive(self) -> Dict[str, Any]:
        raise NotImplementedError


class StdioTransport(MCPTransport):
    """
    stdio 传输层
    
    基于标准输入输出（stdin/stdout）的传输方式。
    适用于本地进程通信，简单高效，无需网络配置。
    客户端将 Server 作为子进程启动，通过 stdin 发送请求，
    通过 stdout 读取响应。
    """
    
    def __init__(self):
        super().__init__("stdio")

    async def connect(self):
        """stdio 连接通常是即时可用的，因为 stdin/stdout 默认存在"""
        self.connected = True
        print(f"  [{self.name}] 已连接到标准输入输出")

    async def disconnect(self):
        """关闭标准输入输出（通常不需要显式关闭）"""
        self.connected = False
        print(f"  [{self.name}] 已断开")

    async def send(self, message: Dict[str, Any]) -> Optional[str]:
        """发送消息到 stdout"""
        json_str = json.dumps(message, ensure_ascii=False) + "\n"
        sys.stdout.write(json_str)
        sys.stdout.flush()
        return json_str

    async def receive(self) -> Dict[str, Any]:
        """从 stdin 读取消息"""
        line = sys.stdin.readline()
        if not line:
            raise EOFError("End of input stream")
        return json.loads(line.strip())


class SSETransport(MCPTransport):
    """
    SSE (Server-Sent Events) 传输层
    
    基于 HTTP 的 SSE 协议。
    适用于远程服务器通信。
    工作流程：
    1. 客户端 GET /sse 建立长连接，接收服务器消息
    2. 客户端 POST /message 发送请求给服务器
    """
    
    def __init__(self, server_url: str = "http://localhost:3000"):
        super().__init__("sse")
        self.server_url = server_url
        self.endpoint_url = ""

    async def connect(self):
        """建立 SSE 连接"""
        print(f"  [{self.name}] 正在连接到 {self.server_url}...")
        self.connected = True
        self.endpoint_url = f"{self.server_url}/message"
        print(f"  [{self.name}] 连接成功，POST 端点: {self.endpoint_url}")

    async def disconnect(self):
        """断开 SSE 连接"""
        self.connected = False
        print(f"  [{self.name}] 已断开")

    async def send(self, message: Dict[str, Any]) -> Optional[str]:
        """通过 POST 请求发送消息"""
        print(f"  [{self.name}] 发送: {message.get('method', 'unknown')} -> {self.endpoint_url}")
        json_str = json.dumps(message, ensure_ascii=False)
        return json_str

    async def receive(self) -> Dict[str, Any]:
        """从 SSE 事件流接收消息"""
        return {"jsonrpc": "2.0", "method": "mock_event"}


class HTTPTransport(MCPTransport):
    """
    HTTP (Streamable) 传输层
    
    最新的 MCP 传输标准。
    支持双向流式传输，比 SSE 更简单高效。
    客户端和服务器通过单个 HTTP 端点即可进行双向通信。
    """
    
    def __init__(self, server_url: str = "http://localhost:3000"):
        super().__init__("http")
        self.server_url = server_url

    async def connect(self):
        """初始化 HTTP 连接"""
        print(f"  [{self.name}] 初始化 HTTP 流式连接到 {self.server_url}")
        self.connected = True

    async def disconnect(self):
        self.connected = False
        print(f"  [{self.name}] 已断开")

    async def send(self, message: Dict[str, Any]) -> Optional[str]:
        """发送 HTTP 请求"""
        print(f"  [{self.name}] 发送请求 -> {self.server_url}")
        return json.dumps(message, ensure_ascii=False)

    async def receive(self) -> Dict[str, Any]:
        """接收 HTTP 响应流"""
        return {"jsonrpc": "2.0", "id": None, "result": "ok"}


# ============================================================
# 模块：传输层工厂
# ============================================================

def create_transport(transport_type: str, url: str = "http://localhost:3000") -> MCPTransport:
    """
    创建传输层实例
    
    Args:
        transport_type: "stdio", "sse", 或 "http"
        url: 服务器地址（对于 stdio 可忽略）
    
    Returns:
        MCPTransport 实例
    """
    if transport_type == "stdio":
        return StdioTransport()
    elif transport_type == "sse":
        return SSETransport(url)
    elif transport_type == "http":
        return HTTPTransport(url)
    else:
        raise ValueError(f"Unknown transport type: {transport_type}")


# ============================================================
# 模块：入口
# ============================================================

async def main():
    print("=" * 60)
    print("  MCP 传输层演示")
    print("=" * 60)

    # 1. stdio 传输
    print("\n 1. stdio 传输层")
    stdio = create_transport("stdio")
    await stdio.connect()
    await stdio.send({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    await stdio.disconnect()

    # 2. SSE 传输
    print("\n 2. SSE 传输层")
    sse = create_transport("sse", "http://remote-mcp.example.com")
    await sse.connect()
    await sse.send({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    await sse.disconnect()

    # 3. HTTP 传输
    print("\n 3. HTTP (Streamable) 传输层")
    http = create_transport("http", "http://modern-mcp.example.com")
    await http.connect()
    await http.send({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    await http.disconnect()

    print("\n" + "=" * 60)
    print("  传输层对比总结")
    print("=" * 60)
    print("  stdio: 本地进程间通信，简单高效")
    print("  SSE: 远程通信，兼容性好，需两个端点")
    print("  HTTP: 远程通信，最新标准，双向流式")


if __name__ == "__main__":
    asyncio.run(main())
