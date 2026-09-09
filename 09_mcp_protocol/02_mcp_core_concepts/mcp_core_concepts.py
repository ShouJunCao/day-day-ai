"""
mcp_core_concepts.py — MCP 核心概念（Server、Client、Tools、Resources）
"""
import os
import json
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


# ============================================================
# 模块：MCP 核心概念
# ============================================================

class MCPTransport(Enum):
    """MCP 传输层类型"""
    STDIO = "stdio"
    SSE = "sse"
    HTTP = "http"


@dataclass
class MCPClient:
    """
    MCP 客户端
    
    代表使用 MCP 服务的 AI 应用。
    客户端通过 MCP 协议与服务器通信，发现并使用服务器提供的工具、资源和 Prompts。
    
    核心职责：
    1. 初始化与服务器的连接
    2. 发现服务器支持的能力
    3. 调用工具、读取资源、获取 Prompts
    4. 处理服务器返回的结果
    """
    name: str
    version: str
    transport: MCPTransport = MCPTransport.STDIO
    connected: bool = False
    server_capabilities: Dict[str, Any] = field(default_factory=dict)

    def connect(self, server_info: Dict[str, Any]) -> None:
        """建立与服务器的连接"""
        self.connected = True
        self.server_capabilities = server_info.get("capabilities", {})

    def disconnect(self) -> None:
        """断开与服务器的连接"""
        self.connected = False
        self.server_capabilities = {}


@dataclass
class MCPServer:
    """
    MCP 服务器
    
    代表提供 MCP 服务的数据源或工具提供者。
    服务器通过 MCP 协议暴露工具、资源和 Prompts 给客户端。
    
    核心职责：
    1. 注册和暴露工具、资源、Prompts
    2. 处理客户端的请求
    3. 执行工具调用、读取资源、生成 Prompts
    4. 返回结果给客户端
    """
    name: str
    version: str
    description: str = ""
    transport: MCPTransport = MCPTransport.STDIO
    tools: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    resources: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    prompts: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def register_tool(self, name: str, description: str, input_schema: Dict[str, Any]) -> None:
        """注册工具"""
        self.tools[name] = {
            "name": name,
            "description": description,
            "inputSchema": input_schema,
        }

    def register_resource(self, uri: str, name: str, description: str = "", mime_type: str = "text/plain") -> None:
        """注册资源"""
        self.resources[uri] = {
            "uri": uri,
            "name": name,
            "description": description,
            "mimeType": mime_type,
        }

    def register_prompt(self, name: str, description: str = "", arguments: Optional[List[Dict[str, Any]]] = None) -> None:
        """注册 Prompt"""
        self.prompts[name] = {
            "name": name,
            "description": description,
            "arguments": arguments or [],
        }

    def get_capabilities(self) -> Dict[str, Any]:
        """获取服务器能力"""
        return {
            "tools": {"listChanged": True},
            "resources": {"listChanged": True, "subscribe": True},
            "prompts": {"listChanged": True},
        }

    def get_server_info(self) -> Dict[str, str]:
        """获取服务器信息"""
        return {
            "name": self.name,
            "version": self.version,
        }


@dataclass
class MCPTool:
    """
    MCP 工具定义
    
    工具是 MCP 服务器暴露给客户端的可执行功能。
    每个工具包含名称、描述和输入参数 Schema。
    
    核心特性：
    1. 通过 tools/list 发现
    2. 通过 tools/call 执行
    3. 支持参数验证
    4. 返回结构化结果
    """
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Optional[Any] = None  # 实际执行函数

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }

    def validate_input(self, arguments: Dict[str, Any]) -> bool:
        """验证输入参数"""
        required = self.input_schema.get("required", [])
        properties = self.input_schema.get("properties", {})
        
        # 检查必填参数
        for param in required:
            if param not in arguments:
                return False
        
        # 检查参数类型
        for param, value in arguments.items():
            if param in properties:
                expected_type = properties[param].get("type")
                if expected_type == "string" and not isinstance(value, str):
                    return False
                elif expected_type == "integer" and not isinstance(value, int):
                    return False
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    return False
                elif expected_type == "boolean" and not isinstance(value, bool):
                    return False
        
        return True


@dataclass
class MCPResource:
    """
    MCP 资源定义
    
    资源是 MCP 服务器暴露给客户端的可读取数据。
    每个资源通过 URI 唯一标识，包含名称、描述和 MIME 类型。
    
    核心特性：
    1. 通过 resources/list 发现
    2. 通过 resources/read 读取
    3. 支持订阅变更通知
    4. 支持多种 MIME 类型
    """
    uri: str
    name: str
    description: str = ""
    mime_type: str = "text/plain"
    content: Optional[str] = None
    last_modified: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
            "mimeType": self.mime_type,
        }

    def read(self) -> Dict[str, Any]:
        """读取资源内容"""
        return {
            "uri": self.uri,
            "mimeType": self.mime_type,
            "text": self.content or "",
        }


