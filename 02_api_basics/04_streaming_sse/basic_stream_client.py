"""
基础流式客户端 - 实现大模型API的SSE流式调用

本模块演示如何使用OpenAI兼容API进行流式输出，
包含完整的错误处理和类型提示。

用法：
    client = BasicStreamClient(api_key="your-key", base_url="https://api.deepseek.com/v1")
    for chunk in client.stream_chat("你好，介绍一下自己"):
        print(chunk, end="", flush=True)
"""

import os
import json
from typing import Generator, Dict, List, Optional

from openai import OpenAI, APIError


class BasicStreamClient:
    """基础流式对话客户端

    支持OpenAI兼容API的流式输出，适用于DeepSeek、Qwen、Zhipu等模型。
    通过stream=True参数启用SSE协议，逐token接收模型响应。

    Attributes:
        client: OpenAI客户端实例
        model: 使用的模型名称
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
    ):
        """初始化流式客户端

        Args:
            api_key: API密钥
            base_url: API基础URL（不同提供商地址不同）
            model: 模型名称
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def stream_chat(
        self,
        user_message: str,
        system_prompt: str = "你是一个有用的助手。",
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> Generator[str, None, None]:
        """流式对话接口，逐token返回模型响应

        Args:
            user_message: 用户输入的消息
            system_prompt: 系统提示词
            temperature: 温度参数，控制输出随机性（0.0-2.0）
            max_tokens: 最大输出token数

        Yields:
            每次返回一个文本片段（通常是一个token或几个字符）

        Raises:
            APIError: API调用失败时抛出
        """
        # 构建消息列表
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        # 发起流式请求
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,  # 关键：启用流式输出
        )

        # 逐块读取响应
        for chunk in stream:
            # 检查是否有内容块
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                yield content


# --- 使用示例 ---
if __name__ == "__main__":
    # 从环境变量读取API密钥
    api_key = os.getenv("DEEPSEEK_API_KEY", "")

    client = BasicStreamClient(
        api_key=api_key,
        base_url="https://api.deepseek.com/v1",
        model="deepseek-chat",
    )

    print("模型回复：", end="", flush=True)
    for text in client.stream_chat("用一句话解释什么是SSE协议"):
        print(text, end="", flush=True)

    print("\n\n✅ 流式输出完成")
