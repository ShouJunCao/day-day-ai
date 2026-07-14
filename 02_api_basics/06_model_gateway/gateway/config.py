"""
配置管理模块

从YAML文件加载配置，支持环境变量替换。
"""

import os
import re
from typing import List, Optional
from pathlib import Path
from pydantic import BaseModel, Field
import yaml


class ModelConfig(BaseModel):
    """单个模型的配置"""
    name: str
    provider: str
    api_key: str
    base_url: str
    input_price: float = 0.0
    output_price: float = 0.0
    max_concurrent: int = 10
    timeout: int = 60
    enabled: bool = True


class GatewaySettings(BaseModel):
    """网关基础设置"""
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    debug: bool = False


class RoutingConfig(BaseModel):
    """路由策略配置"""
    default_model: str = "gpt-4o-mini"
    strategy: str = "cost_first"  # cost_first | quality_first | round_robin
    fallback_models: List[str] = Field(default_factory=list)


class BudgetConfig(BaseModel):
    """预算控制配置"""
    global_daily_limit: float = 100.0
    user_daily_limit: float = 10.0
    request_max_tokens: int = 8000
    rate_limit_per_minute: int = 120


class LoggingConfig(BaseModel):
    """日志配置"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: Optional[str] = None


class GatewayConfig(BaseModel):
    """网关完整配置"""
    gateway: GatewaySettings = Field(default_factory=GatewaySettings)
    models: List[ModelConfig] = Field(default_factory=list)
    routing: RoutingConfig = Field(default_factory=RoutingConfig)
    budget: BudgetConfig = Field(default_factory=BudgetConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    @classmethod
    def from_yaml(cls, path: str) -> "GatewayConfig":
        """从YAML文件加载配置
        
        Args:
            path: YAML配置文件路径
            
        Returns:
            GatewayConfig实例
        """
        with open(path, 'r', encoding='utf-8') as f:
            raw_config = yaml.safe_load(f)
        
        # 替换环境变量
        raw_config = cls._resolve_env_vars(raw_config)
        
        return cls(**raw_config)
    
    @staticmethod
    def _resolve_env_vars(obj):
        """递归替换配置中的环境变量占位符
        
        支持格式: ${ENV_VAR_NAME}
        """
        if isinstance(obj, dict):
            return {k: GatewayConfig._resolve_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [GatewayConfig._resolve_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            # 匹配 ${VAR_NAME} 格式
            pattern = r'\$\{([^}]+)\}'
            def replace(match):
                var_name = match.group(1)
                return os.getenv(var_name, match.group(0))
            return re.sub(pattern, replace, obj)
        else:
            return obj
