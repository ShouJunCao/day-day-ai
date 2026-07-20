"""
example_usage.py — 4.6 多模态对话 使用示例
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from multimodal_dialogue import (
    MultimodalInput, Modality, ModalityDetector,
    MultimodalDialogueProcessor,
)


def demo_modality_detection():
    """演示模态检测"""
    print("=" * 60)
    print("  多模态对话 — 模态检测演示")
    print("=" * 60)

    detector = ModalityDetector()

    # 从文本关键词检测
    test_texts = [
        "帮我看看这张照片",
        "这个截图有问题吗？",
        "语音播报一下",
        "请读给我听",
        "今天天气怎么样",
    ]

    print("\n文本关键词检测:")
    for text in test_texts:
        modality = detector.detect_from_text(text)
        print(f"  \"{text}\" → {modality.value}")

    # 从 MIME 类型检测
    print("\nMIME 类型检测:")
    mime_types = [
        "image/png",
        "image/jpeg",
        "audio/mpeg",
        "audio/wav",
        "text/plain",
        "application/json",
    ]
    for mime in mime_types:
        modality = detector.detect_from_content_type(mime)
        print(f"  {mime} → {modality.value}")


def demo_multimodal_processing():
    """演示多模态处理"""
    print("\n" + "=" * 60)
    print("  多模态对话 — 处理器演示")
    print("=" * 60)

    # 启用所有功能
    processor = MultimodalDialogueProcessor(
        enable_vision=True,
        enable_voice=True,
        enable_asr=True,
    )

    # 场景 1：纯文本
    print("\n场景 1: 纯文本输入")
    inp1 = MultimodalInput(modality=Modality.TEXT, text="今天天气怎么样？")
    resp1 = processor.process(inp1)
    print(f"  输入: {inp1.text}")
    print(f"  回复: {resp1.text}")
    print(f"  模态: {resp1.modality.value}")

    # 场景 2：图片 + 文本
    print("\n场景 2: 图片 + 文本")
    inp2 = MultimodalInput(
        modality=Modality.IMAGE,
        text="这张图片里有什么？",
        image_url="https://example.com/photo.jpg",
    )
    resp2 = processor.process(inp2)
    print(f"  输入: [图片] {inp2.text}")
    print(f"  回复: {resp2.text}")

    # 场景 3：语音输入
    print("\n场景 3: 语音输入")
    inp3 = MultimodalInput(
        modality=Modality.VOICE,
        audio_url="https://example.com/voice.mp3",
        transcribed_text="我想预订后天去北京的酒店",
    )
    resp3 = processor.process(inp3)
    print(f"  输入: [语音] → \"{inp3.transcribed_text}\"")
    print(f"  回复: {resp3.text}")

    # 场景 4：用户期望语音回复
    print("\n场景 4: 文本输入 → 语音回复")
    inp4 = MultimodalInput(
        modality=Modality.TEXT,
        text="读给我听今天的新闻",
    )
    resp4 = processor.process(inp4)
    print(f"  输入: {inp4.text}")
    print(f"  回复: {resp4.text}")
    print(f"  输出模态: {resp4.modality.value} (audio: {resp4.audio_url})")

    # 场景 5：功能未启用
    print("\n场景 5: 功能未启用时")
    processor_limited = MultimodalDialogueProcessor(
        enable_vision=False,
        enable_voice=False,
        enable_asr=False,
    )
    inp5 = MultimodalInput(
        modality=Modality.IMAGE,
        image_url="https://example.com/photo.jpg",
    )
    resp5 = processor_limited.process(inp5)
    print(f"  输入: [图片]")
    print(f"  回复: {resp5.text}")


if __name__ == "__main__":
    demo_modality_detection()
    demo_multimodal_processing()
