"""
prompt_manager.py — Prompt 模板管理与版本控制
支持 YAML 加载、Jinja2 渲染、Git 版本追踪

学习重点:
1. YAML 文件存储 Prompt 模板
2. Jinja2 变量渲染
3. 缓存机制优化性能
4. 简单的灰度发布策略
"""

import os
import yaml
import random
from typing import Optional, Any, Dict
from jinja2 import Environment, FileSystemLoader, select_autoescape
from datetime import datetime


class PromptManager:
    """
    Prompt 模板管理器。
    
    功能:
        1. 从 YAML 文件加载 Prompt
        2. 使用 Jinja2 进行变量替换
        3. 追踪模板版本信息
    """
    
    def __init__(self, prompts_dir: str):
        """
        参数:
            prompts_dir: Prompt 模板文件夹路径
        """
        self.prompts_dir = prompts_dir
        
        # 初始化 Jinja2 环境
        self.env = Environment(
            loader=FileSystemLoader(prompts_dir),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        
        self._cache: Dict[str, Any] = {}
    
    def get_prompt(self, name: str, **kwargs) -> Dict[str, str]:
        """
        获取并渲染 Prompt。
        
        参数:
            name: 模板名称 (不含 .yaml 后缀)
            **kwargs: 用于 Jinja2 渲染的变量
        返回:
            包含 system_prompt 和 user_prompt 的字典
        """
        # 1. 尝试从缓存加载
        if name not in self._cache:
            self._load_template(name)
        
        template = self._cache[name]
        metadata = template.get('metadata', {})
        
        # 2. 渲染 Prompt
        env = self.env
        
        # 系统提示词渲染
        system_template = env.from_string(template.get('system_prompt', ''))
        system_prompt = system_template.render(**kwargs)
        
        # 用户提示词渲染
        user_template = env.from_string(template.get('user_prompt', ''))
        user_prompt = user_template.render(**kwargs)
        
        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "metadata": {
                "version": metadata.get('version', 'unknown'),
                "description": metadata.get('description', ''),
                "author": metadata.get('author', ''),
            }
        }
    
    def _load_template(self, name: str):
        """加载 YAML 模板到缓存"""
        yaml_path = os.path.join(self.prompts_dir, f"{name}.yaml")
        
        if not os.path.exists(yaml_path):
            raise FileNotFoundError(f"找不到 Prompt 模板: {yaml_path}")
        
        with open(yaml_path, 'r', encoding='utf-8') as f:
            self._cache[name] = yaml.safe_load(f)
    
    def list_templates(self) -> list:
        """列出所有可用模板"""
        if not os.path.exists(self.prompts_dir):
            return []
        files = os.listdir(self.prompts_dir)
        return [f.replace('.yaml', '') for f in files if f.endswith('.yaml')]
    
    def clear_cache(self):
        """清空缓存（用于热更新）"""
        self._cache.clear()


class PromptVersionController:
    """
    Prompt 版本控制器：支持灰度发布和 A/B 测试。
    """
    
    def __init__(self, manager: PromptManager):
        self.manager = manager
        self.weights: Dict[str, Dict[str, float]] = {}
    
    def set_weights(self, name: str, weights: dict):
        """
        设置流量分配权重。
        
        参数:
            name: 模板名称
            weights: 版本权重字典，如 {"v1": 0.9, "v2": 0.1}
        """
        total = sum(weights.values())
        if abs(total - 1.0) > 0.001:
            raise ValueError("权重总和必须为 1.0")
        self.weights[name] = weights
    
    def get_prompt_with_version(self, name: str, **kwargs) -> dict:
        """根据权重随机选择 Prompt 版本"""
        if name not in self.weights:
            return self.manager.get_prompt(name, **kwargs)
        
        # 加权随机逻辑
        r = random.random()
        cumulative = 0
        versions = self.weights[name]
        
        for version_tag, weight in versions.items():
            cumulative += weight
            if r <= cumulative:
                print(f"命中版本: {version_tag} (权重 {weight})")
                return self.manager.get_prompt(name, **kwargs)
        
        return self.manager.get_prompt(name, **kwargs)
