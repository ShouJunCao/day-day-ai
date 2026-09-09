"""
text_chunking.py — 文本分块策略实现
包含固定长度分块、语义分块、递归分块、Sentence Window 四种策略。
"""
import re
from typing import Optional, List
from dataclasses import dataclass, field


@dataclass
class Chunk:
    """文本块数据结构"""
    text: str
    index: int
    metadata: dict = field(default_factory=dict)

    @property
    def char_count(self) -> int:
        """计算字符数"""
        return len(self.text)

    @property
    def word_count(self) -> int:
        """计算中文字数"""
        return len(re.findall(r'[\u4e00-\u9fff]', self.text))


# ============================================================
# 策略 1：固定长度分块
# ============================================================

class FixedSizeChunker:
    """
    固定长度分块器：按固定字符数切分文本。

    特点：
    - 实现简单，速度快
    - 不考虑语义边界
    - 适合均匀分布的文本

    参数：
    - chunk_size: 每块最大字符数
    - overlap: 相邻块重叠字符数
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> List[Chunk]:
        """
        将文本切分为固定大小的块。

        使用滑动窗口策略：
        - 每块最大 chunk_size 字符
        - 相邻块之间重叠 overlap 字符
        - 避免语义被硬切断
        """
        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]

            chunks.append(Chunk(
                text=chunk_text,
                index=len(chunks),
                metadata={
                    "strategy": "fixed_size",
                    "start_char": start,
                    "end_char": end,
                },
            ))
            start = end - self.overlap

        return chunks


# ============================================================
# 策略 2：语义分块
# ============================================================

class SemanticChunker:
    """
    语义分块器：基于语义相似度动态调整块边界。

    特点：
    - 在语义转折点切分
    - 保持语义完整性
    - 块大小不均匀

    原理：
    1. 按句子分割文本
    2. 累积句子直到达到目标大小
    3. 在句子边界切分（不切断句子）
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap
        # 句子分割正则：匹配句号、问号、叹号等
        self.sentence_pattern = re.compile(
            r'(?<=[。！？；.!?\n])\s*'
        )

    def _split_sentences(self, text: str) -> List[str]:
        """将文本分割为句子列表"""
        sentences = self.sentence_pattern.split(text)
        return [s.strip() for s in sentences if s.strip()]

    def chunk(self, text: str) -> List[Chunk]:
        """基于语义边界切分文本"""
        sentences = self._split_sentences(text)
        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence_len = len(sentence)

            # 如果当前块加上新句子超过目标大小
            if current_length + sentence_len > self.chunk_size and current_chunk:
                # 保存当前块
                chunk_text = " ".join(current_chunk)
                chunks.append(Chunk(
                    text=chunk_text,
                    index=len(chunks),
                    metadata={
                        "strategy": "semantic",
                        "num_sentences": len(current_chunk),
                    },
                ))

                # 保留重叠部分
                overlap_sentences = []
                overlap_len = 0
                for s in reversed(current_chunk):
                    if overlap_len + len(s) <= self.overlap:
                        overlap_sentences.insert(0, s)
                        overlap_len += len(s)
                    else:
                        break

                current_chunk = overlap_sentences
                current_length = overlap_len

            current_chunk.append(sentence)
            current_length += sentence_len

        # 处理最后一个块
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(Chunk(
                text=chunk_text,
                index=len(chunks),
                metadata={
                    "strategy": "semantic",
                    "num_sentences": len(current_chunk),
                },
            ))

        return chunks


# ============================================================
# 策略 3：递归分块
# ============================================================

class RecursiveChunker:
    """
    递归分块器：按层次结构递归切分文本。

    特点：
    - 按分隔符层次递归切分
    - 优先在大边界（段落）切分
    - 逐步细化到小边界（句子、词）

    分隔符层次（从大到小）：
    1. 双换行（段落）
    2. 单换行
    3. 句号
    4. 分号
    5. 空格
    """

    SEPARATORS = [
        ("\n\n", "paragraph"),    # 段落
        ("\n", "newline"),         # 换行
        ("。", "period"),          # 句号
        ("；", "semicolon"),       # 分号
        (" ", "space"),            # 空格
    ]

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> List[Chunk]:
        """递归切分文本"""
        return self._recursive_split(text, 0)

    def _recursive_split(self, text: str, level: int) -> List[Chunk]:
        """递归切分：从大边界到小边界"""
        # 如果文本已经足够小，直接返回
        if len(text) <= self.chunk_size:
            return [Chunk(
                text=text,
                index=0,
                metadata={"strategy": "recursive", "level": level},
            )]

        # 如果已经没有更小的分隔符可用
        if level >= len(self.SEPARATORS):
            # 退回到固定长度分块
            return self._fallback_split(text)

        separator, name = self.SEPARATORS[level]
        parts = text.split(separator)

        # 尝试合并相邻部分
        chunks = []
        current_parts = []
        current_length = 0

        for part in parts:
            part_with_sep = part + separator
            part_len = len(part_with_sep)

            if current_length + part_len > self.chunk_size and current_parts:
                chunk_text = separator.join(current_parts).rstrip()
                chunks.append(Chunk(
                    text=chunk_text,
                    index=len(chunks),
                    metadata={
                        "strategy": "recursive",
                        "separator": name,
                        "level": level,
                    },
                ))

                # 保留重叠部分
                current_parts = self._get_overlap_parts(
                    current_parts, separator
                )
                current_length = sum(len(p) + len(separator) for p in current_parts)

            current_parts.append(part)
            current_length += part_len

        # 处理剩余部分
        if current_parts:
            remaining = separator.join(current_parts).rstrip()
            if len(remaining) > self.chunk_size:
                # 递归到下一级分隔符
                sub_chunks = self._recursive_split(remaining, level + 1)
                for sc in sub_chunks:
                    sc.metadata["parent_level"] = level
                    sc.metadata["parent_separator"] = name
                chunks.extend(sub_chunks)
            else:
                chunks.append(Chunk(
                    text=remaining,
                    index=len(chunks),
                    metadata={
                        "strategy": "recursive",
                        "separator": name,
                        "level": level,
                    },
                ))

        return chunks

    def _get_overlap_parts(self, parts: List[str], separator: str) -> List[str]:
        """获取重叠部分"""
        overlap_parts = []
        overlap_len = 0

        for part in reversed(parts):
            part_len = len(part) + len(separator)
            if overlap_len + part_len <= self.overlap:
                overlap_parts.insert(0, part)
                overlap_len += part_len
            else:
                break

        return overlap_parts

    def _fallback_split(self, text: str) -> List[Chunk]:
        """退回到固定长度分块"""
        fixed_chunker = FixedSizeChunker(self.chunk_size, self.overlap)
        return fixed_chunker.chunk(text)


