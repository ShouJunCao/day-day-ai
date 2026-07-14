"""
统一SDK使用示例
"""

import asyncio
from llm_sdk import (
    UnifiedLLMClient,
    ModelConfig,
    ModelProvider,
    ChatMessage,
)


async def example_basic_usage():
    """基础使用示例"""
    print("=" * 50)
    print("示例1: 基础使用")
    print("=" * 50)
    
    # 创建客户端
    client = UnifiedLLMClient()
    
    # 注册模型
    client.register_model(ModelConfig(
        name="gpt-3.5-turbo",
        provider=ModelProvider.OPENAI,
        api_key="your-openai-api-key"
    ))
    
    client.register_model(ModelConfig(
        name="deepseek-chat",
        provider=ModelProvider.DEEPSEEK,
        api_key="your-deepseek-api-key"
    ))
    
    # 简单对话
    messages = [
        ChatMessage(role="system", content="你是一个有用的助手"),
        ChatMessage(role="user", content="什么是机器学习？")
    ]
    
    response = await client.chat(messages)
    print(f"模型: {response.model}")
    print(f"提供商: {response.provider.value}")
    print(f"响应: {response.content}")
    print(f"Token使用: {response.usage}")
    print()


async def example_multi_model():
    """多模型对比示例"""
    print("=" * 50)
    print("示例2: 多模型对比")
    print("=" * 50)
    
    client = UnifiedLLMClient()
    
    # 注册多个模型
    client.register_model(ModelConfig(
        name="gpt-4",
        provider=ModelProvider.OPENAI,
        api_key="your-openai-api-key"
    ))
    
    client.register_model(ModelConfig(
        name="deepseek-chat",
        provider=ModelProvider.DEEPSEEK,
        api_key="your-deepseek-api-key"
    ))
    
    client.register_model(ModelConfig(
        name="qwen-plus",
        provider=ModelProvider.QWEN,
        api_key="your-qwen-api-key"
    ))
    
    # 同一个问题，不同模型回答
    question = "用一句话解释什么是神经网络"
    messages = [ChatMessage(role="user", content=question)]
    
    models = ["gpt-4", "deepseek-chat", "qwen-plus"]
    
    for model_name in models:
        try:
            response = await client.chat(messages, model=model_name)
            print(f"\n{response.model}:")
            print(f"  {response.content}")
        except Exception as e:
            print(f"\n{model_name}: 调用失败 - {e}")
    
    print()


async def example_custom_params():
    """自定义参数示例"""
    print("=" * 50)
    print("示例3: 自定义参数")
    print("=" * 50)
    
    client = UnifiedLLMClient()
    client.register_model(ModelConfig(
        name="gpt-4",
        provider=ModelProvider.OPENAI,
        api_key="your-openai-api-key"
    ))
    
    messages = [ChatMessage(role="user", content="写一首关于春天的诗")]
    
    # 使用不同的温度参数
    for temp in [0.0, 0.7, 1.5]:
        response = await client.chat(
            messages,
            temperature=temp,
            max_tokens=100
        )
        print(f"\n温度 {temp}:")
        print(f"  {response.content}")
    
    print()


async def example_conversation():
    """多轮对话示例"""
    print("=" * 50)
    print("示例4: 多轮对话")
    print("=" * 50)
    
    client = UnifiedLLMClient()
    client.register_model(ModelConfig(
        name="gpt-3.5-turbo",
        provider=ModelProvider.OPENAI,
        api_key="your-openai-api-key"
    ))
    
    # 构建对话历史
    messages = [
        ChatMessage(role="system", content="你是一个Python编程专家"),
    ]
    
    # 第一轮
    messages.append(ChatMessage(role="user", content="什么是装饰器？"))
    response1 = await client.chat(messages)
    messages.append(ChatMessage(role="assistant", content=response1.content))
    print(f"第1轮:\n  {response1.content}\n")
    
    # 第二轮（基于上下文）
    messages.append(ChatMessage(role="user", content="能给个简单的例子吗？"))
    response2 = await client.chat(messages)
    messages.append(ChatMessage(role="assistant", content=response2.content))
    print(f"第2轮:\n  {response2.content}\n")
    
    # 第三轮
    messages.append(ChatMessage(role="user", content="什么时候应该使用装饰器？"))
    response3 = await client.chat(messages)
    print(f"第3轮:\n  {response3.content}\n")


async def main():
    """运行所有示例"""
    print("\n" + "=" * 50)
    print("统一SDK使用示例")
    print("=" * 50 + "\n")
    
    # 注意：这些示例需要真实的API Key才能运行
    # 这里只是展示用法，不会真正调用API
    
    print("提示：运行这些示例需要配置真实的API Key\n")
    
    await example_basic_usage()
    await example_multi_model()
    await example_custom_params()
    await example_conversation()
    
    print("=" * 50)
    print("所有示例展示完毕")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
