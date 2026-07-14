"""
example_usage.py — Zero-shot 与 Few-shot 使用示例

演示:
1. Zero-shot 情感分析
2. Few-shot 命名实体识别
3. 动态示例选择
4. 示例库管理
"""

from zero_few_shot import (
    ZeroShotPrompt,
    FewShotPrompt,
    Example,
    ExampleLibrary,
)


# ============================================================
# 示例 1：Zero-shot 构建器
# ============================================================

def example_zero_shot():
    """演示 Zero-shot Prompt 构建"""
    
    print("=" * 60)
    print("示例 1：Zero-shot Prompt 构建")
    print("=" * 60)
    
    # 构建 Zero-shot Prompt
    prompt = ZeroShotPrompt(
        task="将以下中文翻译为英文，保持技术文档风格",
        constraints=[
            "保持原文的格式和结构",
            "技术术语首次出现时附注原文",
            "使用正式、学术的语言风格",
        ],
        output_format="英文文本，Markdown 格式",
    ).build()
    
    print(prompt)
    print()
    
    return prompt


# ============================================================
# 示例 2：Few-shot 构建器
# ============================================================

def example_few_shot():
    """演示 Few-shot Prompt 构建"""
    
    print("=" * 60)
    print("示例 2：Few-shot Prompt 构建（文本分类）")
    print("=" * 60)
    
    examples = [
        Example(
            input="这个产品质量很好，值得购买",
            output='{"category": "正面评价", "confidence": 0.95}',
            tags=["positive", "product"],
        ),
        Example(
            input="客服态度太差了，很失望",
            output='{"category": "负面评价", "confidence": 0.92}',
            tags=["negative", "service"],
        ),
        Example(
            input="请问这个产品支持退换货吗？",
            output='{"category": "咨询问题", "confidence": 0.88}',
            tags=["question", "policy"],
        ),
    ]
    
    prompt = FewShotPrompt(
        task="对客户反馈进行文本分类",
        examples=examples,
        actual_input="发货速度很快，包装也很仔细",
        constraints=[
            "输出 JSON 格式",
            "category 可选值：正面评价 / 负面评价 / 咨询问题 / 投诉建议",
            "confidence 为置信度（0-1 之间）",
        ],
        output_format='{"category": "类别", "confidence": 0.9}'
    ).build()
    
    print(prompt)
    print()
    
    return prompt


# ============================================================
# 示例 3：示例库管理
# ============================================================

def example_library():
    """演示示例库的创建和管理"""
    
    print("=" * 60)
    print("示例 3：示例库管理")
    print("=" * 60)
    
    # 创建示例库
    library = ExampleLibrary()
    
    # 添加示例
    library.add("pos_1", Example(
        input="这个手机拍照效果非常好",
        output='{"sentiment": "positive", "aspect": "camera"}',
        tags=["product", "positive", "camera"]
    ))
    
    library.add("pos_2", Example(
        input="屏幕显示效果很清晰",
        output='{"sentiment": "positive", "aspect": "screen"}',
        tags=["product", "positive", "screen"]
    ))
    
    library.add("neg_1", Example(
        input="电池续航太差了",
        output='{"sentiment": "negative", "aspect": "battery"}',
        tags=["product", "negative", "battery"]
    ))
    
    library.add("neg_2", Example(
        input="价格太贵了，不划算",
        output='{"sentiment": "negative", "aspect": "price"}',
        tags=["product", "negative", "price"]
    ))
    
    library.add("neutral_1", Example(
        input="包装还可以吧",
        output='{"sentiment": "neutral", "aspect": "packaging"}',
        tags=["product", "neutral", "packaging"]
    ))
    
    print(f"示例库大小: {len(library)}")
    print()
    
    # 按标签筛选
    print("--- 筛选 positive 标签的示例 ---")
    positive_examples = library.get_by_tags(["positive"], limit=2)
    for i, ex in enumerate(positive_examples, 1):
        print(f"{i}. {ex.input}")
    print()
    
    # 随机选择
    print("--- 随机选择 2 个示例 ---")
    random_examples = library.get_random(2)
    for i, ex in enumerate(random_examples, 1):
        print(f"{i}. {ex.input}")
    print()
    
    # 查看统计信息
    print("--- 示例库统计 ---")
    stats = library.stats()
    print(f"总数: {stats['total']}")
    print(f"标签分布: {stats['tags']}")
    print(f"使用统计: {stats['usage']}")
    print()
    
    return library


