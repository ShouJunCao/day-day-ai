"""
example_usage.py — System Prompt 角色设定使用示例

演示:
1. 基础 System Prompt 构建
2. 常见角色模板（专家、审查者、导师）
3. 动态上下文注入
4. Prompt 校验与 Token 估算
"""

from role_system import (
    SystemPromptBuilder,
    DynamicSystemPrompt,
    EXPERT_CODE_REVIEWER,
    CRITIC_PATTERN,
    MENTOR_PATTERN,
)


# ============================================================
# 示例 1：基础 System Prompt 构建
# ============================================================

def example_basic_builder():
    """演示 SystemPromptBuilder 的基础用法"""
    
    print("=" * 60)
    print("示例 1：基础 System Prompt 构建")
    print("=" * 60)
    
    builder = SystemPromptBuilder()
    
    prompt = (
        builder
        .set_role("资深 Python 工程师")
        .add_context("项目使用 FastAPI 框架")
        .add_context("数据库为 PostgreSQL")
        .add_rule("代码必须包含类型提示")
        .add_rule("优先使用异步操作")
        .add_rule("解释关键逻辑")
        .add_constraint("不要使用 eval()")
        .add_constraint("不要输出未经验证的 SQL")
        .set_format("Markdown 格式，包含代码块")
        .build()
    )
    
    print(prompt)
    print(f"\n预估 Token 数: {builder.estimate_tokens()}")
    print()


# ============================================================
# 示例 2：使用预设角色模板
# ============================================================

def example_presets():
    """演示如何使用预设的角色模板"""
    
    print("=" * 60)
    print("示例 2：使用预设角色模板")
    print("=" * 60)
    
    print("--- 专家代码审查员 ---")
    print(EXPERT_CODE_REVIEWER.strip()[:300] + "...")
    print()
    
    print("--- 逻辑审查员 (Critic) ---")
    print(CRITIC_PATTERN.strip()[:300] + "...")
    print()
    
    print("--- 编程导师 (Mentor) ---")
    print(MENTOR_PATTERN.strip()[:300] + "...")
    print()


# ============================================================
# 示例 3：动态上下文注入
# ============================================================

def example_dynamic():
    """演示 DynamicSystemPrompt 的动态注入"""
    
    print("=" * 60)
    print("示例 3：动态上下文注入")
    print("=" * 60)
    
    # 模拟两个不同用户
    users = [
        {"name": "Alice", "tier": "Free", "language": "zh"},
        {"name": "Bob", "tier": "Enterprise", "language": "en"},
    ]
    
    for user in users:
        print(f"\n--- 用户: {user['name']} ---")
        builder = DynamicSystemPrompt(user_locale=user['language'])
        
        prompt = (
            builder
            .set_role("智能编程助手")
            .inject_context(user)
            .add_rule("根据用户水平调整回答难度")
            .build()
        )
        
        print(prompt)
    print()


# ============================================================
# 示例 4：Prompt 校验
# ============================================================

def example_validation():
    """演示 Prompt 校验功能"""
    
    print("=" * 60)
    print("示例 4：Prompt 校验")
    print("=" * 60)
    
    # 有效的 Prompt
    builder = SystemPromptBuilder()
    builder.set_role("翻译助手")
    builder.add_rule("准确翻译")
    errors = builder.validate()
    print(f"有效 Prompt 校验结果: {errors}")
    
    # 缺少角色
    empty_builder = SystemPromptBuilder()
    errors = empty_builder.validate()
    print(f"缺少角色校验结果: {errors}")
    
    # 超长 Prompt (模拟)
    long_builder = SystemPromptBuilder()
    long_builder.set_role("A" * 5000)
    errors = long_builder.validate()
    print(f"超长 Prompt 校验结果: {errors}")
    print()


# ============================================================
# 示例 5：XML 标签隔离上下文
# ============================================================

def example_xml_isolation():
    """演示使用 XML 标签隔离上下文"""
    
    print("=" * 60)
    print("示例 5：XML 标签隔离上下文")
    print("=" * 60)
    
    context_data = """
    <user_profile>
        <name>张三</name>
        <level>Beginner</level>
        <goal>学习 Python 基础语法</goal>
    </user_profile>
    
    <project_info>
        <repo>github.com/example/my-project</repo>
        <framework>Django</framework>
    </project_info>
    """
    
    prompt = f"""# 角色
你是一个 Python 导师。

# 背景信息
以下是当前用户的个人资料和项目信息，请根据这些信息调整你的回答：
{context_data}

# 行为准则
1. 使用简单易懂的语言
2. 多举例说明
"""
    print(prompt)
    print()


# ============================================================
# 运行所有示例
# ============================================================

if __name__ == "__main__":
    example_basic_builder()
    example_presets()
    example_dynamic()
    example_validation()
    example_xml_isolation()
    
    print("=" * 60)
    print("所有示例运行完毕！")
    print("核心要点：角色设定、结构化、动态注入")
    print("=" * 60)
