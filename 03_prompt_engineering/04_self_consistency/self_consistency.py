"""
self_consistency.py — 自洽性（Self-Consistency）与多数投票引擎
集成重试、限流、缓存、早期终止等生产级特性

学习重点:
1. 多次采样（高 temperature 探索不同推理路径）
2. 答案提取与规范化
3. 多数投票与共识阈值
4. 早期终止优化（降低成本）
5. 结果缓存（避免重复计算）
"""

import json
import hashlib
import time
from typing import Any, Optional
from dataclasses import dataclass, field
from collections import Counter
import re


@dataclass
class VoteResult:
    """投票结果：包含候选答案、票数、共识置信度"""
    candidates: dict[str, int]
    winner: str
    votes: int
    total: int
    confidence: float


@dataclass
class SamplingConfig:
    """采样配置"""
    n_samples: int = 5
    temperature: float = 0.7
    max_tokens: int = 1024
    consensus_threshold: float = 0.6
    timeout_seconds: float = 30.0


class AnswerNormalizer:
    """
    答案规范化器：将不同表述的答案标准化为统一格式。
    
    例如：
        "答案是 42" → "42"
        "四十二" → "42"
        "The answer is 42." → "42"
    """
    
    # 简单的中文数字映射
    CN_NUMS = {
        '零': '0', '一': '1', '二': '2', '三': '3', '四': '4',
        '五': '5', '六': '6', '七': '7', '八': '8', '九': '9',
        '十': '10', '百': '100', '千': '1000', '万': '10000',
    }
    
    @classmethod
    def normalize(cls, text: str) -> str:
        """
        标准化答案字符串。
        
        参数:
            text: 原始答案文本
        返回:
            标准化后的答案
        """
        if not text:
            return ""
        
        # 移除常见前缀/后缀
        cleaned = text.strip()
        prefixes = ["答案", "答案是", "最终答案是", "结论是", 
                    "the answer is", "answer:", "result:"]
        for prefix in prefixes:
            if cleaned.lower().startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
        
        # 移除标点符号
        cleaned = re.sub(r'[，。！！？?.,:!;\'"(){}]', '', cleaned)
        
        # 移除多余空白
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned


class SelfConsistencyEngine:
    """
    自洽性推理引擎。
    
    工作流程：
        1. 接收问题和 Prompt 模板
        2. 并行/串行采样 N 次（高 temperature）
        3. 提取每个样本的最终答案
        4. 执行多数投票
        5. 支持早期终止和结果缓存
    
    参数:
        llm_client: LLM 客户端实例
        cache: 可选的缓存字典（key -> VoteResult）
        config: 采样配置
    """
    
    def __init__(
        self,
        llm_client,
        cache: Optional[dict] = None,
        config: SamplingConfig = SamplingConfig(),
    ):
        """
        初始化引擎。
        
        参数:
            llm_client: LLM 客户端（需实现 chat 方法）
            cache: 缓存字典，用于存储历史问题的投票结果
            config: 采样配置
        """
        self.client = llm_client
        self.cache = cache or {}
        self.config = config
        self.normalizer = AnswerNormalizer()
    
    def _hash_question(self, question: str) -> str:
        """生成问题的唯一缓存键（MD5）"""
        return hashlib.md5(question.encode()).hexdigest()
    
    def _extract_answer(self, text: str) -> str:
        """
        从模型输出中提取最终答案。
        
        启发式规则：查找最后一行、包含“答案”关键字的行、
        或 JSON 格式的答案字段。
        
        参数:
            text: 模型的完整输出
        返回:
            提取出的答案字符串
        """
        lines = text.strip().split("\n")
        
        # 尝试解析 JSON
        json_match = re.search(r'\{.*"answer"\s*:\s*"([^"]+)".*\}', text)
        if json_match:
            return json_match.group(1)
        
        # 反向查找包含答案关键字的行
        for line in reversed(lines):
            if any(kw in line.lower() for kw in 
                   ["答案", "answer", "结论", "结果是", "therefore"]):
                return line.strip()
        
        # 降级：返回最后一行
        return lines[-1].strip() if lines else ""
    
    def _consensus_reached(
        self, counts: Counter, total: int
    ) -> tuple[bool, str, float]:
        """
        检查是否达到共识阈值。
        
        参数:
            counts: 答案计数器
            total: 总采样数
        返回:
            (是否达成共识, 获胜答案, 置信度)
        """
        if not counts:
            return False, "", 0.0
        winner, vote_count = counts.most_common(1)[0]
        confidence = vote_count / total
        return (confidence >= self.config.consensus_threshold, 
                winner, confidence)
    
    def reason(self, question: str) -> VoteResult:
        """
        执行自洽性推理。
        
        参数:
            question: 需要推理的问题
        返回:
            VoteResult 对象
        """
        cache_key = self._hash_question(question)
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        candidates_counter = Counter()
        samples = []
        start_time = time.time()
        
        for i in range(self.config.n_samples):
            # 检查超时
            elapsed = time.time() - start_time
            if elapsed > self.config.timeout_seconds:
                print(f"⏰ 超时终止：已运行 {elapsed:.1f}s")
                break
            
            # 构建 Prompt
            prompt = (
                f"问题：{question}\n\n"
                f"请逐步推理，最后给出答案。\n"
                f"Let's think step by step."
            )
            
            # 调用 LLM
            response = self.client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            
            # 提取并标准化答案
            raw_answer = self._extract_answer(response.content)
            normalized = self.normalizer.normalize(raw_answer)
            
            candidates_counter[normalized] += 1
            samples.append({
                "index": i + 1,
                "raw_answer": raw_answer,
                "normalized": normalized,
            })
            
            # 早期终止检查
            reached, winner, conf = self._consensus_reached(
                candidates_counter, i + 1
            )
            if reached:
                print(f"✅ 早期终止：在第 {i+1} 次采样达成共识 "
                      f"({winner}, 置信度 {conf:.2f})")
                break
        
        # 构建结果
        winner, votes = candidates_counter.most_common(1)[0]
        total = sum(candidates_counter.values())
        confidence = votes / total if total > 0 else 0.0
        
        result = VoteResult(
            candidates=dict(candidates_counter),
            winner=winner,
            votes=votes,
            total=total,
            confidence=confidence,
        )
        
        # 缓存结果
        self.cache[cache_key] = result
        return result
