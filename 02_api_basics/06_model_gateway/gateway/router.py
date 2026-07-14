"""
模型路由模块

根据策略选择最佳模型，支持自动故障转移。
"""

import logging
import random
from typing import List, Optional, Dict
from .config import RoutingConfig
from .registry import ModelRegistry

logger = logging.getLogger(__name__)


class ModelRouter:
    """模型路由器 - 智能选择最佳模型
    
    支持的策略：
    - cost_first: 优先选择成本最低的模型
    - quality_first: 优先选择质量最高的模型
    - round_robin: 轮询选择
    """
    
    def __init__(self, registry: ModelRegistry, config: RoutingConfig):
        """初始化路由器
        
        Args:
            registry: 模型注册表
            config: 路由配置
        """
        self.registry = registry
        self.config = config
        self.round_robin_index = 0
    
    def select_model(
        self,
        preferred_model: Optional[str] = None,
        max_cost: Optional[float] = None,
    ) -> str:
        """选择最佳模型
        
        Args:
            preferred_model: 用户偏好的模型（如果指定）
            max_cost: 最大成本限制（每百万token）
            
        Returns:
            选中的模型名称
            
        Raises:
            ValueError: 没有可用模型
        """
        # 如果用户指定了偏好模型且可用，直接使用
        if preferred_model:
            if self._is_available(preferred_model, max_cost):
                return preferred_model
            logger.warning(
                f"偏好模型 {preferred_model} 不可用，尝试备选模型"
            )
        
        # 获取所有可用模型
        available = self._get_available_models(max_cost)
        
        if not available:
            raise ValueError("没有可用的模型")
        
        # 根据策略选择
        strategy = self.config.strategy
        
        if strategy == "cost_first":
            return self._select_by_cost(available)
        elif strategy == "quality_first":
            return self._select_by_quality(available)
        elif strategy == "round_robin":
            return self._select_round_robin(available)
        else:
            # 默认使用成本优先
            return self._select_by_cost(available)
    
    def get_fallback_model(self, failed_model: str) -> Optional[str]:
        """获取故障转移模型
        
        Args:
            failed_model: 失败的模型名称
            
        Returns:
            备选模型名称，如果没有可用备选则返回None
        """
        # 优先从配置的fallback列表中选择
        for fallback in self.config.fallback_models:
            if fallback != failed_model and self._is_available(fallback):
                logger.info(f"故障转移: {failed_model} -> {fallback}")
                return fallback
        
        # 如果没有配置的fallback，选择任意可用模型
        available = [
            m for m in self.registry.list_healthy_models()
            if m != failed_model
        ]
        
        if available:
            selected = available[0]
            logger.info(f"故障转移: {failed_model} -> {selected}")
            return selected
        
        return None
    
    def _is_available(
        self,
        model_name: str,
        max_cost: Optional[float] = None,
    ) -> bool:
        """检查模型是否可用
        
        Args:
            model_name: 模型名称
            max_cost: 最大成本限制
            
        Returns:
            True表示可用
        """
        # 检查是否注册
        config = self.registry.get_config(model_name)
        if not config:
            return False
        
        # 检查健康状态
        if not self.registry.is_healthy(model_name):
            return False
        
        # 检查成本限制
        if max_cost is not None:
            if config.input_price > max_cost:
                return False
        
        return True
    
    def _get_available_models(self, max_cost: Optional[float] = None) -> List[str]:
        """获取所有可用模型
        
        Args:
            max_cost: 最大成本限制
            
        Returns:
            可用模型名称列表
        """
        available = []
        for model_name in self.registry.list_models():
            if self._is_available(model_name, max_cost):
                available.append(model_name)
        return available
    
    def _select_by_cost(self, models: List[str]) -> str:
        """按成本选择模型（选择最便宜的）
        
        Args:
            models: 候选模型列表
            
        Returns:
            选中的模型名称
        """
        # 按输入成本排序
        sorted_models = sorted(
            models,
            key=lambda m: self.registry.get_config(m).input_price
        )
        return sorted_models[0]
    
    def _select_by_quality(self, models: List[str]) -> str:
        """按质量选择模型（选择最贵的，假设贵=好）
        
        Args:
            models: 候选模型列表
            
        Returns:
            选中的模型名称
        """
        # 按输入成本倒序排序
        sorted_models = sorted(
            models,
            key=lambda m: self.registry.get_config(m).input_price,
            reverse=True
        )
        return sorted_models[0]
    
    def _select_round_robin(self, models: List[str]) -> str:
        """轮询选择模型
        
        Args:
            models: 候选模型列表
            
        Returns:
            选中的模型名称
        """
        if not models:
            raise ValueError("没有可用模型")
        
        # 使用轮询索引
        selected = models[self.round_robin_index % len(models)]
        self.round_robin_index += 1
        
        return selected
