"""
mcp_protocol.py — MCP 协议概述与设计理念
"""
import os
import json
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


# ============================================================
# 模块：MCP 数据结构
# ============================================================

class MCPErrorCodes(Enum):
    """MCP 错误码"""
    PARSE_ERROR = -32700       # 解析错误
    INVALID_REQUEST = -32600   # 无效请求
    METHOD_NOT_FOUND = -32601  # 方法不存在
    INVALID_PARAMS = -32602    # 参数无效
    INTERNAL_ERROR = -32603    # 内部错误


@dataclass
class MCPServerInfo:
    """MCP 服务器信息"""
    name: str
    version: str
    description: str = ""


@dataclass
class MCPTool:
    """MCP 工具定义"""
    name: str
    description: str
    input_schema: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPResource:
    """MCP 资源定义"""
    uri: str
    name: str
    description: str = ""
    mime_type: str = "text/plain"


@dataclass
class MCPPrompt:
    """MCP Prompt 定义"""
    name: str
    description: str = ""
    arguments: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class MCPMessage:
    """MCP JSON-RPC 消息"""
    jsonrpc: str = "2.0"
    id: Optional[Any] = None
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        data = {"jsonrpc": self.jsonrpc}
        if self.id is not None:
            data["id"] = self.id
        if self.method is not None:
            data["method"] = self.method
            if self.params is not None:
                data["params"] = self.params
        elif self.result is not None:
            data["result"] = self.result
        elif self.error is not None:
            data["error"] = self.error
        return data

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "MCPMessage":
        return MCPMessage(
            jsonrpc=data.get("jsonrpc", "2.0"),
            id=data.get("id"),
            method=data.get("method"),
            params=data.get("params"),
            result=data.get("result"),
            error=data.get("error"),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


# ============================================================
# 模块：MCP 协议处理器
# ============================================================

class MCPProtocolHandler:
    """
    MCP 协议处理器：实现 JSON-RPC 2.0 over stdio 的基本协议处理。

    MCP（Model Context Protocol）是 Anthropic 提出的开放协议，
    用于标准化 AI 应用与外部数据源和工具的集成方式。

    协议核心概念：
    1. Transport Layer: 通信传输层（stdio / SSE / HTTP）
    2. Protocol Layer: JSON-RPC 2.0 协议层
    3. Capabilities: 工具、资源、Prompt 三大能力
    4. Lifecycle: 初始化 → 能力协商 → 交互 → 关闭
    """

    def __init__(self, server_info: MCPServerInfo):
        self.server_info = server_info
        self.tools: Dict[str, MCPTool] = {}
        self.resources: Dict[str, MCPResource] = {}
        self.prompts: Dict[str, MCPPrompt] = {}
        self.initialized = False
        self.message_id = 0

    def register_tool(self, name: str, description: str, input_schema: Dict):
        """注册工具"""
        self.tools[name] = MCPTool(
            name=name, description=description, input_schema=input_schema
        )

    def register_resource(self, uri: str, name: str, description: str = ""):
        """注册资源"""
        self.resources[uri] = MCPResource(
            uri=uri, name=name, description=description
        )

    def register_prompt(self, name: str, description: str = "",
                        arguments: Optional[List[Dict[str, str]]] = None):
        """注册 Prompt"""
        self.prompts[name] = MCPPrompt(
            name=name, description=description,
            arguments=arguments or [],
        )

    # --- Lifecycle Methods ---

    def handle_initialize(self, params: Dict) -> MCPMessage:
        """处理 initialize 请求"""
        self.initialized = True
        return MCPMessage(
            id=params.get("_id"),
            result={
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": True},
                    "resources": {"listChanged": True, "subscribe": True},
                    "prompts": {"listChanged": True},
                },
                "serverInfo": {
                    "name": self.server_info.name,
                    "version": self.server_info.version,
                },
            },
        )

    def handle_initialized(self, params: Dict) -> None:
        """处理 initialized 通知（无回复）"""
        pass  # 通知类型，不需要回复

    # --- Tools Methods ---

    def handle_tools_list(self, params: Dict) -> MCPMessage:
        """处理 tools/list 请求"""
        tools_list = [
            {"name": t.name, "description": t.description, "inputSchema": t.input_schema}
            for t in self.tools.values()
        ]
        return MCPMessage(
            id=params.get("_id"),
            result={"tools": tools_list},
        )

    def handle_tools_call(self, params: Dict) -> MCPMessage:
        """处理 tools/call 请求"""
        tool_name = params.get("name", "")
        tool_args = params.get("arguments", {})

        if tool_name not in self.tools:
            return MCPMessage(
                id=params.get("_id"),
                error={
                    "code": MCPErrorCodes.METHOD_NOT_FOUND.value,
                    "message": f"Tool not found: {tool_name}",
                },
            )

        # 这里模拟工具执行结果
        result_content = f"执行工具 {tool_name}，参数: {json.dumps(tool_args, ensure_ascii=False)}"
        return MCPMessage(
            id=params.get("_id"),
            result={
                "content": [{"type": "text", "text": result_content}],
                "isError": False,
            },
        )

    # --- Resources Methods ---

    def handle_resources_list(self, params: Dict) -> MCPMessage:
        """处理 resources/list 请求"""
        resources_list = [
            {"uri": r.uri, "name": r.name, "description": r.description, "mimeType": r.mime_type}
            for r in self.resources.values()
        ]
        return MCPMessage(
            id=params.get("_id"),
            result={"resources": resources_list},
        )

    def handle_resources_read(self, params: Dict) -> MCPMessage:
        """处理 resources/read 请求"""
        uri = params.get("uri", "")
        if uri not in self.resources:
            return MCPMessage(
                id=params.get("_id"),
                error={
                    "code": MCPErrorCodes.INVALID_PARAMS.value,
                    "message": f"Resource not found: {uri}",
                },
            )
        return MCPMessage(
            id=params.get("_id"),
            result={
                "contents": [{
                    "uri": uri,
                    "mimeType": self.resources[uri].mime_type,
                    "text": f"Content of {uri}",
                }]
            },
        )

    # --- Prompts Methods ---

    def handle_prompts_list(self, params: Dict) -> MCPMessage:
        """处理 prompts/list 请求"""
        prompts_list = [
            {"name": p.name, "description": p.description, "arguments": p.arguments}
            for p in self.prompts.values()
        ]
        return MCPMessage(
            id=params.get("_id"),
            result={"prompts": prompts_list},
        )

    def handle_prompts_get(self, params: Dict) -> MCPMessage:
        """处理 prompts/get 请求"""
        prompt_name = params.get("name", "")
        if prompt_name not in self.prompts:
            return MCPMessage(
                id=params.get("_id"),
                error={
                    "code": MCPErrorCodes.INVALID_PARAMS.value,
                    "message": f"Prompt not found: {prompt_name}",
                },
            )
        return MCPMessage(
            id=params.get("_id"),
            result={
                "description": self.prompts[prompt_name].description,
                "messages": [
                    {"role": "user", "content": {"type": "text", "text": f"使用 prompt: {prompt_name}"}}
                ],
            },
        )

    # --- Protocol Entry Point ---

    def handle_message(self, raw_json: str) -> Optional[MCPMessage]:
        """处理收到的 JSON-RPC 消息"""
        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError:
            return MCPMessage(
                error={
                    "code": MCPErrorCodes.PARSE_ERROR.value,
                    "message": "Parse error",
                }
            )

        msg = MCPMessage.from_dict(data)
        method = msg.method

        # 将 id 传入 params 以便回复
        params = dict(msg.params) if msg.params else {}
        params["_id"] = msg.id

        if method == "initialize":
            return self.handle_initialize(params)
        elif method == "notifications/initialized":
            self.handle_initialized(params)
            return None
        elif method == "tools/list":
            return self.handle_tools_list(params)
        elif method == "tools/call":
            return self.handle_tools_call(params)
        elif method == "resources/list":
            return self.handle_resources_list(params)
        elif method == "resources/read":
            return self.handle_resources_read(params)
        elif method == "prompts/list":
            return self.handle_prompts_list(params)
        elif method == "prompts/get":
            return self.handle_prompts_get(params)
        else:
            return MCPMessage(
                id=msg.id,
                error={
                    "code": MCPErrorCodes.METHOD_NOT_FOUND.value,
                    "message": f"Method not found: {method}",
                },
            )

    def next_message_id(self) -> int:
        self.message_id += 1
        return self.message_id


