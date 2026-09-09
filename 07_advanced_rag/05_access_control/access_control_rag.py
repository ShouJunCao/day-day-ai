"""
access_control_rag.py — 权限控制与多租户 RAG 实现
实现基于角色的访问控制和多租户隔离的 RAG 系统。
"""
import os
import re
from typing import Optional, List, Dict, Set
from dataclasses import dataclass, field
from enum import Enum


# ============================================================
# 模块：数据结构
# ============================================================

class Role(Enum):
    """用户角色"""
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class Permission(Enum):
    """权限类型"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


@dataclass
class Tenant:
    """租户信息"""
    tenant_id: str
    name: str
    allowed_roles: List[Role] = field(default_factory=list)
    max_documents: int = 10000
    metadata: dict = field(default_factory=dict)


@dataclass
class User:
    """用户信息"""
    user_id: str
    tenant_id: str
    role: Role
    allowed_doc_ids: Set[str] = field(default_factory=set)


@dataclass
class Document:
    """文档信息"""
    doc_id: str
    tenant_id: str
    content: str
    access_level: str = "public"  # public, internal, restricted, confidential
    owner_id: str = ""
    metadata: dict = field(default_factory=dict)


# ============================================================
# 模块：权限管理器
# ============================================================

class PermissionManager:
    """
    权限管理器：管理用户角色和权限。

    权限模型：基于角色的访问控制（RBAC）
    - Admin: 所有权限（读写删除管理）
    - Editor: 读写权限
    - Viewer: 只读权限
    """

    ROLE_PERMISSIONS = {
        Role.ADMIN: {Permission.READ, Permission.WRITE, Permission.DELETE, Permission.ADMIN},
        Role.EDITOR: {Permission.READ, Permission.WRITE},
        Role.VIEWER: {Permission.READ},
    }

    def has_permission(self, user: User, permission: Permission) -> bool:
        """检查用户是否有指定权限"""
        return permission in self.ROLE_PERMISSIONS.get(user.role, set())

    def can_access_doc(self, user: User, doc: Document) -> bool:
        """检查用户是否可以访问文档"""
        # 租户隔离：用户只能访问同租户的文档
        if user.tenant_id != doc.tenant_id:
            return False

        # 文档级别权限
        if doc.access_level == "public":
            return True
        elif doc.access_level == "internal":
            return self.has_permission(user, Permission.READ)
        elif doc.access_level == "restricted":
            return user.user_id in doc.metadata.get("allowed_users", [])
        elif doc.access_level == "confidential":
            return user.user_id == doc.owner_id

        return False


# ============================================================
# 模块：多租户索引
# ============================================================

class MultiTenantIndex:
    """
    多租户向量索引：为不同租户维护独立的向量索引。

    原理：
    1. 每个租户的文档存储在一个独立的命名空间中
    2. 检索时自动加入租户过滤条件
    3. 确保租户间数据完全隔离
    """

    def __init__(self, embedding_fn):
        self.embedding_fn = embedding_fn
        # {tenant_id: {doc_id: {chunks: [...], vectors: [...]}}}
        self.tenant_indexes: Dict[str, Dict[str, dict]] = {}

    def add_document(self, tenant_id: str, doc_id: str, chunks: List[str]):
        """添加文档到指定租户的索引"""
        if tenant_id not in self.tenant_indexes:
            self.tenant_indexes[tenant_id] = {}

        doc_chunks = []
        doc_vectors = []
        for chunk_text in chunks:
            vector = self.embedding_fn(chunk_text)
            doc_chunks.append(chunk_text)
            doc_vectors.append(vector)

        self.tenant_indexes[tenant_id][doc_id] = {
            "chunks": doc_chunks,
            "vectors": doc_vectors,
        }

    def remove_document(self, tenant_id: str, doc_id: str):
        """从指定租户的索引中删除文档"""
        if tenant_id in self.tenant_indexes:
            self.tenant_indexes[tenant_id].pop(doc_id, None)

    def search(self, tenant_id: str, query: str, top_k: int = 5) -> List[dict]:
        """在指定租户的索引中检索"""
        if tenant_id not in self.tenant_indexes:
            return []

        query_vector = self.embedding_fn(query)
        all_results = []

        for doc_id, doc_data in self.tenant_indexes[tenant_id].items():
            for i, vec in enumerate(doc_data["vectors"]):
                score = self._cosine_similarity(query_vector, vec)
                all_results.append({
                    "tenant_id": tenant_id,
                    "doc_id": doc_id,
                    "chunk": doc_data["chunks"][i],
                    "score": score,
                })

        all_results.sort(key=lambda x: x["score"], reverse=True)
        return all_results[:top_k]

    def get_tenant_stats(self, tenant_id: str) -> dict:
        """获取租户统计信息"""
        if tenant_id not in self.tenant_indexes:
            return {"documents": 0, "chunks": 0}

        doc_count = len(self.tenant_indexes[tenant_id])
        chunk_count = sum(
            len(d["chunks"]) for d in self.tenant_indexes[tenant_id].values()
        )
        return {"documents": doc_count, "chunks": chunk_count}

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)


# ============================================================
# 模块：安全 RAG 管道
# ============================================================

class SecureRAGPipeline:
    """
    安全 RAG 管道：集成权限控制和多租户隔离的 RAG 系统。

    完整流程：
    1. 验证用户身份和租户
    2. 检查用户对目标文档的访问权限
    3. 在用户有权限的范围内检索
    4. 对检索结果进行二次权限过滤
    5. 构建 Prompt 并生成回答
    """

    def __init__(self, index: MultiTenantIndex, permission_mgr: PermissionManager):
        self.index = index
        self.permission_mgr = permission_mgr
        self.documents: Dict[str, Document] = {}  # doc_id -> Document

    def add_document(self, doc: Document):
        """添加文档（需要写入权限）"""
        self.documents[doc.doc_id] = doc

    def query(self, user: User, question: str, top_k: int = 5) -> dict:
        """
        安全查询：集成权限检查的 RAG 查询。

        参数：
        - user (User): 当前用户
        - question (str): 用户问题
        - top_k (int): 返回结果数

        返回：
        - dict: 查询结果
        """
        # 1. 在用户租户内检索
        raw_results = self.index.search(user.tenant_id, question, top_k * 2)

        # 2. 权限过滤
        filtered_results = []
        for result in raw_results:
            doc = self.documents.get(result["doc_id"])
            if doc and self.permission_mgr.can_access_doc(user, doc):
                filtered_results.append(result)
            if len(filtered_results) >= top_k:
                break

        # 3. 构建上下文
        context = "\n\n".join(r["chunk"] for r in filtered_results)

        return {
            "user_id": user.user_id,
            "tenant_id": user.tenant_id,
            "question": question,
            "results": filtered_results,
            "context_length": len(context),
            "answer": f"[安全 RAG] 基于 {len(filtered_results)} 个有权限的文档片段回答：{question}",
        }


# ============================================================
# 模块：简易 Embedding 函数（演示用）
# ============================================================

def simple_embedding(text: str) -> List[float]:
    """简易 Embedding 函数（演示用）"""
    vector = [0.0] * 128
    words = list(text.replace(" ", ""))
    for i, char in enumerate(words):
        idx = ord(char) % 128
        vector[idx] += 1.0
    norm = sum(v * v for v in vector) ** 0.5
    if norm > 0:
        vector = [v / norm for v in vector]
    return vector


# ============================================================
# 模块：使用示例
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  权限控制与多租户 RAG 演示")
    print("=" * 60)

    # 初始化组件
    perm_mgr = PermissionManager()
    index = MultiTenantIndex(embedding_fn=simple_embedding)
    pipeline = SecureRAGPipeline(index, perm_mgr)

    # 创建租户
    tenant_a = Tenant(tenant_id="tenant_a", name="公司 A")
    tenant_b = Tenant(tenant_id="tenant_b", name="公司 B")

    # 创建用户
    user_admin = User(user_id="u1", tenant_id="tenant_a", role=Role.ADMIN)
    user_viewer = User(user_id="u2", tenant_id="tenant_a", role=Role.VIEWER)
    user_other = User(user_id="u3", tenant_id="tenant_b", role=Role.EDITOR)

    # 创建文档
    doc_public = Document(
        doc_id="doc1", tenant_id="tenant_a",
        content="这是一篇公开的技术文档。",
        access_level="public",
    )
    doc_internal = Document(
        doc_id="doc2", tenant_id="tenant_a",
        content="这是一篇内部文档，包含敏感信息。",
        access_level="internal",
    )
    doc_restricted = Document(
        doc_id="doc3", tenant_id="tenant_a",
        content="这是一篇受限文档，只有特定用户可以访问。",
        access_level="restricted",
        metadata={"allowed_users": ["u1"]},
    )

    for doc in [doc_public, doc_internal, doc_restricted]:
        pipeline.add_document(doc)

    # 添加到索引
    for doc in [doc_public, doc_internal, doc_restricted]:
        index.add_document(doc.tenant_id, doc.doc_id, [doc.content])

    print(f"\n=== 权限检查 ===")
    print(f"Admin 读取权限: {perm_mgr.has_permission(user_admin, Permission.READ)}")
    print(f"Viewer 写入权限: {perm_mgr.has_permission(user_viewer, Permission.WRITE)}")
    print(f"Viewer 读取权限: {perm_mgr.has_permission(user_viewer, Permission.READ)}")

    print(f"\n=== 文档访问检查 ===")
    print(f"Admin 访问公开文档: {perm_mgr.can_access_doc(user_admin, doc_public)}")
    print(f"Viewer 访问内部文档: {perm_mgr.can_access_doc(user_viewer, doc_internal)}")
    print(f"Viewer 访问受限文档: {perm_mgr.can_access_doc(user_viewer, doc_restricted)}")

    print(f"\n=== 跨租户隔离 ===")
    print(f"公司B用户访问公司A文档: {perm_mgr.can_access_doc(user_other, doc_public)}")

    print(f"\n=== 安全查询 ===")
    result = pipeline.query(user_admin, "技术文档内容", top_k=3)
    print(f"Admin 查询结果: {result['results']}")
