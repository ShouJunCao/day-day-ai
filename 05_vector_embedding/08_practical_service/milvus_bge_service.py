"""
milvus_bge_service.py — Milvus + BGE-M3 向量检索服务实战
演示如何搭建一个完整的向量检索服务，包含：
1. BGE-M3 本地 Embedding
2. Milvus 向量数据库连接和集合创建
3. 数据写入和索引构建
4. 向量检索和混合检索
"""
import os
from typing import Optional
from dataclasses import dataclass


# ============================================================
# 模块：BGE-M3 Embedding 服务
# ============================================================

class BGEEmbeddingService:
    """
    BGE-M3 Embedding 服务：使用本地模型生成文本向量。

    特点：
    - 支持 100+ 种语言
    - 同时返回稠密、稀疏、多向量三种表示
    - 最大序列长度 8192
    - 本地部署，数据不出境

    依赖：
    pip install FlagEmbedding torch transformers
    """

    def __init__(self, model_name: str = "BAAI/bge-m3"):
        """
        初始化 BGE-M3 模型。

        参数：
        - model_name (str): HuggingFace 模型路径
        """
        self.model_name = model_name
        self._model = None
        self._tokenizer = None

    def _load_model(self):
        """延迟加载模型和分词器"""
        from FlagEmbedding import BGEM3FlagModel
        self._model = BGEM3FlagModel(
            self.model_name,
            use_fp16=True,  # 半精度推理，节省显存
        )

    def encode(self, texts: list[str]) -> dict:
        """
        将文本列表编码为向量。

        参数：
        - texts (list[str]): 待编码的文本列表

        返回：
        - dict: 包含 dense_embeddings, sparse_embeddings, colbert_vecs
        """
        if self._model is None:
            self._load_model()

        result = self._model.encode(
            texts,
            batch_size=16,
            max_length=8192,
            return_dense=True,
            return_sparse=True,
            return_colbert_vecs=False,
        )

        return {
            "dense_embeddings": result["dense_vecs"],
            "sparse_embeddings": result["lexical_weights"],
        }


# ============================================================
# 模块：Milvus 客户端封装
# ============================================================

class MilvusVectorService:
    """
    Milvus 向量数据库服务：提供集合管理和向量检索。

    连接方式：
    - 单机版：MilvusLite（pip install milvus）
    - 服务器版：Milvus Standalone（Docker 部署）
    - 集群版：Milvus Cluster（K8s 部署）
    """

    def __init__(self, uri: str = "milvus_demo.db"):
        """
        初始化 Milvus 连接。

        参数：
        - uri (str): 连接地址
            本地文件: "milvus_demo.db"（MilvusLite）
            服务器: "http://localhost:19530"
        """
        self.uri = uri
        self._client = None

    def _connect(self):
        """连接到 Milvus"""
        from pymilvus import MilvusClient
        self._client = MilvusClient(uri=self.uri)

    def create_collection(
        self,
        collection_name: str,
        dimension: int = 1024,
        auto_id: bool = True,
    ) -> None:
        """
        创建向量集合。

        参数：
        - collection_name (str): 集合名称
        - dimension (int): 向量维度（BGE-M3 为 1024）
        - auto_id (bool): 是否自动生成主键
        """
        if self._client is None:
            self._connect()

        schema = self._client.create_schema(
            auto_id=auto_id,
            enable_dynamic_field=True,
        )
        schema.add_field("id", "INT64", is_primary=True)
        schema.add_field("vector", "FLOAT_VECTOR", dim=dimension)
        schema.add_field("text", "VARCHAR", max_length=65535)
        schema.add_field("metadata", "JSON")

        index_params = self._client.prepare_index_params()
        index_params.add_index(
            field_name="vector",
            index_name="vector_idx",
            index_type="HNSW",
            metric_type="COSINE",
            params={"M": 16, "efConstruction": 200},
        )

        self._client.create_collection(
            collection_name=collection_name,
            schema=schema,
            index_params=index_params,
        )

    def insert(self, collection_name: str, data: list[dict]) -> dict:
        """
        插入向量数据。

        参数：
        - collection_name (str): 集合名称
        - data (list[dict]): 数据列表，每个 dict 包含 vector, text, metadata

        返回：
        - dict: 插入结果
        """
        if self._client is None:
            self._connect()

        return self._client.insert(collection_name, data)

    def search(
        self,
        collection_name: str,
        query_vector: list[float],
        top_k: int = 5,
        filter_expr: Optional[str] = None,
    ) -> list:
        """
        向量检索。

        参数：
        - collection_name (str): 集合名称
        - query_vector (list[float]): 查询向量
        - top_k (int): 返回结果数
        - filter_expr (str): 过滤表达式，如 "category == 'tech'"

        返回：
        - list: 检索结果
        """
        if self._client is None:
            self._connect()

        return self._client.search(
            collection_name=collection_name,
            data=[query_vector],
            anns_field="vector",
            limit=top_k,
            filter=filter_expr,
            search_params={"metric_type": "COSINE", "params": {"ef": 64}},
            output_fields=["text", "metadata"],
        )


