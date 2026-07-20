"""
使用示例: 演示完整的智能客服系统端到端对话流程。
包含两个场景：成功预订 和 兜底转人工。
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from customer_service_system import CustomerServiceSystem


def demo_successful_booking():
    """演示场景一：用户成功预订酒店"""
    print("=" * 60)
    print("  场景一：成功预订酒店")
    print("=" * 60)

    system = CustomerServiceSystem()

    # 模拟用户输入序列
    inputs = [
        "你好",
        "我想预订酒店",
        "北京",
        "2026-08-01",
        "2026-08-05",
        "是的",
    ]

    print()
    for i, user_input in enumerate(inputs, 1):
        response = system.handle_input(user_input)
        print(f"[轮次 {i}]")
        print(f"  👤 用户: {user_input}")
        print(f"  🤖 系统: {response[:100]}...")
        print(f"  📍 状态: {system.current_state.value}")
        print()

    # 打印会话报告
    report = system.get_session_report()
    print("📊 会话报告:")
    print(f"  总轮次: {report['total_turns']}")
    print(f"  是否完成: {report['completed']}")
    print(f"  兜底次数: {report['fallback_count']}")
    print(f"  已填槽位: {report['slots_filled']}")

    # 打印对话记录
    print("\n📋 对话记录:")
    for entry in system.get_conversation_log():
        print(f"  [{entry['turn']}] {entry['user']} → {entry['state']}")


def demo_fallback_escalation():
    """演示场景二：兜底 → 转人工"""
    print("\n" + "=" * 60)
    print("  场景二：兜底 → 转人工")
    print("=" * 60)

    system = CustomerServiceSystem()

    # 模拟用户输入无法识别的内容
    inputs = [
        "你好",
        "帮我推荐一部电影",      # 不在意图库中
        "随便说说",               # 模糊输入
        "算了",                   # 继续模糊
        "转人工",                 # 要求转人工
    ]

    print()
    for i, user_input in enumerate(inputs, 1):
        response = system.handle_input(user_input)
        print(f"[轮次 {i}]")
        print(f"  👤 用户: {user_input}")
        print(f"  🤖 系统: {response[:100]}...")
        print(f"  📍 状态: {system.current_state.value}")
        print()

    report = system.get_session_report()
    print("📊 会话报告:")
    print(f"  总轮次: {report['total_turns']}")
    print(f"  是否完成: {report['completed']}")
    print(f"  兜底次数: {report['fallback_count']}")
    print(f"  转人工次数: {report['escalation_count']}")
    print(f"  最终状态: {report['final_state']}")


def demo_slot_correction():
    """演示场景三：确认阶段修改信息"""
    print("\n" + "=" * 60)
    print("  场景三：确认 → 修改 → 再确认")
    print("=" * 60)

    system = CustomerServiceSystem()

    inputs = [
        "你好",
        "我要订酒店",
        "上海",
        "2026-09-01",
        "2026-09-03",
        "不对，改日期",           # 否认并请求修改
        "2026-09-05",             # 提供新日期
        "是的",                   # 最终确认
    ]

    print()
    for i, user_input in enumerate(inputs, 1):
        response = system.handle_input(user_input)
        print(f"[轮次 {i}]")
        print(f"  👤 用户: {user_input}")
        print(f"  🤖 系统: {response[:80]}...")
        print(f"  📍 状态: {system.current_state.value}")
        print()

    report = system.get_session_report()
    print("📊 会话报告:")
    print(f"  总轮次: {report['total_turns']}")
    print(f"  是否完成: {report['completed']}")
    print(f"  已填槽位: {report['slots_filled']}")


if __name__ == "__main__":
    demo_successful_booking()
    demo_fallback_escalation()
    demo_slot_correction()
