"""
doc_parsing_tools.py — 高级文档解析工具实现
包含 Unstructured、MinerU、LlamaParse 等高级解析工具的封装。
"""
import os
import json
import time
from typing import Optional
from pathlib import Path
from dataclasses import dataclass, field


# ============================================================
# 模块：解析结果数据结构
# ============================================================

@dataclass
class ParsedDocument:
    """解析结果数据结构"""
    text: str
    source: str
    tool: str
    metadata: dict = field(default_factory=dict)

    @property
    def word_count(self) -> int:
        return len(self.text)

    @property
    def has_tables(self) -> bool:
        return self.metadata.get("tables", 0) > 0

    @property
    def has_images(self) -> bool:
        return self.metadata.get("images", 0) > 0


# ============================================================
# 模块：Unstructured 解析器
# ============================================================

class UnstructuredParser:
    """
    Unstructured 解析器：开源的多格式文档解析库。

    特点：
    - 支持 PDF、HTML、Markdown、DOCX、PPTX 等格式
    - 自动识别文档结构（标题、段落、表格、列表）
    - 提取元数据（创建时间、作者等）
    - 对表格和布局有较好的处理能力

    安装：pip install unstructured
    """

    SUPPORTED_FORMATS = [".pdf", ".html", ".md", ".docx", ".pptx", ".txt", ".eml"]

    def __init__(self, strategy: str = "auto"):
        """
        初始化 Unstructured 解析器。

        参数：
        - strategy (str): 解析策略
            - "auto": 自动选择最佳策略
            - "hi_res": 高精度模式（使用 OCR，较慢）
            - "fast": 快速模式（仅文本提取）
            - "ocr_only": 仅 OCR（适用于扫描版 PDF）
        """
        self.strategy = strategy
        self._available = self._check_availability()

    def _check_availability(self) -> bool:
        """检查 unstructured 是否已安装"""
        try:
            from unstructured.partition.auto import partition
            return True
        except ImportError:
            return False

    def parse(self, filepath: str) -> Optional[ParsedDocument]:
        """
        解析文档文件。

        参数：
        - filepath (str): 文件路径

        返回：
        - ParsedDocument 或 None: 解析结果
        """
        if not self._available:
            print(f"[警告] unstructured 未安装，跳过解析: {filepath}")
            return None

        try:
            from unstructured.partition.auto import partition

            elements = partition(
                filename=filepath,
                strategy=self.strategy,
            )

            # 拼接文本
            text_parts = []
            table_count = 0
            image_count = 0

            for element in elements:
                element_type = type(element).__name__
                text = element.text if hasattr(element, 'text') else str(element)

                if element_type == "Table":
                    table_count += 1
                    text_parts.append(f"[表格] {text}")
                elif element_type == "Image":
                    image_count += 1
                else:
                    text_parts.append(text)

            full_text = "\n\n".join(text_parts)

            return ParsedDocument(
                text=full_text.strip(),
                source=filepath,
                tool="unstructured",
                metadata={
                    "strategy": self.strategy,
                    "num_elements": len(elements),
                    "tables": table_count,
                    "images": image_count,
                },
            )

        except Exception as e:
            print(f"[错误] unstructured 解析失败: {filepath} - {e}")
            return None


# ============================================================
# 模块：MinerU 解析器
# ============================================================

class MinerUParser:
    """
    MinerU 解析器：基于深度学习的文档解析工具。

    特点：
    - 使用 AI 模型识别文档结构
    - 支持复杂 PDF 的版面分析
    - 能准确提取表格、公式、图片
    - 适用于学术论文和技术文档

    安装：pip install magic-pdf
    """

    def __init__(self, model_name: str = "default"):
        """
        初始化 MinerU 解析器。

        参数：
        - model_name (str): 模型名称（默认使用内置模型）
        """
        self.model_name = model_name
        self._available = self._check_availability()

    def _check_availability(self) -> bool:
        """检查 MinerU 是否已安装"""
        try:
            import magic_pdf
            return True
        except ImportError:
            return False

    def parse(self, filepath: str) -> Optional[ParsedDocument]:
        """
        解析文档文件（目前主要支持 PDF）。

        参数：
        - filepath (str): 文件路径

        返回：
        - ParsedDocument 或 None: 解析结果
        """
        if not self._available:
            print(f"[警告] MinerU 未安装，跳过解析: {filepath}")
            return None

        try:
            # 模拟 MinerU 解析流程
            # 实际使用：from magic_pdf.data.data_reader_writer import FileBasedDataWriter
            #            from magic_pdf.tools.cli import process_pdf
            
            print(f"[MinerU] 开始解析: {filepath}")
            
            # 实际解析代码（需要安装 magic-pdf）
            # result = magic_pdf.process(filepath)
            # text = result.get_markdown()
            
            # 占位实现
            text = f"[MinerU 解析结果]\n\n文件: {Path(filepath).name}\n格式: {Path(filepath).suffix}\n状态: 需要安装 magic-pdf 库\n\n提示: pip install magic-pdf"

            return ParsedDocument(
                text=text.strip(),
                source=filepath,
                tool="mineru",
                metadata={
                    "model": self.model_name,
                    "note": "这是占位输出，需要安装 magic-pdf 库才能实际解析",
                },
            )

        except Exception as e:
            print(f"[错误] MinerU 解析失败: {filepath} - {e}")
            return None


# ============================================================
# 模块：LlamaParse 解析器
# ============================================================

