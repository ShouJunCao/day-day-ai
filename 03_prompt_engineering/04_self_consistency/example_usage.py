"""
example_usage.py — 自洽性引擎使用示例

演示:
1. 基础自洽性推理
2. 早期终止机制
3. 答案规范化效果
4. 缓存复用
"""

from self_consistency import (
    SelfConsistencyEngine,
    SamplingConfig,
    AnswerNormalizer,
    VoteResult,
)


# ============================================================
# 示例 1：基础自洽性推理
# ============================================================

def example_basic_reasoning():
    """演示基础自洽性推理流程"""
    
    print("=" * 60)
    print("示例 1：基础自洽性推理")
    print("=" * 60)
    
    # 模拟 LLM 客户端
    class MockLLMClient:
        def __init__(self, answers):
            self.answers = answers
            self.call_count = 0
        
        def chat(self, messages, temperature=0.7, max_tokens=1024):
            self.call_count += 1
            # 模拟不同的回答（有些正确，有些错误）
            answer = self.answers[(self.call_count - 1) % len(self.answers)]
            return type('Response', (), {'content': answer})()
    
    # 模拟 5 次采样，其中 3 次正确
    mock_answers = [
        "1. 首先计算 25 × 4 = 100\n2. 然后 100 ÷ 2 = 50\n答案：50",
        "步骤1: 25*4=100, 步骤2: 100/2=50. 答案是 50。",
        "25 乘以 4 等于 100，除以 2 是 50。最终结果 50。",
        "计算过程：25×4=100, 100÷2=51（计算错误）\n答案：51",
        "25*4=100, 100/2=49（粗心错误）\n答案：49",
    ]
    
    client = MockLLMClient(mock_answers)
    
    config = SamplingConfig(
        n_samples=5,
        temperature=0.7,
        consensus_threshold=0.6,
    )
    
    engine = SelfConsistencyEngine(client, config=config)
    
    question = "25 乘以 4 再除以 2 等于多少？"
    result = engine.reason(question)
    
    print(f"问题: {question}")
    print(f"采样次数: {client.call_count}")
    print(f"候选答案: {result.candidates}")
    print(f"获胜答案: {result.winner} ({result.votes}票, 置信度 {result.confidence:.2f})")
    print()


# ============================================================
# 示例 2：答案规范化
# ============================================================

def example_normalization():
    """演示答案规范化的效果"""
    
    print("=" * 60)
    print("示例 2：答案规范化")
    print("=" * 60)
    
    test_cases = [
        ("答案是 42", "42"),
        ("最终结果是四十二", "最终结果是四十二"),
        ("The answer is 42.", "42"),
        ("结论：42", "42"),
        ("42", "42"),
    ]
    
    normalizer = AnswerNormalizer()
    for raw, expected in test_cases:
        normalized = normalizer.normalize(raw)
        match = "✅" if normalized == expected else "⚠️"
        print(f"{match} 原始: {raw!r} → 标准化: {normalized!r}")
    print()


# ============================================================
# 示例 3：早期终止
# ============================================================

def example_early_stopping():
    """演示早期终止机制"""
    
    print("=" * 60)
    print("示例 3：早期终止机制")
    print("=" * 60)
    
    # 所有采样都回答相同，应该在第 3 次达到 60% 阈值后停止
    consistent_answers = [
        "推理过程：...\n答案：北京",
        "根据分析：...\n答案：北京",
        "逐步推导：...\n答案：北京",
        "推理：...\n答案：北京",
        "分析：...\n答案：北京",
    ]
    
    class MockClient:
        def __init__(self, answers):
            self.answers = answers
            self.call_count = 0
        
        def chat(self, messages, temperature=0.7, max_tokens=1024):
            self.call_count += 1
            return type('Response', (), {
                'content': self.answers[self.call_count - 1]
            })()
    
    client = MockClient(consistent_answers)
    
    config = SamplingConfig(
        n_samples=5,
        temperature=0.7,
        consensus_threshold=0.6,  # 60% 阈值
    )
    
    engine = SelfConsistencyEngine(client, config=config)
    result = engine.reason("中国的首都是哪里？")
    
    print(f"总采样配置: 5 次")
    print(f"实际采样: {client.call_count} 次")
    print(f"节省: {5 - client.call_count} 次调用")
    print(f"结果: {result.winner} (置信度 {result.confidence:.2f})")
    print()


# ============================================================
# 示例 4：缓存复用
# ============================================================

def example_caching():
    """演示缓存复用机制"""
    
    print("=" * 60)
    print("示例 4：缓存复用")
    print("=" * 60)
    
    call_count = 0
    
    class MockClient:
        def chat(self, messages, temperature=0.7, max_tokens=1024):
            nonlocal call_count
            call_count += 1
            return type('Response', (), {'content': "答案是 100"})()
    
    client = MockClient()
    engine = SelfConsistencyEngine(client, config=SamplingConfig(n_samples=3))
    
    # 第一次调用
    result1 = engine.reason("50 + 50 等于多少？")
    print(f"第一次调用: API 调用次数 = {call_count}")
    
    # 第二次调用相同问题
    result2 = engine.reason("50 + 50 等于多少？")
    print(f"第二次调用（相同问题）: API 调用次数 = {call_count}")
    print(f"结果来自缓存: {result1 is result2}")
    print()


# ============================================================
# 示例 5：不同采样次数对比
# ============================================================

def example_sampling_comparison():
    """对比不同采样次数的效果"""
    
    print("=" * 60)
    print("示例 5：采样次数对比")
    print("=" * 60)
    
    print("采样次数 | 预估准确率提升 | 成本倍数 | 适用场景")
    print("-" * 55)
    print("1 次     | 基准           | 1x       | 简单任务、高预算敏感")
    print("3 次     | +5~8%          | 3x       | 日常推理、客服问答")
    print("5 次     | +10~15%        | 5x       | 复杂计算、代码生成")
    print("7-10 次  | +15~20%        | 7-10x    | 医疗/金融关键决策")
    print()


# ============================================================
# 运行所有示例
# ============================================================

if __name__ == "__main__":
    example_basic_reasoning()
    example_normalization()
    example_early_stopping()
    example_caching()
    example_sampling_comparison()
    
    print("=" * 60)
    print("所有示例运行完毕！")
    print("核心要点：多次采样 + 投票 + 缓存 + 早期终止")
    print("=" * 60)
