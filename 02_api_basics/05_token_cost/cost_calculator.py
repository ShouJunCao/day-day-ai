"""
费用计算器 - 精确估算和追踪API调用成本

大模型API按token计费，输入和输出的单价通常不同。
本模块提供费用计算工具，帮助开发者在开发阶段预估成本，
在运行阶段实时追踪实际花费。

计费规则：
    - 输入token：用户发送的prompt + system prompt
    - 输出token：模型生成的response
    - 不同模型价格差异巨大（可达100倍）
    - 缓存命中的token通常享受折扣
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class ModelPricing:
    """模型定价信息

    Attributes:
        model_name: 模型名称
        input_price: 输入价格（每百万token，单位：美元）
        output_price: 输出价格（每百万token，单位：美元）
        provider: 模型提供商
        currency: 货币单位
    """

    model_name: str
    input_price: float
    output_price: float
    provider: str = "OpenAI"
    currency: str = "USD"


@dataclass
class UsageRecord:
    """单次API调用的用量记录

    Attributes:
        model: 使用的模型名称
        input_tokens: 输入token数
        output_tokens: 输出token数
        cost: 本次调用费用
        timestamp: 调用时间
    """

    model: str
    input_tokens: int
    output_tokens: int
    cost: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class CostCalculator:
    """API费用计算器

    功能：
    1. 预估单次调用费用
    2. 累积追踪多次调用费用
    3. 多模型费用对比
    4. 导出用量报告

    Example:
        calc = CostCalculator()
        cost = calc.estimate_cost(
            model="gpt-4o-mini",
            input_tokens=500,
            output_tokens=200,
        )
        print(f"预估费用: ${cost:.6f}")
    """

    # 主流模型定价表（每百万token，美元）
    # 数据来源：各厂商官网，2025年价格
    PRICING: Dict[str, ModelPricing] = {
        # OpenAI
        "gpt-4o": ModelPricing(
            model_name="gpt-4o",
            input_price=2.50,
            output_price=10.00,
            provider="OpenAI",
        ),
        "gpt-4o-mini": ModelPricing(
            model_name="gpt-4o-mini",
            input_price=0.15,
            output_price=0.60,
            provider="OpenAI",
        ),
        # DeepSeek
        "deepseek-chat": ModelPricing(
            model_name="deepseek-chat",
            input_price=0.27,
            output_price=1.10,
            provider="DeepSeek",
        ),
        "deepseek-reasoner": ModelPricing(
            model_name="deepseek-reasoner",
            input_price=0.55,
            output_price=2.19,
            provider="DeepSeek",
        ),
        # 通义千问
        "qwen-plus": ModelPricing(
            model_name="qwen-plus",
            input_price=0.40,
            output_price=1.20,
            provider="阿里云",
        ),
        "qwen-turbo": ModelPricing(
            model_name="qwen-turbo",
            input_price=0.10,
            output_price=0.30,
            provider="阿里云",
        ),
        # Anthropic
        "claude-sonnet-4": ModelPricing(
            model_name="claude-sonnet-4",
            input_price=3.00,
            output_price=15.00,
            provider="Anthropic",
        ),
        "claude-haiku-3.5": ModelPricing(
            model_name="claude-haiku-3.5",
            input_price=0.80,
            output_price=4.00,
            provider="Anthropic",
        ),
    }

    def __init__(self):
        """初始化费用计算器"""
        self.usage_history: List[UsageRecord] = []

    def estimate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """预估单次调用费用

        Args:
            model: 模型名称
            input_tokens: 输入token数
            output_tokens: 输出token数

        Returns:
            预估费用（美元）

        Raises:
            ValueError: 模型不在定价表中
        """
        pricing = self.PRICING.get(model)
        if not pricing:
            available = ", ".join(self.PRICING.keys())
            raise ValueError(f"未知模型: {model}，可用: {available}")

        # 价格单位是"每百万token"，需要除以1,000,000
        input_cost = (input_tokens / 1_000_000) * pricing.input_price
        output_cost = (output_tokens / 1_000_000) * pricing.output_price

        return input_cost + output_cost

    def record_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> UsageRecord:
        """记录一次API调用并计算费用

        Args:
            model: 模型名称
            input_tokens: 输入token数
            output_tokens: 输出token数

        Returns:
            用量记录对象
        """
        cost = self.estimate_cost(model, input_tokens, output_tokens)

        record = UsageRecord(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
        )

        self.usage_history.append(record)
        return record

    def get_total_cost(self) -> float:
        """获取累积总费用

        Returns:
            历史所有调用的总费用（美元）
        """
        return sum(r.cost for r in self.usage_history)

    def get_cost_by_model(self) -> Dict[str, float]:
        """按模型统计费用

        Returns:
            各模型的累积费用字典
        """
        costs: Dict[str, float] = {}
        for record in self.usage_history:
            costs[record.model] = costs.get(record.model, 0) + record.cost
        return costs

    def compare_models(
        self,
        input_tokens: int,
        output_tokens: int,
    ) -> List[Dict]:
        """对比不同模型的费用（帮助选择性价比最高的模型）

        Args:
            input_tokens: 预估输入token数
            output_tokens: 预估输出token数

        Returns:
            按费用从低到高排序的模型费用列表
        """
        comparisons = []
        for name, pricing in self.PRICING.items():
            cost = self.estimate_cost(name, input_tokens, output_tokens)
            comparisons.append({
                "model": name,
                "provider": pricing.provider,
                "cost": cost,
                "input_price": pricing.input_price,
                "output_price": pricing.output_price,
            })

        # 按费用排序
        comparisons.sort(key=lambda x: x["cost"])
        return comparisons


# --- 使用示例 ---
if __name__ == "__main__":
    calc = CostCalculator()

    # 示例1：预估单次调用费用
    print("=" * 50)
    print("单次调用费用预估")
    print("=" * 50)
    cost = calc.estimate_cost("gpt-4o-mini", input_tokens=500, output_tokens=200)
    print(f"GPT-4o-mini (500输入+200输出): ${cost:.6f}")

    # 示例2：多模型费用对比
    print(f"\n{'=' * 50}")
    print("多模型费用对比（1000输入 + 500输出）")
    print(f"{'=' * 50}")
    comparisons = calc.compare_models(input_tokens=1000, output_tokens=500)
    for item in comparisons:
        print(f"  {item['provider']:10} {item['model']:20} ${item['cost']:.6f}")

    # 示例3：模拟多次调用并追踪费用
    print(f"\n{'=' * 50}")
    print("累积费用追踪")
    print(f"{'=' * 50}")
    for i in range(10):
        calc.record_usage("gpt-4o-mini", input_tokens=800, output_tokens=300)
    for i in range(5):
        calc.record_usage("deepseek-chat", input_tokens=800, output_tokens=300)

    print(f"总调用次数: {len(calc.usage_history)}")
    print(f"总费用: ${calc.get_total_cost():.6f}")
    print(f"\n按模型统计:")
    for model, cost in calc.get_cost_by_model().items():
        print(f"  {model}: ${cost:.6f}")
