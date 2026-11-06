"""数据库操作模块

本模块提供异步数据库操作功能，包括连接池管理、SQL执行、数据CRUD操作等。
支持自动重试、健康检查、LRU缓存等高级特性。
"""

import asyncpg
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from functools import wraps, lru_cache
from .config import config

logger = logging.getLogger(__name__)


def with_retry(max_retries: int = 3, delay: float = 1.0):
    """数据库操作重试装饰器

    Args:
        max_retries: 最大重试次数
        delay: 初始延迟时间（秒），支持指数退避
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except (
                    asyncpg.PostgresConnectionError,
                    ConnectionRefusedError,
                    ConnectionResetError,
                    OSError,
                ) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        sleep_time = delay * (2**attempt)
                        logger.warning(f"数据库操作失败，{sleep_time}秒后重试 ({attempt+1}/{max_retries}): {e}")
                        await time.sleep(sleep_time)
                        continue
                    break
                except Exception as e:
                    logger.error(f"数据库操作非连接错误: {e}")
                    raise

            logger.error(f"数据库操作重试失败，已达最大次数 {max_retries}: {last_exception}")
            raise last_exception

        return wrapper

    return decorator


class Db:
    """数据库操作类（单例模式）"""

    _instance: Optional["Db"] = None
    _initialized: bool = False
    _pool: Optional[asyncpg.Pool] = None
    _table_fields_cache: Dict[str, Tuple[float, List[str]]] = {}
    _table_column_types_cache: Dict[str, Tuple[float, Dict[str, str]]] = {}
    _cache_ttl: int = 300

    CREATE_TIME_FIELDS = ["created_at", "create_time", "gmt_create", "createTime", "c_time"]
    UPDATE_TIME_FIELDS = ["updated_at", "update_time", "gmt_modified", "updateTime", "u_time"]
    DELETE_TIME_FIELDS = ["deleted_at", "delete_time", "gmt_delete", "deleteTime", "d_time", "is_deleted"]
    CREATE_BY_FIELDS = ["create_by", "create_user_id", "createUserId", "c_by", "creator"]
    UPDATE_BY_FIELDS = ["update_by", "update_user_id", "updateUserId", "u_by", "updater"]
    DELETE_BY_FIELDS = ["delete_by", "delete_user_id", "deleteUserId", "d_by", "deleter"]

    def __new__(cls) -> "Db":
        if cls._instance is None:
            cls._instance = super(Db, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """初始化数据库配置（仅执行一次）"""
        if Db._initialized:
            return

        self.host: str = config.get_str("PG_HOST")
        self.port: int = config.get_int("PG_PORT")
        self.database: str = config.get_str("PG_DBNAME")
        self.user: str = config.get_str("PG_USER")
        self.password: str = config.get_str("PG_PASSWORD")
        self.prefix: str = config.get_str("PG_PREFIX", "")
        self.pool_min_size: int = config.get_int("PG_POOL_MIN_SIZE", 5)
        self.pool_max_size: int = config.get_int("PG_POOL_MAX_SIZE", 20)
        self.pool_max_inactive_connection_lifetime: int = config.get_int("PG_POOL_MAX_INACTIVE_CONNECTION_LIFETIME", 3600)

        Db._initialized = True

    @with_retry(max_retries=3)
    async def init_pool(self) -> None:
        """初始化连接池"""
        if Db._pool is None:
            try:
                logger.info(f"正在初始化数据库连接池: {self.host}:{self.port}/{self.database}")
                Db._pool = await asyncpg.create_pool(
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    user=self.user,
                    password=self.password,
                    min_size=self.pool_min_size,
                    max_size=self.pool_max_size,
                    max_inactive_connection_lifetime=self.pool_max_inactive_connection_lifetime,
                    command_timeout=60,
                    ssl=False,
                )
                self._last_health_check_time = time.time()
                # 初始化后立即验证连接池可用
                try:
                    async with Db._pool.acquire(timeout=5) as conn:
                        await conn.fetchval("SELECT 1")
                    logger.info("数据库连接池健康检查通过")
                except Exception as e:
                    logger.warning(f"数据库连接池初始化后健康检查失败: {e}")
                logger.info("数据库连接池初始化成功")
            except Exception as e:
                logger.error(f"数据库连接池初始化失败: {str(e)}")
                raise Exception(f"数据库连接池初始化失败: {str(e)}")

    async def close_pool(self) -> None:
        """关闭连接池"""
        if Db._pool:
            await Db._pool.close()
            Db._pool = None
            Db._table_fields_cache.clear()
            logger.info("数据库连接池已关闭")

    async def _ensure_pool(self) -> None:
        """确保连接池已初始化并健康"""
        if Db._pool is None:
            await self.init_pool()
            return

        # 限制健康检查频率，避免 Windows 上并发获取连接导致冲突
        now = time.time()
        last_check = getattr(self, "_last_health_check_time", 0)
        if now - last_check > 30:
            self._last_health_check_time = now
            await self._health_check()

    async def _health_check(self) -> None:
        """连接池健康检查，失败则重建连接池"""
        if Db._pool is None:
            return

        try:
            async with Db._pool.acquire(timeout=5) as conn:
                await conn.fetchval("SELECT 1")
        except Exception as e:
            logger.warning(f"连接池健康检查失败，尝试重建: {e}")
            await self.close_pool()
            await self.init_pool()

    def _add_timestamp_fields(
        self,
        data: Dict[str, Any],
        is_insert: bool = True,
        is_deleted: bool = False,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """自动填充时间戳字段和用户字段"""
        if not data:
            return data

        result = data.copy()
        now = datetime.now(timezone.utc)

        for field in self.CREATE_TIME_FIELDS:
            if field not in result:
                result[field] = now
                break

        for field in self.UPDATE_TIME_FIELDS:
            if field not in result:
                result[field] = now
                break

        if is_deleted:
            for field in self.DELETE_TIME_FIELDS:
                if field not in result:
                    result[field] = now
                    break

        if user_id is not None:
            for field in self.CREATE_BY_FIELDS:
                if field not in result:
                    result[field] = user_id
                    break

            for field in self.UPDATE_BY_FIELDS:
                if field not in result:
                    result[field] = user_id
                    break

            if is_deleted:
                for field in self.DELETE_BY_FIELDS:
                    if field not in result:
                        result[field] = user_id
                        break

        return result

    def _clean_expired_cache(self) -> None:
        """清理过期的字段缓存"""
        current_time = time.time()
        expired_keys = [
            key
            for key, (timestamp, _) in Db._table_fields_cache.items()
            if current_time - timestamp > self._cache_ttl
        ]
        for key in expired_keys:
            del Db._table_fields_cache[key]

        expired_type_keys = [
            key
            for key, (timestamp, _) in Db._table_column_types_cache.items()
            if current_time - timestamp > self._cache_ttl
        ]
        for key in expired_type_keys:
            del Db._table_column_types_cache[key]

    @with_retry(max_retries=2)
    async def execute(self, sql: str, params: Optional[List[Any]] = None) -> None:
        """执行SQL语句"""
        await self._ensure_pool()
        params = self._ensure_params_tz(params)
        async with Db._pool.acquire() as conn:
            try:
                if params:
                    await conn.execute(sql, *params)
                else:
                    await conn.execute(sql)
                self._clean_expired_cache()
            except Exception as e:
                logger.error(f"SQL执行失败: {str(e)}")
                raise Exception(f"SQL执行失败: {str(e)}")

    @staticmethod
    def _ensure_params_tz(params: Optional[List[Any]]) -> Optional[List[Any]]:
        """将所有 aware datetime 参数转为 naive UTC（DB 列均为 timestamp without time zone）"""
        if params is None:
            return None
        result = []
        for p in params:
            if isinstance(p, datetime) and p.tzinfo is not None:
                # 统一转 UTC 后再去掉时区，避免 asyncpg 报错
                utc_dt = p.astimezone(timezone.utc).replace(tzinfo=None)
                result.append(utc_dt)
            else:
                result.append(p)
        return result

    @with_retry(max_retries=2)
    async def fetch_one(self, sql: str, params: Optional[List[Any]] = None) -> Optional[Dict[str, Any]]:
        """查询单行数据"""
        await self._ensure_pool()
        params = self._ensure_params_tz(params)
        async with Db._pool.acquire() as conn:
            try:
                if params:
                    result = await conn.fetchrow(sql, *params)
                else:
                    result = await conn.fetchrow(sql)
                return dict(result) if result else None
            except Exception as e:
                logger.error(f"查询失败: {str(e)}")
                raise Exception(f"查询失败: {str(e)}")

    @with_retry(max_retries=2)
    async def fetch_all(self, sql: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
        """查询多行数据"""
        await self._ensure_pool()
        params = self._ensure_params_tz(params)
        async with Db._pool.acquire() as conn:
            try:
                if params:
                    results = await conn.fetch(sql, *params)
                else:
                    results = await conn.fetch(sql)
                return [dict(row) for row in results]
            except Exception as e:
                logger.error(f"查询失败: {str(e)}")
                raise Exception(f"查询失败: {str(e)}")

    @with_retry(max_retries=2)
    async def fetch_all_session(
        self,
        sql: str,
        params: Optional[List[Any]] = None,
        session_sql: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """在同一连接会话/事务内先执行 session_sql 再查询多行

        用于需注入会话级 GUC（如 pgvector 的 hnsw.ef_search）后在同一连接上执行的场景。
        session_sql 用 SET LOCAL 承载，随事务提交/回滚自动复位，避免 GUC 泄漏到连接池其他查询。
        """
        await self._ensure_pool()
        params = self._ensure_params_tz(params)
        async with Db._pool.acquire() as conn:
            try:
                async with conn.transaction():
                    if session_sql:
                        await conn.execute(session_sql)
                    results = await conn.fetch(sql, *params) if params else await conn.fetch(sql)
                    return [dict(row) for row in results]
            except Exception as e:
                logger.error(f"查询失败: {str(e)}")
                raise Exception(f"查询失败: {str(e)}")

    @with_retry(max_retries=2)
    async def insert(self, table: str, data: Dict[str, Any], user_id: Optional[int] = None) -> int:
        """插入数据并返回ID"""
        await self._ensure_pool()
        data = self._add_timestamp_fields(data, is_insert=True, user_id=user_id)
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["$" + str(i + 1) for i in range(len(data))])
        values = tuple(data.values())

        sql = f'INSERT INTO "{table}" ({columns}) VALUES ({placeholders}) RETURNING id'
        async with Db._pool.acquire() as conn:
            try:
                result = await conn.fetchval(sql, *values)
                self._clean_expired_cache()
                return result
            except Exception as e:
                logger.error(f"插入失败: {str(e)}")
                raise Exception(f"插入失败: {str(e)}")

    @with_retry(max_retries=2)
    async def batch_insert(
        self, table: str, data_list: List[Dict[str, Any]], user_id: Optional[int] = None
    ) -> List[int]:
        """批量插入数据并返回ID列表"""
        if not data_list:
            return []

        await self._ensure_pool()
        async with Db._pool.acquire() as conn:
            try:
                async with conn.transaction():
                    data_list = [
                        self._add_timestamp_fields(data, is_insert=True, user_id=user_id) for data in data_list
                    ]
                    columns = ", ".join(data_list[0].keys())
                    placeholders = ", ".join(["$" + str(i + 1) for i in range(len(data_list[0]))])
                    sql = f'INSERT INTO "{table}" ({columns}) VALUES ({placeholders}) RETURNING id'

                    ids = []
                    stmt = await conn.prepare(sql)
                    for data in data_list:
                        values = tuple(data.values())
                        result = await stmt.fetchval(*values)
                        ids.append(result)

                    self._clean_expired_cache()
                    return ids
            except Exception as e:
                logger.error(f"批量插入失败: {str(e)}")
                raise Exception(f"批量插入失败: {str(e)}")

    @with_retry(max_retries=2)
    async def update(
        self,
        table: str,
        data: Dict[str, Any],
        condition: str,
        params: Optional[List[Any]] = None,
        user_id: Optional[int] = None,
    ) -> int:
        """更新数据并返回影响行数"""
        await self._ensure_pool()
        data = self._add_timestamp_fields(data, is_insert=False, user_id=user_id)
        values = list(data.values())
        param_count = len(values)

        set_clause = ", ".join([f"{k} = ${i+1}" for i, k in enumerate(data.keys())])

        if params:
            import re
            from typing import Match

            def replace_placeholder(match: Match[str]) -> str:
                nonlocal param_count
                param_count += 1
                return f"${param_count}"

            condition = re.sub(r"\$\d+", replace_placeholder, condition)
            values.extend(params)

        sql = f'UPDATE "{table}" SET {set_clause} WHERE {condition}'
        async with Db._pool.acquire() as conn:
            try:
                status = await conn.execute(sql, *values)
                rowcount = status.split()[1]
                self._clean_expired_cache()
                return int(rowcount)
            except Exception as e:
                logger.error(f"更新失败: {str(e)}")
                raise Exception(f"更新失败: {str(e)}")

    @with_retry(max_retries=2)
    async def delete(
        self,
        table: str,
        condition: str,
        params: Optional[List[Any]] = None,
        is_soft: bool = True,
        user_id: Optional[int] = None,
    ) -> int:
        """删除数据并返回影响行数"""
        await self._ensure_pool()

        if is_soft:
            table_fields = await self.get_table_fields(table)
            has_delete_field = any(field in self.DELETE_TIME_FIELDS for field in table_fields)

            if has_delete_field:
                update_data = self._add_timestamp_fields({}, is_insert=False, is_deleted=True, user_id=user_id)
                set_clause = ", ".join([f"{k} = ${i+1}" for i, k in enumerate(update_data.keys())])

                if set_clause:
                    values = list(update_data.values())
                    if params:
                        import re

                        param_idx = len(update_data)

                        def replace_placeholder(match):
                            nonlocal param_idx
                            param_idx += 1
                            return f"${param_idx}"

                        new_condition = re.sub(r"\$\d+", replace_placeholder, condition)
                        values.extend(params)
                    else:
                        new_condition = condition

                    sql = f'UPDATE "{table}" SET {set_clause} WHERE {new_condition}'
                    async with Db._pool.acquire() as conn:
                        try:
                            status = await conn.execute(sql, *values)
                            rowcount = status.split()[1]
                            self._clean_expired_cache()
                            return int(rowcount)
                        except Exception as e:
                            logger.error(f"软删除失败: {str(e)}")
                            raise Exception(f"软删除失败: {str(e)}")

        sql = f'DELETE FROM "{table}" WHERE {condition}'
        async with Db._pool.acquire() as conn:
            try:
                if params:
                    status = await conn.execute(sql, *params)
                else:
                    status = await conn.execute(sql)
                rowcount = status.split()[1]
                self._clean_expired_cache()
                return int(rowcount)
            except Exception as e:
                logger.error(f"删除失败: {str(e)}")
                raise Exception(f"删除失败: {str(e)}")

    async def get_table_fields(self, table_name: str) -> List[str]:
        """获取表的所有字段（带TTL缓存）"""
        current_time = time.time()
        if table_name in Db._table_fields_cache:
            cache_time, fields = Db._table_fields_cache[table_name]
            if current_time - cache_time < self._cache_ttl:
                return fields

        await self._ensure_pool()
        async with Db._pool.acquire() as conn:
            try:
                sql = """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = $1
                ORDER BY ordinal_position
                """
                rows = await conn.fetch(sql, table_name)
                fields = [row.get("column_name") for row in rows if row.get("column_name") is not None]

                if not fields and table_name.startswith(self.prefix):
                    table_name_without_prefix = table_name[len(self.prefix) :]
                    rows = await conn.fetch(sql, table_name_without_prefix)
                    fields = [row.get("column_name") for row in rows if row.get("column_name") is not None]

                Db._table_fields_cache[table_name] = (current_time, fields)
                return fields
            except Exception as e:
                logger.error(f"获取表字段失败: {str(e)}")
                return ["id", "name"]

    async def get_table_column_types(self, table_name: str) -> Dict[str, str]:
        """获取表所有列的数据类型（带TTL缓存）

        Returns:
            列名 -> information_schema.data_type 的映射
        """
        current_time = time.time()
        if table_name in Db._table_column_types_cache:
            cache_time, column_types = Db._table_column_types_cache[table_name]
            if current_time - cache_time < self._cache_ttl:
                return column_types

        await self._ensure_pool()
        async with Db._pool.acquire() as conn:
            try:
                sql = """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = $1
                ORDER BY ordinal_position
                """
                rows = await conn.fetch(sql, table_name)
                column_types = {
                    row.get("column_name"): row.get("data_type")
                    for row in rows
                    if row.get("column_name") is not None
                }

                if not column_types and table_name.startswith(self.prefix):
                    table_name_without_prefix = table_name[len(self.prefix) :]
                    rows = await conn.fetch(sql, table_name_without_prefix)
                    column_types = {
                        row.get("column_name"): row.get("data_type")
                        for row in rows
                        if row.get("column_name") is not None
                    }

                Db._table_column_types_cache[table_name] = (current_time, column_types)
                return column_types
            except Exception as e:
                logger.error(f"获取表字段类型失败: {str(e)}")
                return {}

    async def execute_batch(self, queries: List[Tuple[str, List[Any]]]) -> None:
        """批量执行SQL语句"""
        if not queries:
            return

        await self._ensure_pool()
        async with Db._pool.acquire() as conn:
            try:
                async with conn.transaction():
                    for sql, params in queries:
                        if params:
                            await conn.execute(sql, *params)
                        else:
                            await conn.execute(sql)
                self._clean_expired_cache()
            except Exception as e:
                logger.error(f"批量执行失败: {str(e)}")
                raise Exception(f"批量执行失败: {str(e)}")

    async def fetch_batch(self, queries: List[Tuple[str, List[Any]]]) -> List[Any]:
        """批量执行查询并返回结果"""
        if not queries:
            return []

        await self._ensure_pool()
        results = []
        async with Db._pool.acquire() as conn:
            try:
                for sql, params in queries:
                    if params:
                        result = await conn.fetch(sql, *params)
                    else:
                        result = await conn.fetch(sql)
                    results.append([dict(row) for row in result])
                return results
            except Exception as e:
                logger.error(f"批量查询失败: {str(e)}")
                raise Exception(f"批量查询失败: {str(e)}")


async def init_db() -> Db:
    """初始化数据库"""
    db_instance = Db()
    await db_instance.init_pool()
    return db_instance


db: Db = Db()
