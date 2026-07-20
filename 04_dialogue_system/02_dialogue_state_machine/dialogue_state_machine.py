"""
dialogue_state_machine.py — 对话状态机的核心模型
定义状态、事件、转换规则，支持完整的状态追踪与校验。
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime


class DialogueState(Enum):
    """对话生命周期中的核心状态"""
    IDLE = "idle"                          # 空闲，等待用户发起
    GREETING = "greeting"                  # 问候阶段
    INTENT_RECOGNITION = "intent_rec"      # 意图识别中
    SLOT_FILLING = "slot_filling"          # 槽位填充中
    CONFIRMATION = "confirmation"          # 等待用户确认
    PROCESSING = "processing"              # 处理用户请求
    COMPLETED = "completed"                # 对话完成
    FALLBACK = "fallback"                  # 兜底/澄清中
    ERROR = "error"                        # 异常状态


class DialogueEvent(Enum):
    """触发状态转换的事件"""
    USER_START = "user_start"              # 用户发起对话
    USER_REPLY = "user_reply"              # 用户回复
    INTENT_FOUND = "intent_found"          # 意图识别成功
    INTENT_UNKNOWN = "intent_unknown"      # 意图未识别
    SLOT_COMPLETE = "slot_complete"        # 所有槽位已填满
    SLOT_MISSING = "slot_missing"          # 仍有槽位缺失
    USER_CONFIRM = "user_confirm"          # 用户确认
    USER_DENY = "user_deny"                # 用户否认
    PROCESS_DONE = "process_done"          # 处理完成
    TIMEOUT = "timeout"                    # 超时
    USER_ESCALATE = "user_escalate"        # 用户要求转人工


@dataclass
class StateTransition:
    """单条状态转换规则"""
    from_state: DialogueState
    event: DialogueEvent
    to_state: DialogueState
    description: str = ""

    def matches(self, current: DialogueState, event: DialogueEvent) -> bool:
        """检查当前状态和事件是否匹配该转换"""
        return self.from_state == current and self.event == event


@dataclass
class StateEntry:
    """状态历史记录中的单条记录"""
    state: DialogueState
    event: DialogueEvent
    timestamp: datetime
    duration_ms: int = 0  # 在该状态停留的时长


@dataclass
class DialogueStateMachine:
    """
    对话状态机：管理对话流程的状态转换与追踪。

    特性：
    - 基于规则的确定性转换（可预测、可调试）
    - 完整的状态历史追踪（用于分析和问题排查）
    - 支持 fallback 和兜底策略
    """

    transitions: list[StateTransition] = field(default_factory=list)
    history: list[StateEntry] = field(default_factory=list)
    current_state: DialogueState = DialogueState.IDLE
    _enter_time: Optional[datetime] = field(default=None, repr=False)

    def __post_init__(self):
        """初始化默认状态转换表"""
        self._build_default_transitions()

    def _build_default_transitions(self):
        """构建默认的对话状态转换规则"""
        defaults = [
            StateTransition(
                DialogueState.IDLE, DialogueEvent.USER_START,
                DialogueState.GREETING, "用户发起对话"
            ),
            StateTransition(
                DialogueState.GREETING, DialogueEvent.USER_REPLY,
                DialogueState.INTENT_RECOGNITION, "收到用户输入，开始识别意图"
            ),
            StateTransition(
                DialogueState.INTENT_RECOGNITION, DialogueEvent.INTENT_FOUND,
                DialogueState.SLOT_FILLING, "意图识别成功，开始填充槽位"
            ),
            StateTransition(
                DialogueState.INTENT_RECOGNITION, DialogueEvent.INTENT_UNKNOWN,
                DialogueState.FALLBACK, "意图未识别，进入澄清流程"
            ),
            StateTransition(
                DialogueState.SLOT_FILLING, DialogueEvent.SLOT_MISSING,
                DialogueState.SLOT_FILLING, "仍有槽位缺失，继续追问"
            ),
            StateTransition(
                DialogueState.SLOT_FILLING, DialogueEvent.SLOT_COMPLETE,
                DialogueState.CONFIRMATION, "所有槽位已满，等待确认"
            ),
            StateTransition(
                DialogueState.CONFIRMATION, DialogueEvent.USER_CONFIRM,
                DialogueState.PROCESSING, "用户确认，开始处理请求"
            ),
            StateTransition(
                DialogueState.CONFIRMATION, DialogueEvent.USER_DENY,
                DialogueState.SLOT_FILLING, "用户否认，返回修改槽位"
            ),
            StateTransition(
                DialogueState.PROCESSING, DialogueEvent.PROCESS_DONE,
                DialogueState.COMPLETED, "处理完成，对话结束"
            ),
            StateTransition(
                DialogueState.FALLBACK, DialogueEvent.USER_REPLY,
                DialogueState.INTENT_RECOGNITION, "用户重新输入，再次识别"
            ),
            StateTransition(
                DialogueState.FALLBACK, DialogueEvent.USER_ESCALATE,
                DialogueState.ERROR, "用户要求转人工"
            ),
            # 全局超时处理：任何状态都可以超时
            StateTransition(
                DialogueState.GREETING, DialogueEvent.TIMEOUT,
                DialogueState.IDLE, "问候阶段超时，回到空闲"
            ),
            StateTransition(
                DialogueState.SLOT_FILLING, DialogueEvent.TIMEOUT,
                DialogueState.IDLE, "槽位填充超时，回到空闲"
            ),
            StateTransition(
                DialogueState.CONFIRMATION, DialogueEvent.TIMEOUT,
                DialogueState.IDLE, "确认阶段超时，回到空闲"
            ),
        ]
        self.transitions.extend(defaults)

    def fire(self, event: DialogueEvent) -> tuple[bool, str]:
        """
        触发一个事件，执行状态转换。

        Returns:
            (success, message): 转换是否成功及描述信息
        """
        for transition in self.transitions:
            if transition.matches(self.current_state, event):
                self._record_transition(event, transition)
                self.current_state = transition.to_state
                self._enter_time = datetime.now()
                return True, transition.description

        # 未找到匹配的转换
        return False, (
            f"无效转换: 当前状态={self.current_state.value}, "
            f"事件={event.value}"
        )

    def _record_transition(self, event: DialogueEvent, transition: StateTransition):
        """记录一次状态转换到历史"""
        now = datetime.now()
        duration = 0
        if self._enter_time:
            delta = now - self._enter_time
            duration = int(delta.total_seconds() * 1000)

        entry = StateEntry(
            state=transition.from_state,
            event=event,
            timestamp=now,
            duration_ms=duration,
        )
        self.history.append(entry)

    def can_fire(self, event: DialogueEvent) -> bool:
        """预测某个事件在当前状态下是否合法（不实际执行）"""
        return any(
            t.matches(self.current_state, event)
            for t in self.transitions
        )

    def valid_events(self) -> list[DialogueEvent]:
        """获取当前状态下所有合法事件"""
        return [
            t.event for t in self.transitions
            if t.from_state == self.current_state
        ]

    def get_history_summary(self) -> list[dict]:
        """返回状态历史的摘要列表"""
        return [
            {
                "from": entry.state.value,
                "event": entry.event.value,
                "duration_ms": entry.duration_ms,
                "time": entry.timestamp.isoformat(),
            }
            for entry in self.history
        ]

    def reset(self):
        """重置状态机到初始状态"""
        self.current_state = DialogueState.IDLE
        self._enter_time = datetime.now()

    def __repr__(self) -> str:
        return (
            f"DialogueStateMachine("
            f"state={self.current_state.value}, "
            f"transitions={len(self.transitions)}, "
            f"history={len(self.history)})"
        )
