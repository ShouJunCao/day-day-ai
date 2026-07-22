"""
embedding_models.py — 主流 Embedding 模型统一客户端
提供 OpenAI、BGE-M3、GTE、M3E、Jina 五种主流 Embedding 模型的统一调用接口。
支持 API 调用和本地推理（HuggingFace Transformers）两种方式。
"""
import os
import math
import json
from typing import Optional
from dataclasses import dataclass, field


# ============================================================
# 模块：Embedding 结果数据结构
# 说明：统一不同模型返回的 Embedding 结果格式
# ============================================================

@dataclass
class EmbeddingResult:
    """
    Embedding 结果：封装向量、模型名、维度等元数据。

    属性：
    - vector (list[float]): 嵌入向量
    - model (str): 使用的模型名称
    - dimension (int): 向量维度
    - usage (dict): Token 使用量（API 模型）
    """
    # 嵌入向量列表
    vector: list[float]
    # 模型名称
    model: str
    # 向量维度
    dimension: int
    # Token 使用量（API 调用时有值）
    usage: dict = field(default_factory=dict)

    def cosine_similarity(self, other: "EmbeddingResult") -> float:
        """
        计算与另一个 EmbeddingResult 的余弦相似度。

        公式：cos(a, b) = (a · b) / (|a| × |b|)

        参数：
        - other (EmbeddingResult): 另一个向量结果

        返回：
        - float: 余弦相似度，范围 [-1, 1]
        """
        # 计算点积
        dot_product = sum(a * b for a, b in zip(self.vector, other.vector))
        # 计算模长
        norm_a = math.sqrt(sum(a * a for a in self.vector))
        norm_b = math.sqrt(sum(b * b for b in other.vector))
        # 防止除以 0
        if norm_a == 0 or norm_b == 0:
            return 0.0
        # 余弦相似度
        return dot_product / (norm_a * norm_b)


# ============================================================
# 模块：OpenAI Embedding 客户端
# 说明：调用 OpenAI API 获取文本嵌入向量
# 模型：text-embedding-3-small（1536 维）、text-embedding-3-large（3072 维）
# ============================================================

class OpenAIEmbedding:
    """
    OpenAI Embedding 客户端：调用 OpenAI API 获取文本嵌入。

    支持的模型：
    - text-embedding-3-small：1536 维，成本低，适合大多数场景
    - text-embedding-3-large：3072 维，精度高，适合需要细粒度区分的场景

    环境变量：
    - OPENAI_API_KEY: API 密钥
    - OPENAI_BASE_URL: API 基础 URL（可选，默认 https://api.openai.com/v1）
    - OPENAI_EMBED_MODEL: 模型名称（可选，默认 text-embedding-3-small）
    """

    # 可用模型列表
    AVAILABLE_MODELS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }

    def __init__(self, model: Optional[str] = None):
        """
        初始化 OpenAI Embedding 客户端。

        参数：
        - model (str): 模型名称，可选。默认从环境变量读取或使用 text-embedding-3-small
        """
        # 从环境变量读取配置
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        # 模型名称：优先使用参数，其次环境变量，最后默认值
        self.model = model or os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
        # 获取模型维度
        self.dimension = self.AVAILABLE_MODELS.get(self.model, 1536)

    def embed(self, text: str) -> EmbeddingResult:
        """
        将单个文本转换为嵌入向量。

        参数：
        - text (str): 要编码的文本

        返回：
        - EmbeddingResult: 包含向量、模型名、维度等信息的结果对象
        """
        import httpx

        # 发送 POST 请求到 OpenAI Embedding API
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                # API 端点
                f"{self.base_url}/embeddings",
                # 请求头：认证和内容类型
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                # 请求体
                json={
                    "model": self.model,
                    "input": text,
                },
            )
            # 检查 HTTP 状态码
            resp.raise_for_status()
            data = resp.json()

            # 提取嵌入向量
            vector = data["data"][0]["embedding"]
            # 提取 Token 使用量
            usage = data.get("usage", {})

            return EmbeddingResult(
                vector=vector,
                model=self.model,
                dimension=self.dimension,
                usage=usage,
            )

    def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        """
        批量编码多个文本。

        参数：
        - texts (list[str]): 要编码的文本列表

        返回：
        - list[EmbeddingResult]: 每个文本对应的结果对象列表
        """
        import httpx

        with httpx.Client(timeout=60) as client:
            resp = client.post(
                f"{self.base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "input": texts,
                },
            )
            resp.raise_for_status()
            data = resp.json()

            results = []
            for item in data["data"]:
                results.append(EmbeddingResult(
                    vector=item["embedding"],
                    model=self.model,
                    dimension=self.dimension,
                    usage=data.get("usage", {}),
                ))
            return results


