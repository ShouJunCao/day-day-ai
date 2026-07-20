"""
slot_tracker.py — 槽位追踪器
管理对话中的槽位收集、验证和完整性检查。
支持自定义校验器、可选槽位、槽位优先级。
"""
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from datetime import datetime


@dataclass
class Slot:
    """单个槽位的定义"""
    name: str                          # 槽位名称
    description: str                   # 槽位说明（用于向用户提问）
    value: Any = None                  # 当前值
    required: bool = True              # 是否必填
    validator: Optional[Callable] = None  # 校验函数
    prompt_template: str = "请问{desc}？"  # 追问模板

    @property
    def is_filled(self) -> bool:
        """判断槽位是否已填充"""
        return self.value is not None

    def validate(self, value: Any) -> tuple[bool, str]:
        """
        校验输入值是否合法。

        Returns:
            (is_valid, error_message)
        """
        if self.validator:
            try:
                result = self.validator(value)
                if isinstance(result, tuple):
                    return result
                return (bool(result), "")
            except Exception as e:
                return (False, f"校验失败: {e}")
        return (True, "")

    def fill(self, value: Any) -> tuple[bool, str]:
        """尝试填充槽位值"""
        is_valid, error = self.validate(value)
        if is_valid:
            self.value = value
            return (True, f"槽位 '{self.name}' 已填充")
        return (False, error)

    def prompt(self) -> str:
        """生成向用户追问的文本"""
        return self.prompt_template.format(desc=self.description)


@dataclass
class SlotTracker:
    """
    槽位追踪器：管理一组槽位的收集和验证。

    用法：
        tracker = SlotTracker(slots=[...])
        tracker.fill_slot("city", "北京")
        tracker.get_missing_slots()  # 返回未填充的槽位
    """

    slots: list[Slot] = field(default_factory=list)
    filled_order: list[str] = field(default_factory=list)

    def fill_slot(self, name: str, value: Any) -> tuple[bool, str]:
        """
        填充指定槽位。

        Returns:
            (success, message)
        """
        for slot in self.slots:
            if slot.name == name:
                ok, msg = slot.fill(value)
                if ok:
                    self.filled_order.append(name)
                return (ok, msg)
        return (False, f"槽位 '{name}' 不存在")

    def get_missing_slots(self) -> list[Slot]:
        """获取所有未填充的必填槽位"""
        return [s for s in self.slots if s.required and not s.is_filled]

    def get_next_missing_slot(self) -> Optional[Slot]:
        """获取下一个需要追问的槽位"""
        missing = self.get_missing_slots()
        return missing[0] if missing else None

    def is_complete(self) -> bool:
        """检查所有必填槽位是否已填满"""
        return len(self.get_missing_slots()) == 0

    def get_filled_slots(self) -> list[Slot]:
        """获取所有已填充的槽位"""
        return [s for s in self.slots if s.is_filled]

    def get_summary(self) -> dict:
        """返回槽位收集摘要"""
        total = len(self.slots)
        filled = len([s for s in self.slots if s.is_filled])
        missing = len(self.get_missing_slots())
        return {
            "total": total,
            "filled": filled,
            "missing": missing,
            "complete": missing == 0,
            "filled_order": list(self.filled_order),
            "values": {s.name: s.value for s in self.slots if s.is_filled},
        }

    def reset(self):
        """重置所有槽位"""
        for slot in self.slots:
            slot.value = None
        self.filled_order.clear()


def create_booking_slots() -> SlotTracker:
    """
    创建酒店预订场景的槽位配置。
    这是一个工厂函数，返回预配置的 SlotTracker。
    """

    def validate_date(value: str) -> tuple[bool, str]:
        """校验日期格式 YYYY-MM-DD"""
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return (True, "")
        except ValueError:
            return (False, "日期格式应为 YYYY-MM-DD，例如 2026-07-20")

    def validate_positive_int(value: Any) -> tuple[bool, str]:
        """校验正整数"""
        try:
            n = int(value)
            if n <= 0:
                return (False, "请输入大于 0 的整数")
            return (True, "")
        except (ValueError, TypeError):
            return (False, "请输入有效的整数")

    return SlotTracker(
        slots=[
            Slot(
                name="city",
                description="您要预订哪个城市",
                prompt_template="请问您想预订哪个城市？",
            ),
            Slot(
                name="check_in",
                description="入住日期",
                validator=validate_date,
                prompt_template="请问您的入住日期是？（格式：YYYY-MM-DD）",
            ),
            Slot(
                name="check_out",
                description="退房日期",
                validator=validate_date,
                prompt_template="请问您的退房日期是？（格式：YYYY-MM-DD）",
            ),
            Slot(
                name="guests",
                description="入住人数",
                validator=validate_positive_int,
                required=False,
                prompt_template="请问入住人数是？（默认为 1 人）",
            ),
        ]
    )
