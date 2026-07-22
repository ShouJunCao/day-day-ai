"""
vector_databases.py — 主流向量数据库统一客户端
提供 FAISS、Milvus、Qdrant、Chroma、Pinecone、pgvector 六种向量数据库的统一操作接口。
包含连接、插入、查询、删除等核心操作的模拟实现和真实客户端封装。
"""
import os
import json
import math
from typing import Optional
from dataclasses import dataclass, field


# ============================================================
# 模块：向量搜索结果数据结构
# 说明：统一不同数据库返回的搜索结果格式
# ============================================================

@dataclass
class SearchResult:
    """
    向量搜索结果：封装匹配文档及其相似度分数。

    属性：
    - id (str): 文档 ID
    - score (float): 相似度分数（越高越相似，或距离越低越相似）
    - metadata (dict): 文档元数据
    - vector (list[float]): 匹配文档的向量（可选）
    """
    # 文档 ID
    id: str
    # 相似度分数
    score: float
    # 文档元数据
    metadata: dict = field(default_factory=dict)
    # 匹配文档的向量（可选）
    vector: Optional[list[float]] = None


# ============================================================
# 模块：FAISS 封装
# 说明：FAISS 是 Meta 开源的本地向量搜索库
# 特点：速度最快、不支持持久化（需手动保存）、无分布式
# 适用场景：单机、中小规模、对延迟敏感
# ============================================================

