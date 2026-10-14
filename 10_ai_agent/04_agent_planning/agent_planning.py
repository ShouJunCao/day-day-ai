"""
agent_planning.py — Agent 规划能力（任务分解、动态规划）
演示 Agent 如何将复杂目标分解为子任务，并根据执行反馈动态调整计划。
"""
import os
import re
import json
import time
from typing import List, Dict, Any, Optional
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
# 模块：数据结构
# ============================================================

@dataclass
class SubTask:
    """子任务定义"""
    id: str
    description: str
    status: str = "pending"  # pending, in_progress, completed, failed
    result: str = ""
    dependency: List[str] = field(default_factory=list)

@dataclass
class Plan:
    """计划定义"""
    goal: str
    tasks: List[SubTask] = field(default_factory=list)
    current_step: int = 0
    is_complete: bool = False

# ============================================================
# 模块：任务分解器
# ============================================================

class TaskDecomposer:
    """
    任务分解器
    
    使用 LLM 将复杂目标分解为可执行的子任务序列。
    支持依赖关系分析和并行任务识别。
    """
    
    PROMPT_TEMPLATE = """你是一个任务规划专家。请将以下复杂目标分解为具体的子任务序列。

目标：{goal}

要求：
1. 每个子任务应该具体、可执行、有明确的完成标准。
2. 按逻辑顺序排列，考虑任务之间的依赖关系。
3. 标记哪些任务可以并行执行。
4. 输出 JSON 格式，包含 id, description, dependency 字段。

示例输出格式：
[
  {{"id": "1", "description": "收集数据", "dependency": []}},
  {{"id": "2", "description": "分析数据", "dependency": ["1"]}},
  {{"id": "3", "description": "生成报告", "dependency": ["2"]}}
]

请输出 JSON："""

    def decompose(self, goal: str) -> List[SubTask]:
        """分解目标为子任务"""
        prompt = self.PROMPT_TEMPLATE.format(goal=goal)
        
        try:
            response = client.chat.completions.create(
                model=DASHSCOPE_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            content = response.choices[0].message.content
            if content is None:
                raise ValueError("Empty response")
            content = content.strip()
            
            # 清理可能的 Markdown 代码块标记
            content = re.sub(r'^```json\s*', '', content)
            content = re.sub(r'\s*```$', '', content)
            
            tasks_data = json.loads(content)
            return [
                SubTask(
                    id=t["id"],
                    description=t["description"],
                    dependency=t.get("dependency", [])
                )
                for t in tasks_data
            ]
        except Exception as e:
            print(f"分解失败: {e}")
            # 回退到默认分解
            return [
                SubTask(id="1", description="分析问题需求", dependency=[]),
                SubTask(id="2", description="收集相关信息", dependency=["1"]),
                SubTask(id="3", description="制定解决方案", dependency=["2"]),
                SubTask(id="4", description="执行并验证", dependency=["3"])
            ]

# ============================================================
# 模块：动态规划器
# ============================================================

class DynamicPlanner:
    """
    动态规划器
    
    根据任务执行结果动态调整计划。
    如果某个任务失败，可以决定重试、跳过或调整后续任务。
    """
    
    ADJUST_PROMPT = """你是一个计划调整专家。当前计划执行中遇到了问题，请决定如何调整计划。

当前目标：{goal}
已完成任务：{completed_tasks}
失败任务：{failed_task}
失败原因：{error_reason}
剩余待执行任务：{remaining_tasks}

请输出调整决策（JSON 格式）：
{{
  "action": "retry" | "skip" | "modify" | "abort",
  "reason": "调整原因",
  "modified_plan": "修改后的计划描述（如果 action 是 modify）"
}}"""

    def adjust_plan(self, plan: Plan, failed_task: SubTask, error: str) -> Dict[str, Any]:
        """根据失败情况调整计划"""
        completed = [t for t in plan.tasks if t.status == "completed"]
        remaining = [t for t in plan.tasks if t.status == "pending"]
        
        prompt = self.ADJUST_PROMPT.format(
            goal=plan.goal,
            completed_tasks=[t.description for t in completed],
            failed_task=failed_task.description,
            error_reason=error,
            remaining_tasks=[t.description for t in remaining]
        )
        
        try:
            response = client.chat.completions.create(
                model=DASHSCOPE_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            content = response.choices[0].message.content
            if content is None:
                raise ValueError("Empty response")
            content = content.strip()
            
            # 清理可能的 Markdown 代码块标记
            content = re.sub(r'^```json\s*', '', content)
            content = re.sub(r'\s*```$', '', content)
            return json.loads(content)
        except Exception as e:
            return {
                "action": "retry",
                "reason": f"调整失败，默认重试: {e}",
                "modified_plan": ""
            }

# ============================================================
# 模块：规划 Agent
# ============================================================

class PlanningAgent:
    """
    规划 Agent
    
    结合任务分解和动态规划，实现完整的规划 - 执行循环。
    """
    
    def __init__(self):
        self.decomposer = TaskDecomposer()
        self.planner = DynamicPlanner()
        self.current_plan: Optional[Plan] = None

    def create_plan(self, goal: str) -> Plan:
        """创建计划"""
        print(f"🎯 目标: {goal}")
        print("📝 正在分解任务...")
        tasks = self.decomposer.decompose(goal)
        self.current_plan = Plan(goal=goal, tasks=tasks)
        print(f"✅ 计划生成完成，共 {len(tasks)} 个子任务")
        return self.current_plan

    def execute_plan(self, mock_executor=None) -> Dict[str, Any]:
        """执行计划"""
        if not self.current_plan:
            return {"error": "No plan created"}
        
        plan = self.current_plan
        print(f"\n🚀 开始执行计划...")
        
        for i, task in enumerate(plan.tasks):
            print(f"\n  步骤 {i+1}/{len(plan.tasks)}: {task.description}")
            task.status = "in_progress"
            
            # 模拟执行（实际项目中这里会调用工具或 LLM）
            if mock_executor:
                success, result = mock_executor(task)
            else:
                # 默认模拟成功
                success = True
                result = f"任务 '{task.description}' 执行成功"
            
            if success:
                task.status = "completed"
                task.result = result
                print(f"    ✅ 完成: {result}")
            else:
                task.status = "failed"
                print(f"    ❌ 失败: {result}")
                
                # 动态调整计划
                print("    🔄 正在调整计划...")
                adjustment = self.planner.adjust_plan(plan, task, result)
                print(f"    决策: {adjustment.get('action', 'unknown')}")
                print(f"    原因: {adjustment.get('reason', '')}")
                
                if adjustment.get("action") == "abort":
                    plan.is_complete = True
                    return {
                        "success": False,
                        "reason": "Plan aborted",
                        "plan": plan
                    }
                elif adjustment.get("action") == "skip":
                    task.status = "skipped"
                    continue
                elif adjustment.get("action") == "retry":
                    # 重试逻辑（简化版）
                    task.status = "pending"
                    if mock_executor:
                        success, result = mock_executor(task)
                        if success:
                            task.status = "completed"
                            task.result = result
                        else:
                            task.status = "failed"
        
        plan.is_complete = True
        return {
            "success": True,
            "completed_tasks": len([t for t in plan.tasks if t.status == "completed"]),
            "total_tasks": len(plan.tasks),
            "plan": plan
        }

# ============================================================
# 模块：入口
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  Agent 规划能力演示")
    print("=" * 60)

    agent = PlanningAgent()
    
    # 测试 1：正常任务分解与执行
    print("\n 测试 1: 正常任务分解")
    plan = agent.create_plan("分析公司上一季度的销售数据并生成可视化报告")
    for task in plan.tasks:
        print(f"  - [{task.id}] {task.description} (依赖: {task.dependency})")
    
    # 模拟执行器
    def mock_executor(task):
        return True, f"完成: {task.description}"
    
    result = agent.execute_plan(mock_executor)
    print(f"\n 执行结果: {result['success']}")
    print(f" 完成进度: {result['completed_tasks']}/{result['total_tasks']}")

    # 测试 2：带失败场景的执行
    print("\n 测试 2: 带失败场景的执行")
    agent2 = PlanningAgent()
    agent2.create_plan("构建一个实时推荐系统")
    
    call_count = [0]
    def failing_executor(task):
        call_count[0] += 1
        if "数据清洗" in task.description and call_count[0] == 1:
            return False, "数据格式错误，无法清洗"
        return True, f"完成: {task.description}"
    
    result2 = agent2.execute_plan(failing_executor)
    print(f"\n 执行结果: {result2.get('success', 'N/A')}")

    print("\n" + "=" * 60)
    print("  演示完成")
    print("=" * 60)
