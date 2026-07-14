"""
自定义异常类

为不同类型的API错误提供专门的异常类，便于精确捕获和处理
"""

from typing import Optional, Dict, Any


class APIError(Exception):
    """API错误的基类
    
    所有API相关的异常都应该继承自此类
    """
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class NetworkError(APIError):
    """网络错误
    
    包括：连接超时、DNS解析失败、网络中断等
    这类错误通常是暂时性的，可以重试
    """
    pass


class TimeoutError(NetworkError):
    """请求超时错误
    
    HTTP 408 或连接/读取超时
    """
    pass


class AuthenticationError(APIError):
    """认证错误
    
    HTTP 401 或 403
    包括：API Key无效、权限不足、认证过期等
    这类错误不应该重试（除非更新了认证信息）
    """
    pass


class RateLimitError(APIError):
    """限流错误
    
    HTTP 429
    请求频率超过API限制
    应该等待后重试
    """
    
    def __init__(
        self,
        message: str,
        retry_after: Optional[float] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class ServerError(APIError):
    """服务器错误
    
    HTTP 500, 502, 503, 504
    服务器端故障，通常是暂时性的，可以重试
    """
    pass


class ValidationError(APIError):
    """验证错误
    
    HTTP 400
    请求参数无效
    不应该重试（需要修正请求参数）
    """
    pass


class ResourceNotFoundError(APIError):
    """资源未找到
    
    HTTP 404
    请求的资源不存在
    不应该重试（除非资源是异步创建的）
    """
    pass


class RetryableError(Exception):
    """可重试错误的包装器
    
    用于在重试策略中标记某个错误是可重试的
    """
    
    def __init__(self, original_error: Exception, attempt: int):
        self.original_error = original_error
        self.attempt = attempt
        super().__init__(
            f"第 {attempt} 次尝试失败: {original_error}"
        )


def classify_http_error(status_code: int, message: str, response_data: Optional[Dict] = None) -> APIError:
    """根据HTTP状态码分类错误
    
    Args:
        status_code: HTTP状态码
        message: 错误消息
        response_data: 响应数据
        
    Returns:
        对应的异常实例
    """
    error_map = {
        400: ValidationError,
        401: AuthenticationError,
        403: AuthenticationError,
        404: ResourceNotFoundError,
        408: TimeoutError,
        429: RateLimitError,
        500: ServerError,
        502: ServerError,
        503: ServerError,
        504: TimeoutError,
    }
    
    error_class = error_map.get(status_code, APIError)
    return error_class(message, status_code=status_code, response_data=response_data)
