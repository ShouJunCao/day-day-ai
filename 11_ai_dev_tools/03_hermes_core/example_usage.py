"""
example_usage.py — Hermes Agent 核心功能演示
演示 Skills、Memory、Cron、多平台集成。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hermes_skills import (
    SkillManager,
    MemoryStore,
    CronManager,
    PlatformManager,
)


def demo_skills():
    print("=" * 60)
    print("  1. Skill 系统")
    print("=" * 60)
    
    sm = SkillManager()
    
    print(f"\n  分类: {sm.get_categories()}")
    
    results = sm.search("生成")
    print(f"  搜索'生成': {[s.name for s in results]}")
    
    results = sm.search("调试")
    print(f"  搜索'调试': {[s.name for s in results]}")
    
    skill = sm.load("learning-content-generation")
    print(f"  已加载: {sm.loaded}")
    if skill:
        print(f"  步骤: {skill.steps}")
    
    # 按分类
    dev_skills = sm.list_by_category("software-development")
    print(f"  software-development 分类: {[s.name for s in dev_skills]}")


def demo_memory():
    print("\n" + "=" * 60)
    print("  2. Memory 系统")
    print("=" * 60)
    
    ms = MemoryStore()
    
    ms.add("用户偏好：Python 为主，不要过度强调 Java", target="user")
    ms.add("项目使用 pytest 框架", target="memory")
    ms.add("DashScope API Key 已配置", target="memory")
    ms.add("用户在北京，时区 GMT+8", target="user")
    
    print(f"  统计: {ms.stats()}")
    
    python_results = ms.search("Python")
    print(f"  搜索'Python': {len(python_results)} 条")
    for e in python_results:
        print(f"    [{e['target']}] {e['content']}")
    
    user_results = ms.search("北京")
    print(f"  搜索'北京': {len(user_results)} 条")


def demo_cron():
    print("\n" + "=" * 60)
    print("  3. Cron 系统")
    print("=" * 60)
    
    cm = CronManager()
    
    cm.create("AI 日报", "0 9 * * *", "生成 AI 行业日报")
    cm.create("代码审查", "every 2h", "检查 PR 并生成审查报告")
    cm.create("热点监控", "30m", "监控热点话题")
    
    print("  任务列表:")
    for j in cm.list_jobs():
        status = "✅" if j["enabled"] else "⏸️"
        print(f"    {status} {j['name']} ({j['schedule']})")
    
    # 禁用一个
    cm.disable("热点监控")
    print(f"\n  禁用'热点监控'后:")
    for j in cm.list_jobs():
        status = "✅" if j["enabled"] else "⏸️"
        print(f"    {status} {j['name']} ({j['schedule']})")


def demo_platforms():
    print("\n" + "=" * 60)
    print("  4. 多平台集成")
    print("=" * 60)
    
    pm = PlatformManager()
    
    print("  已连接平台:")
    for p in pm.list_platforms():
        print(f"    • {p['name']} ({p['type']}) - {p['status']}")
        print(f"      功能: {', '.join(p['features'])}")


if __name__ == "__main__":
    demo_skills()
    demo_memory()
    demo_cron()
    demo_platforms()
