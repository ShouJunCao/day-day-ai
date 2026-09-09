"""
agentic_rag.py — Agentic RAG（Agent 自主检索路由）实现
将 Agent 技术与 RAG 结合，实现智能决策的检索架构。
"""
import os
import json
from typing import Optional, List, Dict, Callable
from dataclasses import dataclass, field


# ============================================================
# 模块：数据结构
# ============================================================

@dataclass
class AgentAction:
    """Agent 执行的动作"""
    action_name: str
    action_input: str
    action_result: str = ""
    thought: str = ""


@dataclass
class AgentStep:
    """Agent 执行步骤"""
    step_number: int
    action: AgentAction
    observation: str


@dataclass
class AgentResult:
    """Agent 执行结果"""
    answer: str
    steps: List[AgentStep]
    confidence: float
    route_taken: List[str]


# ============================================================
# 模块：Agent 核心
# ============================================================

class ReActAgent:
    """
    ReAct Agent：基于 ReAct 范式的智能代理。

    原理：
    1. Thought：思考下一步应该做什么
    2. Action：执行具体动作（如检索、计算、查询）
    3. Observation：观察动作的结果
    4. 循环执行直到得出最终答案
    """

    def __init__(self, tools: List[Callable], max_steps: int = 5):
        """
        初始化 ReAct Agent。

        参数：
        - tools (list[Callable]): 可用工具列表
        - max_steps (int): 最大执行步数
        """
        self.tools = {tool.__name__: tool for tool in tools}
        self.max_steps = max_steps
        self.steps: List[AgentStep] = []

    def execute(self, question: str) -> AgentResult:
        """
        执行 Agent 推理流程。

        参数：
        - question (str): 用户问题

        返回：
        - AgentResult: 执行结果
        """
        self.steps = []
        route_taken = []

        # ReAct 循环
        for step_num in range(1, self.max_steps + 1):
            # 1. Thought：决定下一步行动
            thought = self._decide_next_step(question, step_num)

            # 2. Action：选择并执行工具
            action_name, action_input = self._select_action(thought)
            action = AgentAction(
                action_name=action_name,
                action_input=action_input,
                thought=thought,
            )

            # 3. Observation：执行工具并观察结果
            if action_name in self.tools:
                result = self.tools[action_name](action_input)
                action.action_result = str(result)
            else:
                result = f"未知工具: {action_name}"
                action.action_result = result

            step = AgentStep(
                step_number=step_num,
                action=action,
                observation=str(result),
            )
            self.steps.append(step)
            route_taken.append(action_name)

            # 4. 判断是否得出答案
            if self._is_final_answer(action_name, result):
                break

        # 生成最终答案
        answer = self._generate_final_answer(question, self.steps)
        confidence = self._calculate_confidence()

        return AgentResult(
            answer=answer,
            steps=self.steps,
            confidence=confidence,
            route_taken=route_taken,
        )

    def _decide_next_step(self, question: str, step_num: int) -> str:
        """思考下一步应该做什么（简化版）"""
        if step_num == 1:
            return f"首先需要检索与'{question}'相关的文档"
        elif step_num == 2:
            return "检索结果需要重排序以提高相关性"
        elif step_num == 3:
            return "需要验证检索结果是否足够回答问题"
        else:
            return "已收集足够信息，可以生成最终答案"

    def _select_action(self, thought: str) -> tuple:
        """选择要执行的动作"""
        if "检索" in thought:
            return ("vector_search", thought)
        elif "重排序" in thought:
            return ("rerank", thought)
        elif "验证" in thought:
            return ("verify", thought)
        else:
            return ("generate", thought)

    def _is_final_answer(self, action_name: str, result) -> bool:
        """判断是否得出最终答案"""
        return action_name == "generate"

    def _generate_final_answer(self, question: str, steps: List[AgentStep]) -> str:
        """生成最终答案"""
        context_parts = [step.action.action_result for step in steps if step.action.action_result]
        context = " ".join(context_parts)
        return f"[Agentic RAG 回答] 基于 {len(steps)} 步自主推理，关于'{question}'的回答是：{context[:100]}..."

    def _calculate_confidence(self) -> float:
        """计算答案置信度"""
        if not self.steps:
            return 0.0
        return min(0.5 + len(self.steps) * 0.1, 1.0)


