"""
综合示例：重试 + 限流 + 熔断器

展示三种模式如何协同工作
"""

import asyncio
import time
import random
from reliability import (
    RetryPolicy, retry_with_policy,
    TokenBucket, SlidingWindow,
    CircuitBreaker, CircuitBreakerOpenError,
)


class ResilientAPIClient:
    """韧性API客户端
    
    整合重试、限流、熔断器三种模式
    """
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        
        # 重试策略：最多3次，指数退避
        self.retry_policy = RetryPolicy(
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0,
            backoff_multiplier=2.0,
            jitter=True,
            retryable_exceptions=(ConnectionError, TimeoutError),
        )
        
        # 令牌桶限流：容量10，每秒补充5个
        self.token_bucket = TokenBucket(
            capacity=10,
            refill_rate=5.0,
        )
        
        # 滑动窗口限流：60秒内最多30个请求
        self.sliding_window = SlidingWindow(
            max_requests=30,
            window_size=60.0,
        )
        
        # 熔断器：5次失败后打开，30秒后半开，2次成功后关闭
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=30.0,
            success_threshold=2,
            expected_exception=(ConnectionError, TimeoutError, Exception),
        )
        
        # 统计信息
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "rate_limited": 0,
            "circuit_open": 0,
            "retries": 0,
        }
    
    async def call_api(self, endpoint: str, **kwargs):
        """调用API（带完整保护）
        
        执行顺序：
        1. 检查熔断器状态
        2. 检查限流器
        3. 执行请求（带重试）
        """
        self.stats["total_requests"] += 1
        
        # 步骤1: 检查熔断器
        if self.circuit_breaker.state.value == "open":
            self.stats["circuit_open"] += 1
            raise CircuitBreakerOpenError(
                f"服务 {self.service_name} 熔断器已打开"
            )
        
        # 步骤2: 检查限流器
        try:
            self.token_bucket.acquire()
        except Exception as e:
            self.stats["rate_limited"] += 1
            raise
        
        try:
            self.sliding_window.acquire()
        except Exception as e:
            self.stats["rate_limited"] += 1
            raise
        
        # 步骤3: 通过熔断器执行请求（带重试）
        async def make_request():
            # 模拟API调用
            delay = random.uniform(0.1, 0.5)
            await asyncio.sleep(delay)
            
            # 模拟不同的失败场景
            if random.random() < 0.3:  # 30%失败率
                error_type = random.choice(["connection", "timeout", "server"])
                if error_type == "connection":
                    raise ConnectionError("连接失败")
                elif error_type == "timeout":
                    raise TimeoutError("请求超时")
                else:
                    raise Exception("服务器错误")
            
            return {
                "endpoint": endpoint,
                "status": "success",
                "data": f"响应数据 {random.randint(1000, 9999)}",
            }
        
        # 使用重试包装器
        retryable_request = retry_with_policy(self.retry_policy)(make_request)
        
        try:
            # 通过熔断器调用
            result = await self.circuit_breaker.call(retryable_request)
            self.stats["successful_requests"] += 1
            return result
            
        except CircuitBreakerOpenError as e:
            self.stats["circuit_open"] += 1
            raise
        except Exception as e:
            self.stats["failed_requests"] += 1
            raise
    
    def get_stats(self):
        """获取统计信息"""
        return {
            **self.stats,
            "circuit_breaker": {
                "state": self.circuit_breaker.state.value,
                "stats": self.circuit_breaker.stats,
            },
            "rate_limiter": {
                "token_bucket": {
                    "tokens": self.token_bucket.tokens,
                    "capacity": self.token_bucket.capacity,
                },
                "sliding_window": {
                    "current_count": self.sliding_window.current_count,
                    "max_requests": self.sliding_window.max_requests,
                },
            },
        }


async def example_comprehensive():
    """综合示例：模拟真实场景"""
    print("=" * 70)
    print("综合示例：韧性API客户端")
    print("=" * 70)
    print()
    
    # 创建客户端
    client = ResilientAPIClient("example-service")
    
    print("场景：发送50个并发请求")
    print("保护机制：重试（3次）+ 限流（10令牌/秒，30次/分钟）+ 熔断器（5次失败）")
    print("-" * 70)
    
    # 发送请求
    results = {"success": 0, "failed": 0, "rate_limited": 0, "circuit_open": 0}
    
    async def send_request(i):
        try:
            result = await client.call_api(f"/api/endpoint/{i}")
            results["success"] += 1
            return ("success", result)
        except CircuitBreakerOpenError:
            results["circuit_open"] += 1
            return ("circuit_open", None)
        except Exception as e:
            if "rate limit" in str(e).lower() or "限流" in str(e):
                results["rate_limited"] += 1
                return ("rate_limited", str(e))
            else:
                results["failed"] += 1
                return ("failed", str(e))
    
    # 并发发送50个请求
    tasks = [send_request(i) for i in range(50)]
    responses = await asyncio.gather(*tasks)
    
    # 统计结果
    print(f"\n执行结果:")
    print(f"  总请求数: {client.stats['total_requests']}")
    print(f"  成功: {results['success']} ({results['success']/50*100:.1f}%)")
    print(f"  失败: {results['failed']} ({results['failed']/50*100:.1f}%)")
    print(f"  被限流: {results['rate_limited']} ({results['rate_limited']/50*100:.1f}%)")
    print(f"  熔断器打开: {results['circuit_open']} ({results['circuit_open']/50*100:.1f}%)")
    
    # 显示详细统计
    stats = client.get_stats()
    print(f"\n详细统计:")
    print(f"  熔断器状态: {stats['circuit_breaker']['state']}")
    print(f"  令牌桶: {stats['rate_limiter']['token_bucket']['tokens']:.1f}/{stats['rate_limiter']['token_bucket']['capacity']}")
    print(f"  滑动窗口: {stats['rate_limiter']['sliding_window']['current_count']}/{stats['rate_limiter']['sliding_window']['max_requests']}")
    
    print()


