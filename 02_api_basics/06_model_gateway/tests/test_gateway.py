"""
多模型网关单元测试

运行测试：pytest tests/
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from gateway.config import GatewayConfig, ModelConfig
from gateway.registry import ModelRegistry
from gateway.router import ModelRouter
from gateway.middleware import BudgetMiddleware, RateLimitMiddleware


class TestModelRegistry:
    """测试模型注册表"""
    
    def test_register_model(self):
        """测试注册模型"""
        config = ModelConfig(
            name="test-model",
            provider="openai",
            api_key="test-key",
            base_url="https://api.test.com",
            input_price=1.0,
            output_price=2.0,
            enabled=True
        )
        registry = ModelRegistry([config])
        
        assert "test-model" in registry.list_models()
        assert registry.is_healthy("test-model")
        assert registry.get_client("test-model") is not None
    
    def test_mark_unhealthy(self):
        """测试标记模型不健康"""
        config = ModelConfig(
            name="test-model",
            provider="openai",
            api_key="test-key",
            base_url="https://api.test.com",
            input_price=1.0,
            output_price=2.0,
            enabled=True
        )
        registry = ModelRegistry([config])
        
        assert registry.is_healthy("test-model")
        registry.mark_unhealthy("test-model")
        assert not registry.is_healthy("test-model")


class TestModelRouter:
    """测试模型路由器"""
    
    def test_select_cheapest_model(self):
        """测试选择最便宜的模型"""
        configs = [
            ModelConfig("expensive", "openai", "key", "url", 10.0, 20.0, True),
            ModelConfig("cheap", "openai", "key", "url", 1.0, 2.0, True),
        ]
        registry = ModelRegistry(configs)
        router = ModelRouter(registry, strategy="cost_first")
        
        selected = router.select_model()
        assert selected == "cheap"
    
    def test_select_expensive_model(self):
        """测试选择最贵的模型"""
        configs = [
            ModelConfig("cheap", "openai", "key", "url", 1.0, 2.0, True),
            ModelConfig("expensive", "openai", "key", "url", 10.0, 20.0, True),
        ]
        registry = ModelRegistry(configs)
        router = ModelRouter(registry, strategy="quality_first")
        
        selected = router.select_model()
        assert selected == "expensive"
    
    def test_preferred_model(self):
        """测试优先选择指定模型"""
        configs = [
            ModelConfig("model-a", "openai", "key", "url", 1.0, 2.0, True),
            ModelConfig("model-b", "openai", "key", "url", 2.0, 4.0, True),
        ]
        registry = ModelRegistry(configs)
        router = ModelRouter(registry, strategy="cost_first")
        
        selected = router.select_model(preferred="model-b")
        assert selected == "model-b"
    
    def test_fallback_model(self):
        """测试故障转移"""
        configs = [
            ModelConfig("primary", "openai", "key", "url", 1.0, 2.0, True),
            ModelConfig("fallback", "openai", "key", "url", 2.0, 4.0, True),
        ]
        registry = ModelRegistry(configs)
        router = ModelRouter(registry, strategy="cost_first", fallback_models=["fallback"])
        
        # 标记主模型不健康
        registry.mark_unhealthy("primary")
        
        # 应该返回备选模型
        fallback = router.get_fallback_model("primary")
        assert fallback == "fallback"


class TestBudgetMiddleware:
    """测试预算控制中间件"""
    
    def test_record_cost(self):
        """测试记录费用"""
        middleware = BudgetMiddleware(Mock(), global_limit=100.0, user_limit=10.0)
        
        middleware.record_cost("user1", 1.5)
        middleware.record_cost("user1", 2.0)
        
        assert middleware.global_daily_cost == 3.5
        assert middleware.user_daily_costs["user1"] == 3.5
    
    def test_budget_check_pass(self):
        """测试预算检查通过"""
        middleware = BudgetMiddleware(Mock(), global_limit=100.0, user_limit=10.0)
        
        assert middleware.check_budget("user1", 5.0)
    
    def test_budget_check_fail_global(self):
        """测试全局预算超限"""
        middleware = BudgetMiddleware(Mock(), global_limit=100.0, user_limit=10.0)
        middleware.global_daily_cost = 95.0
        
        assert not middleware.check_budget("user1", 10.0)
    
    def test_budget_check_fail_user(self):
        """测试用户预算超限"""
        middleware = BudgetMiddleware(Mock(), global_limit=100.0, user_limit=10.0)
        middleware.user_daily_costs["user1"] = 8.0
        
        assert not middleware.check_budget("user1", 5.0)


class TestRateLimitMiddleware:
    """测试速率限制中间件"""
    
    def test_rate_limit_pass(self):
        """测试限流检查通过"""
        middleware = RateLimitMiddleware(Mock(), rate_limit=10)
        
        # 第一次请求应该通过
        assert middleware._check_rate_limit("user1")
    
    def test_rate_limit_exceed(self):
        """测试限流超限"""
        middleware = RateLimitMiddleware(Mock(), rate_limit=3)
        
        # 发送3次请求
        middleware._check_rate_limit("user1")
        middleware._check_rate_limit("user1")
        middleware._check_rate_limit("user1")
        
        # 第4次应该失败
        assert not middleware._check_rate_limit("user1")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
