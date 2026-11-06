"""文档摘要工具模块

提供文档解析和摘要生成功能，使用 markitdown 将文档转换为 Markdown 格式后再进行 AI 总结。

支持的文档格式：
- PDF
- Word(docx)
- Excel(xlsx/xls)
- PPT(pptx)
- HTML
- TXT/MD
"""

import re
import os
import time
import httpx
import urllib.parse
import logging
from typing import Optional

from framework.core.config import config
from ..core import Agent
from ..prompt import SystemPrompts

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "data",
    "media",
)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".xlsx",
    ".xls",
    ".pptx",
    ".html",
    ".htm",
    ".txt",
    ".md",
}

_last_cleanup_time = 0


def _markitdown_convert(filepath: str) -> Optional[str]:
    """使用 markitdown 将文件转换为 Markdown 文本"""
    try:
        from markitdown import MarkItDown

        md = MarkItDown()
        result = md.convert(filepath)
        return result.text_content
    except ImportError:
        logger.error("需要安装 markitdown: pip install markitdown")
        return None
    except Exception as e:
        logger.error(f"markitdown 转换失败: {e}")
        return None


def _cleanup_old_files(cleanup_hours: int = 24):
    """清理超过 TTL 的临时下载文件"""
    global _last_cleanup_time

    now = time.time()
    cleanup_interval = 3600
    if now - _last_cleanup_time < cleanup_interval:
        return

    ttl_seconds = cleanup_hours * 3600

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
            logger.info(
                f"[文档摘要] 已清理 {count} 个过期临时文件 (TTL={cleanup_hours}h)"
            )
        _last_cleanup_time = now
    except Exception as e:
        logger.warning(f"[文档摘要] 清理临时文件失败: {e}")
        _last_cleanup_time = now


def _safe_filename(url: str, ext: str = "") -> str:
    """从URL中提取文件名并清理特殊字符，支持中文"""
    original_name = ""

    if url:
        parsed = urllib.parse.urlparse(url)
        path = parsed.path

        if path:
            decoded_path = urllib.parse.unquote(path)
            name = os.path.basename(decoded_path)

            if name and "." in name:
                original_name = name
            elif name:
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

    return (
        f"file_{int(time.time() * 1000)}.{ext}"
        if ext
        else f"file_{int(time.time() * 1000)}"
    )


async def _download_file(url: str, filename: str) -> str:
    """下载文件到本地（支持 HTTP/HTTPS 和本地文件）"""
    _cleanup_old_files()

    filepath = os.path.join(DOWNLOAD_DIR, filename)
    if os.path.exists(filepath):
        return filepath

    try:
        if url.lower().startswith("file://"):
            local_path = url[7:]
            if os.name == "nt" and local_path.startswith("/"):
                local_path = local_path[1:]
            local_path = urllib.parse.unquote(local_path)

            if os.path.exists(local_path):
                import shutil

                shutil.copy2(local_path, filepath)
                return filepath
            else:
                raise Exception(f"本地文件不存在: {local_path}")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            with open(filepath, "wb") as f:
                f.write(response.content)
        return filepath
    except Exception as e:
        raise Exception(f"文件下载失败: {str(e)}")


async def _extract_text(document_url: str) -> Optional[str]:
    """提取文档文本内容"""
    if not document_url or not document_url.strip():
        logger.warning("[文档摘要] 文档URL无效")
        return None

    url = document_url.strip()
    url_lower = url.lower()

    ext = os.path.splitext(url_lower)[-1]
    if ext not in SUPPORTED_EXTENSIONS:
        logger.warning(f"[文档摘要] 不支持的文件格式: {url}")
        return None

    filename = _safe_filename(url, ext.lstrip("."))

    try:
        filepath = await _download_file(url, filename)
        content = _markitdown_convert(filepath)

        if content is None:
            logger.error(f"[文档摘要] markitdown 文本提取失败: {filepath}")
            return None

        logger.info(f"[文档摘要] 文本提取成功: {len(content)} 字符")
        return content
    except Exception as e:
        logger.error(f"[文档摘要] 文本提取失败: {str(e)}")
        return None


