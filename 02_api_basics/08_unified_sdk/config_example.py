"""
配置管理示例

展示如何从环境变量或配置文件加载模型配置
"""

import os
from typing import Dict
from llm_sdk import UnifiedLLMClient, ModelConfig, ModelProvider


def load_from_env() -> UnifiedLLMClient:
    """从环境变量加载配置
    
    环境变量格式：
        OPENAI_API_KEY=***        DEEPSEEK_API_KEY=***        QWEN_API_KEY=***    """
    client = UnifiedLLMClient()
    
    # OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        client.register_model(ModelConfig(
            name="gpt-4",
            provider=ModelProvider.OPENAI,
            api_key=openai_key
        ))
        client.register_model(ModelConfig(
            name="gpt-3.5-turbo",
            provider=ModelProvider.OPENAI,
            api_key=openai_key
        ))
    
    # DeepSeek
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    if deepseek_key:
        client.register_model(ModelConfig(
            name="deepseek-chat",
            provider=ModelProvider.DEEPSEEK,
            api_key=deepseek_key
        ))
    
    # 通义千问
    qwen_key = os.getenv("QWEN_API_KEY")
    if qwen_key:
        client.register_model(ModelConfig(
            name="qwen-plus",
            provider=ModelProvider.QWEN,
            api_key=qwen_key
        ))
    
    return client


def load_from_dict(config_dict: Dict) -> UnifiedLLMClient:
    """从字典加载配置
    
    配置字典格式：
        {
            "models": [
                {
                    "name": "gpt-4",
                    "provider": "openai",
                    "api_key": "sk-xxx",
                    "base_url": "https://api.openai.com/v1"
                },
                ...
            ]
        }
    """
    client = UnifiedLLMClient()
    
    for model_config in config_dict.get("models", []):
        provider_str = model_config["provider"]
        provider = ModelProvider(provider_str)
        
        config = ModelConfig(
            name=model_config["name"],
            provider=provider,
            api_key=model_config["api_key"],
            base_url=model_config.get("base_url"),
            default_params=model_config.get("default_params")
        )
        client.register_model(config)
    
    return client


# 示例配置字典
EXAMPLE_CONFIG = {
    "models": [
        {
            "name": "gpt-4",
            "provider": "openai",
            "api_key": "your-openai-key",
            "default_params": {
                "temperature": 0.7,
                "max_tokens": 1000
            }
        },
        {
            "name": "deepseek-chat",
            "provider": "deepseek",
            "api_key": "your-deepseek-key",
            "base_url": "https://api.deepseek.com/v1"
        },
        {
            "name": "qwen-plus",
            "provider": "qwen",
            "api_key": "your-qwen-key",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
        }
    ]
}


if __name__ == "__main__":
    # 从环境变量加载
    print("从环境变量加载:")
    client1 = load_from_env()
    print(f"  已注册模型: {client1.list_models()}")
    print()
    
    # 从字典加载
    print("从字典加载:")
    client2 = load_from_dict(EXAMPLE_CONFIG)
    print(f"  已注册模型: {client2.list_models()}")
    print()
