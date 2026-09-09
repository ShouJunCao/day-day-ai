"""
query_optimization.py — 检索优化策略实现
包含 Query 改写、HyDE、Multi-Query、Step-back 四种优化策略。
"""
import os
from typing import Optional, List
from dataclasses import dataclass, field


# ============================================================
# 模块：查询结果数据结构
# ============================================================

@dataclass
class QueryResult:
    """
    查询结果数据结构。

    属性：
    - query (str): 原始查询
    - rewritten_queries (list[str]): 改写后的查询列表
    - results (list[dict]): 检索结果
    """
    query: str
    rewritten_queries: List[str] = field(default_factory=list)
    results: list = field(default_factory=list)


# ============================================================
# 策略 1：Query 改写
# ============================================================

class QueryRewriter:
    """
    Query 改写器：使用 LLM 优化用户查询。

    原理：
    1. 将用户的原始查询输入 LLM
    2. LLM 生成更精确、更具体的查询
    3. 使用改写后的查询进行检索

    特点：
    - 改善模糊查询的效果
    - 补充缺失的关键词
    - 标准化查询格式
    """

    def __init__(self, prompt_template: Optional[str] = None):
        """
        初始化查询改写器。

        参数：
        - prompt_template (str): 改写 Prompt 模板
        """
        self.prompt_template = prompt_template or self.DEFAULT_PROMPT

    DEFAULT_PROMPT = """你是一个查询优化专家。请将用户的原始查询改写为更精确、更具体的检索查询。

要求：
1. 保留原始查询的核心意图
2. 补充相关的关键词和同义词
3. 使用更专业的术语
4. 只输出改写后的查询，不要解释

原始查询：{query}

改写后的查询："""

    def rewrite(self, query: str) -> str:
        """
        改写单个查询。

        参数：
        - query (str): 原始查询

        返回：
        - str: 改写后的查询
        """
        # 实际项目中调用 LLM API
        # response = llm.generate(self.prompt_template.format(query=query))
        # return response.strip()
        
        # 占位实现：模拟 LLM 改写
        return self._simulate_rewrite(query)

    def _simulate_rewrite(self, query: str) -> str:
        """模拟查询改写（占位实现）"""
        # 简单的关键词扩展
        expansions = {
            "AI": "人工智能 artificial intelligence 机器学习",
            "ML": "机器学习 machine learning 深度学习",
            "NLP": "自然语言处理 natural language processing",
        }
        result = query
        for keyword, expansion in expansions.items():
            if keyword in query and expansion not in query:
                result = result.replace(keyword, f"{keyword}（{expansion}）")
        return result

    def rewrite_batch(self, queries: List[str]) -> List[str]:
        """批量改写多个查询"""
        return [self.rewrite(q) for q in queries]


# ============================================================
# 策略 2：HyDE（Hypothetical Document Embeddings）
# ============================================================

class HyDERetriever:
    """
    HyDE 检索器：假设性文档嵌入检索。

    原理：
    1. 让 LLM 根据查询生成一个假设性回答文档
    2. 将假设性文档编码为向量
    3. 用假设性文档的向量去检索真实文档
    4. 真实文档与假设性文档在向量空间中更接近

    特点：
    - 解决查询和文档之间的表示差距
    - 特别适合开放域问答
    - 增加一次 LLM 调用开销
    """

    def __init__(self, embedding_fn, generation_fn=None):
        """
        初始化 HyDE 检索器。

        参数：
        - embedding_fn: 向量编码函数
        - generation_fn: LLM 生成函数
        """
        self.embedding_fn = embedding_fn
        self.generation_fn = generation_fn
        self.hyde_prompt = """请根据以下问题生成一个详细的回答：

问题：{query}

回答："""

    def retrieve(self, query: str, top_k: int = 5) -> list:
        """
        执行 HyDE 检索。

        参数：
        - query (str): 用户查询
        - top_k (int): 返回结果数

        返回：
        - list: 检索结果
        """
        # 步骤 1：生成假设性文档
        if self.generation_fn:
            hypothetical_doc = self.generation_fn(
                self.hyde_prompt.format(query=query)
            )
        else:
            hypothetical_doc = self._simulate_generation(query)

        # 步骤 2：编码假设性文档
        query_vector = self.embedding_fn(hypothetical_doc)

        # 步骤 3：检索真实文档
        results = self._vector_search(query_vector, top_k)

        return results

    def _simulate_generation(self, query: str) -> str:
        """模拟假设性文档生成（占位实现）"""
        return f"假设性回答：关于'{query}'，这是一个重要的话题..."

    def _vector_search(self, vector: list, top_k: int) -> list:
        """向量检索（占位实现）"""
        return [{"id": i, "score": 0.9 - i * 0.1} for i in range(top_k)]


# ============================================================
# 策略 3：Multi-Query
# ============================================================