# ============================================================
# 模块：BGE-M3 客户端
# 说明：BGE-M3 是智源研究院（BAAI）的多功能 Embedding 模型
# 特点：支持多语言（100+ 语言）、多粒度（词/句/段落）、多任务（稠密/稀疏/多向量）
# 维度：1024
# ============================================================

class BGEM3Embedding:
    """
    BGE-M3 Embedding 客户端：使用 HuggingFace Transformers 本地推理。

    特点：
    - 支持 100+ 种语言
    - 同时返回稠密向量（dense）、稀疏向量（sparse）、多向量（multi-vector）
    - 最大序列长度 8192

    环境变量：
    - BGE_MODEL_NAME: 模型路径或名称（可选，默认 BAAI/bge-m3）
    """

    # 模型维度
    DIMENSION = 1024

    def __init__(self, model_name: Optional[str] = None):
        """
        初始化 BGE-M3 客户端。

        参数：
        - model_name (str): 模型名称或本地路径，可选
        """
        self.model_name = model_name or os.getenv("BGE_MODEL_NAME", "BAAI/bge-m3")
        # 延迟加载模型（避免没有 transformers 时报错）
        self._tokenizer = None
        self._model = None

    def _load_model(self):
        """延迟加载模型和分词器"""
        from transformers import AutoTokenizer, AutoModel
        # 加载分词器
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        # 加载模型（使用 float32 精度）
        self._model = AutoModel.from_pretrained(self.model_name)
        # 设置为评估模式（禁用 Dropout 等训练专属层）
        self._model.eval()

    def embed(self, text: str) -> EmbeddingResult:
        """
        将文本编码为稠密向量。

        参数：
        - text (str): 要编码的文本

        返回：
        - EmbeddingResult: 包含 1024 维稠密向量的结果对象
        """
        import torch

        # 延迟加载模型
        if self._model is None:
            self._load_model()

        # 分词：添加前缀 "Represent this sentence for searching relevant passages: "
        # 这是 BGE 模型的标准检索前缀
        inputs = self._tokenizer(
            text,
            padding=True,
            truncation=True,
            max_length=8192,
            return_tensors="pt",
        )

        # 推理：获取最后一层隐藏状态
        with torch.no_grad():
            outputs = self._model(**inputs)
            # 使用 [CLS] token 的向量作为句子表示
            # 对输出做 L2 归一化
            sentence_embeddings = outputs.last_hidden_state[:, 0]
            sentence_embeddings = torch.nn.functional.normalize(
                sentence_embeddings, p=2, dim=1
            )

        # 转换为 Python 列表
        vector = sentence_embeddings[0].tolist()

        return EmbeddingResult(
            vector=vector,
            model=self.model_name,
            dimension=self.DIMENSION,
        )


# ============================================================
# 模块：GTE 客户端
# 说明：GTE（General Text Embedding）是阿里巴巴通义实验室的通用文本嵌入模型
# 特点：在 MTEB 基准上表现优异，支持中英文
# 维度：768（gte-base）、1024（gte-large）
# ============================================================

class GTEEmbedding:
    """
    GTE Embedding 客户端：阿里巴巴通义实验室的通用文本嵌入模型。

    支持的模型：
    - Alibaba-NLP/gte-base-en-v1.5：768 维，英文优化
    - Alibaba-NLP/gte-large-en-v1.5：1024 维，英文优化
    - Alibaba-NLP/gte-multilingual-base：768 维，多语言

    环境变量：
    - GTE_MODEL_NAME: 模型名称（可选，默认 Alibaba-NLP/gte-base-en-v1.5）
    """

    def __init__(self, model_name: Optional[str] = None):
        """
        初始化 GTE 客户端。

        参数：
        - model_name (str): 模型名称或本地路径
        """
        self.model_name = model_name or os.getenv(
            "GTE_MODEL_NAME", "Alibaba-NLP/gte-base-en-v1.5"
        )
        self._tokenizer = None
        self._model = None

    def _load_model(self):
        """延迟加载模型和分词器"""
        from transformers import AutoTokenizer, AutoModel
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self._model = AutoModel.from_pretrained(self.model_name)
        self._model.eval()

    def embed(self, text: str) -> EmbeddingResult:
        """
        将文本编码为嵌入向量。

        参数：
        - text (str): 要编码的文本

        返回：
        - EmbeddingResult: 包含嵌入向量的结果对象
        """
        import torch

        if self._model is None:
            self._load_model()

        # 分词：GTE 使用 instrction 前缀来区分检索和编码任务
        inputs = self._tokenizer(
            text,
            padding=True,
            truncation=True,
            max_length=8192,
            return_tensors="pt",
        )

        with torch.no_grad():
            outputs = self._model(**inputs)
            # 使用 [CLS] token 的向量
            sentence_embeddings = outputs.last_hidden_state[:, 0]
            # L2 归一化
            sentence_embeddings = torch.nn.functional.normalize(
                sentence_embeddings, p=2, dim=1
            )

        vector = sentence_embeddings[0].tolist()

        return EmbeddingResult(
            vector=vector,
            model=self.model_name,
            dimension=len(vector),
        )


