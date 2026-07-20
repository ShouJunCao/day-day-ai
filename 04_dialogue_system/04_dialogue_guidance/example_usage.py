"""
使用示例: 演示澄清引擎、兜底策略和话术模板的完整流程。
展示从用户模糊输入到系统引导、追问、最终完成任务的全过程。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from clarification_engine import ClarificationEngine
from fallback_handler import FallbackHandler
from response_templates import create_hotel_templates


def demo_clarification_engine():
    """演示澄清引擎在不同场景下的输出"""
    print("=" * 60)
    print("  澄清引擎 — Clarification Engine 演示")
    print("=" * 60)

    engine = ClarificationEngine()

    # 场景 1：模糊意图
    print("\n场景 1: 用户输入模糊")
    result = engine.generate("都行")
    print(f"  类型: {result['type']}")
    print(f"  回复: {result['clarification']}")

    # 场景 2：多个候选意图
    print("\n场景 2: 多个候选意图（歧义消除）")
    result = engine.generate(
        user_input="我要取消",
        intent_candidates=[
            {"name": "取消预订", "confidence": 0.6},
            {"name": "修改预订", "confidence": 0.4},
        ],
    )
    print(f"  类型: {result['type']}")
    print(f"  回复: {result['clarification']}")
    if result["options"]:
        print(f"  选项: {result['options']}")

    # 场景 3：缺失槽位
    print("\n场景 3: 缺失槽位追问")
    result = engine.generate(
        user_input="我想订酒店",
        missing_slots=["city", "check_in", "check_out"],
    )
    print(f"  类型: {result['type']}")
    print(f"  回复: {result['clarification']}")

    # 场景 4：范围太广
    print("\n场景 4: 范围太广")
    result = engine.generate("我想知道所有类型的酒店")
    print(f"  类型: {result['type']}")
    print(f"  回复: {result['clarification']}")

    # 场景 5：默认兜底
    print("\n场景 5: 默认兜底")
    result = engine.generate("今天天气不错")
    print(f"  类型: {result['type']}")
    print(f"  回复: {result['clarification']}")


def demo_fallback_handler():
    """演示多级兜底策略"""
    print("\n" + "=" * 60)
    print("  兜底策略 — Fallback Handler 演示")
    print("=" * 60)

    handler = FallbackHandler(max_retries=3, transfer_threshold=3)

    # 模拟连续失败
    for i in range(5):
        response = handler.handle()
        print(f"\n  第 {handler.current_retry_count} 次失败 [{response.level.value}]:")
        print(f"    回复: {response.text[:50]}...")
        print(f"    置信度: {response.confidence}")
        if response.options:
            print(f"    选项: {response.options}")
        if response.should_transfer:
            print(f"    ⚠️ 需要转人工!")

    summary = handler.get_escalation_summary()
    print(f"\n  升级摘要: {summary}")


def demo_template_manager():
    """演示话术模板管理"""
    print("\n" + "=" * 60)
    print("  话术模板 — Template Manager 演示")
    print("=" * 60)

    mgr = create_hotel_templates()

    # 获取各阶段话术
    stages = [
        ("greeting", "any"),
        ("intent_recognition", "unknown"),
        ("slot_filling", "book_hotel"),
        ("confirmation", "book_hotel"),
        ("completed", "book_hotel"),
    ]

    for stage, intent in stages:
        text = mgr.get_template(stage, intent)
        if text:
            print(f"\n  [{stage}] {intent}:")
            # 显示前 80 字符
            preview = text[:80] + ("..." if len(text) > 80 else "")
            print(f"    {preview}")

    # A/B 测试：多次调用同一模板
    print("\n  A/B 测试变体:")
    for i in range(3):
        text = mgr.get_template("greeting", "any", use_variant=True)
        print(f"    第 {i+1} 次: {text[:40]}...")


def demo_integrated_flow():
    """集成演示：澄清 + 兜底 + 话术"""
    print("\n" + "=" * 60)
    print("  集成演示 — 完整对话引导流程")
    print("=" * 60)

    engine = ClarificationEngine()
    handler = FallbackHandler()
    mgr = create_hotel_templates()

    # 模拟对话轮次
    turns = [
        {"input": "你好", "stage": "greeting", "intent": "greeting"},
        {"input": "随便看看", "stage": "intent", "intent": "unknown"},
        {"input": "订酒店", "stage": "intent", "intent": "book_hotel"},
        {"input": "北京", "stage": "slot", "intent": "book_hotel"},
        # 模拟用户输入不完整
        {"input": "下个月", "stage": "slot", "intent": "book_hotel",
         "missing_slots": ["check_in", "check_out"]},
        {"input": "2026-08-01 到 8月5号", "stage": "confirm",
         "intent": "book_hotel"},
    ]

    for i, turn in enumerate(turns, 1):
        print(f"\n[轮次 {i}] 用户: {turn['input']}")
        stage = turn.get("stage", "")
        intent = turn.get("intent", "")

        # 意图不明时触发澄清
        if intent == "unknown":
            result = engine.generate(turn["input"])
            print(f"  [澄清] {result['clarification'][:60]}...")

        # 缺失槽位时追问
        if turn.get("missing_slots"):
            result = engine.generate(
                turn["input"],
                missing_slots=turn["missing_slots"],
            )
            print(f"  [追问] {result['clarification']}")

        # 获取阶段话术
        stage_text = mgr.get_template(stage, intent)
        if stage_text and stage not in ("slot", "confirm"):
            preview = stage_text[:60] + ("..." if len(stage_text) > 60 else "")
            print(f"  [话术] {preview}")

    print("\n  ✅ 对话流程演示完成")


if __name__ == "__main__":
    demo_clarification_engine()
    demo_fallback_handler()
    demo_template_manager()
    demo_integrated_flow()