class MultiQueryRetriever:
    """
    Multi-Query 检索器：多角度查询检索。

    原理：
    1. 让 LLM 从不同角度生成多个相关查询
    2. 分别用每个查询进行检索
    3. 合并所有检索结果，去重排序
    4. 返回最终的综合结果

    特点：
    - 覆盖更多相关信息
    - 减少单一查询的偏差
    - 增加检索时间（多轮检索）
    """

    def __init__(self, num_queries: int = 3):
        """
        初始化 Multi-Query 检索器。

        参数：
        - num_queries (int): 生成的查询数量
        """
        self.num_queries = num_queries
        self.multi_query_prompt = """请从不同角度为以下问题生成 {n} 个不同的查询。

原始问题：{query}

生成的查询（每行一个）："""

    def retrieve(self, query: str, search_fn) -> list:
        """
        执行 Multi-Query 检索。

        参数：
        - query (str): 用户查询
        - search_fn: 检索函数

        返回：
        - list: 去重后的综合检索结果
        """
        # 步骤 1：生成多个查询
        queries = self._generate_queries(query)

        # 步骤 2：分别检索
        all_results = []
        for q in queries:
            results = search_fn(q)
            all_results.extend(results)

        # 步骤 3：去重合并
        return self._deduplicate(all_results)

    def _generate_queries(self, query: str) -> List[str]:
        """生成多个查询"""
        # 实际调用 LLM
        return [query] + self._simulate_variations(query)

    def _simulate_variations(self, query: str) -> List[str]:
        """模拟查询变化（占位实现）"""
        variations = [
            f"{query} 的原理是什么",
            f"{query} 的具体应用有哪些",
            f"{query} 的最新发展",
        ]
        return variations[:self.num_queries - 1]

    def _deduplicate(self, results: list) -> list:
        """去重合并检索结果"""
        seen = set()
        unique_results = []
        for r in results:
            doc_id = r.get("id", r.get("doc_id", ""))
            if doc_id not in seen:
                seen.add(doc_id)
                unique_results.append(r)
        return unique_results


# ============================================================
# 策略 4：Step-back
# ============================================================

class StepBackRetriever:
    """
    Step-back 检索器：后退一步检索。

    原理：
    1. 生成一个更抽象、更高层次的问题
    2. 用高层次问题检索一般性原理文档
    3. 用原始问题检索具体实例文档
    4. 合并两种检索结果，提供全面回答

    特点：
    - 同时获取原理和实例
    - 适合需要背景知识的复杂问题
    - 增加一次 LLM 调用
    """

    def __init__(self):
        self.step_back_prompt = """请生成一个更高层次、更抽象的问题，涵盖以下具体问题的核心概念。

具体问题：{query}

高层次问题："""

    def retrieve(self, query: str, search_fn) -> dict:
        """
        执行 Step-back 检索。

        参数：
        - query (str): 用户查询
        - search_fn: 检索函数

        返回：
        - dict: 包含原理和实例的检索结果
        """
        # 步骤 1：生成 step-back 问题
        step_back_query = self._generate_step_back(query)

        # 步骤 2：分别检索
        principle_results = search_fn(step_back_query)  # 原理
        specific_results = search_fn(query)               # 实例

        return {
            "original_query": query,
            "step_back_query": step_back_query,
            "principle_results": principle_results,
            "specific_results": specific_results,
        }

    def _generate_step_back(self, query: str) -> str:
        """生成 step-back 问题"""
        # 实际调用 LLM
        return self._simulate_step_back(query)

    def _simulate_step_back(self, query: str) -> str:
        """模拟 step-back 问题生成"""
        return f"什么是{query}的基本原理和应用场景？"


# ============================================================
# 模块：统一检索优化调度器
# ============================================================

class QueryOptimizationScheduler:
    """
    统一检索优化调度器：管理和应用多种查询优化策略。
    """

    STRATEGIES = {
        "rewrite": QueryRewriter,
        "hyde": HyDERetriever,
        "multi_query": MultiQueryRetriever,
        "step_back": StepBackRetriever,
    }

    def __init__(self, strategy: str = "rewrite"):
        """
        初始化调度器。

        参数：
        - strategy (str): 优化策略名称
        """
        self.strategy = strategy
        self.optimizer = self.STRATEGIES[strategy]()

    def optimize(self, query: str, **kwargs) -> dict:
        """
        执行查询优化。

        参数：
        - query (str): 原始查询
        - **kwargs: 传递给优化器的额外参数

        返回：
        - dict: 优化结果
        """
        if self.strategy == "rewrite":
            return {"rewritten_query": self.optimizer.rewrite(query)}
        elif self.strategy == "hyde":
            return {"results": self.optimizer.retrieve(query, **kwargs)}
        elif self.strategy == "multi_query":
            return {"results": self.optimizer.retrieve(query, **kwargs)}
        elif self.strategy == "step_back":
            return self.optimizer.retrieve(query, **kwargs)
        else:
            raise ValueError(f"未知策略: {self.strategy}")


if __name__ == "__main__":
    print("=" * 60)
    print("  检索优化策略演示")
    print("=" * 60)

    # Query 改写演示
    rewriter = QueryRewriter()
    original = "AI 是什么？"
    rewritten = rewriter.rewrite(original)
    print(f"\nQuery 改写:")
    print(f"  原始: {original}")
    print(f"  改写: {rewritten}")

    # Multi-Query 演示
    multi = MultiQueryRetriever(num_queries=3)
    queries = multi._generate_queries("深度学习")
    print(f"\nMulti-Query 生成:")
    for i, q in enumerate(queries, 1):
        print(f"  {i}. {q}")

    # Step-back 演示
    stepback = StepBackRetriever()
    step_back_q = stepback._generate_step_back("Transformer 注意力机制")
    print(f"\nStep-back 生成:")
    print(f"  原问题: Transformer 注意力机制")
    print(f"  后退问题: {step_back_q}")
