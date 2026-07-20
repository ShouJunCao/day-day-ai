"""
multimodal_dialogue.py — 多模态对话处理器
支持文本、图片、语音三种模态的对话输入和输出。
实现模态检测、内容提取、跨模态融合回复。
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime


class Modality(Enum):
    """输入模态类型"""
    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"


@dataclass
class MultimodalInput:
    """多模态输入"""
    modality: Modality
    text: str = ""
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    transcribed_text: Optional[str] = None  # 语音转文字结果

    @property
    def primary_content(self) -> str:
        """获取主要文本内容"""
        if self.text:
            return self.text
        if self.transcribed_text:
            return self.transcribed_text
        return ""


@dataclass
class MultimodalResponse:
    """多模态输出"""
    text: str
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    modality: Modality = Modality.TEXT


@dataclass
class ModalityDetector:
    """
    模态检测器：识别用户输入的模态类型，
    并提取结构化信息。
    """

    def detect_from_text(self, text: str) -> Modality:
        """从文本内容推断意图模态"""
        # 简单的关键词启发式检测
        image_keywords = ["图片", "照片", "截图", "看一下", "看看"]
        voice_keywords = ["语音", "说一下", "读给我听"]

        for kw in image_keywords:
            if kw in text:
                return Modality.IMAGE
        for kw in voice_keywords:
            if kw in text:
                return Modality.VOICE

        return Modality.TEXT

    def detect_from_content_type(self, content_type: str) -> Modality:
        """从 MIME 类型推断模态"""
        if "image" in content_type:
            return Modality.IMAGE
        if "audio" in content_type:
            return Modality.VOICE
        return Modality.TEXT


@dataclass
class MultimodalDialogueProcessor:
    """
    多模态对话处理器：处理不同模态的输入，
    生成合适模态的输出。

    支持的模式：
    - 纯文本 → 纯文本（默认）
    - 图片 + 文本 → 文本分析
    - 语音 → 文本回复
    - 文本 → 语音回复
    """

    detector: ModalityDetector = field(default_factory=ModalityDetector)
    enable_vision: bool = False       # 是否启用图片理解
    enable_voice: bool = False        # 是否启用语音合成
    enable_asr: bool = False          # 是否启用语音识别

    def process(
        self,
        user_input: MultimodalInput,
        context: Optional[dict] = None,
    ) -> MultimodalResponse:
        """
        处理多模态输入，生成回复。
        """
        context = context or {}

        # 根据输入模态选择处理策略
        if user_input.modality == Modality.IMAGE:
            return self._handle_image(user_input, context)
        elif user_input.modality == Modality.VOICE:
            return self._handle_voice(user_input, context)
        else:
            return self._handle_text(user_input, context)

    def _handle_image(
        self, input: MultimodalInput, context: dict
    ) -> MultimodalResponse:
        """处理图片输入"""
        if self.enable_vision and input.image_url:
            # 调用视觉模型分析图片
            analysis = f"[图片分析] 已收到图片: {input.image_url}"
            return MultimodalResponse(
                text=f"我看到了您发送的图片。\n{input.text}\n{analysis}",
            )
        return MultimodalResponse(
            text="抱歉，当前不支持图片分析功能。",
        )

    def _handle_voice(
        self, input: MultimodalInput, context: dict
    ) -> MultimodalResponse:
        """处理语音输入"""
        if self.enable_asr and input.audio_url:
            # 语音转文字
            transcribed = input.transcribed_text or "[语音识别结果]"
            return MultimodalResponse(
                text=f"您说的是：{transcribed}\n我正在为您处理...",
            )
        return MultimodalResponse(
            text="抱歉，当前不支持语音输入功能。",
        )

    def _handle_text(
        self, input: MultimodalInput, context: dict
    ) -> MultimodalResponse:
        """处理纯文本输入"""
        # 检测用户是否期望特定模态的回复
        expected_modality = self.detector.detect_from_text(input.text)

        if expected_modality == Modality.VOICE and self.enable_voice:
            return MultimodalResponse(
                text=f"回复：{input.text}",
                audio_url="https://example.com/tts/output.mp3",
                modality=Modality.VOICE,
            )
        elif expected_modality == Modality.IMAGE:
            return MultimodalResponse(
                text=f"以下是相关图片：\n{input.text}",
                image_url="https://example.com/image/result.jpg",
                modality=Modality.IMAGE,
            )

        return MultimodalResponse(text=f"回复：{input.text}")
