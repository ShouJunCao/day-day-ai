"""
example_usage.py — 权限控制与多租户 RAG 完整演示
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from access_control_rag import (
    PermissionManager,
    MultiTenantIndex,
    SecureRAGPipeline,
    Role,
    Permission,
    User,
    Tenant,
    Document,
    simple_embedding,
)


def demo_permission_model():
    """演示 RBAC 权限模型"""
    print("=" * 60)
    print("  RBAC 权限模型演示")
    print("=" * 60)

    mgr = PermissionManager()

    users = [
        User(user_id="admin1", tenant_id="t1", role=Role.ADMIN),
        User(user_id="editor1", tenant_id="t1", role=Role.EDITOR),
        User(user_id="viewer1", tenant_id="t1", role=Role.VIEWER),
    ]

    perms = [Permission.READ, Permission.WRITE, Permission.DELETE, Permission.ADMIN]

    print(f"\n{'用户':<15s} {'角色':<12s}", end="")
    for p in perms:
        print(f" {p.value:<8s}", end="")
    print()
    print("-" * 60)

    for u in users:
        print(f"{u.user_id:<15s} {u.role.value:<12s}", end="")
        for p in perms:
            has = mgr.has_permission(u, p)
            print(f" {'✅' if has else '❌':<8s}", end="")
        print()


def demo_multi_tenant():
    """演示多租户隔离"""
    print("\n" + "=" * 60)
    print("  多租户隔离演示")
    print("=" * 60)

    index = MultiTenantIndex(embedding_fn=simple_embedding)

    # 租户 A 文档
    index.add_document("tenant_a", "a1", ["公司 A 的产品介绍"])
    index.add_document("tenant_a", "a2", ["公司 A 的技术架构"])

    # 租户 B 文档
    index.add_document("tenant_b", "b1", ["公司 B 的市场报告"])

    print(f"\n租户 A 统计: {index.get_tenant_stats('tenant_a')}")
    print(f"租户 B 统计: {index.get_tenant_stats('tenant_b')}")

    # 跨租户检索（应该只能看到自己租户的数据）
    results_a = index.search("tenant_a", "产品介绍", top_k=3)
    results_b = index.search("tenant_b", "产品介绍", top_k=3)

    print(f"\n租户 A 检索 '产品介绍': {len(results_a)} 条结果")
    for r in results_a:
        print(f"  [{r['tenant_id']}] {r['doc_id']}: {r['chunk']}")

    print(f"\n租户 B 检索 '产品介绍': {len(results_b)} 条结果")
    for r in results_b:
        print(f"  [{r['tenant_id']}] {r['doc_id']}: {r['chunk']}")


def demo_secure_pipeline():
    """演示安全 RAG 管道"""
    print("\n" + "=" * 60)
    print("  安全 RAG 管道演示")
    print("=" * 60)

    perm_mgr = PermissionManager()
    index = MultiTenantIndex(embedding_fn=simple_embedding)
    pipeline = SecureRAGPipeline(index, perm_mgr)

    # 创建文档
    docs = [
        Document("d1", "t1", "公开技术文档", "public"),
        Document("d2", "t1", "内部财务数据", "internal"),
        Document("d3", "t1", "机密战略规划", "confidential", owner_id="admin1"),
    ]

    for doc in docs:
        pipeline.add_document(doc)
        index.add_document(doc.tenant_id, doc.doc_id, [doc.content])

    # 不同用户查询
    users = [
        User("admin1", "t1", Role.ADMIN),
        User("viewer1", "t1", Role.VIEWER),
    ]

    for user in users:
        print(f"\n用户: {user.user_id} (角色: {user.role.value})")
        result = pipeline.query(user, "公司战略", top_k=3)
        print(f"  检索到 {len(result['results'])} 条有权限的文档")
        for r in result['results']:
            print(f"    {r['doc_id']}: {r['chunk'][:30]}...")


def demo_comparison():
    """对比不同方案"""
    print("\n" + "=" * 60)
    print("  多租户方案对比")
    print("=" * 60)

    print(f"\n{'方案':<20s} {'隔离级别':<12s} {'成本':<10s} {'复杂度':<10s}")
    print("-" * 55)
    print(f"{'独立实例':<20s} {'完全隔离':<12s} {'高':<10s} {'低':<10s}")
    print(f"{'命名空间隔离':<20s} {'逻辑隔离':<12s} {'中':<10s} {'中':<10s}")
    print(f"{'行级过滤':<20s} {'权限控制':<12s} {'低':<10s} {'高':<10s}")


if __name__ == "__main__":
    demo_permission_model()
    demo_multi_tenant()
    demo_secure_pipeline()
    demo_comparison()
