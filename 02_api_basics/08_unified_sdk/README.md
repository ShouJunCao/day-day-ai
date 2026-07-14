# 多模型统一调用 SDK

一个简洁实用的Python SDK，用于统一调用不同的大模型API。

## 核心特性

- **统一接口**：所有模型使用相同的API调用方式
- **多提供商支持**：OpenAI、DeepSeek、通义千问等
- **灵活配置**：支持环境变量和配置文件
- **异步设计**：基于asyncio，高性能并发
- **类型安全**：完整的类型提示

## 项目结构

```
08_unified_sdk/
├── llm_sdk.py           # 核心SDK实现
├── example_usage.py     # 使用示例
├── config_example.py    # 配置管理示例
└── README.md           # 项目说明
```

## 快速开始

### 1. 安装依赖

```bash
pip install httpx
```

### 2. 基础使用

```python
import asyncio
from llm_sdk import UnifiedLLMClient, ModelConfig, ModelProvider, ChatMessage

async def main():
    # 创建客户端
    client = UnifiedLLMClient()
    
    # 注册模型
    client.register_model(ModelConfig(
        name="gpt-4",
        provider=ModelProvider.OPENAI,
        api_key="your-api-key"
    ))
    
    # 发送消息
    messages = [
        ChatMessage(role="user", content="你好！")
    ]
    
    response = await client.chat(messages)
    print(response.content)

asyncio.run(main())
```

### 3. 多模型对比

```python
async def compare_models():
    client = UnifiedLLMClient()
    
    # 注册多个模型
    client.register_model(ModelConfig(
        name="gpt-4",
        provider=ModelProvider.OPENAI,
        api_key="openai-key"
    ))
    
    client.register_model(ModelConfig(
        name="deepseek-chat",
        provider=ModelProvider.DEEPSEEK,
        api_key="deepseek-key"
    ))
    
    # 同一个问题，不同模型回答
    messages = [ChatMessage(role="user", content="什么是机器学习？")]
    
    for model in ["gpt-4", "deepseek-chat"]:
        response = await client.chat(messages, model=model)
        print(f"{model}: {response.content}")
```

## 配置方式

### 方式1：环境变量

```bash
export OPENAI_API_KEY=***
export DEEPSEEK_API_KEY=***
export QWEN_API_KEY=***
```

```python
from config_example import load_from_env

client = load_from_env()
```

### 方式2：配置字典

```python
from config_example import load_from_dict

config = {
    "models": [
        {
            "name": "gpt-4",
            "provider": "openai",
            "api_key": "your-key"
        }
    ]
}

client = load_from_dict(config)
```

## 高级用法

### 自定义参数

```python
response = await client.chat(
    messages,
    model="gpt-4",
    temperature=0.8,
    max_tokens=500
)
```

### 多轮对话

```python
messages = [
    ChatMessage(role="system", content="你是一个助手"),
    ChatMessage(role="user", content="你好"),
    ChatMessage(role="assistant", content="你好！有什么可以帮助你的？"),
    ChatMessage(role="user", content="今天天气怎么样？")
]

response = await client.chat(messages)
```

## API 参考

### UnifiedLLMClient

- `register_model(config: ModelConfig)` - 注册模型
- `set_default_model(model_name: str)` - 设置默认模型
- `chat(messages, model, temperature, max_tokens, **kwargs)` - 发送聊天请求
- `list_models()` - 列出所有已注册模型

### ModelConfig

- `name: str` - 模型名称
- `provider: ModelProvider` - 提供商类型
- `api_key: str` - API密钥
- `base_url: Optional[str]` - API基础URL
- `default_params: Optional[Dict]` - 默认参数

### ChatMessage

- `role: str` - 角色（system/user/assistant）
- `content: str` - 消息内容

### ChatResponse

- `content: str` - 响应内容
- `model: str` - 使用的模型
- `provider: ModelProvider` - 提供商
- `usage: Dict` - Token使用情况
- `finish_reason: str` - 结束原因

## 设计原则

1. **简洁**：API设计简单直观
2. **统一**：不同模型使用相同的接口
3. **灵活**：支持多种配置方式
4. **可扩展**：易于添加新的提供商
5. **生产就绪**：异步设计，类型安全

## 注意事项

- 所有API调用都是异步的，需要使用`await`
- API Key请妥善保管，不要硬编码在代码中
- 建议使用环境变量或配置文件管理密钥
- 生产环境建议添加错误处理和重试机制
