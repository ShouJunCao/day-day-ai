# API可靠性工具包

提供重试、限流、熔断器等API调用的最佳实践实现。

## 项目结构

```
07_retry_ratelimit_error/
├── reliability/                    # 核心工具包
│   ├── __init__.py                # 包初始化和导出
│   ├── retry.py                   # 重试策略实现
│   ├── ratelimit.py               # 限流器实现
│   ├── circuit_breaker.py         # 熔断器实现
│   └── errors.py                  # 自定义异常类
├── examples/                       # 使用示例
│   ├── retry_examples.py          # 重试策略示例
│   ├── ratelimit_examples.py      # 限流器示例
│   ├── circuit_breaker_examples.py # 熔断器示例
│   └── comprehensive_example.py   # 综合示例
├── tests/                          # 单元测试
│   ├── test_retry.py              # 重试策略测试
│   ├── test_ratelimit.py          # 限流器测试
│   └── test_circuit_breaker.py    # 熔断器测试
├── requirements.txt               # 依赖包
└── README.md                      # 项目说明
```

## 核心功能

### 1. 重试策略 (Retry)

实现指数退避重试机制，支持：
- 可配置的最大重试次数
- 指数退避延迟
- 随机抖动避免惊群效应
- 自定义可重试异常类型

```python
from reliability import RetryPolicy, retry_with_policy

policy = RetryPolicy(
    max_attempts=3,
    base_delay=1.0,
    backoff_multiplier=2.0,
    jitter=True,
)

@retry_with_policy(policy)
async def call_api():
    # API调用逻辑
    pass
```

### 2. 限流器 (Rate Limiter)

提供两种限流算法：

#### 令牌桶 (Token Bucket)
- 控制突发流量
- 允许一定程度的流量突发

```python
from reliability import TokenBucket

bucket = TokenBucket(capacity=10, refill_rate=2.0)
bucket.acquire()  # 获取令牌
```

#### 滑动窗口 (Sliding Window)
- 控制持续流量
- 精确控制时间窗口内的请求数

```python
from reliability import SlidingWindow

window = SlidingWindow(max_requests=100, window_size=60.0)
window.acquire()  # 检查并记录请求
```

### 3. 熔断器 (Circuit Breaker)

实现熔断器模式，防止故障蔓延：

- **关闭状态**: 正常处理请求
- **打开状态**: 快速失败，保护系统
- **半开状态**: 试探性恢复

```python
from reliability import CircuitBreaker

breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=30.0,
    success_threshold=2,
)

result = await breaker.call(unreliable_service)
```

## 综合使用

三种模式可以组合使用，构建韧性系统：

```python
from reliability import (
    RetryPolicy, retry_with_policy,
    TokenBucket, CircuitBreaker,
)

class ResilientClient:
    def __init__(self):
        self.retry_policy = RetryPolicy(max_attempts=3)
        self.rate_limiter = TokenBucket(capacity=10, refill_rate=5.0)
        self.circuit_breaker = CircuitBreaker(failure_threshold=5)
    
    async def call_api(self, endpoint):
        # 1. 检查熔断器
        if self.circuit_breaker.state == "open":
            raise CircuitBreakerOpenError()
        
        # 2. 检查限流
        self.rate_limiter.acquire()
        
        # 3. 执行请求（带重试）
        @retry_with_policy(self.retry_policy)
        async def make_request():
            return await http_call(endpoint)
        
        return await self.circuit_breaker.call(make_request)
```

## 运行示例

```bash
# 运行重试示例
python examples/retry_examples.py

# 运行限流器示例
python examples/ratelimit_examples.py

# 运行熔断器示例
python examples/circuit_breaker_examples.py

# 运行综合示例
python examples/comprehensive_example.py
```

## 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_retry.py
pytest tests/test_ratelimit.py
pytest tests/test_circuit_breaker.py
```

## 最佳实践

### 1. 重试策略

- ✅ 只对瞬态错误重试（网络超时、5xx错误）
- ✅ 使用指数退避避免过载
- ✅ 添加随机抖动避免惊群效应
- ❌ 不对4xx错误重试（客户端错误）
- ❌ 不设置过高的重试次数

### 2. 限流器

- ✅ 根据API配额设置限流参数
- ✅ 使用令牌桶控制突发流量
- ✅ 使用滑动窗口控制持续流量
- ✅ 组合使用多层限流
- ❌ 不要完全禁用限流

### 3. 熔断器

- ✅ 合理设置失败阈值
- ✅ 根据服务恢复时间设置恢复超时
- ✅ 监控熔断器状态
- ✅ 提供降级方案
- ❌ 不要对所有服务使用相同的阈值

## 学习资源

详细内容请参考HTML文档：`2_7_API重试限流与错误处理.html`
