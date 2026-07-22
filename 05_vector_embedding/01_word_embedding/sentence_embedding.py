"""
sentence_embedding.py — 句向量（Sentence Embedding）实现
演示从词袋模型到上下文感知的句向量化方法的演进。
包含四种句向量化方法的完整实现：
1. 词袋平均（Bag-of-Words Average）
2. TF-IDF 加权平均
3. 简单注意力加权
4. 基于预训练向量的句向量（模拟）
"""
import math
from collections import Counter
from typing import Optional


# ============================================================
# 模块：简单词向量字典（模拟预训练词向量）
# 说明：在实际项目中，词向量来自 Word2Vec/GloVe/FastText 训练
#      这里使用确定性哈希函数生成模拟向量，用于教学演示
# ============================================================

class SimpleWordVectors:
    """
    简易词向量字典：为每个词生成固定维度的向量。

    说明：
    - 实际项目中应加载预训练的 Word2Vec/GloVe 向量
    - 这里使用确定性哈希生成模拟向量，确保相同词得到相同向量
    - 主要用于教学演示，展示句向量如何从词向量组合而来

    属性：
    - dim (int): 词向量维度
    - vectors (dict[str, list[float]]): 词 → 向量的映射
    """

    def __init__(self, dim: int = 8):
        """
        初始化词向量字典。

        参数：
        - dim (int): 词向量维度，默认 8 维
        """
        # 词向量维度
        self.dim = dim
        # 词向量缓存：词 → 向量
        self.vectors: dict[str, list[float]] = {}

    def get_vector(self, word: str) -> Optional[list[float]]:
        """
        获取词的向量表示。

        参数：
        - word (str): 要获取向量的词

        返回：
        - list[float] 或 None: 词向量，如果词为空字符串则返回 None

        说明：
        - 如果词已缓存，直接返回
        - 否则使用确定性哈希生成向量并缓存
        """
        # 空词无法生成向量
        if not word:
            return None

        # 检查缓存中是否已有
        if word in self.vectors:
            return self.vectors[word]

        # 使用确定性哈希生成向量
        # Python 的 hash() 在 Python 3 中每次运行不同，这里用简单算法
        vector = self._hash_to_vector(word, self.dim)
        # 缓存结果
        self.vectors[word] = vector
        return vector

    def _hash_to_vector(self, word: str, dim: int) -> list[float]:
        """
        将词通过哈希函数映射为固定维度的向量。

        参数：
        - word (str): 输入词
        - dim (int): 目标维度

        返回：
        - list[float]: 归一化的随机向量（值域 -1 到 1）

        算法：
        - 使用词的 Unicode 编码值作为种子
        - 生成 dim 个伪随机值
        - 归一化到 [-1, 1] 范围
        """
        # 计算词的编码总和作为种子
        seed = sum(ord(c) for c in word)

        # 生成 dim 维向量
        vector = []
        for i in range(dim):
            # 伪随机：使用种子和维度索引生成确定值
            val = math.sin(seed * (i + 1) * 0.1) * 2 - 1
            vector.append(round(val, 4))

        # 归一化：使向量模长为 1
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]

        return vector


# ============================================================
# 模块：词袋平均句向量（Bag-of-Words Average）
# 说明：将句子中所有词的向量取平均，得到句子向量
# 优点：简单快速，无需训练
# 缺点：忽略词序、无法区分重要词和非重要词
# ============================================================

class BagOfWordsAverage:
    """
    词袋平均编码器：通过对词向量取平均生成句向量。

    原理：
    sentence_vector = mean([word_vector(w) for w in sentence])

    示例：
    句子 = ["我", "喜欢", "猫"]
    向量("我") = [0.1, 0.2, ...]
    向量("喜欢") = [0.3, 0.4, ...]
    向量("猫") = [0.5, 0.6, ...]
    句向量 = [mean(0.1,0.3,0.5), mean(0.2,0.4,0.6), ...]

    属性：
    - word_vectors (SimpleWordVectors): 词向量提供者
    """

    def __init__(self, word_vectors: SimpleWordVectors):
        """
        初始化词袋平均编码器。

        参数：
        - word_vectors (SimpleWordVectors): 提供词向量的对象
        """
        # 词向量提供者
        self.word_vectors = word_vectors

    def encode(self, sentence: list[str]) -> Optional[list[float]]:
        """
        将句子编码为句向量（词向量平均）。

        参数：
        - sentence (list[str]): 分词后的句子

        返回：
        - list[float] 或 None: 句子向量，如果句子为空或无有效词则返回 None

        计算步骤：
        1. 获取每个词的向量
        2. 过滤掉未知词（向量为 None 的词）
        3. 对每个维度求平均
        """
        # 收集所有有效词向量
        valid_vectors: list[list[float]] = []

        # 遍历句子中的每个词
        for word in sentence:
            # 获取词的向量
            vec = self.word_vectors.get_vector(word)
            # 跳过未知词
            if vec is not None:
                valid_vectors.append(vec)

        # 如果没有有效向量，返回 None
        if not valid_vectors:
            return None

        # 获取向量维度
        dim = len(valid_vectors[0])
        # 初始化平均向量（全 0）
        avg_vector = [0.0] * dim

        # 对每个维度求和
        for vec in valid_vectors:
            for i in range(dim):
                avg_vector[i] += vec[i]

        # 求平均：总和 / 有效词数
        num_words = len(valid_vectors)
        avg_vector = [v / num_words for v in avg_vector]

        # 返回平均向量
        return avg_vector


