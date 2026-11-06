"""系统日志接口 + 落库组件测试

覆盖两部分：
1. **落库组件**（进程内直连库）：按配置级别过滤、异常堆栈落库、写入不阻塞业务；
2. **接口**（HTTP 打到本机后端）：鉴权 401、数据隔离、详情/删除/批量、清理（权限与天数下限）、统计。

数据准备说明：
- 管理员：admin / admin123；普通用户：deptuser / 123456
- 测试日志统一用 message 前缀 pytest_log_，teardown 中**物理删除**（日志表软删除没有意义，留着只会污染列表）
"""

import asyncio
import logging
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

import asyncpg
import httpx

# 让测试进程能 import 框架（与 admin/main.py 一致地把项目根加进 sys.path）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

BASE_URL = os.environ.get("TEST_API_URL", "http://localhost:8000")
MSG_PREFIX = "pytest_log_"

PG_CONFIG = {
    "host": os.environ.get("PG_HOST", "127.0.0.1"),
    "port": int(os.environ.get("PG_PORT", "5432")),
    "database": os.environ.get("PG_DBNAME", "sy_erp"),
    "user": os.environ.get("PG_USER", "postgres"),
    "password": os.environ.get("PG_PASSWORD", "admin"),
}

LOG_TABLE = "x_log"


