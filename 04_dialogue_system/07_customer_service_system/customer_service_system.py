"""
customer_service_system.py — 多轮对话智能客服系统
整合状态机、意图识别、槽位填充、澄清引擎、兜底策略、
质量评估，构建完整的端到端对话系统。
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from enum import Enum


# ===== 状态定义 =====

class DialogueState(Enum):
    IDLE = "idle"
    GREETING = "greeting"
    INTENT_RECOGNITION = "intent_rec"
    SLOT_FILLING = "slot_filling"
    CONFIRMATION = "confirmation"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FALLBACK = "fallback"
    ERROR = "error"


class DialogueEvent(Enum):
    USER_START = "user_start"
    USER_REPLY = "user_reply"
    INTENT_FOUND = "intent_found"
    INTENT_UNKNOWN = "intent_unknown"
    SLOT_COMPLETE = "slot_complete"
    SLOT_MISSING = "slot_missing"
    USER_CONFIRM = "user_confirm"
    USER_DENY = "user_deny"
    PROCESS_DONE = "process_done"
    TIMEOUT = "timeout"
    USER_ESCALATE = "user_escalate"


@dataclass
class StateTransition:
    from_state: DialogueState
    event: DialogueEvent
    to_state: DialogueState
    description: str = ""

    def matches(self, current: DialogueState, event: DialogueEvent) -> bool:
        return self.from_state == current and self.event == event


# ===== 槽位定义 =====

@dataclass
class Slot:
    name: str
    description: str
    value: Optional[str] = None
    required: bool = True

    @property
    def is_filled(self) -> bool:
        return self.value is not None

    def fill(self, value: str) -> bool:
        self.value = value
        return True


# ===== 意图定义 =====

@dataclass
class IntentDefinition:
    name: str
    keywords: list[str] = field(default_factory=list)
    response: str = ""
    required_slots: list[str] = field(default_factory=list)


# ===== 对话轮次记录 =====

@dataclass
class TurnRecord:
    turn_number: int
    user_input: str
    system_response: str
    state_before: str
    state_after: str
    timestamp: datetime


# ===== 智能客服系统 =====

@dataclass
class CustomerServiceSystem:
    """
    多轮对话智能客服系统。

    整合以下组件：
    - 对话状态机（流程控制）
    - 意图路由器（语义理解）
    - 槽位追踪器（信息收集）
    - 澄清引擎（模糊处理）
    - 兜底处理器（降级策略）
    - 话术模板（回复生成）
    - 质量指标（性能评估）
    """

    # 状态机
    transitions: list[StateTransition] = field(default_factory=list)
    current_state: DialogueState = DialogueState.IDLE

    # 意图
    intents: dict[str, IntentDefinition] = field(default_factory=dict)

    # 槽位
    active_slots: dict[str, Slot] = field(default_factory=dict)

    # 对话历史
    history: list[TurnRecord] = field(default_factory=list)
    _turn_count: int = 0

    # 兜底
    fallback_count: int = 0
    escalation_count: int = 0

    # 质量指标
    _session_completed: bool = False
    _start_time: Optional[datetime] = None

    def __post_init__(self):
        self._build_transitions()
        self._build_intents()

    def _build_transitions(self):
        """构建状态转换表"""
        defaults = [
            StateTransition(
                DialogueState.IDLE, DialogueEvent.USER_START,
                DialogueState.GREETING, "用户发起对话"
            ),
            StateTransition(
                DialogueState.GREETING, DialogueEvent.USER_REPLY,
                DialogueState.INTENT_RECOGNITION, "收到用户输入，识别意图"
            ),
            StateTransition(
                DialogueState.INTENT_RECOGNITION, DialogueEvent.INTENT_FOUND,
                DialogueState.SLOT_FILLING, "意图识别成功，开始填槽"
            ),
            StateTransition(
                DialogueState.INTENT_RECOGNITION, DialogueEvent.INTENT_UNKNOWN,
                DialogueState.FALLBACK, "意图未识别，进入兜底"
            ),
            StateTransition(
                DialogueState.SLOT_FILLING, DialogueEvent.SLOT_MISSING,
                DialogueState.SLOT_FILLING, "继续追问"
            ),
            StateTransition(
                DialogueState.SLOT_FILLING, DialogueEvent.SLOT_COMPLETE,
                DialogueState.CONFIRMATION, "槽位齐了，等确认"
            ),
            StateTransition(
                DialogueState.CONFIRMATION, DialogueEvent.USER_CONFIRM,
                DialogueState.PROCESSING, "用户确认，开始处理"
            ),
            StateTransition(
                DialogueState.CONFIRMATION, DialogueEvent.USER_DENY,
                DialogueState.SLOT_FILLING, "用户否认，返回修改"
            ),
            StateTransition(
                DialogueState.PROCESSING, DialogueEvent.PROCESS_DONE,
                DialogueState.COMPLETED, "处理完成"
            ),
            StateTransition(
                DialogueState.FALLBACK, DialogueEvent.USER_REPLY,
                DialogueState.INTENT_RECOGNITION, "用户重新输入"
            ),
            StateTransition(
                DialogueState.FALLBACK, DialogueEvent.USER_ESCALATE,
                DialogueState.ERROR, "用户要求转人工"
            ),
            StateTransition(
                DialogueState.INTENT_RECOGNITION, DialogueEvent.USER_ESCALATE,
                DialogueState.ERROR, "识别阶段用户要求转人工"
            ),
        ]
        self.transitions.extend(defaults)

    def _build_intents(self):
        """构建意图库"""
        self.intents = {
            "book_hotel": IntentDefinition(
                name="book_hotel",
                keywords=["预订", "订房", "酒店", "住宿", "booking"],
                response="好的，我来帮您预订酒店。",
                required_slots=["city", "check_in", "check_out"],
            ),
            "check_order": IntentDefinition(
                name="check_order",
                keywords=["查询", "订单", "我的预订", "查看"],
                response="我来帮您查询订单。",
                required_slots=["order_id"],
            ),
            "cancel_booking": IntentDefinition(
                name="cancel_booking",
                keywords=["取消", "退订", "退款"],
                response="好的，我来帮您处理取消。",
                required_slots=["order_id"],
            ),
            "greeting": IntentDefinition(
                name="greeting",
                keywords=["你好", "您好", "hi", "hello"],
                response="您好！有什么可以帮您的？",
                required_slots=[],
            ),
            "price_inquiry": IntentDefinition(
                name="price_inquiry",
                keywords=["多少钱", "价格", "费用", "收费"],
                response="让我为您查询价格信息。",
                required_slots=["city"],
            ),
        }

    def classify_intent(self, text: str) -> Optional[IntentDefinition]:
        """基于关键词匹配识别意图"""
        text_lower = text.lower()
        best_match = None
        best_score = 0

        for intent in self.intents.values():
            score = sum(1 for kw in intent.keywords if kw in text_lower)
            if score > best_score:
                best_score = score
                best_match = intent

        return best_match if best_score > 0 else None

    def initialize_slots(self, intent: IntentDefinition):
        """根据意图初始化槽位"""
        self.active_slots.clear()
        slot_defs = {
            "city": Slot(name="city", description="城市"),
            "check_in": Slot(name="check_in", description="入住日期"),
            "check_out": Slot(name="check_out", description="退房日期"),
            "order_id": Slot(name="order_id", description="订单号"),
        }
        for slot_name in intent.required_slots:
            if slot_name in slot_defs:
                self.active_slots[slot_name] = slot_defs[slot_name]

    def try_fill_slots(self, text: str) -> list[str]:
        """
        尝试从用户输入中提取槽位值。
        返回成功填充的槽位名称列表。
        """
        import re

        filled = []
        # 收集所有日期候选
        date_matches = re.findall(r"\d{4}-\d{2}-\d{2}", text)
        order_match = re.search(r"#[A-Z0-9]+", text)

        # 记录 fill 前 check_in 的状态（避免在同一轮中 check_out 复用 check_in 的值）
        check_in_was_filled = False
        check_in_slot = self.active_slots.get("check_in")
        if check_in_slot and check_in_slot.is_filled:
            check_in_was_filled = True

        for name, slot in self.active_slots.items():
            if name == "city":
                cities = ["北京", "上海", "广州", "深圳", "杭州", "成都"]
                for city in cities:
                    if city in text:
                        slot.fill(city)
                        filled.append(name)
                        break
            elif name == "check_in":
                if date_matches:
                    slot.fill(date_matches[0])
                    filled.append(name)
            elif name == "check_out":
                # check_out 只在以下情况填入：
                # 1) 有 2 个以上日期，取第二个
                # 2) 有 1 个日期且 check_in 在调用前就已填充
                if len(date_matches) >= 2:
                    slot.fill(date_matches[1])
                    filled.append(name)
                elif len(date_matches) == 1 and check_in_was_filled:
                    slot.fill(date_matches[0])
                    filled.append(name)
            elif name == "order_id":
                if order_match:
                    slot.fill(order_match.group())
                    filled.append(name)

        return filled

    def get_missing_slots(self) -> list[Slot]:
        """获取未填充的槽位"""
        return [s for s in self.active_slots.values() if not s.is_filled]

    def all_slots_filled(self) -> bool:
        """检查所有槽位是否已填满"""
        return not self.get_missing_slots()

    def handle_input(self, user_input: str) -> str:
        """
        处理用户输入，返回系统回复。
        这是对话系统的核心入口。
        """
        if self._start_time is None:
            self._start_time = datetime.now()

        state_before = self.current_state.value
        response = ""

        # 根据当前状态选择处理策略
        if self.current_state == DialogueState.IDLE:
            self.current_state = DialogueState.GREETING
            response = (
                "您好！我是酒店预订助手，可以帮您：\n"
                "🔹 预订酒店  🔹 查询订单\n"
                "🔹 取消预订  🔹 价格咨询\n\n"
                "请告诉我您的需求。"
            )

        elif self.current_state == DialogueState.GREETING:
            # 意图识别
            intent = self.classify_intent(user_input)
            if intent:
                self.current_state = DialogueState.INTENT_RECOGNITION
                self._fire_event(DialogueEvent.INTENT_FOUND)
                response = intent.response
                if intent.required_slots:
                    self.initialize_slots(intent)
                    self.current_state = DialogueState.SLOT_FILLING
                    missing = self.get_missing_slots()
                    if missing:
                        response += f"\n请问{missing[0].description}是？"
                    else:
                        self.current_state = DialogueState.CONFIRMATION
                        response = self._build_confirmation()
            else:
                self._fire_event(DialogueEvent.INTENT_UNKNOWN)
                self.current_state = DialogueState.FALLBACK
                self.fallback_count += 1
                response = (
                    "抱歉，我没有完全理解您的意思。\n"
                    "您可以试着更具体地描述需求，或者选择：\n"
                    "1. 预订酒店  2. 查询订单\n"
                    "3. 取消预订  4. 价格咨询"
                )

        elif self.current_state == DialogueState.INTENT_RECOGNITION:
            # 从兜底回来后的重新识别
            intent = self.classify_intent(user_input)
            if intent:
                self._fire_event(DialogueEvent.INTENT_FOUND)
                response = intent.response
                if intent.required_slots:
                    self.initialize_slots(intent)
                    self.current_state = DialogueState.SLOT_FILLING
                    missing = self.get_missing_slots()
                    if missing:
                        response += f"\n请问{missing[0].description}是？"
                else:
                    self.current_state = DialogueState.CONFIRMATION
                    response = self._build_confirmation()
            elif any(kw in user_input for kw in ["转人工", "人工"]):
                self.escalation_count += 1
                self._fire_event(DialogueEvent.USER_ESCALATE)
                self.current_state = DialogueState.ERROR
                response = "正在为您转接人工客服，请稍候..."
            else:
                self._fire_event(DialogueEvent.INTENT_UNKNOWN)
                self.current_state = DialogueState.FALLBACK
                self.fallback_count += 1
                if self.fallback_count >= 3:
                    self.escalation_count += 1
                    response = (
                        "这个问题超出了我的处理能力。\n"
                        "正在为您转接人工客服，请稍候..."
                    )
                    self.current_state = DialogueState.ERROR
                else:
                    response = (
                        "抱歉，我还没有理解您的需求。\n"
                        "您可以换一种方式描述，或者从以下选项中选择：\n"
                        "1. 预订酒店  2. 查询订单\n"
                        "3. 取消预订  4. 价格咨询"
                    )

        elif self.current_state == DialogueState.SLOT_FILLING:
            # 槽位填充
            filled = self.try_fill_slots(user_input)
            if filled:
                if self.all_slots_filled():
                    self._fire_event(DialogueEvent.SLOT_COMPLETE)
                    self.current_state = DialogueState.CONFIRMATION
                    response = self._build_confirmation()
                else:
                    self._fire_event(DialogueEvent.SLOT_MISSING)
                    missing = self.get_missing_slots()
                    if missing:
                        response = f"好的，请问{missing[0].description}是？"
            elif any(kw in user_input for kw in ["是的", "确认"]):
                # 用户在槽位填充阶段说确认，视为确认
                self._fire_event(DialogueEvent.SLOT_COMPLETE)
                self.current_state = DialogueState.CONFIRMATION
                response = self._build_confirmation()
            elif any(kw in user_input for kw in ["改", "修改"]):
                # 用户要修改，尝试提取新信息
                new_filled = self.try_fill_slots(user_input)
                if new_filled:
                    response = f"已更新：{', '.join(new_filled)}。"
                    if self.all_slots_filled():
                        response += "\n请确认以上信息，回复「是的」即可。"
                    else:
                        missing = self.get_missing_slots()
                        if missing:
                            response += f"\n请问{missing[0].description}是？"
                else:
                    missing = self.get_missing_slots()
                    if missing:
                        response = f"好的，请告诉我修改后的{missing[0].description}。"
            else:
                response = "抱歉，我没有识别到有效信息。"
                self.fallback_count += 1
                if self.fallback_count >= 3:
                    self.escalation_count += 1
                    response = "这个问题超出了我的处理能力，正在为您转接人工客服..."
                    self.current_state = DialogueState.ERROR
                else:
                    missing = self.get_missing_slots()
                    if missing:
                        response += f"\n请问{missing[0].description}是？"

        elif self.current_state == DialogueState.CONFIRMATION:
            # 确认阶段
            if any(kw in user_input for kw in ["不对", "不对,", "不对，"]):
                # 用户否认，返回修改
                self._fire_event(DialogueEvent.USER_DENY)
                self.current_state = DialogueState.SLOT_FILLING
                # 提供可修改的槽位列表
                slot_names = [s.description for s in self.active_slots.values() if s.is_filled]
                if slot_names:
                    response = f"好的，请告诉我需要修改哪个信息：{'、'.join(slot_names)}"
                else:
                    response = "好的，请告诉我需要修改什么。"
            elif any(kw in user_input for kw in ["是的", "确认", "对", "没问题", "就这样"]):
                self._fire_event(DialogueEvent.USER_CONFIRM)
                self.current_state = DialogueState.PROCESSING
                response = "正在为您处理，请稍候..."
                self._fire_event(DialogueEvent.PROCESS_DONE)
                self.current_state = DialogueState.COMPLETED
                self._session_completed = True
                response += self._build_completion()
            elif any(kw in user_input for kw in ["修改", "改"]):
                # 用户要修改
                self._fire_event(DialogueEvent.USER_DENY)
                self.current_state = DialogueState.SLOT_FILLING
                slot_names = [s.description for s in self.active_slots.values() if s.is_filled]
                if slot_names:
                    response = f"好的，请告诉我需要修改哪个信息：{'、'.join(slot_names)}"
                else:
                    response = "好的，请告诉我需要修改什么。"
                # 尝试直接填充新信息
                filled = self.try_fill_slots(user_input)
                if filled:
                    response = f"已更新：{', '.join(filled)}。"
                    if self.all_slots_filled():
                        response += "\n请确认以上信息，回复「是的」即可。"
                    else:
                        missing = self.get_missing_slots()
                        if missing:
                            response += f"\n请问{missing[0].description}是？"
            else:
                response = "请回复「是的」确认，或「修改」进行调整。"

        elif self.current_state == DialogueState.COMPLETED:
            response = (
                "您的请求已处理完成！\n"
                "还有其他需要帮助的吗？回复「重新开始」即可。"
            )

        elif self.current_state == DialogueState.FALLBACK:
            # Fallback 状态下的用户输入处理
            if "转人工" in user_input or "人工" in user_input:
                self.escalation_count += 1
                self._fire_event(DialogueEvent.USER_ESCALATE)
                self.current_state = DialogueState.ERROR
                response = "正在为您转接人工客服，请稍候..."
            else:
                # 再次尝试重新识别意图
                intent = self.classify_intent(user_input)
                if intent:
                    self._fire_event(DialogueEvent.USER_REPLY)
                    self.current_state = DialogueState.INTENT_RECOGNITION
                    return self.handle_input(user_input)  # 重新走一遍
                else:
                    self.fallback_count += 1
                    if self.fallback_count >= 3:
                        self.escalation_count += 1
                        response = (
                            "这个问题超出了我的处理能力。\n"
                            "正在为您转接人工客服，请稍候..."
                        )
                        self._fire_event(DialogueEvent.USER_ESCALATE)
                        self.current_state = DialogueState.ERROR
                    else:
                        response = (
                            "抱歉，我还没有理解您的需求。\n"
                            "您可以换一种方式描述，或者从以下选项中选择：\n"
                            "1. 预订酒店  2. 查询订单\n"
                            "3. 取消预订  4. 价格咨询"
                        )
                        self._fire_event(DialogueEvent.USER_REPLY)

        # 记录轮次
        self._turn_count += 1
        state_after = self.current_state.value
        self.history.append(TurnRecord(
            turn_number=self._turn_count,
            user_input=user_input,
            system_response=response,
            state_before=state_before,
            state_after=state_after,
            timestamp=datetime.now(),
        ))

        return response

    def _fire_event(self, event: DialogueEvent):
        """执行状态转换"""
        for t in self.transitions:
            if t.matches(self.current_state, event):
                self.current_state = t.to_state
                return

    def _build_confirmation(self) -> str:
        """构建确认信息"""
        lines = ["请确认以下信息："]
        for slot in self.active_slots.values():
            if slot.is_filled:
                lines.append(f"  • {slot.description}：{slot.value}")
            else:
                lines.append(f"  • {slot.description}：（待提供）")
        lines.append("\n确认请回复「是的」，修改请告诉我需要改的地方。")
        return "\n".join(lines)

    def _build_completion(self) -> str:
        """构建完成信息"""
        import random
        order_id = f"#HTL{random.randint(100000, 999999)}"
        return f"\n✅ 预订成功！\n订单号：{order_id}\n预订详情已发送，请查收。"

    def reset(self):
        """重置对话"""
        self.current_state = DialogueState.IDLE
        self.active_slots.clear()
        self.fallback_count = 0
        self._session_completed = False
        self._start_time = None

    def get_session_report(self) -> dict:
        """获取当前会话的质量报告"""
        return {
            "total_turns": self._turn_count,
            "completed": self._session_completed,
            "fallback_count": self.fallback_count,
            "escalation_count": self.escalation_count,
            "final_state": self.current_state.value,
            "slots_filled": {
                k: v.value for k, v in self.active_slots.items() if v.is_filled
            },
        }

    def get_conversation_log(self) -> list[dict]:
        """返回对话记录"""
        return [
            {
                "turn": r.turn_number,
                "user": r.user_input,
                "system": r.system_response,
                "state": f"{r.state_before} → {r.state_after}",
            }
            for r in self.history
        ]
