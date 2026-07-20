"""
intent_router.py — 轻量级意图路由器
基于关键词匹配和规则映射识别用户意图，
支持默认意图、置信度计算和意图优先级。
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class IntentDefinition:
    """意图定义"""
    name: str                     # 意图名称
    keywords: list[str]           # 关键词列表
    examples: list[str] = field(default_factory=list)  # 示例
    confidence: float = 0.0       # 匹配置信度
    response_template: str = ""   # 响应模板


@dataclass
class IntentRouter:
    """
    意图路由器：根据用户输入文本匹配预定义意图。

    匹配策略：
    1. 完全匹配（输入完全等于某个关键词）
    2. 子串匹配（输入包含某个关键词）
    3. 分词匹配（简单按空格/标点切分后匹配）

    注：生产环境应接入真正的 NLU 模型（如 BERT 分类器），
    此处仅演示基于规则的轻量级实现。
    """

    intents: list[IntentDefinition] = field(default_factory=list)
    default_intent: str = "unknown"
    min_confidence: float = 0.3  # 最低置信度阈值

    def add_intent(
        self,
        name: str,
        keywords: list[str],
        examples: Optional[list[str]] = None,
        response: str = "",
    ):
        """注册一个新意图"""
        intent = IntentDefinition(
            name=name,
            keywords=keywords,
            examples=examples or [],
            response_template=response,
        )
        self.intents.append(intent)

    def classify(self, text: str) -> dict:
        """
        对用户输入进行意图分类。

        Returns:
            {
                "intent": "intent_name",
                "confidence": 0.0-1.0,
                "matched_keywords": ["..."],
                "is_default": True/False
            }
        """
        text_lower = text.lower().strip()
        best_score = 0.0
        best_intent = self.default_intent
        best_keywords = []

        for intent in self.intents:
            score = self._compute_score(text_lower, intent)
            if score > best_score:
                best_score = score
                best_intent = intent.name
                best_keywords = [
                    kw for kw in intent.keywords
                    if kw.lower() in text_lower
                ]

        # 如果最高置信度低于阈值，返回默认意图
        is_default = best_score < self.min_confidence
        if is_default:
            best_intent = self.default_intent
            best_score = 0.0
            best_keywords = []

        return {
            "intent": best_intent,
            "confidence": round(best_score, 2),
            "matched_keywords": best_keywords,
            "is_default": is_default,
        }

    def _compute_score(self, text: str, intent: IntentDefinition) -> float:
        """
        计算输入文本与意图的匹配分数。

        评分规则：
        - 完全匹配关键词: 每个 +1.0
        - 子串包含关键词: 每个 +0.5
        - 匹配示例: 每个 +0.3
        - 分数上限为 1.0
        """
        score = 0.0

        # 关键词匹配
        for kw in intent.keywords:
            kw_lower = kw.lower()
            if text == kw_lower:
                score += 1.0       # 完全匹配
            elif kw_lower in text:
                score += 0.5       # 子串匹配

        # 示例匹配
        for example in intent.examples:
            if example.lower() in text:
                score += 0.3

        return min(score, 1.0)


def create_hotel_intent_router() -> IntentRouter:
    """创建酒店预订场景的意图路由器"""
    router = IntentRouter(default_intent="unknown")

    router.add_intent(
        name="book_hotel",
        keywords=["预订酒店", "订房", "酒店", "住宿", "booking"],
        examples=["我想订个房间", "帮我预订酒店", "需要住宿"],
        response="好的，我来帮您预订酒店。",
    )

    router.add_intent(
        name="check_price",
        keywords=["多少钱", "价格", "费用", "收费", "price"],
        examples=["多少钱一晚", "价格是多少", "收费情况"],
        response="让我为您查询价格信息。",
    )

    router.add_intent(
        name="cancel_booking",
        keywords=["取消", "退订", "退款", "cancel"],
        examples=["我想取消预订", "可以退订吗", "申请退款"],
        response="好的，我来帮您处理取消。",
    )

    router.add_intent(
        name="greeting",
        keywords=["你好", "您好", "hi", "hello", "早上好", "晚上好"],
        examples=["你好啊", "hi there", "早上好"],
        response="您好！有什么可以帮您的吗？",
    )

    router.add_intent(
        name="transfer_human",
        keywords=["转人工", "人工客服", "真人", "人工服务"],
        examples=["我要转人工", "人工客服在哪里"],
        response="正在为您转接人工客服，请稍候。",
    )

    return router
