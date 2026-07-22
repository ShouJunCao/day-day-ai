"""
example_usage.py — 相似度度量方法的完整演示
包含余弦相似度、欧氏距离、点积、曼哈顿距离的对比演示。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from similarity_metrics import (
    SimilarityCalculator,
    normalize_vector,
    cosine_similarity,
    euclidean_distance,
    dot_product,
    manhattan_distance,
)


def demo_basic_metrics():
    """演示基本相似度度量方法"""
    print("=" * 60)
    print("  相似度度量 — Similarity Metrics 演示")
    print("=" * 60)

    # 测试向量
    vec_cat = [0.8, 0.6, 0.0, 0.0]       # 猫
    vec_dog = [0.7, 0.7, 0.0, 0.0]       # 狗（与猫相似）
    vec_car = [0.0, 0.0, 0.9, 0.4]       # 车（与猫狗无关）
    vec_ant = [-0.8, -0.6, 0.0, 0.0]     # 反猫（与猫相反）

    print("\n测试向量:")
    print(f"  猫 (cat): {vec_cat}")
    print(f"  狗 (dog): {vec_dog}")
    print(f"  车 (car): {vec_car}")
    print(f"  反猫:     {vec_ant}")

    # 余弦相似度
    print("\n1. 余弦相似度 (Cosine Similarity):")
    print(f"   猫 vs 狗:   {cosine_similarity(vec_cat, vec_dog):.4f}")
    print(f"   猫 vs 车:   {cosine_similarity(vec_cat, vec_car):.4f}")
    print(f"   猫 vs 反猫: {cosine_similarity(vec_cat, vec_ant):.4f}")

    # 欧氏距离
    print("\n2. 欧氏距离 (Euclidean Distance):")
    print(f"   猫 vs 狗:   {euclidean_distance(vec_cat, vec_dog):.4f}")
    print(f"   猫 vs 车:   {euclidean_distance(vec_cat, vec_car):.4f}")
    print(f"   猫 vs 反猫: {euclidean_distance(vec_cat, vec_ant):.4f}")

    # 点积
    print("\n3. 点积 (Dot Product):")
    print(f"   猫 vs 狗:   {dot_product(vec_cat, vec_dog):.4f}")
    print(f"   猫 vs 车:   {dot_product(vec_cat, vec_car):.4f}")
    print(f"   猫 vs 反猫: {dot_product(vec_cat, vec_ant):.4f}")

    # 曼哈顿距离
    print("\n4. 曼哈顿距离 (Manhattan Distance):")
    print(f"   猫 vs 狗:   {manhattan_distance(vec_cat, vec_dog):.4f}")
    print(f"   猫 vs 车:   {manhattan_distance(vec_cat, vec_car):.4f}")
    print(f"   猫 vs 反猫: {manhattan_distance(vec_cat, vec_ant):.4f}")


def demo_normalization():
    """演示向量归一化的效果"""
    print("\n" + "=" * 60)
    print("  向量归一化 — Vector Normalization 演示")
    print("=" * 60)

    vec_long = [10.0, 6.0, 0.0, 0.0]     # 长向量
    vec_short = [0.1, 0.06, 0.0, 0.0]    # 短向量（方向相同）
    vec_cat = [0.8, 0.6, 0.0, 0.0]       # 参考向量

    print("\n归一化前:")
    print(f"  点积(长, 猫): {dot_product(vec_long, vec_cat):.4f}")
    print(f"  点积(短, 猫): {dot_product(vec_short, vec_cat):.4f}")
    print("  → 点积受向量长度影响很大")

    # 归一化
    vec_long_norm = normalize_vector(vec_long)
    vec_short_norm = normalize_vector(vec_short)

    print("\n归一化后:")
    print(f"  长向量归一化: {[round(v, 3) for v in vec_long_norm]}")
    print(f"  短向量归一化: {[round(v, 3) for v in vec_short_norm]}")
    print(f"  点积(长归一, 猫): {dot_product(vec_long_norm, vec_cat):.4f}")
    print(f"  点积(短归一, 猫): {dot_product(vec_short_norm, vec_cat):.4f}")
    print("  → 归一化后，点积等价于余弦相似度，只关注方向")


def demo_all_metrics_comparison():
    """对比所有度量方法的结果"""
    print("\n" + "=" * 60)
    print("  度量方法综合对比 — All Metrics Comparison")
    print("=" * 60)

    calc = SimilarityCalculator()

    # 测试向量对
    pairs = [
        ("语义相似", [0.8, 0.6, 0.1, 0.0], [0.7, 0.7, 0.1, 0.0]),
        ("语义无关", [0.8, 0.6, 0.0, 0.0], [0.0, 0.0, 0.9, 0.4]),
        ("语义相反", [0.8, 0.6, 0.0, 0.0], [-0.8, -0.6, 0.0, 0.0]),
        ("长度不同", [1.0, 0.75, 0.0, 0.0], [0.1, 0.075, 0.0, 0.0]),
    ]

    print(f"\n{'向量对':<10s} {'余弦':>8s} {'欧氏':>8s} {'点积':>8s} {'曼哈顿':>8s}")
    print("-" * 50)

    for label, v1, v2 in pairs:
        results = calc.compare_all(v1, v2)
        print(f"{label:<10s} {results['cosine_similarity']:>8.4f} "
              f"{results['euclidean_distance']:>8.4f} "
              f"{results['dot_product']:>8.4f} "
              f"{results['manhattan_distance']:>8.4f}")


def demo_practical_selection():
    """演示实际场景中的度量方法选择"""
    print("\n" + "=" * 60)
    print("  度量方法选择建议 — Metric Selection Guide")
    print("=" * 60)

    print("\n{:<15s} {:<20s} {:<20s}".format("度量方法", "适用场景", "不适用场景"))
    print("-" * 60)
    print("{:<15s} {:<20s} {:<20s}".format(
        "余弦相似度", "文本/语义搜索", "长度信息重要的场景"))
    print("{:<15s} {:<20s} {:<20s}".format(
        "欧氏距离", "聚类分析", "向量长度差异大的场景"))
    print("{:<15s} {:<20s} {:<20s}".format(
        "点积", "已归一化向量", "未归一化的向量"))
    print("{:<15s} {:<20s} {:<20s}".format(
        "曼哈顿距离", "高维稀疏数据", "维度相关性强的场景"))


if __name__ == "__main__":
    demo_basic_metrics()
    demo_normalization()
    demo_all_metrics_comparison()
    demo_practical_selection()
