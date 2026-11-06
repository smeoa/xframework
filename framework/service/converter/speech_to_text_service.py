"""语音转文字服务模?

使用本地Whisper模型进行语音识别(离线)

配置示例?env):
SPEECH_WHISPER_MODEL=base  # tiny, base, small, medium, large

安装依赖?
pip install openai-whisper
"""

import logging
import asyncio
from typing import Optional
from framework.core.config import config

logger = logging.getLogger(__name__)


class SpeechToTextService:
    
    def __init__(self):
        self._initialized = False
        self._client = None
        
    async def init(self):
        """初始化语音转文字服务"""
        if self._initialized:
            return
        
        try:
            import whisper
            
            model_name = config.get_str("speech.whisper.model", "base")
            self._client = whisper.load_model(model_name)
            logger.info(f"[语音转文字] Whisisper模型加载成功: {model_name}")
        except ImportError:
            logger.warning("[语音转文字] 未安装whisper库,请运? pip install openai-whisper")
        except Exception as e:
            logger.warning(f"[语音转文字] Whisper模型加载失败: {str(e)}")
            
        self._initialized = True
        
    async def recognize(self, audio_file_path: str, language: str = "zh") -> Optional[str]:
        """识别语音文件并返回文?
        
        Args:
            audio_file_path: 语音文件路径
            language: 语言代码,默认中?zh)
            
        Returns:
            识别出的文字,失败返回None
        """
        if not self._initialized:
            await self.init()
            
        if not self._client:
            logger.warning("[语音转文字] 服务未初始化")
            return None
            
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._client.transcribe(audio_file_path, language=language)
            )
            
            text = result.get("text", "").strip()
            if text:
                logger.info(f"[语音转文字] 识别成功: {text[:50]}")
                return text
            else:
                logger.warning("[语音转文字] 识别结果为空")
                return None
        except Exception as e:
            logger.error(f"[语音转文字] 识别失败: {str(e)}")
            return None


speech_to_text_service = SpeechToTextService()
