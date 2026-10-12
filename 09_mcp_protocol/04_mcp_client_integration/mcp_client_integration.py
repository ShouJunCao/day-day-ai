"""
mcp_client_integration.py — MCP Client 集成与多 Server 编排
演示如何集成 MCP Client 并管理多个 Server。
"""
import os
import json
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


# ============================================================
# 模块：MCP Client SDK 核心类
# ============================================================

class MCPClient:
    """
    MCP Client SDK 核心类
    
    提供 MCP 客户端的基础框架，包括：
    1. 连接管理（单 Server / 多 Server）
    2. 能力发现
    3. 工具调用
    4. 资源读取
    5. Prompt 获取
    6. 多 Server 编排
    """
    
    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version
        self.servers: Dict[str, 'MCPServerConnection'] = {}
        self.connected = False

    def connect_server(self, server_name: str, server_info: Dict[str, Any]) -> None:
        """连接到一个 MCP Server"""
        conn = MCPServerConnection(server_name, server_info)
        self.servers[server_name] = conn
        conn.connect()
        self.connected = True

    def disconnect_server(self, server_name: str) -> None:
        """断开与指定 Server 的连接"""
        if server_name in self.servers:
            self.servers[server_name].disconnect()
            del self.servers[server_name]
        if not self.servers:
            self.connected = False

    def list_all_tools(self) -> List[Dict[str, Any]]:
        """列出所有 Server 的工具"""
        all_tools = []
        for name, conn in self.servers.items():
            tools = conn.list_tools()
            for tool in tools:
                tool['_server'] = name
            all_tools.extend(tools)
        return all_tools

    def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用指定 Server 的工具"""
        if server_name not in self.servers:
            return {"error": f"Server not found: {server_name}"}
        return self.servers[server_name].call_tool(tool_name, arguments)

    def list_all_resources(self) -> List[Dict[str, Any]]:
        """列出所有 Server 的资源"""
        all_resources = []
        for name, conn in self.servers.items():
            resources = conn.list_resources()
            for res in resources:
                res['_server'] = name
            all_resources.extend(resources)
        return all_resources

    def read_resource(self, server_name: str, uri: str) -> Dict[str, Any]:
        """读取指定 Server 的资源"""
        if server_name not in self.servers:
            return {"error": f"Server not found: {server_name}"}
        return self.servers[server_name].read_resource(uri)

    def list_all_prompts(self) -> List[Dict[str, Any]]:
        """列出所有 Server 的 Prompts"""
        all_prompts = []
        for name, conn in self.servers.items():
            prompts = conn.list_prompts()
            for prompt in prompts:
                prompt['_server'] = name
            all_prompts.extend(prompts)
        return all_prompts

    def get_prompt(self, server_name: str, prompt_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """获取指定 Server 的 Prompt"""
        if server_name not in self.servers:
            return {"error": f"Server not found: {server_name}"}
        return self.servers[server_name].get_prompt(prompt_name, arguments)

    def get_capabilities(self) -> Dict[str, Any]:
        """获取所有 Server 的能力摘要"""
        caps = {}
        for name, conn in self.servers.items():
            caps[name] = {
                "tools": len(conn.tools),
                "resources": len(conn.resources),
                "prompts": len(conn.prompts),
            }
        return caps


class MCPServerConnection:
    """
    MCP Server 连接类
    
    管理与单个 MCP Server 的连接和交互。
    """
    
    def __init__(self, name: str, server_info: Dict[str, Any]):
        self.name = name
        self.server_info = server_info
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.resources: Dict[str, Dict[str, Any]] = {}
        self.prompts: Dict[str, Dict[str, Any]] = {}
        self.connected = False
        self._mock_data = self._init_mock_data()

    def _init_mock_data(self) -> Dict[str, Any]:
        """初始化模拟数据"""
        return {
            "weather-server": {
                "tools": {
                    "get_weather": {"description": "获取天气", "params": ["city"]},
                    "get_forecast": {"description": "获取预报", "params": ["city", "days"]},
                    "get_air_quality": {"description": "查询空气质量", "params": ["city"]},
                },
                "resources": {
                    "file:///docs/guide.md": {"name": "用户指南", "type": "text/markdown"},
                    "file:///data/weather.json": {"name": "天气数据", "type": "application/json"},
                },
                "prompts": {
                    "weather_report": {"description": "天气报告", "args": ["city", "days"]},
                    "code_review": {"description": "代码审查", "args": ["language"]},
                }
            },
            "db-server": {
                "tools": {
                    "query_users": {"description": "查询用户", "params": ["name"]},
                    "update_user": {"description": "更新用户", "params": ["id", "data"]},
                    "delete_user": {"description": "删除用户", "params": ["id"]},
                },
                "resources": {
                    "db:///schema/users": {"name": "用户表结构", "type": "application/json"},
                    "db:///schema/orders": {"name": "订单表结构", "type": "application/json"},
                },
                "prompts": {
                    "data_analysis": {"description": "数据分析", "args": ["data_type", "metrics"]},
                }
            },
            "file-server": {
                "tools": {
                    "read_file": {"description": "读取文件", "params": ["path"]},
                    "write_file": {"description": "写入文件", "params": ["path", "content"]},
                    "list_dir": {"description": "列出目录", "params": ["path"]},
                },
                "resources": {
                    "file:///config/app.json": {"name": "应用配置", "type": "application/json"},
                    "file:///logs/app.log": {"name": "应用日志", "type": "text/plain"},
                },
                "prompts": {
                    "file_summary": {"description": "文件摘要", "args": ["path"]},
                }
            }
        }

    def connect(self) -> None:
        """建立连接并发现能力"""
        self.connected = True
        # 模拟能力发现
        if self.name in self._mock_data:
            data = self._mock_data[self.name]
            self.tools = data["tools"]
            self.resources = data["resources"]
            self.prompts = data["prompts"]

    def disconnect(self) -> None:
        """断开连接"""
        self.connected = False
        self.tools = {}
        self.resources = {}
        self.prompts = {}

    def list_tools(self) -> List[Dict[str, Any]]:
        """获取工具列表"""
        return [
            {"name": name, "description": info["description"], "params": info["params"]}
            for name, info in self.tools.items()
        ]

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用工具"""
        if tool_name not in self.tools:
            return {"error": f"Tool not found: {tool_name}"}
        
        # 模拟工具执行结果
        if tool_name == "get_weather":
            return {"content": [{"type": "text", "text": f"{arguments.get('city', '北京')}: 晴, 25°C"}]}
        elif tool_name == "query_users":
            return {"content": [{"type": "text", "text": f"用户: {arguments.get('name', '张三')}"}]}
        elif tool_name == "read_file":
            return {"content": [{"type": "text", "text": f"文件内容: {arguments.get('path', '/path/to/file')}"}]}
        else:
            return {"content": [{"type": "text", "text": f"执行 {tool_name} 成功"}]}

    def list_resources(self) -> List[Dict[str, Any]]:
        """获取资源列表"""
        return [
            {"uri": uri, "name": info["name"], "type": info["type"]}
            for uri, info in self.resources.items()
        ]

    def read_resource(self, uri: str) -> Dict[str, Any]:
        """读取资源"""
        if uri not in self.resources:
            return {"error": f"Resource not found: {uri}"}
        return {
            "uri": uri,
            "mimeType": self.resources[uri]["type"],
            "text": f"内容: {self.resources[uri]['name']}"
        }

    def list_prompts(self) -> List[Dict[str, Any]]:
        """获取 Prompts 列表"""
        return [
            {"name": name, "description": info["description"], "args": info["args"]}
            for name, info in self.prompts.items()
        ]

    def get_prompt(self, prompt_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """获取 Prompt"""
        if prompt_name not in self.prompts:
            return {"error": f"Prompt not found: {prompt_name}"}
        
        template = f"Prompt: {prompt_name}"
        for key, value in arguments.items():
            template += f" ({key}: {value})"
        
        return {
            "description": self.prompts[prompt_name]["description"],
            "messages": [{"role": "user", "content": {"type": "text", "text": template}}]
        }


# ============================================================
# 模块：多 Server 编排器
# ============================================================

class MCPOrchestrator:
    """
    MCP 多 Server 编排器
    
    负责管理和编排多个 MCP Server，实现复杂的能力组合。
    """
    
    def __init__(self, client: MCPClient):
        self.client = client

    def find_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """在所有 Server 中查找工具"""
        for name, conn in self.client.servers.items():
            if tool_name in conn.tools:
                return {
                    "server": name,
                    "tool": conn.tools[tool_name],
                }
        return None

    def call_best_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """自动选择最佳 Server 并调用工具"""
        for name, conn in self.client.servers.items():
            if tool_name in conn.tools:
                return conn.call_tool(tool_name, arguments)
        return {"error": f"Tool not found in any server: {tool_name}"}

    def execute_workflow(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """执行工作流（多步骤工具调用）"""
        results = []
        context = {}
        
        for step in steps:
            server = step.get("server", "")
            tool = step.get("tool", "")
            args = step.get("arguments", {})
            
            # 支持从上下文中获取参数
            resolved_args = {}
            for key, value in args.items():
                if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
                    var_name = value[2:-2]
                    resolved_args[key] = context.get(var_name, value)
                else:
                    resolved_args[key] = value
            
            result = self.client.call_tool(server, tool, resolved_args)
            results.append({
                "step": step,
                "result": result,
            })
            
            # 将结果存入上下文
            context[f"result_{len(results)}"] = result
        
        return results


# ============================================================
# 模块：入口
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  MCP Client 集成与多 Server 编排演示")
    print("=" * 60)

    # 1. 创建 Client
    print("\n🔌 1. 创建 MCP Client")
    client = MCPClient(name="my-app", version="1.0.0")
    print(f"  客户端: {client.name} v{client.version}")

    # 2. 连接多个 Server
    print("\n📦 2. 连接多个 Server")
    client.connect_server("weather-server", {
        "name": "weather-server",
        "version": "1.0.0",
        "description": "天气服务"
    })
    client.connect_server("db-server", {
        "name": "db-server",
        "version": "1.0.0",
        "description": "数据库服务"
    })
    client.connect_server("file-server", {
        "name": "file-server",
        "version": "1.0.0",
        "description": "文件服务"
    })
    print(f"  已连接 Server: {list(client.servers.keys())}")

    # 3. 获取能力摘要
    print("\n📋 3. 能力摘要")
    caps = client.get_capabilities()
    for server, cap in caps.items():
        print(f"  {server}: {cap['tools']} 工具, {cap['resources']} 资源, {cap['prompts']} Prompts")

    # 4. 列出所有工具
    print("\n🔧 4. 所有 Server 的工具")
    tools = client.list_all_tools()
    for tool in tools:
        print(f"  • [{tool['_server']}] {tool['name']}: {tool['description']}")

    # 5. 调用工具
    print("\n🎯 5. 工具调用")
    result = client.call_tool("weather-server", "get_weather", {"city": "北京"})
    print(f"  weather-server/get_weather(北京): {result['content'][0]['text']}")

    result = client.call_tool("db-server", "query_users", {"name": "张三"})
    print(f"  db-server/query_users(张三): {result['content'][0]['text']}")

    # 6. 列出所有资源
    print("\n📄 6. 所有 Server 的资源")
    resources = client.list_all_resources()
    for res in resources:
        print(f"  • [{res['_server']}] {res['name']}: {res['uri']}")

    # 7. 编排器演示
    print("\n🎛️  7. 多 Server 编排")
    orchestrator = MCPOrchestrator(client)

    # 查找工具
    tool_info = orchestrator.find_tool("get_weather")
    print(f"  查找 get_weather: 在 {tool_info['server']} 中找到")

    # 执行工作流
    workflow = [
        {
            "server": "weather-server",
            "tool": "get_weather",
            "arguments": {"city": "北京"}
        },
        {
            "server": "file-server",
            "tool": "write_file",
            "arguments": {"path": "/reports/weather.txt", "content": "{{result_1}}"}
        },
    ]
    results = orchestrator.execute_workflow(workflow)
    print(f"  工作流执行: {len(results)} 步")
    for i, r in enumerate(results):
        print(f"    步骤 {i+1}: {r['step']['tool']} → 成功")

    # 8. 断开连接
    print("\n🔌 8. 断开连接")
    for name in list(client.servers.keys()):
        client.disconnect_server(name)
        print(f"  断开: {name}")
    print(f"  连接状态: {client.connected}")

    print("\n" + "=" * 60)
    print("  演示完成")
    print("=" * 60)
