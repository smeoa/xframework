"""图片理解工具模块

提供图片内容分析和文字提取功能，统一使用多模态模型。
"""

import re
import os
import json
import time
import aiohttp
import base64
import urllib.parse
import logging
import hashlib
import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta

from framework.core.config import config
from ..core import Agent
from ..prompt import UserPrompts

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "media"
)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

_last_cleanup_time = 0
_analysis_cache: Dict[str, Dict[str, Any]] = {}

# Agent.chat 吞掉异常后返回的伪文本前缀（据此把「伪成功」还原为失败，避免误当结果缓存）
_AGENT_FAILURE_PREFIX = "AI服务调用失败"


def _get_cache_key(url: str) -> str:
    """生成图片URL的缓存键"""
    return hashlib.md5(url.encode("utf-8")).hexdigest()


def _get_cached_result(url: str, ttl_hours: int) -> Optional[str]:
    """从缓存获取图片分析结果"""
    global _analysis_cache

    cache_key = _get_cache_key(url)
    entry = _analysis_cache.get(cache_key)

    if entry:
        if datetime.now(timezone.utc) - entry["timestamp"] < timedelta(hours=ttl_hours):
            logger.debug(f"[图片理解] 缓存命中 | url={url[:30]}...")
            return entry["result"]
        else:
            del _analysis_cache[cache_key]

    return None


def _set_cached_result(url: str, result: str):
    """设置图片分析结果到缓存"""
    global _analysis_cache

    cache_key = _get_cache_key(url)
    _analysis_cache[cache_key] = {
        "result": result,
        "timestamp": datetime.now(timezone.utc),
    }


def _cleanup_old_files(cache_ttl_hours: int):
    """清理超过 TTL 的临时下载文件"""
    global _last_cleanup_time

    now = time.time()
    cleanup_interval = 3600
    if now - _last_cleanup_time < cleanup_interval:
        return

    ttl_seconds = cache_ttl_hours * 3600

    try:
        count = 0
        for filename in os.listdir(DOWNLOAD_DIR):
            filepath = os.path.join(DOWNLOAD_DIR, filename)
            if (
                os.path.isfile(filepath)
                and now - os.path.getmtime(filepath) > ttl_seconds
            ):
                os.remove(filepath)
                count += 1
        if count > 0:
            logger.info(f"[图片理解] 已清理 {count} 个过期缓存文件 (TTL={cache_ttl_hours}h)")
        _last_cleanup_time = now
    except Exception as e:
        logger.warning(f"[图片理解] 清理缓存文件失败: {e}")
        _last_cleanup_time = now


def _safe_filename(url: str, ext: str = "") -> str:
    """从URL中提取文件名并清理特殊字符"""
    original_name = ""

    if url:
        parsed = urllib.parse.urlparse(url)
        path = parsed.path

        if path:
            decoded_path = urllib.parse.unquote(path)
            name = os.path.basename(decoded_path)
            if name and "." in name:
                original_name = name

        if not original_name:
            query = urllib.parse.parse_qs(parsed.query)
            if "filename" in query:
                original_name = query["filename"][0]
            elif "fileName" in query:
                original_name = query["fileName"][0]

    if original_name:
        safe_name = re.sub(r'[<>:"|?*]', "_", original_name)
        safe_name = safe_name.strip()

        if ext and safe_name.lower().endswith(f".{ext.lower()}"):
            name_without_ext = safe_name[: -len(ext) - 1]
            return f"{name_without_ext}_{int(time.time() * 1000)}.{ext}"
        elif ext:
            return f"{safe_name}_{int(time.time() * 1000)}.{ext}"
        else:
            return f"{safe_name}_{int(time.time() * 1000)}"

    return f"file_{int(time.time() * 1000)}.{ext}" if ext else f"file_{int(time.time() * 1000)}"


async def _download_file(url: str, filename: str, download_timeout: int) -> str:
    """下载文件到本地"""
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    if os.path.exists(filepath):
        return filepath

    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=download_timeout)
        ) as session:
            async with session.get(url, allow_redirects=True) as response:
                if response.status != 200:
                    raise Exception(f"下载返回状态码{response.status}")
                data = await response.read()
                with open(filepath, "wb") as f:
                    f.write(data)
        return filepath
    except Exception as e:
        raise Exception(f"文件下载失败: {str(e)}")


async def _call_vision_model(
    image_base64: str, 
    prompt: str,
    model_base_url: str,
    model_api_key: str,
    model_name: str
) -> str:
    """调用支持视觉的 AI 模型（基于 Agent）"""
    agent = Agent(
        base_url=model_base_url,
        api_key=model_api_key,
        model_name=model_name,
    )

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}"
                    },
                },
                {"type": "text", "text": prompt},
            ],
        }
    ]

    try:
        result = await agent.chat(context=messages, max_tokens=1000)
        content = (result.content or "").strip()
    except Exception as e:
        raise Exception(f"视觉模型调用失败: {str(e)}")
    # Agent.chat 会吞掉异常并返回「AI服务调用失败: xxx」伪文本，这里还原为真正的失败，
    # 否则调用方会把这段伪文本当成正常描述返回并缓存（服务恢复后仍长期返回失败内容）
    if not content or content.startswith(_AGENT_FAILURE_PREFIX):
        raise Exception(f"视觉模型调用失败: {content or '模型返回空响应'}")
    return content