async def _convert_to_markdown(document_url: str) -> Optional[str]:
    """将文档转换为Markdown格式"""
    if not document_url or not document_url.strip():
        logger.warning("[文档摘要] 文档URL无效")
        return None

    url = document_url.strip()
    url_lower = url.lower()

    ext = os.path.splitext(url_lower)[-1]
    if ext not in SUPPORTED_EXTENSIONS:
        logger.warning(f"[文档摘要] 不支持的文件格式: {url}")
        return f"不支持的格式：{ext}"

    try:
        filename = _safe_filename(url, ext.lstrip("."))
        filepath = await _download_file(url, filename)

        print(f"[文档摘要] 文档已下载: {os.path.basename(filepath)}")
        print(f"[文档摘要] 开始转换为Markdown...")

        md_content = _markitdown_convert(filepath)

        if md_content is None:
            logger.error(f"[文档摘要] Markdown转换失败: {filepath}")
            return None

        print(f"[文档摘要] Markdown转换完成: {len(md_content)} 字符")
        return md_content

    except Exception as e:
        logger.error(f"[文档摘要] Markdown转换失败: {str(e)}")
        return None


async def _replace_images_with_description(markdown_content: str) -> str:
    """使用图片理解工具替换图片链接为描述"""
    try:
        from .image_understanding import understand_image

        pattern = r"!\[([^\]]*)\]\(([^)]+)\)"

        matches = list(re.finditer(pattern, markdown_content))
        if not matches:
            return markdown_content

        result = markdown_content
        offset = 0

        for match in matches:
            alt_text = match.group(1)
            image_url = match.group(2)
            start = match.start() + offset
            end = match.end() + offset

            print(f"[文档摘要] 分析图片: {image_url[:50]}...")

            try:
                image_result = await understand_image(image_url)
                if image_result.get("success"):
                    description = image_result.get("result")
                    if description:
                        replacement = f"\n**图片描述**: {description}\n"
                    else:
                        replacement = (
                            f"\n**图片**: [{alt_text or '图片'}]({image_url})\n"
                        )
                else:
                    replacement = f"\n**图片**: [{alt_text or '图片'}]({image_url})\n"
            except Exception as e:
                logger.error(f"[文档摘要] 图片分析失败: {e}")
                replacement = f"\n**图片**: [{alt_text or '图片'}]({image_url})\n"

            result = result[:start] + replacement + result[end:]
            offset += len(replacement) - (end - start)

        print(f"[文档摘要] 图片理解替换完成")
        return result

    except ImportError:
        logger.warning("[文档摘要] 图片理解工具未安装")
        return markdown_content
    except Exception as e:
        logger.error(f"[文档摘要] 图片理解替换失败: {e}")
        return markdown_content


