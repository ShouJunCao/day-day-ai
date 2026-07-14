"""
国内主流模型统一客户端

提供一个统一的接口调用所有国内大模型，支持：
- 通义千问 (Qwen)
- DeepSeek
- 智谱 GLM
- Moonshot (Kimi)
- MiniMax

使用方式：
    client = DomesticLLMClient("qwen")
    response = client.chat("你好")
"""

import os
from openai import OpenAI
from typing import Optional, List, Dict


class DomesticLLMClient:
    """国内大模型统一客户端"""
    
    # 各模型的配置信息
    MODEL_CONFIGS = {
        "qwen": {
            "name": "通义千问",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "model": "qwen-plus",
            "env_key": "DASHSCOPE_API_KEY",
            "features": ["多模态", "长文本", "Function Calling"],
        },
        "deepseek": {
            "name": "DeepSeek",
            "base_url": "https://api.deepseek.com/v1",
            "model": "deepseek-chat",
            "env_key": "DEEPSEEK_API_KEY",
            "features": ["高性价比", "代码能力强", "长上下文"],
        },
        "zhipu": {
            "name": "智谱 GLM",
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "model": "glm-4",
            "env_key": "ZHIPU_API_KEY",
            "features": ["中文优化", "多模态", "知识图谱"],
        },
        "moonshot": {
            "name": "Moonshot (Kimi)",
            "base_url": "https://api.moonshot.cn/v1",
            "model": "moonshot-v1-8k",
            "env_key": "MOONSHOT_API_KEY",
            "features": ["超长上下文", "文档理解", "联网搜索"],
        },
        "minimax": {
            "name": "MiniMax",
            "base_url": "https://api.minimax.chat/v1",
            "model": "abab6.5-chat",
            "env_key": "MINIMAX_API_KEY",
            "features": ["语音合成", "角色扮演", "多模态"],
        },
    }
    
    def __init__(self, provider: str):
        """
        初始化客户端
        
        Args:
            provider: 模型提供商，可选值：qwen/deepseek/zhipu/moonshot/minimax
        """
        if provider not in self.MODEL_CONFIGS:
            raise ValueError(f"不支持的模型: {provider}，可选: {list(self.MODEL_CONFIGS.keys())}")
        
        self.provider = provider
        self.config = self.MODEL_CONFIGS[provider]
        
        # 从环境变量获取 API Key
        api_key = os.getenv(self.config["env_key"])
        if not api_key:
            raise ValueError(f"请设置环境变量 {self.config['env_key']}")
        
        # 创建 OpenAI 兼容客户端
        self.client = OpenAI(
            base_url=self.config["base_url"],
            api_key=api_key
        )
        
        print(f"✅ {self.config['name']} 客户端初始化成功")
        print(f"   模型: {self.config['model']}")
        print(f"   特性: {', '.join(self.config['features'])}")
    
    def chat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stream: bool = False
    ):
        """
        发送对话请求
        
        Args:
            message: 用户消息
            system_prompt: 系统提示词
            history: 历史消息列表
            temperature: 温度参数
            max_tokens: 最大输出token数
            stream: 是否流式输出
            
        Returns:
            模型响应内容
        """
        # 构建消息列表
        messages = []
        
        # 添加系统提示
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # 添加历史消息
        if history:
            messages.extend(history)
        
        # 添加当前用户消息
        messages.append({"role": "user", "content": message})
        
        # 调用模型
        if stream:
            return self._stream_chat(messages, temperature, max_tokens)
        else:
            return self._sync_chat(messages, temperature, max_tokens)
    
    def _sync_chat(self, messages: List[Dict], temperature: float, max_tokens: int) -> str:
        """同步调用"""
        response = self.client.chat.completions.create(
            model=self.config["model"],
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    
    def _stream_chat(self, messages: List[Dict], temperature: float, max_tokens: int):
        """流式调用（生成器）"""
        stream = self.client.chat.completions.create(
            model=self.config["model"],
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


# 使用示例
if __name__ == "__main__":
    # 测试所有模型
    providers = ["qwen", "deepseek", "zhipu", "moonshot", "minimax"]
    
    for provider in providers:
        try:
            print(f"\n{'='*50}")
            client = DomesticLLMClient(provider)
            
            # 简单对话
            response = client.chat("用一句话介绍你自己")
            print(f"\n回复: {response}\n")
            
        except Exception as e:
            print(f"❌ {provider} 测试失败: {e}")
