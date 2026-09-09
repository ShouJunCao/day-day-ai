"""
function_calling.py — Function Calling 原理与完整流程实现
"""
import os
import re
import json
from typing import Optional, List, Dict, Callable
from dataclasses import dataclass, field


# ============================================================
# 模块：数据结构
# ============================================================

@dataclass
class ToolDefinition:
    """工具定义"""
    name: str
    description: str
    parameters: dict


@dataclass
class ToolCall:
    """工具调用"""
    tool_name: str
    arguments: dict
    result: str = ""


@dataclass
class Message:
    """消息"""
    role: str  # "user", "assistant", "tool", "system"
    content: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    tool_call_id: str = ""


@dataclass
class FunctionCallingResult:
    """Function Calling 结果"""
    messages: List[Message]
    final_answer: str
    tool_calls_made: List[ToolCall]


# ============================================================
# 模块：工具注册表
# ============================================================

class ToolRegistry:
    """
    工具注册表：管理可用工具的定义和实现。
    """

    def __init__(self):
        self.definitions: List[ToolDefinition] = []
        self.implementations: Dict[str, Callable] = {}

    def register(self, name: str, description: str, parameters: dict, func: Callable):
        """注册一个工具"""
        self.definitions.append(ToolDefinition(
            name=name,
            description=description,
            parameters=parameters,
        ))
        self.implementations[name] = func

    def get_definitions(self) -> List[dict]:
        """获取所有工具定义（用于发送给 LLM）"""
        return [
            {
                "type": "function",
                "function": {
                    "name": d.name,
                    "description": d.description,
                    "parameters": d.parameters,
                }
            }
            for d in self.definitions
        ]

    def execute(self, tool_name: str, arguments: dict) -> str:
        """执行工具调用"""
        if tool_name not in self.implementations:
            return f"错误: 未知工具 '{tool_name}'"
        try:
            result = self.implementations[tool_name](**arguments)
            return str(result)
        except Exception as e:
            return f"错误: {str(e)}"


# ============================================================
# 模块：Function Calling 引擎
# ============================================================

class FunctionCallingEngine:
    """
    Function Calling 引擎：处理完整的 Function Calling 流程。

    流程：
    1. 用户发送查询
    2. LLM 判断是否需要调用工具
    3. 如果需要，返回工具调用请求
    4. 执行工具调用
    5. 将工具结果返回给 LLM
    6. LLM 生成最终回答
    """

    def __init__(self, registry: ToolRegistry, llm_fn=None):
        self.registry = registry
        self.llm_fn = llm_fn
        self.max_tool_calls = 5

    def execute(self, user_query: str) -> FunctionCallingResult:
        """执行完整的 Function Calling 流程"""
        messages = [Message(role="system", content="你是一个有帮助的助手。")]
        messages.append(Message(role="user", content=user_query))
        tool_calls_made = []

        for _ in range(self.max_tool_calls):
            # 1. 调用 LLM
            response = self._call_llm(messages)

            # 2. 判断是否有工具调用
            if response.get("tool_calls"):
                for tc in response["tool_calls"]:
                    tool_call = ToolCall(
                        tool_name=tc["function"]["name"],
                        arguments=json.loads(tc["function"]["arguments"]),
                    )

                    # 3. 执行工具
                    result = self.registry.execute(
                        tool_call.tool_name,
                        tool_call.arguments,
                    )
                    tool_call.result = result
                    tool_calls_made.append(tool_call)

                    # 4. 添加工具结果到消息
                    messages.append(Message(
                        role="tool",
                        content=result,
                        tool_call_id=tc["id"],
                    ))
            else:
                # 5. LLM 生成最终回答
                final_answer = response.get("content", "")
                return FunctionCallingResult(
                    messages=messages,
                    final_answer=final_answer,
                    tool_calls_made=tool_calls_made,
                )

        # 达到最大工具调用次数
        return FunctionCallingResult(
            messages=messages,
            final_answer="达到最大工具调用次数限制。",
            tool_calls_made=tool_calls_made,
        )

    def _call_llm(self, messages: List[Message]) -> dict:
        """调用 LLM（模拟实现）"""
        if self.llm_fn:
            return self.llm_fn(messages, self.registry.get_definitions())
        return self._mock_llm(messages)

    def _mock_llm(self, messages: List[Message]) -> dict:
        """模拟 LLM 响应"""
        last_msg = messages[-1].content.lower()
        if "天气" in last_msg:
            return {
                "tool_calls": [{
                    "id": "tc_1",
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "arguments": '{"city": "北京"}',
                    },
                }],
            }
        elif "搜索" in last_msg or "查询" in last_msg:
            return {
                "tool_calls": [{
                    "id": "tc_1",
                    "type": "function",
                    "function": {
                        "name": "search_knowledge",
                        "arguments": '{"query": "Function Calling"}',
                    },
                }],
            }
        return {"content": f"好的，我理解你的问题：{messages[-1].content}"}


# ============================================================
# 模块：示例工具实现
# ============================================================

def get_weather(city: str) -> str:
    """获取天气信息"""
    weather_data = {
        "北京": "晴，25°C，风力 2 级",
        "上海": "多云，28°C，风力 3 级",
        "广州": "雷阵雨，32°C，风力 1 级",
    }
    return weather_data.get(city, f"未知城市: {city}")


def search_knowledge(query: str) -> str:
    """搜索知识库"""
    return f"搜索结果: 关于'{query}'的相关文档有 3 篇。"


def calculate(expression: str) -> str:
    """计算数学表达式"""
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return f"计算结果: {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"


# ============================================================
# 模块：入口
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  Function Calling 完整流程演示")
    print("=" * 60)

    # 1. 注册工具
    registry = ToolRegistry()
    registry.register(
        name="get_weather",
        description="获取指定城市的天气信息",
        parameters={
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称"},
            },
            "required": ["city"],
        },
        func=get_weather,
    )
    registry.register(
        name="search_knowledge",
        description="搜索内部知识库",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"},
            },
            "required": ["query"],
        },
        func=search_knowledge,
    )

    # 2. 创建引擎
    engine = FunctionCallingEngine(registry)

    # 3. 执行查询
    queries = [
        "北京今天天气怎么样？",
        "帮我搜索一下 Function Calling 的相关资料",
        "你好",
    ]

    for q in queries:
        print(f"\n{'=' * 50}")
        print(f"用户: {q}")
        result = engine.execute(q)
        if result.tool_calls_made:
            print("工具调用:")
            for tc in result.tool_calls_made:
                print(f"  → {tc.tool_name}({tc.arguments}) = {tc.result}")
        print(f"助手: {result.final_answer}")
