"""
agent_react.py — AI Agent 架构概述与 ReAct 模式实现
演示 ReAct (Reasoning + Acting) 模式的核心循环：思考 -> 行动 -> 观察 -> 循环。
"""
import os
import re
import json
import time
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
# 模块：工具定义
# ============================================================

@dataclass
class AgentTool:
    """Agent 工具定义"""
    name: str
    description: str
    func: Callable
    input_schema: Dict[str, str] = field(default_factory=dict)

class ToolRegistry:
    """工具注册表"""
    def __init__(self):
        self.tools: Dict[str, AgentTool] = {}

    def register(self, tool: AgentTool):
        self.tools[tool.name] = tool

    def get_tools_description(self) -> List[Dict[str, Any]]:
        return [
            {"name": t.name, "description": t.description, "schema": t.input_schema}
            for t in self.tools.values()
        ]

    def execute(self, name: str, arguments: Dict[str, Any]) -> Any:
        if name not in self.tools:
            return {"error": f"Unknown tool: {name}"}
        return self.tools[name].func(**arguments)

# ============================================================
# 模块：ReAct Agent 核心
# ============================================================

class ReActAgent:
    """
    ReAct Agent 实现
    
    循环执行：思考 (Thought) -> 行动 (Action) -> 观察 (Observation)
    直到得出最终答案 (Final Answer) 或达到最大迭代次数。
    """
    
    SYSTEM_PROMPT = """你是一个 AI Agent，使用 ReAct 模式解决问题。
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

    def __init__(self, registry: ToolRegistry, max_iterations: int = 5):
        self.registry = registry
        self.max_iterations = max_iterations
        self.trace: List[Dict[str, str]] = []

    def _call_llm(self, prompt: str) -> str:
        """调用 LLM 生成响应"""
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
        """解析 LLM 响应"""
        thought_match = re.search(r"Thought:\s*(.*)", response)
        action_match = re.search(r"Action:\s*(.*)", response)
        input_match = re.search(r"Action Input:\s*(.*)", response)
        final_match = re.search(r"Final Answer:\s*(.*)", response, re.DOTALL)

        def _safe_group(match, idx=1):
            return match.group(idx).strip() if match else ""
        
        return {
            "thought": _safe_group(thought_match),
            "action": _safe_group(action_match),
            "action_input": _safe_group(input_match) or "{}",
            "final_answer": _safe_group(final_match),
        }

    def run(self, query: str) -> Dict[str, Any]:
        """执行 ReAct 循环"""
        tools_desc = "\n".join([
            f"- {t['name']}: {t['description']}"
            for t in self.registry.get_tools_description()
        ])
        prompt = self.SYSTEM_PROMPT.format(tools=tools_desc) + f"\n\nQuestion: {query}\n"
        
        print(f"🤖 Agent 启动: {query}")
        
        for i in range(self.max_iterations):
            response = self._call_llm(prompt)
            print(f"\n LLM 响应:\n{response}")
            parsed = self._parse_response(response)
            
            if not parsed["thought"] and not parsed["action"] and not parsed["final_answer"]:
                print(f"⚠️ 无法解析响应")
                break
                
            if parsed["thought"]:
                print(f"\n💭 Thought: {parsed['thought']}")
            self.trace.append({"step": "thought", "content": parsed.get("thought", "")})
            
            if parsed["final_answer"]:
                print(f"✅ Final Answer: {parsed['final_answer']}")
                self.trace.append({"step": "final_answer", "content": parsed["final_answer"]})
                return {"success": True, "answer": parsed["final_answer"], "trace": self.trace}
            
            if parsed["action"]:
                action_input = parsed.get("action_input", "{}")
                print(f"🔧 Action: {parsed['action']}")
                print(f"📥 Input: {action_input}")
                self.trace.append({"step": "action", "tool": parsed["action"], "input": action_input})
                
                try:
                    args = json.loads(action_input)
                except json.JSONDecodeError:
                    args = {}
                
                observation = self.registry.execute(parsed["action"], args)
                obs_text = str(observation)
                print(f"️ Observation: {obs_text[:100]}")
                self.trace.append({"step": "observation", "content": obs_text})
                
                prompt += f"\nThought: {parsed.get('thought', '')}\nAction: {parsed['action']}\nAction Input: {action_input}\nObservation: {obs_text}\n"
        
        return {"success": False, "error": "Max iterations reached", "trace": self.trace}

# ============================================================
# 模块：示例工具
# ============================================================

def calculator(expression: str) -> str:
    """计算数学表达式"""
    try:
        if re.match(r'^[\d\s\+\-\*\/\(\)\.]+$', expression):
            return str(eval(expression))
        return "Error: Invalid expression"
    except Exception as e:
        return f"Error: {e}"

def get_weather(city: str) -> str:
    """获取天气"""
    return f"{city} 天气：晴，25°C"

# ============================================================
# 模块：入口
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  ReAct Agent 演示")
    print("=" * 60)

    registry = ToolRegistry()
    registry.register(AgentTool(
        name="calculator",
        description="计算数学表达式",
        func=calculator,
        input_schema={"expression": "string"}
    ))
    registry.register(AgentTool(
        name="get_weather",
        description="查询城市天气",
        func=get_weather,
        input_schema={"city": "string"}
    ))

    agent = ReActAgent(registry)
    
    # 测试 1：需要工具调用
    print("\n📌 测试 1: 计算与天气查询")
    result = agent.run("北京今天天气如何？另外计算 25 * 4 + 10 等于多少？")
    print(f"结果: {result.get('answer')}")
    
    # 测试 2：纯推理
    print("\n📌 测试 2: 纯推理问题")
    result2 = agent.run("苹果和香蕉哪个更适合在热带种植？")
    print(f"结果: {result2.get('answer')}")

    print("\n" + "=" * 60)
    print("  演示完成")
    print("=" * 60)
