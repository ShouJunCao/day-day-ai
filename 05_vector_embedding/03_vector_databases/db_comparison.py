"""
db_comparison.py — 向量数据库对比工具
对比 FAISS、Milvus、Qdrant、Chroma、Pinecone、pgvector 的关键特性。
提供选型决策辅助、成本估算、性能模拟等功能。
"""
import math
from dataclasses import dataclass, field
from typing import Optional


# ============================================================
# 模块：向量数据库规格定义
# ============================================================

@dataclass
class VectorDBSpec:
    """
    向量数据库规格：封装数据库的关键参数。

    属性：
    - name (str): 数据库名称
    - type (str): 类型（本地库/独立服务/全托管/扩展）
    - language (str): 主要开发语言
    - max_vectors (str): 最大向量规模描述
    - distributed (bool): 是否支持分布式
    - persistence (bool): 是否内置持久化
    - filtering (bool): 是否支持元数据过滤
    - cloud_managed (bool): 是否全托管云服务
    - open_source (bool): 是否开源
    - learning_curve (str): 学习曲线（低/中/高）
    - best_for (str): 最佳适用场景
    """
    # 数据库名称
    name: str
    # 类型：本地库、独立服务、全托管、扩展
    type: str
    # 主要开发语言
    language: str
    # 最大向量规模描述
    max_vectors: str
    # 是否支持分布式
    distributed: bool = False
    # 是否内置持久化
    persistence: bool = False
    # 是否支持元数据过滤
    filtering: bool = False
    # 是否全托管云服务
    cloud_managed: bool = False
    # 是否开源
    open_source: bool = True
    # 学习曲线
    learning_curve: str = "中"
    # 最佳适用场景
    best_for: str = ""


# ============================================================
# 模块：预定义的向量数据库规格
# ============================================================

VECTOR_DATABASES = [
    VectorDBSpec(
        name="FAISS",
        type="本地库",
        language="C++ (Python 接口)",
        max_vectors="10 亿（单机）",
        distributed=False,
        persistence=False,
        filtering=False,
        cloud_managed=False,
        open_source=True,
        learning_curve="低",
        best_for="单机、对延迟敏感的中小规模检索",
    ),
    VectorDBSpec(
        name="Chroma",
        type="嵌入式数据库",
        language="Python/Rust",
        max_vectors="百万级（单机）",
        distributed=False,
        persistence=True,
        filtering=True,
        cloud_managed=False,
        open_source=True,
        learning_curve="低",
        best_for="快速原型、本地开发、小型项目",
    ),
    VectorDBSpec(
        name="Qdrant",
        type="独立服务",
        language="Rust",
        max_vectors="10 亿（集群）",
        distributed=True,
        persistence=True,
        filtering=True,
        cloud_managed=True,
        open_source=True,
        learning_curve="中",
        best_for="生产环境、需要复杂过滤的检索",
    ),
    VectorDBSpec(
        name="Milvus",
        type="独立服务",
        language="Go/C++",
        max_vectors="100 亿（集群）",
        distributed=True,
        persistence=True,
        filtering=True,
        cloud_managed=True,
        open_source=True,
        learning_curve="高",
        best_for="大规模向量检索、企业级生产环境",
    ),
    VectorDBSpec(
        name="Pinecone",
        type="全托管云服务",
        language="SaaS",
        max_vectors="百亿级（自动扩展）",
        distributed=True,
        persistence=True,
        filtering=True,
        cloud_managed=True,
        open_source=False,
        learning_curve="低",
        best_for="不想运维基础设施的团队",
    ),
    VectorDBSpec(
        name="pgvector",
        type="PostgreSQL 扩展",
        language="C",
        max_vectors="千万级（单节点）",
        distributed=False,
        persistence=True,
        filtering=True,
        cloud_managed=False,
        open_source=True,
        learning_curve="中",
        best_for="已有 PostgreSQL、需要关系+向量联合查询",
    ),
]


# ============================================================
# 模块：向量数据库对比分析器
# ============================================================

