"""
multimodal_rag.py — 多模态 RAG（图片、表格、代码块处理）实现
"""
import os
import re
import json
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class MultimodalContent:
    """多模态内容"""
    content_id: str
    content_type: str  # "image", "table", "code", "text"
    content: str
    metadata: dict = field(default_factory=dict)


@dataclass
class MultimodalChunk:
    """多模态文本块"""
    chunk_id: str
    text: str
    multimodal_contents: List[MultimodalContent] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class MultimodalSearchResult:
    """多模态检索结果"""
    chunk_id: str
    text: str
    score: float
    images: List[str] = field(default_factory=list)
    tables: List[str] = field(default_factory=list)
    codes: List[str] = field(default_factory=list)


# ============================================================
# 模块：Markdown 多模态解析器
# ============================================================

class MarkdownMultimodalParser:
    """
    Markdown 多模态解析器：解析 Markdown 中的图片、表格和代码块。
    """

    def __init__(self):
        self.image_pattern = r"!\[([^\]]*)\]\(([^)]+)\)"
        self.table_pattern = r"(\|[^\n]+\n\|[^\n]+\n)"
        self.code_pattern = r"```(\w+)?\n([\s\S]*?)```"

    def parse(self, filepath: str) -> Tuple[str, List[MultimodalContent]]:
        """解析 Markdown 文件，提取文本和多模态内容"""
        content = Path(filepath).read_text(encoding="utf-8")
        images = self._extract_images(content)
        tables = self._extract_tables(content)
        codes = self._extract_codes(content)
        text = self._clean_markdown(content)
        return text, images + tables + codes

    def _extract_images(self, content: str) -> List[MultimodalContent]:
        images = []
        for i, match in enumerate(re.finditer(self.image_pattern, content)):
            images.append(MultimodalContent(
                content_id=f"img_{i}",
                content_type="image",
                content=match.group(2),
                metadata={"alt_text": match.group(1), "index": i},
            ))
        return images

    def _extract_tables(self, content: str) -> List[MultimodalContent]:
        tables = []
        for i, match in enumerate(re.finditer(self.table_pattern, content)):
            tables.append(MultimodalContent(
                content_id=f"table_{i}",
                content_type="table",
                content=match.group(1).strip(),
                metadata={"index": i},
            ))
        return tables

    def _extract_codes(self, content: str) -> List[MultimodalContent]:
        codes = []
        for i, match in enumerate(re.finditer(self.code_pattern, content)):
            codes.append(MultimodalContent(
                content_id=f"code_{i}",
                content_type="code",
                content=match.group(2).strip(),
                metadata={"language": match.group(1) or "unknown", "index": i},
            ))
        return codes

    def _clean_markdown(self, content: str) -> str:
        text = re.sub(self.image_pattern, "", content)
        text = re.sub(self.code_pattern, "", text)
        text = re.sub(r"\|[^\n]+\n\|[^\n]+\n", "", text)
        text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
        text = text.replace("**", "").replace("*", "")
        return text.strip()


# ============================================================
# 模块：图片内容提取器
# ============================================================

class ImageContentExtractor:
    """图片内容提取器：使用 OCR 和视觉描述模型"""

    def extract(self, image_path: str) -> dict:
        ocr_text = self._mock_ocr(image_path)
        description = self._mock_description(image_path)
        return {"ocr_text": ocr_text, "description": description, "image_path": image_path}

    def _mock_ocr(self, image_path: str) -> str:
        return f"[OCR] 从 {Path(image_path).name} 提取的文字。"

    def _mock_description(self, image_path: str) -> str:
        return f"[描述] {Path(image_path).stem} 的图片。"


# ============================================================
# 模块：表格内容提取器
# ============================================================

class TableContentExtractor:
    """表格内容提取器"""

    def extract(self, table_content: str) -> dict:
        rows = table_content.strip().split("\n")
        if len(rows) < 2:
            return {"headers": [], "data": [], "summary": "空表格"}
        headers = [h.strip() for h in rows[0].split("|") if h.strip()]
        data_rows = []
        for row in rows[2:]:
            cells = [c.strip() for c in row.split("|") if c.strip()]
            if cells:
                data_rows.append(cells)
        return {
            "headers": headers,
            "data": data_rows,
            "summary": f"表格包含 {len(headers)} 列、{len(data_rows)} 行数据。",
        }


# ============================================================
# 模块：多模态检索器
# ============================================================

class MultimodalRetriever:
    """多模态检索器"""

    def __init__(self, embedding_fn):
        self.embedding_fn = embedding_fn
        self.chunks: List[MultimodalChunk] = []
        self.vectors: List[List[float]] = []

    def add_chunk(self, chunk: MultimodalChunk):
        search_text = chunk.text
        for c in chunk.multimodal_contents:
            if c.content_type == "image":
                search_text += f" {c.metadata.get('alt_text', '')}"
            elif c.content_type == "table":
                search_text += f" {c.content}"
            elif c.content_type == "code":
                search_text += f" {c.content}"
        vector = self.embedding_fn(search_text)
        self.chunks.append(chunk)
        self.vectors.append(vector)

    def search(self, query: str, top_k: int = 5) -> List[MultimodalSearchResult]:
        qv = self.embedding_fn(query)
        scores = [(i, self._cosine(qv, v)) for i, v in enumerate(self.vectors)]
        scores.sort(key=lambda x: x[1], reverse=True)
        results = []
        for idx, score in scores[:top_k]:
            chunk = self.chunks[idx]
            results.append(MultimodalSearchResult(
                chunk_id=chunk.chunk_id,
                text=chunk.text,
                score=score,
                images=[c.content for c in chunk.multimodal_contents if c.content_type == "image"],
                tables=[c.content for c in chunk.multimodal_contents if c.content_type == "table"],
                codes=[c.content for c in chunk.multimodal_contents if c.content_type == "code"],
            ))
        return results

    def _cosine(self, v1, v2):
        dot = sum(a * b for a, b in zip(v1, v2))
        n1 = sum(a * a for a in v1) ** 0.5
        n2 = sum(b * b for b in v2) ** 0.5
        return dot / (n1 * n2) if n1 and n2 else 0.0


def simple_embedding(text: str) -> List[float]:
    vector = [0.0] * 128
    for char in text.replace(" ", ""):
        idx = ord(char) % 128
        vector[idx] += 1.0
    norm = sum(v * v for v in vector) ** 0.5
    return [v / norm for v in vector] if norm else vector


if __name__ == "__main__":
    print("=" * 60)
    print("  多模态 RAG 演示")
    print("=" * 60)

    parser = MarkdownMultimodalParser()
    retriever = MultimodalRetriever(simple_embedding)

    md = """# Transformer

![架构图](attn.png)

| 组件 | 功能 |
|------|------|
| 注意力 | 依赖关系 |

```python
class Model: pass
```
"""
    import tempfile
    fd, path = tempfile.mkstemp(suffix=".md")
    os.write(fd, md.encode("utf-8")); os.close(fd)
    text, contents = parser.parse(path)
    retriever.add_chunk(MultimodalChunk("doc_1", text, contents))
    os.unlink(path)

    results = retriever.search("Transformer 组件")
    for r in results:
        print(f"  分数: {r.score:.3f}")
        if r.images: print(f"  📷 {r.images}")
        if r.tables: print(f"  📊 {r.tables}")
        if r.codes: print(f"  💻 {r.codes}")
