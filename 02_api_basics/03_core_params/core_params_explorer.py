"""
API 核心参数实验

本模块通过实验演示各个核心参数对模型输出的影响：
1. temperature - 控制输出随机性
2. top_p - 核采样，控制词汇多样性
3. max_tokens - 最大输出 token 数
4. stop sequences - 停止序列
5. presence_penalty / frequency_penalty - 惩罚参数
6. seed - 随机种子，实现确定性输出

运行方式：
    python3 core_params_explorer.py --param temperature --values 0.0,0.5,1.0,1.5,2.0
    python3 core_params_explorer.py --param top_p --values 0.1,0.5,0.9,1.0
    python3 core_params_explorer.py --param penalty --presence 0,1,2 --frequency 0,1,2
    python3 core_params_explorer.py --demo stop_sequences
    python3 core_params_explorer.py --demo seed_determinism
"""

import argparse
import os
import sys
from collections import Counter
from openai import OpenAI


def create_client() -> OpenAI:
    """创建 OpenAI 兼容客户端（默认使用通义千问）"""
    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY", "sk-placeholder")
    base_url = os.getenv("API_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    return OpenAI(base_url=base_url, api_key=api_key)


# ============================================================
# 实验 1：temperature 对比
# ============================================================

def experiment_temperature(client: OpenAI, prompt: str,
                           temperatures: list[float], runs: int = 3):
    """
    对比不同 temperature 下模型输出的多样性。

    temperature=0.0 → 几乎确定性，每次输出相似
    temperature=0.7 → 平衡创造性和准确性（推荐默认值）
    temperature=1.0 → 标准随机性
    temperature=1.5 → 高随机性，可能出现不连贯
    temperature=2.0 → 极高随机性，输出可能混乱

    Args:
        client: OpenAI 客户端
        prompt: 提示词
        temperatures: 要测试的 temperature 值列表
        runs: 每个 temperature 运行次数
    """
    model = os.getenv("MODEL_NAME", "qwen-plus")
    print(f"{'='*60}")
    print(f"实验：temperature 对比 | prompt: {prompt[:50]}...")
    print(f"{'='*60}\n")

    for temp in temperatures:
        print(f"\n📊 temperature = {temp}")
        print("-" * 40)
        outputs = []
        for i in range(runs):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temp,
                    max_tokens=100,
                )
                text = response.choices[0].message.content.strip()
                outputs.append(text)
                print(f"  Run {i+1}: {text[:80]}...")
            except Exception as e:
                print(f"  Run {i+1}: ❌ Error - {e}")

        # 计算多样性
        unique = len(set(outputs))
        print(f"\n  多样性: {unique}/{runs} 个不同的输出")


# ============================================================
# 实验 2：top_p 对比
# ============================================================

def experiment_top_p(client: OpenAI, prompt: str,
                     top_p_values: list[float], runs: int = 3):
    """
    对比不同 top_p 下模型输出的多样性。

    top_p=0.1 → 仅从概率最高的 10% token 中采样，输出保守
    top_p=0.5 → 从概率最高的 50% token 中采样
    top_p=0.9 → 从概率最高的 90% token 中采样（推荐值）
    top_p=1.0 → 从所有 token 中采样（等价于不限制）

    注意：top_p 和 temperature 通常只调一个，不要同时调。

    Args:
        client: OpenAI 客户端
        prompt: 提示词
        top_p_values: 要测试的 top_p 值列表
        runs: 每个 top_p 运行次数
    """
    model = os.getenv("MODEL_NAME", "qwen-plus")
    print(f"{'='*60}")
    print(f"实验：top_p 对比 | prompt: {prompt[:50]}...")
    print(f"{'='*60}\n")

    for top_p in top_p_values:
        print(f"\n📊 top_p = {top_p}")
        print("-" * 40)
        outputs = []
        for i in range(runs):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    top_p=top_p,
                    temperature=1.0,  # 固定 temperature
                    max_tokens=100,
                )
                text = response.choices[0].message.content.strip()
                outputs.append(text)
                print(f"  Run {i+1}: {text[:80]}...")
            except Exception as e:
                print(f"  Run {i+1}: ❌ Error - {e}")

        unique = len(set(outputs))
        print(f"\n  多样性: {unique}/{runs} 个不同的输出")


