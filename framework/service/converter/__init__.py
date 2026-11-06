"""格式转换服务模块

提供各种格式转换功能，包括音频格式转换和语音识别。
"""

from .silk_converter_service import AudioConverterService, audio_converter_service, silk_converter_service
from .speech_to_text_service import SpeechToTextService, speech_to_text_service

__all__ = [
    "AudioConverterService",
    "audio_converter_service",
    "silk_converter_service",  # 兼容旧名称
    "SpeechToTextService",
    "speech_to_text_service",
]
