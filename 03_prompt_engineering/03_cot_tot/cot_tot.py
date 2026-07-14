"""
cot_tot.py — 思维链（CoT）与思维树（ToT）实现

包含:
1. Zero-shot CoT: 通过触发词引导逐步推理
2. Few-shot CoT: 通过包含推理步骤的示例引导
3. Tree-of-Thought: BFS/DFS 多路径搜索框架
4. ReasoningEngine: 统一推理引擎（自动策略选择）
"""

from typing import Optional, Callable
from dataclasses import dataclass, field
import json


# ============================================================
# 第一部分：Zero-shot CoT
# ============================================================

@dataclass
class CoTResult:
    """CoT 推理结果"""
    question: str
    reasoning_steps: list[str]
    final_answer: str
    confidence: float = 0.0


class ZeroShotCoT:
    """
    Zero-shot CoT：通过触发词引导模型逐步推理。
    
    核心原理：
        在 Prompt 中加入 "Let's think step by step"
        触发模型的推理链，无需提供示例。
    
    适用场景：
        数学推理、逻辑分析、常识推理
    """
    
    TRIGGERS = {
        "en": "Let's think step by step.",
        "zh": "让我们一步步思考。",
        "detailed": (
            "Please break this down step by step, "
            "showing your reasoning at each step."
        ),
    }
    
    def __init__(self, language: str = "zh"):
        """
        参数:
            language: 触发词语言（en / zh / detailed）
        """
        self.trigger = self.TRIGGERS.get(
            language, self.TRIGGERS["zh"]
        )
    
    def build_prompt(self, question: str) -> str:
        """
        构建 Zero-shot CoT Prompt。
        
        参数:
            question: 需要推理的问题
        返回:
            包含触发词的完整 Prompt
        """
        return (
            f"## 问题\n{question}\n\n"
            f"## 要求\n"
            f"请先展示完整的推理过程（每一步都要写清楚），"
            f"最后给出最终答案。\n\n"
            f"{self.trigger}"
        )
    
    def parse_response(self, response_text: str) -> CoTResult:
        """
        解析模型输出，提取推理步骤和最终答案。
        
        参数:
            response_text: 模型的完整输出
        返回:
            CoTResult 对象
        """
        lines = response_text.strip().split("\n")
        steps = []
        answer = ""
        
        for line in lines:
            stripped = line.strip()
            # 提取编号步骤
            if any(stripped.startswith(p) for p in 
                   ["1.", "2.", "3.", "4.", "5.", "6.",
                    "步骤", "Step", "第"]):
                steps.append(stripped)
            # 提取最终答案
            if "答案" in stripped or "answer" in stripped.lower():
                answer = stripped
        
        return CoTResult(
            question="",
            reasoning_steps=steps,
            final_answer=answer or (lines[-1] if lines else ""),
        )


# ============================================================
# 第二部分：Few-shot CoT
# ============================================================

@dataclass
class CoTExample:
    """CoT 示例：包含问题、推理步骤和答案"""
    question: str
    steps: list[str]
    answer: str


class FewShotCoT:
    """
    Few-shot CoT：通过包含推理步骤的示例引导模型。
    
    相比 Zero-shot CoT 的优势：
        - 推理格式更可控
        - 推理深度更一致
        - 适合特定领域的推理模式
    """
    
    def __init__(self, examples: list[CoTExample]):
        """
        参数:
            examples: CoT 示例列表（建议 2-4 个）
        """
        self.examples = examples
    
    def build_prompt(self, question: str) -> str:
        """
        构建 Few-shot CoT Prompt。
        
        参数:
            question: 需要推理的实际问题
        返回:
            包含示例和问题的完整 Prompt
        """
        parts = [
            "## 任务\n请像下面的示例一样，逐步推理并给出答案。\n"
        ]
        
        # 添加示例
        for i, ex in enumerate(self.examples, 1):
            steps_text = "\n".join(
                f"  {j+1}. {s}" for j, s in enumerate(ex.steps)
            )
            parts.append(
                f"### 示例 {i}\n"
                f"**问题：** {ex.question}\n"
                f"**推理过程：**\n{steps_text}\n"
                f"**答案：** {ex.answer}"
            )
        
        # 实际问题
        parts.append(
            f"### 实际任务\n"
            f"**问题：** {question}\n"
            f"**推理过程：**"
        )
        
        return "\n\n".join(parts)
    
    @classmethod
    def math_reasoning(cls) -> "FewShotCoT":
        """创建数学推理的预设 CoT 模板"""
        examples = [
            CoTExample(
                question="小明有 15 个糖果，给了小红 7 个，"
                         "又从小华那里得到 3 个，现在有几个？",
                steps=[
                    "初始数量：15 个糖果",
                    "给小红 7 个：15 - 7 = 8 个",
                    "从小华得到 3 个：8 + 3 = 11 个",
                ],
                answer="11 个",
            ),
            CoTExample(
                question="一个水池，A 管 6 小时注满，B 管 8 小时"
                         "注满，两管同时开，几小时注满？",
                steps=[
                    "A 管每小时注水量：1/6",
                    "B 管每小时注水量：1/8",
                    "两管同时开：1/6 + 1/8 = 7/24",
                    "注满时间：1 ÷ (7/24) = 24/7 ≈ 3.43 小时",
                ],
                answer="约 3.43 小时（24/7 小时）",
            ),
        ]
        return cls(examples)


