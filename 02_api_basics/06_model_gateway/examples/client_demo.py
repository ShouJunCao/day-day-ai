"""
客户端使用示例

演示如何通过多模型网关调用API
"""

import asyncio
from openai import OpenAI, AsyncOpenAI


def example_sync_client():
    """同步客户端示例"""
    print("=" * 50)
    print("示例1：同步客户端调用")
    print("=" * 50)
    
    # 创建客户端，指向网关地址
    client = OpenAI(
        api_key="dummy-key",  # 网关会验证真实API Key
        base_url="http://localhost:8000/v1"
    )
    
    # 发送请求（自动路由）
    response = client.chat.completions.create(
        model="auto",  # 自动选择模型
        messages=[
            {"role": "system", "content": "你是一个有用的助手"},
            {"role": "user", "content": "你好，请介绍一下自己"}
        ],
        temperature=0.7,
        max_tokens=200
    )
    
    print(f"使用模型: {response.model}")
    print(f"回复: {response.choices[0].message.content}")
    print(f"Token用量: {response.usage}")
    print()


def example_specific_model():
    """指定特定模型"""
    print("=" * 50)
    print("示例2：指定特定模型")
    print("=" * 50)
    
    client = OpenAI(
        api_key="dummy-key",
        base_url="http://localhost:8000/v1"
    )
    
    # 指定使用deepseek-chat
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "user", "content": "用Python写一个快速排序算法"}
        ],
        temperature=0.5
    )
    
    print(f"使用模型: {response.model}")
    print(f"回复: {response.choices[0].message.content[:200]}...")
    print()


async def example_async_client():
    """异步客户端示例"""
    print("=" * 50)
    print("示例3：异步客户端调用")
    print("=" * 50)
    
    client = AsyncOpenAI(
        api_key="dummy-key",
        base_url="http://localhost:8000/v1"
    )
    
    response = await client.chat.completions.create(
        model="auto",
        messages=[
            {"role": "user", "content": "解释什么是API网关"}
        ]
    )
    
    print(f"使用模型: {response.model}")
    print(f"回复: {response.choices[0].message.content}")
    print()


async def example_concurrent_requests():
    """并发请求示例"""
    print("=" * 50)
    print("示例4：并发请求（测试负载均衡）")
    print("=" * 50)
    
    client = AsyncOpenAI(
        api_key="dummy-key",
        base_url="http://localhost:8000/v1"
    )
    
    questions = [
        "什么是机器学习？",
        "Python的优势是什么？",
        "解释RESTful API",
        "什么是微服务架构？",
        "数据库索引的作用"
    ]
    
    # 并发发送5个请求
    tasks = []
    for q in questions:
        task = client.chat.completions.create(
            model="auto",
            messages=[{"role": "user", "content": q}],
            max_tokens=100
        )
        tasks.append(task)
    
    responses = await asyncio.gather(*tasks)
    
    for i, (q, r) in enumerate(zip(questions, responses), 1):
        print(f"问题{i}: {q}")
        print(f"模型: {r.model}")
        print(f"回复: {r.choices[0].message.content[:100]}...")
        print()


def example_list_models():
    """列出可用模型"""
    print("=" * 50)
    print("示例5：列出可用模型")
    print("=" * 50)
    
    client = OpenAI(
        api_key="dummy-key",
        base_url="http://localhost:8000/v1"
    )
    
    models = client.models.list()
    
    print("可用模型列表:")
    for model in models.data:
        print(f"  - {model.id} (所有者: {model.owned_by})")
    print()


if __name__ == "__main__":
    # 同步示例
    try:
        example_sync_client()
        example_specific_model()
        example_list_models()
    except Exception as e:
        print(f"同步示例错误（网关未启动？）: {e}")
        print("请先启动网关: python main.py")
        print()
    
    # 异步示例
    try:
        asyncio.run(example_async_client())
        asyncio.run(example_concurrent_requests())
    except Exception as e:
        print(f"异步示例错误（网关未启动？）: {e}")
        print("请先启动网关: python main.py")
