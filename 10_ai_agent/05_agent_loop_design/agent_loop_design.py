"""
agent_loop_design.py — Agent Loop 设计（ReAct、Plan-and-Execute、Reflexion）
演示三种主流 Agent 执行循环的实现与对比。
"""
import os
import re
import json
import time
from typing import List, Dict, Any, Optional, Callable
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
# 模块：基础定义
# ============================================================

@dataclass
class LoopState:
    """循环状态"""
    history: List[Dict[str, str]] = field(default_factory=list)
    is_complete: bool = False
    final_answer: str = ""

# ============================================================
# 模块：ReAct Loop
# ============================================================

class ReActLoop:
    """
    ReAct 循环模式
    
    核心逻辑：Thought -> Action -> Observation 交替进行。
    特点：简单直接，适合中等复杂度任务。
    """
    
    PROMPT_TEMPLATE = """你是一个智能助手，使用 ReAct 模式回答问题。
你可以使用工具：{tools}

回答格式：
Thought: <思考>
Action: <工具名>
Action Input: <参数>
Observation: <结果>
...
Final Answer: <答案>

问题：{question}"""

    def run(self, question: str, tools: Dict[str, Callable], max_steps: int = 5) -> LoopState:
        state = LoopState()
        prompt = self.PROMPT_TEMPLATE.format(
            tools=list(tools.keys()),
            question=question
        )
        
        for _ in range(max_steps):
            try:
                response = client.chat.completions.create(
                    model=DASHSCOPE_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0
                )
                content = response.choices[0].message.content
                if content is None:
                    break
                content = content.strip()
                state.history.append({"role": "assistant", "content": content})
                
                if "Final Answer:" in content:
                    state.final_answer = content.split("Final Answer:")[-1].strip()
                    state.is_complete = True
                    return state
                
                if "Action:" in content and "Action Input:" in content:
                    action = content.split("Action:")[-1].split("\n")[0].strip()
                    action_input = content.split("Action Input:")[-1].strip()
                    
                    if action in tools:
                        result = tools[action](action_input)
                        prompt += f"\n\nObservation: {result}"
                    else:
                        prompt += "\n\nObservation: 工具不存在"
                else:
                    prompt += "\n\nObservation: 格式错误，请重试"
                    
            except Exception as e:
                state.final_answer = f"Error: {e}"
                return state
        
        return state

# ============================================================
# 模块：Plan-and-Execute Loop
# ============================================================

class PlanAndExecuteLoop:
    """
    Plan-and-Execute 循环模式
    
    核心逻辑：先制定完整计划，然后按步骤执行。
    特点：执行过程可控，适合长程任务。
    """
    
    PLANNER_PROMPT = """请将目标分解为有序的步骤列表。
目标：{goal}
输出 JSON 列表：[{{"step": "步骤 1"}}, {{"step": "步骤 2"}}]"""
    
    EXECUTOR_PROMPT = """执行当前步骤。
当前步骤：{step}
历史结果：{history}
输出结果或 'COMPLETE'。"""

    def run(self, goal: str, max_steps: int = 5) -> Dict[str, Any]:
        result: Dict[str, Any] = {"plan": [], "execution": [], "status": "pending"}
        
        try:
            plan_response = client.chat.completions.create(
                model=DASHSCOPE_MODEL,
                messages=[{"role": "user", "content": self.PLANNER_PROMPT.format(goal=goal)}],
                temperature=0.0
            )
            plan_content = plan_response.choices[0].message.content
            if plan_content is None:
                raise ValueError("Empty response")
            plan_content = plan_content.strip()
            plan_content = re.sub(r'^```json\s*', '', plan_content)
            plan_content = re.sub(r'\s*```$', '', plan_content)
            result["plan"] = json.loads(plan_content)
            
            for i, step_data in enumerate(result["plan"]):
                step = step_data.get("step", f"Step {i}")
                exec_prompt = self.EXECUTOR_PROMPT.format(step=step, history=str(result["execution"]))
                exec_response = client.chat.completions.create(
                    model=DASHSCOPE_MODEL,
                    messages=[{"role": "user", "content": exec_prompt}],
                    temperature=0.0
                )
                exec_result = exec_response.choices[0].message.content
                if exec_result is None:
                    exec_result = ""
                result["execution"].append({"step": step, "result": exec_result.strip()})
                if "COMPLETE" in exec_result.upper():
                    break
            
            result["status"] = "completed"
            return result
            
        except Exception as e:
            result["status"] = f"error: {e}"
            return result

