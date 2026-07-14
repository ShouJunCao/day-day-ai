"""
企业级 Prompt 模板库使用示例
演示模板注册、加载、渲染、版本管理与缓存策略。
"""
from prompt_library import PromptTemplate, PromptRegistry, TemplateLoader
from cache_layer import PromptCache

def main() -> None:
    # 1. 初始化注册中心与缓存
    registry = PromptRegistry()
    loader = TemplateLoader(registry)
    cache = PromptCache(max_size=512, default_ttl=600.0)

    # 2. 内联创建模板
    t1 = loader.create_inline(
        id="customer_service_greeting",
        name="客服欢迎语",
        category="customer_service",
        version="2.1.0",
        content="您好，{{customer_name}}！我是{{agent_name}}，很高兴为您服务。请问有什么可以帮您？",
        metadata={"tone": "professional", "language": "zh"}
    )
    print(f"✅ 创建模板: {t1.name} (v{t1.version})")

    # 3. 渲染模板
    rendered = t1.render(customer_name="张三", agent_name="小艾")
    print(f"📝 渲染结果: {rendered}")

    # 4. 缓存渲染结果
    cache_key = f"{t1.id}:customer_name=张三:agent_name=小艾"
    cache.put(cache_key, rendered)
    cached_result = cache.get(cache_key)
    print(f"💾 缓存命中: {cached_result == rendered}")

    # 5. 分类检索
    registry.register(PromptTemplate(
        id="email_followup", name="邮件跟进", category="sales",
        version="1.0.0", content="感谢您的咨询，关于{{product}}..."
    ))
    sales_templates = registry.list_by_category("sales")
    print(f"📂 Sales 类模板: {[t.name for t in sales_templates]}")

    # 6. 版本历史
    t1_v2 = loader.create_inline(
        id="customer_service_greeting",
        name="客服欢迎语",
        category="customer_service",
        version="2.2.0",
        content="您好，{{customer_name}}！我是{{agent_name}}，很高兴为您服务。\n\n请问有什么可以帮您？",
        metadata={"tone": "professional", "language": "zh", "change": "added_newline"}
    )
    history = registry._version_history.get("customer_service_greeting", [])
    print(f"📊 版本历史: {[t.version for t in history]}")

    # 7. 缓存统计
    stats = cache.stats()
    print(f"📈 缓存状态: {stats}")

if __name__ == "__main__":
    main()