# ============================================================
# 策略 4：Sentence Window 分块
# ============================================================

class SentenceWindowChunker:
    """
    Sentence Window 分块器：以句子为中心，保留上下文窗口。

    特点：
    - 每个块以单个句子为核心
    - 包含前后若干句作为上下文
    - 检索时使用核心句子，生成时使用完整上下文
    - 适合需要精确检索但又要完整上下文的场景

    参数：
    - window_size: 前后各保留的句子数
    """

    def __init__(self, window_size: int = 3):
        self.window_size = window_size
        self.sentence_pattern = re.compile(r'(?<=[。！？.!?])\s*')

    def _split_sentences(self, text: str) -> List[str]:
        """将文本分割为句子列表"""
        sentences = self.sentence_pattern.split(text)
        return [s.strip() for s in sentences if s.strip()]

    def chunk(self, text: str) -> List[Chunk]:
        """生成带上下文窗口的句子块"""
        sentences = self._split_sentences(text)
        chunks = []

        for i, sentence in enumerate(sentences):
            # 获取前后上下文
            start = max(0, i - self.window_size)
            end = min(len(sentences), i + self.window_size + 1)

            context = " ".join(sentences[start:end])

            chunks.append(Chunk(
                text=context,
                index=i,
                metadata={
                    "strategy": "sentence_window",
                    "core_sentence": sentence,
                    "core_index": i,
                    "context_start": start,
                    "context_end": end,
                    "window_size": self.window_size,
                },
            ))

        return chunks


# ============================================================
# 模块：统一分块调度器
# ============================================================

class ChunkingScheduler:
    """
    统一分块调度器：根据文本特征自动选择最佳分块策略。
    """

    STRATEGIES = {
        "fixed_size": FixedSizeChunker,
        "semantic": SemanticChunker,
        "recursive": RecursiveChunker,
        "sentence_window": SentenceWindowChunker,
    }

    def __init__(
        self,
        chunk_size: int = 500,
        overlap: int = 50,
        strategy: str = "recursive",
    ):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.strategy = strategy

    def chunk(self, text: str) -> List[Chunk]:
        """执行分块"""
        chunker_class = self.STRATEGIES.get(self.strategy)
        if chunker_class is None:
            raise ValueError(f"未知分块策略: {self.strategy}")

        if self.strategy == "sentence_window":
            chunker = chunker_class(window_size=3)
        else:
            chunker = chunker_class(self.chunk_size, self.overlap)

        return chunker.chunk(text)

    @classmethod
    def compare_strategies(cls, text: str, chunk_size: int = 500) -> dict:
        """对比不同分块策略的效果"""
        results = {}
        for name, chunker_class in cls.STRATEGIES.items():
            if name == "sentence_window":
                chunker = chunker_class(window_size=3)
            else:
                chunker = chunker_class(chunk_size, overlap=50)

            chunks = chunker.chunk(text)
            results[name] = {
                "num_chunks": len(chunks),
                "avg_length": sum(c.char_count for c in chunks) / len(chunks) if chunks else 0,
                "min_length": min(c.char_count for c in chunks) if chunks else 0,
                "max_length": max(c.char_count for c in chunks) if chunks else 0,
            }

        return results


if __name__ == "__main__":
    # 测试文本
    sample_text = """
    人工智能是计算机科学的一个分支，致力于开发能够模拟人类智能行为的系统。
    机器学习是 AI 的核心技术之一，通过从数据中学习来实现智能决策。
    深度学习是机器学习的子领域，使用多层神经网络来学习数据的复杂表示。
    Transformer 架构是近年来最重要的深度学习突破之一。
    自然语言处理是 AI 的重要应用方向，涉及文本理解、情感分析、机器翻译等任务。
    大语言模型的出现极大推动了 NLP 的发展。
    """

    print("=" * 60)
    print("  文本分块策略对比")
    print("=" * 60)

    results = ChunkingScheduler.compare_strategies(sample_text.strip(), chunk_size=100)

    print(f"\n{'策略':<20s} {'块数':>6s} {'平均长度':>10s} {'最小长度':>10s} {'最大长度':>10s}")
    print("-" * 60)
    for name, stats in results.items():
        print(f"{name:<20s} {stats['num_chunks']:>6d} {stats['avg_length']:>10.1f} "
              f"{stats['min_length']:>10d} {stats['max_length']:>10d}")