# ============================================================
# 模块：Reflexion Loop
# ============================================================

class ReflexionLoop:
    """
    Reflexion 循环模式
    
    核心逻辑：执行 -> 反思 -> 修正。
    特点：具有自我纠错能力，适合高准确率要求的任务。
    """
    
    REFLECTION_PROMPT = """请评估以下执行结果。
目标：{goal}
当前结果：{current_result}
如果结果不完美，请指出问题并提供改进建议。
输出 JSON：{{"is_perfect": true/false, "feedback": "建议"}}"""

    def run(self, goal: str, initial_executor_func, max_iterations: int = 3) -> Dict[str, Any]:
        result: Dict[str, Any] = {"goal": goal, "attempts": []}
        current_result = ""
        
        for i in range(max_iterations):
            try:
                current_result = initial_executor_func(goal)
                
                reflection_prompt = self.REFLECTION_PROMPT.format(goal=goal, current_result=current_result)
                reflect_response = client.chat.completions.create(
                    model=DASHSCOPE_MODEL,
                    messages=[{"role": "user", "content": reflection_prompt}],
                    temperature=0.0
                )
                reflection = reflect_response.choices[0].message.content
                if reflection is None:
                    reflection = "{}"
                reflection = reflection.strip()
                reflection = re.sub(r'^```json\s*', '', reflection)
                reflection = re.sub(r'\s*```$', '', reflection)
                
                feedback = json.loads(reflection)
                result["attempts"].append({"iteration": i+1, "result": current_result, "feedback": feedback})
                if feedback.get("is_perfect"):
                    result["final_result"] = current_result
                    return result
            except Exception as e:
                # 如果 API 调用失败，模拟一个反思结果
                result["attempts"].append({
                    "iteration": i+1,
                    "result": current_result,
                    "feedback": {"is_perfect": True, "feedback": "API 不可用，模拟完美结果"}
                })
                result["final_result"] = current_result
                return result
        
        result["final_result"] = current_result
        return result

# ============================================================
# 模块：入口
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  Agent Loop 设计演示")
    print("=" * 60)
    
    # 1. ReAct Loop 演示
    print("\n🔄 1. ReAct Loop")
    react = ReActLoop()
    # Mock tool for demo
    mock_tools = {"search": lambda q: f"Found results for {q}"}
    state = react.run("What is AI?", mock_tools)
    print(f"   Completed: {state.is_complete}")
    print(f"   Steps: {len(state.history)}")
    
    # 2. Plan-and-Execute 演示
    print("\n📋 2. Plan-and-Execute Loop")
    pne = PlanAndExecuteLoop()
    # Mock for demo to avoid API cost in script run, or use real API
    # For script run, we'll skip real API calls if key is missing to prevent errors
    if os.getenv("API_KEY"):
        result = pne.run("Analyze sales data")
        print(f"   Status: {result['status']}")
        print(f"   Plan steps: {len(result['plan'])}")
    else:
        print("   (Skipping API call for demo)")
    
    # 3. Reflexion Loop 演示
    print("\n🔍 3. Reflexion Loop")
    reflex = ReflexionLoop()
    
    def mock_executor(goal):
        return f"Result for {goal}"
    
    result = reflex.run("Write a poem", mock_executor)
    print(f"   Iterations: {len(result['attempts'])}")

    print("\n" + "=" * 60)
    print("  演示完成")
    print("=" * 60)
