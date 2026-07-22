"""
使用示例: 演示向量数据库的对比、选型和 FAISS 搜索原理模拟。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_comparison import VectorDBComparator, demo_db_comparison, demo_faiss_simulation, demo_index_comparison


def demo_storage_estimation():
    """演示不同规模的存储成本估算"""
    print("=" * 60)
    print("  存储成本估算 — Storage Cost Estimation")
    print("=" * 60)

    comparator = VectorDBComparator()

    # 不同规模
    scales = [
        ("小规模", 10_000, 768),
        ("中规模", 1_000_000, 768),
        ("大规模", 10_000_000, 1024),
        ("超大规模", 100_000_000, 1536),
    ]

    for label, num_vecs, dim in scales:
        print(f"\n{label}: {num_vecs:,} 向量 × {dim} 维")
        costs = comparator.estimate_storage_cost(num_vecs, dim)
        for db_name, size in costs.items():
            print(f"   {db_name:15s} → {size}")


def demo_decision_helper():
    """演示选型决策辅助"""
    print("\n" + "=" * 60)
    print("  选型决策辅助 — Decision Helper")
    print("=" * 60)

    comparator = VectorDBComparator()

    scenarios = [
        {
            "name": "个人开发者的本地知识库",
            "requirements": {
                "open_source_only": True,
            },
        },
        {
            "name": "创业公司的中文 RAG 系统",
            "requirements": {
                "open_source_only": True,
            },
        },
        {
            "name": "大企业的多语言搜索引擎",
            "requirements": {
                "need_distributed": True,
            },
        },
        {
            "name": "SaaS 产品的 AI 功能（不想运维）",
            "requirements": {
                "no_ops": True,
            },
        },
    ]

    for scenario in scenarios:
        print(f"\n场景: {scenario['name']}")
        recs = comparator.get_recommendation(scenario["requirements"])
        for db in recs[:3]:
            print(f"  ✅ {db.name}: {db.best_for}")
            print(f"     类型: {db.type} | 分布式: {'是' if db.distributed else '否'} "
                  f"| 开源: {'是' if db.open_source else '否'}")


if __name__ == "__main__":
    demo_db_comparison()
    demo_faiss_simulation()
    demo_index_comparison()
    demo_storage_estimation()
    demo_decision_helper()
