"""
clarification_engine.py — 澄清引擎
当用户输入模糊、意图不明或信息不足时，生成合适的澄清问题。
支持多级澄清策略：上下文复用、选项引导、开放式追问。
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import re


class ClarificationType(Enum):
    """澄清问题的类型"""
    DISAMBIGUATION = "disambiguation"    # 消除歧义
    SLOT_REQUEST = "slot_request"        # 请求缺失槽位
    CONFIRMATION = "confirmation"        # 确认理解
    SCOPE_NARROW = "scope_narrow"        # 缩小范围
    OPEN_PROBE = "open_probe"            # 开放式追问


@dataclass
class ClarificationRule:
    """单条澄清规则"""
    trigger_pattern: str               # 触发条件（正则或关键词）
    clarification_type: ClarificationType
    templates: list[str]               # 澄清话术模板
    options: list[str] = field(default_factory=list)  # 可选选项
    priority: int = 5                  # 优先级（1最高，10最低）

    def matches(self, text: str, context: dict) -> bool:
        """检查是否触发此规则"""
        if self.trigger_pattern in text.lower():
            return True
        try:
            if re.search(self.trigger_pattern, text, re.IGNORECASE):
                return True
        except re.error:
            pass
        return False


@dataclass
class ClarificationEngine:
    """
    澄清引擎：根据对话上下文和用户输入，
    生成最合适的澄清问题或引导话术。
    """

    rules: list[ClarificationRule] = field(default_factory=list)
    max_options: int = 4  # 最多提供几个选项
    fallback_template: str = (
        "抱歉，我没有完全理解您的意思。\n"
        "您可以试着说得更具体一些，或者从以下选项中选择："
    )

    def __post_init__(self):
        """初始化默认澄清规则"""
        self._build_default_rules()

    def _build_default_rules(self):
        """构建默认的澄清规则集"""
        defaults = [
            # 模糊意图
            ClarificationRule(
                trigger_pattern=r"^(就行|随便|都行|不知道|不清楚|看看)$",
                clarification_type=ClarificationType.OPEN_PROBE,
                templates=[
                    "好的，那我简单介绍一下我能帮您的事情：\n"
                    "{options_text}\n"
                    "您有具体想了解的吗？",
                ],
                priority=1,
            ),
            # 歧义：多个可能的意图
            ClarificationRule(
                trigger_pattern="multi_intent",
                clarification_type=ClarificationType.DISAMBIGUATION,
                templates=[
                    "我注意到您可能有两个需求，请问您是想：\n"
                    "{options_text}",
                ],
                priority=2,
            ),
            # 缺少关键信息
            ClarificationRule(
                trigger_pattern="missing_slot",
                clarification_type=ClarificationType.SLOT_REQUEST,
                templates=[
                    "好的，请问您能告诉我{slot_name}吗？"
                ],
                priority=3,
            ),
            # 范围太广
            ClarificationRule(
                trigger_pattern=r"(所有|全部|一切|各种|所有类型)",
                clarification_type=ClarificationType.SCOPE_NARROW,
                templates=[
                    "这个话题范围比较广，我们可以先聚焦某一方面。\n"
                    "您更关心哪个方向？\n"
                    "{options_text}",
                ],
                priority=4,
            ),
        ]
        self.rules.extend(defaults)

    def generate(
        self,
        user_input: str,
        context: Optional[dict] = None,
        intent_candidates: Optional[list[dict]] = None,
        missing_slots: Optional[list[str]] = None,
    ) -> dict:
        """
        生成澄清问题。

        Args:
            user_input: 用户输入文本
            context: 对话上下文
            intent_candidates: 多个候选意图（用于歧义消除）
            missing_slots: 缺失的槽位列表

        Returns:
            {"clarification": str, "type": str, "options": list}
        """
        context = context or {}

        # 策略 1：多意图歧义消除
        if intent_candidates and len(intent_candidates) > 1:
            return self._disambiguate(intent_candidates)

        # 策略 2：缺失槽位追问
        if missing_slots:
            return self._request_slot(missing_slots[0], context)

        # 策略 3：匹配澄清规则
        matched = self._match_rules(user_input, context)
        if matched:
            return self._format_clarification(matched, context)

        # 策略 4：默认兜底
        return self._fallback(context)

    def _disambiguate(self, candidates: list[dict]) -> dict:
        """消除多个候选意图之间的歧义"""
        options = [
            f"{c.get('name', '?')}" for c in candidates[:self.max_options]
        ]
        options_text = "\n".join(
            f"  {i+1}. {opt}" for i, opt in enumerate(options)
        )
        templates = [r.templates for r in self.rules
                     if r.clarification_type == ClarificationType.DISAMBIGUATION]
        template = templates[0][0] if templates else self.fallback_template
        text = template.format(options_text=options_text)
        return {
            "clarification": text,
            "type": ClarificationType.DISAMBIGUATION.value,
            "options": options,
        }

    def _request_slot(self, slot_name: str, context: dict) -> dict:
        """生成缺失槽位的追问"""
        templates = [r.templates for r in self.rules
                     if r.clarification_type == ClarificationType.SLOT_REQUEST]
        template = templates[0][0] if templates else "请问您能提供{slot_name}吗？"
        text = template.format(slot_name=slot_name)
        return {
            "clarification": text,
            "type": ClarificationType.SLOT_REQUEST.value,
            "options": [],
        }

    def _match_rules(self, text: str, context: dict) -> Optional[ClarificationRule]:
        """匹配澄清规则，返回优先级最高的"""
        matched = [r for r in self.rules if r.matches(text, context)]
        if not matched:
            return None
        return min(matched, key=lambda r: r.priority)

    def _format_clarification(
        self, rule: ClarificationRule, context: dict
    ) -> dict:
        """格式化澄清输出"""
        options = rule.options[:self.max_options]
        options_text = "\n".join(
            f"  {i+1}. {opt}" for i, opt in enumerate(options)
        )
        template = rule.templates[0]
        try:
            text = template.format(
                options_text=options_text,
                **context,
            )
        except KeyError:
            text = template.replace("{options_text}", options_text)

        return {
            "clarification": text,
            "type": rule.clarification_type.value,
            "options": options,
        }

    def _fallback(self, context: dict) -> dict:
        """默认兜底话术"""
        text = self.fallback_template
        return {
            "clarification": text,
            "type": ClarificationType.OPEN_PROBE.value,
            "options": [],
        }
