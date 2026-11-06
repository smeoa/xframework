"""数据库日志模块

把 logging 记录按 `.env` 里的 `LOG_LEVEL` 过滤后写入 `x_log` 表。

为什么要这套桥接：
- logging 是**同步** API，而本项目用 asyncpg 异步连接池，不能在 emit 里 await；
  所以走「emit 同步入队 → 后台协程异步批量落库」。
- 日志组件自身**绝不允许把异常抛回业务**：队列满就丢最旧的，落库失败重试几次仍不行就
  自动停用并提示一次，避免"日志写不进去导致接口 500"或"错误日志刷屏"。

用法（admin/main.py 的 lifespan 里）：
    setup_logging(config.get("LOG_LEVEL", "INFO"))   # 先配控制台
    log_db.install()                                  # 再把 DB handler 挂到 root
    await log_db.start()                              # 起后台落库协程
    ...
    await log_db.stop()                               # 关闭前把队列里剩的落完
"""

import asyncio
import logging
import queue
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .config import config
from .db import db

LOG_TABLE = "x_log"

# 落库批量的列顺序（与 log.sql 一致）
COLUMNS = (
    "level", "logger", "module", "func", "line", "message", "exc_info",
    "request_id", "request_path", "request_method", "client_ip", "user_id", "create_time",
)

QUEUE_MAX = 5000          # 队列上限，满了丢最旧的
BATCH_SIZE = 100          # 单次最多落多少条
POLL_INTERVAL = 1.0       # 队列空闲时的轮询间隔（秒）
MAX_MESSAGE_LEN = 20000   # 单条消息上限，超长截断
MAX_FLUSH_FAILURES = 3    # 连续落库失败几次后停用 DB 日志

# ---------------------------------------------------------------- 请求上下文
# 由 log_context_middleware 写入，落库时一并记录，方便按 request_id 串联排查
ctx_request_id: ContextVar[Optional[str]] = ContextVar("log_request_id", default=None)
ctx_request_path: ContextVar[Optional[str]] = ContextVar("log_request_path", default=None)
ctx_request_method: ContextVar[Optional[str]] = ContextVar("log_request_method", default=None)
ctx_client_ip: ContextVar[Optional[str]] = ContextVar("log_client_ip", default=None)
ctx_user_id: ContextVar[Optional[int]] = ContextVar("log_user_id", default=None)

_queue: "queue.Queue[Dict[str, Any]]" = queue.Queue(maxsize=QUEUE_MAX)
_writer_task: Optional[asyncio.Task] = None
_handler: Optional["DbLogHandler"] = None
_flush_failures = 0
_disabled = False
_in_writer = False        # 防止"落库失败 → 打日志 → 又入队"的自我循环


def _level_of(name: str, default: int = logging.INFO) -> int:
    """把配置里的级别字符串转成 logging 级别数字"""
    level = logging.getLevelName(str(name).upper())
    return level if isinstance(level, int) else default


def current_context() -> Dict[str, Any]:
    """当前请求上下文（供日志 handler 使用）"""
    return {
        "request_id": ctx_request_id.get(),
        "request_path": ctx_request_path.get(),
        "request_method": ctx_request_method.get(),
        "client_ip": ctx_client_ip.get(),
        "user_id": ctx_user_id.get(),
    }


async def log_context_middleware(request, call_next):
    """把请求上下文塞进 contextvar，日志落库时自动带上

    Args:
        request: FastAPI 请求
        call_next: 下游处理

    Returns:
        下游响应
    """
    tokens = [
        (ctx_request_id, ctx_request_id.set(uuid.uuid4().hex[:16])),
        (ctx_request_path, ctx_request_path.set(str(request.url.path)[:255])),
        (ctx_request_method, ctx_request_method.set(str(request.method)[:16])),
        (ctx_client_ip, ctx_client_ip.set(_client_ip_of(request))),
        (ctx_user_id, ctx_user_id.set(_user_id_of(request))),
    ]
    try:
        return await call_next(request)
    finally:
        for var, token in reversed(tokens):
            try:
                var.reset(token)
            except Exception:
                pass


def _client_ip_of(request) -> Optional[str]:
    """尽量取真实客户端 IP（有反代时看 X-Forwarded-For）"""
    try:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()[:64]
        return (request.client.host if request.client else None)
    except Exception:
        return None


