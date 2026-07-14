"""
example_usage.py — CoT 与 ToT 使用示例

演示:
1. Zero-shot CoT 构建与解析
2. Few-shot CoT 数学推理
3. Tree-of-Thought 搜索框架
4. 统一推理引擎（自动策略选择）
"""

from cot_tot import (
    ZeroShotCoT,
    FewShotCoT,
    CoTExample,
    TreeOfThought,
    ReasoningEngine,
)


# ============================================================
# 示例 1：Zero-shot CoT
# ============================================================

def example_zero_shot_cot():
    """演示 Zero-shot CoT 的构建和解析"""
    
    print("=" * 60)
    print("示例 1：Zero-shot CoT")
    print("=" * 60)
    
    # 创建 Zero-shot CoT（中文）
    cot = ZeroShotCoT(language="zh")
    
    # 构建 Prompt
    question = (
        "一家公司有 120 名员工，其中 60% 是技术人员。"
        "如果技术人员中有 25% 是高级工程师，"
        "那么高级工程师有多少人？"
    )
    
    prompt = cot.build_prompt(question)
    print("生成的 Prompt：")
    print(prompt)
    print()
    
    # 模拟模型输出
    mock_response = """
1. 首先计算技术人员总数：120 × 60% = 72 人
2. 然后计算高级工程师人数：72 × 25% = 18 人
3. 所以高级工程师有 18 人
答案：18 人
"""
    
    # 解析响应
    result = cot.parse_response(mock_response)
    print("\n解析结果：")
    print(f"  推理步骤数: {len(result.reasoning_steps)}")
    for i, step in enumerate(result.reasoning_steps, 1):
        print(f"  {i}. {step}")
    print(f"  最终答案: {result.final_answer}")
    print()


# ============================================================
# 示例 2：Few-shot CoT
# ============================================================

def example_few_shot_cot():
    """演示 Few-shot CoT 数学推理"""
    
    print("=" * 60)
    print("示例 2：Few-shot CoT 数学推理")
    print("=" * 60)
    
    # 使用预设的数学推理模板
    cot = FewShotCoT.math_reasoning()
    
    # 构建 Prompt
    question = (
        "一本书 240 页，第一天读了 1/4，第二天读了剩余的 1/3，"
        "还剩多少页没读？"
    )
    
    prompt = cot.build_prompt(question)
    print(prompt)
    print()
    
    # 也可以自定义示例
    custom_examples = [
        CoTExample(
            question="一个班有 40 人，男生占 3/5，女生有多少人？",
            steps=[
                "男生人数：40 × 3/5 = 24 人",
                "女生人数：40 - 24 = 16 人",
            ],
            answer="16 人",
        ),
        CoTExample(
            question="商品原价 200 元，打 8 折后再打 9 折，现价多少？",
            steps=[
                "打 8 折：200 × 0.8 = 160 元",
                "再打 9 折：160 × 0.9 = 144 元",
            ],
            answer="144 元",
        ),
    ]
    
    custom_cot = FewShotCoT(custom_examples)
    print("--- 自定义示例 Prompt ---")
    print(custom_cot.build_prompt("火车时速 120km，行驶 3.5 小时，走了多远？"))
    print()


# ============================================================
# 示例 3：CoT 触发词对比
# ============================================================

def example_triggers():
    """演示不同触发词的效果差异"""
    
    print("=" * 60)
    print("示例 3：不同 CoT 触发词对比")
    print("=" * 60)
    
    question = "证明：任意偶数的平方都是 4 的倍数"
    
    triggers = ["en", "zh", "detailed"]
    
    for trigger_type in triggers:
        cot = ZeroShotCoT(language=trigger_type)
        prompt = cot.build_prompt(question)
        
        print(f"\n--- 触发词类型: {trigger_type} ---")
        # 只显示触发部分
        lines = prompt.split("\n")
        for line in lines[-3:]:
            print(f"  {line}")
    
    print()


# ============================================================
# 示例 4：推理引擎自动策略选择
# ============================================================

def example_reasoning_engine():
    """演示统一推理引擎的使用"""
    
    print("=" * 60)
    print("示例 4：推理引擎自动策略选择")
    print("=" * 60)
    
    print("推理引擎支持三种策略：")
    print("  - auto: 自动评估复杂度，选择 CoT 或 ToT")
    print("  - cot: 强制使用思维链")
    print("  - tot: 强制使用思维树")
    print()
    
    print("策略选择逻辑：")
    print("  1. auto 模式：先评估问题复杂度")
    print("     - simple → Zero-shot CoT（1次调用）")
    print("     - complex → ToT BFS（多次调用）")
    print()
    print("  2. 成本对比：")
    print("     - CoT: 1-2 次 API 调用")
    print("     - ToT: 10-50 次 API 调用")
    print()
    
    # 模拟不同问题的策略选择
    test_questions = [
        ("15 + 27 = ?", "simple"),
        ("证明素数有无穷多个", "complex"),
        ("北京到上海多远？", "simple"),
        ("一个逻辑推理谜题...", "complex"),
    ]
    
    print("问题复杂度评估示例：")
    for question, expected in test_questions:
        print(f"  Q: {question}")
        print(f"  预期策略: {expected} → {'CoT' if expected == 'simple' else 'ToT'}")
        print()


# ============================================================
# 示例 5：CoT 与 ToT 对比总结
# ============================================================

def example_comparison_summary():
    """CoT 与 ToT 的完整对比"""
    
    print("=" * 60)
    print("示例 5：CoT vs ToT 完整对比")
    print("=" * 60)
    
    comparison = {
        "推理结构": ("线性链", "树状搜索"),
        "路径数量": ("单条", "多条并行"),
        "API调用": ("1次", "10-50次"),
        "Token成本": ("低", "高"),
        "准确率": ("中等", "高"),
        "延迟": ("低", "高"),
        "实现复杂度": ("简单", "复杂"),
    }
    
    print(f"{'维度':<15} {'CoT':<20} {'ToT':<20}")
    print("-" * 55)
    for dim, (cot_val, tot_val) in comparison.items():
        print(f"{dim:<15} {cot_val:<20} {tot_val:<20}")
    
    print()
    print("选择建议：")
    print("  ✓ 简单推理、实时响应 → CoT")
    print("  ✓ 复杂问题、高准确率要求 → ToT")
    print("  ✓ 生产环境 → ReasoningEngine(auto)")
    print()


# ============================================================
# 运行所有示例
# ============================================================

if __name__ == "__main__":
    example_zero_shot_cot()
    example_few_shot_cot()
    example_triggers()
    example_reasoning_engine()
    example_comparison_summary()
    
    print("=" * 60)
    print("所有示例运行完毕！")
    print("核心要点：CoT 是基础，ToT 是进阶")
    print("=" * 60)
