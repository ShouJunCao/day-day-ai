"""
企业级 Prompt 模板库核心模块
支持 YAML/JSON 加载、变量渲染、分类检索、缓存与版本控制。
"""
from __future__ import annotations
import json
import time
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

import yaml

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class PromptTemplate:
    """不可变的 Prompt 模板对象"""
    id: str
    name: str
    category: str
    version: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def render(self, **kwargs: Any) -> str:
        """使用 Jinja2 风格进行简单变量替换"""
        result = self.content
        for key, value in kwargs.items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))
        missing = [k for k, v in kwargs.items() if f"{{{{{k}}}}}" not in self.content]
        if missing:
            logger.warning("Unused variables for template %s: %s", self.id, missing)
        return result

@dataclass
class PromptRegistry:
    """企业级 Prompt 注册中心"""
    templates: dict[str, PromptTemplate] = field(default_factory=dict)
    index_by_category: dict[str, list[str]] = field(default_factory=dict)
    _version_history: dict[str, list[PromptTemplate]] = field(default_factory=dict)

    def register(self, template: PromptTemplate) -> None:
        """注册或更新模板"""
        old = self.templates.get(template.id)
        self.templates[template.id] = template
        
        cat = template.category
        if cat not in self.index_by_category:
            self.index_by_category[cat] = []
        if template.id not in self.index_by_category[cat]:
            self.index_by_category[cat].append(template.id)
            
        if old is not None:
            if template.id not in self._version_history:
                self._version_history[template.id] = [old]
            self._version_history[template.id].append(template)
            logger.info("Updated template %s: v%s -> v%s", template.id, old.version, template.version)
        else:
            logger.info("Registered new template: %s (v%s)", template.id, template.version)

    def get(self, template_id: str, version: str | None = None) -> PromptTemplate | None:
        """按 ID 获取模板，可选指定版本"""
        if version and template_id in self._version_history:
            for t in reversed(self._version_history[template_id]):
                if t.version == version:
                    return t
        return self.templates.get(template_id)

    def list_by_category(self, category: str) -> list[PromptTemplate]:
        """按分类列出模板"""
        ids = self.index_by_category.get(category, [])
        return [self.templates[i] for i in ids if i in self.templates]

    def count(self) -> int:
        return len(self.templates)

@dataclass
class TemplateLoader:
    """从文件或字符串加载模板"""
    registry: PromptRegistry

    def load_from_yaml(self, path: str | Path) -> list[PromptTemplate]:
        """从 YAML 文件批量加载"""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Template file not found: {p}")
        with open(p, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, list):
            data = [data]
        templates = []
        for item in data:
            t = PromptTemplate(
                id=item["id"],
                name=item["name"],
                category=item.get("category", "default"),
                version=item.get("version", "1.0.0"),
                content=item["content"],
                metadata=item.get("metadata", {})
            )
            self.registry.register(t)
            templates.append(t)
        logger.info("Loaded %d templates from %s", len(templates), p)
        return templates

    def load_from_json(self, path: str | Path) -> list[PromptTemplate]:
        """从 JSON 文件批量加载"""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Template file not found: {p}")
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            data = [data]
        templates = []
        for item in data:
            t = PromptTemplate(
                id=item["id"],
                name=item["name"],
                category=item.get("category", "default"),
                version=item.get("version", "1.0.0"),
                content=item["content"],
                metadata=item.get("metadata", {})
            )
            self.registry.register(t)
            templates.append(t)
        logger.info("Loaded %d templates from %s", len(templates), p)
        return templates

    def create_inline(self, **kwargs: Any) -> PromptTemplate:
        """动态创建内联模板"""
        required = {"id", "name", "content"}
        missing = required - kwargs.keys()
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
        t = PromptTemplate(
            id=kwargs["id"],
            name=kwargs["name"],
            category=kwargs.get("category", "dynamic"),
            version=kwargs.get("version", "0.1.0"),
            content=kwargs["content"],
            metadata=kwargs.get("metadata", {})
        )
        self.registry.register(t)
        return t
