"""
example_usage.py — 三种索引算法的完整演示
包含 HNSW、IVF、PQ 的插入、搜索、对比演示。
"""
import os
import sys
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vector_indexes import HNSWIndex, IVFIndex, PQIndex


def generate_test_vectors(n: int, dim: int) -> list[list[float]]:
    """
    生成随机测试向量。
    
    参数：
    - n (int): 向量数量
    - dim (int): 向量维度
    
    返回：
    - list[list[float]]: 随机向量列表
    """
    random.seed(42)
    return [
        [random.gauss(0, 1) for _ in range(dim)]
        for _ in range(n)
    ]


def demo_hnsw():
    """演示 HNSW 索引的插入和搜索"""
    print("=" * 60)
    print("  HNSW 索引 — Hierarchical Navigable Small World")
    print("=" * 60)

    dim = 8
    n_vectors = 50
    vectors = generate_test_vectors(n_vectors, dim)

    # 创建索引
    index = HNSWIndex(dimension=dim, M=8, max_layer=3)

    # 插入向量
    print(f"\n插入 {n_vectors} 个向量（{dim} 维）...")
    for i, vec in enumerate(vectors):
        index.insert(vec, f"doc_{i:03d}")

    # 搜索
    query = vectors[0]  # 用第一个向量作为查询
    results = index.search(query, top_k=5)

    print(f"\n查询向量: doc_000")
    print("Top 5 搜索结果:")
    for nid, dist in results:
        print(f"  {nid:10s}  距离: {dist:.4f}")

    print(f"\nHNSW 特点:")
    print(f"  • 多层图结构，从粗到细搜索")
    print(f"  • 速度最快（O(log N) 复杂度）")
    print(f"  • 内存占用大（存储图连接）")


def demo_ivf():
    """演示 IVF 索引的训练、插入和搜索"""
    print("\n" + "=" * 60)
    print("  IVF 索引 — Inverted File Index")
    print("=" * 60)

    dim = 8
    n_vectors = 200
    vectors = generate_test_vectors(n_vectors, dim)

    # 创建索引
    index = IVFIndex(dimension=dim, nlist=20, nprobe=5)

    # 训练
    print(f"\n训练 IVF 索引（{index.nlist} 个簇）...")
    index.train(vectors)
    print(f"  聚类中心数: {len(index.centroids)}")

    # 插入向量
    print(f"插入 {n_vectors} 个向量...")
    for i, vec in enumerate(vectors):
        index.insert(vec, f"doc_{i:03d}")

    # 搜索
    query = vectors[10]
    results = index.search(query, top_k=5)

    print(f"\n查询向量: doc_010")
    print("Top 5 搜索结果:")
    for nid, dist in results:
        print(f"  {nid:10s}  距离: {dist:.4f}")

    print(f"\nIVF 特点:")
    print(f"  • 先聚类，再在相关簇中搜索")
    print(f"  • 内存占用小（只需存簇中心 + 倒排表）")
    print(f"  • 需要训练阶段（K-Means）")


def demo_pq():
    """演示 PQ 索引的训练、编码和搜索"""
    print("\n" + "=" * 60)
    print("  PQ 索引 — Product Quantization")
    print("=" * 60)

    dim = 16
    n_vectors = 500
    vectors = generate_test_vectors(n_vectors, dim)

    # 创建索引
    index = PQIndex(dimension=dim, m=4, k=64)

    # 训练
    print(f"\n训练 PQ 索引（{index.m} 段，每段 {index.k} 个码字）...")
    index.train(vectors)
    print(f"  每段维度: {index.sub_dim}")
    print(f"  压缩比: {dim * 4} bytes → {index.m * 1} bytes ({dim * 4 / index.m:.1f}x)")

    # 插入向量
    print(f"插入并编码 {n_vectors} 个向量...")
    for i, vec in enumerate(vectors):
        index.insert(vec, f"doc_{i:03d}")

    # 搜索
    query = vectors[5]
    results = index.search(query, top_k=5)

    print(f"\n查询向量: doc_005")
    print("Top 5 搜索结果:")
    for nid, dist in results:
        print(f"  {nid:10s}  距离: {dist:.4f}")

    print(f"\nPQ 特点:")
    print(f"  • 向量分段量化，压缩存储")
    print(f"  • 内存占用极小（压缩比可达 100x）")
    print(f"  • 有量化误差，精度低于 HNSW/IVF")


def demo_index_comparison():
    """对比三种索引的精度和性能"""
    print("\n" + "=" * 60)
    print("  索引对比 — Index Comparison")
    print("=" * 60)

    dim = 32
    n_vectors = 1000
    vectors = generate_test_vectors(n_vectors, dim)
    query = vectors[0]

    # HNSW
    hnsw = HNSWIndex(dimension=dim, M=16, max_layer=4)
    for i, vec in enumerate(vectors):
        hnsw.insert(vec, f"d_{i}")
    hnsw_results = hnsw.search(query, top_k=5)

    # IVF
    ivf = IVFIndex(dimension=dim, nlist=30, nprobe=5)
    ivf.train(vectors)
    for i, vec in enumerate(vectors):
        ivf.insert(vec, f"d_{i}")
    ivf_results = ivf.search(query, top_k=5)

    # PQ
    pq = PQIndex(dimension=dim, m=4, k=64)
    pq.train(vectors)
    for i, vec in enumerate(vectors):
        pq.insert(vec, f"d_{i}")
    pq_results = pq.search(query, top_k=5)

    print(f"\n数据集: {n_vectors} 向量 × {dim} 维")
    print(f"\n{'索引':<10s} {'Top-1 距离':<15s} {'内存开销':<15s} {'精度':<10s}")
    print("-" * 55)
    print(f"{'HNSW':<10s} {hnsw_results[0][1]:<15.4f} {'大（图结构）':<15s} {'高':<10s}")
    print(f"{'IVF':<10s} {ivf_results[0][1]:<15.4f} {'中（簇中心）':<15s} {'中高':<10s}")
    print(f"{'PQ':<10s} {pq_results[0][1]:<15.4f} {'小（量化编码）':<15s} {'中':<10s}")

    print(f"\n选择建议:")
    print(f"  • 追求速度 → HNSW")
    print(f"  • 追求内存效率 → PQ")
    print(f"  • 平衡两者 → IVF")


if __name__ == "__main__":
    demo_hnsw()
    demo_ivf()
    demo_pq()
    demo_index_comparison()
