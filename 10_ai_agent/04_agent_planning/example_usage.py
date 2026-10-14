"""
example_usage.py — Agent 规划能力演示
演示任务分解、依赖分析和规划执行流程。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_planning import (
    PlanningAgent,
    TaskDecomposer,
    DynamicPlanner,
    SubTask,
    Plan,
)


class DependencyAnalyzer:
    """任务依赖分析器"""
    
    def __init__(self, tasks):
        self.tasks = tasks
        self.graph = {}
        self.in_degree = {}
        self._build_graph()
    
    def _build_graph(self):
        for task in self.tasks:
            self.graph[task.id] = []
            self.in_degree[task.id] = 0
        
        for task in self.tasks:
            for dep in task.dependency:
                if dep in self.graph:
                    self.graph[dep].append(task.id)
                    self.in_degree[task.id] += 1
    
    def get_execution_order(self):
        """获取拓扑排序的执行顺序"""
        from collections import deque
        queue = deque([t for t in self.in_degree if self.in_degree[t] == 0])
        order = []
        temp_in = dict(self.in_degree)
        
        while queue:
            task_id = queue.popleft()
            order.append(task_id)
            for next_id in self.graph.get(task_id, []):
                temp_in[next_id] -= 1
                if temp_in[next_id] == 0:
                    queue.append(next_id)
        
        return order

    def get_parallel_groups(self):
        """获取可并行执行的任务组"""
        from collections import deque
        groups = []
        remaining = set(self.in_degree.keys())
        temp_in = dict(self.in_degree)
        
        while remaining:
            available = [t for t in remaining if temp_in[t] == 0]
            if not available:
                break
            groups.append(available)
            for t in available:
                remaining.remove(t)
                for next_id in self.graph.get(t, []):
                    temp_in[next_id] -= 1
        
        return groups


def demo_decomposition():
    """演示任务分解"""
    print("=" * 60)
    print("  任务分解")
    print("=" * 60)
    
    decomposer = TaskDecomposer()
    
    goals = [
        "分析公司上一季度的销售数据并生成可视化报告",
        "构建一个实时推荐系统",
        "写一篇关于人工智能发展的综述文章"
    ]
    
    for goal in goals:
        print(f"\n 目标: {goal}")
        tasks = decomposer.decompose(goal)
        print(f" 分解为 {len(tasks)} 个子任务:")
        for task in tasks:
            deps = task.dependency if task.dependency else ["无"]
            print(f"    [{task.id}] {task.description} (依赖: {', '.join(deps)})")


def demo_dependency():
    """演示依赖分析"""
    print("\n" + "=" * 60)
    print("  依赖分析")
    print("=" * 60)
    
    tasks = [
        SubTask(id="1", description="收集数据", dependency=[]),
        SubTask(id="2", description="数据清洗", dependency=["1"]),
        SubTask(id="3", description="数据探索", dependency=["1"]),
        SubTask(id="4", description="特征工程", dependency=["2", "3"]),
        SubTask(id="5", description="模型训练", dependency=["4"]),
        SubTask(id="6", description="生成报告", dependency=["5"])
    ]
    
    analyzer = DependencyAnalyzer(tasks)
    
    print("\n 执行顺序（拓扑排序）:")
    order = analyzer.get_execution_order()
    for i, tid in enumerate(order):
        task = next(t for t in tasks if t.id == tid)
        print(f"  {i+1}. {task.description}")
    
    print("\n 可并行执行组:")
    groups = analyzer.get_parallel_groups()
    for i, group in enumerate(groups):
        task_descs = [next(t.description for t in tasks if t.id == tid) for tid in group]
        print(f"  组 {i+1}: {', '.join(task_descs)}")


def demo_planning_agent():
    """演示规划 Agent"""
    print("\n" + "=" * 60)
    print("  规划 Agent")
    print("=" * 60)
    
    agent = PlanningAgent()
    
    print("\n 创建计划...")
    plan = agent.create_plan("分析公司上一季度的销售数据并生成可视化报告")
    
    print("\n 计划详情:")
    for task in plan.tasks:
        deps = task.dependency if task.dependency else ["无"]
        print(f"  [{task.id}] {task.description} (依赖: {', '.join(deps)})")


def demo_planning_flow():
    """演示规划流程"""
    print("\n" + "=" * 60)
    print("  规划流程示意")
    print("=" * 60)
    
    print("""
    规划 - 执行循环:
    
    ┌─────────────────────────────────────────
    │              用户目标                     │
    │   "分析销售数据并生成报告"                 │
    └──────────────┬──────────────────────────┘
                   │
            ┌──────▼──────┐
            │  任务分解     │
            │ (Decompose)   │
            └──────┬──────
                   │
    ┌──────────────┼──────────────┐
    │              │              │
┌───▼────┐  ┌─────▼────┐  ┌────▼─────┐
│ 收集数据│  │ 数据分析 │  │ 生成报告 │
│        │  │          │  │          │
└───┬────┘  └─────┬────┘  ────┬─────┘
    │              │              │
    └──────────────┼──────────────┘
                   │
            ┌──────▼──────┐
            │  动态调整     │
            │ (如有失败)    │
            └────────────┘
                   │
            ┌──────▼──────┐
            │  最终结果     │
            └─────────────┘
    """)


if __name__ == "__main__":
    demo_decomposition()
    demo_dependency()
    demo_planning_agent()
    demo_planning_flow()
