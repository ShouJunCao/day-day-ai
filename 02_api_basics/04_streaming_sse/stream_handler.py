"""
完整流式处理器 - 支持多轮对话、内容拼接和流式回调

本模块提供一个生产级的流式处理器，除了基础的流式输出，
还支持：
    - 多轮对话上下文管理
    - 回调函数机制（进度通知、token计数）
    - 完整响应的自动拼接
    - 流式中断检测

典型场景：
    - Web后端通过WebSocket转发流式响应给前端
    - CLI工具实时显示生成进度
    - 日志记录每次API调用的token用量
"""

import os
import time
from typing import Generator, Dict, List, Callable, Optional
from dataclasses import dataclass, field

from openai import OpenAI, APIError


@dataclass
class StreamEvent:
    """流式事件数据类

    封装每次流式回调的元数据，方便上层处理逻辑。

    Attributes:
        content: 本次收到的文本片段
        is_start: 是否为第一个片段（流开始标志）
        is_end: 是否为最后一个片段（流结束标志）
        chunk_index: 当前是第几个片段（从0开始）
        elapsed_seconds: 从请求发出到当前片段的耗时
    """

    content: str = ""
    is_start: bool = False
    is_end: bool = False
    chunk_index: int = 0
    elapsed_seconds: float = 0.0


class StreamHandler:
    """流式对话处理器

    相比基础客户端，增加了：
    1. 多轮对话上下文自动管理
    2. 事件回调机制（on_chunk, on_start, on_end）
    3. 完整响应自动拼接，方便后续使用
    4. 性能统计（首token延迟、总耗时、吞吐量）

    Example:
        handler = StreamHandler(api_key="...")

        def on_progress(event: StreamEvent):
            if event.is_start:
                print(f"开始响应... (首token延迟: {event.elapsed_seconds:.2f}s)")
            print(event.content, end="", flush=True)

        handler.on_chunk = on_progress
        response = handler.chat("你好")
        print(f"\\n完整响应长度: {len(response)} 字符")
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
    ):
        """初始化流式处理器

        Args:
            api_key: API密钥
            base_url: API基础URL
            model: 模型名称
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

        # 对话历史（用于多轮对话）
        self.history: List[Dict[str, str]] = []

        # 回调函数
        self.on_start: Optional[Callable[[StreamEvent], None]] = None
        self.on_chunk: Optional[Callable[[StreamEvent], None]] = None
        self.on_end: Optional[Callable[[StreamEvent, str], None]] = None

    def chat(
        self,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """多轮流式对话接口

        自动维护对话历史，支持上下文关联的多轮对话。

        Args:
            user_message: 用户输入的消息
            temperature: 温度参数
            max_tokens: 最大输出token数

        Returns:
            完整的模型响应文本
        """
        # 添加用户消息到历史
        self.history.append({"role": "user", "content": user_message})

        start_time = time.time()
        full_response = ""
        chunk_index = 0
        first_token_time = None

        # 发起流式请求
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=self.history,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        # 处理流式响应
        for chunk in stream:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta
            if not delta.content:
                continue

            content = delta.content
            elapsed = time.time() - start_time

            # 记录首token延迟
            if first_token_time is None:
                first_token_time = elapsed
                if self.on_start:
                    event = StreamEvent(
                        content=content,
                        is_start=True,
                        is_end=False,
                        chunk_index=chunk_index,
                        elapsed_seconds=elapsed,
                    )
                    self.on_start(event)
            else:
                # 普通片段回调
                if self.on_chunk:
                    event = StreamEvent(
                        content=content,
                        is_start=False,
                        is_end=False,
                        chunk_index=chunk_index,
                        elapsed_seconds=elapsed,
                    )
                    self.on_chunk(event)

            # 拼接完整响应
            full_response += content
            chunk_index += 1

        # 结束回调
        total_elapsed = time.time() - start_time
        if self.on_end:
            end_event = StreamEvent(
                content="",
                is_start=False,
                is_end=True,
                chunk_index=chunk_index,
                elapsed_seconds=total_elapsed,
            )
            self.on_end(end_event, full_response)

        # 将助手响应添加到历史
        self.history.append({"role": "assistant", "content": full_response})

        return full_response

    def clear_history(self) -> None:
        """清空对话历史，开始新对话"""
        self.history.clear()


# --- 使用示例 ---
if __name__ == "__main__":
    api_key = os.getenv("DEEPSEEK_API_KEY", "")

    handler = StreamHandler(
        api_key=api_key,
        base_url="https://api.deepseek.com/v1",
        model="deepseek-chat",
    )

    # 注册回调函数
    def on_start(event: StreamEvent):
        print(f"[首token延迟: {event.elapsed_seconds:.2f}s]")
        print("模型: ", end="", flush=True)

    def on_chunk(event: StreamEvent):
        print(event.content, end="", flush=True)

    def on_end(event: StreamEvent, full_text: str):
        char_per_sec = len(full_text) / event.elapsed_seconds
        print(f"\n[总耗时: {event.elapsed_seconds:.2f}s | "
              f"片段数: {event.chunk_index} | "
              f"速度: {char_per_sec:.0f} 字符/秒]")

    handler.on_start = on_start
    handler.on_chunk = on_chunk
    handler.on_end = on_end

    # 多轮对话测试
    print("=" * 50)
    print("第一轮对话")
    print("=" * 50)
    handler.chat("我叫小明，我是一名Python开发者")

    print("\n" + "=" * 50)
    print("第二轮对话（测试上下文记忆）")
    print("=" * 50)
    handler.chat("我叫什么名字？我的职业是什么？")