async def _call_ai_summary(
    content: str, summary_type: str, custom_prompt: str = None
) -> str:
    """基于 Agent 调用AI进行文档总结"""
    try:
        temperature = config.get_float("ASSISTANT_DOC_SUMMARY_TEMPERATURE", 0.3)
        max_tokens = config.get_int("ASSISTANT_DOC_SUMMARY_MAX_TOKENS", 2000)
        max_content_length = config.get_int(
            "ASSISTANT_DOC_SUMMARY_MAX_CONTENT_LENGTH", 8000
        )

        if custom_prompt:
            prompt = custom_prompt
        else:
            prompt = SystemPrompts.DOC_SUMMARY_TYPES.get(
                summary_type, SystemPrompts.DOC_SUMMARY_TYPES["brief"]
            )

        user_message = prompt.format(content=content[:max_content_length])

        print(f"[文档摘要] 调用AI模型")

        agent = Agent()
        result = await agent.chat(
            system_prompt=SystemPrompts.DOCUMENT_SUMMARY,
            context=[],
            user_prompt=user_message,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        summary = result.content

        print(f"[文档摘要] AI总结完成")
        print(f"[文档摘要] 总结结果:\n{summary}")
        print("-" * 60)
        return summary.content

    except Exception as e:
        logger.error(f"[文档摘要] AI调用失败: {str(e)}")
        return f"AI调用失败: {str(e)}"


async def summarize_document(document_url: str, summary_type: str = "brief") -> dict:
    """文档总结工具"""
    enabled = config.get_bool("ASSISTANT_DOC_SUMMARY_ENABLED", True)
    if not enabled:
        return {
            "success": False,
            "error": "文档摘要服务已禁用",
            "fallback": "文档摘要服务已禁用",
        }

    if not document_url or not document_url.strip():
        return {
            "success": False,
            "error": "文档URL无效",
            "fallback": "请提供有效的文档URL",
        }

    try:
        print(f"[文档摘要] 开始处理文档: {document_url[:50]}...")

        md_content = await _convert_to_markdown(document_url)

        if md_content is None:
            return {
                "success": False,
                "error": "文档转换失败",
                "fallback": "文档转换失败",
            }

        if md_content.startswith("不支持"):
            return {"success": False, "error": md_content, "fallback": md_content}

        print(f"[文档摘要] Markdown内容长度: {len(md_content)} 字符")

        if len(md_content.strip()) == 0:
            return {
                "success": False,
                "error": "文档内容为空",
                "fallback": "文档内容为空或无法读取",
            }

        md_content = await _replace_images_with_description(md_content)

        summary = await _call_ai_summary(md_content, summary_type)

        if (
            summary
            and not summary.startswith("不支持")
            and not summary.startswith("文档总结失败")
            and not summary.startswith("AI调用失败")
        ):
            return {"success": True, "result": summary}
        else:
            return {
                "success": False,
                "error": summary if summary else "总结失败",
                "fallback": f"无法总结文档 {document_url}。请检查文档URL是否有效。",
            }

    except Exception as e:
        logger.error(f"[文档摘要] 总结失败: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "fallback": f"无法总结文档 {document_url}。请检查文档URL是否有效。",
        }


async def analyze_webpage(webpage_url: str, task: str = "提取并总结主要内容") -> dict:
    """网页分析工具"""
    enabled = config.get_bool("ASSISTANT_DOC_SUMMARY_ENABLED", True)
    if not enabled:
        return {
            "success": False,
            "error": "文档摘要服务已禁用",
            "fallback": "文档摘要服务已禁用",
        }

    if not webpage_url or not webpage_url.strip():
        return {
            "success": False,
            "error": "网页URL无效",
            "fallback": "请提供有效的网页URL",
        }

    url = webpage_url.strip()

    try:
        print(f"[文档摘要] 开始分析网页: {url[:50]}...")

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()

            content = response.text
            html_path = os.path.join(
                DOWNLOAD_DIR, f"page_{int(time.time() * 1000)}.html"
            )
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(content)

            md_content = _markitdown_convert(html_path)
            os.remove(html_path)

            if md_content is None:
                return {
                    "success": False,
                    "error": "markitdown 转换失败",
                    "fallback": f"无法分析网页 {url}。markitdown 转换失败。",
                }

            print(f"[文档摘要] 网页内容提取完成: {len(md_content)} 字符")

            md_content = await _replace_images_with_description(md_content)

            summary = await _call_ai_summary(md_content, "brief")

            if (
                summary
                and not summary.startswith("网页分析失败")
                and not summary.startswith("不支持")
                and not summary.startswith("AI调用失败")
            ):
                return {"success": True, "result": summary}
            else:
                domain = url.split("//")[-1].split("/")[0] if "://" in url else url
                return {
                    "success": False,
                    "error": summary if summary else "网页分析失败",
                    "fallback": f"无法直接访问网页 {url}。如果你想了解关于 '{domain}' 的具体信息，可以描述你感兴趣的内容，我会尽力为你解答。",
                }

    except Exception as e:
        domain = url.split("//")[-1].split("/")[0] if "://" in url else url
        logger.error(f"[文档摘要] 网页总结失败: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "fallback": f"无法访问网页 {url}。如果你想了解关于 '{domain}' 的具体信息，可以描述你感兴趣的内容，我会尽力为你解答。",
        }
