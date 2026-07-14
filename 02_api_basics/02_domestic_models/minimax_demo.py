"""
MiniMax API 接入示例

MiniMax 特点：
- 语音合成能力突出（TTS）
- 角色扮演和情景对话
- 多模态支持
- 支持 Function Calling
- 完全兼容 OpenAI API 格式

官方文档: https://www.minimaxi.com/document/introduction
"""

import os
from openai import OpenAI


# ============================================================
# 基础对话
# ============================================================

def demo_basic_chat():
    """基础对话示例"""
    
    client = OpenAI(
        base_url="https://api.minimax.chat/v1",
        api_key=os.getenv("MINIMAX_API_KEY")
    )
    
    response = client.chat.completions.create(
        model="abab6.5-chat",  # 可选：abab5.5-chat, abab6.5-chat
        messages=[
            {"role": "system", "content": "你是一个友好的AI助手"},
            {"role": "user", "content": "你好，介绍一下MiniMax"}
        ],
        temperature=0.7,
        max_tokens=500
    )
    
    print("=" * 60)
    print("MiniMax - 基础对话")
    print("=" * 60)
    print(f"回复: {response.choices[0].message.content}")
    print(f"Token: {response.usage}\n")


# ============================================================
# 角色扮演（MiniMax特色）
# ============================================================

def demo_role_play():
    """角色扮演示例"""
    
    client = OpenAI(
        base_url="https://api.minimax.chat/v1",
        api_key=os.getenv("MINIMAX_API_KEY")
    )
    
    # MiniMax 在角色扮演场景表现出色
    response = client.chat.completions.create(
        model="abab6.5-chat",
        messages=[
            {
                "role": "system",
                "content": """你是一个名叫小明的程序员，性格幽默风趣。
你热爱编程，经常加班到深夜。
你喜欢喝咖啡，讨厌开会。
说话风格轻松随意，偶尔会用一些网络流行语。"""
            },
            {"role": "user", "content": "今天工作怎么样？"}
        ],
        temperature=0.9,  # 角色扮演用高温度
        max_tokens=800
    )
    
    print("=" * 60)
    print("MiniMax - 角色扮演")
    print("=" * 60)
    print(f"小明: {response.choices[0].message.content}\n")


# ============================================================
# 流式输出
# ============================================================

def demo_streaming():
    """流式输出示例"""
    
    client = OpenAI(
        base_url="https://api.minimax.chat/v1",
        api_key=os.getenv("MINIMAX_API_KEY")
    )
    
    print("=" * 60)
    print("MiniMax - 流式输出")
    print("=" * 60)
    print("回复: ", end="", flush=True)
    
    stream = client.chat.completions.create(
        model="abab6.5-chat",
        messages=[
            {"role": "user", "content": "讲一个关于程序员的搞笑故事"}
        ],
        stream=True,
        temperature=0.8
    )
    
    for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    
    print("\n")


# ============================================================
# Function Calling
# ============================================================

def demo_function_calling():
    """Function Calling 示例"""
    
    client = OpenAI(
        base_url="https://api.minimax.chat/v1",
        api_key=os.getenv("MINIMAX_API_KEY")
    )
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "play_music",
                "description": "播放指定的音乐",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "song_name": {
                            "type": "string",
                            "description": "歌曲名称"
                        },
                        "artist": {
                            "type": "string",
                            "description": "歌手名称"
                        }
                    },
                    "required": ["song_name"]
                }
            }
        }
    ]
    
    def play_music(song_name: str, artist: str = "未知") -> dict:
        print(f"  [播放音乐] {song_name} - {artist}")
        return {"status": "playing", "song": song_name, "artist": artist}
    
    print("=" * 60)
    print("MiniMax - Function Calling")
    print("=" * 60)
    
    messages = [
        {"role": "user", "content": "帮我播放周杰伦的晴天"}
    ]
    
    response = client.chat.completions.create(
        model="abab6.5-chat",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    
    msg = response.choices[0].message
    
    if msg.tool_calls:
        print(f"工具调用: {msg.tool_calls[0].function.name}")
        
        import json
        args = json.loads(msg.tool_calls[0].function.arguments)
        result = play_music(**args)
        
        messages.append(msg)
        messages.append({
            "role": "tool",
            "tool_call_id": msg.tool_calls[0].id,
            "content": json.dumps(result, ensure_ascii=False)
        })
        
        final = client.chat.completions.create(
            model="abab6.5-chat",
            messages=messages
        )
        
        print(f"\n最终回复: {final.choices[0].message.content}\n")


# ============================================================
# 运行示例
# ============================================================

if __name__ == "__main__":
    if not os.getenv("MINIMAX_API_KEY"):
        print("❌ 请先设置环境变量 MINIMAX_API_KEY")
        print("   获取地址: https://www.minimaxi.com/")
        exit(1)
    
    demo_basic_chat()
    # demo_role_play()
    # demo_streaming()
    # demo_function_calling()
    
    print("✅ MiniMax 示例运行完成")
