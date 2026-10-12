"""
react_framework.py — ReAct 框架深度解析与实现
演示 ReAct 框架的高级特性：多工具编排、错误恢复、上下文管理。
"""
import os
import re
import json
import time
import random
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from openai import OpenAI

# 阿里云 DashScope 配置
DASHSCOPE_API_KEY = os.getenv("API_KEY", "sk-492...81ff")
DASHSCOPE_BASE_URL = os.getenv("BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
DASHSCOPE_MODEL = os.getenv("MODEL_NAME", "qwen3.7-max")

client = OpenAI(
    api_key=DASHSCOPE_API_KEY,
    base_url=DASHSCOPE_BASE_URL,
)

# ============================================================
# 模块：高级工具定义
# ============================================================

@dataclass
class AdvancedTool:
    """高级工具定义，支持错误重试和超时"""
    name: str
    description: str
    func: Callable
    input_schema: Dict[str, str] = field(default_factory=dict)
    max_retries: int = 3
    timeout: float = 10.0
    error_handler: Optional[Callable] = None

class AdvancedToolRegistry:
    """高级工具注册表，支持错误恢复"""
    def __init__(self):
        self.tools: Dict[str, AdvancedTool] = {}

    def register(self, tool: AdvancedTool):
        self.tools[tool.name] = tool

    def execute_with_retry(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """带重试机制的工具执行"""
        tool = self.tools.get(name)
        if not tool:
            return {"error": f"Unknown tool: {name}"}
        
        for attempt in range(tool.max_retries):
            try:
                result = tool.func(**arguments)
                return {"success": True, "data": result, "attempt": attempt + 1}
            except Exception as e:
                if tool.error_handler:
                    recovery = tool.error_handler(e, attempt)
                    if recovery:
                        arguments = recovery
                if attempt == tool.max_retries - 1:
                    return {
                        "success": False,
                        "error": str(e),
                        "attempts": attempt + 1
                    }
        return {"success": False, "error": "Unknown error"}

    def get_tools_description(self) -> str:
        """生成 LLM 可读的工具描述"""
        lines = []
        for name, tool in self.tools.items():
            schema_str = ", ".join(
                f"{k}: {v}" for k, v in tool.input_schema.items()
            )
            lines.append(f"- {name}: {tool.description} ({schema_str})")
        return "\n".join(lines)

# ============================================================
# 模块：上下文管理器
# ============================================================

class AgentContext:
    """
    Agent 上下文管理器
    
    管理对话历史、工具调用记录和中间状态。
    支持上下文窗口限制和摘要压缩。
    """
    
    MAX_CONTEXT_TOKENS = 4000
    
    def __init__(self):
        self.history: List[Dict[str, str]] = []
        self.tool_calls: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}

    def add_thought(self, thought: str):
        self.history.append({"role": "thought", "content": thought})

    def add_action(self, action: str, input_data: str):
        self.history.append({"role": "action", "action": action, "input": input_data})

    def add_observation(self, observation: str):
        self.history.append({"role": "observation", "content": observation})

    def add_final_answer(self, answer: str):
        self.history.append({"role": "final_answer", "content": answer})

    def get_context_summary(self) -> str:
        """获取上下文摘要"""
        summary_parts = []
        for entry in self.history[-10:]:  # 只保留最近 10 条
            if entry["role"] == "thought":
                summary_parts.append(f"[思考] {entry['content']}")
            elif entry["role"] == "action":
                summary_parts.append(f"[行动] {entry['action']}: {entry['input']}")
            elif entry["role"] == "observation":
                summary_parts.append(f"[观察] {entry['content'][:100]}")
            elif entry["role"] == "final_answer":
                summary_parts.append(f"[答案] {entry['content']}")
        return "\n".join(summary_parts)

    def to_prompt(self, system_prompt: str, question: str) -> str:
        """构建完整的 Prompt"""
        context = self.get_context_summary()
        if context:
            return f"{system_prompt}\n\nQuestion: {question}\n\nContext:\n{context}\n"
        return f"{system_prompt}\n\nQuestion: {question}\n"

# ============================================================
# 模块：高级 ReAct Agent
# ============================================================

class AdvancedReActAgent:
    """
    高级 ReAct Agent
    
    特性：
    1. 多工具编排：支持复杂的多步骤工具调用
    2. 错误恢复：工具调用失败时自动重试
    3. 上下文管理：维护对话历史和中间状态
    4. 安全限制：最大迭代次数和超时控制
    """
    
    SYSTEM_PROMPT = """你是一个高级 AI Agent，使用 ReAct 模式解决问题。
你可以使用以下工具：
{tools}

回答格式必须严格遵守（关键字必须用英文）：
Thought: <你的思考过程>
Action: <工具名称>
Action Input: <JSON 参数>
Observation: <系统自动填充>

重复循环直到完成。完成后输出：
Final Answer: <最终答案>

如果不需要工具，直接输出：
Final Answer: <最终答案>"""

    def __init__(self, registry: AdvancedToolRegistry, max_iterations: int = 8):
        self.registry = registry
        self.max_iterations = max_iterations
        self.context = AgentContext()

    def _call_llm(self, prompt: str) -> str:
        try:
            response = client.chat.completions.create(
                model=DASHSCOPE_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"LLM Error: {e}"

    def _parse_response(self, response: str) -> Dict[str, str]:
        thought = re.search(r"Thought:\s*(.*)", response)
        action = re.search(r"Action:\s*(.*)", response)
        action_input = re.search(r"Action Input:\s*(.*)", response)
        final = re.search(r"Final Answer:\s*(.*)", response, re.DOTALL)
        
        def _safe_group(match, idx=1):
            val = match.group(idx) if match else None
            return val.strip() if val else ""
        
        return {
            "thought": _safe_group(thought),
            "action": _safe_group(action),
            "action_input": _safe_group(action_input) or "{}",
            "final_answer": _safe_group(final),
        }

    def run(self, query: str) -> Dict[str, Any]:
        tools_desc = self.registry.get_tools_description()
        prompt = self.SYSTEM_PROMPT.format(tools=tools_desc) + f"\n\nQuestion: {query}\n"
        
        print(f"🤖 高级 Agent 启动: {query}")
        
        for i in range(self.max_iterations):
            response = self._call_llm(prompt)
            parsed = self._parse_response(response)
            
            if parsed["thought"]:
                print(f"\n💭 Thought: {parsed['thought']}")
                self.context.add_thought(parsed["thought"])
            
            if parsed["final_answer"]:
                print(f"✅ Final Answer: {parsed['final_answer']}")
                self.context.add_final_answer(parsed["final_answer"])
                return {
                    "success": True,
                    "answer": parsed["final_answer"],
                    "iterations": i + 1,
                    "context": self.context.history,
                }
            
            if parsed["action"]:
                action_input = parsed.get("action_input", "{}")
                print(f"🔧 Action: {parsed['action']}")
                print(f"📥 Input: {action_input}")
                self.context.add_action(parsed["action"], action_input)
                
                try:
                    args = json.loads(action_input)
                except json.JSONDecodeError:
                    args = {}
                
                result = self.registry.execute_with_retry(parsed["action"], args)
                obs_text = str(result.get("data", result.get("error", "No result")))
                print(f"👁️ Observation: {obs_text[:100]}")
                self.context.add_observation(obs_text)
                
                prompt = self.context.to_prompt(
                    self.SYSTEM_PROMPT.format(tools=tools_desc),
                    query
                ) + f"\nObservation: {obs_text}\n"
        
        return {
            "success": False,
            "error": "Max iterations reached",
            "context": self.context.history,
        }

# ============================================================
# 模块：示例工具
# ============================================================

def search_database(query: str) -> str:
    """模拟数据库搜索"""
    data = {
        "用户信息": "Alice (admin), Bob (editor), Charlie (viewer)",
        "订单数据": "订单 #001: ¥299, 订单 #002: ¥599, 订单 #003: ¥129",
        "产品列表": "产品 A (库存: 50), 产品 B (库存: 30), 产品 C (库存: 0)",
    }
    for key, value in data.items():
        if query.lower() in key.lower():
            return value
    return "未找到相关数据"

def calculate(expression: str) -> str:
    """安全计算"""
    if re.match(r'^[\d\s\+\-\*\/\(\)\.]+$', expression):
        return str(eval(expression))
    return "Error: Invalid expression"

def send_notification(message: str, channel: str = "email") -> str:
    """发送通知"""
    return f"通知已发送到 {channel}: {message[:50]}..."

# ============================================================
# 模块：入口
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  高级 ReAct 框架演示")
    print("=" * 60)

    registry = AdvancedToolRegistry()
    registry.register(AdvancedTool(
        name="search_database",
        description="搜索数据库获取信息",
        func=search_database,
        input_schema={"query": "搜索关键词"},
        max_retries=2,
    ))
    registry.register(AdvancedTool(
        name="calculate",
        description="计算数学表达式",
        func=calculate,
        input_schema={"expression": "数学表达式"},
        max_retries=1,
    ))
    registry.register(AdvancedTool(
        name="send_notification",
        description="发送通知消息",
        func=send_notification,
        input_schema={"message": "消息内容", "channel": "发送渠道"},
        max_retries=3,
    ))

    agent = AdvancedReActAgent(registry)
    
    print("\n📌 测试: 多步骤任务")
    result = agent.run(
        "请查询产品列表，计算产品 A 和 B 的总库存，然后通过邮件发送报告"
    )
    print(f"\n结果: {result.get('answer', '未完成')}")
    print(f"迭代次数: {result.get('iterations', 0)}")

    print("\n" + "=" * 60)
    print("  演示完成")
    print("=" * 60)
