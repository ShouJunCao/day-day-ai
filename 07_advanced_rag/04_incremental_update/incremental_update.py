"""
incremental_update.py — 增量更新与文档版本管理实现
实现知识库的增量更新、版本控制和一致性检查。
"""
import os
import re
import json
import hashlib
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime


# ============================================================
# 模块：数据结构
# ============================================================

@dataclass
class DocumentVersion:
    """文档版本信息"""
    doc_id: str
    version: int
    content_hash: str
    file_path: str
    updated_at: str
    chunk_count: int = 0
    status: str = "active"  # "active", "archived", "deleted"


@dataclass
class UpdateResult:
    """更新结果"""
    added: int
    updated: int
    deleted: int
    total_chunks: int
    duration_seconds: float
    version_log: List[dict] = field(default_factory=list)


# ============================================================
# 模块：文档哈希计算
# ============================================================

class DocumentHasher:
    """
    文档哈希计算器：用于检测文档内容变化。

    原理：
    1. 读取文档内容
    2. 计算内容的 MD5/SHA256 哈希值
    3. 通过对比哈希值判断文档是否发生变化
    """

    def __init__(self, algorithm: str = "md5"):
        self.algorithm = algorithm

    def compute_hash(self, file_path: str) -> str:
        """计算文件内容的哈希值"""
        content = Path(file_path).read_bytes()
        if self.algorithm == "md5":
            return hashlib.md5(content).hexdigest()
        elif self.algorithm == "sha256":
            return hashlib.sha256(content).hexdigest()
        else:
            raise ValueError(f"不支持的算法: {self.algorithm}")

    def has_changed(self, file_path: str, old_hash: str) -> bool:
        """判断文件是否发生变化"""
        new_hash = self.compute_hash(file_path)
        return new_hash != old_hash


# ============================================================
# 模块：版本管理器
# ============================================================

