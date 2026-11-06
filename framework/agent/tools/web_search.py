"""网页搜索工具模块

基于 Tavily Search API 提供网页搜索功能，用于获取实时网络信息。
"""

import logging
from typing import Dict, Any

from framework.core.config import config

logger = logging.getLogger(__name__)


async def web_search(query: str, max_results: int = 3, search_depth: str = "basic") -> Dict[str, Any]:
    """网页搜索工具
    
    Args:
        query: 搜索查询词
        max_results: 最大返回结果数量，默认3
        search_depth: 搜索深度，默认basic
        
    Returns:
        包含搜索结果的字典
    """
    api_key = config.get_str("TAVILY_API_KEY", "")
    
    if not api_key:
        return {
            "success": False,
            "error": "Tavily API Key 未配置",
            "fallback": "网页搜索功能需要配置 Tavily API Key。请在 .env 文件中设置 TAVILY_API_KEY 环境变量。",
        }

    if not query or not query.strip():
        return {
            "success": False,
            "error": "搜索查询词无效",
            "fallback": "请提供有效的搜索查询词",
        }

    # 参数校验
    valid_depths = {"basic", "advanced", "fast", "ultra-fast"}
    if search_depth not in valid_depths:
        search_depth = "basic"
    if not isinstance(max_results, int) or max_results < 1:
        max_results = 3

    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=api_key)
        
        logger.info(f"[网页搜索] 开始搜索: {query} | depth={search_depth} | max={max_results}")
        
        response = client.search(
            query=query.strip(),
            max_results=max_results,
            search_depth=search_depth,
        )

        if not response or not response.get("results"):
            return {
                "success": False,
                "error": "未找到搜索结果",
                "fallback": f"未找到关于 '{query}' 的搜索结果。",
            }

        results = response.get("results", [])
        summaries = []
        
        for i, result in enumerate(results, 1):
            title = result.get("title", "")
            url = result.get("url", "")
            content = result.get("content", "")
            
            if title or content:
                summary = f"{i}. **{title}**\n"
                if content:
                    summary += f"   {content[:200]}..."
                if url:
                    summary += f"\n   链接: {url}"
                summaries.append(summary)

        if summaries:
            logger.info(f"[网页搜索] 搜索完成，找到 {len(summaries)} 条结果")
            return {"success": True, "result": "\n\n".join(summaries)}
        else:
            return {
                "success": False,
                "error": "搜索结果为空",
                "fallback": f"未找到关于 '{query}' 的有效搜索结果。",
            }

    except ImportError:
        logger.error("需要安装 tavily-python: pip install tavily-python")
        return {
            "success": False,
            "error": "Tavily 模块未安装",
            "fallback": "网页搜索功能需要安装 tavily-python 包。请运行: pip install tavily-python",
        }
    except Exception as e:
        logger.error(f"网页搜索失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "fallback": f"搜索 '{query}' 时遇到问题，请稍后重试。",
        }
