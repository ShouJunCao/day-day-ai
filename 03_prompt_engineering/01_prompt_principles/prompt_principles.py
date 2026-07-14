"""
prompt_principles.py — Prompt 设计四大原则示例
清晰、具体、结构化、分步骤的实际应用

学习重点：
1. 清晰原则：消除歧义，明确任务类型和意图
2. 具体原则：给出约束条件和细节信息
3. 结构化原则：使用模板组织 Prompt 内容
4. 分步骤原则：将复杂任务拆解为有序步骤
"""

from dataclasses import dataclass, field
from typing import Optional, Any
from string import Template
from pathlib import Path
import json
import re
from datetime import datetime


# ============================================================
# 第一部分：PromptBuilder — 结构化 Prompt 构建器
# ============================================================

@dataclass
class PromptBuilder:
    """
    结构化 Prompt 构建器，遵循四大原则。

    属性:
        role: 角色设定（清晰原则）
        task: 任务描述（清晰 + 具体原则）
        context: 背景上下文（具体原则）
        constraints: 约束条件列表（具体原则）
        output_format: 输出格式要求（结构化原则）
        steps: 执行步骤列表（分步骤原则）
        examples: Few-shot 示例列表
    """

    role: str = ""
    task: str = ""
    context: str = ""
    constraints: list = field(default_factory=list)
    output_format: str = ""
    steps: list = field(default_factory=list)
    examples: list = field(default_factory=list)

    def build(self) -> str:
        """
        将各模块组装为完整 Prompt 字符串。

        返回:
            组装好的 Markdown 格式 Prompt
        """
        parts = []

        # 角色设定（清晰原则）
        if self.role:
            parts.append(f"## 角色\n你是一个{self.role}。")

        # 任务描述（清晰 + 具体原则）
        if self.task:
            parts.append(f"## 任务\n{self.task}")

        # 上下文（具体原则）
        if self.context:
            parts.append(f"## 背景信息\n{self.context}")

        # 约束条件（具体原则）
        if self.constraints:
            items = "\n".join(f"- {c}" for c in self.constraints)
            parts.append(f"## 约束条件\n{items}")

        # 分步骤指引（分步骤原则）
        if self.steps:
            numbered = "\n".join(
                f"{i+1}. {s}" for i, s in enumerate(self.steps)
            )
            parts.append(f"## 执行步骤\n{numbered}")

        # 输出格式（结构化原则）
        if self.output_format:
            parts.append(f"## 输出格式\n{self.output_format}")

        # 示例（Few-shot 提示）
        if self.examples:
            example_text = "\n\n".join(
                f"示例 {i+1}:\n{e}" for i, e in enumerate(self.examples)
            )
            parts.append(f"## 示例\n{example_text}")

        return "\n\n".join(parts)

    def add_constraint(self, constraint: str) -> "PromptBuilder":
        """添加一条约束条件，支持链式调用"""
        self.constraints.append(constraint)
        return self

    def add_step(self, step: str) -> "PromptBuilder":
        """添加一个执行步骤，支持链式调用"""
        self.steps.append(step)
        return self

    def add_example(self, example: str) -> "PromptBuilder":
        """添加一个 Few-shot 示例，支持链式调用"""
        self.examples.append(example)
        return self


# ============================================================
# 第二部分：PromptTemplate — 基于文件的可复用模板系统
# ============================================================

class PromptTemplate:
    """
    基于 string.Template 的可复用 Prompt 模板系统。

    支持 $variable 占位符语法，可从文件加载模板。
    """

    def __init__(self, template_str: str):
        """
        初始化模板。

        参数:
            template_str: 包含 $variable 占位符的模板字符串
        """
        self._template = Template(template_str)
        self._variables = self._extract_variables(template_str)

    @staticmethod
    def _extract_variables(template_str: str) -> list[str]:
        """提取模板中所有变量名"""
        return re.findall(r'\$([a-zA-Z_]\w+)', template_str)

    @classmethod
    def from_file(cls, path: str | Path) -> "PromptTemplate":
        """
        从文件加载模板。

        参数:
            path: 模板文件路径
        返回:
            PromptTemplate 实例
        """
        content = Path(path).read_text(encoding="utf-8")
        return cls(content)

    def render(self, **kwargs: Any) -> str:
        """
        渲染模板，填充变量。

        参数:
            **kwargs: 模板变量的键值对
        返回:
            渲染后的字符串
        异常:
            ValueError: 如果缺少必要的模板变量
        """
        missing = set(self._variables) - set(kwargs.keys())
        if missing:
            raise ValueError(f"缺少模板变量: {missing}")
        return self._template.safe_substitute(**kwargs)

    @property
    def variables(self) -> list[str]:
        """返回模板所需的所有变量名"""
        return list(self._variables)


# ============================================================
# 第三部分：PromptRegistry — Prompt 注册管理中心
# ============================================================

class PromptRegistry:
    """
    Prompt 注册中心：管理多个 Prompt 模板的版本和元数据。

    功能:
        - 模板注册与版本管理
        - 按名称检索模板
        - 标签分类与筛选
        - JSON 持久化存储
    """

    def __init__(self, storage_dir: str = "./prompts"):
        """
        初始化注册中心。

        参数:
            storage_dir: 模板文件存储目录
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._registry: dict = {}
        self._load_registry()

    def _registry_path(self) -> Path:
        """注册表 JSON 文件路径"""
        return self.storage_dir / "registry.json"

    def _load_registry(self) -> None:
        """从磁盘加载注册表"""
        path = self._registry_path()
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            self._registry = data.get("templates", {})

    def _save_registry(self) -> None:
        """持久化注册表到磁盘"""
        data = {
            "updated_at": datetime.now().isoformat(),
            "templates": self._registry,
        }
        self._registry_path().write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def register(
        self,
        name: str,
        template: str,
        description: str = "",
        tags: Optional[list[str]] = None,
    ) -> dict:
        """
        注册一个新的 Prompt 模板。
        如果同名模板已存在，自动创建新版本。

        参数:
            name: 模板名称（唯一标识）
            template: 模板内容字符串
            description: 模板描述
            tags: 标签列表，用于分类筛选
        返回:
            模板注册信息字典
        """
        existing = self._registry.get(name, {})
        version = existing.get("version", 0) + 1

        # 保存模板文件
        template_file = self.storage_dir / f"{name}_v{version}.txt"
        template_file.write_text(template, encoding="utf-8")

        # 更新注册表
        self._registry[name] = {
            "name": name,
            "version": version,
            "description": description,
            "tags": tags or [],
            "template_file": str(template_file),
            "created_at": datetime.now().isoformat(),
        }
        self._save_registry()
        return self._registry[name]

    def get(self, name: str) -> Optional[PromptTemplate]:
        """
        获取指定名称的最新版本模板。

        参数:
            name: 模板名称
        返回:
            PromptTemplate 实例，不存在时返回 None
        """
        entry = self._registry.get(name)
        if not entry:
            return None
        content = Path(entry["template_file"]).read_text(encoding="utf-8")
        return PromptTemplate(content)

    def list_templates(self) -> list[dict]:
        """列出所有已注册的模板信息"""
        return list(self._registry.values())

    def search_by_tag(self, tag: str) -> list[dict]:
        """按标签筛选模板"""
        return [
            info for info in self._registry.values()
            if tag in info.get("tags", [])
        ]
