"""
example_usage.py — Prompt 设计四大原则使用示例

演示如何使用 PromptBuilder、PromptTemplate 和 PromptRegistry
来构建高质量的 Prompt。
"""

from prompt_principles import PromptBuilder, PromptTemplate, PromptRegistry


# ============================================================
# 示例 1：使用 PromptBuilder 构建数据分析 Prompt
# ============================================================

def example_prompt_builder():
    """演示 PromptBuilder 的四大原则应用"""

    print("=" * 60)
    print("示例 1：PromptBuilder 构建数据分析 Prompt")
    print("=" * 60)

    # 清晰原则：明确角色和任务
    builder = PromptBuilder(
        role="资深数据分析师",
        task="分析以下电商销售数据，生成月度分析报告",
        context="数据来源：公司 CRM 系统，时间范围：2024年1月",
    )

    # 具体原则：添加约束条件
    builder.add_constraint("报告长度控制在 800-1200 字")
    builder.add_constraint("必须包含同比和环比数据对比")
    builder.add_constraint("使用 Markdown 表格展示关键指标")
    builder.add_constraint("不要使用专业术语，面向管理层汇报")
    builder.add_constraint("至少给出 3 条可执行的改进建议")

    # 结构化原则：指定输出格式
    builder.output_format = (
        "Markdown 格式，包含：摘要、数据概览、问题分析、建议"
    )

    prompt = builder.build()
    print(prompt)
    print()

    return prompt


# ============================================================
# 示例 2：分步骤原则 — 竞品分析
# ============================================================

def example_step_by_step():
    """演示分步骤原则处理复杂任务"""

    print("=" * 60)
    print("示例 2：分步骤竞品分析 Prompt")
    print("=" * 60)

    analysis_builder = PromptBuilder(
        role="商业分析师",
        task="分析竞品产品并输出竞品分析报告",
        steps=[
            "第一步：列出竞品的 5 个核心功能特性",
            "第二步：分析每个功能的优势和劣势",
            "第三步：与我们的产品进行逐项对比",
            "第四步：识别竞品的差异化策略",
            "第五步：提出 3 条应对建议，按优先级排序",
        ],
        constraints=[
            "每个步骤完成后输出该步骤的结论",
            "最终报告不超过 1500 字",
            "使用 SWOT 分析框架组织结论",
        ],
        output_format="Markdown 报告，每个步骤一个小节",
    )

    prompt = analysis_builder.build()
    print(prompt)
    print()

    return prompt


# ============================================================
# 示例 3：PromptTemplate 模板渲染
# ============================================================

CODE_REVIEW_TEMPLATE = """## 角色
你是一个有 10 年经验的 $language 高级工程师，专注于代码审查。

## 任务
请审查以下代码，给出专业的审查意见。

## 待审查代码
```$language
$code
```

## 审查维度
1. **代码质量**：可读性、命名规范、代码风格
2. **潜在 Bug**：边界条件、空值处理、异常安全
3. **性能**：算法复杂度、内存使用、不必要的计算
4. **安全性**：注入风险、敏感数据暴露、权限校验

## 输出要求
- 按严重程度分级：🔴 严重 / 🟡 警告 / 🟢 建议
- 每条意见包含：问题位置、问题描述、修复建议
- 最后给出总体评分（1-10 分）和总结
"""


def example_template():
    """演示 PromptTemplate 模板系统"""

    print("=" * 60)
    print("示例 3：PromptTemplate 模板渲染")
    print("=" * 60)

    reviewer = PromptTemplate(CODE_REVIEW_TEMPLATE)

    # 查看模板变量
    print(f"模板变量: {reviewer.variables}")
    print()

    # 渲染模板
    sample_code = '''
def calc(x, y):
    return x / y

def process(data):
    result = []
    for item in data:
        result.append(calc(item[0], item[1]))
    return result
'''

    rendered = reviewer.render(
        language="python",
        code=sample_code.strip(),
    )
    print(rendered[:500])
    print("...(输出截断)")
    print()

    return rendered


# ============================================================
# 示例 4：PromptRegistry 注册管理中心
# ============================================================

def example_registry():
    """演示 Prompt 注册管理中心"""

    print("=" * 60)
    print("示例 4：PromptRegistry 注册管理中心")
    print("=" * 60)

    # 创建注册中心
    registry = PromptRegistry(storage_dir="/tmp/prompt_demo")

    # 注册代码审查模板
    info = registry.register(
        name="code_review",
        template=CODE_REVIEW_TEMPLATE,
        description="通用代码审查模板，支持多语言",
        tags=["code", "review", "quality"],
    )
    print(f"注册成功: {info['name']} v{info['version']}")

    # 注册翻译模板
    translation_template = """## 角色
你是一个专业的 $source_lang 到 $target_lang 翻译专家。

## 任务
将以下文本从 $source_lang 翻译为 $target_lang。

## 待翻译文本
$text

## 要求
- 保持原文的格式和结构
- 技术术语保持原文或附注原文
- 翻译风格：$style
"""
    registry.register(
        name="translation",
        template=translation_template,
        description="多语言翻译模板",
        tags=["translation", "i18n"],
    )

    # 列出所有模板
    templates = registry.list_templates()
    print(f"\n已注册模板数: {len(templates)}")
    for t in templates:
        print(f"  - {t['name']} v{t['version']} [{', '.join(t['tags'])}]")

    # 按标签搜索
    code_templates = registry.search_by_tag("code")
    print(f"\n标签 'code' 的模板: {len(code_templates)} 个")

    # 获取并使用模板
    tpl = registry.get("translation")
    if tpl:
        result = tpl.render(
            source_lang="中文",
            target_lang="英文",
            text="人工智能正在改变世界",
            style="正式、学术",
        )
        print(f"\n渲染结果预览:\n{result[:200]}")

    print()


# ============================================================
# 示例 5：好 Prompt vs 坏 Prompt 对比
# ============================================================

def example_comparison():
    """演示好 Prompt 与坏 Prompt 的差异"""

    print("=" * 60)
    print("示例 5：好 Prompt vs 坏 Prompt 对比")
    print("=" * 60)

    # 坏 Prompt：模糊、不具体、无结构
    bad_prompt = "帮我写个函数处理数据"

    # 好 Prompt：清晰、具体、结构化
    good_builder = PromptBuilder(
        role="Python 后端工程师",
        task="编写一个数据去重和排序的工具函数",
        constraints=[
            "输入：List[dict]，每个 dict 包含 'id' 和 'score' 字段",
            "输出：去重后按 score 降序排列的列表",
            "时间复杂度要求：O(n log n)",
            "包含类型提示和文档字符串",
            "处理 id 为空或 score 为非数字的异常情况",
        ],
        steps=[
            "验证输入数据的合法性",
            "按 id 去重，保留 score 最高的记录",
            "按 score 降序排序",
            "添加单元测试",
        ],
        output_format="Python 代码，包含函数定义、类型提示、docstring、测试",
    )
    good_prompt = good_builder.build()

    print(f"❌ 坏 Prompt:\n  {bad_prompt}")
    print(f"\n✅ 好 Prompt:\n{good_prompt}")
    print()


# ============================================================
# 运行所有示例
# ============================================================

if __name__ == "__main__":
    example_prompt_builder()
    example_step_by_step()
    example_template()
    example_registry()
    example_comparison()

    print("=" * 60)
    print("所有示例运行完毕！")
    print("核心要点：清晰、具体、结构化、分步骤")
    print("=" * 60)
