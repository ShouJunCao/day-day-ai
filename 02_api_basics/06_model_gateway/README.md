# 多模型网关（Multi-Model Gateway）

生产级多模型网关服务，提供统一的 OpenAI 兼容 API 接口，智能路由多个大模型提供商。

## 🚀 核心特性

- **统一接口**：所有模型使用相同的 OpenAI 兼容 API 格式
- **智能路由**：支持成本优先、质量优先、轮询等多种路由策略
- **故障转移**：模型故障时自动切换到备选模型
- **预算控制**：全局和用户级别的每日预算限制
- **速率限制**：防止恶意刷接口
- **请求日志**：完整的请求追踪和性能监控
- **健康检查**：实时监控各模型状态

## 📁 项目结构

```
06_model_gateway/
├── config.yaml              # 配置文件（模型、路由、预算）
├── requirements.txt         # Python依赖
├── main.py                  # FastAPI应用入口
├── .env.example             # 环境变量示例
├── README.md                # 本文件
└── gateway/                 # 核心网关模块
    ├── __init__.py
    ├── config.py            # 配置管理
    ├── registry.py          # 模型注册表
    ├── router.py            # 智能路由
    └── middleware.py        # 中间件（日志、限流、预算）
```

## 🔧 安装与启动

### 1. 安装依赖

```bash
cd workspace/02_api_basics/06_model_gateway
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API Keys
```

### 3. 配置模型（可选）

编辑 `config.yaml`，添加或修改模型配置：

```yaml
models:
  - name: "gpt-4o-mini"
    provider: "openai"
    api_key: "${OPENAI_API_KEY}"
    base_url: "https://api.openai.com/v1"
    input_price: 0.15
    output_price: 0.60
    enabled: true
```

### 4. 启动服务

```bash
# 方式1：直接运行
python main.py

# 方式2：使用uvicorn（推荐生产环境）
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📡 API 使用

### 列出可用模型

```bash
curl http://localhost:8000/v1/models
```

### 发送聊天请求

**非流式请求：**

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "你好，介绍一下自己"}
    ],
    "temperature": 0.7,
    "max_tokens": 500
  }'
```

**指定模型：**

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-chat",
    "messages": [
      {"role": "user", "content": "Python的装饰器是什么？"}
    ]
  }'
```

### 健康检查

```bash
curl http://localhost:8000/health
```

### 查看统计信息

```bash
curl http://localhost:8000/stats
```

## 🎯 路由策略

在 `config.yaml` 中配置路由策略：

```yaml
routing:
  strategy: "cost_first"  # 或 "quality_first" 或 "round_robin"
```

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| `cost_first` | 优先选择成本最低的模型 | 日常对话、简单任务 |
| `quality_first` | 优先选择质量最高的模型 | 复杂推理、专业任务 |
| `round_robin` | 轮询选择所有可用模型 | 负载均衡、测试 |

## 💰 预算控制

在 `config.yaml` 中配置预算限制：

```yaml
budget:
  global_daily_limit: 100.0  # 全局每日预算（美元）
  user_daily_limit: 10.0     # 每用户每日预算（美元）
  rate_limit_per_minute: 120 # 每分钟最大请求数
```

## 🔄 故障转移

当某个模型调用失败时，网关会自动：

1. 将模型标记为不健康
2. 尝试使用 `fallback_models` 中的备选模型
3. 如果所有备选都不可用，返回 503 错误

```yaml
routing:
  default_model: "gpt-4o-mini"
  fallback_models:
    - "deepseek-chat"
    - "qwen-plus"
```

## 🐍 Python 客户端使用

```python
from openai import OpenAI

# 指向网关地址
client = OpenAI(
    api_key="any-key",  # 网关会验证真实的API Key
    base_url="http://localhost:8000/v1"
)

# 发送请求（网关会自动选择模型）
response = client.chat.completions.create(
    messages=[
        {"role": "user", "content": "你好"}
    ]
)

print(response.choices[0].message.content)

# 指定特定模型
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "user", "content": "用Python写一个快速排序"}
    ]
)
```

## 📊 监控与日志

网关会记录：

- 每个请求的方法、路径、状态码、耗时
- 模型选择决策
- 故障转移事件
- 费用记录

日志输出示例：

```
2026-06-26 22:30:15 - gateway - INFO - 注册模型: gpt-4o-mini (openai)
2026-06-26 22:30:15 - gateway - INFO - 注册模型: deepseek-chat (openai)
2026-06-26 22:30:16 - gateway - INFO - 用户 127.0.0.1 -> 模型 gpt-4o-mini
2026-06-26 22:30:17 - gateway - INFO - POST /v1/chat/completions - 200 - 1.234s
```

## 🔐 安全建议

**生产环境部署时：**

1. **不要将 API Key 硬编码在配置文件中**，使用环境变量
2. **启用 HTTPS**（通过反向代理如 Nginx）
3. **添加认证中间件**（验证客户端的 API Key）
4. **限制网络访问**（只允许受信任的 IP）
5. **定期审查日志**（发现异常请求）

## 🚀 生产部署

### 使用 Docker（推荐）

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### 使用 systemd（Linux）

创建 `/etc/systemd/system/gateway.service`：

```ini
[Unit]
Description=Multi-Model Gateway
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/06_model_gateway
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

## 📝 扩展开发

### 添加新的模型提供商

1. 在 `config.yaml` 中添加模型配置
2. 如果是 OpenAI 兼容 API，无需修改代码
3. 如果是非标准 API，需要在 `registry.py` 中添加适配器

### 添加自定义中间件

参考 `middleware.py` 中的示例，创建新的中间件类：

```python
from starlette.middleware.base import BaseHTTPMiddleware

class CustomMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # 请求前处理
        response = await call_next(request)
        # 响应后处理
        return response
```

然后在 `main.py` 中注册：

```python
app.add_middleware(CustomMiddleware)
```

## 📄 License

MIT License - 可自由使用和修改