# ============================================================
# 模块：TF-IDF 加权平均句向量
# 说明：不是简单平均，而是用 TF-IDF 值作为权重进行加权平均
#      重要词（高 TF-IDF）对句向量的贡献更大
# 优点：比简单平均更能反映句子的核心语义
# 缺点：仍然忽略词序
# ============================================================

class TFIDFWeightedAverage:
    """
    TF-IDF 加权平均编码器：用 TF-IDF 作为权重对词向量加权平均。

    原理：
    sentence_vector = sum(tfidf(w) * word_vector(w)) / sum(tfidf(w))

    与词袋平均的区别：
    - 词袋平均：每个词权重相同（1/n）
    - TF-IDF 加权：重要词权重大，停用词权重小

    属性：
    - word_vectors (SimpleWordVectors): 词向量提供者
    - idf (dict[str, float]): IDF 值字典
    """

    def __init__(self, word_vectors: SimpleWordVectors, idf: dict[str, float]):
        """
        初始化 TF-IDF 加权平均编码器。

        参数：
        - word_vectors (SimpleWordVectors): 提供词向量的对象
        - idf (dict[str, float]): 预计算的 IDF 值字典
        """
        # 词向量提供者
        self.word_vectors = word_vectors
        # IDF 值字典：词 → IDF 值
        self.idf = idf

    def encode(self, sentence: list[str]) -> Optional[list[float]]:
        """
        将句子编码为 TF-IDF 加权平均向量。

        参数：
        - sentence (list[str]): 分词后的句子

        返回：
        - list[float] 或 None: 加权平均向量

        计算步骤：
        1. 计算每个词的 TF 和 TF-IDF
        2. 获取每个词的向量
        3. 用 TF-IDF 作为权重加权平均
        """
        # 文档总词数
        doc_length = len(sentence)
        if doc_length == 0:
            return None

        # 统计词频
        term_freq = Counter(sentence)

        # 存储 (词向量, TF-IDF权重) 对
        weighted_pairs: list[tuple[list[float], float]] = []
        # TF-IDF 权重总和
        total_weight = 0.0

        # 遍历文档中的每个唯一词
        for word, count in term_freq.items():
            # ---------- 计算 TF ----------
            tf = count / doc_length

            # ---------- 获取 IDF ----------
            idf = self.idf.get(word, 1.0)

            # ---------- 计算 TF-IDF ----------
            tfidf = tf * idf

            # ---------- 获取词向量 ----------
            vec = self.word_vectors.get_vector(word)
            if vec is None:
                # 未知词，跳过
                continue

            # 添加加权对
            weighted_pairs.append((vec, tfidf))
            # 累加总权重
            total_weight += tfidf

        # 如果没有有效词，返回 None
        if not weighted_pairs:
            return None

        # ---------- 加权平均 ----------
        # 获取维度
        dim = len(weighted_pairs[0][0])
        # 初始化加权向量
        weighted_vector = [0.0] * dim

        # 累加：sum(weight * vector)
        for vec, weight in weighted_pairs:
            for i in range(dim):
                weighted_vector[i] += weight * vec[i]

        # 归一化：除以总权重
        weighted_vector = [v / total_weight for v in weighted_vector]

        return weighted_vector


# ============================================================
# 模块：简单注意力加权句向量
# 说明：模拟注意力机制的思想，让模型自动学习哪些词更重要
#      这里使用查询向量与词向量的点积作为注意力权重
# 优点：引入上下文感知，比 TF-IDF 更灵活
# 缺点：需要训练查询向量（这里用模拟实现）
# ============================================================

