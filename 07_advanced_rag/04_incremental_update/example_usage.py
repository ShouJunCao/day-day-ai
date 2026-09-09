"""
example_usage.py — 增量更新与文档版本管理完整演示
"""
import os
import sys
import tempfile
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from incremental_update import (
    DocumentHasher,
    VersionManager,
    IncrementalUpdater,
    ConsistencyChecker,
    DocumentVersion,
)


def demo_document_hashing():
    """演示文档哈希计算"""
    print("=" * 60)
    print("  文档哈希计算演示")
    print("=" * 60)

    hasher = DocumentHasher()

    # 创建临时文件
    fd, path = tempfile.mkstemp(suffix=".md")
    with os.fdopen(fd, 'w') as f:
        f.write("# 测试文档\n\n这是一段测试内容。")

    hash1 = hasher.compute_hash(path)
    print(f"\n文件: {os.path.basename(path)}")
    print(f"哈希值: {hash1}")

    # 修改文件
    with open(path, 'w') as f:
        f.write("# 测试文档\n\n这是一段修改后的内容。")

    hash2 = hasher.compute_hash(path)
    print(f"修改后哈希值: {hash2}")
    print(f"是否变化: {hash1 != hash2}")

    os.unlink(path)


def demo_version_management():
    """演示版本管理"""
    print("\n" + "=" * 60)
    print("  文档版本管理演示")
    print("=" * 60)

    version_mgr = VersionManager("demo_versions.json")

    # 添加第一个版本
    v1 = version_mgr.add_version(
        doc_id="doc1.md",
        file_path="/docs/doc1.md",
        content_hash="abc123",
        chunk_count=5,
    )
    print(f"添加版本 1: 版本号={v1}")

    # 添加第二个版本（文档更新）
    v2 = version_mgr.add_version(
        doc_id="doc1.md",
        file_path="/docs/doc1.md",
        content_hash="def456",
        chunk_count=6,
    )
    print(f"添加版本 2: 版本号={v2}")

    # 查看活跃版本
    active = version_mgr.get_active_version("doc1.md")
    print(f"\n当前活跃版本: v{active.version} (哈希: {active.content_hash})")
    print(f"旧版本状态: archived")

    # 回滚到版本 1
    success = version_mgr.rollback("doc1.md", target_version=1)
    print(f"\n回滚到版本 1: {'成功' if success else '失败'}")

    active = version_mgr.get_active_version("doc1.md")
    print(f"当前活跃版本: v{active.version} (内容哈希: {active.content_hash})")

    # 清理
    if os.path.exists("demo_versions.json"):
        os.unlink("demo_versions.json")


def demo_incremental_update():
    """演示增量更新"""
    print("\n" + "=" * 60)
    print("  增量更新演示")
    print("=" * 60)

    hasher = DocumentHasher()
    version_mgr = VersionManager("demo_update_log.json")
    updater = IncrementalUpdater(hasher, version_mgr)

    # 第一次扫描（全部新增）
    first_scan = {
        "doc1.md": {"path": "/docs/doc1.md", "hash": "aaa111"},
        "doc2.md": {"path": "/docs/doc2.md", "hash": "bbb222"},
    }

    changes = updater.compute_changes(first_scan)
    print(f"\n第一次扫描:")
    print(f"  新增: {changes['added']}")
    print(f"  更新: {changes['updated']}")
    print(f"  删除: {changes['deleted']}")

    # 模拟执行更新
    result = updater.execute_update(changes, indexer=None)
    print(f"  更新结果: +{result.added} ~{result.updated} -{result.deleted}")

    # 第二次扫描（部分更新，部分删除）
    second_scan = {
        "doc1.md": {"path": "/docs/doc1.md", "hash": "aaa111"},  # 未变
        "doc2.md": {"path": "/docs/doc2.md", "hash": "bbb333"},  # 已修改
        "doc3.md": {"path": "/docs/doc3.md", "hash": "ccc444"},  # 新增
    }

    changes = updater.compute_changes(second_scan)
    print(f"\n第二次扫描:")
    print(f"  新增: {changes['added']}")
    print(f"  更新: {changes['updated']}")
    print(f"  删除: {changes['deleted']}")

    # 清理
    if os.path.exists("demo_update_log.json"):
        os.unlink("demo_update_log.json")


def demo_consistency_check():
    """演示一致性检查"""
    print("\n" + "=" * 60)
    print("  一致性检查演示")
    print("=" * 60)

    checker = ConsistencyChecker()
    version_mgr = VersionManager("demo_consistency.json")

    # 模拟版本状态
    version_mgr.add_version("doc1.md", "/docs/doc1.md", "hash1", 5)
    version_mgr.add_version("doc2.md", "/docs/doc2.md", "hash2", 3)

    # 模拟索引状态
    index_chunks = [
        {"doc_id": "doc1.md", "chunk_id": "c1"},
        {"doc_id": "doc2.md", "chunk_id": "c2"},
        {"doc_id": "doc3.md", "chunk_id": "c3"},  # 孤儿块
    ]

    result = checker.check(version_mgr, index_chunks)
    print(f"\n一致性检查结果:")
    print(f"  一致: {result['consistent']}")
    print(f"  活跃文档数: {result['total_active_docs']}")
    print(f"  索引文档数: {result['total_indexed_docs']}")
    print(f"  孤儿块: {result['orphaned_chunks']}")
    print(f"  缺失文档: {result['missing_docs']}")

    # 清理
    if os.path.exists("demo_consistency.json"):
        os.unlink("demo_consistency.json")


def demo_summary():
    """总结对比"""
    print("\n" + "=" * 60)
    print("  全量更新 vs 增量更新对比")
    print("=" * 60)

    print(f"\n{'维度':<20s} {'全量更新':<20s} {'增量更新':<20s}")
    print("-" * 60)
    print(f"{'处理范围':<20s} {'所有文档':<20s} {'仅变化文档':<20s}")
    print(f"{'更新速度':<20s} {'慢':<20s} {'快':<20s}")
    print(f"{'资源消耗':<20s} {'高':<20s} {'低':<20s}")
    print(f"{'适用场景':<20s} {'首次构建':<20s} {'日常维护':<20s}")
    print(f"{'一致性保证':<20s} {'高':<20s} {'需额外检查':<20s}")


if __name__ == "__main__":
    demo_document_hashing()
    demo_version_management()
    demo_incremental_update()
    demo_consistency_check()
    demo_summary()