class VectorDBComparator:
    """
    向量数据库对比分析器。

    功能：
    - 按不同维度筛选和排序数据库
    - 估算存储成本
    - 生成选型建议
    """

    def __init__(self, databases: Optional[list[VectorDBSpec]] = None):
        """
        初始化对比分析器。

        参数：
        - databases (list[VectorDBSpec]): 要对比的数据库列表
        """
        self.databases = databases or VECTOR_DATABASES

    def filter_open_source(self) -> list[VectorDBSpec]:
        """筛选开源数据库"""
        return [db for db in self.databases if db.open_source]

    def filter_distributed(self) -> list[VectorDBSpec]:
        """筛选支持分布式的数据库"""
        return [db for db in self.databases if db.distributed]

    def filter_by_type(self, db_type: str) -> list[VectorDBSpec]:
        """
        按类型筛选。

        参数：
        - db_type (str): 数据库类型，如 "本地库"、"独立服务"、"全托管云服务"
        """
        return [db for db in self.databases if db.type == db_type]

    def get_recommendation(self, requirements: dict) -> list[VectorDBSpec]:
        """
        根据需求推荐数据库。

        参数：
        - requirements (dict): 需求字典
            - "need_distributed": 是否需要分布式
            - "open_source_only": 是否只考虑开源
            - "has_postgres": 是否已有 PostgreSQL
            - "no_ops": 是否不想运维
            - "scale": 数据规模（"small"/"medium"/"large"）

        返回：
        - list[VectorDBSpec]: 满足条件的数据库列表
        """
        candidates = list(self.databases)

        # 需要分布式
        if requirements.get("need_distributed"):
            candidates = [db for db in candidates if db.distributed]

        # 只考虑开源
        if requirements.get("open_source_only"):
            candidates = [db for db in candidates if db.open_source]

        # 不想运维 → 全托管
        if requirements.get("no_ops"):
            candidates = [db for db in candidates if db.cloud_managed]

        # 已有 PostgreSQL → 优先 pgvector
        if requirements.get("has_postgres"):
            candidates = [db for db in candidates if db.name == "pgvector"] + \
                         [db for db in candidates if db.name != "pgvector"]

        return candidates

    def estimate_storage_cost(self, num_vectors: int, dimension: int) -> dict[str, str]:
        """
        估算存储成本。

        参数：
        - num_vectors (int): 向量数量
        - dimension (int): 向量维度

        返回：
        - dict[str, str]: 数据库名 → 存储大小（人类可读）的映射
        """
        # 每个 float32 占 4 字节
        bytes_per_vector = dimension * 4
        total_bytes = num_vectors * bytes_per_vector

        results = {}
        for db in self.databases:
            # 不同数据库有额外开销
            overhead = {
                "FAISS": 1.0,      # 纯向量，几乎无额外开销
                "Chroma": 1.5,     # 元数据 + 向量
                "Qdrant": 1.8,     # HNSW 图结构 + 元数据
                "Milvus": 2.0,     # 索引 + 元数据 + 副本
                "Pinecone": 2.5,   # 全托管，含索引和冗余
                "pgvector": 2.0,   # PostgreSQL 页面开销
            }
            factor = overhead.get(db.name, 1.5)
            estimated_bytes = int(total_bytes * factor)
            results[db.name] = self._human_readable_size(estimated_bytes)

        return results

    @staticmethod
    def _human_readable_size(size_bytes: int) -> str:
        """将字节数转换为人类可读的大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 ** 2:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 ** 3:
            return f"{size_bytes / 1024 ** 2:.1f} MB"
        elif size_bytes < 1024 ** 4:
            return f"{size_bytes / 1024 ** 3:.1f} GB"
        else:
            return f"{size_bytes / 1024 ** 4:.2f} TB"


# ============================================================
# 模块：演示函数
# ============================================================

def demo_db_comparison():
    """演示数据库对比功能"""
    print("=" * 60)
    print("  向量数据库对比 — Database Comparison 演示")
    print("=" * 60)

    comparator = VectorDBComparator()

    # 按类型对比
    print("\n1. 按类型分类:")
    for db_type in ["本地库", "嵌入式数据库", "独立服务", "全托管云服务", "PostgreSQL 扩展"]:
        dbs = comparator.filter_by_type(db_type)
        if dbs:
            names = ", ".join(db.name for db in dbs)
            print(f"   {db_type}: {names}")

    # 开源 vs 闭源
    print("\n2. 开源 vs 闭源:")
    oss = comparator.filter_open_source()
    print(f"   开源 ({len(oss)}): {', '.join(db.name for db in oss)}")
    closed = [db for db in comparator.databases if not db.open_source]
    if closed:
        print(f"   闭源 ({len(closed)}): {', '.join(db.name for db in closed)}")

    # 存储成本估算
    print("\n3. 存储成本估算（100 万向量 × 768 维）:")
    costs = comparator.estimate_storage_cost(1_000_000, 768)
    for db_name, size in costs.items():
        print(f"   {db_name:15s} → {size}")

    # 场景推荐
    print("\n4. 场景推荐:")

    # 场景 1：快速原型
    rec1 = comparator.get_recommendation({"open_source_only": True})
    print("   快速原型（开源优先）:")
    for db in rec1[:3]:
        print(f"     ✅ {db.name} ({db.type}, 学习曲线: {db.learning_curve})")

    # 场景 2：大规模生产
    rec2 = comparator.get_recommendation({"need_distributed": True, "open_source_only": True})
    print("   大规模生产（分布式 + 开源）:")
    for db in rec2:
        print(f"     ✅ {db.name} ({db.best_for})")

    # 场景 3：不想运维
    rec3 = comparator.get_recommendation({"no_ops": True})
    print("   不想运维（全托管）:")
    for db in rec3:
        print(f"     ✅ {db.name} ({db.type})")


def demo_faiss_simulation():
    """演示 FAISS 的搜索原理（纯 Python 模拟）"""
    print("\n" + "=" * 60)
    print("  FAISS 搜索原理模拟 — FAISS Search Simulation")
    print("=" * 60)

    # 模拟文档库的向量（4 维）
    documents = {
        "doc_001": {"text": "猫和狗都是常见的宠物", "vector": [0.8, 0.6, 0.1, 0.2]},
        "doc_002": {"text": "Python 是一门编程语言", "vector": [0.1, 0.1, 0.9, 0.8]},
        "doc_003": {"text": "猫喜欢抓老鼠", "vector": [0.7, 0.5, 0.2, 0.1]},
        "doc_004": {"text": "机器学习需要大量数据", "vector": [0.1, 0.2, 0.8, 0.7]},
        "doc_005": {"text": "狗是人类最好的朋友", "vector": [0.6, 0.7, 0.1, 0.1]},
    }

    # 查询向量
    query = "可爱的宠物动物"
    query_vec = [0.75, 0.65, 0.0, 0.1]

    print(f"\n查询: \"{query}\"")
    print(f"查询向量: {query_vec}\n")

    # FAISS Flat 模式：暴力搜索（L2 距离）
    print("FAISS Flat Index（L2 距离暴力搜索）:")
    distances = []
    for doc_id, doc_data in documents.items():
        vec = doc_data["vector"]
        # L2 距离 = √(Σ(aᵢ - bᵢ)²)
        dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(query_vec, vec)))
        distances.append((doc_id, dist, doc_data["text"]))

    # 按距离升序排序（距离越小越相似）
    distances.sort(key=lambda x: x[1])

    for i, (doc_id, dist, text) in enumerate(distances, 1):
        similarity = 1.0 / (1.0 + dist)
        bar = "█" * int(similarity * 20)
        print(f"  {i}. [{bar:<20s}] L2={dist:.4f}  相似度={similarity:.4f}  {text}")

    print("\n说明: FAISS 的 Flat 索引会计算查询向量与所有向量的 L2 距离，")
    print("      然后返回最近的 K 个。这是最精确但也是大数据量时最慢的方法。")


def demo_index_comparison():
    """演示不同索引类型的差异"""
    print("\n" + "=" * 60)
    print("  向量索引类型对比 — Index Type Comparison")
    print("=" * 60)

    index_types = [
        ("Flat (暴力搜索)", "精确", "O(N)", "慢", "适合 < 100 万向量"),
        ("IVF (倒排文件)", "近似", "O(N/nlist)", "快", "适合百万到千万级"),
        ("HNSW (小世界图)", "近似", "O(log N)", "很快", "适合各种规模，精度最高"),
        ("PQ (乘积量化)", "近似", "O(N)", "最快", "适合大规模，牺牲精度换速度"),
    ]

    print("\n{:<20s} {:<8s} {:<12s} {:<8s} {}".format(
        "索引类型", "精度", "复杂度", "速度", "适用场景"
    ))
    print("-" * 70)
    for name, accuracy, complexity, speed, use_case in index_types:
        print(f"{name:<20s} {accuracy:<8s} {complexity:<12s} {speed:<8s} {use_case}")


if __name__ == "__main__":
    demo_db_comparison()
    demo_faiss_simulation()
    demo_index_comparison()
