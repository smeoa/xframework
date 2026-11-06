"""HTTP请求服务模块

提供统一的HTTP请求封装，支持异步请求、超时处理、错误重试等功能。
"""

import httpx
import logging
from typing import Dict, Any, Optional, List
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class HttpService:
    """HTTP请求服务类"""

    def __init__(self):
        self._client = None

    @property
    def client(self):
        """获取HTTP客户端（懒加载）"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=30,
                headers={
                    "User-Agent": "WeChat-Agent-Service/1.0",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def get(self, url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """发送GET请求

        Args:
            url: 请求URL
            params: 查询参数
            headers: 额外的请求头

        Returns:
            响应数据
        """
        try:
            logger.debug(f"发送GET请求: {url}, params: {params}")
            request_headers = {**self.client.headers, **(headers or {})}
            response = await self.client.get(url, params=params, headers=request_headers)
            response.raise_for_status()
            result = response.json()
            logger.debug(f"GET请求成功: {url}, 响应: {result}")
            return result
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP请求失败 {url}: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"GET请求异常 {url}: {str(e)}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def post(self, url: str, data: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """发送POST请求

        Args:
            url: 请求URL
            data: 请求体数据
            headers: 额外的请求头

        Returns:
            响应数据
        """
        try:
            logger.debug(f"发送POST请求: {url}, data: {data}")
            request_headers = {**self.client.headers, **(headers or {})}
            response = await self.client.post(url, json=data, headers=request_headers)
            response.raise_for_status()
            result = response.json()
            logger.debug(f"POST请求成功: {url}, 响应: {result}")
            return result
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP请求失败 {url}: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"POST请求异常 {url}: {str(e)}")
            raise

    async def close(self):
        """关闭HTTP客户端"""
        if self._client:
            await self._client.aclose()


http_service = HttpService()