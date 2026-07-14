"""
智谱 GLM API 接入示例

智谱 GLM 特点：
- 中文能力优化
- 多模态支持（文本+图像）
- 知识图谱能力
- 支持 Function Calling
- 完全兼容 OpenAI API 格式

官方文档: https://open.bigmodel.cn/dev/howuse/introduction
"""

import os
from openai import OpenAI
from zhipuai import ZhipuAI


# ============================================================
# 方式一：OpenAI 兼容模式（推荐）
# ============================================================

def demo_openai_compatible():
    """使用 OpenAI SDK 调用智谱 GLM"""
    
    client = OpenAI(
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.getenv("ZHIPU_API_KEY")
    )
    
    response = client.chat.completions.create(
        model="glm-4",  # 可选：glm-3-turbo, glm-4, glm-4v（多模态）
        messages=[
            {"role": "system", "content": "你是一个知识渊博的AI助手"},
            {"role": "user", "content": "解释一下什么是知识图谱"}
        ],
        temperature=0.7,
        max_tokens=800
    )
    
    print("=" * 60)
    print("智谱 GLM - OpenAI 兼容模式")
    print("=" * 60)
    print(f"回复: {response.choices[0].message.content}")
    print(f"Token: {response.usage}\n")


# ============================================================
# 方式二：官方 SDK 模式
# ============================================================

def demo_zhipuai_sdk():
    """使用智谱官方 SDK"""
    
    client = ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY"))
    
    response = client.chat.completions.create(
        model="glm-4",
        messages=[
            {"role": "user", "content": "用Python写一个快速排序算法"}
        ],
        temperature=0.7
    )
    
    print("=" * 60)
    print("智谱 GLM - 官方 SDK 模式")
    print("=" * 60)
    print(response.choices[0].message.content)
    print()


# ============================================================
# 多模态（图文理解）
# ============================================================

def demo_multimodal():
    """多模态示例（使用 glm-4v 模型）"""
    
    client = OpenAI(
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.getenv("ZHIPU_API_KEY")
    )
    
    response = client.chat.completions.create(
        model="glm-4v",  # 多模态模型
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "这张图片里有什么？"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "https://open.bigmodel.cn/api/paas/v4/images/1"
                        }
                    }
                ]
            }
        ]
    )
    
    print("=" * 60)
    print("智谱 GLM - 多模态")
    print("=" * 60)
    print(f"回复: {response.choices[0].message.content}\n")


# ============================================================
# Function Calling
# ============================================================

def demo_function_calling():
    """Function Calling 示例"""
    
    client = OpenAI(
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.getenv("ZHIPU_API_KEY")
    )
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "search_knowledge_base",
                "description": "搜索知识库获取相关信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索关键词"
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "返回结果数量",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]
    
    def search_knowledge_base(query: str, top_k: int = 5) -> dict:
        print(f"  [搜索知识库] query={query}, top_k={top_k}")
        return {
            "results": [
                {"title": "知识图谱基础", "content": "知识图谱是一种结构化知识表示方法..."},
                {"title": "RAG技术", "content": "检索增强生成结合了检索和生成..."}
            ]
        }
    
    print("=" * 60)
    print("智谱 GLM - Function Calling")
    print("=" * 60)
    
    messages = [
        {"role": "user", "content": "帮我查一下知识图谱和RAG的资料"}
    ]
    
    response = client.chat.completions.create(
        model="glm-4",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    
    msg = response.choices[0].message
    
    if msg.tool_calls:
        print(f"工具调用: {msg.tool_calls[0].function.name}")
        
        import json
        args = json.loads(msg.tool_calls[0].function.arguments)
        result = search_knowledge_base(**args)
        
        messages.append(msg)
        messages.append({
            "role": "tool",
            "tool_call_id": msg.tool_calls[0].id,
            "content": json.dumps(result, ensure_ascii=False)
        })
        
        final = client.chat.completions.create(
            model="glm-4",
            messages=messages
        )
        
        print(f"\n最终回复: {final.choices[0].message.content}\n")


# ============================================================
# 运行示例
# ============================================================

if __name__ == "__main__":
    if not os.getenv("ZHIPU_API_KEY"):
        print("❌ 请先设置环境变量 ZHIPU_API_KEY")
        print("   获取地址: https://open.bigmodel.cn/")
        exit(1)
    
    demo_openai_compatible()
    # demo_zhipuai_sdk()
    # demo_multimodal()
    # demo_function_calling()
    
    print("✅ 智谱 GLM 示例运行完成")
