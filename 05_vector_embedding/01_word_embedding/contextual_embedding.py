"""
contextual_embedding.py — 上下文感知嵌入（Contextual Embedding）
演示从静态词向量到上下文动态词向量的演进。
包含三种上下文感知方法的完整实现：
1. 基于双向上下文的词向量（简化版 BiLSTM 思想）
2. 基于自注意力的上下文编码
3. 完整的 Transformer Encoder 层（教学版）
"""
import math
from typing import Optional


# ============================================================
# 模块：双向上下文词向量（简化版 BiLSTM 思想）
# 说明：传统词向量（如 Word2Vec）是静态的，同一个词在任何上下文中向量相同
#      上下文感知词向量根据词的左右邻居动态调整向量
# 公式：context_vector(w) = forward(w) + backward(w)
#       forward(w)  = 从左到右累积上下文
#       backward(w) = 从右到左累积上下文
# ============================================================

class BiContextualEncoder:
    """
    双向上下文编码器：根据词的左右邻居生成动态词向量。

    原理（简化版 BiLSTM）：
    - 前向传递：从左到右扫描，每个词的向量累加左侧上下文信息
    - 后向传递：从右到左扫描，每个词的向量累加右侧上下文信息
    - 最终向量 = 前向向量 + 后向向量 + 词本身向量

    与静态词向量的区别：
    - 静态："银行"在"人民银行"和"银行门口"中向量相同
    - 动态：根据左右邻居调整向量，区分不同含义

    属性：
    - word_vectors: 基础词向量提供者
    - context_weight: 上下文信息的影响权重（0-1）
    """

    def __init__(self, word_vectors, context_weight: float = 0.3):
        """
        初始化双向上下文编码器。

        参数：
        - word_vectors: 提供基础词向量的对象（需有 get_vector 方法）
        - context_weight (float): 上下文信息的权重
            0.0 = 完全忽略上下文（退化为静态词向量）
            1.0 = 上下文影响最大
        """
        # 基础词向量提供者
        self.word_vectors = word_vectors
        # 上下文权重
        self.context_weight = context_weight

    def encode_sentence(self, sentence: list[str]) -> list[Optional[list[float]]]:
        """
        将整个句子编码为上下文感知的词向量列表。

        参数：
        - sentence (list[str]): 分词后的句子

        返回：
        - list[Optional[list[float]]]: 每个词的上下文感知向量

        计算步骤：
        1. 获取所有基础词向量
        2. 前向传递：从左到右累积上下文
        3. 后向传递：从右到左累积上下文
        4. 合并：词向量 + 前向上下文 + 后向上下文
        """
        # 获取所有基础词向量
        base_vectors: list[Optional[list[float]]] = []
        for word in sentence:
            vec = self.word_vectors.get_vector(word)
            base_vectors.append(vec)

        # 获取维度
        dim = 0
        for vec in base_vectors:
            if vec is not None:
                dim = len(vec)
                break

        if dim == 0:
            return base_vectors

        # ---------- 前向传递（从左到右） ----------
        # forward_context[i] = 前 i 个词的累积信息
        forward_context = [[0.0] * dim for _ in range(len(sentence))]
        # 当前累积的上下文向量
        accumulated = [0.0] * dim

        for i in range(len(sentence)):
            if base_vectors[i] is not None:
                # 将当前词加入累积上下文
                for j in range(dim):
                    accumulated[j] += base_vectors[i][j]
                # 记录当前位置的前向上下文
                for j in range(dim):
                    forward_context[i][j] = accumulated[j]

        # ---------- 后向传递（从右到左） ----------
        # backward_context[i] = 从第 i 个词到末尾的累积信息
        backward_context = [[0.0] * dim for _ in range(len(sentence))]
        accumulated = [0.0] * dim

        for i in range(len(sentence) - 1, -1, -1):
            if base_vectors[i] is not None:
                # 将当前词加入累积上下文
                for j in range(dim):
                    accumulated[j] += base_vectors[i][j]
                # 记录当前位置的后向上下文
                for j in range(dim):
                    backward_context[i][j] = accumulated[j]

        # ---------- 合并 ----------
        contextual_vectors: list[Optional[list[float]]] = []
        for i in range(len(sentence)):
            if base_vectors[i] is None:
                # 未知词
                contextual_vectors.append(None)
                continue

            # 创建结果向量
            result = [0.0] * dim
            # 安全访问：已确认 base_vectors[i] 不是 None
            bv = base_vectors[i]
            assert bv is not None  # 类型守卫
            for j in range(dim):
                # 基础词向量 + 前向上下文权重 + 后向上下文权重
                result[j] = (
                    bv[j]
                    + self.context_weight * forward_context[i][j]
                    + self.context_weight * backward_context[i][j]
                )

            # 归一化
            norm = math.sqrt(sum(v * v for v in result))
            if norm > 0:
                result = [v / norm for v in result]

            contextual_vectors.append(result)

        return contextual_vectors


