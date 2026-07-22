"""
vector_indexes.py — 向量索引算法实现
包含 HNSW、IVF、PQ 三种主流向量索引的简化实现。
用于教学演示，帮助理解各索引的工作原理和性能特征。
"""
import math
import random
from typing import Optional
from dataclasses import dataclass, field


# ============================================================
# 模块：向量距离计算工具
# ============================================================

def euclidean_distance(vec1: list[float], vec2: list[float]) -> float:
    """
    计算两个向量的欧氏距离。
    
    公式：d = √(Σ(aᵢ - bᵢ)²)
    
    参数：
    - vec1 (list[float]): 第一个向量
    - vec2 (list[float]): 第二个向量
    
    返回：
    - float: 欧氏距离值
    """
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(vec1, vec2)))


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """
    计算两个向量的余弦相似度。
    
    公式：cos = (a · b) / (|a| × |b|)
    
    参数：
    - vec1 (list[float]): 第一个向量
    - vec2 (list[float]): 第二个向量
    
    返回：
    - float: 余弦相似度，范围 [-1, 1]
    """
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


# ============================================================
# 模块：HNSW 索引（Hierarchical Navigable Small World）
# 说明：多层图结构，每层是下一层的子集
#      从顶层（节点少）开始粗搜索，逐层细化
# 优点：速度快、精度高、适合各种规模
# 缺点：内存占用大（存储图结构）
# ============================================================

@dataclass
class HNSWNode:
    """
    HNSW 图节点。

    属性：
    - vector: 节点对应的向量
    - node_id: 节点唯一标识
    - layer: 节点所在的最高层（0 为基础层）
    - neighbors: 每层的邻居节点列表
    """
    vector: list[float]
    node_id: str
    layer: int
    neighbors: list[list[str]] = field(default_factory=list)

    def __post_init__(self):
        """初始化每层的邻居列表"""
        self.neighbors = [[] for _ in range(self.layer + 1)]


class HNSWIndex:
    """
    HNSW（分层可导航小世界）索引的简化实现。

    原理：
    - 构建多层图结构，顶层节点少、底层节点多
    - 搜索时从顶层开始，找到最近节点后下沉到下一层
    - 逐层逼近，最终在底层找到最相似的 K 个节点

    参数：
    - M: 每层每个节点的最大连接数（默认 16）
    - max_layer: 最大层数（默认 4）
    """

    def __init__(self, dimension: int, M: int = 16, max_layer: int = 4):
        """
        初始化 HNSW 索引。

        参数：
        - dimension (int): 向量维度
        - M (int): 每层最大连接数
        - max_layer (int): 最大层数
        """
        self.dimension = dimension
        self.M = M
        self.max_layer = max_layer
        # 节点存储
        self.nodes: dict[str, HNSWNode] = {}
        # 入口节点（顶层搜索起点）
        self.entry_point: Optional[str] = None

    def _random_layer(self) -> int:
        """随机生成节点的层数，指数分布（高层节点少）"""
        layer = 0
        while random.random() < 0.5 and layer < self.max_layer:
            layer += 1
        return layer

    def insert(self, vector: list[float], node_id: str) -> None:
        """
        插入一个向量节点。

        参数：
        - vector: 要插入的向量
        - node_id: 节点唯一标识
        """
        # 随机分配层数
        node_layer = self._random_layer()
        # 创建节点
        node = HNSWNode(vector=vector, node_id=node_id, layer=node_layer)
        self.nodes[node_id] = node

        # 如果这是第一个节点，设为入口
        if self.entry_point is None:
            self.entry_point = node_id
            return

        # 简化版：将新节点连接到每层距离最近的 M 个已有节点
        for layer in range(node_layer + 1):
            # 找到该层所有已有节点
            existing = [
                nid for nid, n in self.nodes.items()
                if n.layer >= layer and nid != node_id
            ]
            # 按距离排序，取最近的 M 个
            existing.sort(
                key=lambda nid: euclidean_distance(
                    self.nodes[nid].vector, vector
                )
            )
            nearest = existing[:self.M]
            # 双向连接
            for nid in nearest:
                if layer < len(self.nodes[nid].neighbors):
                    if node_id not in self.nodes[nid].neighbors[layer]:
                        self.nodes[nid].neighbors[layer].append(node_id)
                if layer < len(node.neighbors):
                    if nid not in node.neighbors[layer]:
                        node.neighbors[layer].append(nid)

    def search(self, query_vector: list[float], top_k: int = 5) -> list[tuple[str, float]]:
        """
        搜索最相似的 K 个向量。

        参数：
        - query_vector: 查询向量
        - top_k: 返回结果数

        返回：
        - list[(node_id, distance)]: 节点 ID 和距离的列表，按距离升序
        """
        if not self.nodes:
            return []

        # 从入口节点开始搜索
        current_id = self.entry_point

        # 从顶层逐层下沉到底层
        for layer in range(self.max_layer, -1, -1):
            changed = True
            while changed:
                changed = False
                current_node = self.nodes.get(current_id)
                if not current_node or layer >= len(current_node.neighbors):
                    break
                # 在当前层的邻居中找更近的节点
                for neighbor_id in current_node.neighbors[layer]:
                    neighbor = self.nodes.get(neighbor_id)
                    if not neighbor:
                        continue
                    current_dist = euclidean_distance(
                        self.nodes[current_id].vector, query_vector
                    )
                    neighbor_dist = euclidean_distance(
                        neighbor.vector, query_vector
                    )
                    if neighbor_dist < current_dist:
                        current_id = neighbor_id
                        changed = True

        # 在底层（第 0 层）找 top_k 个最近节点
        bottom_node = self.nodes.get(current_id)
        if not bottom_node:
            return []

        candidates = {current_id}
        # 收集第 0 层邻居
        if bottom_node.neighbors:
            candidates.update(bottom_node.neighbors[0])

        # 计算所有候选节点的距离并排序
        results = []
        for nid in candidates:
            node = self.nodes.get(nid)
            if node:
                dist = euclidean_distance(node.vector, query_vector)
                results.append((nid, dist))

        results.sort(key=lambda x: x[1])
        return results[:top_k]


