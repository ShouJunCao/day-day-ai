"""
knowledge_base_qa.py — 企业知识库问答系统实战
综合运用模块五和模块六的所有知识，构建完整的 RAG 系统。
"""
import os
import re
import json
import time
from typing import Optional, List, Dict, Tuple
from pathlib import Path
from dataclasses import dataclass, field


# ============================================================
# 模块：数据结构
# ============================================================

@dataclass
class Document:
    """文档数据"""
    doc_id: str
    text: str
    source: str
    metadata: dict = field(default_factory=dict)


@dataclass
class Chunk:
    """文本块"""
    chunk_id: str
    doc_id: str
    text: str
    index: int
    metadata: dict = field(default_factory=dict)


@dataclass
class SearchResult:
    """检索结果"""
    chunk_id: str
    doc_id: str
    text: str
    score: float
    metadata: dict = field(default_factory=dict)


# ============================================================
# 模块：文档解析（6.2/6.3 节知识）
# ============================================================

class DocumentParser:
    """
    文档解析器：支持多种格式。
    综合了 6.2 和 6.3 节的文档解析知识。
    """

    @staticmethod
    def parse_text(filepath: str) -> str:
        """解析 TXT 文件"""
        return Path(filepath).read_text(encoding="utf-8").strip()

    @staticmethod
    def parse_markdown(filepath: str) -> str:
        """解析 Markdown 文件"""
        text = Path(filepath).read_text(encoding="utf-8")
        # 去除代码块
        text = re.sub(r"```[\s\S]*?```", "", text)
        # 去除图片标记
        text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
        # 提取链接文字
        text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)
        # 去除标题标记
        text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
        # 去除粗体/斜体
        text = text.replace("**", "").replace("*", "")
        # 去除引用标记
        text = re.sub(r"^>\s+", "", text, flags=re.MULTILINE)
        return text.strip()

    @staticmethod
    def parse_html(filepath: str) -> str:
        """解析 HTML 文件"""
        html = Path(filepath).read_text(encoding="utf-8")
        # 去除脚本和样式
        text = re.sub(r"<script[\s\S]*?</script>", "", html, flags=re.IGNORECASE)
        text = re.sub(r"<style[\s\S]*?</style>", "", text, flags=re.IGNORECASE)
        # 去除标签
        text = re.sub(r"<[^>]+>", " ", text)
        # 解码实体
        text = text.replace("&amp;", "&").replace("&lt;", "<")
        text = text.replace("&gt;", ">").replace("&nbsp;", " ")
        # 清理空白
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @classmethod
    def parse(cls, filepath: str) -> Optional[Document]:
        """根据扩展名自动解析"""
        ext = Path(filepath).suffix.lower()
        parsers = {
            ".txt": cls.parse_text,
            ".md": cls.parse_markdown,
            ".html": cls.parse_html,
        }
        parser = parsers.get(ext)
        if parser is None:
            print(f"[警告] 不支持的格式: {ext}")
            return None

        try:
            text = parser(filepath)
            return Document(
                doc_id=Path(filepath).stem,
                text=text,
                source=str(filepath),
                metadata={"format": ext, "length": len(text)},
            )
        except Exception as e:
            print(f"[错误] 解析失败: {filepath} - {e}")
            return None


# ============================================================
# 模块：文本分块（6.4 节知识）
# ============================================================

