"""
使用示例: 演示对话状态机完整流程，包括意图识别、槽位填充、
状态转换追踪和完整对话循环。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dialogue_state_machine import (
    DialogueStateMachine, DialogueState, DialogueEvent,
)
from slot_tracker import SlotTracker, Slot, create_booking_slots
from intent_router import IntentRouter, create_hotel_intent_router


def demo_state_transitions():
    """演示状态机的基本状态转换"""
    print("=" * 60)
    print("  对话状态机 — 状态转换演示")
    print("=" * 60)

    sm = DialogueStateMachine()
    print(f"初始状态: {sm.current_state.value}\n")

    # 模拟一个完整的对话流程
    steps = [
        (DialogueEvent.USER_START, "用户发起对话"),
        (DialogueEvent.USER_REPLY, "用户说：我想订酒店"),
        (DialogueEvent.INTENT_FOUND, "识别到意图：book_hotel"),
        (DialogueEvent.SLOT_MISSING, "追问：请问哪个城市？"),
        (DialogueEvent.SLOT_MISSING, "追问：入住日期是？"),
        (DialogueEvent.SLOT_COMPLETE, "用户提供了所有信息"),
        (DialogueEvent.USER_CONFIRM, "用户确认：对，就这样"),
        (DialogueEvent.PROCESS_DONE, "预订处理完成"),
    ]

    for event, desc in steps:
        ok, msg = sm.fire(event)
        status = "✅" if ok else "❌"
        print(f"  {status} {desc}")
        print(f"     状态: {sm.current_state.value} | {msg}\n")

    # 打印历史记录
    print("状态转换历史:")
    for entry in sm.get_history_summary():
        print(f"  {entry['from']} --[{entry['event']}]--> "
              f"(耗时 {entry['duration_ms']}ms)")


def demo_slot_filling():
    """演示槽位追踪器"""
    print("\n" + "=" * 60)
    print("  槽位追踪器 — Slot Filling 演示")
    print("=" * 60)

    tracker = create_booking_slots()
    print(f"初始状态: {tracker.get_summary()}\n")

    # 模拟用户逐步提供信息
    fills = [
        ("city", "北京"),
        ("check_in", "2026-08-01"),
        ("check_out", "2026-08-05"),
        ("guests", "2"),
    ]

    for name, value in fills:
        ok, msg = tracker.fill_slot(name, value)
        status = "✅" if ok else "❌"
        summary = tracker.get_summary()
        print(f"  {status} 填充 {name}={value}: {msg}")
        print(f"     进度: {summary['filled']}/{summary['total']} "
              f"({summary['missing']} 个缺失)\n")

    print(f"最终槽位值: {tracker.get_summary()['values']}")
    print(f"填充顺序: {tracker.filled_order}")

    # 演示校验失败
    print("\n校验失败测试:")
    ok, msg = tracker.fill_slot("check_in", "invalid-date")
    print(f"  {'✅' if ok else '❌'} check_in='invalid-date': {msg}")

    ok, msg = tracker.fill_slot("guests", "-1")
    print(f"  {'✅' if ok else '❌'} guests=-1: {msg}")


def demo_intent_classification():
    """演示意图分类器"""
    print("\n" + "=" * 60)
    print("  意图路由器 — Intent Classification 演示")
    print("=" * 60)

    router = create_hotel_intent_router()

    test_inputs = [
        "你好，我想预订酒店",
        "北京有什么推荐的酒店？",
        "多少钱一晚？",
        "我要取消预订",
        "帮我转人工客服",
        "今天的天气怎么样",  # 未知意图
    ]

    for text in test_inputs:
        result = router.classify(text)
        icon = "✅" if not result["is_default"] else "❓"
        print(f"  {icon} 输入: {text}")
        print(f"     意图: {result['intent']} "
              f"(置信度: {result['confidence']})")
        if result["matched_keywords"]:
            print(f"     匹配关键词: {', '.join(result['matched_keywords'])}")
        print()


def demo_full_dialogue_flow():
    """演示完整的多轮对话流程"""
    print("=" * 60)
    print("  完整对话流程 — 状态机 + 意图 + 槽位 集成演示")
    print("=" * 60)

    sm = DialogueStateMachine()
    tracker = create_booking_slots()
    router = create_hotel_intent_router()

    # 模拟对话轮次
    dialogue_turns = [
        {"user": "你好", "fill": []},
        {"user": "我想预订酒店", "fill": []},
        {"user": "北京", "fill": [("city", "北京")]},
        {"user": "2026-08-01", "fill": [("check_in", "2026-08-01")]},
        {"user": "2026-08-05", "fill": [("check_out", "2026-08-05")]},
        {"user": "是的，确认", "fill": []},
    ]

    # Step 1: 用户发起对话
    ok, msg = sm.fire(DialogueEvent.USER_START)
    print(f"  [轮次 0] 用户发起: {sm.current_state.value}")

    for i, turn in enumerate(dialogue_turns, 1):
        user_input = turn["user"]
        print(f"\n  [轮次 {i}] 用户: {user_input}")

        # 意图识别
        if sm.current_state == DialogueState.GREETING:
            sm.fire(DialogueEvent.USER_REPLY)
            intent_result = router.classify(user_input)
            print(f"    意图: {intent_result['intent']} "
                  f"(置信度: {intent_result['confidence']})")

            if not intent_result["is_default"]:
                sm.fire(DialogueEvent.INTENT_FOUND)
            else:
                sm.fire(DialogueEvent.INTENT_UNKNOWN)

        # 槽位填充
        if sm.current_state == DialogueState.SLOT_FILLING:
            for name, value in turn["fill"]:
                ok, msg = tracker.fill_slot(name, value)
                print(f"    槽位: {name}={value} ({'✅' if ok else '❌'})")

            if tracker.is_complete():
                sm.fire(DialogueEvent.SLOT_COMPLETE)
                print(f"    所有槽位已填满!")
            else:
                missing = tracker.get_next_missing_slot()
                if missing:
                    print(f"    追问: {missing.prompt()}")

        # 确认阶段
        if sm.current_state == DialogueState.CONFIRMATION:
            if "确认" in user_input or "是的" in user_input:
                sm.fire(DialogueEvent.USER_CONFIRM)
                print(f"    用户确认，开始处理...")
                sm.fire(DialogueEvent.PROCESS_DONE)
                print(f"    ✅ 处理完成!")

        print(f"    当前状态: {sm.current_state.value}")

    # 打印完整历史
    print("\n  完整状态转换历史:")
    print("  " + "-" * 50)
    for entry in sm.get_history_summary():
        print(f"  {entry['from']:<18s} --[{entry['event']:<20s}]--> "
              f"(耗时 {entry['duration_ms']}ms)")
    print("  " + "-" * 50)

    final_summary = tracker.get_summary()
    print(f"\n  槽位最终状态:")
    print(f"    完成: {final_summary['complete']}")
    print(f"    已填充: {final_summary['values']}")
    print(f"    填充顺序: {final_summary['filled_order']}")


if __name__ == "__main__":
    demo_state_transitions()
    demo_slot_filling()
    demo_intent_classification()
    demo_full_dialogue_flow()
