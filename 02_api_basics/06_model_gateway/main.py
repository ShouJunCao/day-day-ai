"""
多模型网关 - 主入口

统一的OpenAI兼容API网关，支持多模型路由、预算控制和故障转移。

启动方式：
    python main.py
    
    或
    
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""

import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, AsyncGenerator

from gateway.config import GatewayConfig
from gateway.registry import ModelRegistry
from gateway.router import ModelRouter
from gateway.middleware import (
    LoggingMiddleware,
    RateLimitMiddleware,
    BudgetMiddleware,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局配置（在lifespan中初始化）
config: GatewayConfig = None
registry: ModelRegistry = None
router: ModelRouter = None
budget_middleware: BudgetMiddleware = None


# ============================================================
# 数据模型（Pydantic）
# ============================================================

class Message(BaseModel):
    """聊天消息"""
    role: str
    content: str


class ChatRequest(BaseModel):
    """聊天请求体（OpenAI兼容格式）"""
    model: Optional[str] = None
    messages: List[Message]
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1, le=8192)
    stream: bool = False


class ChatResponse(BaseModel):
    """聊天响应体（OpenAI兼容格式）"""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict]
    usage: Dict


class ModelInfo(BaseModel):
    """模型信息"""
    id: str
    object: str = "model"
    created: int = 1700000000
    owned_by: str


# ============================================================
# FastAPI应用生命周期
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global config, registry, router, budget_middleware
    
    # 启动时：加载配置并初始化组件
    logger.info("正在启动多模型网关...")
    
    # 加载配置
    config_path = Path(__file__).parent / "config.yaml"
    config = GatewayConfig.from_yaml(str(config_path))
    
    # 初始化模型注册表
    registry = ModelRegistry(config.models)
    logger.info(f"已注册 {len(registry.list_models())} 个模型")
    
    # 初始化路由器
    router = ModelRouter(registry, config.routing)
    
    # 初始化中间件（预算控制需要全局访问）
    budget_middleware = BudgetMiddleware(app, config.budget)
    
    logger.info("网关启动完成！")
    
    yield
    
    # 关闭时：清理资源
    logger.info("正在关闭网关...")
    # 关闭所有OpenAI客户端连接
    for model_name in registry.list_models():
        client = registry.get_client(model_name)
        if client:
            await client.close()
    logger.info("网关已关闭")


# ============================================================
# FastAPI应用实例
# ============================================================

app = FastAPI(
    title="Multi-Model Gateway",
    description="生产级多模型网关 - 统一管理和路由多个大模型API",
    version="1.0.0",
    lifespan=lifespan,
)

# 添加中间件
app.add_middleware(LoggingMiddleware)


# ============================================================
# API路由
# ============================================================

@app.get("/v1/models")
async def list_models() -> Dict:
    """列出所有可用模型（OpenAI兼容）"""
    models = []
    for model_name in registry.list_models():
        model_config = registry.get_config(model_name)
        models.append({
            "id": model_name,
            "object": "model",
            "created": 1700000000,
            "owned_by": model_config.provider,
            "healthy": registry.is_healthy(model_name),
        })
    
    return {
        "object": "list",
        "data": models,
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest, http_request: Request) -> Dict:
    """聊天补全接口（OpenAI兼容）
    
    支持：
    - 自动模型路由
    - 故障转移
    - 预算控制
    - 流式和非流式响应
    """
    user_id = http_request.client.host if http_request.client else "unknown"
    
    # 1. 选择模型
    try:
        selected_model = router.select_model(
            preferred_model=request.model,
        )
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    
    logger.info(f"用户 {user_id} -> 模型 {selected_model}")
    
    # 2. 获取客户端
    client = registry.get_client(selected_model)
    if not client:
        raise HTTPException(status_code=503, detail="模型不可用")
    
    # 3. 准备请求参数
    messages = [msg.model_dump() for msg in request.messages]
    
    kwargs = {
        "model": selected_model,
        "messages": messages,
        "temperature": request.temperature,
        "stream": request.stream,
    }
    
    if request.max_tokens:
        kwargs["max_tokens"] = request.max_tokens
    
    # 4. 调用模型API（带故障转移）
    try:
        response = await client.chat.completions.create(**kwargs)
    except Exception as e:
        logger.error(f"模型 {selected_model} 调用失败: {e}")
        
        # 标记模型为不健康
        registry.mark_unhealthy(selected_model)
        
        # 尝试故障转移
        fallback = router.get_fallback_model(selected_model)
        if fallback:
            logger.info(f"尝试故障转移到 {fallback}")
            fallback_client = registry.get_client(fallback)
            if fallback_client:
                kwargs["model"] = fallback
                response = await fallback_client.chat.completions.create(**kwargs)
                selected_model = fallback
            else:
                raise HTTPException(status_code=503, detail="所有模型不可用")
        else:
            raise HTTPException(status_code=503, detail="模型不可用且无备选")
    
    # 5. 处理响应
    if request.stream:
        # 流式响应（简化处理，生产环境应该使用StreamingResponse）
        return {"error": "流式响应请使用SSE接口"}
    else:
        # 非流式响应
        result = {
            "id": response.id,
            "object": response.object,
            "created": response.created,
            "model": selected_model,
            "choices": [
                {
                    "index": choice.index,
                    "message": {
                        "role": choice.message.role,
                        "content": choice.message.content,
                    },
                    "finish_reason": choice.finish_reason,
                }
                for choice in response.choices
            ],
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            } if response.usage else {},
        }
        
        # 6. 记录费用（如果有usage信息）
        if response.usage and budget_middleware:
            model_config = registry.get_config(selected_model)
            if model_config:
                input_cost = (response.usage.prompt_tokens / 1_000_000) * model_config.input_price
                output_cost = (response.usage.completion_tokens / 1_000_000) * model_config.output_price
                total_cost = input_cost + output_cost
                
                budget_middleware.record_cost(user_id, total_cost)
        
        return result


@app.get("/health")
async def health_check() -> Dict:
    """健康检查接口"""
    healthy_models = registry.list_healthy_models()
    all_models = registry.list_models()
    
    return {
        "status": "healthy" if healthy_models else "degraded",
        "healthy_models": len(healthy_models),
        "total_models": len(all_models),
        "models": {
            name: registry.is_healthy(name)
            for name in all_models
        }
    }


@app.get("/stats")
async def get_stats() -> Dict:
    """获取网关统计信息"""
    return {
        "total_models": len(registry.list_models()),
        "healthy_models": len(registry.list_healthy_models()),
        "global_daily_cost": budget_middleware.global_daily_cost if budget_middleware else 0,
        "routing_strategy": config.routing.strategy,
    }


# ============================================================
# 启动入口
# ============================================================

if __name__ == "__main__":
    # 从配置中读取启动参数
    config_path = Path(__file__).parent / "config.yaml"
    startup_config = GatewayConfig.from_yaml(str(config_path))
    
    uvicorn.run(
        "main:app",
        host=startup_config.gateway.host,
        port=startup_config.gateway.port,
        workers=startup_config.gateway.workers,
        reload=startup_config.gateway.debug,
    )
