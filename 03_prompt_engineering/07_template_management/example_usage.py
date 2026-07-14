"""
example_usage.py — Prompt 模板管理使用示例

演示:
1. 基于 YAML 的模板管理
2. Jinja2 变量渲染
3. 版本控制与灰度发布
"""

import os
import yaml
from prompt_manager import PromptManager, PromptVersionController


# ============================================================
# 示例 1：加载并渲染模板
# ============================================================

def example_template_rendering():
    """演示从 YAML 文件加载并渲染 Prompt"""
    
    print("=" * 60)
    print("示例 1：加载并渲染模板")
    print("=" * 60)
    
    # 创建模拟的 prompts 目录
    prompts_dir = "./mock_prompts"
    os.makedirs(prompts_dir, exist_ok=True)
    
    # 写入模拟的 YAML 文件
    template_data = {
        "metadata": {
            "version": "1.0.0",
            "author": "Dev Team",
            "description": "客服助手模板"
        },
        "system_prompt": """你是一个专业的客服助手。
{% if user_language == 'en' %}
Please respond in English.
{% elif user_language == 'zh' %}
请使用中文回复。
{% endif %}
保持礼貌和专业。""",
        "user_prompt": """用户问题：{{ user_question }}
用户订单：{{ order_info }}
请回复："""
    }
    
    yaml_path = os.path.join(prompts_dir, "customer_service.yaml")
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(template_data, f, allow_unicode=True, default_flow_style=False)
    
    # 初始化 Manager
    manager = PromptManager(prompts_dir)
    
    # 渲染 Prompt
    result = manager.get_prompt(
        "customer_service",
        user_language="zh",
        user_question="我的订单什么时候发货？",
        order_info="订单号：12345"
    )
    
    print(f"模板元数据: {result['metadata']}")
    print("\n--- System Prompt ---")
    print(result['system_prompt'])
    print("\n--- User Prompt ---")
    print(result['user_prompt'])
    print()


# ============================================================
# 示例 2：列出所有模板
# ============================================================

def example_list_templates():
    """演示列出所有可用模板"""
    
    print("=" * 60)
    print("示例 2：列出所有模板")
    print("=" * 60)
    
    prompts_dir = "./mock_prompts"
    manager = PromptManager(prompts_dir)
    
    templates = manager.list_templates()
    print(f"可用模板: {templates}")
    print()


# ============================================================
# 示例 3：灰度发布
# ============================================================

def example_ab_testing():
    """演示 A/B 测试与灰度发布"""
    
    print("=" * 60)
    print("示例 3：灰度发布 (A/B Testing)")
    print("=" * 60)
    
    prompts_dir = "./mock_prompts"
    manager = PromptManager(prompts_dir)
    controller = PromptVersionController(manager)
    
    # 设置 90% v1, 10% v2
    controller.set_weights("customer_service", {"v1": 0.9, "v2": 0.1})
    
    # 模拟 10 次调用
    for i in range(10):
        controller.get_prompt_with_version(
            "customer_service",
            user_language="zh",
            user_question=f"测试问题 {i+1}",
            order_info="无"
        )
    print()


# ============================================================
# 示例 4：对比硬编码 vs 模板化
# ============================================================

def comparison_example():
    """对比硬编码与模板化的差异"""
    
    print("=" * 60)
    print("示例 4：对比硬编码 vs 模板化")
    print("=" * 60)
    
    print("--- 硬编码方式 ---")
    print("def chat():")
    print("    prompt = '你是一个助手...' # 修改需要改代码")
    print("    return llm(prompt)")
    
    print("\n--- 模板化方式 ---")
    print("def chat():")
    print("    prompt = manager.get_prompt('bot_v2')")
    print("    return llm(prompt)")
    print("\n优势：修改 YAML 文件即可更新 Prompt，无需重新部署代码。")
    print()


# ============================================================
# 运行所有示例
# ============================================================

if __name__ == "__main__":
    example_template_rendering()
    example_list_templates()
    example_ab_testing()
    comparison_example()
    
    print("=" * 60)
    print("所有示例运行完毕！")
    print("核心要点：配置与代码分离，Jinja2 渲染，版本控制")
    print("=" * 60)
