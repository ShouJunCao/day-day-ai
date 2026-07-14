"""
example_usage.py — 结构化输出使用示例

演示:
1. 鲁棒的 JSON 解析
2. XML 标签提取
3. Pydantic 强类型校验
4. 修复 Prompt 生成
"""

from pydantic import BaseModel, ValidationError
from structured_output import (
    StructuredOutputParser,
    XMLExtractor,
    PydanticValidator,
)


# ============================================================
# 示例 1：鲁棒的 JSON 解析
# ============================================================

def example_json_parsing():
    """演示解析各种“不听话”的模型输出"""
    
    print("=" * 60)
    print("示例 1：鲁棒的 JSON 解析")
    print("=" * 60)
    
    test_cases = [
        # 标准 JSON
        ('{"name": "Alice", "age": 25}', "标准 JSON"),
        # Markdown 包裹
        ('```json\n{"name": "Bob", "age": 30}\n```', "Markdown 包裹"),
        # 包含前后缀文本
        ('好的，这是结果：\n{"name": "Charlie", "age": 35}\n希望对你有帮助。', "前后缀文本"),
        # 截断的 JSON (模拟)
        ('{"name": "Dave", "age": 40, "job": "Dev}', "截断 JSON (预期失败)"),
    ]
    
    for raw, desc in test_cases:
        print(f"\n--- {desc} ---")
        print(f"输入: {raw!r}")
        result = StructuredOutputParser.parse_json(raw)
        print(f"解析结果: {result}")
    print()


# ============================================================
# 示例 2：XML 标签提取
# ============================================================

def example_xml_extraction():
    """演示从混合内容中提取结构化数据"""
    
    print("=" * 60)
    print("示例 2：XML 标签提取")
    print("=" * 60)
    
    raw_response = """
    你好！关于你的问题，我认为：
    
    <analysis>
    根据数据，Q3 增长了 15%，但 Q4 有所下降。
    主要受季节性因素影响。
    </analysis>
    
    我的结论如下：
    <conclusion>
    建议增加 Q4 营销预算。
    </conclusion>
    
    希望这能帮到你！
    """
    
    print("--- 原始内容 ---")
    print(raw_response)
    
    extractor = XMLExtractor()
    
    analysis = extractor.extract_tag(raw_response, "analysis")
    print(f"\n提取 <analysis>:\n{analysis}")
    
    conclusion = extractor.extract_tag(raw_response, "conclusion")
    print(f"\n提取 <conclusion>:\n{conclusion}")
    
    # 提取所有
    all_data = extractor.extract_all_tags(raw_response)
    print(f"\n提取所有标签:\n{all_data}")
    print()


# ============================================================
# 示例 3：Pydantic 强类型校验
# ============================================================

def example_pydantic_validation():
    """演示 Pydantic 校验机制"""
    
    print("=" * 60)
    print("示例 3：Pydantic 强类型校验")
    print("=" * 60)
    
    # 定义数据模型
    class UserResponse(BaseModel):
        name: str
        age: int
        is_active: bool = True
        tags: list[str]

    validator = PydanticValidator(schema=UserResponse)
    
    # 测试用例
    test_data = [
        {"name": "Alice", "age": 25, "tags": ["admin"]}, # 有效
        {"name": "Bob", "age": "30", "tags": ["user"]}, # age 类型错误
        {"name": "Charlie", "age": 25}, # 缺少 tags
    ]
    
    for i, data in enumerate(test_data, 1):
        print(f"--- 测试 {i}: {data} ---")
        try:
            result = validator.validate_and_fix(data)
            print(f"✅ 校验通过: {result}")
        except ValidationError:
            print("❌ 校验失败")
    print()


# ============================================================
# 示例 4：修复 Prompt 生成
# ============================================================

def generate_fix_prompt(
    original_input: str,
    bad_output: str,
    schema_desc: str,
    error_msg: str
) -> str:
    """
    生成用于修复结构化输出的 Prompt。
    
    参数:
        original_input: 用户的原始问题
        bad_output: 模型生成的错误输出
        schema_desc: JSON Schema 描述
        error_msg: 具体的校验错误信息
    返回:
        修复 Prompt 字符串
    """
    return f"""
# 任务
你之前的输出不符合预期的 JSON 格式。请根据错误信息修正你的回答。

# 原始问题
{original_input}

# 你的错误输出
{bad_output}

# 预期的 JSON Schema
{schema_desc}

# 校验错误
{error_msg}

# 要求
1. 严格遵循 JSON Schema 格式
2. 不要包含任何解释性文字，只输出 JSON
3. 确保所有必填字段都存在且类型正确
"""


def example_fix_prompt():
    """演示修复 Prompt 的生成"""
    
    print("=" * 60)
    print("示例 4：修复 Prompt 生成")
    print("=" * 60)
    
    prompt = generate_fix_prompt(
        original_input="分析这段文本的情感",
        bad_output='{"sentiment": "positive"}',
        schema_desc='{"type": "object", "properties": {"sentiment": {"type": "string"}, "confidence": {"type": "number"}}}',
        error_msg="'confidence' is a required property"
    )
    print(prompt)
    print()


# ============================================================
# 示例 5：三种方案对比总结
# ============================================================

def example_comparison():
    """对比三种结构化输出方案"""
    
    print("=" * 60)
    print("示例 5：三种方案对比总结")
    print("=" * 60)
    
    print(f"{'维度':<15} {'JSON Mode':<15} {'XML 标签':<15} {'Pydantic 校验':<15}")
    print("-" * 60)
    print(f"{'适用场景':<12} {'纯数据返回':<15} {'混合内容':<15} {'高可靠性要求':<15}")
    print(f"{'模型支持':<12} {'OpenAI, etc':<15} {'所有模型':<15} {'所有模型':<15}")
    print(f"{'稳定性':<12} {'高':<15} {'中高':<15} {'最高':<15}")
    print(f"{'实现复杂度':<12} {'极低':<15} {'低':<15} {'高':<15}")
    print(f"{'容错能力':<12} {'无':<15} {'中':<15} {'强':<15}")
    print()


# ============================================================
# 运行所有示例
# ============================================================

if __name__ == "__main__":
    example_json_parsing()
    example_xml_extraction()
    example_pydantic_validation()
    example_fix_prompt()
    example_comparison()
    
    print("=" * 60)
    print("所有示例运行完毕！")
    print("核心要点：鲁棒解析、强类型校验、自动修复")
    print("=" * 60)