class FAISSClient:
    """
    FAISS 客户端：基于 Meta FAISS 库的本地向量搜索。

    特点：
    - 速度最快（C++ 底层，高度优化）
    - 不支持内置持久化（需要手动保存索引文件）
    - 无分布式能力（单机使用）
    - 支持多种索引类型（Flat、IVF、HNSW、PQ 等）

    安装：pip install faiss-cpu（CPU）或 faiss-gpu（GPU）
    """

    def __init__(self, dimension: int, index_type: str = "flat"):
        """
        初始化 FAISS 客户端。

        参数：
        - dimension (int): 向量维度
        - index_type (str): 索引类型，可选 "flat"、"ivf"、"hnsw"
        """
        # 向量维度
        self.dimension = dimension
        # 索引类型
        self.index_type = index_type
        # FAISS 索引对象（延迟初始化）
        self.index = None
        # ID 映射表：FAISS 内部 ID → 业务 ID
        self.id_mapping: dict[int, str] = {}
        # 元数据存储：业务 ID → 元数据
        self.metadata_store: dict[str, dict] = {}
        # 下一个内部 ID
        self._next_id = 0

    def _init_index(self):
        """延迟初始化 FAISS 索引"""
        import faiss

        if self.index_type == "flat":
            # Flat 索引：暴力搜索，最精确但大数据量时慢
            self.index = faiss.IndexFlatL2(self.dimension)
        elif self.index_type == "ivf":
            # IVF 索引：倒排文件，适合大数据量
            nlist = 100  # 聚类中心数
            quantizer = faiss.IndexFlatL2(self.dimension)
            self.index = faiss.IndexIVFFlat(quantizer, self.dimension, nlist)
        elif self.index_type == "hnsw":
            # HNSW 索引：分层可导航小世界图，平衡速度和精度
            M = 16  # 每个节点的连接数
            self.index = faiss.IndexHNSWFlat(self.dimension, M)

    def insert(self, vectors: list[list[float]], ids: list[str], metadata: Optional[list[dict]] = None) -> int:
        """
        批量插入向量。

        参数：
        - vectors (list[list[float]]): 向量列表
        - ids (list[str]): 对应的业务 ID 列表
        - metadata (list[dict]): 对应的元数据列表（可选）

        返回：
        - int: 插入的向量数量
        """
        import numpy as np

        if self.index is None:
            self._init_index()

        # 将向量列表转换为 numpy 数组（FAISS 要求 float32）
        np_vectors = np.array(vectors, dtype=np.float32)

        # IVF 索引需要先训练
        if self.index_type == "ivf" and not self.index.is_trained:
            self.index.train(np_vectors)

        # 生成内部 ID 并添加到索引
        internal_ids = []
        for i, vec in enumerate(vectors):
            # 记录业务 ID 映射
            self.id_mapping[self._next_id] = ids[i]
            # 存储元数据
            if metadata and i < len(metadata):
                self.metadata_store[ids[i]] = metadata[i]
            internal_ids.append(self._next_id)
            self._next_id += 1

        # 批量添加到 FAISS 索引
        self.index.add(np_vectors)

        return len(vectors)

    def search(self, query_vector: list[float], top_k: int = 5) -> list[SearchResult]:
        """
        搜索最相似的 K 个向量。

        参数：
        - query_vector (list[float]): 查询向量
        - top_k (int): 返回最相似的结果数

        返回：
        - list[SearchResult]: 搜索结果列表，按相似度降序排列
        """
        import numpy as np

        if self.index is None:
            return []

        # 将查询向量转换为 numpy 数组
        np_query = np.array([query_vector], dtype=np.float32)

        # 搜索：返回 top_k 个最近邻
        distances, indices = self.index.search(np_query, top_k)

        results = []
        for i, idx in enumerate(indices[0]):
            if idx == -1:
                # FAISS 返回 -1 表示没有更多结果
                continue

            # 将内部 ID 映射回业务 ID
            business_id = self.id_mapping.get(int(idx), str(idx))
            # 获取元数据
            meta = self.metadata_store.get(business_id, {})

            # FAISS 返回的是 L2 距离（越小越相似），转换为相似度分数
            # 相似度 = 1 / (1 + distance)
            similarity = 1.0 / (1.0 + distances[0][i])

            results.append(SearchResult(
                id=business_id,
                score=similarity,
                metadata=meta,
            ))

        return results

    def delete(self, ids: list[str]) -> int:
        """
        删除指定 ID 的向量（FAISS 不直接支持删除，需要重建索引）。

        参数：
        - ids (list[str]): 要删除的业务 ID 列表

        返回：
        - int: 实际删除的数量
        """
        # FAISS 不直接支持删除，这里标记为删除
        # 生产环境中需要定期重建索引
        deleted = 0
        for biz_id in ids:
            if biz_id in self.metadata_store:
                del self.metadata_store[biz_id]
                deleted += 1
        return deleted

    def save(self, path: str) -> None:
        """
        保存索引到磁盘。

        参数：
        - path (str): 保存路径
        """
        import faiss
        if self.index is not None:
            faiss.write_index(self.index, path)
            # 同时保存元数据
            meta_path = path + ".meta.json"
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump({
                    "id_mapping": {str(k): v for k, v in self.id_mapping.items()},
                    "metadata": self.metadata_store,
                    "next_id": self._next_id,
                }, f, ensure_ascii=False, indent=2)

    def load(self, path: str) -> None:
        """
        从磁盘加载索引。

        参数：
        - path (str): 索引文件路径
        """
        import faiss
        self.index = faiss.read_index(path)
        meta_path = path + ".meta.json"
        if os.path.exists(meta_path):
            with open(meta_path, encoding="utf-8") as f:
                data = json.load(f)
                self.id_mapping = {int(k): v for k, v in data["id_mapping"].items()}
                self.metadata_store = data["metadata"]
                self._next_id = data["next_id"]


# ============================================================
# 模块：Chroma 封装
# 说明：Chroma 是轻量级嵌入式向量数据库，适合快速原型开发
# 特点：无需外部服务、Python 原生、支持持久化
# 适用场景：本地开发、小型项目、快速原型
# ============================================================