# ============================================================
# 示例 4：动态示例选择
# ============================================================

def example_dynamic_selection():
    """演示根据输入特征动态选择示例"""
    
    print("=" * 60)
    print("示例 4：动态示例选择")
    print("=" * 60)
    
    # 假设我们有一个输入分类器
    def classify_input(text: str) -> list[str]:
        """
        简单的输入分类器（实际应用中可用更复杂的模型）
        
        参数:
            text: 输入文本
        返回:
            标签列表
        """
        tags = ["product"]
        
        # 简单的关键词匹配
        if any(word in text for word in ["好", "棒", "喜欢", "满意"]):
            tags.append("positive")
        elif any(word in text for word in ["差", "糟", "失望", "不好"]):
            tags.append("negative")
        else:
            tags.append("neutral")
        
        # 方面识别
        if "电池" in text or "续航" in text:
            tags.append("battery")
        elif "屏幕" in text or "显示" in text:
            tags.append("screen")
        elif "拍照" in text or "相机" in text:
            tags.append("camera")
        elif "价格" in text or "贵" in text:
            tags.append("price")
        
        return tags
    
    # 创建示例库
    library = ExampleLibrary()
    library.add("ex1", Example(
        input="拍照效果很好",
        output='{"sentiment": "positive", "aspect": "camera"}',
        tags=["product", "positive", "camera"]
    ))
    library.add("ex2", Example(
        input="电池不耐用",
        output='{"sentiment": "negative", "aspect": "battery"}',
        tags=["product", "negative", "battery"]
    ))
    library.add("ex3", Example(
        input="屏幕很清晰",
        output='{"sentiment": "positive", "aspect": "screen"}',
        tags=["product", "positive", "screen"]
    ))
    
    # 测试动态选择
    test_inputs = [
        "这个手机拍照效果太棒了",
        "电池续航太差了",
        "屏幕显示效果一般",
    ]
    
    for text in test_inputs:
        tags = classify_input(text)
        print(f"\n输入: {text}")
        print(f"识别标签: {tags}")
        
        # 动态选择示例
        selected = library.get_by_tags(tags, limit=2)
        print(f"选择 {len(selected)} 个示例:")
        for i, ex in enumerate(selected, 1):
            print(f"  {i}. {ex.input} -> {ex.output}")
    
    print()


# ============================================================
# 示例 5：Zero-shot vs Few-shot 对比
# ============================================================

def example_comparison():
    """对比 Zero-shot 和 Few-shot 的 Prompt 构建"""
    
    print("=" * 60)
    print("示例 5：Zero-shot vs Few-shot 对比")
    print("=" * 60)
    
    task = "提取文本中的关键信息"
    input_text = "张三，30岁，软件工程师，在北京工作"
    
    # Zero-shot
    print("\n--- Zero-shot Prompt ---")
    zero_shot = ZeroShotPrompt(
        task=f"{task}：\n\n{input_text}",
        constraints=[
            "提取姓名、年龄、职业、地点",
            "输出 JSON 格式",
        ],
        output_format='{"name": "", "age": 0, "job": "", "location": ""}'
    ).build()
    print(zero_shot)
    
    # Few-shot
    print("\n--- Few-shot Prompt ---")
    few_shot = FewShotPrompt(
        task=task,
        examples=[
            Example(
                input="李四，25岁，产品经理，在上海工作",
                output='{"name": "李四", "age": 25, "job": "产品经理", "location": "上海"}',
            ),
            Example(
                input="王五，35岁，数据分析师，在深圳工作",
                output='{"name": "王五", "age": 35, "job": "数据分析师", "location": "深圳"}',
            ),
        ],
        actual_input=input_text,
        constraints=["输出 JSON 格式"],
        output_format='{"name": "", "age": 0, "job": "", "location": ""}'
    ).build()
    print(few_shot)
    print()


# ============================================================
# 运行所有示例
# ============================================================

if __name__ == "__main__":
    example_zero_shot()
    example_few_shot()
    example_library()
    example_dynamic_selection()
    example_comparison()
    
    print("=" * 60)
    print("所有示例运行完毕！")
    print("核心要点：Zero-shot 快速验证，Few-shot 提高质量")
    print("=" * 60)
