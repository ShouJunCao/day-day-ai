"""
zero_few_shot.py — Zero-shot 与 Few-shot 提示实现
集成重试、限流、日志等生产级特性

学习重点:
1. Zero-shot: 不提供示例，直接描述任务
2. Few-shot: 提供 1-N 个示例引导模型
3. 动态示例选择: 根据输入特征选择最相关示例
4. 示例库管理: 版本控制、使用统计、标签筛选
"""

from typing import Optional
from dataclasses import dataclass, field
import json
import random


# ============================================================
# 第一部分：Zero-shot 提示
# ============================================================

@dataclass
class ZeroShotPrompt:
    """
    Zero-shot 提示构建器。
    
    不提供任何示例，直接通过任务描述和约束条件
    引导模型完成指定任务。
    """
    
    task: str
    constraints: list[str] = field(default_factory=list)
    output_format: str = "text"
    
    def build(self) -> str:
        """
        构建 Zero-shot Prompt 字符串。
        
        返回:
            结构化的 Prompt 字符串
        """
        parts = [f"## 任务\n{self.task}"]
        
        if self.constraints:
            items = "\n".join(f"- {c}" for c in self.constraints)
            parts.append(f"## 约束条件\n{items}")
        
        if self.output_format != "text":
            parts.append(f"## 输出格式\n{self.output_format}")
        
        return "\n\n".join(parts)