# ============================================================
# 模块：入口
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  MCP 协议概述与设计理念演示")
    print("=" * 60)

    # 1. 创建 MCP 服务器
    server = MCPProtocolHandler(
        MCPServerInfo(name="demo-server", version="1.0.0", description="MCP 协议演示服务器")
    )

    # 2. 注册能力
    server.register_tool(
        name="get_weather",
        description="获取指定城市天气",
        input_schema={
            "type": "object",
            "properties": {"city": {"type": "string", "description": "城市名称"}},
            "required": ["city"],
        },
    )

    server.register_resource(
        uri="file:///docs/guide.md",
        name="用户指南",
        description="MCP 用户使用指南",
    )

    server.register_prompt(
        name="code_review",
        description="代码审查 Prompt",
        arguments=[{"name": "language", "description": "编程语言"}],
    )

    # 3. 生命周期：initialize
    print("\n📋 步骤 1: Initialize")
    init_msg = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "demo-client", "version": "1.0.0"},
        },
    }, ensure_ascii=False)
    response = server.handle_message(init_msg)
    print(f"  请求: {init_msg[:80]}...")
    if response:
        print(f"  响应: {response.to_json()[:120]}...")

    # 4. 通知: initialized
    print("\n📋 步骤 2: Initialized 通知")
    init_notify = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}, ensure_ascii=False)
    server.handle_message(init_notify)
    print(f"  通知: {init_notify}")
    print(f"  服务器状态: initialized={server.initialized}")

    # 5. 工具列表
    print("\n📋 步骤 3: Tools/List")
    tools_list_msg = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, ensure_ascii=False)
    response = server.handle_message(tools_list_msg)
    print(f"  工具数量: {len(server.tools)}")
    for tool in server.tools.values():
        print(f"  • {tool.name}: {tool.description}")

    # 6. 工具调用
    print("\n📋 步骤 4: Tools/Call")
    call_msg = json.dumps({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": "get_weather", "arguments": {"city": "北京"}},
    }, ensure_ascii=False)
    response = server.handle_message(call_msg)
    print(f"  请求: tools/call(get_weather, 北京)")
    if response and response.result:
        print(f"  响应: {response.result['content'][0]['text']}")
    else:
        print(f"  响应: {response}")

    # 7. 资源列表
    print("\n📋 步骤 5: Resources/List")
    res_msg = json.dumps({"jsonrpc": "2.0", "id": 4, "method": "resources/list"}, ensure_ascii=False)
    response = server.handle_message(res_msg)
    print(f"  资源数量: {len(server.resources)}")
    for res in server.resources.values():
        print(f"  • {res.uri}: {res.name}")

    # 8. 协议对比表
    print("\n" + "=" * 60)
    print("  MCP vs Function Calling vs OpenAPI 对比")
    print("=" * 60)
    print(f"{'维度':<15s} {'MCP':<25s} {'Function Calling':<25s}")
    print("-" * 65)
    print(f"{'协议性质':<15s} {'开放标准协议':<25s} {'厂商特定实现':<25s}")
    print(f"{'传输层':<15s} {'stdio / SSE / HTTP':<25s} {'HTTP API':<25s}")
    print(f"{'数据格式':<15s} {'JSON-RPC 2.0':<25s} {'厂商自定义':<25s}")
    print(f"{'能力类型':<15s} {'工具+资源+Prompt':<25s} {'仅工具调用':<25s}")
    print(f"{'生态系统':<15s} {'跨厂商互操作':<25s} {'绑定特定厂商':<25s}")
    print(f"{'设计理念':<15s} {'统一协议标准':<25s} {'SDK 集成':<25s}")