async def understand_image(image_url: str) -> dict:
    """图片理解工具"""
    enabled = config.get_bool("VISION_ENABLED", True)
    if not enabled:
        return {"success": False, "error": "图片理解服务已禁用", "fallback": "图片理解服务已禁用"}

    if not image_url or not image_url.strip():
        return {"success": False, "error": "图片URL无效", "fallback": "请提供有效的图片URL"}

    url = image_url.strip()

    cache_ttl_hours = config.get_int("VISION_RESULT_CACHE_TTL_HOURS", 24)
    download_timeout = config.get_int("VISION_DOWNLOAD_TIMEOUT_SEC", 60)
    model_base_url = config.get_str("VISION_MODEL_BASE_URL", "http://localhost:11434/v1")
    model_api_key = config.get_str("VISION_MODEL_API_KEY", "ollama")
    model_name = config.get_str("VISION_MODEL_NAME", "qwen3.5:9b")

    _cleanup_old_files(config.get_int("VISION_CACHE_TTL_HOURS", 24))

    cached_result = _get_cached_result(url, cache_ttl_hours)
    if cached_result is not None:
        return {"success": True, "result": cached_result}

    filename = _safe_filename(url, "jpg")

    try:
        print(f"[图片理解] 开始分析图片: {url[:50]}...")

        filepath = await _download_file(url, filename, download_timeout)
        print(f"[图片理解] 图片已下载: {os.path.basename(filepath)}")

        with open(filepath, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
        print(f"[图片理解] 图片已加载 (大小: {len(image_data)//1024} KB)")

        prompt = UserPrompts.IMAGE_ANALYSIS

        print(f"[图片理解] 调用多模态模型分析...")
        vision_result = await _call_vision_model(image_data, prompt, model_base_url, model_api_key, model_name)

        _set_cached_result(url, vision_result)

        print(f"[图片理解] 分析完成")
        print(f"[图片理解] 分析结果:")
        print(vision_result)
        print("-" * 60)

        return {"success": True, "result": vision_result}

    except Exception as e:
        logger.error(f"[图片理解] 综合分析失败: {str(e)}")
        print(f"[图片理解] 分析失败: {str(e)}")
        print("-" * 60)
        return {"success": False, "error": str(e), "fallback": f"无法分析图片 {image_url}。请检查图片URL是否有效，或者提供图片的描述信息。"}


def _parse_ocr_text(raw: str) -> str:
    """从模型返回中解析文字原文：优先取 JSON 的 text 字段，解析失败则退回原文"""
    content = (raw or "").strip()
    if not content:
        return ""
    match = re.search(r"\{.*\}", content, re.S)
    if match:
        try:
            data = json.loads(match.group(0))
            if isinstance(data, dict) and "text" in data:
                return str(data.get("text") or "").strip()
        except (ValueError, TypeError):
            pass
    return content


async def extract_image_text(image_url: str) -> dict:
    """提取图片中的文字原文（发布前合规检查用：判定中文 / 联系方式）

    与 understand_image 的区别：使用「只提取原文、不翻译不解释」的提示词并单独缓存，
    避免模型自身的分析文字混入，把中文 / 联系方式误判成图片内容。

    Returns:
        {"success": bool, "text": 识别到的文字原文, "error": 失败原因}
    """
    if not config.get_bool("VISION_ENABLED", True):
        return {"success": False, "error": "图片理解服务已禁用", "text": ""}

    if not image_url or not image_url.strip():
        return {"success": False, "error": "图片URL无效", "text": ""}

    url = image_url.strip()

    cache_ttl_hours = config.get_int("VISION_RESULT_CACHE_TTL_HOURS", 24)
    download_timeout = config.get_int("VISION_DOWNLOAD_TIMEOUT_SEC", 60)
    model_base_url = config.get_str("VISION_MODEL_BASE_URL", "http://localhost:11434/v1")
    model_api_key = config.get_str("VISION_MODEL_API_KEY", "ollama")
    model_name = config.get_str("VISION_MODEL_NAME", "qwen3.5:9b")

    _cleanup_old_files(config.get_int("VISION_CACHE_TTL_HOURS", 24))

    cache_key = f"{url}#text_ocr"
    cached_result = _get_cached_result(cache_key, cache_ttl_hours)
    if cached_result is not None:
        return {"success": True, "text": cached_result, "error": ""}

    filename = _safe_filename(url, "jpg")

    try:
        filepath = await _download_file(url, filename, download_timeout)
        with open(filepath, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()

        raw = await _call_vision_model(
            image_data,
            UserPrompts.IMAGE_TEXT_OCR,
            model_base_url,
            model_api_key,
            model_name,
        )
        text = _parse_ocr_text(raw)
        _set_cached_result(cache_key, text)
        return {"success": True, "text": text, "error": ""}
    except Exception as e:
        logger.error(f"[图片文字提取] 失败: {str(e)}")
        return {"success": False, "error": str(e), "text": ""}