def _user_id_of(request) -> Optional[int]:
    """从 Authorization 里解出 user_id（解不出就留空，不抛错）

    这里只做"尽力而为"的解析：不校验签名有效性（校验在 auth 里），
    目的只是让日志能标出是谁触发的。
    """
    try:
        header = request.headers.get("authorization") or ""
        if not header.lower().startswith("bearer "):
            return None
        import jwt

        payload = jwt.decode(header[7:], config.get("JWT_SECRET"), algorithms=["HS256"], options={"verify_exp": False})
        return int(payload.get("user_id")) if payload.get("user_id") is not None else None
    except Exception:
        return None


# ---------------------------------------------------------------- handler

class _ExcludeFilter(logging.Filter):
    """按 logger 名排除噪音（默认排除 uvicorn.access，每个请求一条太占库）"""

    def __init__(self, excludes: List[str]) -> None:
        super().__init__()
        self.excludes = excludes

    def filter(self, record: logging.LogRecord) -> bool:
        name = record.name or ""
        return not any(name == e or name.startswith(e + ".") for e in self.excludes)


class DbLogHandler(logging.Handler):
    """把日志记录塞进队列；真正的落库由后台协程做"""

    def __init__(self, level: int = logging.INFO) -> None:
        super().__init__(level)
        self.setFormatter(logging.Formatter("%(message)s"))

    def emit(self, record: logging.LogRecord) -> None:
        """入队；任何异常都吞掉，绝不打扰业务"""
        if _disabled or _in_writer:
            return
        try:
            message = record.getMessage()
            if len(message) > MAX_MESSAGE_LEN:
                message = message[:MAX_MESSAGE_LEN] + "...(截断)"

            exc_text = None
            if record.exc_info:
                try:
                    # ⚠️ formatException 是 Formatter 的方法，Handler 上没有（踩过：写错会静默吞成"只有异常消息"）
                    exc_text = logging.Formatter().formatException(record.exc_info)
                except Exception:
                    exc_text = str(record.exc_info[1])[:MAX_MESSAGE_LEN]

            item = {
                "level": record.levelname,
                "logger": (record.name or "")[:128],
                "module": (record.module or "")[:128],
                "func": (record.funcName or "")[:128],
                "line": int(record.lineno or 0),
                "message": message,
                "exc_info": exc_text,
                "create_time": datetime.now(timezone.utc),
            }
            item.update({k: (v[:255] if isinstance(v, str) else v) for k, v in
                         {kk: vv for kk, vv in current_context().items()
                          if kk in ("request_id", "request_path", "request_method", "client_ip")}.items()})
            item["user_id"] = current_context().get("user_id")

            try:
                _queue.put_nowait(item)
            except queue.Full:
                # 丢最旧的一条再塞，保证新日志（通常更有价值）进得去
                try:
                    _queue.get_nowait()
                except queue.Empty:
                    pass
                try:
                    _queue.put_nowait(item)
                except queue.Full:
                    pass
        except Exception:
            pass


# ---------------------------------------------------------------- 落库

def _build_insert(rows: List[Dict[str, Any]]) -> (str, List[Any]):
    """拼多行 INSERT（一次往返落一批）"""
    params: List[Any] = []
    chunks: List[str] = []
    for row in rows:
        placeholders = []
        for col in COLUMNS:
            params.append(row.get(col))
            placeholders.append("$%d" % len(params))
        chunks.append("(" + ", ".join(placeholders) + ")")
    sql = 'INSERT INTO "%s" (%s) VALUES %s' % (LOG_TABLE, ", ".join(COLUMNS), ", ".join(chunks))
    return sql, params


async def _flush(rows: List[Dict[str, Any]]) -> None:
    """把一批日志写库；失败计数超阈值就停用（不刷屏、不干扰业务）"""
    global _flush_failures, _disabled, _in_writer

    if not rows:
        return
    sql, params = _build_insert(rows)
    _in_writer = True
    try:
        await db.execute(sql, params)
        _flush_failures = 0
    except Exception as e:
        _flush_failures += 1
        if _flush_failures >= MAX_FLUSH_FAILURES:
            _disabled = True
            logging.getLogger("framework.log_db").error(
                "[log_db] 连续 %d 次写入 %s 失败，已停用数据库日志（原因: %s）——"
                "检查表是否存在、连接是否正常", _flush_failures, LOG_TABLE, str(e)[:200],
            )
    finally:
        _in_writer = False


