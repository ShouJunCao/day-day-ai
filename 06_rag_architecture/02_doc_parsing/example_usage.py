"""
example_usage.py — 文档解析器完整演示
演示 Markdown、HTML、TXT 格式的解析过程。
"""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from doc_parser import DocumentParser, MarkdownParser, HTMLParser, TXTParser


def demo_markdown_parsing():
    """演示 Markdown 解析"""
    print("=" * 60)
    print("  Markdown 解析演示")
    print("=" * 60)

    # 创建临时 Markdown 文件
    md_content = """# 深度学习基础

## 1. 什么是深度学习？

**深度学习**是机器学习的一个子领域，使用多层神经网络来学习数据的复杂表示。

### 核心概念
- 神经网络由多层神经元组成
- 每一层学习不同级别的特征
- 通过反向传播算法进行训练

## 2. 常见架构

1. **CNN**（卷积神经网络）：用于图像识别
2. **RNN**（循环神经网络）：用于序列数据
3. **Transformer**：用于自然语言处理

> 注意：Transformer 是目前最主流的架构

参考链接：[PyTorch 官网](https://pytorch.org)
"""

    # 写入临时文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(md_content)
        md_path = f.name

    try:
        # 解析
        result = MarkdownParser.parse(md_path)

        print(f"\n原始内容长度: {result.metadata['original_length']} 字符")
        print(f"解析后文本长度: {result.char_count} 字符")
        print(f"\n解析后的文本（前 200 字符）:")
        print("-" * 60)
        print(result.text[:200])
        print("...")
    finally:
        os.unlink(md_path)


def demo_html_parsing():
    """演示 HTML 解析"""
    print("\n" + "=" * 60)
    print("  HTML 解析演示")
    print("=" * 60)

    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>自然语言处理入门</title>
    <style>body { font-family: sans-serif; }</style>
    <script>console.log('This should be removed');</script>
</head>
<body>
    <h1>自然语言处理入门</h1>
    <p>自然语言处理（NLP）是<strong>人工智能</strong>的重要分支。</p>
    <p>它致力于让计算机能够<strong>理解</strong>和<strong>生成</strong>人类语言。</p>
    <ul>
        <li>文本分类</li>
        <li>情感分析</li>
        <li>机器翻译</li>
    </ul>
    <img src="example.png" alt="示例图片">
</body>
</html>"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html_content)
        html_path = f.name

    try:
        result = HTMLParser.parse(html_path)

        print(f"\n原始 HTML 长度: {result.metadata['original_length']} 字符")
        print(f"提取文本长度: {result.char_count} 字符")
        print(f"\n提取的纯文本:")
        print("-" * 60)
        print(result.text)
    finally:
        os.unlink(html_path)


def demo_txt_parsing():
    """演示 TXT 解析"""
    print("\n" + "=" * 60)
    print("  TXT 解析演示")
    print("=" * 60)

    txt_content = """这是一个纯文本文件示例。

纯文本文件不需要任何特殊处理，
直接读取内容即可。

常见的纯文本文件扩展名：
- .txt
- .log
- .csv
- .json
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(txt_content)
        txt_path = f.name

    try:
        result = TXTParser.parse(txt_path)

        print(f"\n文件路径: {result.source}")
        print(f"文件格式: {result.format}")
        print(f"文本长度: {result.char_count} 字符")
        print(f"\n内容:")
        print("-" * 60)
        print(result.text)
    finally:
        os.unlink(txt_path)


def demo_unified_parser():
    """演示统一文档解析器"""
    print("\n" + "=" * 60)
    print("  统一解析器 — DocumentParser 演示")
    print("=" * 60)

    # 创建多个临时文件
    files = []
    try:
        # Markdown 文件
        md_path = tempfile.mktemp(suffix=".md")
        Path(md_path).write_text("# 测试文档\n\n这是一段测试内容。", encoding="utf-8")
        files.append(md_path)

        # TXT 文件
        txt_path = tempfile.mktemp(suffix=".txt")
        Path(txt_path).write_text("这是纯文本内容。\n第二行。", encoding="utf-8")
        files.append(txt_path)

        # 不支持的格式
        unsupported_path = tempfile.mktemp(suffix=".xyz")
        Path(unsupported_path).write_text("不支持的格式", encoding="utf-8")
        files.append(unsupported_path)

        print(f"\n待解析文件数: {len(files)}")
        print("文件列表:")
        for f in files:
            print(f"  {Path(f).suffix:6s} → {Path(f).name}")

        # 批量解析
        print("\n开始批量解析:")
        results = DocumentParser.parse_batch(files)

        print(f"\n成功解析: {len(results)}/{len(files)} 个文件")
        for doc in results:
            print(f"  [{doc.format}] {doc.char_count} 字符")
    finally:
        for f in files:
            if os.path.exists(f):
                os.unlink(f)


if __name__ == "__main__":
    demo_markdown_parsing()
    demo_html_parsing()
    demo_txt_parsing()
    demo_unified_parser()
