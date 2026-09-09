"""
example_usage.py — 实战工具集演示
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from practical_toolkit import PracticalToolkit


def demo_weather():
    """天气工具演示"""
    print("=" * 60)
    print("  天气工具")
    print("=" * 60)

    toolkit = PracticalToolkit()

    # 单个查询
    weather = toolkit.weather.get_weather("北京")
    print(f"\n  北京天气: {weather}")

    # 预报
    forecast = toolkit.weather.get_forecast("上海", days=5)
    print(f"  上海预报: {forecast}")

    # 缓存测试
    weather2 = toolkit.weather.get_weather("北京")
    print(f"  北京天气(缓存): {weather2[:50]}...")

    toolkit.close()


def demo_database():
    """数据库工具演示"""
    print("\n" + "=" * 60)
    print("  数据库工具")
    print("=" * 60)

    toolkit = PracticalToolkit()

    # 查询用户
    users = toolkit.database.query("SELECT * FROM users")
    print(f"\n  所有用户: {users[:80]}...")

    # 查询订单
    orders = toolkit.database.get_user_orders(1)
    print(f"  用户 1 的订单: {orders[:80]}...")

    # 插入用户
    new_user = toolkit.database.insert_user("赵六", "zhaoliu@example.com")
    print(f"  新用户: {new_user}")

    toolkit.close()


def demo_api():
    """API 工具演示"""
    print("\n" + "=" * 60)
    print("  API 工具")
    print("=" * 60)

    toolkit = PracticalToolkit()

    # 搜索
    search = toolkit.api.search("Machine Learning", limit=3)
    print(f"\n  搜索结果: {search[:80]}...")

    # 新闻
    news = toolkit.api.get_news("finance", count=3)
    print(f"  财经新闻: {news[:80]}...")

    toolkit.close()


def demo_file():
    """文件工具演示"""
    print("\n" + "=" * 60)
    print("  文件工具")
    print("=" * 60)

    toolkit = PracticalToolkit()

    # 写入
    write = toolkit.files.write_file("demo/hello.txt", "Hello, Function Calling!")
    print(f"\n  写入: {write}")

    # 读取
    read = toolkit.files.read_file("demo/hello.txt")
    print(f"  读取: {read}")

    # 列表
    listing = toolkit.files.list_dir("demo")
    print(f"  目录: {listing}")

    toolkit.close()


def demo_parallel():
    """并行执行演示"""
    print("\n" + "=" * 60)
    print("  并行综合查询")
    print("=" * 60)

    toolkit = PracticalToolkit()

    calls = [
        {"tool_name": "get_weather", "arguments": {"city": "北京"}},
        {"tool_name": "get_forecast", "arguments": {"city": "北京", "days": 5}},
        {"tool_name": "search", "arguments": {"query": "AI", "limit": 3}},
        {"tool_name": "get_news", "arguments": {"category": "tech", "count": 3}},
    ]

    # 并行
    print("\n🚀 并行执行:")
    parallel_result = toolkit.execute(calls, parallel=True)
    print(f"  摘要: {parallel_result.summary}")
    for r in parallel_result.results:
        print(f"  {'✅' if r.success else '❌'} {r.tool_name} ({r.execution_time:.3f}s)")

    # 顺序
    print("\n🐌 顺序执行:")
    sequential_result = toolkit.execute(calls, parallel=False)
    print(f"  摘要: {sequential_result.summary}")

    if parallel_result.total_time > 0:
        speedup = sequential_result.total_time / parallel_result.total_time
        print(f"\n⚡ 加速比: {speedup:.1f}x")

    toolkit.close()


if __name__ == "__main__":
    demo_weather()
    demo_database()
    demo_api()
    demo_file()
    demo_parallel()
