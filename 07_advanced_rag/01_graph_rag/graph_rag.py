"""
graph_rag.py — Graph RAG（知识图谱增强检索）实现
基于 Microsoft GraphRAG 思路的简化实现。
不依赖第三方图库，使用纯 Python 实现。
"""
import os
import re
from collections import defaultdict
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, field


# ============================================================
# 模块：数据结构
# ============================================================

@dataclass
class Entity:
    """实体节点"""
    name: str
    description: str
    entity_type: str = "unknown"


@dataclass
class Relationship:
    """实体关系"""
    source: str
    target: str
    description: str
    weight: float = 1.0


@dataclass
class Community:
    """社区（实体集群）"""
    community_id: int
    entities: List[str]
    summary: str = ""
    level: int = 0


@dataclass
class GraphRAGResult:
    """Graph RAG 查询结果"""
    answer: str
    entities_used: List[str]
    communities_used: List[int]
    confidence: float


# ============================================================
# 模块：知识图谱构建器
# ============================================================

class KnowledgeGraphBuilder:
    """
    知识图谱构建器：从文档中提取实体和关系，构建知识图谱。

    原理：
    1. 从文本中提取命名实体（人名、地名、组织、概念等）
    2. 识别实体之间的关系
    3. 构建图结构（节点=实体，边=关系）
    4. 使用社区检测算法发现实体集群
    """

    def __init__(self):
        self.adjacency: Dict[str, set] = defaultdict(set)
        self.entities: Dict[str, Entity] = {}
        self.relationships: List[Relationship] = []
        self.communities: List[Community] = []

    def extract_entities(self, text: str) -> List[Entity]:
        """
        从文本中提取实体（简化版：基于关键词匹配）。

        实际项目中应使用 NER 模型（如 spaCy、BERT-NER）。
        """
        entities = []
        patterns = {
            "technology": r"(?:Transformer|BERT|GPT|RAG|LLM|Embedding)",
            "organization": r"(?:Google|OpenAI|Microsoft|Meta|百度|阿里|腾讯)",
            "concept": r"(?:注意力机制|自注意力|预训练|微调|幻觉)",
        }
        for entity_type, pattern in patterns.items():
            for match in re.finditer(pattern, text):
                name = match.group()
                if name not in self.entities:
                    entity = Entity(name=name, entity_type=entity_type, description="")
                    entities.append(entity)
                    self.entities[name] = entity
        return entities

    def extract_relationships(self, text: str, entities: List[Entity]) -> List[Relationship]:
        """
        从文本中提取实体之间的关系（简化版）。

        实际项目中应使用关系抽取模型。
        """
        relationships = []
        entity_names = [e.name for e in entities]

        # 简化实现：如果两个实体在同一段落中出现，认为它们有关系
        paragraphs = re.split(r"\n\n+", text)
        for para in paragraphs:
            para_entities = [e for e in entity_names if e in para]
            for i in range(len(para_entities)):
                for j in range(i + 1, len(para_entities)):
                    source, target = para_entities[i], para_entities[j]
                    rel = Relationship(
                        source=source, target=target,
                        description="在文档中共同出现",
                        weight=1.0,
                    )
                    relationships.append(rel)
                    self.relationships.append(rel)

                    # 添加到图
                    self.adjacency[source].add(target)
                    self.adjacency[target].add(source)

        return relationships

    def detect_communities(self) -> List[Community]:
        """
        使用社区检测算法发现实体集群。

        使用 Louvain 算法进行社区划分。
        """
        if len(self.adjacency) == 0:
            return []

        try:
            from community import best_partition
            # Build temp graph for community detection
            import networkx as nx
            temp_g = nx.Graph()
            for node, neighbors in self.adjacency.items():
                for nb in neighbors:
                    temp_g.add_edge(node, nb)
            partition = best_partition(temp_g)

            # 按社区分组
            community_map = {}
            for node, comm_id in partition.items():
                if comm_id not in community_map:
                    community_map[comm_id] = []
                community_map[comm_id].append(node)

            communities = []
            for comm_id, members in community_map.items():
                community = Community(
                    community_id=comm_id,
                    entities=members,
                    summary=f"社区 {comm_id}: 包含 {len(members)} 个实体",
                    level=0,
                )
                communities.append(community)

            self.communities = communities
            return communities

        except ImportError:
            # 如果没有 python-louvain，返回单个社区
            return [Community(
                community_id=0,
                entities=list(self.adjacency.keys()),
                summary="默认社区",
                level=0,
            )]

    def build(self, documents: List[str]) -> Dict:
        """
        从文档列表构建知识图谱。

        参数：
        - documents (list[str]): 文档文本列表

        返回：
        - dict: 构建结果统计
        """
        all_entities = []
        all_relationships = []

        for doc in documents:
            entities = self.extract_entities(doc)
            all_entities.extend(entities)
            rels = self.extract_relationships(doc, entities)
            all_relationships.extend(rels)

        communities = self.detect_communities()

        num_edges = sum(len(nbs) for nbs in self.adjacency.values()) // 2
        return {
            "num_entities": len(self.entities),
            "num_relationships": len(self.relationships),
            "num_communities": len(communities),
            "num_nodes": len(self.adjacency),
            "num_edges": num_edges,
        }


