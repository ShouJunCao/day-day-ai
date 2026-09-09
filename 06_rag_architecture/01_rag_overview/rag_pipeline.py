"""
rag_pipeline.py — RAG 检索增强生成管道实现
包含文档加载、分块、Embedding、检索、Prompt 构建的完整流程。
用于教学演示，帮助理解 RAG 系统的核心组件和工作流程。
"""
import os
import math
from typing import Optional
from dataclasses import dataclass, field


# ============================================================
# 模块：文档与分块
# ============================================================

@dataclass
class Document:
    """
    文档对象：包含文本内容和元数据。

    属性：
    - text (str): 文档文本内容
    - metadata (dict): 文档元数据（分类、来源等）
    - doc_id (str): 文档唯一标识
    """
    text: str
    metadata: dict = field(default_factory=dict)
    doc_id: str = ""


class DocumentChunker:
    """
    文档分块器：将长文档切分为固定大小的文本块。

    分块策略：
    1. 按固定字符数分割（控制块大小）
    2. 滑动窗口重叠（避免上下文断裂）

    参数：
    - chunk_size: 每块最大字符数（默认 500）
    - overlap: 相邻块之间的重叠字符数（默认 50）
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_document(self, doc: Document) -> list[Document]:
        """
        将长文档切分为多个文本块。

        使用滑动窗口策略：
        - 每块最大 chunk_size 字符
        - 相邻块之间重叠 overlap 字符
        - 避免语义被硬切断

        参数：
        - doc (Document): 原始文档

        返回：
        - list[Document]: 切分后的文本块列表
        """
        text = doc.text
        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]
            chunk_id = f"{doc.doc_id}_chunk_{len(chunks)}"

            chunks.append(Document(
                text=chunk_text,
                metadata={**doc.metadata, "chunk_index": len(chunks)},
                doc_id=chunk_id,
            ))
            start = end - self.overlap  # 滑动窗口

        return chunks


# ============================================================
# 模块：RAG 管道
# ============================================================

class RAGPipeline:
    """
    RAG（检索增强生成）管道：整合检索和生成的完整流程。

    核心流程：
    1. 文档加载 → 2. 分块 → 3. Embedding → 4. 存储
    5. 查询 Embedding → 6. 检索 Top-K → 7. 构建 Prompt → 8. LLM 生成

    参数：
    - chunk_size: 分块大小
    - chunk_overlap: 分块重叠
    - top_k: 检索返回的文档数
    """

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        top_k: int = 3,
    ):
        self.chunker = DocumentChunker(chunk_size, chunk_overlap)
        self.top_k = top_k
        self._documents: list[Document] = []
        self._chunks: list[Document] = []

    def load_documents(
        self, texts: list[str], metadata_list: Optional[list[dict]] = None
    ) -> None:
        """
        加载文档并分块。

        参数：
        - texts (list[str]): 文档文本列表
        - metadata_list (list[dict]): 对应的元数据列表
        """
        for i, text in enumerate(texts):
            meta = metadata_list[i] if metadata_list else {}
            doc = Document(text=text, metadata=meta, doc_id=f"doc_{i}")
            self._documents.append(doc)
            chunks = self.chunker.chunk_document(doc)
            self._chunks.extend(chunks)

    def _embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        将文本列表编码为向量（占位方法）。
        实际项目中替换为 BGE-M3 或 OpenAI Embedding。
        """
        import random
        random.seed(42)
        return [
            [random.gauss(0, 1) for _ in range(768)]
            for _ in texts
        ]

    def _search(self, query_vector: list[float], top_k: int) -> list[Document]:
        """
        向量检索（占位方法）。
        实际项目中替换为 Milvus/Qdrant 检索。
        """
        return self._chunks[:top_k]

    def _build_prompt(self, query: str, context: list[Document]) -> str:
        """
        构建 RAG Prompt：将查询和检索到的上下文组合。

        参数：
        - query (str): 用户查询
        - context (list[Document]): 检索到的相关文档

        返回：
        - str: 构建好的 Prompt
        """
        context_text = "\n\n".join(
            f"参考资料 {i+1}:\n{doc.text}"
            for i, doc in enumerate(context)
        )

        prompt = f"""你是一个知识助手。请根据以下参考资料回答用户的问题。

参考资料：
{context_text}

用户问题：{query}

请基于上述参考资料给出准确的回答。如果参考资料中没有相关信息，请明确告知用户。"""
        return prompt

    def query(self, question: str) -> dict:
        """
        执行完整的 RAG 查询流程。

        参数：
        - question (str): 用户问题

        返回：
        - dict: 包含查询结果的字典
        """
        # 1. 查询 Embedding
        query_vector = self._embed_documents([question])[0]

        # 2. 检索相关文档
        context_docs = self._search(query_vector, self.top_k)

        # 3. 构建 Prompt
        prompt = self._build_prompt(question, context_docs)

        return {
            "question": question,
            "context": [doc.text for doc in context_docs],
            "prompt": prompt,
            "num_docs_retrieved": len(context_docs),
        }
