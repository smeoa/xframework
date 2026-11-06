"""数据库连接池（asyncpg）与查询辅助

site 库的新表无 x_ 前缀，全部使用真实表名。
"""
from contextlib import asynccontextmanager
from typing import Any, Iterable, Sequence

import asyncpg

from settings import settings

_pool: asyncpg.Pool | None = None


async def init_pool() -> None:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            host=settings.pg_host,
            port=settings.pg_port,
            database=settings.pg_database,
            user=settings.pg_user,
            password=settings.pg_password,
            min_size=settings.pg_pool_min,
            max_size=settings.pg_pool_max,
        )


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("数据库连接池未初始化")
    return _pool


async def fetch(sql: str, *args: Any) -> list[asyncpg.Record]:
    return await pool().fetch(sql, *args)


async def fetchrow(sql: str, *args: Any) -> asyncpg.Record | None:
    return await pool().fetchrow(sql, *args)


async def fetchval(sql: str, *args: Any) -> Any:
    return await pool().fetchval(sql, *args)


async def execute(sql: str, *args: Any) -> str:
    return await pool().execute(sql, *args)


@asynccontextmanager
async def transaction():
    async with pool().acquire() as conn:
        async with conn.transaction():
            yield conn


def to_dict(record: asyncpg.Record | None) -> dict[str, Any] | None:
    return dict(record) if record is not None else None


def to_dicts(records: Iterable[asyncpg.Record]) -> list[dict[str, Any]]:
    return [dict(item) for item in records]


def placeholders(values: Sequence[Any], start: int = 1) -> str:
    """生成 $1,$2,... 占位串"""
    return ", ".join(f"${index}" for index in range(start, start + len(values)))
