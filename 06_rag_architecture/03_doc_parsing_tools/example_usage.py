"""
example_usage.py — 高级文档解析工具演示
演示 Unstructured、MinerU、LlamaParse 等工具的使用方法。
"""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from doc_parsing_tools import (
    UnstructuredParser,
    MinerUParser,
    LlamaParseParser,
    ParsingToolScheduler,
)


def demo_unstructured():
    """演示 Unstructured 解析器"""
    print("=" * 60)
    print("  Unstructured 解析器演示")
    print("=" * 60)

    parser = UnstructuredParser(strategy="auto")
    print(f"\nUnstructured 可用状态: {'✅ 已安装' if parser._available else '❌ 未安装'}")
    print(f"支持格式: {', '.join(parser.SUPPORTED_FORMATS)}")
    print(f"解析策略: {parser.strategy}")

    if parser._available:
        print("\n使用方式:")
        print("  parser = UnstructuredParser(strategy='auto')")
        print("  result = parser.parse('document.pdf')")
        print(f"  print(f'元素数: {{result.metadata[\"num_elements\"]}}')")
    else:
        print("\n安装命令: pip install unstructured")


def demo_mineru():
    """演示 MinerU 解析器"""
    print("\n" + "=" * 60)
    print("  MinerU 解析器演示")
    print("=" * 60)

    parser = MinerUParser()
    print(f"\nMinerU 可用状态: {'✅ 已安装' if parser._available else '❌ 未安装'}")
    print(f"模型名称: {parser.model_name}")

    if not parser._available:
        print("\nMinerU 是基于深度学习的 PDF 解析工具")
        print("安装命令: pip install magic-pdf")
        print("\n特点:")
        print("  • 使用 AI 模型识别文档结构")
        print("  • 支持复杂 PDF 的版面分析")
        print("  • 能准确提取表格、公式、图片")
        print("  • 适用于学术论文和技术文档")


def demo_llamaparse():
    """演示 LlamaParse 解析器"""
    print("\n" + "=" * 60)
    print("  LlamaParse 解析器演示")
    print("=" * 60)

    parser = LlamaParseParser()
    print(f"\nLlamaParse 可用状态: {'✅ 已配置' if parser._available else '❌ 未配置 API Key'}")

    if not parser._available:
        print("\nLlamaParse 是 LlamaIndex 提供的云端解析服务")
        print("安装命令: pip install llama-parse")
        print("配置 API Key: export LLAMA_PARSE_API_KEY=your_key")
        print("\n特点:")
        print("  • 基于 LLM 的文档理解能力")
        print("  • 支持复杂 PDF 解析（表格、公式、图表）")
        print("  • 返回结构化的 Markdown 格式")
        print("  • 需要 API Key（付费服务）")


def demo_scheduler():
    """演示统一调度器"""
    print("\n" + "=" * 60)
    print("  统一解析工具调度器 — ParsingToolScheduler")
    print("=" * 60)

    scheduler = ParsingToolScheduler()

    # 查看工具状态
    print("\n工具状态:")
    status = scheduler.get_tool_status()
    for name, available in status.items():
        icon = "✅" if available == "available" else "❌"
        print(f"  {icon} {name:15s}: {available}")

    # 自动选择工具逻辑
    print("\n自动选择规则:")
    print("  .txt / .md     → basic（直接读取）")
    print("  .pdf / .docx   → unstructured → mineru（回退）")
    print("  .html          → unstructured")
    print("  不支持的格式    → 跳过")

    # 创建临时文件测试
    print("\n批量解析测试:")
    test_files = []
    try:
        # TXT 文件
        txt_path = tempfile.mktemp(suffix=".txt")
        Path(txt_path).write_text("这是一个纯文本文件示例。", encoding="utf-8")
        test_files.append(txt_path)

        # Markdown 文件
        md_path = tempfile.mktemp(suffix=".md")
        Path(md_path).write_text("# 标题\n\n这是一段 Markdown 内容。", encoding="utf-8")
        test_files.append(md_path)

        results = scheduler.parse_batch(test_files)
        print(f"  成功解析: {len(results)}/{len(test_files)} 个文件")
        for doc in results:
            print(f"    [{doc.tool}] {doc.word_count} 字符 - {Path(doc.source).suffix}")

    finally:
        for f in test_files:
            if os.path.exists(f):
                os.unlink(f)


def demo_tool_comparison():
    """工具对比"""
    print("\n" + "=" * 60)
    print("  文档解析工具对比")
    print("=" * 60)

    print(f"\n{'工具':<15s} {'类型':<8s} {'费用':<8s} {'擅长':<20s}")
    print("-" * 55)
    print(f"{'基础解析':<15s} {'内置':<8s} {'免费':<8s} {'TXT/MD 简单文本'}")
    print(f"{'Unstructured':<15s} {'开源':<8s} {'免费':<8s} {'多格式通用解析'}")
    print(f"{'MinerU':<15s} {'开源':<8s} {'免费':<8s} {'复杂 PDF 版面分析'}")
    print(f"{'LlamaParse':<15s} {'云端':<8s} {'付费':<8s} {'LLM 驱动的高精度解析'}")


if __name__ == "__main__":
    demo_unstructured()
    demo_mineru()
    demo_llamaparse()
    demo_scheduler()
    demo_tool_comparison()
