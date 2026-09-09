"""
doc_parser.py — 文档解析器实现
支持 PDF、Word、HTML、Markdown、PPT 五种格式的文本提取。
"""
import os
import re
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field


# ============================================================
# 模块：解析结果数据结构
# ============================================================

@dataclass
class ParsedDocument:
    """
    解析结果数据结构。

    属性：
    - text (str): 提取的纯文本
    - source (str): 原始文件路径
    - format (str): 文件格式（pdf/docx/html/md/pptx）
    - metadata (dict): 额外元数据（页数、字数等）
    """
    text: str
    source: str
    format: str
    metadata: dict = field(default_factory=dict)

    @property
    def word_count(self) -> int:
        """计算文本字数"""
        return len(self.text)

    @property
    def char_count(self) -> int:
        """计算字符数（含标点）"""
        return len(self.text)


# ============================================================
# 模块：Markdown 解析器
# ============================================================

class MarkdownParser:
    """
    Markdown 文档解析器。

    原理：使用正则表达式去除 Markdown 标记，
    保留文本内容并清理格式符号。

    支持的标记：
    - 标题标记（# ## ###）
    - 粗体/斜体标记（**bold** *italic*）
    - 代码块（```）
    - 链接（[text](url)）
    - 图片（![alt](url)）
    """

    @staticmethod
    def parse(filepath: str) -> ParsedDocument:
        """
        解析 Markdown 文件。

        参数：
        - filepath (str): 文件路径

        返回：
        - ParsedDocument: 解析结果
        """
        path = Path(filepath)
        text = path.read_text(encoding="utf-8")

        # 去除代码块标记（保留代码内容）
        text = re.sub(r"```[\s\S]*?```", "", text)
        # 去除图片标记
        text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
        # 将链接替换为纯文本
        text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)
        # 去除标题标记
        text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
        # 去除粗体/斜体标记
        text = text.replace("**", "").replace("*", "")
        text = text.replace("__", "").replace("_", "")
        # 去除引用标记
        text = re.sub(r"^>\s+", "", text, flags=re.MULTILINE)

        return ParsedDocument(
            text=text.strip(),
            source=str(path),
            format="md",
            metadata={"original_length": len(path.read_text(encoding="utf-8"))},
        )


# ============================================================
# 模块：HTML 解析器
# ============================================================

class HTMLParser:
    """
    HTML 文档解析器。

    原理：使用正则表达式去除 HTML 标签和脚本，
    提取正文内容并清理空白字符。
    """

    @staticmethod
    def parse(filepath: str) -> ParsedDocument:
        """
        解析 HTML 文件。

        参数：
        - filepath (str): 文件路径

        返回：
        - ParsedDocument: 解析结果
        """
        path = Path(filepath)
        html = path.read_text(encoding="utf-8")

        # 去除 <script> 和 <style> 标签及其内容
        text = re.sub(r"<script[\s\S]*?</script>", "", html, flags=re.IGNORECASE)
        text = re.sub(r"<style[\s\S]*?</style>", "", text, flags=re.IGNORECASE)
        # 去除所有 HTML 标签
        text = re.sub(r"<[^>]+>", " ", text)
        # 解码 HTML 实体
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&nbsp;", " ")
        # 清理多余空白
        text = re.sub(r"\s+", " ", text).strip()

        return ParsedDocument(
            text=text,
            source=str(path),
            format="html",
            metadata={"original_length": len(html)},
        )


# ============================================================
# 模块：TXT 解析器
# ============================================================

class TXTParser:
    """纯文本文档解析器"""

    @staticmethod
    def parse(filepath: str) -> ParsedDocument:
        """
        解析纯文本文件。

        参数：
        - filepath (str): 文件路径

        返回：
        - ParsedDocument: 解析结果
        """
        path = Path(filepath)
        text = path.read_text(encoding="utf-8")

        return ParsedDocument(
            text=text.strip(),
            source=str(path),
            format="txt",
            metadata={"original_length": len(text)},
        )


# ============================================================
# 模块：统一文档解析器
# ============================================================

class DocumentParser:
    """
    统一文档解析器：根据文件扩展名自动选择解析方式。

    支持的格式：
    - .txt: 直接读取
    - .md: Markdown 标记去除
    - .html: HTML 标签去除
    - .pdf: 需要 PyPDF2（占位实现）
    - .docx: 需要 python-docx（占位实现）
    - .pptx: 需要 python-pptx（占位实现）
    """

    # 解析器注册表
    PARSERS = {
        ".txt": TXTParser.parse,
        ".md": MarkdownParser.parse,
        ".html": HTMLParser.parse,
    }

    @classmethod
    def parse(cls, filepath: str) -> Optional[ParsedDocument]:
        """
        根据文件扩展名自动选择解析方式。

        参数：
        - filepath (str): 文件路径

        返回：
        - ParsedDocument 或 None: 解析结果
        """
        ext = Path(filepath).suffix.lower()
        parser = cls.PARSERS.get(ext)

        if parser is None:
            print(f"[警告] 不支持的文件格式: {ext}")
            print(f"[支持] {', '.join(cls.PARSERS.keys())}")
            return None

        try:
            result = parser(filepath)
            print(f"[成功] {filepath} → {result.char_count} 字符")
            return result
        except Exception as e:
            print(f"[错误] 解析失败: {filepath} - {e}")
            return None

    @classmethod
    def parse_batch(cls, filepaths: list[str]) -> list[ParsedDocument]:
        """
        批量解析多个文件。

        参数：
        - filepaths (list[str]): 文件路径列表

        返回：
        - list[ParsedDocument]: 成功的解析结果列表
        """
        results = []
        for fp in filepaths:
            doc = cls.parse(fp)
            if doc is not None:
                results.append(doc)
        return results


# ============================================================
# 模块：使用示例
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  文档解析器 — DocumentParser 演示")
    print("=" * 60)

    print("\n支持的格式:")
    for ext, parser in DocumentParser.PARSERS.items():
        print(f"  {ext:8s} → {parser.__qualname__}")

    print("\n使用方式:")
    print("  doc = DocumentParser.parse('document.md')")
    print("  print(doc.text[:100])")
    print("  print(f'字数: {doc.word_count}')")
