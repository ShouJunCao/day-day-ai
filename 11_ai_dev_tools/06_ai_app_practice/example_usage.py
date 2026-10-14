"""
example_usage.py — AI 应用实战演示
演示应用架构、Specs 生成、Memory/Cron 配置。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_app_practice import (
    APP_TEMPLATE,
    AppSpecGenerator,
    AppMemoryConfig,
    AppCronConfig,
)


def demo_app_architecture():
    print("=" * 60)
    print("  AI 应用架构")
    print("=" * 60)
    
    print(f"\n  应用: {APP_TEMPLATE.name}")
    print(f"  描述: {APP_TEMPLATE.description}")
    print(f"  架构: {APP_TEMPLATE.architecture}")
    print(f"  部署: {APP_TEMPLATE.deployment}")
    
    print("\n  组件:")
    for comp in APP_TEMPLATE.components:
        ai = "✅ AI 辅助" if comp.ai_assisted else "手动"
        print(f"    • {comp.name} ({comp.technology}) [{ai}]")
        print(f"      {comp.description}")


def demo_specs():
    print("\n" + "=" * 60)
    print("  Specs 驱动生成")
    print("=" * 60)
    
    gen = AppSpecGenerator()
    specs = gen.generate_from_template(APP_TEMPLATE)
    
    print(f"\n  生成 {len(specs)} 个应用规格:")
    for spec in specs:
        print(f"\n    [{spec.id}] {spec.name}")
        print(f"    {spec.description}")
        for req in spec.requirements:
            print(f"      - {req['id']}: {req['desc']} ({req['priority']})")


def demo_code_structure():
    print("\n" + "=" * 60)
    print("  代码结构")
    print("=" * 60)
    
    gen = AppSpecGenerator()
    structure = gen.generate_code_structure(APP_TEMPLATE)
    
    for comp, files in structure.items():
        print(f"\n  {comp}/")
        for f in files:
            print(f"    └─ {f}")


def demo_memory():
    print("\n" + "=" * 60)
    print("  Memory 配置")
    print("=" * 60)
    
    memory = AppMemoryConfig.init_memory()
    print(f"\n  初始化 {len(memory)} 条记忆:")
    for entry in memory:
        print(f"    [{entry['target']}] {entry['content']}")


def demo_cron():
    print("\n" + "=" * 60)
    print("  Cron 配置")
    print("=" * 60)
    
    cron = AppCronConfig.init_cron()
    print(f"\n  初始化 {len(cron)} 个定时任务:")
    for job in cron:
        print(f"    • {job['name']} ({job['schedule']})")
        print(f"      {job['desc']}")


def demo_integration():
    print("\n" + "=" * 60)
    print("  Hermes + Kiro 集成流程")
    print("=" * 60)
    
    print("""
    完整集成流程:
    
    1. 使用 Kiro 定义应用 Specs
       → 需求条目 → 验收标准 → 技术架构
    
    2. 使用 Hermes Skills 加载开发技能
       → 编码技能 → 测试技能 → 部署技能
    
    3. 使用 Hermes Memory 存储项目配置
       → 技术栈 → 代码规范 → 部署信息
    
    4. 使用 Hermes Cron 自动化开发流程
       → 代码审查 → 测试运行 → 文档生成
    
    5. 使用 AI 编码工具实现代码
       → Copilot/Cursor 补全 → Claude Code 生成
    
    6. 使用 CI/CD 自动化部署
       → 自动化测试 → Docker 构建 → 灰度发布
    """)


if __name__ == "__main__":
    demo_app_architecture()
    demo_specs()
    demo_code_structure()
    demo_memory()
    demo_cron()
    demo_integration()
