"""
intent_classifier.py — 意图分类器
提供三种意图分类实现：
1. 基于 BERT 的传统方法
2. 基于关键词的轻量方法（零依赖）
3. 混合路由（低成本优先，必要时回退 LLM）
"""
import os
import re
from typing import Optional


class IntentClassifier:
    """
    意图分类器：将用户输入分类到预定义意图。

    提供两种模式：
    - keyword: 基于关键词匹配，零依赖，极低延迟
    - bert: 基于 BERT 微调，需要 transformers 库

    生产环境推荐使用混合模式：先用 keyword 过滤高置信度样本，
    低置信度样本回退到 BERT 或 LLM。
    """

    # 预定义意图列表
    INTENTS = [
        "book_flight",
        "book_hotel",
        "query_weather",
        "query_order",
        "cancel_booking",
        "greet",
        "chitchat",
        "unknown",
    ]

    # 关键词映射表（零依赖模式使用）
    KEYWORD_MAP = {
        "book_flight": ["订机票", "订航班", "机票", "航班", "飞", "机票预订"],
        "book_hotel": ["订酒店", "订房", "酒店", "住宿", "booking", "订个房"],
        "query_weather": ["天气", "气温", "下雨", "晴天", "天气预报"],
        "query_order": ["查询订单", "查订单", "订单", "我的预订", "查看"],
        "cancel_booking": ["取消", "退订", "退款", "cancel"],
        "greet": ["你好", "您好", "hi", "hello", "早上好", "晚上好"],
        "chitchat": ["聊天", "随便", "聊聊", "笑话", "讲故事"],
    }

    def __init__(self, mode: str = "keyword"):
        """
        初始化分类器。

        Args:
            mode: "keyword"（关键词匹配）或 "bert"（BERT 分类）
        """
        self.mode = mode
        if mode == "bert":
            self._init_bert()

    def _init_bert(self):
        """初始化 BERT 分类模型"""
        try:
            import torch
            from transformers import BertTokenizer, BertForSequenceClassification
        except ImportError:
            raise ImportError(
                "BERT 模式需要安装 transformers 和 torch: "
                "pip install transformers torch"
            )

        model_name = os.getenv("BERT_MODEL", "bert-base-chinese")
        self.tokenizer = BertTokenizer.from_pretrained(model_name)
        self.model = BertForSequenceClassification.from_pretrained(
            model_name, num_labels=len(self.INTENTS)
        )
        self.model.eval()

    def predict(self, text: str) -> dict:
        """
        预测输入文本的意图。

        Returns:
            {
                "intent": str,
                "confidence": float,
                "all_scores": {"intent_name": score, ...}
            }
        """
        if self.mode == "keyword":
            return self._predict_keyword(text)
        else:
            return self._predict_bert(text)

    def _predict_keyword(self, text: str) -> dict:
        """基于关键词匹配的意图分类"""
        text_lower = text.lower()
        scores = {}

        for intent, keywords in self.KEYWORD_MAP.items():
            match_count = sum(1 for kw in keywords if kw in text_lower)
            # 置信度 = 匹配关键词数（至少 1 个即有分）
            scores[intent] = match_count

        # 找出最高分意图
        best_intent = "unknown"
        best_score = 0.0
        for intent, score in scores.items():
            if score > best_score:
                best_score = score
                best_intent = intent

        # 如果没有任何匹配，返回 unknown
        if best_score == 0:
            return {
                "intent": "unknown",
                "confidence": 0.0,
                "all_scores": {
                    k: round(v / max(len(self.KEYWORD_MAP.get(k, [])), 1), 3)
                    for k, v in scores.items()
                },
            }

        # 归一化置信度
        max_possible = max(len(kw) for kw in self.KEYWORD_MAP.values())
        confidence = min(best_score / max_possible, 1.0)

        # 格式化 all_scores
        all_scores = {}
        for k, v in scores.items():
            max_kw = len(self.KEYWORD_MAP.get(k, []))
            all_scores[k] = round(v / max_kw if max_kw > 0 else 0.0, 3)

        return {
            "intent": best_intent,
            "confidence": round(confidence, 3),
            "all_scores": all_scores,
        }

    def _predict_bert(self, text: str) -> dict:
        """基于 BERT 的意图分类"""
        import torch

        inputs = self.tokenizer(
            text, return_tensors="pt", truncation=True, max_length=128
        )
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)
            top_idx = probs.argmax().item()

        all_scores = {
            label: round(probs[0][i].item(), 3)
            for i, label in enumerate(self.INTENTS)
        }

        return {
            "intent": self.INTENTS[top_idx],
            "confidence": round(probs[0][top_idx].item(), 3),
            "all_scores": all_scores,
        }


class HybridIntentClassifier:
    """
    混合意图分类器：平衡成本和效果。

    策略：
    1. 先用关键词匹配做快速分类
    2. 如果置信度 >= 0.8，直接返回
    3. 如果置信度在 0.3-0.8 之间，回退到 BERT 或 LLM
    4. 如果置信度 < 0.3，直接返回 unknown
    """

    def __init__(
        self,
        high_threshold: float = 0.8,
        low_threshold: float = 0.3,
        fallback_mode: str = "keyword",
    ):
        """
        Args:
            high_threshold: 高置信度阈值，超过直接返回
            low_threshold: 低置信度阈值，低于直接返回 unknown
            fallback_mode: 回退模式（"keyword" 或 "bert"）
        """
        self.high_threshold = high_threshold
        self.low_threshold = low_threshold
        self.fast_classifier = IntentClassifier(mode="keyword")
        self.fallback_classifier = IntentClassifier(mode=fallback_mode)

    def predict(self, text: str) -> dict:
        """混合分类"""
        # 第一步：快速分类
        fast_result = self.fast_classifier.predict(text)
        confidence = fast_result["confidence"]

        if confidence >= self.high_threshold:
            # 高置信度，直接返回
            return {"intent": fast_result["intent"], "confidence": confidence, "source": "keyword"}

        if confidence < self.low_threshold:
            # 低置信度，返回 unknown
            return {"intent": "unknown", "confidence": 0.0, "source": "keyword"}

        # 中间置信度，回退到精确分类
        fallback_result = self.fallback_classifier.predict(text)
        return {
            **fallback_result,
            "source": "fallback",
            "fast_score": confidence,
        }