async def insert_now(rows: List[Dict[str, Any]]) -> int:
    """同步落库（供「外部程序写入日志」接口使用）

    与后台批量落库共用同一套列与拼 SQL 逻辑，区别是：这里不吞异常 ——
    接口调用方需要知道到底写没写成功。

    Args:
        rows: 待写入的记录（只需包含 COLUMNS 里的字段，缺的按 None）

    Returns:
        写入条数
    """
    if not rows:
        return 0
    normalized = [{col: row.get(col) for col in COLUMNS} for row in rows]
    sql, params = _build_insert(normalized)
    await db.execute(sql, params)
    return len(normalized)


async def _writer_loop() -> None:
    """后台协程：从队列取，攒一批就写"""
    buf: List[Dict[str, Any]] = []
    while True:
        try:
            try:
                item = await asyncio.to_thread(_queue.get, True, POLL_INTERVAL)
                buf.append(item)
            except queue.Empty:
                pass

            while len(buf) < BATCH_SIZE:
                try:
                    buf.append(_queue.get_nowait())
                except queue.Empty:
                    break

            if buf:
                await _flush(buf)
                buf = []
        except asyncio.CancelledError:
            break
        except Exception:
            # 兜底：绝不因日志协程自身异常而中断
            buf = []
            await asyncio.sleep(POLL_INTERVAL)

    if buf:
        try:
            await _flush(buf)
        except Exception:
            pass


async def _drain_once() -> int:
    """把队列里剩余的都写掉（关闭时用），返回写了多少条"""
    rows: List[Dict[str, Any]] = []
    while True:
        try:
            rows.append(_queue.get_nowait())
        except queue.Empty:
            break
    if rows:
        await _flush(rows)
    return len(rows)


# ---------------------------------------------------------------- 对外接口

def install(level: Optional[str] = None) -> Optional[DbLogHandler]:
    """把 DB 日志 handler 挂到 root logger

    级别取参数 > 配置 LOG_LEVEL；`LOG_DB_ENABLED=false` 时完全不挂。

    Args:
        level: 显式级别（默认取配置 LOG_LEVEL）

    Returns:
        挂上的 handler（未启用返回 None）
    """
    global _handler

    if not config.get_bool("LOG_DB_ENABLED", True):
        print("[日志] LOG_DB_ENABLED=false，数据库日志未启用")
        return None
    if _handler is not None:
        return _handler

    configured = level or config.get("LOG_LEVEL", "INFO")
    handler = DbLogHandler(_level_of(configured))

    excludes = [s.strip() for s in str(config.get("LOG_DB_EXCLUDE", "uvicorn.access")).split(",") if s.strip()]
    if excludes:
        handler.addFilter(_ExcludeFilter(excludes))

    logging.getLogger().addHandler(handler)
    _handler = handler
    print("[OK] 数据库日志已挂载: 表=%s 级别=%s 排除=%s"
          % (LOG_TABLE, logging.getLevelName(handler.level), excludes or "无"))
    return handler


async def start() -> None:
    """启动后台落库协程"""
    global _writer_task
    if _handler is None:
        return
    if _writer_task is None or _writer_task.done():
        _writer_task = asyncio.create_task(_writer_loop())


async def stop() -> None:
    """停止落库协程，并尽力把队列里剩下的写掉"""
    global _writer_task
    if _writer_task is not None:
        _writer_task.cancel()
        try:
            await _writer_task
        except (asyncio.CancelledError, Exception):
            pass
        _writer_task = None
    try:
        left = await _drain_once()
        if left:
            print("[OK] 数据库日志收尾写入 %d 条" % left)
    except Exception as e:
        print("[WARNING] 数据库日志收尾失败: %s" % str(e)[:200])


def stats() -> Dict[str, Any]:
    """运行态（供健康检查/排查）"""
    return {
        "enabled": _handler is not None and not _disabled,
        "table": LOG_TABLE,
        "level": logging.getLevelName(_handler.level) if _handler else None,
        "queue_size": _queue.qsize(),
        "flush_failures": _flush_failures,
        "disabled": _disabled,
    }
