"""
word_embedding.py — 词向量（Word Embedding）实现
演示从独热编码（One-Hot）到词向量（Word2Vec/TF-IDF）的演进过程。
包含三种词向量化方法的完整实现：
1. One-Hot 编码（传统稀疏表示）
2. TF-IDF（词频-逆文档频率）
3. 基于共现矩阵的简单词向量
"""
import math
from collections import Counter
from typing import Optional


# ============================================================
# 模块：独热编码（One-Hot Encoding）
# 说明：将词汇表中的每个词映射为一个高维稀疏向量
#      向量长度等于词汇表大小，只有一个位置为 1，其余为 0
# 缺点：维度灾难（词汇表 10 万 → 向量 10 万维）、无语义信息
# ============================================================

class OneHotEncoder:
    """
    独热编码器：将词语转换为独热向量。

    原理：
    - 首先从语料中构建词汇表（每个词分配一个唯一的索引）
    - 对于每个词，创建一个长度为词汇表大小的向量
    - 该词对应的索引位置设为 1，其余位置为 0

    示例：
    词汇表 = {"猫": 0, "狗": 1, "鸟": 2}
    "猫" → [1, 0, 0]
    "狗" → [0, 1, 0]
    "鸟" → [0, 0, 1]
    """

    def __init__(self):
        """
        初始化独热编码器。

        属性：
        - vocab (dict[str, int]): 词汇表，键为词，值为索引
        - vocab_size (int): 词汇表大小（不同词的数量）
        """
        # 词汇表字典：词 → 索引
        self.vocab: dict[str, int] = {}
        # 词汇表大小
        self.vocab_size: int = 0

    def build_vocab(self, corpus: list[list[str]]) -> None:
        """
        从语料库中构建词汇表。

        参数：
        - corpus (list[list[str]]): 语料库，每个元素是一个分词后的句子
          示例：[["我", "喜欢", "猫"], ["我", "喜欢", "狗"]]

        说明：
        - 遍历所有句子的所有词
        - 为每个新出现的词分配一个递增的索引
        - 最终词汇表大小等于不同词的数量
        """
        # 索引计数器：从 0 开始，每遇到新词加 1
        idx = 0

        # 遍历语料库中的每个句子
        for sentence in corpus:
            # 遍历句子中的每个词
            for word in sentence:
                # 如果词尚未在词汇表中，分配新索引
                if word not in self.vocab:
                    # 词 → 索引的映射
                    self.vocab[word] = idx
                    # 索引递增
                    idx += 1

        # 更新词汇表大小
        self.vocab_size = idx

    def encode(self, word: str) -> Optional[list[int]]:
        """
        将单个词编码为独热向量。

        参数：
        - word (str): 要编码的词

        返回：
        - list[int] 或 None: 独热向量（列表），如果词不在词汇表中则返回 None

        示例：
        词汇表 = {"猫": 0, "狗": 1, "鸟": 2}，词汇表大小 = 3
        encode("猫") → [1, 0, 0]  # 索引 0 为 1
        encode("狗") → [0, 1, 0]  # 索引 1 为 1
        encode("鱼") → None        # "鱼"不在词汇表中
        """
        # 检查词是否在词汇表中
        if word not in self.vocab:
            # 未知词（OOV），无法编码
            return None

        # 获取词对应的索引
        word_idx = self.vocab[word]

        # 创建全 0 向量，长度等于词汇表大小
        one_hot_vector = [0] * self.vocab_size

        # 将词对应的索引位置设为 1
        one_hot_vector[word_idx] = 1

        # 返回独热向量
        return one_hot_vector

    def encode_sentence(self, sentence: list[str]) -> list[list[int]]:
        """
        将整个句子编码为独热向量列表。

        参数：
        - sentence (list[str]): 分词后的句子，如 ["我", "喜欢", "猫"]

        返回：
        - list[list[int]]: 每个词对应的独热向量列表

        示例：
        encode_sentence(["猫", "狗"]) → [[1, 0, 0], [0, 1, 0]]
        """
        # 存储所有词的独热向量
        vectors = []

        # 遍历句子中的每个词
        for word in sentence:
            # 对每个词进行独热编码
            vec = self.encode(word)
            # 如果词在词汇表中，添加向量
            if vec is not None:
                vectors.append(vec)

        # 返回所有词的向量列表
        return vectors


# ============================================================
# 模块：TF-IDF（Term Frequency-Inverse Document Frequency）
# 说明：衡量一个词在文档中的重要程度
#      - TF（词频）：词在文档中出现的频率
#      - IDF（逆文档频率）：词在所有文档中的稀有程度
#      - TF-IDF = TF × IDF
# 优点：比独热编码更能反映词的语义重要性
# 缺点：仍然是词级别表示，不捕获上下文语义
# ============================================================

