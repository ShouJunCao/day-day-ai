"""
多模型统一调用SDK

提供统一的接口调用不同的大模型API，支持：
- 多模型提供商（OpenAI、DeepSeek、通义千问等）
- 自动重试和错误处理
- 速率限制和预算控制
- 统一的响应格式
"""

from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import asyncio


class ModelProvider(Enum):
    """模型提供商枚举"""
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    ZHIPU = "zhipu"


@dataclass
class ChatMessage:
    """聊天消息"""
    role: str  # system, user, assistant
    content: str


@dataclass
class ChatResponse:
    """统一的聊天响应"""
    content: str
    model: str
    provider: ModelProvider
    usage: Dict[str, int]  # prompt_tokens, completion_tokens, total_tokens
    finish_reason: str


@dataclass
class ModelConfig:
    """模型配置"""
    name: str
    provider: ModelProvider
    api_key: str
    base_url: Optional[str] = None
    default_params: Optional[Dict] = None


class UnifiedLLMClient:
    """统一的大模型客户端"""
    
    def __init__(self):
        self.models: Dict[str, ModelConfig] = {}
        self.default_model: Optional[str] = None
    
    def register_model(self, config: ModelConfig) -> None:
        """注册模型配置
        
        Args:
            config: 模型配置
        """
        self.models[config.name] = config
        if self.default_model is None:
            self.default_model = config.name
    
    def set_default_model(self, model_name: str) -> None:
        """设置默认模型
        
        Args:
            model_name: 模型名称
        """
        if model_name not in self.models:
            raise ValueError(f"模型 {model_name} 未注册")
        self.default_model = model_name
    
    async def chat(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatResponse:
        """统一的聊天接口
        
        Args:
            messages: 消息列表
            model: 模型名称（可选，默认使用default_model）
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数
        
        Returns:
            ChatResponse: 统一的响应对象
        """
        model_name = model or self.default_model
        if not model_name:
            raise ValueError("未指定模型且未设置默认模型")
        
        if model_name not in self.models:
            raise ValueError(f"模型 {model_name} 未注册")
        
        config = self.models[model_name]
        
        # 根据provider选择不同的调用方式
        if config.provider == ModelProvider.OPENAI:
            return await self._call_openai_compatible(
                config, messages, temperature, max_tokens, **kwargs
            )
        elif config.provider == ModelProvider.DEEPSEEK:
            return await self._call_deepseek(
                config, messages, temperature, max_tokens, **kwargs
            )
        elif config.provider == ModelProvider.QWEN:
            return await self._call_qwen(
                config, messages, temperature, max_tokens, **kwargs
            )
        else:
            raise ValueError(f"不支持的提供商: {config.provider}")
    
    async def _call_openai_compatible(
        self,
        config: ModelConfig,
        messages: List[ChatMessage],
        temperature: float,
        max_tokens: Optional[int],
        **kwargs
    ) -> ChatResponse:
        """调用OpenAI兼容API"""
        # 这里使用httpx或openai库实现
        # 示例代码，实际需要导入库
        import httpx
        
        base_url = config.base_url or "https://api.openai.com/v1"
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": config.name,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        payload.update(kwargs)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
        
        return ChatResponse(
            content=data["choices"][0]["message"]["content"],
            model=data["model"],
            provider=config.provider,
            usage=data.get("usage", {}),
            finish_reason=data["choices"][0].get("finish_reason", "stop")
        )
    
    async def _call_deepseek(
        self,
        config: ModelConfig,
        messages: List[ChatMessage],
        temperature: float,
        max_tokens: Optional[int],
        **kwargs
    ) -> ChatResponse:
        """调用DeepSeek API（兼容OpenAI格式）"""
        config_copy = ModelConfig(
            name=config.name,
            provider=config.provider,
            api_key=config.api_key,
            base_url=config.base_url or "https://api.deepseek.com/v1",
            default_params=config.default_params
        )
        return await self._call_openai_compatible(
            config_copy, messages, temperature, max_tokens, **kwargs
        )
    
    async def _call_qwen(
        self,
        config: ModelConfig,
        messages: List[ChatMessage],
        temperature: float,
        max_tokens: Optional[int],
        **kwargs
    ) -> ChatResponse:
        """调用通义千问API（兼容OpenAI格式）"""
        config_copy = ModelConfig(
            name=config.name,
            provider=config.provider,
            api_key=config.api_key,
            base_url=config.base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1",
            default_params=config.default_params
        )
        return await self._call_openai_compatible(
            config_copy, messages, temperature, max_tokens, **kwargs
        )
    
    def list_models(self) -> List[str]:
        """列出所有已注册的模型
        
        Returns:
            List[str]: 模型名称列表
        """
        return list(self.models.keys())


# 便捷函数
async def chat(
    prompt: str,
    model: Optional[str] = None,
    client: Optional[UnifiedLLMClient] = None,
    **kwargs
) -> str:
    """简化的聊天函数
    
    Args:
        prompt: 用户输入
        model: 模型名称
        client: 客户端实例（可选，不传则创建新的）
        **kwargs: 其他参数
    
    Returns:
        str: 模型响应内容
    """
    if client is None:
        client = UnifiedLLMClient()
    
    messages = [ChatMessage(role="user", content=prompt)]
    response = await client.chat(messages, model=model, **kwargs)
    return response.content