class TestLogAPI:
    """系统日志测试类"""

    def setup_method(self):
        """测试方法前置处理"""
        self.base_url = BASE_URL
        self.timeout = 30.0

    def teardown_method(self):
        """测试方法后置处理：物理删除本次测试产生的日志行"""
        deleted = asyncio.run(self._cleanup())
        print(f"[teardown] 物理删除测试日志 {deleted} 行")

    # ==================== 内部工具 ====================

    async def _cleanup(self) -> int:
        conn = await asyncpg.connect(**PG_CONFIG)
        try:
            result = await conn.execute(f"DELETE FROM {LOG_TABLE} WHERE message LIKE $1", f"{MSG_PREFIX}%")
        finally:
            await conn.close()
        return int(str(result).split()[-1])

    async def _fetch_all(self, sql: str, *args):
        conn = await asyncpg.connect(**PG_CONFIG)
        try:
            return await conn.fetch(sql, *args)
        finally:
            await conn.close()

    async def _execute(self, sql: str, *args):
        conn = await asyncpg.connect(**PG_CONFIG)
        try:
            return await conn.execute(sql, *args)
        finally:
            await conn.close()

    async def _login(self, username: str, password: str) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base_url}/admin/auth/login",
                                     json={"username": username, "password": password})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["code"] == 200, body
        return body["data"]

    async def _post(self, path: str, payload: dict, token: str = None) -> httpx.Response:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.post(f"{self.base_url}{path}", json=payload, headers=headers)

    def _tag(self) -> str:
        return f"{MSG_PREFIX}{uuid.uuid4().hex[:8]}"

    # ==================== 建表 ====================

    def test_01_table_structure(self):
        """x_log 表存在且关键列齐全"""
        rows = asyncio.run(self._fetch_all(
            """SELECT column_name, data_type FROM information_schema.columns WHERE table_name = $1""",
            LOG_TABLE,
        ))
        columns = {r["column_name"]: r["data_type"] for r in rows}
        expected = {
            "id", "data_id", "level", "logger", "module", "func", "line", "message", "exc_info",
            "request_id", "request_path", "request_method", "client_ip", "user_id",
            "create_time", "is_deleted", "delete_time", "delete_by",
        }
        missing = expected - set(columns)
        assert not missing, f"缺列: {missing}"
        assert columns["message"] == "text"

    # ==================== 落库组件（级别过滤 / 异常 / 不阻塞） ====================

    def test_02_db_handler_level_filter_and_exception(self):
        """落库组件：级别过滤 + 异常堆栈 + 绝不抛回业务

        注意：框架的 db 是进程内单例、连接池绑定事件循环，所以组件级断言必须
        在**同一个 asyncio.run** 里做完，不能每个用例各起一个事件循环。
        """
        async def run():
            from framework.core import log_db, db

            await db.init_pool()
            handler = log_db.install("WARNING")
            assert handler is not None, "DB handler 未挂载"
            assert logging.getLevelName(handler.level) == "WARNING", handler.level
            await log_db.start()

            tag = self._tag()
            logger = logging.getLogger("pytest_log_db")

            logger.info("%s-INFO低于级别应被过滤" % tag)        # 低于阈值 → 不落库
            logger.warning("%s-WARNING应入库" % tag)          # 达到阈值 → 落库
            try:
                raise ValueError("%s-故意的异常" % tag)
            except ValueError:
                logger.error("%s-异常日志" % tag, exc_info=True)   # ERROR + 堆栈 → 落库

            # 直接调 emit 验证"参数化消息/不可序列化对象"也不会抛异常
            handler.emit(logging.LogRecord(
                "pytest_log_db.raw", logging.INFO, __file__, 1, "%s-裸emit带参数 %s %s" % (tag, "a", object()),
                None, None,
            ))

            await asyncio.sleep(2.5)                          # 等后台批量落库
            await log_db.stop()

            rows = await self._fetch_all(
                f"SELECT level, message, exc_info FROM {LOG_TABLE} WHERE message LIKE $1 ORDER BY id",
                f"{tag}%",
            )
            stats = log_db.stats()
            # 连接池绑定创建它的 event loop：必须在本轮 asyncio.run 内收尾，
            # 否则类级单例 Db._pool 会残留并污染后续用例（如 order_test）
            await db.close_pool()
            return rows, stats

        rows, stats = asyncio.run(run())
        messages = [r["message"] for r in rows]
        levels = {r["level"] for r in rows}

        assert any("WARNING" in m for m in messages), f"WARNING 未入库: {messages}"
        assert not any("低于级别" in m for m in messages), f"低于级别的 INFO 不应入库: {messages}"
        assert "WARNING" in levels and "ERROR" in levels, levels

        error_rows = [r for r in rows if r["level"] == "ERROR"]
        assert error_rows, "异常日志未入库"
        assert error_rows[0]["exc_info"] and "ValueError" in error_rows[0]["exc_info"], error_rows[0]
        assert "故意的异常" in error_rows[0]["exc_info"]

        assert stats["table"] == LOG_TABLE
        assert stats["disabled"] is False
        assert stats["queue_size"] == 0, "落库后队列应清空"

    # ==================== 接口 ====================

    def test_03_list_requires_auth(self):
        """未携带 token 返回 401"""
        resp = asyncio.run(self._post("/admin/log/get-log-list", {"page": 1, "limit": 5}))
        assert resp.status_code == 401, resp.text

    def test_04_list_and_detail_via_api(self):
        """管理员能按关键字查到日志，并取到详情"""
        async def run():
            tag = self._tag()
            await self._execute(
                f"""INSERT INTO {LOG_TABLE} (level, logger, module, func, line, message, request_path)
                    VALUES ('INFO', 'pytest_log_db', 'pytest', 'test_06', 10, $1, '/pytest/log')""",
                f"{tag}-接口列表用例",
            )
            admin = await self._login("admin", "admin123")
            listing = await self._post(
                "/admin/log/get-log-list",
                {"page": 1, "limit": 20, "keyword": tag, "searchFields": ["message"]},
                admin["token"],
            )
            body = listing.json()
            assert body["code"] == 200, body
            assert body["data"]["total"] >= 1, body
            log_id = body["data"]["items"][0]["id"]
            detail = await self._post("/admin/log/get-log", {"id": log_id}, admin["token"])
            return tag, log_id, body, detail.json()

        tag, log_id, listing, detail = asyncio.run(run())
        assert detail["code"] == 200, detail
        assert detail["data"]["message"] == f"{tag}-接口列表用例"
        assert detail["data"]["level"] == "INFO"

    def test_05_non_admin_forbidden_and_admin_visible(self):
        """非管理员无 log:list 权限 → 403；管理员可见系统日志"""
        async def run():
            tag = self._tag()
            await self._execute(
                f"""INSERT INTO {LOG_TABLE} (level, logger, message, user_id)
                    VALUES ('WARNING', 'pytest_log_db', $1, NULL)""",
                f"{tag}-系统日志",
            )
            dept = await self._login("deptuser", "123456")
            listing = await self._post(
                "/admin/log/get-log-list",
                {"page": 1, "limit": 20, "keyword": tag, "searchFields": ["message"]},
                dept["token"],
            )
            admin = await self._login("admin", "admin123")
            admin_listing = await self._post(
                "/admin/log/get-log-list",
                {"page": 1, "limit": 20, "keyword": tag, "searchFields": ["message"]},
                admin["token"],
            )
            return listing, listing.json(), admin_listing.json()

        listing, dept_body, admin_body = asyncio.run(run())
        assert listing.status_code == 403, listing.text
        assert "log:list" in listing.json().get("detail", ""), dept_body
        assert admin_body["code"] == 200 and admin_body["data"]["total"] >= 1, "管理员应能看到"

    def test_06_delete_and_batch_delete(self):
        """删除为软删除；批量删除按ID生效"""
        async def run():
            tag = self._tag()
            ids = []
            for i in range(2):
                await self._execute(
                    f"""INSERT INTO {LOG_TABLE} (level, logger, message, user_id)
                        VALUES ('INFO', 'pytest_log_db', $1, 1)""",
                    f"{tag}-待删除{i}",
                )
            rows = await self._fetch_all(
                f"SELECT id FROM {LOG_TABLE} WHERE message LIKE $1 ORDER BY id", f"{tag}%"
            )
            ids = [r["id"] for r in rows]
            admin = await self._login("admin", "admin123")
            single = await self._post("/admin/log/delete-log", {"id": ids[0]}, admin["token"])
            batch = await self._post("/admin/log/batch-log", {"ids": [ids[1]]}, admin["token"])
            after = await self._fetch_all(
                f"SELECT id, is_deleted FROM {LOG_TABLE} WHERE id = ANY($1::bigint[]) ORDER BY id", ids
            )
            detail = await self._post("/admin/log/get-log", {"id": ids[0]}, admin["token"])
            return single.json(), batch.json(), after, detail.json()

        single, batch, after, detail = asyncio.run(run())
        assert single["code"] == 200 and single["data"] is None, single
        assert batch["code"] == 200, batch
        assert all(int(r["is_deleted"]) == 1 for r in after), after
        assert detail["code"] == 404, "软删除后详情应 404"

    def test_07_clean_log_permission_and_min_days(self):
        """清理日志：非管理员 403、天数低于下限 400、正常清理生效"""
        async def run():
            tag = self._tag()
            old_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=40)  # 列是 naive UTC
            await self._execute(
                f"""INSERT INTO {LOG_TABLE} (level, logger, message, create_time)
                    VALUES ('INFO', 'pytest_log_db', $1, $2)""",
                f"{tag}-40天前的老日志", old_time,
            )
            admin = await self._login("admin", "admin123")
            dept = await self._login("deptuser", "123456")
            forbidden = await self._post("/admin/log/clean-log", {"beforeDays": 30}, dept["token"])
            too_few = await self._post("/admin/log/clean-log", {"beforeDays": 3}, admin["token"])
            ok = await self._post("/admin/log/clean-log", {"beforeDays": 30}, admin["token"])
            left = await self._fetch_all(
                f"SELECT id FROM {LOG_TABLE} WHERE message LIKE $1", f"{tag}%"
            )
            return forbidden, forbidden.json(), too_few.json(), ok.json(), left

        forbidden, forbidden_body, too_few, ok, left = asyncio.run(run())
        assert forbidden.status_code == 403, forbidden.text
        assert "log:clean" in forbidden.json().get("detail", ""), forbidden_body
        assert too_few["code"] == 400, too_few
        assert ok["code"] == 200, ok
        assert ok["data"]["deleted"] >= 1, ok
        assert len(left) == 0, "40 天前的测试日志应被物理清掉"

    def test_08_stats_endpoint(self):
        """统计接口返回各级别条数与落库组件状态"""
        async def run():
            admin = await self._login("admin", "admin123")
            return await self._post("/admin/log/get-log-stats", {}, admin["token"])

        resp = asyncio.run(run())
        body = resp.json()
        assert body["code"] == 200, body
        assert set(body["data"]["levels"]) == {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        assert "writer" in body["data"]
        assert body["data"]["writer"]["table"] == LOG_TABLE

    # ==================== 外部程序写入接口 ====================

    def test_09_write_log_requires_auth(self):
        """外部写入接口未携带 token 返回 401"""
        resp = asyncio.run(self._post("/admin/log/write-log",
                                      {"level": "INFO", "message": f"{MSG_PREFIX}未授权"}))
        assert resp.status_code == 401, resp.text

    def test_10_write_log_single_and_level_filter(self):
        """单条写入：级别达阈值入库、低于阈值丢弃、非法级别 400"""
        async def run():
            tag = self._tag()
            admin = await self._login("admin", "admin123")

            ok = await self._post("/admin/log/write-log", {
                "level": "INFO", "message": f"{tag}-采集脚本上报",
                "logger": "1688.collect", "requestId": "cycle-1",
            }, admin["token"])

            below = await self._post("/admin/log/write-log", {
                "level": "DEBUG", "message": f"{tag}-调试细节（应被丢弃）",
                "logger": "1688.collect",
            }, admin["token"])

            bad_level = await self._post("/admin/log/write-log", {
                "level": "TRACE", "message": f"{tag}-非法级别",
            }, admin["token"])

            no_msg = await self._post("/admin/log/write-log", {"level": "INFO"}, admin["token"])

            rows = await self._fetch_all(
                f"""SELECT level, logger, message, user_id, request_id FROM {LOG_TABLE}
                    WHERE message LIKE $1 ORDER BY id""", f"{tag}%"
            )
            return tag, ok.json(), below.json(), bad_level.json(), no_msg.json(), rows, admin

        tag, ok, below, bad_level, no_msg, rows, admin = asyncio.run(run())

        assert ok["code"] == 200, ok
        assert ok["data"]["written"] == 1 and ok["data"]["dropped"] == 0, ok
        assert below["code"] == 200, below
        assert below["data"]["written"] == 0 and below["data"]["dropped"] == 1, below
        assert "低于配置级别" in below["data"]["details"][0]["reason"], below
        assert bad_level["code"] == 400, bad_level
        assert "级别非法" in bad_level["message"], bad_level
        assert no_msg["code"] == 400, no_msg

        assert len(rows) == 1, f"只应落库 1 条（DEBUG 被丢弃）: {rows}"
        assert rows[0]["level"] == "INFO"
        assert rows[0]["logger"] == "1688.collect"
        assert rows[0]["request_id"] == "cycle-1"
        assert rows[0]["user_id"] == 1, "user_id 应强制取当前登录用户"

    def test_11_write_log_batch_and_permission_boundary(self):
        """批量写入正常 + 非管理员无 log:write/log:list 权限 → 403 + 超量拒绝"""
        async def run():
            tag = self._tag()
            admin = await self._login("admin", "admin123")
            dept = await self._login("deptuser", "123456")

            batch = await self._post("/admin/log/write-log", {
                "logs": [
                    {"level": "WARNING", "message": f"{tag}-批量WARNING", "logger": "1688.collect"},
                    {"level": "ERROR", "message": f"{tag}-批量ERROR", "logger": "1688.collect",
                     "excInfo": "Traceback (most recent call last):\nRuntimeError: boom"},
                ]
            }, admin["token"])

            dept_write = await self._post("/admin/log/write-log",
                                          {"level": "ERROR", "message": f"{tag}-普通用户上报", "logger": "1688.collect"},
                                          dept["token"])

            too_many = await self._post("/admin/log/write-log",
                                        {"logs": [{"level": "INFO", "message": f"{tag}-x{i}"} for i in range(201)]},
                                        admin["token"])

            admin_list = await self._post("/admin/log/get-log-list",
                                          {"page": 1, "limit": 20, "keyword": tag, "searchFields": ["message"]},
                                          admin["token"])
            dept_list = await self._post("/admin/log/get-log-list",
                                         {"page": 1, "limit": 20, "keyword": tag, "searchFields": ["message"]},
                                         dept["token"])
            rows = await self._fetch_all(
                f"SELECT level, message, user_id, exc_info FROM {LOG_TABLE} WHERE message LIKE $1 ORDER BY id",
                f"{tag}%",
            )
            return (batch.json(), dept_write, dept_write.json(), too_many.json(),
                    admin_list.json(), dept_list, dept_list.json(), rows)

        (batch, dept_write, dept_write_body, too_many, admin_list,
         dept_list, dept_list_body, rows) = asyncio.run(run())

        assert batch["code"] == 200 and batch["data"]["written"] == 2, batch
        assert dept_write.status_code == 403, dept_write.text
        assert "log:write" in dept_write.json().get("detail", ""), dept_write_body
        assert too_many["code"] == 400 and "最多" in too_many["message"], too_many

        assert len(rows) == 2, f"应落库 2 条（普通用户写入被拒）: {rows}"
        assert {r["level"] for r in rows} == {"WARNING", "ERROR"}, rows
        assert all(r["user_id"] == 1 for r in rows), "均归属管理员"
        exc_rows = [r for r in rows if r["message"].endswith("批量ERROR")]
        assert exc_rows and "RuntimeError: boom" in exc_rows[0]["exc_info"], exc_rows

        # 非管理员无 log:list 权限 → 403；管理员能看到 2 条
        assert admin_list["code"] == 200 and admin_list["data"]["total"] == 2, admin_list
        assert dept_list.status_code == 403, dept_list.text
        assert "log:list" in dept_list.json().get("detail", ""), dept_list_body
