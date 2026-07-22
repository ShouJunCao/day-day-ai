"""
distributed_deployment.py — 向量数据库分布式部署配置与优化
包含 Milvus、Qdrant 集群配置示例和性能调优参数。
用于教学演示，帮助理解分布式向量数据库的架构和配置。
"""
from typing import Optional
from dataclasses import dataclass, field


# ============================================================
# 模块：Milvus 集群配置
# 说明：Milvus 采用微服务架构，各组件可独立扩展
# ============================================================

@dataclass
class MilvusConfig:
    """
    Milvus 集群配置。

    Milvus 架构包含以下核心组件：
    - Proxy: 接收客户端请求，负责权限验证和 SQL 解析
    - QueryNode: 执行向量检索和标量过滤
    - DataNode: 处理数据写入和持久化
    - RootCoord: 管理元数据和 DDL 操作
    - DataCoord: 管理数据分布和 Compaction
    - etcd: 元数据存储（类似 ZooKeeper）
    - MinIO: 对象存储（持久化向量数据）
    - Pulsar: 消息队列（数据同步）
    """

    # Proxy 配置
    proxy_replicas: int = 2  # Proxy 副本数（水平扩展）
    query_node_replicas: int = 3  # QueryNode 副本数
    data_node_replicas: int = 2  # DataNode 副本数

    # 索引参数
    index_type: str = "HNSW"  # 索引类型
    index_metric_type: str = "COSINE"  # 度量类型
    index_params: dict = field(default_factory=lambda: {
        "M": 16,  # HNSW 连接数
        "efConstruction": 200,  # 构建参数
    })

    # 搜索参数
    search_ef: int = 64  # 搜索宽度（越大越精确但越慢）
    search_topk: int = 10  # 返回结果数

    # 持久化配置
    storage_type: str = "minio"  # 存储后端
    minio_endpoint: str = "minio:9000"
    minio_bucket: str = "milvus-data"

    # etcd 配置
    etcd_endpoints: list[str] = field(default_factory=lambda: ["etcd:2379"])

    # 性能调优
    max_nq: int = 1000  # 单次查询最大向量数
    max_partition_num: int = 4096  # 最大分区数
    graceful_stop_timeout: int = 30  # 优雅停止超时


# ============================================================
# 模块：Qdrant 集群配置
# 说明：Qdrant 采用分布式共识架构（Raft）
# ============================================================

@dataclass
class QdrantConfig:
    """
    Qdrant 集群配置。

    Qdrant 架构特点：
    - 基于 Raft 协议的分布式共识
    - 支持自动分片（Sharding）
    - 支持多副本（Replication）
    - 轻量级部署（单个二进制文件）
    """

    # 集群配置
    cluster_enabled: bool = True
    cluster_p2p_port: int = 6335  # 节点间通信端口
    consensus_tick_period_ms: int = 100  # Raft 心跳间隔

    # 分片配置
    default_shard_number: int = 3  # 默认分片数
    replication_factor: int = 2  # 副本数
    write_consistency_factor: int = 1  # 写入一致性因子

    # 存储配置
    storage_path: str = "/qdrant/storage"
    snapshots_path: str = "/qdrant/snapshots"

    # 性能调优
    optimizers_max_threads: int = 4  # 优化器最大线程数
    max_search_threads: int = 8  # 搜索最大线程数
    memmap_threshold: int = 20000  # mmap 阈值


# ============================================================
# 模块：性能优化建议
# ============================================================

class DeploymentOptimizer:
    """
    部署优化器：根据数据规模和查询 QPS 推荐配置。
    """

    @staticmethod
    def recommend(data_count: int, qps: int, dimension: int) -> dict:
        """
        根据数据量和 QPS 推荐部署配置。

        参数：
        - data_count (int): 向量总数
        - qps (int): 预期每秒查询数
        - dimension (int): 向量维度
        """
        config: dict[str, object] = {
            "data_count": data_count,
            "qps": qps,
            "dimension": dimension,
        }

        # 数据量估算
        memory_gb = data_count * dimension * 4 / (1024 ** 3) * 2  # ×2 是 HNSW 开销
        config["estimated_memory_gb"] = round(memory_gb, 1)

        if data_count < 1_000_000 and qps < 100:
            config["architecture"] = "单机部署"
            config["database"] = "Chroma / Qdrant (单机)"
            config["replicas"] = 1
            config["shards"] = 1
        elif data_count < 10_000_000 and qps < 500:
            config["architecture"] = "小规模集群"
            config["database"] = "Qdrant (3 节点)"
            config["replicas"] = 2
            config["shards"] = 3
        elif data_count < 100_000_000 and qps < 2000:
            config["architecture"] = "中等规模集群"
            config["database"] = "Milvus (6-9 节点)"
            config["replicas"] = 2
            config["shards"] = 6
        else:
            config["architecture"] = "大规模集群"
            config["database"] = "Milvus (10+ 节点)"
            config["replicas"] = 3
            config["shards"] = 12

        return config