class TextChunker:
    """
    文本分块器：使用递归分块策略。
    综合了 6.4 节的分块知识。
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, doc: Document) -> List[Chunk]:
        """将文档切分为文本块"""
        text = doc.text
        chunks = []

        # 先按段落分割
        paragraphs = re.split(r"\n\n+", text)
        current_chunk = []
        current_length = 0
        chunk_index = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # 如果单个段落超过 chunk_size，按句子分割
            if len(para) > self.chunk_size:
                sentences = re.split(r"(?<=[。！？.!?])\s*", para)
                for sent in sentences:
                    sent = sent.strip()
                    if not sent:
                        continue
                    if current_length + len(sent) > self.chunk_size and current_chunk:
                        chunks.append(Chunk(
                            chunk_id=f"{doc.doc_id}_{chunk_index}",
                            doc_id=doc.doc_id,
                            text=" ".join(current_chunk),
                            index=chunk_index,
                            metadata={"doc_source": doc.source},
                        ))
                        chunk_index += 1
                        # 保留重叠
                        overlap_parts = []
                        overlap_len = 0
                        for s in reversed(current_chunk):
                            if overlap_len + len(s) <= self.overlap:
                                overlap_parts.insert(0, s)
                                overlap_len += len(s)
                            else:
                                break
                        current_chunk = overlap_parts
                        current_length = overlap_len

                    current_chunk.append(sent)
                    current_length += len(sent)
            else:
                if current_length + len(para) > self.chunk_size and current_chunk:
                    chunks.append(Chunk(
                        chunk_id=f"{doc.doc_id}_{chunk_index}",
                        doc_id=doc.doc_id,
                        text=" ".join(current_chunk),
                        index=chunk_index,
                        metadata={"doc_source": doc.source},
                    ))
                    chunk_index += 1
                    current_chunk = []
                    current_length = 0

                current_chunk.append(para)
                current_length += len(para)

        if current_chunk:
            chunks.append(Chunk(
                chunk_id=f"{doc.doc_id}_{chunk_index}",
                doc_id=doc.doc_id,
                text=" ".join(current_chunk),
                index=chunk_index,
                metadata={"doc_source": doc.source},
            ))

        return chunks


# ============================================================
# 模块：向量检索（模块五知识）
# ============================================================

class SimpleVectorIndex:
    """
    简易向量索引：使用余弦相似度进行检索。
    综合了模块五的向量检索知识。
    """

    def __init__(self, embedding_fn):
        """
        参数：
        - embedding_fn: 将文本编码为向量的函数
        """
        self.embedding_fn = embedding_fn
        self.chunks: List[Chunk] = []
        self.vectors: List[List[float]] = []

    def add_chunks(self, chunks: List[Chunk]):
        """添加文本块到索引"""
        for chunk in chunks:
            vector = self.embedding_fn(chunk.text)
            self.chunks.append(chunk)
            self.vectors.append(vector)

    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """检索最相关的文本块"""
        query_vector = self.embedding_fn(query)
        scores = []

        for i, vec in enumerate(self.vectors):
            score = self._cosine_similarity(query_vector, vec)
            scores.append((i, score))

        # 按分数降序
        scores.sort(key=lambda x: x[1], reverse=True)
        results = []
        for idx, score in scores[:top_k]:
            chunk = self.chunks[idx]
            results.append(SearchResult(
                chunk_id=chunk.chunk_id,
                doc_id=chunk.doc_id,
                text=chunk.text,
                score=score,
                metadata=chunk.metadata,
            ))

        return results

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)


# ============================================================
# 模块：重排序（6.6 节知识）
# ============================================================

class SimpleReranker:
    """
    简易重排序器：基于关键词匹配度重排序。
    模拟了 6.6 节的重排序知识。
    """

    def rerank(self, query: str, results: List[SearchResult], top_k: int = 3) -> List[SearchResult]:
        """对检索结果重排序"""
        query_words = set(query.replace(" ", ""))

        reranked = []
        for result in results:
            doc_words = set(result.text.replace(" ", ""))
            overlap = len(query_words & doc_words) / max(len(query_words), 1)
            # 结合原始分数和匹配度
            combined_score = result.score * 0.5 + overlap * 0.5
            reranked.append(SearchResult(
                chunk_id=result.chunk_id,
                doc_id=result.doc_id,
                text=result.text,
                score=combined_score,
                metadata=result.metadata,
            ))

        reranked.sort(key=lambda x: x.score, reverse=True)
        return reranked[:top_k]


# ============================================================
# 模块：上下文管理（6.7 节知识）
# ============================================================

class ContextManager:
    """
    上下文管理器：过滤、压缩、重排序。
    综合了 6.7 节的上下文管理知识。
    """

    def __init__(self, threshold: float = 0.3, max_tokens: int = 2000):
        self.threshold = threshold
        self.max_tokens = max_tokens

    def process(self, query: str, results: List[SearchResult]) -> str:
        """处理检索结果为最终上下文"""
        # 1. 过滤低分结果
        filtered = [r for r in results if r.score >= self.threshold]
        if not filtered:
            filtered = results[:1]  # 至少保留一个

        # 2. 按相关性排序
        filtered.sort(key=lambda x: x.score, reverse=True)

        # 3. 拼接为上下文
        context_parts = []
        total_tokens = 0
        for r in filtered:
            token_estimate = len(r.text) // 2  # 粗略估计
            if total_tokens + token_estimate > self.max_tokens:
                break
            context_parts.append(f"[文档 {r.doc_id}] {r.text}")
            total_tokens += token_estimate

        return "\n\n".join(context_parts)


# ============================================================
# 模块：Prompt 构建与 LLM 调用（6.1 节知识）
# ============================================================

class PromptBuilder:
    """
    Prompt 构建器：构建 RAG 系统的 Prompt。
    综合了 6.1 节的 RAG 流程知识。
    """

    RAG_PROMPT = """你是一个专业的知识库助手。请根据以下参考资料回答用户的问题。

参考资料：
{context}

问题：{question}