class VersionManager:
    """
    文档版本管理器：管理文档的版本历史和状态。

    功能：
    1. 记录每个文档的版本历史
    2. 支持版本回滚
    3. 跟踪文档的增删改状态
    """

    def __init__(self, version_log_path: str = "version_log.json"):
        self.version_log_path = version_log_path
        self.versions: Dict[str, List[DocumentVersion]] = {}
        self._load_log()

    def _load_log(self):
        """加载版本日志"""
        if os.path.exists(self.version_log_path):
            with open(self.version_log_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for doc_id, versions in data.items():
                    self.versions[doc_id] = [
                        DocumentVersion(**v) for v in versions
                    ]

    def save_log(self):
        """保存版本日志"""
        data = {}
        for doc_id, versions in self.versions.items():
            data[doc_id] = [
                {
                    "doc_id": v.doc_id,
                    "version": v.version,
                    "content_hash": v.content_hash,
                    "file_path": v.file_path,
                    "updated_at": v.updated_at,
                    "chunk_count": v.chunk_count,
                    "status": v.status,
                }
                for v in versions
            ]
        with open(self.version_log_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_version(self, doc_id: str, file_path: str, content_hash: str, chunk_count: int) -> int:
        """添加新版本"""
        if doc_id not in self.versions:
            self.versions[doc_id] = []

        # 将旧版本标记为 archived
        for v in self.versions[doc_id]:
            if v.status == "active":
                v.status = "archived"

        # 创建新版本
        new_version = DocumentVersion(
            doc_id=doc_id,
            version=len(self.versions[doc_id]) + 1,
            content_hash=content_hash,
            file_path=file_path,
            updated_at=datetime.now().isoformat(),
            chunk_count=chunk_count,
            status="active",
        )
        self.versions[doc_id].append(new_version)
        return new_version.version

    def get_active_version(self, doc_id: str) -> Optional[DocumentVersion]:
        """获取当前活跃版本"""
        if doc_id not in self.versions:
            return None
        for v in self.versions[doc_id]:
            if v.status == "active":
                return v
        return None

    def rollback(self, doc_id: str, target_version: int) -> bool:
        """回滚到指定版本"""
        if doc_id not in self.versions:
            return False

        target = None
        for v in self.versions[doc_id]:
            if v.version == target_version:
                target = v
                break

        if target is None:
            return False

        # 将当前活跃版本标记为 archived
        for v in self.versions[doc_id]:
            if v.status == "active":
                v.status = "archived"

        # 创建新版本（复制目标版本的内容）
        new_version = DocumentVersion(
            doc_id=doc_id,
            version=len(self.versions[doc_id]) + 1,
            content_hash=target.content_hash,
            file_path=target.file_path,
            updated_at=datetime.now().isoformat(),
            chunk_count=target.chunk_count,
            status="active",
        )
        self.versions[doc_id].append(new_version)
        return True


# ============================================================
# 模块：增量更新器
# ============================================================

class IncrementalUpdater:
    """
    增量更新器：只更新发生变化的文档，避免全量重建。

    原理：
    1. 扫描文档目录，获取所有文件列表
    2. 对比文件哈希值，识别新增、修改、删除的文档
    3. 只处理变化的文档，更新向量索引
    4. 记录版本日志
    """

    def __init__(self, hasher: DocumentHasher, version_manager: VersionManager):
        self.hasher = hasher
        self.version_manager = version_manager

    def scan_directory(self, directory: str, extensions: Optional[List[str]] = None) -> Dict[str, str]:
        """扫描目录，返回文件路径到哈希值的映射"""
        if extensions is None:
            extensions = [".txt", ".md", ".html"]

        file_hashes = {}
        for ext in extensions:
            for path in Path(directory).rglob(f"*{ext}"):
                if path.is_file():
                    file_hash = self.hasher.compute_hash(str(path))
                    doc_id = str(path.relative_to(directory))
                    file_hashes[doc_id] = {
                        "path": str(path),
                        "hash": file_hash,
                    }
        return file_hashes

    def compute_changes(self, current_files: Dict[str, dict]) -> Dict[str, List[str]]:
        """计算新增、修改、删除的文件"""
        added = []
        updated = []
        deleted = []

        # 检查新增和修改
        for doc_id, info in current_files.items():
            active_version = self.version_manager.get_active_version(doc_id)
            if active_version is None:
                added.append(doc_id)
            elif active_version.content_hash != info["hash"]:
                updated.append(doc_id)

        # 检查删除
        for doc_id in self.version_manager.versions:
            if doc_id not in current_files:
                active = self.version_manager.get_active_version(doc_id)
                if active and active.status == "active":
                    deleted.append(doc_id)

        return {
            "added": added,
            "updated": updated,
            "deleted": deleted,
        }

    def execute_update(self, changes: Dict[str, List[str]], indexer) -> UpdateResult:
        """
        执行增量更新。

        参数：
        - changes: 包含 added/updated/deleted 列表
        - indexer: 向量索引对象，需要有 add/remove 方法

        返回：
        - UpdateResult: 更新结果统计
        """
        import time
        start_time = time.time()

        added_count = 0
        updated_count = 0
        deleted_count = 0
        version_log = []

        # 处理新增
        for doc_id in changes["added"]:
            # 实际项目中：解析文档 → 分块 → 添加到索引
            added_count += 1
            version_log.append({"action": "added", "doc_id": doc_id})

        # 处理更新
        for doc_id in changes["updated"]:
            # 实际项目中：删除旧块 → 解析新文档 → 添加新块
            updated_count += 1
            version_log.append({"action": "updated", "doc_id": doc_id})

        # 处理删除
        for doc_id in changes["deleted"]:
            # 实际项目中：从索引中删除相关块
            deleted_count += 1
            version_log.append({"action": "deleted", "doc_id": doc_id})

        duration = time.time() - start_time

        return UpdateResult(
            added=added_count,
            updated=updated_count,
            deleted=deleted_count,
            total_chunks=added_count + updated_count,
            duration_seconds=duration,
            version_log=version_log,
        )


# ============================================================
# 模块：一致性检查器
# ============================================================

class ConsistencyChecker:
    """
    一致性检查器：确保向量索引与文档状态一致。

    功能：
    1. 检查索引中是否存在已删除文档的块
    2. 检查是否存在文档没有对应的索引块
    3. 报告不一致的地方
    """

    def __init__(self):
        pass

    def check(self, version_manager: VersionManager, index_chunks: List[dict]) -> dict:
        """
        检查一致性。

        参数：
        - version_manager: 版本管理器
        - index_chunks: 索引中的所有块列表

        返回：
        - dict: 检查结果
        """
        # 获取所有活跃文档
        active_docs = set()
        for doc_id in version_manager.versions:
            active = version_manager.get_active_version(doc_id)
            if active and active.status == "active":
                active_docs.add(doc_id)

        # 获取索引中的文档
        indexed_docs = set()
        for chunk in index_chunks:
            indexed_docs.add(chunk.get("doc_id"))

        # 检查不一致
        orphaned_chunks = indexed_docs - active_docs
        missing_docs = active_docs - indexed_docs

        return {
            "consistent": len(orphaned_chunks) == 0 and len(missing_docs) == 0,
            "orphaned_chunks": list(orphaned_chunks),
            "missing_docs": list(missing_docs),
            "total_active_docs": len(active_docs),
            "total_indexed_docs": len(indexed_docs),
        }


# ============================================================
# 模块：使用示例
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  增量更新与文档版本管理演示")
    print("=" * 60)

    # 创建组件
    hasher = DocumentHasher()
    version_mgr = VersionManager("demo_version_log.json")

    # 模拟增量更新
    updater = IncrementalUpdater(hasher, version_mgr)

    # 模拟当前文件状态
    current_files = {
        "doc1.md": {"path": "/docs/doc1.md", "hash": "abc123"},
        "doc2.md": {"path": "/docs/doc2.md", "hash": "def456"},
        "doc3.md": {"path": "/docs/doc3.md", "hash": "ghi789"},
    }

    # 计算变化
    changes = updater.compute_changes(current_files)
    print(f"\n新增文档: {changes['added']}")
    print(f"更新文档: {changes['updated']}")
    print(f"删除文档: {changes['deleted']}")

    # 执行更新
    result = updater.execute_update(changes, indexer=None)
    print(f"\n更新结果:")
    print(f"  新增: {result.added}")
    print(f"  更新: {result.updated}")
    print(f"  删除: {result.deleted}")
    print(f"  耗时: {result.duration_seconds:.3f} 秒")

    # 清理
    if os.path.exists("demo_version_log.json"):
        os.unlink("demo_version_log.json")
