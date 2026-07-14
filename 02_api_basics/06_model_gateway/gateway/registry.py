"""
模型注册表

管理所有可用模型的客户端实例和状态。
"""

import logging
from typing import Dict, List, Optional
from openai import AsyncOpenAI
from .config import ModelConfig

logger = logging.getLogger(__name__)


class ModelRegistry:
    """模型注册表 - 管理所有可用模型
    
    职责：
    1. 初始化并缓存模型客户端
    2. 跟踪模型状态（健康/故障）
    3. 提供模型查询接口
    """
    
    def __init__(self, model_configs: List[ModelConfig]):
        """初始化模型注册表
        
        Args:
            model_configs: 模型配置列表
        """
        self.configs: Dict[str, ModelConfig] = {}
        self.clients: Dict[str, AsyncOpenAI] = {}
        self.health_status: Dict[str, bool] = {}
        
        # 注册所有启用的模型
        for config in model_configs:
            if config.enabled:
                self.register(config)
    
    def register(self, config: ModelConfig) -> None:
        """注册一个新模型
        
        Args:
            config: 模型配置
        """
        self.configs[config.name] = config
        
        # 创建OpenAI客户端
        self.clients[config.name] = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=float(config.timeout),
        )
        
        # 初始化健康状态
        self.health_status[config.name] = True
        
        logger.info(f"注册模型: {config.name} ({config.provider})")
    
    def get_client(self, model_name: str) -> Optional[AsyncOpenAI]:
        """获取模型客户端
        
        Args:
            model_name: 模型名称
            
        Returns:
            AsyncOpenAI客户端实例，如果模型不存在则返回None
        """
        return self.clients.get(model_name)
    
    def get_config(self, model_name: str) -> Optional[ModelConfig]:
        """获取模型配置
        
        Args:
            model_name: 模型名称
            
        Returns:
            ModelConfig实例，如果模型不存在则返回None
        """
        return self.configs.get(model_name)
    
    def is_healthy(self, model_name: str) -> bool:
        """检查模型是否健康
        
        Args:
            model_name: 模型名称
            
        Returns:
            True表示健康，False表示故障
        """
        return self.health_status.get(model_name, False)
    
    def mark_unhealthy(self, model_name: str) -> None:
        """将模型标记为不健康
        
        Args:
            model_name: 模型名称
        """
        self.health_status[model_name] = False
        logger.warning(f"模型 {model_name} 已标记为不健康")
    
    def mark_healthy(self, model_name: str) -> None:
        """将模型恢复为健康状态
        
        Args:
            model_name: 模型名称
        """
        self.health_status[model_name] = True
        logger.info(f"模型 {model_name} 已恢复为健康状态")
    
    def list_models(self) -> List[str]:
        """列出所有已注册的模型名称
        
        Returns:
            模型名称列表
        """
        return list(self.configs.keys())
    
    def list_healthy_models(self) -> List[str]:
        """列出所有健康的模型名称
        
        Returns:
            健康模型名称列表
        """
        return [
            name for name, healthy in self.health_status.items()
            if healthy and name in self.configs
        ]