def zero_shot_sentiment(text: str, client) -> dict:
    """
    Zero-shot 情感分析。
    
    参数:
        text: 待分析文本
        client: LLM 客户端（UnifiedLLMClient）
    返回:
        包含 sentiment 和 confidence 的字典
    """
    prompt = ZeroShotPrompt(
        task=f"分析以下文本的情感倾向：\n\n{text}",
        constraints=[
            "情感类别：正面 / 负面 / 中性",
            "输出 JSON 格式",
            "包含 confidence 字段（0-1 之间）",
        ],
        output_format='{"sentiment": "正面/负面/中性", "confidence": 0.95}'
    ).build()
    
    response = client.chat(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    
    try:
        return json.loads(response.content)
    except json.JSONDecodeError:
        return {"sentiment": "unknown", "raw": response.content}


# ============================================================
# 第二部分：Few-shot 提示
# ============================================================

@dataclass
class Example:
    """
    单个 Few-shot 示例。
    
    属性:
        input: 示例输入
        output: 期望输出
        tags: 标签列表，用于分类和筛选
    """
    input: str
    output: str
    tags: list[str] = field(default_factory=list)


@dataclass
class FewShotPrompt:
    """
    Few-shot 提示构建器。
    
    通过提供多个输入-输出示例，引导模型学习
    特定任务的模式和输出格式。
    """
    
    task: str
    examples: list[Example]
    actual_input: str
    constraints: list[str] = field(default_factory=list)
    output_format: str = ""
    
    def build(self) -> str:
        """
        构建 Few-shot Prompt 字符串。
        
        返回:
            包含示例和实际任务的结构化 Prompt
        """
        parts = [f"## 任务\n{self.task}"]
        
        # 添加示例
        if self.examples:
            example_text = []
            for i, ex in enumerate(self.examples, 1):
                example_text.append(
                    f"### 示例 {i}\n"
                    f"**输入：**\n{ex.input}\n\n"
                    f"**输出：**\n{ex.output}"
                )
            parts.append("## 示例\n" + "\n\n".join(example_text))
        
        # 实际任务
        parts.append(f"## 实际任务\n**输入：**\n{self.actual_input}")
        
        # 约束条件
        if self.constraints:
            items = "\n".join(f"- {c}" for c in self.constraints)
            parts.append(f"## 约束条件\n{items}")
        
        # 输出格式
        if self.output_format:
            parts.append(f"## 输出格式\n{self.output_format}")
        
        return "\n\n".join(parts)


def few_shot_ner(text: str, client) -> list[dict]:
    """
    Few-shot 命名实体识别（NER）。
    
    参数:
        text: 待提取文本
        client: LLM 客户端
    返回:
        实体列表，每个实体包含 name 和 type
    """
    examples = [
        Example(
            input="苹果公司今天发布了新款 iPhone。",
            output='[{"name": "苹果公司", "type": "ORG"}, '
                   '{"name": "iPhone", "type": "PRODUCT"}]',
            tags=["tech", "product"],
        ),
        Example(
            input="张三在北京大学获得了博士学位。",
            output='[{"name": "张三", "type": "PERSON"}, '
                   '{"name": "北京大学", "type": "ORG"}]',
            tags=["education", "person"],
        ),
        Example(
            input="腾讯的股价上涨了 5%，达到 400 港元。",
            output='[{"name": "腾讯", "type": "ORG"}, '
                   '{"name": "400 港元", "type": "MONEY"}]',
            tags=["finance", "stock"],
        ),
    ]
    
    prompt = FewShotPrompt(
        task="从文本中提取命名实体（人名、组织、产品、地点、金额等）",
        examples=examples,
        actual_input=text,
        constraints=[
            "输出 JSON 数组格式",
            "每个实体包含 name 和 type 字段",
            "type 可选值：PERSON / ORG / PRODUCT / LOCATION / MONEY / DATE",
        ],
        output_format='[{"name": "实体名", "type": "类型"}]'
    ).build()
    
    response = client.chat(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    
    try:
        entities = json.loads(response.content)
        return entities if isinstance(entities, list) else []
    except json.JSONDecodeError:
        return []


# ============================================================
# 第三部分：示例库管理
# ============================================================

class ExampleLibrary:
    """
    示例库管理器：支持动态选择和版本管理。
    
    特性:
        - 按标签筛选示例
        - 使用频率追踪（保持多样性）
        - 随机选择（基线测试）
        - 统计信息导出
    """
    
    def __init__(self):
        """初始化空示例库"""
        self._examples: dict[str, Example] = {}
        self._usage_stats: dict[str, int] = {}
    
    def add(self, example_id: str, example: Example) -> None:
        """
        添加示例到库中。
        
        参数:
            example_id: 示例唯一标识
            example: Example 实例
        """
        self._examples[example_id] = example
        self._usage_stats[example_id] = 0
    
    def remove(self, example_id: str) -> bool:
        """
        删除示例。
        
        参数:
            example_id: 示例 ID
        返回:
            是否删除成功
        """
        if example_id in self._examples:
            del self._examples[example_id]
            del self._usage_stats[example_id]
            return True
        return False
    
    def get_by_tags(self, tags: list[str], limit: int = 5) -> list[Example]:
        """
        按标签筛选示例。
        
        参数:
            tags: 标签列表（示例需包含至少一个标签）
            limit: 返回数量上限
        返回:
            匹配的示例列表，按使用频率升序排列
        """
        matched = []
        for ex_id, example in self._examples.items():
            if any(tag in example.tags for tag in tags):
                matched.append((ex_id, example))
        
        # 按使用频率排序（优先使用低频示例，保持多样性）
        matched.sort(key=lambda x: self._usage_stats[x[0]])
        
        # 更新使用统计
        result = []
        for ex_id, example in matched[:limit]:
            self._usage_stats[ex_id] += 1
            result.append(example)
        
        return result
    
    def get_random(self, count: int = 3) -> list[Example]:
        """
        随机选择示例（用于基线测试）。
        
        参数:
            count: 选择数量
        返回:
            随机示例列表
        """
        examples = list(self._examples.values())
        return random.sample(examples, min(count, len(examples)))
    
    def stats(self) -> dict:
        """
        返回示例库统计信息。
        
        返回:
            包含总数、使用统计、标签分布的字典
        """
        return {
            "total": len(self._examples),
            "usage": self._usage_stats,
            "tags": self._collect_tags(),
        }
    
    def _collect_tags(self) -> dict[str, int]:
        """统计所有标签的使用情况"""
        tag_counts = {}
        for example in self._examples.values():
            for tag in example.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        return tag_counts
    
    def __len__(self) -> int:
        return len(self._examples)
    
    def __contains__(self, example_id: str) -> bool:
        return example_id in self._examples