async def example_cascading_failures():
    """示例：级联故障场景"""
    print("=" * 70)
    print("示例：级联故障与恢复")
    print("=" * 70)
    print()
    
    # 创建两个服务的客户端
    service_a = ResilientAPIClient("service-a")
    service_b = ResilientAPIClient("service-b")
    
    print("场景：服务A依赖服务B，服务B开始故障")
    print("-" * 70)
    
    # 阶段1: 正常情况
    print("\n阶段1: 正常情况（前10个请求）")
    for i in range(10):
        try:
            result_a = await service_a.call_api("/process")
            result_b = await service_b.call_api("/validate")
            print(f"  请求 {i+1}: A={result_a['status']}, B={result_b['status']}")
        except Exception as e:
            print(f"  请求 {i+1}: 失败 - {type(e).__name__}")
    
    # 阶段2: 服务B开始故障（模拟）
    print("\n阶段2: 服务B开始故障（中间10个请求）")
    
    # 临时修改服务B的熔断器阈值
    service_b.circuit_breaker.failure_threshold = 2
    
    for i in range(10):
        try:
            result_a = await service_a.call_api("/process")
            result_b = await service_b.call_api("/validate")
            print(f"  请求 {i+1}: A=成功, B=成功")
        except CircuitBreakerOpenError:
            print(f"  请求 {i+1}: B熔断器打开")
        except Exception as e:
            print(f"  请求 {i+1}: B失败 - {type(e).__name__}")
    
    # 阶段3: 服务B恢复
    print("\n阶段3: 等待服务B恢复（30秒）")
    print("等待中...")
    await asyncio.sleep(30)
    
    # 重置服务B
    service_b.circuit_breaker.reset()
    
    print("\n阶段4: 服务B恢复后（后10个请求）")
    for i in range(10):
        try:
            result_a = await service_a.call_api("/process")
            result_b = await service_b.call_api("/validate")
            print(f"  请求 {i+1}: A=成功, B=成功")
        except Exception as e:
            print(f"  请求 {i+1}: 失败 - {type(e).__name__}")
    
    print()


async def example_adaptive_protection():
    """示例：自适应保护"""
    print("=" * 70)
    print("示例：自适应保护策略")
    print("=" * 70)
    print()
    
    client = ResilientAPIClient("adaptive-service")
    
    print("场景：根据系统负载动态调整保护参数")
    print("-" * 70)
    
    # 初始配置
    print("\n初始配置:")
    print(f"  令牌桶容量: {client.token_bucket.capacity}")
    print(f"  滑动窗口限制: {client.sliding_window.max_requests}")
    print(f"  熔断器阈值: {client.circuit_breaker.failure_threshold}")
    
    # 阶段1: 低负载
    print("\n阶段1: 低负载（发送10个请求）")
    for i in range(10):
        try:
            result = await client.call_api(f"/low-load/{i}")
            print(f"  请求 {i+1}: 成功")
        except Exception as e:
            print(f"  请求 {i+1}: {type(e).__name__}")
    
    # 阶段2: 检测到高负载，调整参数
    print("\n阶段2: 检测到高负载，收紧保护参数")
    client.token_bucket.capacity = 5  # 降低容量
    client.token_bucket.refill_rate = 2.0  # 降低补充速率
    client.sliding_window.max_requests = 15  # 降低窗口限制
    client.circuit_breaker.failure_threshold = 3  # 更容易触发熔断
    
    print(f"  新令牌桶容量: {client.token_bucket.capacity}")
    print(f"  新滑动窗口限制: {client.sliding_window.max_requests}")
    print(f"  新熔断器阈值: {client.circuit_breaker.failure_threshold}")
    
    print("\n发送20个请求（受限流保护）:")
    success_count = 0
    for i in range(20):
        try:
            result = await client.call_api(f"/high-load/{i}")
            success_count += 1
        except Exception:
            pass
    
    print(f"  成功请求: {success_count}/20")
    
    # 阶段3: 负载恢复，放宽参数
    print("\n阶段3: 负载恢复，放宽保护参数")
    client.token_bucket.capacity = 15
    client.token_bucket.refill_rate = 10.0
    client.sliding_window.max_requests = 50
    client.circuit_breaker.failure_threshold = 10
    
    print(f"  新令牌桶容量: {client.token_bucket.capacity}")
    print(f"  新滑动窗口限制: {client.sliding_window.max_requests}")
    print(f"  新熔断器阈值: {client.circuit_breaker.failure_threshold}")
    
    print("\n发送30个请求（负载恢复）:")
    success_count = 0
    for i in range(30):
        try:
            result = await client.call_api(f"/recovered/{i}")
            success_count += 1
        except Exception:
            pass
    
    print(f"  成功请求: {success_count}/30")
    
    print()


async def main():
    """运行所有综合示例"""
    print("\n" + "=" * 70)
    print("综合示例：重试 + 限流 + 熔断器")
    print("=" * 70 + "\n")
    
    await example_comprehensive()
    await asyncio.sleep(2)
    
    await example_cascading_failures()
    await asyncio.sleep(2)
    
    await example_adaptive_protection()
    
    print("=" * 70)
    print("所有综合示例执行完毕")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
