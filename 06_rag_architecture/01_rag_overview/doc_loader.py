"""
doc_loader.py — 文档加载器实现
支持多种文档格式的加载和文本提取。
"""
from pathlib import Path
from typing import Optional


class DocumentLoader:
    """
    文档加载器：将各种格式的文件转换为纯文本。

    支持的格式：
    - .txt: 直接读取
    - .md: 去除 Markdown 标记
    - .html: 去除 HTML 标签
    """

    @staticmethod
    def load_txt(filepath: str) -> str:
        """
        加载纯文本文件。

        参数：
        - filepath (str): 文件路径

        返回：
        - str: 文件内容
        """
        path = Path(filepath)
        return path.read_text(encoding="utf-8")

    @staticmethod
    def load_markdown(filepath: str) -> str:
        """
        加载 Markdown 文件，去除格式标记。

        参数：
        - filepath (str): 文件路径

        返回：
        - str: 去除标记后的纯文本
        """
        text = Path(filepath).read_text(encoding="utf-8")
        # 去除标题标记
        text = text.replace("# ", "").replace("## ", "")
        # 去除粗体和斜体标记
        text = text.replace("**", "").replace("*", "")
        return text.strip()

    @staticmethod
    def load_html(filepath: str) -> str:
        """
        加载 HTML 文件，提取纯文本。

        参数：
        - filepath (str): 文件路径

        返回：
        - str: 去除 HTML 标签后的纯文本
        """
        import re
        html = Path(filepath).read_text(encoding="utf-8")
        # 去除所有 HTML 标签
        text = re.sub(r"<[^>]+>", " ", html)
        # 清理多余空白
        text = " ".join(text.split())
        return text

    @classmethod
    def load(cls, filepath: str) -> Optional[str]:
        """
        根据文件扩展名自动选择加载方式。

        参数：
        - filepath (str): 文件路径

        返回：
        - str 或 None: 加载的文本内容，不支持的格式返回 None
        """
        ext = Path(filepath).suffix.lower()
        loaders = {
            ".txt": cls.load_txt,
            ".md": cls.load_markdown,
            ".html": cls.load_html,
        }
        loader = loaders.get(ext)
        if loader is None:
            print(f"不支持的文件格式: {ext}")
            return None
        return loader(filepath)


if __name__ == "__main__":
    print("DocumentLoader 示例:")
    print("  支持格式: .txt, .md, .html")
    print("  用法: DocumentLoader.load('file.txt')")
