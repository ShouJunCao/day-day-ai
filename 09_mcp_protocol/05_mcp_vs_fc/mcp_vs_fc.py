"""
mcp_vs_fc.py — MCP 与 Function Calling 的关系与差异
演示 MCP 工具如何适配 Function Calling 格式。
"""
import os
import json
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field


# ============================================================
# 模块：数据结构
# ============================================================

@dataclass
class MCPTool:
    """MCP 工具定义"""
    name: str
    description: str
    input_schema: Dict[str, Any]

    def to_fc_format(self) -> Dict[str, Any]:
        """转换为 Function Calling 格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema,
            }
        }


@dataclass
class FCMessage:
    """Function Calling 消息"""
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None


# ============================================================
# 模块：MCP 到 FC 适配器
# ============================================================

class MCPToFCAdapter:
    """
    MCP 到 Function Calling 适配器
    
    将 MCP 工具转换为 LLM 所需的 Function Calling 格式，
    并处理工具调用的执行和结果返回。
    """
    
    def __init__(self):
        self.tools: List[MCPTool] = []
        self._handlers: Dict[str, Callable] = {}

    def register_tool(self, tool: MCPTool, handler: callable):
        """注册 MCP 工具及其处理函数"""
        self.tools.append(tool)
        self._handlers[tool.name] = handler

    def get_fc_tools(self) -> List[Dict[str, Any]]:
        """获取所有工具的 FC 格式"""
        return [tool.to_fc_format() for tool in self.tools]

    def execute_tool_call(self, tool_call: Dict[str, Any]) -> FCMessage:
        """执行工具调用并返回 FC 消息格式"""
        function = tool_call.get("function", {})
        name = function.get("name")
        args_str = function.get("arguments", "{}")
        arguments = json.loads(args_str)
        
        if name in self._handlers:
            try:
                result = self._handlers[name](**arguments)
                return FCMessage(
                    role="tool",
                    name=name,
                    tool_call_id=tool_call.get("id"),
                    content=str(result)
                )
            except Exception as e:
                return FCMessage(
                    role="tool",
                    name=name,
                    tool_call_id=tool_call.get("id"),
                    content=f"Error: {str(e)}"
                )
        else:
            return FCMessage(
                role="tool",
                name=name,
                tool_call_id=tool_call.get("id"),
                content=f"Error: Tool {name} not found"
            )


# ============================================================
# 模块：示例工具实现
# ============================================================

def get_weather(city: str) -> str:
    """获取天气"""
    weather_data = {
        "北京": "晴, 25°C, 湿度 45%",
        "上海": "多云, 28°C, 湿度 65%",
        "广州": "雷阵雨, 32°C, 湿度 85%",
    }
    return weather_data.get(city, "未知城市")

def search_database(query: str) -> str:
    """搜索数据库"""
    return f"搜索结果: 找到 10 条关于 '{query}' 的记录"

def read_file(path: str) -> str:
    """读取文件"""
    return f"文件 {path} 内容: # 示例文档..."


# ============================================================
# 模块：入口
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  MCP 与 Function Calling 关系演示")
    print("=" * 60)

    # 1. 创建适配器
    adapter = MCPToFCAdapter()

    # 2. 注册 MCP 工具
    print("\n 1. 注册 MCP 工具")
    weather_tool = MCPTool(
        name="get_weather",
        description="获取指定城市天气",
        input_schema={
            "type": "object",
            "properties": {"city": {"type": "string", "description": "城市名称"}},
            "required": ["city"]
        }
    )
    adapter.register_tool(weather_tool, get_weather)
    print(f"  已注册: {weather_tool.name}")

    db_tool = MCPTool(
        name="search_db",
        description="搜索数据库",
        input_schema={
            "type": "object",
            "properties": {"query": {"type": "string", "description": "查询关键词"}},
            "required": ["query"]
        }
    )
    adapter.register_tool(db_tool, search_database)
    print(f"  已注册: {db_tool.name}")

    # 3. 转换为 FC 格式
    print("\n🔄 2. 转换为 Function Calling 格式")
    fc_tools = adapter.get_fc_tools()
    print(f"  工具数量: {len(fc_tools)}")
    for tool in fc_tools:
        print(f"  • {tool['function']['name']}: {tool['function']['description']}")

    # 4. 模拟 FC 调用
    print("\n📞 3. 模拟 Function Calling 调用")
    # 模拟 LLM 返回的工具调用请求
    mock_tool_call = {
        "id": "call_123",
        "type": "function",
        "function": {
            "name": "get_weather",
            "arguments": '{"city": "北京"}'
        }
    }
    
    # 适配器执行调用
    result_msg = adapter.execute_tool_call(mock_tool_call)
    print(f"  调用: {mock_tool_call['function']['name']}({mock_tool_call['function']['arguments']})")
    print(f"  结果角色: {result_msg.role}")
    print(f"  结果内容: {result_msg.content}")

    # 5. 对比总结
    print("\n" + "=" * 60)
    print("  MCP vs Function Calling 总结")
    print("=" * 60)
    print("  MCP: 协议层，负责工具发现、连接管理、数据传输")
    print("  FC: 能力层，负责工具选择、参数生成、结果整合")
    print("  关系: MCP 是 FC 的基础设施，FC 是 MCP 的使用方式")