class TFIDFEncoder:
    """
    TF-IDF 编码器：计算词频-逆文档频率权重。

    公式：
    - TF(t, d) = 词 t 在文档 d 中出现的次数 / 文档 d 的总词数
    - IDF(t) = log(总文档数 / 包含词 t 的文档数) + 1  # +1 是平滑项
    - TF-IDF(t, d) = TF(t, d) × IDF(t)

    直觉：
    - 一个词在某文档中频繁出现（高 TF）且在少数文档中出现（高 IDF）
    - 则该词对该文档具有高区分度（高 TF-IDF）
    """

    def __init__(self):
        """
        初始化 TF-IDF 编码器。

        属性：
        - vocab (dict[str, int]): 词汇表，词 → 索引
        - vocab_size (int): 词汇表大小
        - idf (dict[str, float]): IDF 值字典，词 → IDF 值
        - num_docs (int): 文档总数
        """
        # 词汇表：词 → 索引
        self.vocab: dict[str, int] = {}
        # 词汇表大小
        self.vocab_size: int = 0
        # IDF 值字典
        self.idf: dict[str, float] = {}
        # 文档总数
        self.num_docs: int = 0

    def build_vocab(self, corpus: list[list[str]]) -> None:
        """
        从语料库中构建词汇表并计算 IDF 值。

        参数：
        - corpus (list[list[str]]): 语料库，每个元素是一个文档（分词后的词列表）

        说明：
        - 第一步：构建词汇表（同独热编码）
        - 第二步：计算每个词的 IDF 值
        """
        # 文档总数 = 语料库中的文档数量
        self.num_docs = len(corpus)

        # ---------- 第一步：构建词汇表 ----------
        idx = 0  # 索引计数器
        # 遍历所有文档
        for doc in corpus:
            # 遍历文档中的每个词
            for word in doc:
                # 新词分配索引
                if word not in self.vocab:
                    self.vocab[word] = idx
                    idx += 1

        # 更新词汇表大小
        self.vocab_size = idx

        # ---------- 第二步：计算 IDF ----------
        # 统计每个词出现在多少个文档中
        doc_freq: dict[str, int] = {}

        # 遍历每个文档
        for doc in corpus:
            # 去重：一个词在一个文档中只计一次
            unique_words = set(doc)
            # 遍历文档中的唯一词
            for word in unique_words:
                # 该词的文档频率 +1
                doc_freq[word] = doc_freq.get(word, 0) + 1

        # 计算每个词的 IDF 值
        for word, df in doc_freq.items():
            # IDF 公式：log(N / df) + 1
            # N = 总文档数，df = 包含该词的文档数
            # +1 是平滑项，防止 IDF 为 0
            self.idf[word] = math.log(self.num_docs / df) + 1

    def transform(self, doc: list[str]) -> list[float]:
        """
        将文档转换为 TF-IDF 向量。

        参数：
        - doc (list[str]): 分词后的文档

        返回：
        - list[float]: TF-IDF 向量，长度等于词汇表大小

        计算步骤：
        1. 计算每个词的 TF（词频）
        2. 乘以对应的 IDF 值
        3. 按词汇表索引填充向量
        """
        # 创建全 0 向量，长度等于词汇表大小
        tfidf_vector = [0.0] * self.vocab_size

        # 文档总词数（用于计算 TF）
        doc_length = len(doc)
        # 如果文档为空，返回零向量
        if doc_length == 0:
            return tfidf_vector

        # 统计文档中每个词的出现次数
        term_freq = Counter(doc)

        # 遍历文档中的每个唯一词
        for word, count in term_freq.items():
            # 检查词是否在词汇表中
            if word not in self.vocab:
                # 未知词，跳过
                continue

            # ---------- 计算 TF ----------
            # TF = 词在文档中的出现次数 / 文档总词数
            tf = count / doc_length

            # ---------- 获取 IDF ----------
            # 从预计算的 IDF 字典中获取
            idf = self.idf.get(word, 1.0)  # 默认 IDF=1.0（平滑值）

            # ---------- 计算 TF-IDF ----------
            # TF-IDF = TF × IDF
            tfidf_value = tf * idf

            # ---------- 填充向量 ----------
            # 获取词在词汇表中的索引
            word_idx = self.vocab[word]
            # 将 TF-IDF 值填入对应位置
            tfidf_vector[word_idx] = tfidf_value

        # 返回完整的 TF-IDF 向量
        return tfidf_vector

    def get_top_words(self, doc: list[str], top_k: int = 5) -> list[tuple[str, float]]:
        """
        获取文档中 TF-IDF 值最高的词。

        参数：
        - doc (list[str]): 分词后的文档
        - top_k (int): 返回前 k 个词

        返回：
        - list[tuple[str, float]]: (词, TF-IDF值) 的列表，按值降序排列

        用途：
        - 关键词提取
        - 文档特征分析
        """
        # 获取 TF-IDF 向量
        vector = self.transform(doc)

        # 构建 (词, TF-IDF值) 对列表
        word_scores: list[tuple[str, float]] = []
        # 遍历词汇表
        for word, idx in self.vocab.items():
            score = vector[idx]
            # 只保留 TF-IDF > 0 的词
            if score > 0:
                word_scores.append((word, score))

        # 按 TF-IDF 值降序排序
        word_scores.sort(key=lambda x: x[1], reverse=True)

        # 返回前 top_k 个
        return word_scores[:top_k]
