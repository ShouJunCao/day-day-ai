"""
使用示例: 演示滑动窗口和 Token 预算在长对话中的表现。
"""
import os
import sys

# 确保能导入模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from context_window import SlidingWindowContext
from token_budget import TokenBudgetController


def demo_sliding_window():
    """演示滑动窗口管理"""
    print("=" * 60)
    print("  滑动窗口管理器 (Sliding Window) 演示")
    print("=" * 60)

    # 初始化上下文 (小窗口便于观察)
    ctx = SlidingWindowContext(max_tokens=80, max_turns=8)

    # 1. 添加 System Prompt
    ctx.add("system", "你是一个专业的编程助手。")
    print(f"初始: {len(ctx)} 条消息, Token: {ctx.token_usage}")

    # 2. 模拟多轮对话
    queries = [
        "Python 如何实现单例模式?",
        "解释一下这个代码的复杂度。",
        "有没有更好的写法?",
        "如果是多线程环境怎么办?",
        "使用 threading.Lock 会怎样?",
        "能写个完整的例子吗?",
    ]

    for i, q in enumerate(queries):
        ctx.add("user", q)
        ctx.add("assistant", f"这是第 {i+1} 条回答: 关于{q[:10]}...")
        print(f"  第 {i+1} 轮: {len(ctx)} 条消息, Token: {ctx.token_usage}")

    print(f"\n最终保留 {len(ctx)} 条消息, Token 用量: {ctx.token_usage}")
    print("\n发送给 LLM 的上下文:")
    for msg in ctx.get_context():
        preview = msg["content"][:30] + ("..." if len(msg["content"]) > 30 else "")
        print(f"  [{msg['role']:10s}] {preview}")


def demo_token_budget():
    """演示 Token 预算控制"""
    print("\n" + "=" * 60)
    print("  Token 预算控制 (Token Budget) 演示")
    print("=" * 60)

    # 设置一个较低的预算限制来触发裁剪
    controller = TokenBudgetController(limit=100)

    messages = [
        {"role": "system", "content": "你是一个编程助手。"},
        {"role": "user", "content": "请详细解释 Python 中的装饰器模式, " * 5},
        {"role": "assistant", "content": "装饰器是 Python 中非常强大的功能... " * 8},
        {"role": "user", "content": "能再详细一点吗?" * 3},
        {"role": "assistant", "content": "当然可以。装饰器的本质是... " * 6},
    ]

    result = controller.check(messages)
    print(f"原始: {result['used']} tokens (限额: {controller.limit})")
    print(f"状态: {'✅ 正常' if result['ok'] else '❌ 超出预算'}")

    if not result["ok"]:
        print(f"超出 {result['over_by']} tokens, 自动裁剪中...")
        trimmed = controller.trim_to_fit(messages)
        new_result = controller.check(trimmed)
        print(f"裁剪后: {new_result['used']} tokens (保留了 {len(trimmed)}/{len(messages)} 条消息)")


if __name__ == "__main__":
    demo_sliding_window()
    demo_token_budget()
