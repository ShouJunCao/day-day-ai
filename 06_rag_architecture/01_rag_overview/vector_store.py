"""
vector_store.py — 简易向量存储实现
使用内存存储向量，支持相似度检索。适用于教学演示。
"""
import math
from typing import Optional


class MemoryVectorStore:
    """
    内存向量存储：将向量和文本存储在内存中，
    通过余弦相似度进行检索。
    """

    def __init__(self) -> None:
        self._vectors: list[list[float]] = []
        self._texts: list[str] = []
        self._metadata: list[dict] = []

    def add(self, vector: list[float], text: str, metadata: Optional[dict] = None) -> None:
        """
        添加一个向量到存储中。

        参数：
        - vector (list[float]): 嵌入向量
        - text (str): 对应的文本
        - metadata (dict): 元数据（可选）
        """
        self._vectors.append(vector)
        self._texts.append(text)
        self._metadata.append(metadata or {})

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """
        计算余弦相似度。

        公式：cos = (a · b) / (|a| × |b|)
        """
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    def search(self, query_vector: list[float], top_k: int = 3) -> list[dict]:
        """
        检索最相似的 K 个向量。

        参数：
        - query_vector (list[float]): 查询向量
        - top_k (int): 返回结果数

        返回：
        - list[dict]: 包含文本、相似度和元数据的结果列表
        """
        scores = []
        for i, vec in enumerate(self._vectors):
            sim = self._cosine_similarity(query_vector, vec)
            scores.append({
                "text": self._texts[i],
                "similarity": sim,
                "metadata": self._metadata[i],
            })
        # 按相似度降序排序
        scores.sort(key=lambda x: x["similarity"], reverse=True)
        return scores[:top_k]


if __name__ == "__main__":
    store = MemoryVectorStore()
    store.add([0.8, 0.6, 0.0], "人工智能概述", {"category": "AI"})
    store.add([0.7, 0.7, 0.0], "机器学习基础", {"category": "ML"})
    store.add([0.0, 0.0, 0.9], "体育新闻", {"category": "News"})

    results = store.search([0.8, 0.5, 0.0], top_k=2)
    for r in results:
        print(f"  {r['text']}: {r['similarity']:.4f} [{r['metadata']['category']}]")