# ============================================================
# 实验 3：stop sequences
# ============================================================

def demo_stop_sequences(client: OpenAI):
    """
    演示 stop sequences（停止序列）的用法。

    stop sequences 用于在模型输出特定字符串时立即停止生成，
    常用于：
    - 控制输出格式（如在特定标记处停止）
    - 防止模型继续生成多余内容
    - 实现结构化输出的边界控制

    示例：让模型生成一个 JSON 对象，在 "}" 后立即停止。
    """
    model = os.getenv("MODEL_NAME", "qwen-plus")
    print(f"{'='*60}")
    print("实验：stop sequences 演示")
    print(f"{'='*60}\n")

    # 示例 1：在特定字符串处停止
    print("📊 示例 1：在 '\\n---' 处停止")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": "列出3个Python内置数据类型，每个占一行，然后在末尾写上 ---"}
        ],
        stop=["\n---"],
        max_tokens=200,
    )
    print(f"输出: {response.choices[0].message.content}")
    print(f"停止原因: {response.choices[0].finish_reason}\n")

    # 示例 2：多个停止序列
    print("📊 示例 2：多个停止序列 ['。', '.', '\\n']")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": "用一句话解释什么是机器学习。"}
        ],
        stop=["。", "."],
        max_tokens=200,
    )
    print(f"输出: {response.choices[0].message.content}")
    print(f"停止原因: {response.choices[0].finish_reason}\n")


# ============================================================
# 实验 4：seed 确定性输出
# ============================================================

def demo_seed_determinism(client: OpenAI):
    """
    演示 seed 参数实现确定性输出。

    设置相同的 seed 值，在相同输入下模型应该返回相同或非常相似的输出。
    这对于调试和测试非常有用。

    注意：seed 参数并不能保证 100% 确定性，只是大大提高确定性。
    """
    model = os.getenv("MODEL_NAME", "qwen-plus")
    print(f"{'='*60}")
    print("实验：seed 确定性输出")
    print(f"{'='*60}\n")

    prompt = "用一句话介绍Python"
    seed_value = 42

    print(f"📊 使用 seed={seed_value} 运行 3 次：")
    outputs_with_seed = []
    for i in range(3):
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            seed=seed_value,
            temperature=0.7,
            max_tokens=100,
        )
        text = response.choices[0].message.content.strip()
        outputs_with_seed.append(text)
        print(f"  Run {i+1}: {text}")

    print(f"\n  相同输出数: {outputs_with_seed.count(outputs_with_seed[0])}/3")

    print(f"\n📊 不使用 seed 运行 3 次（对比）：")
    outputs_no_seed = []
    for i in range(3):
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=100,
        )
        text = response.choices[0].message.content.strip()
        outputs_no_seed.append(text)
        print(f"  Run {i+1}: {text}")

    print(f"\n  相同输出数: {outputs_no_seed.count(outputs_no_seed[0])}/3")


# ============================================================
# 实验 5：penalty 参数
# ============================================================

def experiment_penalties(client: OpenAI, prompt: str,
                         presence_values: list[float],
                         frequency_values: list[float]):
    """
    对比 presence_penalty 和 frequency_penalty 的效果。

    presence_penalty: 惩罚已出现过的 token（鼓励讨论新话题）
    - 取值范围: -2.0 到 2.0
    - 正值：鼓励模型讨论新话题
    - 负值：鼓励模型重复已有话题

    frequency_penalty: 按出现频率惩罚 token（减少重复）
    - 取值范围: -2.0 到 2.0
    - 正值：减少模型重复相同的词句
    - 负值：鼓励模型重复

    Args:
        client: OpenAI 客户端
        prompt: 提示词
        presence_values: presence_penalty 测试值
        frequency_values: frequency_penalty 测试值
    """
    model = os.getenv("MODEL_NAME", "qwen-plus")
    print(f"{'='*60}")
    print(f"实验：penalty 参数对比")
    print(f"{'='*60}\n")

    for pp in presence_values:
        for fp in frequency_values:
            print(f"\n📊 presence_penalty={pp}, frequency_penalty={fp}")
            print("-" * 40)
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    presence_penalty=pp,
                    frequency_penalty=fp,
                    temperature=0.9,
                    max_tokens=200,
                )
                text = response.choices[0].message.content.strip()
                print(f"  输出: {text[:150]}...")

                # 统计重复词
                words = text.split()
                counter = Counter(words)
                repeated = sum(1 for w, c in counter.items() if c > 1)
                print(f"  重复词数: {repeated}/{len(counter)}")
            except Exception as e:
                print(f"  ❌ Error - {e}")