class LlamaParseParser:
    """
    LlamaParse 解析器：由 LlamaIndex 提供的云端文档解析服务。

    特点：
    - 基于 LLM 的文档理解能力
    - 支持复杂的 PDF 解析（表格、公式、图表）
    - 返回结构化的 Markdown 格式
    - 需要 API Key（付费服务）

    安装：pip install llama-parse
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 LlamaParse 解析器。

        参数：
        - api_key (str): LlamaParse API Key（从环境变量读取）
        """
        self.api_key = api_key or os.getenv("LLAMA_PARSE_API_KEY", "")
        self._available = self._check_availability()

    def _check_availability(self) -> bool:
        """检查 LlamaParse 是否可用"""
        if not self.api_key:
            print("[LlamaParse] 警告: 未设置 LLAMA_PARSE_API_KEY")
            return False
        try:
            from llama_parse import LlamaParse
            return True
        except ImportError:
            return False

    def parse(self, filepath: str) -> Optional[ParsedDocument]:
        """
        解析文档文件（主要支持 PDF）。

        参数：
        - filepath (str): 文件路径

        返回：
        - ParsedDocument 或 None: 解析结果
        """
        if not self._available:
            print(f"[警告] LlamaParse 不可用，跳过解析: {filepath}")
            return None

        try:
            from llama_parse import LlamaParse

            parser = LlamaParse(
                api_key=self.api_key,
                result_type="markdown",  # 返回 Markdown 格式
                verbose=True,
            )

            # 异步解析
            import asyncio
            
            async def _parse_async():
                documents = await parser.aload_data(filepath)
                return documents
            
            # 运行异步任务
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                documents = loop.run_until_complete(_parse_async())
            finally:
                loop.close()

            # 拼接结果
            full_text = "\n\n".join(
                doc.text for doc in documents
            )

            return ParsedDocument(
                text=full_text.strip(),
                source=filepath,
                tool="llamaparse",
                metadata={
                    "num_pages": len(documents),
                    "result_type": "markdown",
                },
            )

        except Exception as e:
            print(f"[错误] LlamaParse 解析失败: {filepath} - {e}")
            return None


# ============================================================
# 模块：统一解析工具调度器
# ============================================================

class ParsingToolScheduler:
    """
    统一解析工具调度器：管理和调度多个解析工具。

    特点：
    - 根据文件类型和复杂度自动选择最佳工具
    - 支持多工具回退机制
    - 提供统一的解析接口
    """

    # 工具优先级（从高到低）
    TOOL_PRIORITY = {
        "simple": ["basic", "unstructured"],
        "complex": ["mineru", "llamaparse"],
        "fallback": ["basic"],
    }

    def __init__(self):
        self.parsers = {
            "basic": None,  # 简单文本解析器
            "unstructured": UnstructuredParser(),
            "mineru": MinerUParser(),
            "llamaparse": LlamaParseParser(),
        }

    def parse(self, filepath: str, force_tool: Optional[str] = None) -> Optional[ParsedDocument]:
        """
        解析文档，自动选择最佳工具。

        参数：
        - filepath (str): 文件路径
        - force_tool (str): 强制使用指定工具（可选）

        返回：
        - ParsedDocument 或 None: 解析结果
        """
        if force_tool:
            return self._try_parse(filepath, force_tool)

        # 自动选择工具
        ext = Path(filepath).suffix.lower()
        
        # 简单格式使用基础解析器
        if ext in [".txt", ".md"]:
            return self._try_parse(filepath, "basic")
        
        # 复杂格式尝试高级工具
        elif ext in [".pdf", ".docx", ".pptx"]:
            result = self._try_parse(filepath, "unstructured")
            if result is None:
                result = self._try_parse(filepath, "mineru")
            return result
        
        # HTML 使用 unstructured
        elif ext in [".html"]:
            return self._try_parse(filepath, "unstructured")
        
        return None

    def _try_parse(self, filepath: str, tool_name: str) -> Optional[ParsedDocument]:
        """尝试使用指定工具解析"""
        if tool_name == "basic":
            # 简单文本读取
            try:
                text = Path(filepath).read_text(encoding="utf-8")
                return ParsedDocument(
                    text=text.strip(),
                    source=filepath,
                    tool="basic",
                    metadata={"original_length": len(text)},
                )
            except Exception as e:
                print(f"[错误] 基础解析失败: {filepath} - {e}")
                return None
        
        parser = self.parsers.get(tool_name)
        if parser is None:
            print(f"[错误] 未知解析工具: {tool_name}")
            return None
        
        return parser.parse(filepath)

    def parse_batch(self, filepaths: list[str]) -> list[ParsedDocument]:
        """批量解析多个文件"""
        results = []
        for fp in filepaths:
            doc = self.parse(fp)
            if doc is not None:
                results.append(doc)
        return results

    def get_tool_status(self) -> dict:
        """获取各工具的可用状态"""
        status = {}
        for name, parser in self.parsers.items():
            if parser is None:
                status[name] = "available"
            elif hasattr(parser, "_available"):
                status[name] = "available" if parser._available else "not_installed"
            else:
                status[name] = "available"
        return status


# ============================================================
# 模块：使用示例
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  高级文档解析工具 — 使用示例")
    print("=" * 60)

    # 创建调度器
    scheduler = ParsingToolScheduler()

    # 查看工具状态
    print("\n工具状态:")
    status = scheduler.get_tool_status()
    for name, available in status.items():
        icon = "✅" if available == "available" else "❌"
        print(f"  {icon} {name:15s}: {available}")

    print("\n使用方式:")
    print("  scheduler = ParsingToolScheduler()")
    print("  result = scheduler.parse('document.pdf')")
    print(f"  print(f'文本长度: {{result.word_count}} 字符')")
