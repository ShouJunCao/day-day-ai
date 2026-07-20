"""
fallback_handler.py — 兜底策略处理器
当用户输入超出系统处理能力时，执行降级策略。
支持多级兜底：重试引导、意图推测、转人工、礼貌结束。
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class FallbackLevel(Enum):
    """兜底级别"""
    LEVEL1_RETRY = "retry"                    # 一级：引导重试
    LEVEL2_SUGGEST = "suggest"                # 二级：建议选项
    LEVEL3_PARTIAL = "partial"                # 三级：部分响应
    LEVEL4_TRANSFER = "transfer"              # 四级：转人工
    LEVEL5_END = "end"                        # 五级：礼貌结束


@dataclass
class FallbackResponse:
    """兜底响应"""
    level: FallbackLevel
    text: str
    options: list[str] = field(default_factory=list)
    should_transfer: bool = False
    confidence: float = 0.0


@dataclass
class FallbackHandler:
    """
    兜底策略处理器：当系统无法正常处理用户输入时，
    根据上下文和失败次数选择合适的降级策略。
    
    策略梯度：
    LEVEL1: 温和引导重试（"您能换一种方式说吗？"）
    LEVEL2: 提供预设选项（"您是想问A还是B？"）
    LEVEL3: 给出部分/模糊响应（"关于X的信息是..."）
    LEVEL4: 转接人工客服
    LEVEL5: 礼貌结束对话
    """
    
    max_retries: int = 3                     # 最大重试次数
    current_retry_count: int = 0             # 当前重试计数
    transfer_threshold: int = 3              # 转人工阈值
    fallback_responses: dict = field(default_factory=dict)
    
    def __post_init__(self):
        self._init_responses()
    
    def _init_responses(self):
        """初始化各级兜底话术"""
        self.fallback_responses = {
            FallbackLevel.LEVEL1_RETRY: FallbackResponse(
                level=FallbackLevel.LEVEL1_RETRY,
                text=(
                    "抱歉，我没有完全理解您的意思。\n"
                    "您能换一种方式描述一下吗？"
                ),
                confidence=0.3,
            ),
            FallbackLevel.LEVEL2_SUGGEST: FallbackResponse(
                level=FallbackLevel.LEVEL2_SUGGEST,
                text="我可能理解有误，您是想了解以下内容吗？",
                options=["预订酒店", "查询订单", "取消预订", "价格咨询"],
                confidence=0.2,
            ),
            FallbackLevel.LEVEL3_PARTIAL: FallbackResponse(
                level=FallbackLevel.LEVEL3_PARTIAL,
                text=(
                    "我没有找到完全匹配的答案，\n"
                    "但以下信息可能对您有帮助..."
                ),
                confidence=0.1,
            ),
            FallbackLevel.LEVEL4_TRANSFER: FallbackResponse(
                level=FallbackLevel.LEVEL4_TRANSFER,
                text=(
                    "这个问题超出了我的处理能力。\n"
                    "正在为您转接人工客服，请稍候..."
                ),
                should_transfer=True,
                confidence=0.0,
            ),
            FallbackLevel.LEVEL5_END: FallbackResponse(
                level=FallbackLevel.LEVEL5_END,
                text=(
                    "感谢您的使用！\n"
                    "如有其他问题，欢迎随时联系我们。\n"
                    "祝您生活愉快！"
                ),
                confidence=0.0,
            ),
        }
    
    def handle(self, context: Optional[dict] = None) -> FallbackResponse:
        """
        根据当前重试次数选择适当的兜底级别。
        
        策略：
        - 第1次失败：温和引导重试
        - 第2次失败：提供预设选项
        - 第3次失败：部分响应 + 建议转人工
        - 超过阈值：转人工或礼貌结束
        """
        self.current_retry_count += 1
        
        if self.current_retry_count == 1:
            return self.fallback_responses[FallbackLevel.LEVEL1_RETRY]
        elif self.current_retry_count == 2:
            return self.fallback_responses[FallbackLevel.LEVEL2_SUGGEST]
        elif self.current_retry_count <= self.transfer_threshold:
            return self.fallback_responses[FallbackLevel.LEVEL3_PARTIAL]
        else:
            return self.fallback_responses[FallbackLevel.LEVEL4_TRANSFER]
    
    def reset(self):
        """重置重试计数器"""
        self.current_retry_count = 0
    
    def get_escalation_summary(self) -> dict:
        """返回升级摘要"""
        return {
            "total_fallbacks": self.current_retry_count,
            "threshold": self.transfer_threshold,
            "should_transfer": self.current_retry_count >= self.transfer_threshold,
        }