请根据参考资料提供准确、简洁的回答。如果参考资料中没有相关信息，请直接说明。"""

    @classmethod
    def build(cls, question: str, context: str) -> str:
        """构建 RAG Prompt"""
        return cls.RAG_PROMPT.format(context=context, question=question)


class MockLLM:
    """
    模拟 LLM：用于教学演示。
    实际项目中应替换为真实的 LLM API 调用。
    """

    @staticmethod
    def generate(prompt: str) -> str:
        """生成回答（模拟）"""
        # 实际项目中：
        # from openai import OpenAI
        # client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # response = client.chat.completions.create(
        #     model="gpt-4",
        #     messages=[{"role": "user", "content": prompt}],
        # )
        # return response.choices[0].message.content

        return f"[模拟 LLM 回答] 根据提供的参考资料，这个问题的答案可以在相关文档中找到。"


# ============================================================
# 模块：完整的知识库问答系统
# ============================================================

class KnowledgeBaseQA:
    """
    企业知识库问答系统：综合运用所有 RAG 知识。

    完整流程：
    1. 文档加载与解析
    2. 文本分块
    3. 向量索引构建
    4. 查询 → 检索 → 重排序 → 上下文管理
    5. Prompt 构建 → LLM 生成回答
    """

    def __init__(self, embedding_fn, llm_fn=None):
        """
        初始化知识库问答系统。

        参数：
        - embedding_fn: 文本编码为向量的函数
        - llm_fn: LLM 生成函数（可选，默认使用 MockLLM）
        """
        self.parser = DocumentParser()
        self.chunker = TextChunker(chunk_size=500, overlap=50)
        self.vector_index = SimpleVectorIndex(embedding_fn)
        self.reranker = SimpleReranker()
        self.context_manager = ContextManager(threshold=0.3, max_tokens=2000)
        self.llm = llm_fn or MockLLM.generate
        self.documents: List[Document] = []
        self.all_chunks: List[Chunk] = []

    def ingest(self, filepaths: List[str]):
        """
        导入文档到知识库。

        参数：
        - filepaths (list[str]): 文件路径列表
        """
        print(f"\n{'=' * 50}")
        print(f"  知识库导入")
        print(f"{'=' * 50}")

        for filepath in filepaths:
            print(f"\n处理: {filepath}")

            # 1. 解析
            doc = self.parser.parse(filepath)
            if doc is None:
                continue
            self.documents.append(doc)
            print(f"  ✓ 解析成功: {len(doc.text)} 字符")

            # 2. 分块
            chunks = self.chunker.chunk(doc)
            self.all_chunks.extend(chunks)
            print(f"  ✓ 分块完成: {len(chunks)} 个块")

            # 3. 建索引
            self.vector_index.add_chunks(chunks)
            print(f"  ✓ 索引构建完成")

        print(f"\n导入完成:")
        print(f"  文档数: {len(self.documents)}")
        print(f"  文本块数: {len(self.all_chunks)}")

    def query(self, question: str, top_k: int = 5) -> str:
        """
        查询知识库。

        参数：
        - question (str): 用户问题
        - top_k (int): 检索结果数

        返回：
        - str: LLM 生成的回答
        """
        # 1. 向量检索
        results = self.vector_index.search(question, top_k=top_k)

        # 2. 重排序
        reranked = self.reranker.rerank(question, results, top_k=3)

        # 3. 上下文管理
        context = self.context_manager.process(question, reranked)

        # 4. 构建 Prompt
        prompt = PromptBuilder.build(question, context)

        # 5. LLM 生成
        answer = self.llm(prompt)

        return answer

    def get_stats(self) -> dict:
        """获取知识库统计信息"""
        return {
            "documents": len(self.documents),
            "chunks": len(self.all_chunks),
            "total_chars": sum(len(d.text) for d in self.documents),
        }


# ============================================================
# 模块：简易 Embedding 函数（演示用）
# ============================================================

def simple_embedding(text: str) -> List[float]:
    """
    简易 Embedding 函数：基于词频的伪向量。
    仅用于演示，实际项目应使用真实的 Embedding 模型。
    """
    # 使用字符 n-gram 的哈希作为伪向量
    vector = [0.0] * 128
    words = list(text.replace(" ", ""))
    for i, char in enumerate(words):
        idx = ord(char) % 128
        vector[idx] += 1.0
    # 归一化
    norm = sum(v * v for v in vector) ** 0.5
    if norm > 0:
        vector = [v / norm for v in vector]
    return vector


# ============================================================
# 主程序
# ============================================================

if __name__ == "__main__":
    import tempfile

    print("=" * 60)
    print("  企业知识库问答系统 — 实战演示")
    print("=" * 60)

    # 创建临时测试文档
    docs = []
    for i in range(3):
        fd, path = tempfile.mkstemp(suffix=".txt")
        os.write(fd, f"这是测试文档 {i + 1}。".encode("utf-8"))
        os.close(fd)
        docs.append(path)

    # 初始化系统
    kb = KnowledgeBaseQA(embedding_fn=simple_embedding)

    # 导入文档
    kb.ingest(docs)

    # 查询
    question = "测试文档的内容是什么？"
    print(f"\n{'=' * 50}")
    print(f"  用户问题: {question}")
    print(f"{'=' * 50}")

    answer = kb.query(question)
    print(f"\n系统回答: {answer}")

    # 统计信息
    stats = kb.get_stats()
    print(f"\n知识库统计: {stats}")

    # 清理临时文件
    for path in docs:
        os.unlink(path)
