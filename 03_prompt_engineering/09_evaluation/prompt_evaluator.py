"""
Prompt 自动化评估管道
实现基于 LLM-as-a-Judge 和规则评分的混合评估系统。
"""
from __future__ import annotations
import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Protocol, Sequence

import httpx

logger = logging.getLogger(__name__)

class ScoreMetric(Protocol):
    """评估指标接口"""
    async def score(self, prompt: str, output: str, reference: str | None) -> float:
        ...

@dataclass(frozen=True)
class EvaluationResult:
    prompt_id: str
    metrics: dict[str, float]
    latency_ms: float
    judge_feedback: str | None = None

@dataclass
class LLMEvaluator:
    """使用 LLM 作为评估器（LLM-as-a-Judge）"""
    judge_model: str
    api_key: str
    base_url: str = "https://api.openai.com/v1"
    rubric: str = "评估回答的准确性、完整性和逻辑性（0-100分）"
    client: httpx.AsyncClient | None = field(default=None, repr=False)
    _timeout: float = 30.0

    def __post_init__(self) -> None:
        if self.client is None:
            self.client = httpx.AsyncClient(timeout=self._timeout)

    async def _call_judge(self, prompt: str, output: str) -> str:
        """调用裁判模型"""
        if not self.client:
            raise RuntimeError("HTTP client is not initialized")
        payload = {
            "model": self.judge_model,
            "messages": [
                {"role": "system", "content": f"你是一个严格的评估专家。{self.rubric}。只返回数字分数。"},
                {"role": "user", "content": f"Prompt:\n{prompt}\n---\nOutput:\n{output}"}
            ]
        }
        try:
            resp = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            logger.error("Judge API call failed: %s", exc)
            return "0"

    async def score(self, prompt: str, output: str, reference: str | None = None) -> float:
        raw = await self._call_judge(prompt, output)
        try:
            return max(0.0, min(100.0, float(raw)))
        except ValueError:
            logger.warning("Non-numeric judge score: %s", raw)
            return 0.0

@dataclass
class RuleBasedEvaluator:
    """基于规则的轻量评估器"""
    min_length: int = 10
    max_length: int = 2000
    forbidden_terms: Sequence[str] = field(default_factory=lambda: ["不知道", "无法回答", "抱歉"])

    async def score(self, prompt: str, output: str, reference: str | None = None) -> float:
        if not output:
            return 0.0
        length_penalty = 1.0 if self.min_length <= len(output) <= self.max_length else 0.5
        term_penalty = sum(1 for t in self.forbidden_terms if t in output) * 10.0
        return max(0.0, 100.0 - term_penalty) * length_penalty

@dataclass
class EvaluationPipeline:
    """组合多个评估器的流水线"""
    evaluators: dict[str, ScoreMetric]
    judge_model: str | None = None

    async def run(self, prompt_id: str, prompt: str, output: str, reference: str | None = None) -> EvaluationResult:
        import time
        start = time.perf_counter()
        metrics: dict[str, float] = {}
        judge_feedback: str | None = None
        
        for name, evaluator in self.evaluators.items():
            if isinstance(evaluator, LLMEvaluator):
                raw = await evaluator.score(prompt, output, reference)
                metrics[name] = raw
                judge_feedback = f"基于 {evaluator.judge_model} 的评估"
            else:
                metrics[name] = await evaluator.score(prompt, output, reference)
                
        latency_ms = (time.perf_counter() - start) * 1000
        return EvaluationResult(
            prompt_id=prompt_id,
            metrics=metrics,
            latency_ms=latency_ms,
            judge_feedback=judge_feedback
        )