# ============================================================
# 模块：IVF 索引（Inverted File Index，倒排文件索引）
# 说明：先对向量空间聚类，搜索时只在相关簇中查找
# 优点：内存占用小、适合大数据量
# 缺点：需要训练（聚类）、精度略低于 HNSW
# ============================================================

class IVFIndex:
    """
    IVF（倒排文件）索引的简化实现。

    原理：
    1. 训练阶段：用 K-Means 将所有向量聚类为 nlist 个簇
    2. 索引阶段：每个向量归入最近的簇，建立倒排表
    3. 搜索阶段：
       a. 找到查询向量最近的 nprobe 个簇
       b. 只在这些簇中暴力搜索
       c. 返回最近的结果

    参数：
    - nlist: 聚类中心数（簇数）
    - nprobe: 搜索时探查的簇数
    """

    def __init__(self, dimension: int, nlist: int = 100, nprobe: int = 10):
        """
        初始化 IVF 索引。

        参数：
        - dimension (int): 向量维度
        - nlist (int): 聚类中心数
        - nprobe (int): 搜索时探查的簇数
        """
        self.dimension = dimension
        self.nlist = nlist
        self.nprobe = nprobe
        # 聚类中心
        self.centroids: list[list[float]] = []
        # 倒排表：簇 ID → 节点 ID 列表
        self.inverted_lists: dict[int, list[str]] = {}
        # 节点存储
        self.nodes: dict[str, list[float]] = {}
        # 是否已训练
        self.is_trained = False

    def train(self, vectors: list[list[float]]) -> None:
        """
        训练 IVF 索引（K-Means 聚类）。

        参数：
        - vectors: 训练向量列表
        """
        if len(vectors) < self.nlist:
            # 向量太少，直接用所有向量作为中心
            self.centroids = vectors[:][:]
        else:
            # 简化 K-Means：随机选 nlist 个向量作为初始中心
            random.seed(42)  # 固定种子保证可重复
            self.centroids = random.sample(vectors, self.nlist)

            # 简化版：只做一轮分配
            for vec in vectors:
                # 找到最近的聚类中心
                distances = [
                    euclidean_distance(vec, c) for c in self.centroids
                ]
                cluster_id = distances.index(min(distances))
                if cluster_id not in self.inverted_lists:
                    self.inverted_lists[cluster_id] = []

        self.is_trained = True

    def insert(self, vector: list[float], node_id: str) -> None:
        """
        插入向量到倒排表中。

        参数：
        - vector: 要插入的向量
        - node_id: 节点唯一标识
        """
        self.nodes[node_id] = vector
        if not self.is_trained:
            return

        # 找到最近的聚类中心
        distances = [
            euclidean_distance(vector, c) for c in self.centroids
        ]
        cluster_id = distances.index(min(distances))

        if cluster_id not in self.inverted_lists:
            self.inverted_lists[cluster_id] = []
        self.inverted_lists[cluster_id].append(node_id)

    def search(self, query_vector: list[float], top_k: int = 5) -> list[tuple[str, float]]:
        """
        搜索最相似的 K 个向量。

        参数：
        - query_vector: 查询向量
        - top_k: 返回结果数
        """
        if not self.is_trained or not self.centroids:
            return []

        # 找到最近的 nprobe 个簇
        centroid_dists = [
            euclidean_distance(query_vector, c)
            for c in self.centroids
        ]
        sorted_clusters = sorted(
            range(len(centroid_dists)),
            key=lambda i: centroid_dists[i]
        )
        probe_clusters = sorted_clusters[:self.nprobe]

        # 收集这些簇中的所有节点
        candidates = set()
        for cluster_id in probe_clusters:
            if cluster_id in self.inverted_lists:
                candidates.update(self.inverted_lists[cluster_id])

        # 计算距离并排序
        results = []
        for nid in candidates:
            if nid in self.nodes:
                dist = euclidean_distance(self.nodes[nid], query_vector)
                results.append((nid, dist))

        results.sort(key=lambda x: x[1])
        return results[:top_k]


