"""
model_comparison.py — Embedding 模型对比工具
不依赖实际 API 调用，使用模拟数据演示模型间的差异。
提供模型规格对比、向量相似度计算、成本评估等功能。
"""
import math
import json
from typing import Optional
from dataclasses import dataclass, field


# ============================================================
# 模块：模型规格定义
# 说明：定义各 Embedding 模型的关键参数
# ============================================================

@dataclass
class ModelSpec:
    """
    Embedding 模型规格：封装模型的关键参数。

    属性：
    - name (str): 模型名称
    - provider (str): 提供方
    - dimension (int): 向量维度
    - max_tokens (int): 最大输入 Token 数
    - languages (list[str]): 支持的语言
    - pricing_per_1m (float): 每百万 Token 价格（美元）
    - is_open_source (bool): 是否开源
    - hf_model_id (str): HuggingFace 模型 ID
    - mteb_score (float): MTEB 基准评分（0-100）
    """
    # 模型名称
    name: str
    # 提供方
    provider: str
    # 向量维度
    dimension: int
    # 最大输入 Token 数
    max_tokens: int
    # 支持的语言
    languages: list[str] = field(default_factory=list)
    # 每百万 Token 价格（美元）
    pricing_per_1m: float = 0.0
    # 是否开源
    is_open_source: bool = False
    # HuggingFace 模型 ID
    hf_model_id: str = ""
    # MTEB 基准评分
    mteb_score: float = 0.0

    def estimate_cost(self, num_texts: int, avg_tokens_per_text: float) -> float:
        """
        估算处理指定文本量的成本。

        参数：
        - num_texts (int): 文本数量
        - avg_tokens_per_text (float): 平均每条文本的 Token 数

        返回：
        - float: 估算成本（美元）
        """
        total_tokens = num_texts * avg_tokens_per_text
        return (total_tokens / 1_000_000) * self.pricing_per_1m


# ============================================================
# 模块：预定义的主流 Embedding 模型规格
# ============================================================

EMBEDDING_MODELS = [
    ModelSpec(
        name="text-embedding-3-small",
        provider="OpenAI",
        dimension=1536,
        max_tokens=8191,
        languages=["en"],
        pricing_per_1m=0.02,
        is_open_source=False,
        hf_model_id="",
        mteb_score=64.6,
    ),
    ModelSpec(
        name="text-embedding-3-large",
        provider="OpenAI",
        dimension=3072,
        max_tokens=8191,
        languages=["en"],
        pricing_per_1m=0.13,
        is_open_source=False,
        hf_model_id="",
        mteb_score=67.3,
    ),
    ModelSpec(
        name="BGE-M3",
        provider="BAAI (智源)",
        dimension=1024,
        max_tokens=8192,
        languages=["zh", "en", "ja", "ko", "fr", "de", "es"] + ["multi (100+)"],
        pricing_per_1m=0.0,
        is_open_source=True,
        hf_model_id="BAAI/bge-m3",
        mteb_score=65.4,
    ),
    ModelSpec(
        name="GTE-large-en-v1.5",
        provider="Alibaba (通义)",
        dimension=1024,
        max_tokens=8192,
        languages=["en"],
        pricing_per_1m=0.0,
        is_open_source=True,
        hf_model_id="Alibaba-NLP/gte-large-en-v1.5",
        mteb_score=66.8,
    ),
    ModelSpec(
        name="m3e-base",
        provider="MokaAI",
        dimension=768,
        max_tokens=512,
        languages=["zh", "en"],
        pricing_per_1m=0.0,
        is_open_source=True,
        hf_model_id="moka-ai/m3e-base",
        mteb_score=63.2,
    ),
    ModelSpec(
        name="jina-embeddings-v3",
        provider="Jina AI",
        dimension=768,
        max_tokens=8192,
        languages=["zh", "en", "ja", "ko", "de", "fr", "es"] + ["multi"],
        pricing_per_1m=0.0,
        is_open_source=True,
        hf_model_id="jinaai/jina-embeddings-v3",
        mteb_score=62.1,
    ),
]


# ============================================================
# 模块：模型对比分析器
# 说明：对比各模型的关键指标，生成选择建议
# ============================================================

