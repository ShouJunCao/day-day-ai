"""
reranking.py — 重排序技术实现
包含 BGE-Reranker、Cross-Encoder、Cohere Rerank 三种重排序策略。
"""
import os
import math
from typing import Optional, List, Tuple
from dataclasses import dataclass, field


# ============================================================
# 模块：重排序结果数据结构
# ============================================================

@dataclass
class RerankResult:
    """
    重排序结果。

    属性：
    - doc_id (str): 文档 ID
    - text (str): 文档内容
    - score (float): 重排序得分
    - original_rank (int): 原始排名
    """
    doc_id: str
    text: str
    score: float
    original_rank: int = 0


# ============================================================
# 策略 1：Cross-Encoder 重排序
# ============================================================

class CrossEncoderReranker:
    """
    Cross-Encoder 重排序器：使用 Cross-Encoder 模型对检索结果重排序。

    原理：
    1. 将查询和文档拼接为一个输入 [CLS] query [SEP] doc [SEP]
    2. 通过 Cross-Encoder 模型（如 BERT）编码
    3. 取 [CLS] token 的输出经过分类头得到相关性分数
    4. 按分数重新排序

    特点：
    - 精度高（查询和文档深度交互）
    - 速度慢（每对查询 - 文档都需要一次推理）
    - 适合 Top-K 精排（K 通常 < 50）
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        初始化 Cross-Encoder 重排序器。

        参数：
        - model_name (str): 预训练模型名称
        """
        self.model_name = model_name
        self._model = None
        self._tokenizer = None

    def _load_model(self):
        """延迟加载模型"""
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self._model = AutoModelForSequenceClassification.from_pretrained(self.model_name)

    def rerank(self, query: str, candidates: List[Tuple[str, str]], top_k: int = 10) -> List[RerankResult]:
        """
        对候选文档进行重排序。

        参数：
        - query (str): 查询文本
        - candidates (list[tuple]): (doc_id, text) 元组列表
        - top_k (int): 返回结果数

        返回：
        - list[RerankResult]: 重排序后的结果
        """
        if not candidates:
            return []

        # 计算每对查询 - 文档的相关性分数
        scored_candidates = []
        for i, (doc_id, text) in enumerate(candidates):
            score = self._compute_similarity(query, text)
            scored_candidates.append(RerankResult(
                doc_id=doc_id,
                text=text,
                score=score,
                original_rank=i + 1,
            ))

        # 按分数降序排序
        scored_candidates.sort(key=lambda x: x.score, reverse=True)
        return scored_candidates[:top_k]

    def _compute_similarity(self, query: str, doc: str) -> float:
        """计算查询和文档的相关性分数"""
        import torch

        if self._tokenizer is None or self._model is None:
            self._load_model()
        assert self._tokenizer is not None
        assert self._model is not None

        inputs = self._tokenizer(
            query, doc, return_tensors="pt", truncation=True, max_length=512
        )

        with torch.no_grad():
            outputs = self._model(**inputs)
            score = outputs.logits.squeeze().item()

        return score


# ============================================================
# 策略 2：BGE-Reranker 重排序
# ============================================================

class BGEReranker:
    """
    BGE-Reranker 重排序器：使用 BGE 系列重排序模型。

    原理：与 Cross-Encoder 类似，但使用专门优化的 BGE-Reranker 模型，
    在中文重排序任务上表现更好。

    特点：
    - 中文优化效果好
    - 支持多语言
    - 模型体积适中
    """

    def __init__(self, model_name: str = "BAAI/bge-reranker-large"):
        """
        初始化 BGE-Reranker。

        参数：
        - model_name (str): 模型名称
            - "BAAI/bge-reranker-large": 大型模型（推荐）
            - "BAAI/bge-reranker-base": 基础模型
            - "BAAI/bge-reranker-v2-m3": V2 多语言版本
        """
        self.model_name = model_name
        self._model = None
        self._tokenizer = None

    def _load_model(self):
        """延迟加载模型"""
        from FlagEmbedding import FlagReranker
        self._model = FlagReranker(self.model_name, use_fp16=True)

    def rerank(self, query: str, candidates: List[Tuple[str, str]], top_k: int = 10) -> List[RerankResult]:
        """
        对候选文档进行重排序。

        参数：
        - query (str): 查询文本
        - candidates (list[tuple]): (doc_id, text) 元组列表
        - top_k (int): 返回结果数

        返回：
        - list[RerankResult]: 重排序后的结果
        """
        if not candidates:
            return []

        if self._model is None:
            self._load_model()
        assert self._model is not None

        # BGE-Reranker 接受 (query, doc) 对的列表
        pairs = [(query, doc_text) for _, doc_text in candidates]
        scores = self._model.compute_score(pairs, normalize=True)

        # 确保 scores 是列表
        if isinstance(scores, float):
            scores = [scores]

        scored_candidates = []
        for i, (doc_id, text) in enumerate(candidates):
            score = scores[i] if i < len(scores) else 0.0
            scored_candidates.append(RerankResult(
                doc_id=doc_id,
                text=text,
                score=score,
                original_rank=i + 1,
            ))

        scored_candidates.sort(key=lambda x: x.score, reverse=True)
        return scored_candidates[:top_k]


