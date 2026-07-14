"""
异步流式客户端 - 基于asyncio的高并发流式处理

在Web服务和API网关场景下，异步流式处理能显著提升并发性能。
本模块演示如何使用httpx和asyncio实现非阻塞的SSE流式读取，
适用于需要同时处理多个流式请求的场景（如多模型并发调用）。

核心优势：
    - 非阻塞I/O：不占用线程等待网络响应
    - 高并发：单线程即可处理数百个并发流
    - 与FastAPI/Starlette天然兼容

适用场景：
    - Web后端转发流式响应
    - 多模型并行调用与结果聚合
    - 实时聊天系统的后端推送
"""

import os
import asyncio
import json
from typing import AsyncGenerator, Dict, List

import httpx


class AsyncStreamClient:
    """异步流式客户端

    使用httpx的异步API直接发送HTTP请求，手动解析SSE数据流。
    相比同步客户端，在高并发场景下性能提升显著。

    Attributes:
        api_key: API密钥
        base_url: API基础URL
        model: 模型名称
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
    ):
        """初始化异步流式客户端

        Args:
            api_key: API密钥
            base_url: API基础URL
            model: 模型名称
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    def _build_headers(self) -> Dict[str, str]:
        """构建HTTP请求头

        Returns:
            包含认证和Content-Type的请求头字典
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _build_payload(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> Dict:
        """构建请求体

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数

        Returns:
            JSON请求体字典
        """
        return {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

    async def stream_chat(
        self,
        user_message: str,
        system_prompt: str = "你是一个有用的助手。",
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncGenerator[str, None]:
        """异步流式对话接口

        Args:
            user_message: 用户消息
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大token数

        Yields:
            每次返回一个文本片段
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        url = f"{self.base_url}/chat/completions"
        headers = self._build_headers()
        payload = self._build_payload(messages, temperature, max_tokens)

        # 使用httpx异步流式请求
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST", url, json=payload, headers=headers
            ) as response:
                response.raise_for_status()

                # 逐行读取SSE数据流
                async for line in response.aiter_lines():
                    # SSE协议：跳过空行和注释行
                    if not line.strip() or line.startswith(":"):
                        continue

                    # 解析 "data: {...}" 格式
                    if line.startswith("data: "):
                        data_str = line[6:]  # 去掉 "data: " 前缀

                        # [DONE] 表示流结束
                        if data_str.strip() == "[DONE]":
                            break

                        try:
                            data = json.loads(data_str)
                            choices = data.get("choices", [])

                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content

                        except json.JSONDecodeError:
                            # 跳过解析失败的行
                            continue


async def demo_parallel_streams():
    """演示：并发调用多个模型（并行流式请求）

    这个示例展示了异步的优势：
    同时向不同模型发起流式请求，互不阻塞。
    """
    api_key = os.getenv("DEEPSEEK_API_KEY", "")

    # 配置多个模型（这里用同一个API演示）
    models = [
        ("DeepSeek-Chat", "deepseek-chat"),
        ("DeepSeek-Reasoner", "deepseek-reasoner"),
    ]

    async def query_model(name: str, model_id: str, question: str):
        """查询单个模型并收集完整响应"""
        client = AsyncStreamClient(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1",
            model=model_id,
        )

        full_text = ""
        async for chunk in client.stream_chat(question):
            full_text += chunk

        return name, full_text

    # 并发发起多个流式请求
    question = "用一句话概括Python的GIL是什么"
    tasks = [
        query_model(name, model_id, question)
        for name, model_id in models
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 打印结果
    for result in results:
        if isinstance(result, Exception):
            print(f"❌ 错误: {result}")
        else:
            name, text = result
            print(f"\n📦 {name}:")
            print(f"   {text[:200]}...")


# --- 运行入口 ---
if __name__ == "__main__":
    asyncio.run(demo_parallel_streams())
