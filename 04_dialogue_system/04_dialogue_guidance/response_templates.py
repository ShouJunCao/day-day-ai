"""
response_templates.py — 对话引导话术模板管理
按对话阶段和意图分类组织引导话术，支持 A/B 测试和多语言。
"""
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path
import json
import random


@dataclass
class DialogueTemplate:
    """单条话术模板"""
    template_id: str                     # 模板唯一标识
    stage: str                           # 对话阶段
    intent: str                          # 匹配的意图
    text: str                            # 模板文本
    variants: list[str] = field(default_factory=list)  # A/B 测试变体
    is_active: bool = True               # 是否启用


@dataclass
class TemplateManager:
    """
    话术模板管理器：组织和管理对话各阶段的引导话术。
    支持模板检索、变体随机选择、A/B 测试。
    """

    templates: list[DialogueTemplate] = field(default_factory=list)
    _template_index: dict = field(default_factory=dict)

    def add_template(
        self,
        template_id: str,
        stage: str,
        intent: str,
        text: str,
        variants: Optional[list[str]] = None,
    ):
        """注册一条话术模板"""
        tpl = DialogueTemplate(
            template_id=template_id,
            stage=stage,
            intent=intent,
            text=text,
            variants=variants or [],
        )
        self.templates.append(tpl)
        self._template_index[template_id] = tpl

    def get_template(
        self, stage: str, intent: str, use_variant: bool = True
    ) -> Optional[str]:
        """
        获取指定阶段和意图的话术模板。
        
        Args:
            stage: 对话阶段
            intent: 意图名称
            use_variant: 是否随机选择变体（用于 A/B 测试）
            
        Returns:
            模板文本，或 None
        """
        # 精确匹配
        for tpl in self.templates:
            if (tpl.stage == stage and tpl.intent == intent
                    and tpl.is_active):
                if use_variant and tpl.variants:
                    return random.choice([tpl.text] + tpl.variants)
                return tpl.text

        # 回退：匹配阶段但忽略意图
        for tpl in self.templates:
            if tpl.stage == stage and tpl.is_active:
                return tpl.text

        return None

    def load_from_json(self, path: str | Path):
        """从 JSON 文件批量加载模板"""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        for item in data.get("templates", []):
            self.add_template(
                template_id=item["id"],
                stage=item["stage"],
                intent=item["intent"],
                text=item["text"],
                variants=item.get("variants", []),
            )

    def list_by_stage(self, stage: str) -> list[DialogueTemplate]:
        """列出某个阶段的所有模板"""
        return [t for t in self.templates if t.stage == stage]

    def get_template_ids(self) -> list[str]:
        """返回所有模板 ID"""
        return list(self._template_index.keys())


def create_hotel_templates() -> TemplateManager:
    """创建酒店预订场景的话术模板"""
    mgr = TemplateManager()

    # 问候阶段
    mgr.add_template(
        "greeting_welcome",
        stage="greeting",
        intent="any",
        text="您好！我是酒店预订助手，请问有什么可以帮您？",
        variants=[
            "您好，欢迎使用酒店预订服务！请问需要什么帮助？",
            "您好！我可以帮您预订酒店、查询订单或处理其他问题。",
        ],
    )

    # 意图识别 - 未识别
    mgr.add_template(
        "intent_unknown",
        stage="intent_recognition",
        intent="unknown",
        text=(
            "抱歉，我没有完全理解您的意思。\n"
            "您可以试着更具体地描述您的需求，或者从以下选项中选择：\n"
            "  1. 预订酒店\n"
            "  2. 查询订单\n"
            "  3. 取消预订\n"
            "  4. 价格咨询"
        ),
    )

    # 槽位填充 - 追问城市
    mgr.add_template(
        "slot_ask_city",
        stage="slot_filling",
        intent="book_hotel",
        text="请问您想预订哪个城市的酒店？",
        variants=[
            "好的，目的地是哪里呢？",
            "请问您要去哪个城市？",
        ],
    )

    # 槽位填充 - 追问日期
    mgr.add_template(
        "slot_ask_date",
        stage="slot_filling",
        intent="book_hotel",
        text="请问您的入住日期是？（格式如：2026-08-01）",
        variants=[
            "您计划哪天入住呢？",
            "入住日期是？例如 2026-08-01",
        ],
    )

    # 确认阶段
    mgr.add_template(
        "confirm_summary",
        stage="confirmation",
        intent="book_hotel",
        text=(
            "请确认以下预订信息：\n"
            "📍 城市：{city}\n"
            "📅 入住：{check_in}\n"
            "📅 退房：{check_out}\n"
            "👤 人数：{guests}\n\n"
            "确认请回复「是的」，修改请告诉我需要改的地方。"
        ),
    )

    # 完成阶段
    mgr.add_template(
        "complete_success",
        stage="completed",
        intent="book_hotel",
        text=(
            "✅ 预订成功！\n"
            "您的订单号是 {order_id}。\n"
            "预订详情已发送至您的手机，请注意查收。\n"
            "祝您旅途愉快！"
        ),
    )

    return mgr
