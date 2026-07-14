"""
通义千问 (Qwen) API 接入示例

通义千问是阿里云推出的大语言模型，特点：
- 多模态能力强（文本+图像+音频）
- 支持超长上下文（128K tokens）
- Function Calling 支持完善
- 完全兼容 OpenAI API 格式

官方文档: https://help.aliyun.com/zh/model-studio/
"""

import os
from openai import OpenAI
from dashscope import Generation
import dashscope


# ============================================================
# 方式一：OpenAI 兼容模式（推荐）
# ============================================================

def demo_openai_compatible():
    """使用 OpenAI SDK 调用通义千问"""
    
    # 初始化客户端
    client = OpenAI(
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key=os.getenv("DASHSCOPE_API_KEY")
    )
    
    # 基础对话
    response = client.chat.completions.create(
        model="qwen-plus",  # 可选：qwen-turbo, qwen-plus, qwen-max
        messages=[
            {"role": "system", "content": "你是一个专业的Python开发助手"},
            {"role": "user", "content": "什么是装饰器？"}
        ],
        temperature=0.7,
        max_tokens=500
    )
    
    print("=" * 60)
    print("通义千问 - OpenAI 兼容模式")
    print("=" * 60)
    print(f"模型: {response.model}")
    print(f"回复: {response.choices[0].message.content}")
    print(f"Token 使用: {response.usage}")
    print()


def demo_streaming():
    """流式输出示例"""
    
    client = OpenAI(
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key=os.getenv("DASHSCOPE_API_KEY")
    )
    
    print("=" * 60)
    print("通义千问 - 流式输出")
    print("=" * 60)
    print("回复: ", end="", flush=True)
    
    stream = client.chat.completions.create(
        model="qwen-plus",
        messages=[
            {"role": "user", "content": "用三句话解释Python的GIL"}
        ],
        stream=True
    )
    
    for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    
    print("\n")


def demo_multimodal():
    """多模态示例（图文理解）"""
    
    client = OpenAI(
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key=os.getenv("DASHSCOPE_API_KEY")
    )
    
    # 使用 qwen-vl-max 模型支持图像理解
    response = client.chat.completions.create(
        model="qwen-vl-max",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "描述这张图片的内容"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "https://dashscope.oss-cn-beijing.aliyuncs.com/images/dog_and_girl.jpeg"
                        }
                    }
                ]
            }
        ]
    )
    
    print("=" * 60)
    print("通义千问 - 多模态（图文理解）")
    print("=" * 60)
    print(f"回复: {response.choices[0].message.content}\n")


def demo_function_calling():
    """Function Calling 示例"""
    
    client = OpenAI(
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key=os.getenv("DASHSCOPE_API_KEY")
    )
    
    # 定义工具
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_stock_price",
                "description": "获取股票实时价格",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "股票代码，如：600519.SH"
                        }
                    },
                    "required": ["symbol"]
                }
            }
        }
    ]
    
    # 模拟股票API
    def get_stock_price(symbol: str) -> dict:
        mock_data = {
            "600519.SH": {"price": 1688.50, "change": "+2.3%"},
            "000001.SZ": {"price": 12.35, "change": "-0.5%"}
        }
        return mock_data.get(symbol, {"price": 0, "change": "N/A"})
    
    print("=" * 60)
    print("通义千问 - Function Calling")
    print("=" * 60)
    
    # 第一轮：模型决定调用工具
    messages = [
        {"role": "user", "content": "茅台股票现在多少钱？"}
    ]
    
    response = client.chat.completions.create(
        model="qwen-plus",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    
    msg = response.choices[0].message
    
    if msg.tool_calls:
        print(f"模型调用工具: {msg.tool_calls[0].function.name}")
        
        # 执行工具
        import json
        args = json.loads(msg.tool_calls[0].function.arguments)
        result = get_stock_price(**args)
        
        print(f"工具返回: {result}")
        
        # 第二轮：将工具结果返回给模型
        messages.append(msg)
        messages.append({
            "role": "tool",
            "tool_call_id": msg.tool_calls[0].id,
            "content": json.dumps(result, ensure_ascii=False)
        })
        
        final_response = client.chat.completions.create(
            model="qwen-plus",
            messages=messages
        )
        
        print(f"\n最终回复: {final_response.choices[0].message.content}\n")


# ============================================================
# 方式二：官方 SDK 模式（DashScope）
# ============================================================

def demo_dashscope_sdk():
    """使用 DashScope 官方 SDK"""
    
    # 设置 API Key
    dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
    
    # 调用模型
    response = Generation.call(
        model="qwen-plus",
        messages=[
            {"role": "system", "content": "你是一个友好的AI助手"},
            {"role": "user", "content": "讲一个关于程序员的笑话"}
        ],
        result_format="message"
    )
    
    print("=" * 60)
    print("通义千问 - DashScope SDK 模式")
    print("=" * 60)
    
    if response.status_code == 200:
        print(f"回复: {response.output.choices[0].message.content}")
        print(f"请求ID: {response.request_id}\n")
    else:
        print(f"错误: {response.code} - {response.message}\n")


# ============================================================
# 运行示例
# ============================================================

if __name__ == "__main__":
    # 检查 API Key
    if not os.getenv("DASHSCOPE_API_KEY"):
        print("❌ 请先设置环境变量 DASHSCOPE_API_KEY")
        print("   获取地址: https://dashscope.console.aliyun.com/apiKey")
        exit(1)
    
    # 运行各个示例（取消注释需要的示例）
    demo_openai_compatible()
    # demo_streaming()
    # demo_multimodal()
    # demo_function_calling()
    # demo_dashscope_sdk()
    
    print("✅ 通义千问示例运行完成")
