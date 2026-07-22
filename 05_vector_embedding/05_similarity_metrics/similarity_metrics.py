"""
similarity_metrics.py — 相似度度量方法实现
包含余弦相似度、欧氏距离、点积、曼哈顿距离等常用度量方法。
用于教学演示，帮助理解各度量方法的原理和适用场景。
"""
import math
from typing import Optional


# ============================================================
# 模块：余弦相似度（Cosine Similarity）
# 说明：衡量两个向量的夹角余弦值，范围 [-1, 1]
#      值越大表示方向越接近，与向量长度无关
# 适用：文本相似度、语义搜索
# ============================================================

def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """
    计算两个向量的余弦相似度。

    公式：cos(a, b) = (a · b) / (|a| × |b|)

    参数：
    - vec1 (list[float]): 第一个向量
    - vec2 (list[float]): 第二个向量

    返回：
    - float: 余弦相似度，范围 [-1, 1]
        1.0 表示完全相同方向
        0.0 表示正交（无关）
        -1.0 表示完全相反方向
    """
    # 计算点积
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    # 计算模长
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    # 防止除以 0
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot_product / (norm1 * norm2)


# ============================================================
# 模块：欧氏距离（Euclidean Distance）
# 说明：衡量两个向量在空间中的直线距离
#      值越小表示越相似
# 适用：聚类分析、图像检索
# ============================================================

def euclidean_distance(vec1: list[float], vec2: list[float]) -> float:
    """
    计算两个向量的欧氏距离。

    公式：d = √(Σ(aᵢ - bᵢ)²)

    参数：
    - vec1 (list[float]): 第一个向量
    - vec2 (list[float]): 第二个向量

    返回：
    - float: 欧氏距离，值越小表示越相似
    """
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(vec1, vec2)))


# ============================================================
# 模块：点积（Dot Product / Inner Product）
# 说明：两个向量对应位置相乘后求和
#      值越大表示越相似
# 适用：已归一化的向量（此时等价于余弦相似度）
# ============================================================

def dot_product(vec1: list[float], vec2: list[float]) -> float:
    """
    计算两个向量的点积（内积）。

    公式：dot = Σ(aᵢ × bᵢ)

    参数：
    - vec1 (list[float]): 第一个向量
    - vec2 (list[float]): 第二个向量

    返回：
    - float: 点积值
    """
    return sum(a * b for a, b in zip(vec1, vec2))


# ============================================================
# 模块：曼哈顿距离（Manhattan Distance / L1 Distance）
# 说明：两个向量在各维度上绝对差之和
#      值越小表示越相似
# 适用：高维稀疏数据、鲁棒性要求高的场景
# ============================================================

def manhattan_distance(vec1: list[float], vec2: list[float]) -> float:
    """
    计算两个向量的曼哈顿距离（L1 距离）。

    公式：d = Σ|aᵢ - bᵢ|

    参数：
    - vec1 (list[float]): 第一个向量
    - vec2 (list[float]): 第二个向量

    返回：
    - float: 曼哈顿距离
    """
    return sum(abs(a - b) for a, b in zip(vec1, vec2))


# ============================================================
# 模块：相似度计算器类
# 说明：封装所有相似度度量方法，提供统一接口
# ============================================================

class SimilarityCalculator:
    """
    相似度计算器：提供多种向量距离和相似度度量方法。
    """

    @staticmethod
    def cosine(vec1: list[float], vec2: list[float]) -> float:
        """
        余弦相似度：衡量方向相似性。
        范围 [-1, 1]，值越大越相似。
        """
        return cosine_similarity(vec1, vec2)

    @staticmethod
    def euclidean(vec1: list[float], vec2: list[float]) -> float:
        """
        欧氏距离：衡量空间距离。
        范围 [0, ∞)，值越小越相似。
        """
        return euclidean_distance(vec1, vec2)

    @staticmethod
    def dot(vec1: list[float], vec2: list[float]) -> float:
        """
        点积：衡量向量乘积和。
        范围 (-∞, ∞)，值越大越相似（对已归一化向量）。
        """
        return dot_product(vec1, vec2)

    @staticmethod
    def manhattan(vec1: list[float], vec2: list[float]) -> float:
        """
        曼哈顿距离：各维度绝对差之和。
        范围 [0, ∞)，值越小越相似。
        """
        return manhattan_distance(vec1, vec2)

    @staticmethod
    def compare_all(vec1: list[float], vec2: list[float]) -> dict[str, float]:
        """
        计算所有度量方法的结果。

        参数：
        - vec1 (list[float]): 第一个向量
        - vec2 (list[float]): 第二个向量

        返回：
        - dict[str, float]: 各度量方法的结果
        """
        return {
            "cosine_similarity": cosine_similarity(vec1, vec2),
            "euclidean_distance": euclidean_distance(vec1, vec2),
            "dot_product": dot_product(vec1, vec2),
            "manhattan_distance": manhattan_distance(vec1, vec2),
        }


# ============================================================
# 模块：向量归一化工具
# 说明：将向量归一化为单位向量（模长为 1）
# ============================================================

def normalize_vector(vec: list[float]) -> list[float]:
    """
    将向量归一化为单位向量。

    公式：normalized = vec / |vec|

    参数：
    - vec (list[float]): 输入向量

    返回：
    - list[float]: 归一化后的单位向量
    """
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        return vec[:]
    return [v / norm for v in vec]
