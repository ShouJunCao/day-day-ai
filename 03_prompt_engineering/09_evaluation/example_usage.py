"""
评估管道使用示例
展示如何配置 LLM-as-a-Judge、组合规则评估器、
执行批量测试并检测回归。
"""
import asyncio
from prompt_evaluator import EvaluationPipeline, LLMEvaluator, RuleBasedEvaluator
from metrics import aggregate_scores

import os

async def main() -> None:
    # 1. 初始化评估器
    judge = LLMEvaluator(
        judge_model=os.getenv("MODEL"),
        api_key=os.getenv("API_KEY"),
        base_url=os.getenv("BASE_URL"),
        rubric="评估代码的正确性、边界处理与可读性（0-100）"
    )
    rule_engine = RuleBasedEvaluator(
        min_length=50,
        forbidden_terms=["TODO", "FIXME", "placeholder"]
    )

    # 2. 构建评估管道
    pipeline = EvaluationPipeline(
        evaluators={
            "llm_judge": judge,
            "rule_check": rule_engine
        },
        judge_model="gpt-4o-mini"
    )

    # 3. 模拟批量评估数据
    test_cases = [
        ("case_1", "解释递归", "递归是函数调用自身的过程..."),
        ("case_2", "写排序算法", "def quicksort(arr): return arr if len(arr) <= 1 else ..."),
        ("case_3", "TODO: 实现错误处理", "抱歉，这个我还不会...")
    ]

    results = []
    for pid, prompt, output in test_cases:
        res = await pipeline.run(prompt_id=pid, prompt=prompt, output=output)
        results.append(res.metrics)
        print(f"{pid}: {res.metrics} (延迟 {res.latency_ms:.0f}ms)")

    # 4. 聚合分析
    baseline = {"llm_judge": 85.0, "rule_check": 90.0}
    summary = aggregate_scores(results, baseline)
    print("\n=== 评估汇总 ===")
    for s in summary.summaries:
        print(s)
    if summary.regression_detected:
        print(f"⚠️ 检测到退化指标: {summary.regression_metrics}")

if __name__ == "__main__":
    asyncio.run(main())
