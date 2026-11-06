"""音频格式转换服务模块

提供基于 ffmpeg 的音频格式转换功能，主要用于微信 silk 语音格式转换。
"""

import logging
import os
import subprocess

import httpx

logger = logging.getLogger(__name__)


class AudioConverterService:
    """音频格式转换服务（基于 ffmpeg）"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._ffmpeg_path = None
        self._ffmpeg_available = self._check_ffmpeg()
        logger.info(f"[音频转换] 初始化完成 | ffmpeg={'可用' if self._ffmpeg_available else '不可用'}")

    def _check_ffmpeg(self) -> bool:
        """检查 ffmpeg 是否可用，优先使用项目目录下的版本"""
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Windows 下检查项目目录中的 ffmpeg.exe
        if os.name == "nt":
            possible_paths = [
                os.path.join(current_dir, "ffmpeg", "bin", "ffmpeg.exe"),
                os.path.join(current_dir, "ffmpeg", "ffmpeg.exe"),
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    self._ffmpeg_path = path
                    logger.info(f"[音频转换] 使用项目目录下的 ffmpeg: {path}")
                    return True

        # 检查系统 PATH 中的 ffmpeg
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                self._ffmpeg_path = "ffmpeg"
                logger.info("[音频转换] 使用系统 PATH 中的 ffmpeg")
                return True
        except Exception:
            pass

        logger.warning("[音频转换] ffmpeg 未找到，请安装 ffmpeg 或放到 framework/service/converter/ffmpeg/ 目录")
        return False

    def _get_ffmpeg_path(self) -> str:
        """获取 ffmpeg 可执行文件路径"""
        return self._ffmpeg_path or "ffmpeg"

    def is_available(self) -> bool:
        """检查转换服务是否可用"""
        return self._ffmpeg_available

    def convert_to_mp3(self, audio_data: bytes, input_format: str = "silk") -> bytes:
        """将音频数据转换为 MP3 格式

        Args:
            audio_data: 原始音频数据
            input_format: 输入格式（silk, pcm, wav 等）

        Returns:
            转换后的 MP3 数据，失败返回空 bytes
        """
        if not audio_data or not self._ffmpeg_available:
            return b""

        try:
            ffmpeg_path = self._get_ffmpeg_path()

            # 构建 ffmpeg 命令
            if input_format.lower() == "silk":
                # silk 格式需要特殊处理
                cmd = [
                    ffmpeg_path, "-y",
                    "-f", "s16le", "-ar", "24000", "-ac", "1",
                    "-i", "-",
                    "-ar", "24000", "-ac", "1",
                    "-f", "mp3", "-"
                ]
            else:
                # 其他格式让 ffmpeg 自动检测
                cmd = [
                    ffmpeg_path, "-y",
                    "-f", input_format, "-i", "-",
                    "-ar", "24000", "-ac", "1",
                    "-f", "mp3", "-"
                ]

            result = subprocess.run(
                cmd,
                input=audio_data,
                capture_output=True,
                timeout=60
            )

            if result.returncode == 0 and result.stdout:
                logger.info(f"[音频转换] 转换成功 | 输入: {len(audio_data)} bytes | 输出: {len(result.stdout)} bytes")
                return result.stdout
            else:
                stderr = result.stderr.decode("utf-8", errors="ignore")[:500]
                logger.warning(f"[音频转换] ffmpeg 转换失败: {stderr}")
                return b""

        except subprocess.TimeoutExpired:
            logger.error("[音频转换] ffmpeg 超时")
            return b""
        except Exception as e:
            logger.error(f"[音频转换] 转换异常: {str(e)}")
            return b""

    def convert_silk_to_mp3(self, silk_data: bytes) -> bytes:
        """将微信 silk 格式语音转换为 MP3

        Args:
            silk_data: silk 格式的音频数据

        Returns:
            转换后的 MP3 数据
        """
        if not silk_data:
            return b""

        # 微信 silk 格式有特殊的文件头，需要去掉前 2 字节
        # silk 文件头: #!SILK_V3
        if silk_data.startswith(b"#!SILK_V3"):
            # 标准 silk 格式，直接使用
            pass
        elif len(silk_data) > 2 and silk_data[0] == 0x02:
            # 微信 silk 格式，去掉第一个字节（0x02）
            silk_data = silk_data[1:]

        return self.convert_to_mp3(silk_data, "silk")

    async def convert_silk_url_to_mp3(self, url: str) -> bytes:
        """从 URL 下载 silk 文件并转换为 MP3 格式

        Args:
            url: silk 文件的 URL 地址

        Returns:
            转换后的 MP3 数据，失败返回空 bytes
        """
        if not url:
            return b""

        try:
            async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                silk_data = resp.content

            if not silk_data:
                logger.warning("[音频转换] 下载的文件为空")
                return b""

            logger.info(f"[音频转换] 下载成功，大小: {len(silk_data)} bytes")
            return self.convert_silk_to_mp3(silk_data)

        except httpx.HTTPStatusError as e:
            logger.error(f"[音频转换] 下载失败 HTTP {e.response.status_code}: {url}")
            return b""
        except httpx.RequestError as e:
            logger.error(f"[音频转换] 下载请求失败: {str(e)}")
            return b""
        except Exception as e:
            logger.error(f"[音频转换] 转换异常: {str(e)}", exc_info=True)
            return b""


# 单例实例
audio_converter_service = AudioConverterService()

# 兼容旧名称
silk_converter_service = audio_converter_service