# ============================================================
# 模块：工具定义
# ============================================================

def vector_search(query: str) -> str:
    """向量检索工具"""
    return f"[检索结果] 找到 5 个与'{query}'相关的文档片段。"


def rerank(query: str) -> str:
    """重排序工具"""
    return f"[重排序结果] 对检索结果重排序，Top-3 相关性分数为 0.95, 0.88, 0.82。"


def verify(query: str) -> str:
    """验证工具"""
    return f"[验证结果] 当前检索结果足以回答'{query}'。"


def generate(query: str) -> str:
    """生成工具"""
    return f"[生成结果] 基于检索和验证结果，生成关于'{query}'的最终回答。"


# ============================================================
# 模块：路由 Agent
# ============================================================

class RoutingAgent:
    """
    路由 Agent：根据问题类型自动选择最佳检索策略。

    支持的策略：
    - vector_search: 向量检索（默认）
    - keyword_search: 关键词检索
    - graph_search: 图谱检索
    - hybrid_search: 混合检索
    """

    STRATEGIES = {
        "vector_search": "向量检索",
        "keyword_search": "关键词检索",
        "graph_search": "图谱检索",
        "hybrid_search": "混合检索",
    }

    def __init__(self):
        pass

    def route(self, question: str) -> str:
        """
        根据问题类型选择最佳策略。

        参数：
        - question (str): 用户问题

        返回：
        - str: 选择的策略名称
        """
        # 简单的规则路由
        if any(kw in question for kw in ["什么", "谁", "哪里"]):
            return "vector_search"
        elif any(kw in question for kw in ["比较", "区别", "对比"]):
            return "hybrid_search"
        elif any(kw in question for kw in ["关系", "关联", "联系"]):
            return "graph_search"
        else:
            return "keyword_search"

    def execute_routed_query(self, question: str) -> dict:
        """执行路由后的查询"""
        strategy = self.route(question)
        strategy_name = self.STRATEGIES.get(strategy, "未知策略")

        return {
            "question": question,
            "selected_strategy": strategy,
            "strategy_name": strategy_name,
            "result": f"使用 {strategy_name} 检索到相关结果。",
        }


# ============================================================
# 模块：使用示例
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  Agentic RAG 演示")
    print("=" * 60)

    # ReAct Agent 演示
    tools = [vector_search, rerank, verify, generate]
    agent = ReActAgent(tools=tools, max_steps=4)

    question = "Transformer 和 BERT 的关系是什么？"
    result = agent.execute(question)

    print(f"\n问题: {question}")
    print(f"\nAgent 执行步骤 ({len(result.steps)} 步):")
    for step in result.steps:
        print(f"  步骤 {step.step_number}:")
        print(f"    Thought: {step.action.thought}")
        print(f"    Action: {step.action.action_name}")
        print(f"    Result: {step.action.action_result[:50]}...")

    print(f"\n最终答案: {result.answer}")
    print(f"置信度: {result.confidence:.2f}")
    print(f"执行路径: {' → '.join(result.route_taken)}")

    # Routing Agent 演示
    print("\n" + "=" * 60)
    print("  路由 Agent 演示")
    print("=" * 60)

    router = RoutingAgent()
    test_questions = [
        "什么是 Transformer？",
        "BERT 和 GPT 有什么区别？",
        "Transformer 和注意力机制的关系是什么？",
        "如何优化 RAG 系统？",
    ]

    print(f"\n{'问题':<30s} {'选择策略':<15s} {'策略名称':<15s}")
    print("-" * 60)
    for q in test_questions:
        route_result = router.execute_routed_query(q)
        print(f"{q:<30s} {route_result['selected_strategy']:<15s} {route_result['strategy_name']:<15s}")