# ============================================================
# 模块：Graph RAG 查询引擎
# ============================================================

class GraphRAGQueryEngine:
    """
    Graph RAG 查询引擎：基于知识图谱的增强检索。

    原理：
    1. 从查询中提取相关实体
    2. 在知识图谱中找到这些实体及其邻居
    3. 获取相关社区摘要
    4. 将实体描述、关系和社区摘要组合为上下文
    5. 发送给 LLM 生成回答
    """

    def __init__(self, graph_builder: KnowledgeGraphBuilder, llm_fn=None):
        self.adjacency = graph_builder.adjacency
        self.entities = graph_builder.entities
        self.communities = graph_builder.communities
        self.llm_fn = llm_fn or self._mock_llm

    def query(self, question: str) -> GraphRAGResult:
        """
        执行 Graph RAG 查询。

        参数：
        - question (str): 用户问题

        返回：
        - GraphRAGResult: 查询结果
        """
        # 1. 从问题中提取相关实体
        query_entities = self._find_relevant_entities(question)

        # 2. 找到这些实体在图中的邻居
        neighbors = self._find_neighbors(query_entities)

        # 3. 获取相关社区
        related_communities = self._find_related_communities(query_entities)

        # 4. 构建上下文
        context = self._build_context(query_entities, neighbors, related_communities)

        # 5. 生成回答
        answer = self.llm_fn(question, context)

        return GraphRAGResult(
            answer=answer,
            entities_used=query_entities,
            communities_used=[c.community_id for c in related_communities],
            confidence=0.8 if query_entities else 0.3,
        )

    def _find_relevant_entities(self, question: str) -> List[str]:
        """从问题中找到相关的实体"""
        relevant = []
        for name in self.entities:
            if name in question:
                relevant.append(name)
        return relevant

    def _find_neighbors(self, entities: List[str]) -> Dict[str, List[str]]:
        """找到实体的邻居节点"""
        neighbors = {}
        for entity in entities:
            if entity in self.adjacency:
                neighbors[entity] = list(self.adjacency[entity])
            else:
                neighbors[entity] = []
        return neighbors

    def _find_related_communities(self, entities: List[str]) -> List[Community]:
        """找到包含这些实体的社区"""
        related = []
        for community in self.communities:
            if any(e in community.entities for e in entities):
                related.append(community)
        return related

    def _build_context(self, entities, neighbors, communities) -> str:
        """构建增强上下文"""
        parts = []

        # 实体描述
        for entity in entities:
            if entity in self.entities:
                e = self.entities[entity]
                parts.append(f"实体: {e.name} ({e.entity_type})")

        # 关系信息
        for entity, nbs in neighbors.items():
            if nbs:
                parts.append(f"{entity} 关联到: {', '.join(nbs)}")

        # 社区摘要
        for comm in communities:
            parts.append(comm.summary)

        return "\n".join(parts)

    def _mock_llm(self, question: str, context: str) -> str:
        """模拟 LLM 回答"""
        return f"[Graph RAG 回答] 基于知识图谱中的 {len(self.entities)} 个实体和 {len(self.communities)} 个社区，关于'{question}'的回答可以在相关实体关系中找到。"


# ============================================================
# 模块：使用示例
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  Graph RAG 知识图谱增强检索演示")
    print("=" * 60)

    # 模拟文档
    documents = [
        "Transformer 是一种基于自注意力机制的深度学习架构。Google 提出了 Transformer 模型。",
        "BERT 是基于 Transformer Encoder 的预训练模型。Google 开发了 BERT。",
        "GPT 是基于 Transformer Decoder 的模型。OpenAI 开发了 GPT 系列。",
        "RAG 结合了检索和生成。Microsoft 提出了 Graph RAG。",
        "注意力机制是 Transformer 的核心组件。自注意力机制能够捕捉长程依赖。",
    ]

    # 构建知识图谱
    builder = KnowledgeGraphBuilder()
    stats = builder.build(documents)

    print(f"\n知识图谱构建结果:")
    print(f"  实体数: {stats['num_entities']}")
    print(f"  关系数: {stats['num_relationships']}")
    print(f"  社区数: {stats['num_communities']}")
    print(f"  节点数: {stats['num_nodes']}")
    print(f"  边数: {stats['num_edges']}")

    # 查询
    engine = GraphRAGQueryEngine(builder)
    result = engine.query("Transformer 和 BERT 的关系是什么？")

    print(f"\n查询: Transformer 和 BERT 的关系是什么？")
    print(f"相关实体: {result.entities_used}")
    print(f"相关社区: {result.communities_used}")
    print(f"置信度: {result.confidence}")
    print(f"回答: {result.answer}")