@dataclass
class MCPPrompt:
    """
    MCP Prompt 定义
    
    Prompt 是 MCP 服务器暴露给客户端的可复用提示词模板。
    每个 Prompt 包含名称、描述和参数列表。
    
    核心特性：
    1. 通过 prompts/list 发现
    2. 通过 prompts/get 获取
    3. 支持参数填充
    4. 返回结构化消息
    """
    name: str
    description: str = ""
    arguments: List[Dict[str, Any]] = field(default_factory=list)
    template: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "name": self.name,
            "description": self.description,
            "arguments": self.arguments,
        }

    def get(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """获取填充参数后的 Prompt"""
        messages = []
        if self.template:
            template = self.template
            for key, value in arguments.items():
                template = template.replace(f"{{{key}}}", str(value))
            messages.append({"role": "user", "content": {"type": "text", "text": template}})
        
        return {
            "description": self.description,
            "messages": messages,
        }


# ============================================================
# 模块：示例工具实现
# ============================================================

class WeatherTool:
    """天气查询工具示例"""
    
    def __init__(self):
        self.weather_data = {
            "北京": {"weather": "晴", "temp": 25, "humidity": 45, "wind": "北风 2 级"},
            "上海": {"weather": "多云", "temp": 28, "humidity": 65, "wind": "东南风 3 级"},
            "广州": {"weather": "雷阵雨", "temp": 32, "humidity": 85, "wind": "南风 1 级"},
        }

    def get_weather(self, city: str) -> str:
        """获取指定城市天气"""
        data = self.weather_data.get(city, {"weather": "未知", "temp": 0, "humidity": 0, "wind": "未知"})
        return json.dumps({"city": city, **data}, ensure_ascii=False)


class FileResource:
    """文件资源示例"""
    
    def __init__(self, uri: str, content: str):
        self.uri = uri
        self.content = content
        self.last_modified = time.time()

    def read(self) -> Dict[str, Any]:
        """读取文件内容"""
        return {
            "uri": self.uri,
            "mimeType": "text/plain",
            "text": self.content,
        }


# ============================================================
# 模块：入口
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  MCP 核心概念演示")
    print("=" * 60)

    # 1. 创建服务器
    print("\n📦 1. 创建 MCP 服务器")
    server = MCPServer(
        name="demo-server",
        version="1.0.0",
        description="MCP 核心概念演示服务器"
    )
    print(f"  服务器: {server.name} v{server.version}")

    # 2. 注册工具
    print("\n🔧 2. 注册工具")
    server.register_tool(
        name="get_weather",
        description="获取指定城市天气",
        input_schema={
            "type": "object",
            "properties": {"city": {"type": "string", "description": "城市名称"}},
            "required": ["city"],
        }
    )
    print(f"  已注册工具: {list(server.tools.keys())}")

    # 3. 注册资源
    print("\n📄 3. 注册资源")
    server.register_resource(
        uri="file:///docs/guide.md",
        name="用户指南",
        description="MCP 用户使用指南",
        mime_type="text/markdown"
    )
    print(f"  已注册资源: {list(server.resources.keys())}")

    # 4. 注册 Prompt
    print("\n💬 4. 注册 Prompt")
    server.register_prompt(
        name="code_review",
        description="代码审查 Prompt",
        arguments=[{"name": "language", "description": "编程语言", "required": True}]
    )
    print(f"  已注册 Prompts: {list(server.prompts.keys())}")

    # 5. 创建客户端
    print("\n🔌 5. 创建 MCP 客户端")
    client = MCPClient(
        name="demo-client",
        version="1.0.0",
        transport=MCPTransport.STDIO
    )
    print(f"  客户端: {client.name} v{client.version}")

    # 6. 建立连接
    print("\n🤝 6. 建立连接")
    server_info = {
        "capabilities": server.get_capabilities(),
        "serverInfo": server.get_server_info(),
    }
    client.connect(server_info)
    print(f"  连接状态: {client.connected}")
    print(f"  服务器能力: {list(client.server_capabilities.keys())}")

    # 7. 工具调用示例
    print("\n🎯 7. 工具调用示例")
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
    valid_input = {"city": "北京"}
    invalid_input = {"temperature": 25}  # 缺少必填参数 city
    
    print(f"  有效输入: {tool.validate_input(valid_input)}")
    print(f"  无效输入: {tool.validate_input(invalid_input)}")

    # 8. 资源读取示例
    print("\n📖 8. 资源读取示例")
    resource = MCPResource(
        uri="file:///docs/guide.md",
        name="用户指南",
        description="MCP 用户使用指南",
        mime_type="text/markdown",
        content="# MCP 用户指南\n\n欢迎使用 MCP 协议...",
        last_modified=time.time()
    )
    resource_data = resource.read()
    print(f"  资源 URI: {resource_data['uri']}")
    print(f"  内容长度: {len(resource_data['text'])} 字符")

    # 9. Prompt 获取示例
    print("\n📝 9. Prompt 获取示例")
    prompt = MCPPrompt(
        name="code_review",
        description="代码审查 Prompt",
        arguments=[{"name": "language", "description": "编程语言", "required": True}],
        template="请审查以下{language}代码的质量和规范"
    )
    prompt_data = prompt.get({"language": "Python"})
    print(f"  Prompt 名称: {prompt.name}")
    print(f"  生成消息: {prompt_data['messages'][0]['content']['text']}")

    # 10. 断开连接
    print("\n🔌 10. 断开连接")
    client.disconnect()
    print(f"  连接状态: {client.connected}")

    print("\n" + "=" * 60)
    print("  MCP 核心概念演示完成")
    print("=" * 60)