class ChromaClient:
    """
    Chroma 客户端：轻量级嵌入式向量数据库。

    特点：
    - 无需外部服务（嵌入式运行）
    - Python 原生 API
    - 支持持久化到磁盘
    - 内置文本嵌入（sentence-transformers）

    安装：pip install chromadb
    """

    def __init__(self, collection_name: str = "default", persist_dir: str = "./chroma_data"):
        """
        初始化 Chroma 客户端。

        参数：
        - collection_name (str): 集合名称
        - persist_dir (str): 持久化目录
        """
        # 集合名称
        self.collection_name = collection_name
        # 持久化目录
        self.persist_dir = persist_dir
        # Chroma 客户端对象（延迟初始化）
        self.client = None
        # 集合对象
        self.collection = None

    def _init_client(self):
        """延迟初始化 Chroma 客户端"""
        import chromadb
        # 创建持久化客户端
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        # 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},  # 使用余弦相似度
        )

    def insert(self, vectors: list[list[float]], ids: list[str], metadata: Optional[list[dict]] = None, documents: Optional[list[str]] = None) -> int:
        """
        批量插入向量。

        参数：
        - vectors (list[list[float]]): 向量列表（Chroma 可自动生成嵌入，但这里我们提供预计算的）
        - ids (list[str]): 业务 ID 列表
        - metadata (list[dict]): 元数据列表（可选）
        - documents (list[str]): 原始文本列表（可选，用于 Chroma 内置嵌入）

        返回：
        - int: 插入数量
        """
        if self.client is None:
            self._init_client()

        # Chroma 的添加接口
        add_kwargs = {
            "ids": ids,
            "embeddings": vectors,
        }
        if metadata:
            add_kwargs["metadatas"] = metadata
        if documents:
            add_kwargs["documents"] = documents

        self.collection.add(**add_kwargs)
        return len(ids)

    def search(self, query_vector: list[float], top_k: int = 5, where: Optional[dict] = None) -> list[SearchResult]:
        """
        向量搜索。

        参数：
        - query_vector (list[float]): 查询向量
        - top_k (int): 返回结果数
        - where (dict): 元数据过滤条件（可选）

        返回：
        - list[SearchResult]: 搜索结果
        """
        if self.client is None:
            return []

        query_kwargs = {
            "query_embeddings": [query_vector],
            "n_results": top_k,
        }
        if where:
            query_kwargs["where"] = where

        results = self.collection.query(**query_kwargs)

        search_results = []
        for i, doc_id in enumerate(results["ids"][0]):
            meta = results["metadatas"][0][i] if results.get("metadatas") else {}
            dist = results["distances"][0][i] if results.get("distances") else 0.0
            # Chroma 返回的是距离（越小越相似），转换为相似度
            similarity = 1.0 / (1.0 + dist)
            search_results.append(SearchResult(
                id=doc_id,
                score=similarity,
                metadata=meta,
            ))

        return search_results

    def delete(self, ids: list[str]) -> int:
        """删除指定 ID 的向量"""
        if self.client is None:
            return 0
        self.collection.delete(ids=ids)
        return len(ids)


# ============================================================
# 模块：Qdrant 封装
# 说明：Qdrant 是 Rust 编写的高性能向量数据库
# 特点：过滤查询、分布式部署、REST/gRPC 双接口
# 适用场景：生产环境、需要复杂过滤的检索
# ============================================================

class QdrantClient:
    """
    Qdrant 客户端：Rust 编写的高性能向量数据库。

    特点：
    - 高性能（Rust 底层）
    - 支持复杂过滤查询（payload filtering）
    - 支持分布式部署
    - REST API 和 gRPC 双接口

    安装：pip install qdrant-client
    """

    def __init__(self, collection_name: str = "default", url: str = "http://localhost:6333"):
        """
        初始化 Qdrant 客户端。

        参数：
        - collection_name (str): 集合名称
        - url (str): Qdrant 服务地址
        """
        self.collection_name = collection_name
        self.url = url
        self.client = None

    def _init_client(self):
        """延迟初始化 Qdrant 客户端"""
        from qdrant_client import QdrantClient as QdrantSDK
        from qdrant_client.models import Distance, VectorParams

        self.client = QdrantSDK(url=self.url)

        # 检查集合是否存在
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)

        if not exists:
            # 创建集合（使用余弦相似度）
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=768,  # 默认维度，实际使用时需传入
                    distance=Distance.COSINE,
                ),
            )

    def insert(self, vectors: list[list[float]], ids: list[str], metadata: Optional[list[dict]] = None) -> int:
        """批量插入向量（模拟实现）"""
        # 实际实现需要调用 Qdrant SDK 的 upsert 方法
        # 这里提供接口框架
        return len(ids)

    def search(self, query_vector: list[float], top_k: int = 5) -> list[SearchResult]:
        """向量搜索（模拟实现）"""
        # 实际实现需要调用 Qdrant SDK 的 search 方法
        return []


# ============================================================
# 模块：Milvus 封装
# 说明：Milvus 是开源的分布式向量数据库
# 特点：分布式、高可用、支持多种索引、GPU 加速
# 适用场景：大规模向量检索、企业级生产环境
# ============================================================