class ModelComparator:
    """
    Embedding 模型对比分析器。

    功能：
    - 按不同指标排序和筛选模型
    - 估算使用成本
    - 生成选择建议
    """

    def __init__(self, models: Optional[list[ModelSpec]] = None):
        """
        初始化对比分析器。

        参数：
        - models (list[ModelSpec]): 要对比的模型列表
        """
        self.models = models or EMBEDDING_MODELS

    def sort_by_score(self) -> list[ModelSpec]:
        """
        按 MTEB 评分降序排列模型。

        返回：
        - list[ModelSpec]: 按评分降序排列的模型列表
        """
        return sorted(self.models, key=lambda m: m.mteb_score, reverse=True)

    def sort_by_cost(self) -> list[ModelSpec]:
        """
        按成本升序排列模型（免费 → 付费）。

        返回：
        - list[ModelSpec]: 按成本升序排列的模型列表
        """
        return sorted(self.models, key=lambda m: m.pricing_per_1m)

    def filter_open_source(self) -> list[ModelSpec]:
        """
        筛选开源模型。

        返回：
        - list[ModelSpec]: 开源模型列表
        """
        return [m for m in self.models if m.is_open_source]

    def filter_by_language(self, language: str) -> list[ModelSpec]:
        """
        筛选支持指定语言的模型。

        参数：
        - language (str): 语言代码，如 "zh"、"en"

        返回：
        - list[ModelSpec]: 支持该语言的模型列表
        """
        return [m for m in self.models if language in m.languages]

    def estimate_costs(self, num_texts: int, avg_tokens: float) -> dict[str, float]:
        """
        估算各模型处理指定文本量的成本。

        参数：
        - num_texts (int): 文本数量
        - avg_tokens (float): 平均每条文本的 Token 数

        返回：
        - dict[str, float]: 模型名 → 成本（美元）的映射
        """
        costs = {}
        for model in self.models:
            costs[model.name] = model.estimate_cost(num_texts, avg_tokens)
        return costs

    def get_recommendation(self, requirements: dict) -> list[ModelSpec]:
        """
        根据需求推荐模型。

        参数：
        - requirements (dict): 需求字典
            - "language": 需要的语言
            - "max_budget": 最大预算（美元/百万 Token）
            - "min_score": 最低 MTEB 评分
            - "open_source_only": 是否只考虑开源

        返回：
        - list[ModelSpec]: 满足条件的模型列表，按评分降序
        """
        candidates = list(self.models)

        # 按语言筛选
        if "language" in requirements:
            lang = requirements["language"]
            candidates = [m for m in candidates if lang in m.languages]

        # 按预算筛选
        if "max_budget" in requirements:
            budget = requirements["max_budget"]
            candidates = [m for m in candidates if m.pricing_per_1m <= budget]

        # 按最低评分筛选
        if "min_score" in requirements:
            min_score = requirements["min_score"]
            candidates = [m for m in candidates if m.mteb_score >= min_score]

        # 只考虑开源
        if requirements.get("open_source_only", False):
            candidates = [m for m in candidates if m.is_open_source]

        # 按评分降序
        return sorted(candidates, key=lambda m: m.mteb_score, reverse=True)


# ============================================================
# 模块：向量相似度计算工具
# 说明：提供余弦相似度、欧氏距离等向量距离计算方法
# ============================================================

class SimilarityCalculator:
    """
    向量相似度计算器：提供多种向量距离度量方法。
    """

    @staticmethod
    def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
        """
        计算余弦相似度。

        公式：cos(a, b) = (a · b) / (|a| × |b|)

        参数：
        - vec1 (list[float]): 第一个向量
        - vec2 (list[float]): 第二个向量

        返回：
        - float: 余弦相似度，范围 [-1, 1]
            1.0 表示完全相同，-1.0 表示完全相反，0 表示正交
        """
        # 计算点积
        dot = sum(a * b for a, b in zip(vec1, vec2))
        # 计算模长
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    @staticmethod
    def euclidean_distance(vec1: list[float], vec2: list[float]) -> float:
        """
        计算欧氏距离。

        公式：dist = √(Σ(a_i - b_i)²)

        参数：
        - vec1 (list[float]): 第一个向量
        - vec2 (list[float]): 第二个向量

        返回：
        - float: 欧氏距离，值越小表示越相似
        """
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(vec1, vec2)))

    @staticmethod
    def dot_product(vec1: list[float], vec2: list[float]) -> float:
        """
        计算点积（内积）。

        公式：dot = Σ(a_i × b_i)

        参数：
        - vec1 (list[float]): 第一个向量
        - vec2 (list[float]): 第二个向量

        返回：
        - float: 点积值
        """
        return sum(a * b for a, b in zip(vec1, vec2))


# ============================================================
# 模块：演示函数
# ============================================================