class SimpleAttentionSentence:
    """
    简单注意力加权编码器：模拟注意力机制生成句向量。

    原理（简化版注意力）：
    1. 定义一个查询向量 query（代表"句子主题"）
    2. 计算每个词向量与 query 的点积作为注意力分数
    3. 用 softmax 将分数归一化为注意力权重
    4. 用注意力权重对词向量加权求和

    公式：
    attention_score(w) = dot(query, word_vector(w))
    attention_weight(w) = softmax(attention_scores)
    sentence_vector = sum(attention_weight(w) * word_vector(w))

    属性：
    - word_vectors (SimpleWordVectors): 词向量提供者
    - query (list[float]): 查询向量，用于计算注意力
    """

    def __init__(self, word_vectors: SimpleWordVectors, dim: int = 8):
        """
        初始化注意力编码器。

        参数：
        - word_vectors (SimpleWordVectors): 词向量提供者
        - dim (int): 向量维度
        """
        # 词向量提供者
        self.word_vectors = word_vectors
        # 查询向量：初始化为均匀的向量
        # 在实际应用中，query 是通过训练学习得到的
        self.query = [1.0 / math.sqrt(dim)] * dim

    def _softmax(self, scores: list[float]) -> list[float]:
        """
        计算 softmax，将分数归一化为概率分布。

        公式：softmax(x_i) = exp(x_i) / sum(exp(x_j))

        参数：
        - scores (list[float]): 原始分数列表

        返回：
        - list[float]: 归一化后的概率分布（和为 1）

        注意：使用减去最大值的技巧防止数值溢出
        """
        # 数值稳定性：减去最大值防止 exp 溢出
        max_score = max(scores)
        # 计算 exp(x - max)
        exp_scores = [math.exp(s - max_score) for s in scores]
        # 计算总和
        total = sum(exp_scores)
        # 归一化
        return [e / total for e in exp_scores]

    def _dot_product(self, vec1: list[float], vec2: list[float]) -> float:
        """
        计算两个向量的点积（内积）。

        公式：dot(a, b) = sum(a_i * b_i)

        参数：
        - vec1 (list[float]): 第一个向量
        - vec2 (list[float]): 第二个向量

        返回：
        - float: 点积结果
        """
        result = 0.0
        for i in range(len(vec1)):
            result += vec1[i] * vec2[i]
        return result

    def encode(self, sentence: list[str]) -> Optional[list[float]]:
        """
        将句子编码为注意力加权句向量。

        参数：
        - sentence (list[str]): 分词后的句子

        返回：
        - list[float] 或 None: 注意力加权向量

        计算步骤：
        1. 获取每个词的向量
        2. 计算每个词与 query 的点积作为注意力分数
        3. 用 softmax 归一化为注意力权重
        4. 用注意力权重加权平均词向量
        """
        # 收集有效词向量
        valid_vectors: list[list[float]] = []
        valid_words: list[str] = []

        for word in sentence:
            vec = self.word_vectors.get_vector(word)
            if vec is not None:
                valid_vectors.append(vec)
                valid_words.append(word)

        # 没有有效词
        if not valid_vectors:
            return None

        # 获取维度
        dim = len(valid_vectors[0])

        # ---------- 步骤 1：计算注意力分数 ----------
        scores = []
        for vec in valid_vectors:
            # 点积：query · word_vector
            score = self._dot_product(self.query, vec)
            scores.append(score)

        # ---------- 步骤 2：softmax 归一化 ----------
        weights = self._softmax(scores)

        # ---------- 步骤 3：加权求和 ----------
        result_vector = [0.0] * dim
        for vec, weight in zip(valid_vectors, weights):
            for i in range(dim):
                result_vector[i] += weight * vec[i]

        return result_vector

    def get_attention_weights(self, sentence: list[str]) -> list[tuple[str, float]]:
        """
        获取每个词的注意力权重，用于可视化分析。

        参数：
        - sentence (list[str]): 分词后的句子

        返回：
        - list[tuple[str, float]]: (词, 注意力权重) 列表

        用途：
        - 分析哪些词在句子中更重要
        - 调试注意力机制的效果
        """
        # 收集有效词向量
        valid_vectors: list[list[float]] = []
        valid_words: list[str] = []

        for word in sentence:
            vec = self.word_vectors.get_vector(word)
            if vec is not None:
                valid_vectors.append(vec)
                valid_words.append(word)

        if not valid_vectors:
            return []

        # 计算注意力分数
        scores = []
        for vec in valid_vectors:
            score = self._dot_product(self.query, vec)
            scores.append(score)

        # softmax 归一化
        weights = self._softmax(scores)

        # 返回 (词, 权重) 对
        return list(zip(valid_words, weights))
