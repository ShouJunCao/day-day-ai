"""
graph_agentic_rag.py — Graph RAG + Agentic RAG 综合实战系统
综合运用知识图谱和 Agent 技术构建企业级 RAG 系统。
"""
import os
import re
from typing import Optional, List, Dict
from dataclasses import dataclass, field


# ============================================================
# 模块：数据结构
# ============================================================

@dataclass
class Entity:
    """知识图谱实体"""
    entity_id: str
    name: str
    entity_type: str  # "person", "concept", "technology", etc.
    description: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class Relation:
    """知识图谱关系"""
    source: str
    target: str
    relation_type: str
    weight: float = 1.0


@dataclass
class Document:
    """文档"""
    doc_id: str
    content: str
    title: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class SearchResult:
    """搜索结果"""
    doc_id: str
    score: float
    content: str
    entities: List[str] = field(default_factory=list)


# ============================================================
# 模块：知识图谱构建
# ============================================================

class KnowledgeGraph:
    """
    知识图谱：存储实体和关系，支持图谱遍历和查询。
    """

    def __init__(self):
        self.entities: Dict[str, Entity] = {}
        self.relations: List[Relation] = []
        self.adjacency: Dict[str, List[str]] = {}

    def add_entity(self, entity: Entity):
        """添加实体"""
        self.entities[entity.entity_id] = entity
        if entity.entity_id not in self.adjacency:
            self.adjacency[entity.entity_id] = []

    def add_relation(self, relation: Relation):
        """添加关系"""
        self.relations.append(relation)
        if relation.source in self.adjacency:
            if relation.target not in self.adjacency[relation.source]:
                self.adjacency[relation.source].append(relation.target)
        if relation.target in self.adjacency:
            if relation.source not in self.adjacency[relation.target]:
                self.adjacency[relation.target].append(relation.source)

    def get_neighbors(self, entity_id: str) -> List[str]:
        """获取实体的邻居"""
        return self.adjacency.get(entity_id, [])

    def find_path(self, source: str, target: str, max_depth: int = 3) -> List[List[str]]:
        """查找两个实体之间的路径（BFS）"""
        if source not in self.adjacency or target not in self.adjacency:
            return []

        queue = [[source]]
        visited = {source}
        paths = []

        while queue and len(paths) < 3:
            path = queue.pop(0)
            if len(path) > max_depth:
                continue

            current = path[-1]
            if current == target and len(path) > 1:
                paths.append(path)
                continue

            for neighbor in self.adjacency.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(path + [neighbor])

        return paths

    def get_entity_info(self, entity_id: str) -> Optional[dict]:
        """获取实体信息"""
        if entity_id in self.entities:
            e = self.entities[entity_id]
            return {
                "id": e.entity_id,
                "name": e.name,
                "type": e.entity_type,
                "description": e.description,
                "neighbors": self.get_neighbors(entity_id),
            }
        return None


# ============================================================
# 模块：Agent 路由
# ============================================================

class AgentRouter:
    """
    Agent 路由器：根据问题类型选择最佳检索策略。
    """

    def __init__(self):
        self.routes = {
            "factual": self._route_factual,
            "comparative": self._route_comparative,
            "relational": self._route_relational,
            "procedural": self._route_procedural,
        }

    def classify_query(self, query: str) -> str:
        """简单分类"""
        if any(kw in query for kw in ["什么", "谁", "哪里", "何时"]):
            return "factual"
        elif any(kw in query for kw in ["比较", "区别", "对比", "不同"]):
            return "comparative"
        elif any(kw in query for kw in ["关系", "关联", "联系", "影响"]):
            return "relational"
        else:
            return "procedural"

    def route(self, query: str) -> str:
        """路由查询"""
        query_type = self.classify_query(query)
        handler = self.routes.get(query_type, self._route_procedural)
        return handler(query, query_type)

    def _route_factual(self, query: str, qtype: str) -> str:
        return f"事实型查询 → 向量检索: '{query}'"

    def _route_comparative(self, query: str, qtype: str) -> str:
        return f"比较型查询 → 混合检索: '{query}'"

    def _route_relational(self, query: str, qtype: str) -> str:
        return f"关系型查询 → 图谱检索: '{query}'"

    def _route_procedural(self, query: str, qtype: str) -> str:
        return f"过程型查询 → 文档检索: '{query}'"


# ============================================================
# 模块：向量索引
# ============================================================

class VectorIndex:
    """简易向量索引"""

    def __init__(self, embedding_fn):
        self.embedding_fn = embedding_fn
        self.documents: Dict[str, Document] = {}
        self.vectors: Dict[str, List[float]] = {}

    def add_document(self, doc: Document):
        self.documents[doc.doc_id] = doc
        self.vectors[doc.doc_id] = self.embedding_fn(doc.content)

    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        qv = self.embedding_fn(query)
        scored = []
        for doc_id, vec in self.vectors.items():
            score = self._cosine(qv, vec)
            scored.append(SearchResult(
                doc_id=doc_id,
                score=score,
                content=self.documents[doc_id].content,
            ))
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:top_k]

    def _cosine(self, v1, v2):
        dot = sum(a * b for a, b in zip(v1, v2))
        n1 = sum(a * a for a in v1) ** 0.5
        n2 = sum(b * b for b in v2) ** 0.5
        return dot / (n1 * n2) if n1 and n2 else 0.0


