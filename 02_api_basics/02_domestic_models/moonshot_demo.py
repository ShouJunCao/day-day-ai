"""
Moonshot (Kimi) API 接入示例

Moonshot 特点：
- 超长上下文（200K tokens，业界领先）
- 文档理解能力强
- 支持联网搜索
- 中文能力优秀
- 完全兼容 OpenAI API 格式

官方文档: https://platform.moonshot.cn/docs/intro
"""

import os
from openai import OpenAI


# ============================================================
# 基础对话
# ============================================================

def demo_basic_chat():
    """基础对话示例"""
    
    client = OpenAI(
        base_url="https://api.moonshot.cn/v1",
        api_key=os.getenv("MOONSHOT_API_KEY")
    )
    
    # 可选模型：moonshot-v1-8k, moonshot-v1-32k, moonshot-v1-128k
    response = client.chat.completions.create(
        model="moonshot-v1-8k",
        messages=[
            {"role": "system", "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手"},
            {"role": "user", "content": "介绍一下你自己"}
        ],
        temperature=0.7
    )
    
    print("=" * 60)
    print("Moonshot - 基础对话")
    print("=" * 60)
    print(f"回复: {response.choices[0].message.content}")
    print(f"Token: {response.usage}\n")


# ============================================================
# 超长文本处理（核心优势）
# ============================================================

def demo_long_context():
    """超长文本处理示例（200K上下文）"""
    
    client = OpenAI(
        base_url="https://api.moonshot.cn/v1",
        api_key=os.getenv("MOONSHOT_API_KEY")
    )
    
    # 构造超长文本（约50000字）
    # 实际项目中可以是完整的文档、书籍章节等
    long_text = """
    Python是一门高级编程语言，由Guido van Rossum于1989年发明。
    Python的设计哲学强调代码的可读性和简洁性。
    Python支持多种编程范式，包括面向对象、命令式、函数式编程。
    """ * 1000  # 重复1000次，约30000字
    
    print("=" * 60)
    print("Moonshot - 超长文本处理")
    print("=" * 60)
    print(f"输入文本长度: {len(long_text)} 字符")
    
    response = client.chat.completions.create(
        model="moonshot-v1-128k",  # 使用128K上下文版本
        messages=[
            {
                "role": "user",
                "content": f"以下是一段关于Python的介绍（约{len(long_text)}字）：\n\n{long_text[:10000]}...\n\n请总结这段文本的主要内容，并回答：Python的核心设计理念是什么？"
            }
        ],
        temperature=0.3
    )
    
    print(f"回复: {response.choices[0].message.content}\n")


# ============================================================
# 文件理解（通过API上传文件）
# ============================================================

def demo_file_understanding():
    """文件理解示例"""
    
    client = OpenAI(
        base_url="https://api.moonshot.cn/v1",
        api_key=os.getenv("MOONSHOT_API_KEY")
    )
    
    # 步骤1：上传文件
    # 注意：Moonshot的文件上传使用独立的API
    # 这里演示的是通过文件ID引用已上传的文件
    
    print("=" * 60)
    print("Moonshot - 文件理解")
    print("=" * 60)
    
    # 假设文件已上传，获得file_id
    # file_id = "file-xxxxx"
    
    # 在对话中引用文件
    response = client.chat.completions.create(
        model="moonshot-v1-32k",
        messages=[
            {
                "role": "system",
                "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手。"
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请阅读这个文件并总结主要内容"
                    },
                    {
                        "type": "file",
                        "file": {
                            "file_id": "file-xxxxx"  # 替换为实际file_id
                        }
                    }
                ]
            }
        ]
    )
    
    print(f"回复: {response.choices[0].message.content}\n")


# ============================================================
# 联网搜索
# ============================================================

def demo_web_search():
    """联网搜索示例"""
    
    client = OpenAI(
        base_url="https://api.moonshot.cn/v1",
        api_key=os.getenv("MOONSHOT_API_KEY")
    )
    
    # Moonshot 支持在 system prompt 中启用联网搜索
    response = client.chat.completions.create(
        model="moonshot-v1-8k",
        messages=[
            {
                "role": "system",
                "content": """你是 Kimi，由 Moonshot AI 提供的人工智能助手。
你能够通过联网搜索获取最新信息。
当用户询问需要最新数据的问题时，请使用联网搜索功能。"""
            },
            {
                "role": "user",
                "content": "今天北京的天气怎么样？"
            }
        ],
        temperature=0.7,
        # 启用联网搜索（Moonshot特有参数）
        extra_body={
            "tools": [
                {
                    "type": "builtin_function",
                    "function": {
                        "name": "$web_search"
                    }
                }
            ]
        }
    )
    
    print("=" * 60)
    print("Moonshot - 联网搜索")
    print("=" * 60)
    print(f"回复: {response.choices[0].message.content}\n")


# ============================================================
# 流式输出
# ============================================================

def demo_streaming():
    """流式输出示例"""
    
    client = OpenAI(
        base_url="https://api.moonshot.cn/v1",
        api_key=os.getenv("MOONSHOT_API_KEY")
    )
    
    print("=" * 60)
    print("Moonshot - 流式输出")
    print("=" * 60)
    print("回复: ", end="", flush=True)
    
    stream = client.chat.completions.create(
        model="moonshot-v1-8k",
        messages=[
            {"role": "user", "content": "写一篇关于人工智能未来发展的短文"}
        ],
        stream=True,
        temperature=0.7
    )
    
    for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    
    print("\n")


# ============================================================
# 运行示例
# ============================================================

if __name__ == "__main__":
    if not os.getenv("MOONSHOT_API_KEY"):
        print("❌ 请先设置环境变量 MOONSHOT_API_KEY")
        print("   获取地址: https://platform.moonshot.cn/")
        exit(1)
    
    demo_basic_chat()
    # demo_long_context()
    # demo_file_understanding()
    # demo_web_search()
    # demo_streaming()
    
    print("✅ Moonshot 示例运行完成")
