"""
带重试机制的流式客户端 - 处理网络抖动和API限流

在真实生产环境中，API调用可能因网络抖动、限流（429）或
服务端临时故障而失败。本模块实现指数退避重试策略，
确保流式输出的可靠性。

核心设计：
    - 指数退避：重试间隔按 1s, 2s, 4s... 递增
    - 幂等判断：仅对可重试的错误（网络超时、429限流）重试
    - 流式安全：一旦开始接收数据，不再重试（避免重复输出）
"""

import os
import time
import logging
from typing import Generator, Dict, List, Set

from openai import OpenAI, APIError, RateLimitError, APITimeoutError

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 可重试的HTTP状态码
RETRYABLE_STATUS_CODES: Set[int] = {429, 500, 502, 503, 504}


class RetryStreamClient:
    """带重试机制的流式客户端

    在基础流式客户端的基础上，增加了指数退避重试策略。
    关键设计：只在请求发出前重试，一旦开始接收流数据，
    就不再重试，避免部分内容被重复输出。

    Attributes:
        client: OpenAI客户端实例
        model: 使用的模型名称
        max_retries: 最大重试次数
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        max_retries: int = 3,
        base_delay: float = 1.0,
    ):
        """初始化带重试的流式客户端

        Args:
            api_key: API密钥
            base_url: API基础URL
            model: 模型名称
            max_retries: 最大重试次数，默认3次
            base_delay: 基础延迟时间（秒），用于指数退避计算
        """
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=30.0,  # 请求超时30秒
        )
        self.model = model
        self.max_retries = max_retries
        self.base_delay = base_delay

    def _should_retry(self, error: Exception, attempt: int) -> bool:
        """判断当前错误是否应该重试

        Args:
            error: 捕获的异常对象
            attempt: 当前重试次数

        Returns:
            True表示应该重试，False表示应该放弃
        """
        # 超过最大重试次数，不再重试
        if attempt >= self.max_retries:
            return False

        # 限流错误（429）可以重试
        if isinstance(error, RateLimitError):
            return True

        # 超时错误可以重试
        if isinstance(error, APITimeoutError):
            return True

        # 其他API错误，检查状态码
        if isinstance(error, APIError):
            status = getattr(error, "status_code", None)
            return status in RETRYABLE_STATUS_CODES

        return False

    def _calculate_delay(self, attempt: int) -> float:
        """计算重试延迟时间（指数退避）

        公式：base_delay * (2 ^ attempt)
        示例：attempt=0 → 1s, attempt=1 → 2s, attempt=2 → 4s

        Args:
            attempt: 当前重试次数（从0开始）

        Returns:
            延迟秒数
        """
        return self.base_delay * (2 ** attempt)

    def stream_chat(
        self,
        user_message: str,
        system_prompt: str = "你是一个有用的助手。",
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        """流式对话接口，带自动重试

        Args:
            user_message: 用户输入的消息
            system_prompt: 系统提示词
            temperature: 温度参数

        Yields:
            每次返回一个文本片段
        """
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        # 重试循环
        for attempt in range(self.max_retries + 1):
            try:
                logger.info(f"发起请求（第 {attempt + 1} 次）")

                stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    stream=True,
                )

                # 开始流式读取
                # 注意：一旦进入这个循环，就不再重试
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content

                # 成功完成，直接返回
                return

            except Exception as e:
                if self._should_retry(e, attempt):
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"请求失败: {e}，{delay}秒后重试..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"请求失败且不可重试: {e}")
                    raise


# --- 使用示例 ---
if __name__ == "__main__":
    api_key = os.getenv("DEEPSEEK_API_KEY", "")

    client = RetryStreamClient(
        api_key=api_key,
        base_url="https://api.deepseek.com/v1",
        model="deepseek-chat",
        max_retries=3,
        base_delay=1.0,
    )

    print("模型回复：", end="", flush=True)
    for text in client.stream_chat("Python的装饰器是什么？请简要解释"):
        print(text, end="", flush=True)

    print("\n\n✅ 流式输出完成")