# ============================================================
# 模块：综合 RAG 系统
# ============================================================

class GraphAgenticRAG:
    """
    Graph + Agentic RAG 综合系统。

    流程：
    1. Agent 路由：根据问题类型选择策略
    2. 多源检索：向量检索 + 图谱检索
    3. 结果融合：合并检索结果
    4. 生成回答：基于检索结果生成
    """

    def __init__(self, graph: KnowledgeGraph, vector_index: VectorIndex, router: AgentRouter):
        self.graph = graph
        self.vector_index = vector_index
        self.router = router

    def query(self, question: str) -> dict:
        # 1. 路由
        route_result = self.router.route(question)

        # 2. 检索
        vector_results = self.vector_index.search(question, top_k=3)

        # 3. 图谱增强（如果是关系型查询）
        query_type = self.router.classify_query(question)
        graph_results = []
        if query_type == "relational":
            graph_results = self._graph_search(question)

        # 4. 融合
        all_results = self._merge_results(vector_results, graph_results)

        return {
            "question": question,
            "route": route_result,
            "query_type": query_type,
            "results": [{"doc_id": r.doc_id, "score": r.score, "content": r.content[:50]} for r in all_results],
            "answer": f"[Graph+Agentic RAG] 基于 {len(all_results)} 个来源，回答: {question}",
        }

    def _graph_search(self, question: str) -> List[SearchResult]:
        """图谱检索"""
        results = []
        for eid, entity in self.graph.entities.items():
            if entity.name in question or entity.name.lower() in question.lower():
                info = self.graph.get_entity_info(eid)
                if info:
                    results.append(SearchResult(
                        doc_id=f"graph_{eid}",
                        score=0.9,
                        content=info["description"],
                        entities=[eid] + info["neighbors"],
                    ))
        return results

    def _merge_results(self, vector_results, graph_results) -> List[SearchResult]:
        """合并结果"""
        seen = set()
        merged = []
        for r in vector_results + graph_results:
            if r.doc_id not in seen:
                seen.add(r.doc_id)
                merged.append(r)
        merged.sort(key=lambda x: x.score, reverse=True)
        return merged


# ============================================================
# 模块：简易 Embedding
# ============================================================

def simple_embedding(text: str) -> List[float]:
    vector = [0.0] * 128
    for char in text.replace(" ", ""):
        idx = ord(char) % 128
        vector[idx] += 1.0
    norm = sum(v * v for v in vector) ** 0.5
    return [v / norm for v in vector] if norm else vector


# ============================================================
# 模块：入口
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  Graph + Agentic RAG 实战系统")
    print("=" * 60)

    # 1. 构建知识图谱
    graph = KnowledgeGraph()
    graph.add_entity(Entity("e1", "Transformer", "technology", "深度学习架构"))
    graph.add_entity(Entity("e2", "BERT", "model", "预训练语言模型"))
    graph.add_entity(Entity("e3", "GPT", "model", "生成式预训练模型"))
    graph.add_entity(Entity("e4", "自注意力", "concept", "核心机制"))
    graph.add_relation(Relation("e2", "e4", "使用", 1.0))
    graph.add_relation(Relation("e3", "e4", "使用", 1.0))
    graph.add_relation(Relation("e2", "e1", "基于", 0.9))
    graph.add_relation(Relation("e3", "e1", "基于", 0.9))

    # 2. 构建向量索引
    vector_index = VectorIndex(simple_embedding)
    vector_index.add_document(Document("d1", "Transformer 是一种基于自注意力的深度学习架构"))
    vector_index.add_document(Document("d2", "BERT 是基于 Transformer 的预训练模型"))
    vector_index.add_document(Document("d3", "GPT 是生成式预训练模型"))

    # 3. 创建 Agent 路由
    router = AgentRouter()

    # 4. 创建综合系统
    system = GraphAgenticRAG(graph, vector_index, router)

    # 测试查询
    questions = [
        "什么是 Transformer？",
        "BERT 和 GPT 的区别是什么？",
        "Transformer 和自注意力的关系是什么？",
    ]

    for q in questions:
        print(f"\n{'=' * 50}")
        print(f"问题: {q}")
        result = system.query(q)
        print(f"路由: {result['route']}")
        print(f"类型: {result['query_type']}")
        for r in result['results']:
            print(f"  [{r['doc_id']}] 分数={r['score']:.2f} | {r['content']}...")
        print(f"回答: {result['answer']}")
