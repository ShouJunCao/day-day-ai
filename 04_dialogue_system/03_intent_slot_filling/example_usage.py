"""
使用示例: 演示意图识别与槽位填充的三种方法。
包括关键词分类、规则槽位提取、LLM 端到端理解。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from intent_classifier import IntentClassifier, HybridIntentClassifier
from slot_filler import SlotFiller


def demo_intent_classification():
    """演示意图分类"""
    print("=" * 60)
    print("  意图分类 — Intent Classification 演示")
    print("=" * 60)

    classifier = IntentClassifier(mode="keyword")

    test_inputs = [
        "你好，有什么可以帮我的？",
        "帮我订明天北京到上海的机票",
        "我想预订酒店",
        "北京今天天气怎么样",
        "查询我的订单",
        "我要取消预订",
        "今天心情不好，聊聊天吧",
        "帮我推荐一部电影",  # 未知意图
    ]

    print()
    for text in test_inputs:
        result = classifier.predict(text)
        print(f"  输入: {text}")
        print(f"    意图: {result['intent']} (置信度: {result['confidence']:.1%})")
        if result["all_scores"]:
            top3 = sorted(
                result["all_scores"].items(),
                key=lambda x: x[1],
                reverse=True,
            )[:3]
            scores_str = ", ".join(f"{k}={v:.1%}" for k, v in top3)
            print(f"    Top 3: {scores_str}")
        print()


def demo_slot_filling():
    """演示槽位填充"""
    print("\n" + "=" * 60)
    print("  槽位填充 — Slot Filling 演示")
    print("=" * 60)

    filler = SlotFiller(mode="rule")

    # 机票场景
    flight_schema = {
        "departure": {"type": "city", "required": True},
        "arrival": {"type": "city", "required": True},
        "date": {"type": "date", "required": True},
        "passengers": {"type": "number", "required": False},
    }

    test_cases = [
        ("订明天北京到上海的机票", flight_schema),
        ("后天广州飞成都，2个人", flight_schema),
        ("2026-08-01 从深圳到杭州", flight_schema),
        ("订个房", flight_schema),  # 缺失槽位
    ]

    print("\n机票场景:")
    for text, schema in test_cases:
        result = filler.fill(text, schema)
        print(f"  输入: {text}")
        print(f"    槽位: {result['slots']}")
        print(f"    缺失: {result['missing']}")
        print(f"    置信度: {result['confidence']:.1%}")
        print()

    # 酒店场景
    hotel_schema = {
        "city": {"type": "city", "required": True},
        "check_in": {"type": "date", "required": True},
        "check_out": {"type": "date", "required": False},
    }

    print("酒店场景:")
    hotel_cases = [
        "预订后天北京的酒店",
        "明天入住上海，住 3 天",
    ]
    for text in hotel_cases:
        result = filler.fill(text, hotel_schema)
        print(f"  输入: {text}")
        print(f"    槽位: {result['slots']}")
        print(f"    缺失: {result['missing']}")
        print()


def demo_hybrid_classifier():
    """演示混合分类器"""
    print("\n" + "=" * 60)
    print("  混合分类器 — Hybrid Classifier 演示")
    print("=" * 60)

    classifier = HybridIntentClassifier(
        high_threshold=0.8,
        low_threshold=0.3,
        fallback_mode="keyword",
    )

    test_inputs = [
        "订机票",                     # 高置信度 → keyword 直接返回
        "帮我订后天上海飞北京的商务舱",  # 中置信度 → fallback
        "推荐一部电影",               # 低置信度 → unknown
    ]

    print()
    for text in test_inputs:
        result = classifier.predict(text)
        print(f"  输入: {text}")
        print(f"    意图: {result['intent']} "
              f"(置信度: {result['confidence']:.1%})")
        print(f"    来源: {result.get('source', 'unknown')}")
        if "fast_score" in result:
            print(f"    快速得分: {result['fast_score']:.1%} "
                  f"→ 触发回退")
        print()


def demo_nlu_integration():
    """演示 LLM 端到端理解"""
    print("\n" + "=" * 60)
    print("  LLM 端到端对话理解 — NLU 演示")
    print("=" * 60)

    try:
        from llm_nlu import DialogueUnderstandingClient, SchemaBasedNLU
    except ImportError:
        print("  ⚠️ LLM NLU 需要配置 API_KEY 环境变量，跳过演示")
        return

    # Schema-based NLU
    nlu = SchemaBasedNLU()
    test_inputs = [
        "帮我订后天上海飞北京的商务舱",
        "明天北京天气怎么样",
        "查询订单 #HTL123456",
    ]

    print("\nSchema-based NLU:")
    for text in test_inputs:
        try:
            result = nlu.extract(text)
            if result is None:
                print(f"  输入: {text}")
                print(f"    ⚠️ 返回值为 None")
                print()
                continue
            is_valid, errors = nlu.validate(result)
            print(f"  输入: {text}")
            print(f"    意图: {result.get('intent')}")
            print(f"    槽位: {result.get('slots')}")
            print(f"    缺失: {result.get('missing_slots')}")
            print(f"    验证: {'✅ 通过' if is_valid else f'❌ {errors}'}")
            print()
        except Exception as e:
            print(f"  ⚠️ LLM 调用失败: {e}")
            print("  （需要配置 API_KEY 环境变量）")
            print()


if __name__ == "__main__":
    demo_intent_classification()
    demo_slot_filling()
    demo_hybrid_classifier()
    demo_nlu_integration()
