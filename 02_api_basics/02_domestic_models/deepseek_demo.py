"""
DeepSeek API 接入示例

DeepSeek 特点：
- 高性价比（价格约为GPT-4的1/10）
- 代码生成能力强（DeepSeek-Coder）
- 支持128K超长上下文
- 推理能力出色（DeepSeek-R1）
- 完全兼容 OpenAI API 格式

官方文档: https://platform.deepseek.com/api-docs/
"""

import os
from openai import OpenAI


# ============================================================
# 基础对话
# ============================================================

def demo_basic_chat():
    """基础对话示例"""
    
    client = OpenAI(
        base_url="https://api.deepseek.com/v1",
        api_key=os.getenv("DEEPSEEK_API_KEY")
    )
    
    response = client.chat.completions.create(
        model="deepseek-chat",  # 或 deepseek-coder（代码专用）
        messages=[
            {"role": "system", "content": "你是一个技术专家，回答简洁准确"},
            {"role": "user", "content": "什么是微服务架构？"}
        ],
        temperature=0.7,
        max_tokens=800
    )
    
    print("=" * 60)
    print("DeepSeek - 基础对话")
    print("=" * 60)
    print(f"回复: {response.choices[0].message.content}")
    print(f"Token: 输入={response.usage.prompt_tokens}, 输出={response.usage.completion_tokens}\n")


# ============================================================
# 代码生成（DeepSeek-Coder）
# ============================================================

def demo_code_generation():
    """代码生成示例（使用 deepseek-coder 模型）"""
    
    client = OpenAI(
        base_url="https://api.deepseek.com/v1",
        api_key=os.getenv("DEEPSEEK_API_KEY")
    )
    
    response = client.chat.completions.create(
        model="deepseek-coder",  # 代码专用模型
        messages=[
            {
                "role": "user",
                "content": """用Python实现一个LRU缓存类，要求：
1. 支持get和put操作
2. 容量可配置
3. 时间复杂度O(1)
4. 包含详细注释"""
            }
        ],
        temperature=0.3,  # 代码生成用低温度
        max_tokens=1500
    )
    
    print("=" * 60)
    print("DeepSeek - 代码生成")
    print("=" * 60)
    print(response.choices[0].message.content)
    print()


# ============================================================
# 流式输出
# ============================================================

def demo_streaming():
    """流式输出示例"""
    
    client = OpenAI(
        base_url="https://api.deepseek.com/v1",
        api_key=os.getenv("DEEPSEEK_API_KEY")
    )
    
    print("=" * 60)
    print("DeepSeek - 流式输出")
    print("=" * 60)
    print("回复: ", end="", flush=True)
    
    stream = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "user", "content": "用500字介绍Python的异步编程"}
        ],
        stream=True,
        temperature=0.7
    )
    
    for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    
    print("\n")


# ============================================================
# Function Calling
# ============================================================

def demo_function_calling():
    """Function Calling 示例"""
    
    client = OpenAI(
        base_url="https://api.deepseek.com/v1",
        api_key=os.getenv("DEEPSEEK_API_KEY")
    )
    
    # 定义数据库查询工具
    tools = [
        {
            "type": "function",
            "function": {
                "name": "query_database",
                "description": "执行SQL查询并返回结果",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sql": {
                            "type": "string",
                            "description": "SQL查询语句"
                        },
                        "database": {
                            "type": "string",
                            "description": "数据库名称",
                            "enum": ["users", "orders", "products"]
                        }
                    },
                    "required": ["sql", "database"]
                }
            }
        }
    ]
    
    # 模拟数据库查询
    def query_database(sql: str, database: str) -> dict:
        # 实际项目中这里会执行真实SQL
        print(f"  [执行SQL] {database}: {sql}")
        return {
            "rows": 42,
            "sample": [{"id": 1, "name": "张三"}, {"id": 2, "name": "李四"}]
        }
    
    print("=" * 60)
    print("DeepSeek - Function Calling（数据库查询）")
    print("=" * 60)
    
    messages = [
        {"role": "user", "content": "查询users表中所有用户的数量"}
    ]
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    
    msg = response.choices[0].message
    
    if msg.tool_calls:
        print(f"工具调用: {msg.tool_calls[0].function.name}")
        
        import json
        args = json.loads(msg.tool_calls[0].function.arguments)
        result = query_database(**args)
        
        messages.append(msg)
        messages.append({
            "role": "tool",
            "tool_call_id": msg.tool_calls[0].id,
            "content": json.dumps(result, ensure_ascii=False)
        })
        
        final = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages
        )
        
        print(f"\n最终回复: {final.choices[0].message.content}\n")


# ============================================================
# 长文本处理
# ============================================================

def demo_long_context():
    """长文本处理示例（128K上下文）"""
    
    client = OpenAI(
        base_url="https://api.deepseek.com/v1",
        api_key=os.getenv("DEEPSEEK_API_KEY")
    )
    
    # 构造长文本（约10000字）
    long_text = "Python是一门优秀的编程语言。" * 500
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "user",
                "content": f"以下是关于Python的介绍（约{len(long_text)}字）：\n\n{long_text}\n\n请用一句话总结这段文本的主题。"
            }
        ],
        temperature=0.3
    )
    
    print("=" * 60)
    print("DeepSeek - 长文本处理")
    print("=" * 60)
    print(f"输入长度: {len(long_text)} 字符")
    print(f"回复: {response.choices[0].message.content}\n")


# ============================================================
# 运行示例
# ============================================================

if __name__ == "__main__":
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("❌ 请先设置环境变量 DEEPSEEK_API_KEY")
        print("   获取地址: https://platform.deepseek.com/")
        exit(1)
    
    demo_basic_chat()
    # demo_code_generation()
    # demo_streaming()
    # demo_function_calling()
    # demo_long_context()
    
    print("✅ DeepSeek 示例运行完成")