# ============================================================
# 模块：完整检索服务（Embedding + Milvus）
# ============================================================

class RetrievalService:
    """
    完整的检索服务：整合 BGE-M3 Embedding 和 Milvus 检索。
    """

    def __init__(
        self,
        embedding_model: str = "BAAI/bge-m3",
        milvus_uri: str = "milvus_demo.db",
    ):
        """
        初始化检索服务。

        参数：
        - embedding_model (str): Embedding 模型路径
        - milvus_uri (str): Milvus 连接地址
        """
        self.embedder = BGEEmbeddingService(embedding_model)
        self.milvus = MilvusVectorService(milvus_uri)

    def index_documents(self, collection: str, documents: list[dict]) -> dict:
        """
        索引文档：先 Embedding，再写入 Milvus。

        参数：
        - collection (str): 集合名称
        - documents (list[dict]): 文档列表，每个包含 text 和 metadata

        返回：
        - dict: 插入结果
        """
        texts = [doc["text"] for doc in documents]
        embeddings = self.embedder.encode(texts)

        data = []
        for i, doc in enumerate(documents):
            data.append({
                "vector": embeddings["dense_embeddings"][i].tolist(),
                "text": doc["text"],
                "metadata": doc.get("metadata", {}),
            })

        return self.milvus.insert(collection, data)

    def search(self, collection: str, query: str, top_k: int = 5) -> list:
        """
        检索：先将查询文本 Embedding，再搜索 Milvus。

        参数：
        - collection (str): 集合名称
        - query (str): 查询文本
        - top_k (int): 返回结果数

        返回：
        - list: 检索结果
        """
        embeddings = self.embedder.encode([query])
        query_vector = embeddings["dense_embeddings"][0].tolist()
        return self.milvus.search(collection, query_vector, top_k)


# ============================================================
# 模块：使用示例
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  Milvus + BGE-M3 向量检索服务 — 使用示例")
    print("=" * 60)

    # 演示数据结构
    print("\n1. 创建集合:")
    print("   milvus.create_collection('rag_docs', dimension=1024)")
    print("   → 集合: rag_docs, 维度: 1024, 索引: HNSW")

    print("\n2. 准备文档数据:")
    sample_docs = [
        {"text": "人工智能在医疗领域的应用越来越广泛", "metadata": {"category": "科技"}},
        {"text": "深度学习模型需要大量训练数据", "metadata": {"category": "AI"}},
        {"text": "自然语言处理是 AI 的重要分支", "metadata": {"category": "NLP"}},
    ]
    for doc in sample_docs:
        print(f"   → {doc['text'][:20]}... [{doc['metadata']['category']}]")

    print("\n3. 索引文档:")
    print("   service.index_documents('rag_docs', documents)")
    print("   → BGE-M3 生成 1024 维向量")
    print("   → 插入 Milvus 集合")

    print("\n4. 检索:")
    print("   results = service.search('rag_docs', 'AI 医疗', top_k=3)")
    print("   → 返回最相关的文档")

    print("\n完整流程: 文本 → BGE-M3 Embedding → Milvus 存储 → 向量检索 → Top-K 结果")