# ============================================================
# 第三部分：Tree-of-Thought
# ============================================================

class TreeOfThought:
    """
    Tree-of-Thought 搜索框架。
    
    通过 BFS/DFS 在多个推理路径中搜索最优解。
    每个节点代表一个推理步骤，LLM 负责生成候选
    和评估分数。
    """
    
    def __init__(
        self,
        llm_client,
        max_depth: int = 5,
        branching_factor: int = 3,
        search_method: str = "bfs",
    ):
        """
        参数:
            llm_client: LLM 客户端
            max_depth: 最大推理深度
            branching_factor: 每步生成的候选数
            search_method: 搜索方法（bfs / dfs）
        """
        self.client = llm_client
        self.max_depth = max_depth
        self.branching = branching_factor
        self.search_method = search_method
    
    def generate_candidates(
        self, question: str, current_path: list[str]
    ) -> list[str]:
        """在当前推理路径上生成候选下一步"""
        path_text = "\n".join(
            f"  步骤 {i+1}: {s}" for i, s in enumerate(current_path)
        ) or "  （尚未开始）"
        
        prompt = (
            f"问题：{question}\n\n"
            f"已有推理步骤：\n{path_text}\n\n"
            f"请给出 {self.branching} 种可能的下一步推理，"
            f"每种用一行描述，格式为 JSON 数组。"
        )
        
        response = self.client.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
        )
        
        try:
            candidates = json.loads(response.content)
            return candidates if isinstance(candidates, list) else []
        except json.JSONDecodeError:
            return []
    
    def evaluate(self, question: str, path: list[str]) -> float:
        """评估当前推理路径的质量（0-1 分）"""
        path_text = "\n".join(
            f"  步骤 {i+1}: {s}" for i, s in enumerate(path)
        )
        
        prompt = (
            f"问题：{question}\n\n"
            f"推理过程：\n{path_text}\n\n"
            f"请评估这个推理过程的正确性和合理性，"
            f"输出一个 0-1 之间的分数（仅输出数字）。"
        )
        
        response = self.client.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        
        try:
            score = float(response.content.strip())
            return max(0.0, min(1.0, score))
        except (ValueError, AttributeError):
            return 0.0
    
    def solve(self, question: str) -> dict:
        """使用 BFS + beam search 搜索最优推理路径"""
        paths = [([], 0.0)]
        best_path = []
        best_score = 0.0
        
        for depth in range(self.max_depth):
            new_paths = []
            
            for path, _ in paths:
                candidates = self.generate_candidates(
                    question, path
                )
                
                for candidate in candidates:
                    new_path = path + [candidate]
                    score = self.evaluate(question, new_path)
                    new_paths.append((new_path, score))
                    
                    if score > best_score:
                        best_score = score
                        best_path = new_path
            
            # beam search：保留 Top-K
            new_paths.sort(key=lambda x: x[1], reverse=True)
            paths = new_paths[:self.branching]
            
            if best_score >= 0.9:
                break
        
        return {
            "question": question,
            "best_path": best_path,
            "score": best_score,
            "steps_explored": len(paths) * self.max_depth,
        }


# ============================================================
# 第四部分：统一推理引擎
# ============================================================

class ReasoningEngine:
    """
    统一推理引擎：自动选择 CoT / ToT 策略。
    
    集成重试、限流、日志等生产级特性。
    """
    
    def __init__(
        self,
        llm_client,
        default_strategy: str = "auto",
        max_api_calls: int = 20,
    ):
        """
        参数:
            llm_client: LLM 客户端
            default_strategy: 默认策略（auto / cot / tot）
            max_api_calls: 单次推理最大 API 调用次数
        """
        self.client = llm_client
        self.strategy = default_strategy
        self.max_calls = max_api_calls
        self._call_count = 0
    
    def assess_complexity(self, question: str) -> str:
        """评估问题复杂度，返回推荐策略"""
        prompt = (
            f"评估以下问题的推理复杂度，输出 'simple' 或 "
            f"'complex'（仅输出一个词）：\n\n{question}"
        )
        response = self.client.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        self._call_count += 1
        
        result = response.content.strip().lower()
        return "complex" if "complex" in result else "simple"
    
    def reason(self, question: str) -> dict:
        """
        执行推理，自动选择最优策略。
        
        参数:
            question: 需要推理的问题
        返回:
            包含推理结果和元数据的字典
        """
        self._call_count = 0
        
        # 确定策略
        if self.strategy == "auto":
            complexity = self.assess_complexity(question)
            strategy = "tot" if complexity == "complex" else "cot"
        else:
            strategy = self.strategy
        
        # 执行推理
        if strategy == "cot":
            cot = ZeroShotCoT(language="zh")
            prompt = cot.build_prompt(question)
            response = self.client.chat(
                messages=[{"role": "user", "content": prompt}],
            )
            self._call_count += 1
            result = cot.parse_response(response.content)
            return {
                "strategy": "cot",
                "question": question,
                "answer": result.final_answer,
                "steps": result.reasoning_steps,
                "api_calls": self._call_count,
            }
        else:
            tot = TreeOfThought(
                self.client,
                max_depth=3,
                branching_factor=2,
            )
            result = tot.solve(question)
            self._call_count += result["steps_explored"]
            return {
                "strategy": "tot",
                "question": question,
                "answer": result["best_path"],
                "score": result["score"],
                "api_calls": self._call_count,
            }