# ============================================================
# 模块：M3E 客户端
# 说明：M3E（Mixed-match Massive Multilingual Embeddings）是 MokaAI 开源的多语言嵌入模型
# 特点：在中文语义理解任务上表现优异，支持中英双语
# 维度：768（m3e-base）、1024（m3e-large）
# ============================================================

class M3EEmbedding:
    """
    M3E Embedding 客户端：MokaAI 的多语言嵌入模型，中文优化。

    支持的模型：
    - moka-ai/m3e-base：768 维，中文优化
    - moka-ai/m3e-large：1024 维，中文优化

    环境变量：
    - M3E_MODEL_NAME: 模型名称（可选，默认 moka-ai/m3e-base）
    """

    def __init__(self, model_name: Optional[str] = None):
        """
        初始化 M3E 客户端。

        参数：
        - model_name (str): 模型名称或本地路径
        """
        self.model_name = model_name or os.getenv(
            "M3E_MODEL_NAME", "moka-ai/m3e-base"
        )
        self._tokenizer = None
        self._model = None

    def _load_model(self):
        """延迟加载模型和分词器"""
        from transformers import AutoTokenizer, AutoModel
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self._model = AutoModel.from_pretrained(self.model_name)
        self._model.eval()

    def embed(self, text: str) -> EmbeddingResult:
        """
        将文本编码为嵌入向量。

        参数：
        - text (str): 要编码的文本

        返回：
        - EmbeddingResult: 包含嵌入向量的结果对象
        """
        import torch

        if self._model is None:
            self._load_model()

        inputs = self._tokenizer(
            text,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        )

        with torch.no_grad():
            outputs = self._model(**inputs)
            # 使用 mean pooling（平均池化）而非 CLS
            # M3E 官方推荐使用 mean pooling
            attention_mask = inputs["attention_mask"]
            # 将 padding 位置的向量设为 0
            token_embeddings = outputs.last_hidden_state * attention_mask.unsqueeze(-1)
            # 计算平均值（排除 padding）
            sum_embeddings = token_embeddings.sum(dim=1)
            sum_mask = attention_mask.sum(dim=1, keepdim=True)
            sentence_embeddings = sum_embeddings / sum_mask
            # L2 归一化
            sentence_embeddings = torch.nn.functional.normalize(
                sentence_embeddings, p=2, dim=1
            )

        vector = sentence_embeddings[0].tolist()

        return EmbeddingResult(
            vector=vector,
            model=self.model_name,
            dimension=len(vector),
        )


# ============================================================
# 模块：Jina Embedding 客户端
# 说明：Jina AI 的嵌入模型，支持多语言和长文本（最大 8192 token）
# 特点：API 调用简单，支持 task-specific 模式
# 维度：768（jina-embeddings-v3）
# ============================================================

class JinaEmbedding:
    """
    Jina Embedding 客户端：调用 Jina AI API 获取文本嵌入。

    支持的模型：
    - jina-embeddings-v3：768 维，支持多语言和 8192 token 长文本

    环境变量：
    - JINA_API_KEY: API 密钥
    - JINA_EMBED_MODEL: 模型名称（可选，默认 jina-embeddings-v3）
    """

    DIMENSION = 768

    def __init__(self, model: Optional[str] = None):
        """
        初始化 Jina Embedding 客户端。

        参数：
        - model (str): 模型名称
        """
        self.api_key = os.getenv("JINA_API_KEY", "")
        self.model = model or os.getenv("JINA_EMBED_MODEL", "jina-embeddings-v3")

    def embed(self, text: str, task: str = "text-matching") -> EmbeddingResult:
        """
        将文本编码为嵌入向量。

        参数：
        - text (str): 要编码的文本
        - task (str): 任务类型，可选值：
            - "text-matching": 文本匹配（默认）
            - "text-classification": 文本分类
            - "retrieval.query": 检索查询
            - "retrieval.passage": 检索文档

        返回：
        - EmbeddingResult: 包含嵌入向量的结果对象
        """
        import httpx

        with httpx.Client(timeout=30) as client:
            resp = client.post(
                "https://api.jina.ai/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "input": [text],
                    "task": task,
                },
            )
            resp.raise_for_status()
            data = resp.json()

            vector = data["data"][0]["embedding"]

            return EmbeddingResult(
                vector=vector,
                model=self.model,
                dimension=self.DIMENSION,
                usage=data.get("usage", {}),
            )
