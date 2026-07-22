"""
hybrid_search.py — 混合检索实现
包含 BM25 全文检索、向量检索、元数据过滤以及混合排序。
用于教学演示，帮助理解混合检索的原理和实现方式。
"""
import math
from collections import Counter
from typing import Optional
from dataclasses import dataclass, field


# ============================================================
# 模块：BM25 全文检索
# 说明：基于词频和逆文档频率的全文检索算法
# 优点：对关键词匹配精确，擅长处理专有名词
# 缺点：无法理解语义相似度
# ============================================================

class BM25Search:
    """
    BM25（Best Matching 25）全文检索实现。

    原理：
    1. 对每个文档分词，建立倒排索引
    2. 对查询词分词，计算每个文档的 BM25 分数
    3. 分数越高表示匹配度越好

    BM25 公式：
    Score(D, Q) = Σ IDF(qᵢ) × (TF(qᵢ, D) × (k₁ + 1)) / (TF(qᵢ, D) + k₁ × (1 - b + b × |D|/avgdl))

    参数：
    - k1: 控制词频饱和点（默认 1.5）
    - b: 控制文档长度归一化（默认 0.75）
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        初始化 BM25 检索器。

        参数：
        - k1 (float): 词频饱和参数
        - b (float): 文档长度归一化参数
        """
        self.k1 = k1
        self.b = b
        # 文档存储
        self.documents: dict[str, list[str]] = {}
        # 逆文档频率
        self.idf: dict[str, float] = {}
        # 平均文档长度
        self.avg_doc_length: float = 0.0

    def add_document(self, doc_id: str, tokens: list[str]) -> None:
        """
        添加文档到索引。

        参数：
        - doc_id (str): 文档唯一标识
        - tokens (list[str]): 分词后的词列表
        """
        self.documents[doc_id] = tokens
        self._rebuild_index()

    def _rebuild_index(self) -> None:
        """重建 BM25 索引（IDF 和平均文档长度）"""
        n_docs = len(self.documents)
        if n_docs == 0:
            return

        # 计算平均文档长度
        total_length = sum(len(tokens) for tokens in self.documents.values())
        self.avg_doc_length = total_length / n_docs

        # 计算每个词的文档频率
        doc_freq: dict[str, int] = Counter()
        for tokens in self.documents.values():
            unique_tokens = set(tokens)
            for token in unique_tokens:
                doc_freq[token] += 1

        # 计算 IDF
        for term, df in doc_freq.items():
            # IDF = log((N - df + 0.5) / (df + 0.5) + 1)
            self.idf[term] = math.log(
                (n_docs - df + 0.5) / (df + 0.5) + 1
            )

    def search(self, query_tokens: list[str], top_k: int = 10) -> list[tuple[str, float]]:
        """
        搜索最相关的文档。

        参数：
        - query_tokens (list[str]): 查询词分词列表
        - top_k (int): 返回结果数

        返回：
        - list[(doc_id, score)]: 文档 ID 和 BM25 分数
        """
        if not self.documents:
            return []

        results = []
        for doc_id, tokens in self.documents.items():
            score = self._score_document(doc_id, tokens, query_tokens)
            if score > 0:
                results.append((doc_id, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def _score_document(
        self, doc_id: str, tokens: list[str], query_tokens: list[str]
    ) -> float:
        """计算单个文档的 BM25 分数"""
        doc_length = len(tokens)
        term_freq = Counter(tokens)
        score = 0.0

        for query_term in query_tokens:
            if query_term not in self.idf:
                continue

            tf = term_freq.get(query_term, 0)
            idf = self.idf[query_term]

            # BM25 核心公式
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (
                1 - self.b + self.b * (doc_length / self.avg_doc_length)
            )
            score += idf * (numerator / denominator)

        return score


# ============================================================
# 模块：混合检索器
# 说明：将向量检索和 BM25 检索结果融合
# ============================================================

@dataclass
class SearchResult:
    """检索结果"""
    doc_id: str
    vector_score: float = 0.0
    bm25_score: float = 0.0
    hybrid_score: float = 0.0
    metadata: dict = field(default_factory=dict)


class HybridSearcher:
    """
    混合检索器：融合向量检索和 BM25 全文检索。

    原理：
    1. 分别执行向量检索和 BM25 检索
    2. 对两种分数做归一化
    3. 按权重加权融合：hybrid = α × vector + (1-α) × bm25
    4. 可选：应用元数据过滤
    """

    def __init__(self, alpha: float = 0.7):
        """
        初始化混合检索器。

        参数：
        - alpha (float): 向量检索权重（0-1）
            alpha=1 表示纯向量检索
            alpha=0 表示纯 BM25 检索
            alpha=0.7 表示向量权重 70%，BM25 权重 30%
        """
        self.alpha = alpha
        self.bm25 = BM25Search()
        # 文档元数据存储
        self.metadata: dict[str, dict] = {}

    def add_document(
        self,
        doc_id: str,
        tokens: list[str],
        vector: list[float],
        metadata: Optional[dict] = None,
    ) -> None:
        """
        添加文档（同时用于向量检索和 BM25 检索）。

        参数：
        - doc_id (str): 文档 ID
        - tokens (list[str]): 分词列表（用于 BM25）
        - vector (list[float]): 嵌入向量（用于向量检索）
        - metadata (dict): 元数据（用于过滤）
        """
        self.bm25.add_document(doc_id, tokens)
        self.metadata[doc_id] = metadata or {}

    def search(
        self,
        query_vector: list[float],
        query_tokens: list[str],
        top_k: int = 10,
        metadata_filter: Optional[dict] = None,
    ) -> list[SearchResult]:
        """
        执行混合检索。

        参数：
        - query_vector (list[float]): 查询向量
        - query_tokens (list[str]): 查询分词
        - top_k (int): 返回结果数
        - metadata_filter (dict): 元数据过滤条件

        返回：
        - list[SearchResult]: 混合排序结果
        """
        # 1. 向量检索
        vector_results = self._vector_search(query_vector, top_k)
        # 2. BM25 检索
        bm25_results = self.bm25.search(query_tokens, top_k)

        # 3. 合并所有候选文档
        all_doc_ids = set()
        for doc_id, _ in vector_results:
            all_doc_ids.add(doc_id)
        for doc_id, _ in bm25_results:
            all_doc_ids.add(doc_id)

        # 4. 构建分数映射
        vector_scores = dict(vector_results)
        bm25_scores = dict(bm25_results)

        # 5. 归一化分数
        max_vector = max(vector_scores.values()) if vector_scores else 1.0
        max_bm25 = max(bm25_scores.values()) if bm25_scores else 1.0

        results = []
        for doc_id in all_doc_ids:
            # 元数据过滤
            if metadata_filter:
                meta = self.metadata.get(doc_id, {})
                if not self._matches_filter(meta, metadata_filter):
                    continue

            v_score = vector_scores.get(doc_id, 0.0) / max_vector
            b_score = bm25_scores.get(doc_id, 0.0) / max_bm25
            hybrid = self.alpha * v_score + (1 - self.alpha) * b_score

            results.append(SearchResult(
                doc_id=doc_id,
                vector_score=v_score,
                bm25_score=b_score,
                hybrid_score=hybrid,
                metadata=self.metadata.get(doc_id, {}),
            ))

        results.sort(key=lambda r: r.hybrid_score, reverse=True)
        return results[:top_k]

    def _vector_search(
        self, query_vector: list[float], top_k: int
    ) -> list[tuple[str, float]]:
        """简化版向量检索（余弦相似度）"""
        # 实际应用中这里会调用向量数据库
        # 此处返回模拟结果用于演示
        return []

    def _matches_filter(self, metadata: dict, filter_dict: dict) -> bool:
        """检查文档元数据是否满足过滤条件"""
        for key, value in filter_dict.items():
            if metadata.get(key) != value:
                return False
        return True