# ============================================================
# 模块：自注意力层（Self-Attention）
# 说明：Transformer 的核心组件
#      让序列中的每个词都能"看到"其他所有词的信息
# 公式：Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) · V
# ============================================================

class SelfAttentionLayer:
    """
    自注意力层：计算序列中所有词对之间的注意力权重。

    原理：
    - Query (Q)：我想知道什么？
    - Key (K)：我有什么信息可以提供？
    - Value (V)：我的实际内容是什么？

    对于每个词：
    1. 用 Q 向量去"查询"所有词的 K 向量
    2. 点积越大，表示相关性越高
    3. 用 softmax 归一化为注意力权重
    4. 用权重对所有词的 V 向量加权求和

    属性：
    - dim (int): 向量维度
    - W_q (list[float]): Query 权重矩阵（展平）
    - W_k (list[float]): Key 权重矩阵（展平）
    - W_v (list[float]): Value 权重矩阵（展平）
    """

    def __init__(self, dim: int = 8):
        """
        初始化自注意力层。

        参数：
        - dim (int): 向量维度
        """
        # 向量维度
        self.dim = dim
        # 初始化 Q/K/V 权重矩阵（简化为对角矩阵）
        # 实际 Transformer 中这些是训练的密集矩阵
        self.W_q = [1.0] * dim  # Query 权重
        self.W_k = [1.0] * dim  # Key 权重
        self.W_v = [1.0] * dim  # Value 权重

    def _apply_weight(self, vec: list[float], weights: list[float]) -> list[float]:
        """
        将权重应用到向量上（逐元素乘法）。

        参数：
        - vec (list[float]): 输入向量
        - weights (list[float]): 权重向量

        返回：
        - list[float]: 加权后的向量
        """
        result = []
        for i in range(len(vec)):
            result.append(vec[i] * weights[i])
        return result

    def _dot_product(self, vec1: list[float], vec2: list[float]) -> float:
        """
        计算两个向量的点积。

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

    def _softmax(self, scores: list[float]) -> list[float]:
        """
        计算 softmax，将注意力分数归一化为概率分布。

        参数：
        - scores (list[float]): 原始注意力分数

        返回：
        - list[float]: 归一化后的注意力权重
        """
        max_score = max(scores)
        exp_scores = [math.exp(s - max_score) for s in scores]
        total = sum(exp_scores)
        return [e / total for e in exp_scores]

    def forward(self, input_vectors: list[list[float]]) -> list[list[float]]:
        """
        前向传播：计算自注意力输出。

        参数：
        - input_vectors (list[list[float]]): 输入序列的词向量列表

        返回：
        - list[list[float]]: 输出序列的上下文感知向量

        计算步骤（对每个位置 i）：
        1. 计算 query_i = W_q · input_i
        2. 对每个位置 j，计算 key_j = W_k · input_j
        3. 计算注意力分数 score_ij = dot(query_i, key_j) / sqrt(dim)
        4. 对分数做 softmax 得到注意力权重
        5. 计算输出 = sum(weight_ij * value_j)，其中 value_j = W_v · input_j
        """
        n = len(input_vectors)
        if n == 0:
            return []

        dim = len(input_vectors[0])

        # ---------- 步骤 1：计算所有位置的 Q, K, V ----------
        Q = []  # Query 向量列表
        K = []  # Key 向量列表
        V = []  # Value 向量列表

        for vec in input_vectors:
            # Q_i = W_q ⊙ input_i（逐元素乘法）
            Q.append(self._apply_weight(vec, self.W_q))
            # K_i = W_k ⊙ input_i
            K.append(self._apply_weight(vec, self.W_k))
            # V_i = W_v ⊙ input_i
            V.append(self._apply_weight(vec, self.W_v))

        # ---------- 步骤 2：计算注意力分数矩阵 ----------
        # attention_scores[i][j] = Q_i · K_j / sqrt(dim)
        # 缩放因子：防止点积过大导致 softmax 梯度消失
        scale = math.sqrt(dim)

        # ---------- 步骤 3：对每个位置计算输出 ----------
        output = []
        for i in range(n):
            # 计算位置 i 对所有位置 j 的注意力分数
            scores = []
            for j in range(n):
                # 点积 + 缩放
                score = self._dot_product(Q[i], K[j]) / scale
                scores.append(score)

            # softmax 归一化
            weights = self._softmax(scores)

            # 加权求和 Value
            result_vec = [0.0] * dim
            for j in range(n):
                for d in range(dim):
                    result_vec[d] += weights[j] * V[j][d]

            output.append(result_vec)

        return output


# ============================================================
# 模块：Transformer Encoder 层（教学版）
# 说明：完整的 Transformer Encoder 层包含：
#      1. 多头自注意力（这里简化为单头）
#      2. 残差连接（Residual Connection）
#      3. 层归一化（Layer Normalization）
#      4. 前馈神经网络（Feed-Forward Network）
# ============================================================

class TransformerEncoderLayer:
    """
    Transformer Encoder 层：自注意力 + 前馈网络的组合。

    结构：
    Input → 自注意力 → 残差连接 → 层归一化 → 前馈网络 → 残差连接 → 层归一化 → Output

    每个子步骤：
    1. 自注意力：让每个词看到所有其他词的信息
    2. 残差连接：input + sublayer(input)，防止梯度消失
    3. 层归一化：对每个位置的向量做归一化，稳定训练
    4. 前馈网络：两层 MLP，引入非线性变换
    """

    def __init__(self, dim: int = 8):
        """
        初始化 Encoder 层。

        参数：
        - dim (int): 向量维度
        """
        # 向量维度
        self.dim = dim
        # 自注意力子层
        self.attention = SelfAttentionLayer(dim)

    def _layer_norm(self, vectors: list[list[float]]) -> list[list[float]]:
        """
        层归一化（Layer Normalization）：对每个位置的向量做归一化。

        公式：
        mean = sum(x_i) / n
        variance = sum((x_i - mean)^2) / n
        normalized = (x_i - mean) / sqrt(variance + epsilon)

        参数：
        - vectors (list[list[float]]): 输入向量列表

        返回：
        - list[list[float]]: 归一化后的向量

        作用：
        - 稳定训练过程
        - 加速收敛
        - 减少对初始化的敏感度
        """
        epsilon = 1e-5  # 防止除以 0
        normalized = []

        for vec in vectors:
            # 计算均值
            mean = sum(vec) / len(vec)
            # 计算方差
            variance = sum((x - mean) ** 2 for x in vec) / len(vec)
            # 归一化
            norm_vec = []
            for x in vec:
                norm_vec.append((x - mean) / math.sqrt(variance + epsilon))
            normalized.append(norm_vec)

        return normalized

    def _residual_add(self, original: list[list[float]], transformed: list[list[float]]) -> list[list[float]]:
        """
        残差连接：原始输入 + 变换后的输出。

        公式：output = original + transformed

        参数：
        - original (list[list[float]]): 原始输入
        - transformed (list[list[float]]): 变换后的输出

        返回：
        - list[list[float]]: 残差连接结果

        作用：
        - 防止深层网络中的梯度消失
        - 让信息可以直接跳过子层传递
        """
        result = []
        for orig, trans in zip(original, transformed):
            residual = []
            for i in range(len(orig)):
                residual.append(orig[i] + trans[i])
            result.append(residual)
        return result

    def _feed_forward(self, vectors: list[list[float]], hidden_dim: int = 16) -> list[list[float]]:
        """
        前馈神经网络（Feed-Forward Network）：两层 MLP + ReLU 激活。

        结构：
        x → Linear(dim → hidden_dim) → ReLU → Linear(hidden_dim → dim)

        参数：
        - vectors (list[list[float]]): 输入向量列表
        - hidden_dim (int): 隐藏层维度

        返回：
        - list[list[float]]: 前馈网络输出
        """
        # 简化实现：使用确定性权重（实际中通过训练学习）
        output = []
        for vec in vectors:
            # 第一层：dim → hidden_dim + ReLU
            hidden = []
            for h in range(hidden_dim):
                val = 0.0
                for d in range(self.dim):
                    # 简化权重：使用正弦函数
                    val += vec[d] * math.sin((h + 1) * (d + 1) * 0.1)
                # ReLU 激活：max(0, x)
                hidden.append(max(0.0, val))

            # 第二层：hidden_dim → dim
            result = []
            for d in range(self.dim):
                val = 0.0
                for h in range(hidden_dim):
                    val += hidden[h] * math.sin((h + 1) * (d + 1) * 0.1)
                result.append(val)

            output.append(result)

        return output

    def forward(self, input_vectors: list[list[float]]) -> list[list[float]]:
        """
        Encoder 层的前向传播。

        完整流程：
        Input
          ↓
        [Sub-layer 1: 自注意力]
          ↓
        [残差连接: Input + Attention(Input)]
          ↓
        [层归一化]
          ↓
        [Sub-layer 2: 前馈网络]
          ↓
        [残差连接: Norm1 + FFN(Norm1)]
          ↓
        [层归一化]
          ↓
        Output

        参数：
        - input_vectors (list[list[float]]): 输入序列的词向量

        返回：
        - list[list[float]]: 编码后的上下文感知向量
        """
        # ===== Sub-layer 1: 自注意力 =====
        # 自注意力输出
        attn_output = self.attention.forward(input_vectors)
        # 残差连接
        residual1 = self._residual_add(input_vectors, attn_output)
        # 层归一化
        norm1 = self._layer_norm(residual1)

        # ===== Sub-layer 2: 前馈网络 =====
        # 前馈网络输出
        ffn_output = self._feed_forward(norm1)
        # 残差连接
        residual2 = self._residual_add(norm1, ffn_output)
        # 层归一化
        norm2 = self._layer_norm(residual2)

        return norm2