# ============================================================
# 策略 3：Cohere Rerank（API 调用）
# ============================================================

class CohereReranker:
    """
    Cohere Rerank 重排序器：使用 Cohere API 进行重排序。

    特点：
    - 云端服务，无需本地模型
    - 多语言支持
    - 按量付费
    - 需要 API Key
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "rerank-multilingual-v3.0"):
        """
        初始化 Cohere Reranker。

        参数：
        - api_key (str): Cohere API Key
        - model (str): 模型名称
        """
        self.api_key = api_key or os.getenv("COHERE_API_KEY", "")
        self.model = model

    def rerank(self, query: str, candidates: List[Tuple[str, str]], top_k: int = 10) -> List[RerankResult]:
        """
        使用 Cohere API 进行重排序。

        参数：
        - query (str): 查询文本
        - candidates (list[tuple]): (doc_id, text) 元组列表
        - top_k (int): 返回结果数

        返回：
        - list[RerankResult]: 重排序后的结果
        """
        if not candidates:
            return []

        if not self.api_key:
            print("[警告] 未设置 COHERE_API_KEY")
            return self._fallback_rerank(candidates, top_k)

        try:
            import cohere
            client = cohere.Client(api_key=self.api_key)

            documents = [text for _, text in candidates]
            response = client.rerank(
                model=self.model,
                query=query,
                documents=documents,
                top_n=top_k,
            )

            scored_candidates = []
            for r in response.results:
                orig_idx = r.index
                doc_id, text = candidates[orig_idx]
                scored_candidates.append(RerankResult(
                    doc_id=doc_id,
                    text=text,
                    score=r.relevance_score,
                    original_rank=orig_idx + 1,
                ))

            return scored_candidates

        except Exception as e:
            print(f"[错误] Cohere API 调用失败: {e}")
            return self._fallback_rerank(candidates, top_k)

    def _fallback_rerank(self, candidates: List[Tuple[str, str]], top_k: int) -> List[RerankResult]:
        """API 不可用时的降级方案"""
        return [
            RerankResult(doc_id=did, text=text, score=0.5, original_rank=i + 1)
            for i, (did, text) in enumerate(candidates[:top_k])
        ]


# ============================================================
# 模块：统一重排序调度器
# ============================================================

class RerankingScheduler:
    """
    统一重排序调度器：管理和调度多种重排序策略。
    """

    STRATEGIES = {
        "cross_encoder": CrossEncoderReranker,
        "bge_reranker": BGEReranker,
        "cohere": CohereReranker,
    }

    def __init__(self, strategy: str = "bge_reranker", top_k: int = 5):
        """
        初始化调度器。

        参数：
        - strategy (str): 重排序策略
        - top_k (int): 返回结果数
        """
        self.strategy = strategy
        self.top_k = top_k
        self.reranker = self.STRATEGIES[strategy]()

    def rerank(self, query: str, candidates: List[Tuple[str, str]]) -> List[RerankResult]:
        """执行重排序"""
        return self.reranker.rerank(query, candidates, self.top_k)

    def two_stage_retrieve(self, query: str, initial_results: List[Tuple[str, str]]) -> List[RerankResult]:
        """
        两阶段检索：先用向量检索初筛，再用重排序精排。

        参数：
        - query (str): 查询文本
        - initial_results (list[tuple]): 初筛结果 (doc_id, text)

        返回：
        - list[RerankResult]: 精排后的结果
        """
        if not initial_results:
            return []

        return self.rerank(query, initial_results)


if __name__ == "__main__":
    print("=" * 60)
    print("  重排序技术演示")
    print("=" * 60)

    # 模拟初筛结果
    candidates = [
        ("doc_1", "Transformer 是一种基于自注意力机制的神经网络架构"),
        ("doc_2", "BERT 是基于 Transformer Encoder 的预训练模型"),
        ("doc_3", "GPT 是基于 Transformer Decoder 的生成模型"),
        ("doc_4", "注意力机制是 Transformer 的核心组件"),
        ("doc_5", "卷积神经网络主要用于图像处理任务"),
    ]

    query = "Transformer 的原理是什么？"

    print(f"\n查询: {query}")
    print(f"\n初筛结果（{len(candidates)} 个候选文档）:")
    for i, (doc_id, text) in enumerate(candidates, 1):
        print(f"  [{i}] {doc_id}: {text}")

    print("\n重排序策略对比:")
    print(f"{'策略':<20s} {'精度':<10s} {'速度':<10s} {'适用场景':<20s}")
    print("-" * 60)
    print(f"{'Cross-Encoder':<20s} {'高':<10s} {'慢':<10s} {'英文重排序':<20s}")
    print(f"{'BGE-Reranker':<20s} {'最高':<10s} {'中等':<10s} {'中文重排序':<20s}")
    print(f"{'Cohere Rerank':<20s} {'高':<10s} {'快（云端）':<10s} {'多语言/免部署':<20s}")
