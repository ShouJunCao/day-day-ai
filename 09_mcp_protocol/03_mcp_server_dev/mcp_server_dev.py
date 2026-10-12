"""
mcp_server_dev.py — MCP Server 开发（Python SDK）
演示如何使用 MCP Python SDK 开发 MCP 服务器。
"""
import os
import json
import time
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum


# ============================================================
# 模块：MCP Server SDK 核心类
# ============================================================

class MCPServer:
    """
    MCP Server SDK 核心类
    
    提供 MCP 服务器的基础框架，包括：
    1. 工具注册和暴露
    2. 资源注册和暴露
    3. Prompt 注册和暴露
    4. 请求处理和路由
    5. 生命周期管理
    """
    
    def __init__(self, name: str, version: str, description: str = ""):
        self.name = name
        self.version = version
        self.description = description
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.resources: Dict[str, Dict[str, Any]] = {}
        self.prompts: Dict[str, Dict[str, Any]] = {}
        self.initialized = False
        self._tool_handlers: Dict[str, callable] = {}
        self._resource_handlers: Dict[str, callable] = {}
        self._prompt_handlers: Dict[str, callable] = {}

    def tool(self, name: str = None, description: str = ""):
        """
        工具注册装饰器
        
        使用方式：
        @server.tool(description="获取天气")
        def get_weather(city: str) -> str:
            return f"{city} 天气：晴"
        """
        def decorator(func):
            tool_name = name or func.__name__
            # 解析函数参数
            import inspect
            sig = inspect.signature(func)
            properties = {}
            required = []
            
            for param_name, param in sig.parameters.items():
                param_type = "string"
                if param.annotation == int:
                    param_type = "integer"
                elif param.annotation == float:
                    param_type = "number"
                elif param.annotation == bool:
                    param_type = "boolean"
                
                properties[param_name] = {
                    "type": param_type,
                    "description": f"参数 {param_name}"
                }
                
                if param.default == inspect.Parameter.empty:
                    required.append(param_name)
            
            self.tools[tool_name] = {
                "name": tool_name,
                "description": description,
                "inputSchema": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
            self._tool_handlers[tool_name] = func
            return func
        return decorator

    def resource(self, uri: str, name: str = "", description: str = "", mime_type: str = "text/plain"):
        """
        资源注册装饰器
        
        使用方式：
        @server.resource(uri="file:///docs/guide.md", name="用户指南")
        async def read_guide() -> str:
            return "# 用户指南\n欢迎使用..."
        """
        def decorator(func):
            self.resources[uri] = {
                "uri": uri,
                "name": name or uri.split("/")[-1],
                "description": description,
                "mimeType": mime_type
            }
            self._resource_handlers[uri] = func
            return func
        return decorator

    def prompt(self, name: str = None, description: str = ""):
        """
        Prompt 注册装饰器
        
        使用方式：
        @server.prompt(description="代码审查")
        def code_review(language: str) -> str:
            return f"请审查以下{language}代码"
        """
        def decorator(func):
            prompt_name = name or func.__name__
            # 解析参数
            import inspect
            sig = inspect.signature(func)
            arguments = []
            
            for param_name, param in sig.parameters.items():
                arguments.append({
                    "name": param_name,
                    "description": f"参数 {param_name}",
                    "required": param.default == inspect.Parameter.empty
                })
            
            self.prompts[prompt_name] = {
                "name": prompt_name,
                "description": description,
                "arguments": arguments
            }
            self._prompt_handlers[prompt_name] = func
            return func
        return decorator

    def get_capabilities(self) -> Dict[str, Any]:
        """获取服务器能力"""
        return {
            "tools": {"listChanged": True},
            "resources": {"listChanged": True, "subscribe": True},
            "prompts": {"listChanged": True}
        }

    def get_server_info(self) -> Dict[str, str]:
        """获取服务器信息"""
        return {
            "name": self.name,
            "version": self.version
        }

    def handle_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理 MCP 请求"""
        if method == "initialize":
            return {
                "protocolVersion": "2024-11-05",
                "capabilities": self.get_capabilities(),
                "serverInfo": self.get_server_info()
            }
        elif method == "tools/list":
            return {"tools": list(self.tools.values())}
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            if tool_name in self._tool_handlers:
                result = self._tool_handlers[tool_name](**arguments)
                return {
                    "content": [{"type": "text", "text": str(result)}],
                    "isError": False
                }
            return {"error": f"Tool not found: {tool_name}"}
        elif method == "resources/list":
            return {"resources": list(self.resources.values())}
        elif method == "resources/read":
            uri = params.get("uri")
            if uri in self._resource_handlers:
                content = self._resource_handlers[uri]()
                return {
                    "contents": [{
                        "uri": uri,
                        "mimeType": self.resources[uri].get("mimeType", "text/plain"),
                        "text": content
                    }]
                }
            return {"error": f"Resource not found: {uri}"}
        elif method == "prompts/list":
            return {"prompts": list(self.prompts.values())}
        elif method == "prompts/get":
            prompt_name = params.get("name")
            prompt_args = params.get("arguments", {})
            if prompt_name in self._prompt_handlers:
                content = self._prompt_handlers[prompt_name](**prompt_args)
                return {
                    "description": self.prompts[prompt_name].get("description", ""),
                    "messages": [{"role": "user", "content": {"type": "text", "text": content}}]
                }
            return {"error": f"Prompt not found: {prompt_name}"}
        else:
            return {"error": f"Method not found: {method}"}


# ============================================================
# 模块：示例 Server 实现
# ============================================================

# 创建 MCP Server 实例
server = MCPServer(
    name="weather-server",
    version="1.0.0",
    description="天气数据服务"
)

# 注册工具
@server.tool(description="获取指定城市天气")
def get_weather(city: str) -> str:
    """获取指定城市天气"""
    weather_data = {
        "北京": "晴, 25°C, 湿度 45%",
        "上海": "多云, 28°C, 湿度 65%",
        "广州": "雷阵雨, 32°C, 湿度 85%",
        "深圳": "晴, 30°C, 湿度 70%",
        "杭州": "小雨, 22°C, 湿度 80%"
    }
    return weather_data.get(city, f"未知城市：{city}")

@server.tool(description="获取城市天气预报")
def get_forecast(city: str, days: int = 3) -> str:
    """获取城市天气预报"""
    forecast_data = {
        "北京": ["晴", "多云", "晴", "阴", "小雨"],
        "上海": ["多云", "晴", "晴", "多云", "晴"],
        "广州": ["雷阵雨", "晴", "多云", "晴", "晴"],
    }
    forecasts = forecast_data.get(city, ["未知", "未知", "未知"])
    return json.dumps({
        "city": city,
        "days": days,
        "forecast": forecasts[:days]
    }, ensure_ascii=False)

@server.tool(description="查询空气质量")
def get_air_quality(city: str) -> str:
    """查询空气质量"""
    aqi_data = {
        "北京": {"aqi": 85, "level": "良", "pm25": 35},
        "上海": {"aqi": 65, "level": "良", "pm25": 25},
        "广州": {"aqi": 55, "level": "良", "pm25": 20},
    }
    data = aqi_data.get(city, {"aqi": 0, "level": "未知", "pm25": 0})
    return json.dumps({"city": city, **data}, ensure_ascii=False)

# 注册资源
@server.resource(uri="file:///docs/guide.md", name="用户指南", description="MCP 用户使用指南", mime_type="text/markdown")
def read_guide() -> str:
    """读取用户指南"""
    return """# MCP 用户指南

欢迎使用 MCP 协议！

## 快速开始

1. 安装 MCP SDK
2. 创建 Server 实例
3. 注册工具和资源
4. 启动服务

## 工具列表

- get_weather: 获取天气
- get_forecast: 获取预报
- get_air_quality: 查询空气质量

## 资源列表

- file:///docs/guide.md: 用户指南
- file:///data/weather.json: 天气数据
"""

@server.resource(uri="file:///data/weather.json", name="天气数据", description="城市天气数据", mime_type="application/json")
def read_weather_data() -> str:
    """读取天气数据"""
    data = {
        "cities": ["北京", "上海", "广州", "深圳", "杭州"],
        "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source": "中国气象局"
    }
    return json.dumps(data, ensure_ascii=False)

# 注册 Prompt
@server.prompt(description="生成天气报告")
def weather_report(city: str, days: int = 3) -> str:
    """生成天气报告 Prompt"""
    return f"""请生成{city}的天气报告，包括以下内容：

1. 当前天气状况
2. 未来{days}天天气预报
3. 空气质量指数
4. 出行建议

请使用友好的语气，提供实用的建议。"""

@server.prompt(description="代码审查")
def code_review(language: str = "Python", focus: str = "代码质量") -> str:
    """代码审查 Prompt"""
    return f"""请审查以下{language}代码，重点关注{focus}：

审查要点：
1. 代码规范和风格
2. 潜在的错误和 bug
3. 性能优化建议
4. 安全性和最佳实践

请提供具体的改进建议。"""

@server.prompt(description="数据分析")
def data_analysis(data_type: str = "销售数据", metrics: str = "趋势分析") -> str:
    """数据分析 Prompt"""
    return f"""请对{data_type}进行{metrics}：

分析要求：
1. 数据概览和统计
2. 关键指标分析
3. 趋势和模式识别
4. 洞察和建议

请使用图表和表格展示分析结果。"""


# ============================================================
# 模块：入口
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  MCP Server 开发演示（Python SDK）")
    print("=" * 60)

    # 1. 查看 Server 信息
    print(f"\n📦 Server 信息:")
    print(f"  名称: {server.name}")
    print(f"  版本: {server.version}")
    print(f"  描述: {server.description}")

    # 2. 查看注册的工具
    print(f"\n 注册的工具 ({len(server.tools)} 个):")
    for tool_name, tool_info in server.tools.items():
        print(f"  • {tool_name}: {tool_info['description']}")
        params = tool_info['inputSchema'].get('properties', {})
        if params:
            param_list = ", ".join(params.keys())
            print(f"    参数: {param_list}")

    # 3. 查看注册的资源
    print(f"\n📄 注册的资源 ({len(server.resources)} 个):")
    for uri, res_info in server.resources.items():
        print(f"  • {res_info['name']}: {res_info['description']}")
        print(f"    URI: {uri}")

    # 4. 查看注册的 Prompts
    print(f"\n 注册的 Prompts ({len(server.prompts)} 个):")
    for prompt_name, prompt_info in server.prompts.items():
        print(f"  • {prompt_name}: {prompt_info['description']}")
        args = prompt_info.get('arguments', [])
        if args:
            arg_list = ", ".join([a['name'] for a in args])
            print(f"    参数: {arg_list}")

    # 5. 模拟请求处理
    print(f"\n🔄 模拟请求处理:")
    
    # 获取能力
    caps = server.handle_request("initialize", {})
    print(f"  初始化响应: {caps['serverInfo']['name']} v{caps['serverInfo']['version']}")
    
    # 获取工具列表
    tools_list = server.handle_request("tools/list", {})
    print(f"  工具数量: {len(tools_list['tools'])}")
    
    # 调用工具
    weather_result = server.handle_request("tools/call", {
        "name": "get_weather",
        "arguments": {"city": "北京"}
    })
    print(f"  get_weather(北京): {weather_result['content'][0]['text']}")
    
    forecast_result = server.handle_request("tools/call", {
        "name": "get_forecast",
        "arguments": {"city": "上海", "days": 3}
    })
    print(f"  get_forecast(上海, 3): {forecast_result['content'][0]['text'][:50]}...")
    
    # 读取资源
    guide_result = server.handle_request("resources/read", {
        "uri": "file:///docs/guide.md"
    })
    print(f"  资源读取: {len(guide_result['contents'][0]['text'])} 字符")
    
    # 获取 Prompt
    prompt_result = server.handle_request("prompts/get", {
        "name": "weather_report",
        "arguments": {"city": "广州", "days": 5}
    })
    print(f"  Prompt 获取: {prompt_result['messages'][0]['content']['text'][:50]}...")

    # 6. 获取 Server 能力
    print(f"\n📋 Server 能力:")
    capabilities = server.get_capabilities()
    print(f"  工具: {capabilities['tools']}")
    print(f"  资源: {capabilities['resources']}")
    print(f"  Prompts: {capabilities['prompts']}")

    print(f"\n" + "=" * 60)
    print("  MCP Server 开发演示完成")
    print("=" * 60)