class MilvusClient:
    """
    Milvus 客户端：开源分布式向量数据库。

    特点：
    - 分布式架构（支持水平扩展）
    - 高可用（多副本）
    - 支持多种索引（IVF、HNSW、DiskANN 等）
    - GPU 加速

    安装：pip install pymilvus
    """

    def __init__(self, collection_name: str = "default", uri: str = "http://localhost:19530"):
        """
        初始化 Milvus 客户端。

        参数：
        - collection_name (str): 集合名称
        - uri (str): Milvus 服务地址
        """
        self.collection_name = collection_name
        self.uri = uri
        self.client = None

    def _init_client(self):
        """延迟初始化 Milvus 客户端"""
        from pymilvus import MilvusClient as MilvusSDK
        self.client = MilvusSDK(uri=self.uri)

    def insert(self, vectors: list[list[float]], ids: list[str], metadata: Optional[list[dict]] = None) -> int:
        """批量插入向量（模拟实现）"""
        return len(ids)

    def search(self, query_vector: list[float], top_k: int = 5) -> list[SearchResult]:
        """向量搜索（模拟实现）"""
        return []


# ============================================================
# 模块：Pinecone 封装
# 说明：Pinecone 是全托管的云端向量数据库服务
# 特点：无需运维、自动扩展、serverless
# 适用场景：不想运维基础设施的团队
# ============================================================

class PineconeClient:
    """
    Pinecone 客户端：全托管云端向量数据库。

    特点：
    - 全托管（无需运维）
    - 自动扩展
    - Serverless 模式
    - 按量计费

    安装：pip install pinecone
    """

    def __init__(self, index_name: str = "default", api_key: Optional[str] = None):
        """
        初始化 Pinecone 客户端。

        参数：
        - index_name (str): 索引名称
        - api_key (str): API 密钥（或从环境变量 PINECONE_API_KEY 读取）
        """
        self.index_name = index_name
        self.api_key = api_key or os.getenv("PINECONE_API_KEY", "")
        self.index = None

    def _init_client(self):
        """延迟初始化 Pinecone 客户端"""
        import pinecone
        pinecone.init(api_key=self.api_key, environment="us-east1-aws")
        self.index = pinecone.Index(self.index_name)

    def insert(self, vectors: list[list[float]], ids: list[str], metadata: Optional[list[dict]] = None) -> int:
        """批量插入向量（模拟实现）"""
        return len(ids)

    def search(self, query_vector: list[float], top_k: int = 5) -> list[SearchResult]:
        """向量搜索（模拟实现）"""
        return []


# ============================================================
# 模块：pgvector 封装
# 说明：pgvector 是 PostgreSQL 的向量扩展
# 特点：与关系型数据库集成、SQL 查询 + 向量搜索、开源
# 适用场景：已有 PostgreSQL、需要关系+向量联合查询
# ============================================================

class PgVectorClient:
    """
    pgvector 客户端：PostgreSQL 向量扩展。

    特点：
    - 与 PostgreSQL 集成
    - SQL 查询 + 向量搜索
    - 开源免费
    - 适合关系型+向量混合场景

    安装：pip install psycopg2-binary
    数据库端：CREATE EXTENSION vector;
    """

    def __init__(self, table_name: str = "embeddings", dsn: str = "postgresql://localhost:5432/mydb"):
        """
        初始化 pgvector 客户端。

        参数：
        - table_name (str): 表名
        - dsn (str): 数据库连接字符串
        """
        self.table_name = table_name
        self.dsn = dsn
        self.conn = None

    def _init_client(self):
        """延迟初始化数据库连接"""
        import psycopg2
        self.conn = psycopg2.connect(self.dsn)
        # 创建表（如果不存在）
        with self.conn.cursor() as cur:
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id TEXT PRIMARY KEY,
                    embedding VECTOR(768),
                    metadata JSONB
                );
            """)
            self.conn.commit()

    def insert(self, vectors: list[list[float]], ids: list[str], metadata: Optional[list[dict]] = None) -> int:
        """批量插入向量（模拟实现）"""
        return len(ids)

    def search(self, query_vector: list[float], top_k: int = 5) -> list[SearchResult]:
        """向量搜索（模拟实现）"""
        return []