def demo_model_comparison():
    """演示模型对比功能"""
    print("=" * 60)
    print("  Embedding 模型对比 — Model Comparison 演示")
    print("=" * 60)

    comparator = ModelComparator()

    # 按 MTEB 评分排序
    print("\n1. 按 MTEB 评分排序:")
    for i, model in enumerate(comparator.sort_by_score(), 1):
        print(f"   {i}. {model.name:30s} MTEB={model.mteb_score:.1f} "
              f"维度={model.dimension} 价格=${model.pricing_per_1m:.2f}/M")

    # 按成本排序
    print("\n2. 按成本排序（免费优先）:")
    for i, model in enumerate(comparator.sort_by_cost(), 1):
        tag = "🆓" if model.pricing_per_1m == 0 else f"💰 ${model.pricing_per_1m:.2f}/M"
        print(f"   {i}. {model.name:30s} {tag}  MTEB={model.mteb_score:.1f}")

    # 中文支持筛选
    print("\n3. 支持中文的模型:")
    zh_models = comparator.filter_by_language("zh")
    for model in zh_models:
        print(f"   • {model.name:30s} 维度={model.dimension} "
              f"开源={'✅' if model.is_open_source else '❌'}")

    # 成本估算
    print("\n4. 成本估算（10 万条文本，平均 100 Token/条）:")
    costs = comparator.estimate_costs(100_000, 100)
    for name, cost in costs.items():
        if cost > 0:
            print(f"   {name:30s} ${cost:.2f}")
        else:
            print(f"   {name:30s} 🆓 免费")

    # 推荐
    print("\n5. 场景推荐:")
    # 场景 1：中文 + 免费 + 开源
    rec1 = comparator.get_recommendation({
        "language": "zh",
        "open_source_only": True,
    })
    print("   中文 + 开源:")
    for m in rec1[:3]:
        print(f"     ✅ {m.name} (MTEB={m.mteb_score}, 维度={m.dimension})")

    # 场景 2：最高精度
    rec2 = comparator.get_recommendation({"min_score": 65.0})
    print("   最高精度 (MTEB ≥ 65):")
    for m in rec2[:3]:
        price = f"${m.pricing_per_1m:.2f}/M" if m.pricing_per_1m > 0 else "免费"
        print(f"     ✅ {m.name} (MTEB={m.mteb_score}, 价格={price})")


def demo_similarity_calculation():
    """演示向量相似度计算"""
    print("\n" + "=" * 60)
    print("  向量相似度计算 — Similarity Calculator 演示")
    print("=" * 60)

    calc = SimilarityCalculator()

    # 模拟向量
    vec_cat = [0.1, 0.2, 0.3, 0.4, 0.5]
    vec_dog = [0.15, 0.18, 0.32, 0.38, 0.48]
    vec_car = [0.8, 0.1, 0.0, 0.0, 0.1]

    print("\n测试向量（5 维，模拟）:")
    print(f"  猫 (cat):   {vec_cat}")
    print(f"  狗 (dog):   {vec_dog}")
    print(f"  车 (car):   {vec_car}")

    print("\n余弦相似度:")
    sim_cd = calc.cosine_similarity(vec_cat, vec_dog)
    sim_cc = calc.cosine_similarity(vec_cat, vec_car)
    print(f"  猫 vs 狗: {sim_cd:.4f} (语义相近，应较高)")
    print(f"  猫 vs 车: {sim_cc:.4f} (语义无关，应较低)")

    print("\n欧氏距离:")
    dist_cd = calc.euclidean_distance(vec_cat, vec_dog)
    dist_cc = calc.euclidean_distance(vec_cat, vec_car)
    print(f"  猫 vs 狗: {dist_cd:.4f} (距离近)")
    print(f"  猫 vs 车: {dist_cc:.4f} (距离远)")

    print("\n点积:")
    dp_cd = calc.dot_product(vec_cat, vec_dog)
    dp_cc = calc.dot_product(vec_cat, vec_car)
    print(f"  猫 vs 狗: {dp_cd:.4f}")
    print(f"  猫 vs 车: {dp_cc:.4f}")


def demo_embedding_search_simulation():
    """演示使用 Embedding 进行语义搜索的模拟流程"""
    print("\n" + "=" * 60)
    print("  语义搜索模拟 — Semantic Search Simulation")
    print("=" * 60)

    calc = SimilarityCalculator()

    # 模拟文档库的嵌入向量（简化为 4 维）
    documents = {
        "文档 1: 猫和狗都是常见的宠物": [0.8, 0.6, 0.1, 0.2],
        "文档 2: Python 是一门编程语言": [0.1, 0.1, 0.9, 0.8],
        "文档 3: 猫喜欢抓老鼠": [0.7, 0.5, 0.2, 0.1],
        "文档 4: 机器学习需要大量数据": [0.1, 0.2, 0.8, 0.7],
        "文档 5: 狗是人类最好的朋友": [0.6, 0.7, 0.1, 0.1],
    }

    # 查询向量（模拟"可爱的动物"的嵌入）
    query = "可爱的动物"
    query_vec = [0.75, 0.65, 0.0, 0.1]

    print(f"\n查询: \"{query}\"")
    print(f"查询向量: {query_vec}\n")

    # 计算每个文档与查询的余弦相似度
    results = []
    for doc_text, doc_vec in documents.items():
        similarity = calc.cosine_similarity(query_vec, doc_vec)
        results.append((doc_text, similarity))

    # 按相似度降序排序
    results.sort(key=lambda x: x[1], reverse=True)

    print("搜索结果（按余弦相似度排序）:")
    for i, (doc, sim) in enumerate(results, 1):
        bar = "█" * int(sim * 20)
        print(f"  {i}. [{bar:<20s}] {sim:.4f}  {doc}")


if __name__ == "__main__":
    demo_model_comparison()
    demo_similarity_calculation()
    demo_embedding_search_simulation()
