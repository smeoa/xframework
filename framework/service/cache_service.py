"""缓存服务

提供统一的缓存接口，支持内存缓存和 Redis 缓存两种实现。
"""

import time
import json
import threading
from typing import Any, Optional

from framework.core.logger import get_logger
from framework.core.config import get_str, get_int

logger = get_logger("cache")


class CacheService:
    """统一缓存服务接口"""

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，如果不存在或已过期则返回 None
        """
        raise NotImplementedError

    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），默认 3600 秒（1小时）
        """
        raise NotImplementedError

    def delete(self, key: str) -> None:
        """删除缓存值

        Args:
            key: 缓存键
        """
        raise NotImplementedError

    def exists(self, key: str) -> bool:
        """检查缓存键是否存在

        Args:
            key: 缓存键

        Returns:
            是否存在
        """
        raise NotImplementedError

    def flush(self) -> None:
        """清空所有缓存"""
        raise NotImplementedError


class MemoryCacheService(CacheService):
    """内存缓存服务实现"""

    def __init__(self):
        self._cache: dict[str, dict] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                return None
            entry = self._cache[key]
            if time.time() > entry["expire_at"]:
                del self._cache[key]
                return None
            return entry["value"]

    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        with self._lock:
            self._cache[key] = {
                "value": value,
                "expire_at": time.time() + ttl,
                "created_at": time.time(),
            }

    def delete(self, key: str) -> None:
        with self._lock:
            if key in self._cache:
                del self._cache[key]

    def exists(self, key: str) -> bool:
        return self.get(key) is not None

    def flush(self) -> None:
        with self._lock:
            self._cache.clear()


class RedisCacheService(CacheService):
    """Redis 缓存服务实现"""

    def __init__(self):
        self._client = None
        self._connect()

    def _connect(self):
        try:
            import redis

            host = get_str("redis.host", "localhost")
            port = get_int("redis.port", 6379)
            db = get_int("redis.db", 0)
            password = get_str("redis.password", "")

            self._client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password if password else None,
                decode_responses=True,
            )
            # 测试连接
            self._client.ping()
            logger.info("Redis 缓存连接成功")
        except Exception as e:
            logger.error(f"Redis 连接失败，将使用内存缓存: {e}")
            self._client = None

    def get(self, key: str) -> Optional[Any]:
        if not self._client:
            return None
        try:
            value = self._client.get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception as e:
            logger.error(f"Redis get 失败: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        if not self._client:
            return
        try:
            self._client.set(key, json.dumps(value), ex=ttl)
        except Exception as e:
            logger.error(f"Redis set 失败: {e}")

    def delete(self, key: str) -> None:
        if not self._client:
            return
        try:
            self._client.delete(key)
        except Exception as e:
            logger.error(f"Redis delete 失败: {e}")

    def exists(self, key: str) -> bool:
        if not self._client:
            return False
        try:
            return self._client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis exists 失败: {e}")
            return False

    def flush(self) -> None:
        if not self._client:
            return
        try:
            self._client.flushdb()
        except Exception as e:
            logger.error(f"Redis flush 失败: {e}")


def create_cache_service() -> CacheService:
    """创建缓存服务实例"""
    cache_type = get_str("cache.type", "memory")
    if cache_type == "redis":
        return RedisCacheService()
    return MemoryCacheService()


# 创建全局缓存服务实例
cache_service = create_cache_service()
DEFAULT_TTL = get_int("cache.ttl", 3600)