# ============================================================
# 参数推荐配置
# ============================================================

def get_recommended_params(scenario: str) -> dict:
    """
    根据场景返回推荐的参数配置。

    常见场景：
    - code_generation: 代码生成（低温度，高确定性）
    - creative_writing: 创意写作（高温度，高多样性）
    - factual_qa: 事实问答（低温度，准确优先）
    - chatbot: 聊天机器人（中等温度，平衡）
    - structured_output: 结构化输出（低温度 + stop sequences）
    """
    configs = {
        "code_generation": {
            "temperature": 0.2,
            "top_p": 0.95,
            "max_tokens": 2000,
            "presence_penalty": 0.0,
            "frequency_penalty": 0.0,
        },
        "creative_writing": {
            "temperature": 0.9,
            "top_p": 0.95,
            "max_tokens": 1500,
            "presence_penalty": 0.5,
            "frequency_penalty": 0.3,
        },
        "factual_qa": {
            "temperature": 0.3,
            "top_p": 0.9,
            "max_tokens": 800,
            "presence_penalty": 0.0,
            "frequency_penalty": 0.0,
        },
        "chatbot": {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 1000,
            "presence_penalty": 0.1,
            "frequency_penalty": 0.1,
        },
        "structured_output": {
            "temperature": 0.1,
            "top_p": 0.95,
            "max_tokens": 500,
            "stop": ["}\n", "```"],
            "presence_penalty": 0.0,
            "frequency_penalty": 0.0,
        },
    }
    return configs.get(scenario, configs["chatbot"])


# ============================================================
# 主程序
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="API 核心参数实验工具")
    parser.add_argument("--param", choices=["temperature", "top_p", "penalty"],
                        help="要测试的参数")
    parser.add_argument("--values", type=str, default="",
                        help="参数值列表（逗号分隔）")
    parser.add_argument("--presence", type=str, default="0,1",
                        help="presence_penalty 测试值")
    parser.add_argument("--frequency", type=str, default="0,1",
                        help="frequency_penalty 测试值")
    parser.add_argument("--demo", choices=["stop_sequences", "seed_determinism"],
                        help="运行特定演示")
    parser.add_argument("--prompt", type=str,
                        default="给我讲一个关于程序员的短故事",
                        help="测试用提示词")
    parser.add_argument("--runs", type=int, default=3, help="每个参数运行次数")

    args = parser.parse_args()

    client = create_client()

    if args.demo == "stop_sequences":
        demo_stop_sequences(client)
    elif args.demo == "seed_determinism":
        demo_seed_determinism(client)
    elif args.param == "temperature":
        values = [float(v) for v in args.values.split(",")] if args.values else [0.0, 0.5, 1.0, 1.5]
        experiment_temperature(client, args.prompt, values, args.runs)
    elif args.param == "top_p":
        values = [float(v) for v in args.values.split(",")] if args.values else [0.1, 0.5, 0.9, 1.0]
        experiment_top_p(client, args.prompt, values, args.runs)
    elif args.param == "penalty":
        pp = [float(v) for v in args.presence.split(",")]
        fp = [float(v) for v in args.frequency.split(",")]
        experiment_penalties(client, args.prompt, pp, fp)
    else:
        print("用法示例：")
        print("  python3 core_params_explorer.py --param temperature --values 0.0,0.7,1.0,1.5")
        print("  python3 core_params_explorer.py --param top_p --values 0.1,0.5,0.9")
        print("  python3 core_params_explorer.py --demo stop_sequences")
        print("  python3 core_params_explorer.py --demo seed_determinism")
        print("  python3 core_params_explorer.py --param penalty --presence 0,1 --frequency 0,1")
