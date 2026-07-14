"""
FastAPI + SSE 流式转发服务 - Web后端实战

本模块演示如何在FastAPI后端中接收用户请求，
调用大模型API获取流式响应，并通过SSE协议转发给前端。
这是构建AI聊天应用最常用的架构模式。

架构：
    前端（浏览器）→ FastAPI后端 → 大模型API
        ↑                ↓
     SSE流式接收     SSE流式转发

运行方式：
    uvicorn fastapi_sse_server:app --reload --port 8000

测试方式（curl）：
    curl -N http://localhost:8000/api/chat/stream?message=你好
"""

import os
from typing import Dict, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from openai import AsyncOpenAI


# --- 配置管理 ---

class AppConfig:
    """应用配置（从环境变量读取）"""

    API_KEY: str = os.getenv("LLM_API_KEY", "")
    BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
    MODEL: str = os.getenv("LLM_MODEL", "deepseek-chat")
    MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "2048"))


# --- 请求数据模型 ---

class ChatRequest(BaseModel):
    """聊天请求体（Pydantic模型，自动校验）

    Attributes:
        message: 用户输入的消息
        system_prompt: 系统提示词（可选）
        temperature: 温度参数（0.0-2.0）
        history: 对话历史（用于多轮对话）
    """

    message: str = Field(..., min_length=1, max_length=4000)
    system_prompt: str = Field(default="你是一个有用的助手。", max_length=1000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    history: List[Dict[str, str]] = Field(default_factory=list)


# --- 应用初始化 ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时初始化客户端，关闭时清理资源"""
    # 启动时：创建异步OpenAI客户端
    app.state.client = AsyncOpenAI(
        api_key=AppConfig.API_KEY,
        base_url=AppConfig.BASE_URL,
    )
    yield
    # 关闭时：清理客户端连接
    await app.state.client.close()


app = FastAPI(
    title="AI Chat SSE Server",
    description="基于SSE协议的AI聊天流式服务",
    version="1.0.0",
    lifespan=lifespan,
)


# --- SSE流式生成器 ---

async def generate_sse_stream(request: ChatRequest):
    """SSE流式响应生成器

    将大模型的流式响应转换为SSE协议格式，
    逐块推送给前端浏览器。

    SSE协议要求每条消息格式为：
        data: {"content": "xxx"}\n\n

    Args:
        request: 聊天请求参数

    Yields:
        SSE格式的消息字符串
    """
    client: AsyncOpenAI = app.state.client

    # 构建完整消息列表
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": request.system_prompt},
    ]

    # 添加历史对话（多轮上下文）
    for msg in request.history:
        messages.append(msg)

    # 添加当前用户消息
    messages.append({"role": "user", "content": request.message})

    try:
        # 发起异步流式请求
        stream = await client.chat.completions.create(
            model=AppConfig.MODEL,
            messages=messages,
            temperature=request.temperature,
            max_tokens=AppConfig.MAX_TOKENS,
            stream=True,
        )

        # 逐块转发为SSE格式
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content

                # SSE消息格式：data: {json}\n\n
                sse_data = f'data: {{"content": "{content}"}}\n\n'
                yield sse_data

        # 流结束标记
        yield 'data: {"done": true}\n\n'

    except Exception as e:
        # 错误也通过SSE返回给前端
        yield f'data: {{"error": "{str(e)}"}}\n\n'


# --- API路由 ---

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """流式聊天接口（POST）

    接收JSON请求体，返回SSE流式响应。
    前端使用EventSource或fetch + ReadableStream接收。

    Args:
        request: 聊天请求参数

    Returns:
        StreamingResponse: SSE流式响应
    """
    return StreamingResponse(
        generate_sse_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用Nginx缓冲
        },
    )


@app.get("/api/chat/stream")
async def chat_stream_get(
    message: str,
    system_prompt: str = "你是一个有用的助手。",
    temperature: float = 0.7,
):
    """流式聊天接口（GET，方便curl测试）

    使用URL参数传递消息，适用于简单测试。

    Args:
        message: 用户消息
        system_prompt: 系统提示词
        temperature: 温度参数

    Returns:
        StreamingResponse: SSE流式响应
    """
    request = ChatRequest(
        message=message,
        system_prompt=system_prompt,
        temperature=temperature,
    )
    return StreamingResponse(
        generate_sse_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "model": AppConfig.MODEL}


# --- 启动入口 ---
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "fastapi_sse_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