# ============================================================
# 模块：PQ 索引（Product Quantization，乘积量化）
# 说明：将向量分段，每段独立量化为码本中的一个码字
# 优点：内存占用极小（压缩比可达 100 倍）
# 缺点：有量化误差、精度低于 HNSW 和 IVF
# ============================================================

class PQIndex:
    """
    PQ（乘积量化）索引的简化实现。

    原理：
    1. 将 D 维向量分成 m 段，每段 D/m 维
    2. 对每段独立运行 K-Means，生成 k 个聚类中心（码本）
    3. 每个向量用 m 个码字 ID 表示（压缩存储）
    4. 搜索时用码本预计算距离表，加速查询

    参数：
    - m: 分段数
    - k: 每段的码本大小（聚类中心数）
    """

    def __init__(self, dimension: int, m: int = 4, k: int = 256):
        """
        初始化 PQ 索引。

        参数：
        - dimension (int): 向量维度
        - m (int): 分段数
        - k (int): 每段码本大小
        """
        self.dimension = dimension
        self.m = m
        self.k = k
        self.sub_dim = dimension // m  # 每段维度
        # 码本：每段一个码本，每个码本包含 k 个中心向量
        self.codebooks: list[list[list[float]]] = []
        # 压缩后的编码：node_id → [码字ID列表]
        self.encoded: dict[str, list[int]] = {}
        # 原始向量存储（用于精确搜索）
        self.nodes: dict[str, list[float]] = {}
        self.is_trained = False

    def _split_vector(self, vector: list[float]) -> list[list[float]]:
        """将向量切分为 m 段"""
        return [
            vector[i * self.sub_dim: (i + 1) * self.sub_dim]
            for i in range(self.m)
        ]

    def train(self, vectors: list[list[float]]) -> None:
        """
        训练 PQ 索引（对每段运行 K-Means）。

        参数：
        - vectors: 训练向量列表
        """
        random.seed(42)
        self.codebooks = []

        for seg_idx in range(self.m):
            # 提取该段的所有子向量
            sub_vectors = [
                v[seg_idx * self.sub_dim: (seg_idx + 1) * self.sub_dim]
                for v in vectors
            ]

            # 简化 K-Means：随机选 k 个作为初始中心
            n_centers = min(self.k, len(sub_vectors))
            centers = random.sample(sub_vectors, n_centers)

            self.codebooks.append(centers)

        self.is_trained = True

    def encode(self, vector: list[float]) -> list[int]:
        """
        将向量编码为码字 ID 列表。

        参数：
        - vector: 要编码的向量

        返回：
        - list[int]: m 个码字 ID
        """
        if not self.is_trained:
            return []

        sub_vectors = self._split_vector(vector)
        codes = []

        for seg_idx, sub_vec in enumerate(sub_vectors):
            # 找到该段最近的码本中心
            distances = [
                euclidean_distance(sub_vec, center)
                for center in self.codebooks[seg_idx]
            ]
            code_id = distances.index(min(distances))
            codes.append(code_id)

        return codes

    def insert(self, vector: list[float], node_id: str) -> None:
        """插入向量并编码"""
        self.nodes[node_id] = vector
        if self.is_trained:
            self.encoded[node_id] = self.encode(vector)

    def search(self, query_vector: list[float], top_k: int = 5) -> list[tuple[str, float]]:
        """
        搜索最相似的 K 个向量（使用预计算距离表加速）。

        参数：
        - query_vector: 查询向量
        - top_k: 返回结果数
        """
        if not self.is_trained:
            return []

        # 预计算查询向量每段到各码本中心的距离表
        query_subs = self._split_vector(query_vector)
        distance_table = []
        for seg_idx, query_sub in enumerate(query_subs):
            table = [
                euclidean_distance(query_sub, center)
                for center in self.codebooks[seg_idx]
            ]
            distance_table.append(table)

        # 用距离表快速计算所有节点的近似距离（ADC：Asymmetric Distance Computation）
        results = []
        for node_id, codes in self.encoded.items():
            approx_dist = 0.0
            for seg_idx, code_id in enumerate(codes):
                approx_dist += distance_table[seg_idx][code_id]
            results.append((node_id, approx_dist))

        results.sort(key=lambda x: x[1])
        return results[:top_k]
