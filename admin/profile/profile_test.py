"""个人设置（API 密钥）接口测试

覆盖内容：
- 鉴权：API 密钥 4 个接口未携带 token 一律 401
- 数据隔离：密钥归属强制为当前登录用户；所有用户（含管理员）仅能看到 / 操作本人密钥；
  越权操作返回 403，记录不存在返回 404
- 列表：字段完整（id / name / key / status / description / create_time / expire_time）
- 创建：名称必填、名称超长 400、过期时间必填且格式合法并须晚于当前时间、
  成功后返回完整密钥且落库归属为当前用户
- 切换状态：状态值仅支持 0 / 1，ID 必填，成功后库中状态同步变更
- 删除：成功后记录消失，重复删除返回 404
- 请求体兼容：data 包裹与直接传参两种形式均可正常解析

数据准备说明：
- 管理员：admin / admin123（user_id = 1）
- 普通用户：deptuser / 123456（user_id = 5）

测试数据统一使用 pytest_apikey_ 前缀，teardown 中直连库物理删除清理。
"""

import asyncio
import os
import uuid
from datetime import datetime, timedelta

import asyncpg
import httpx

# 后端服务基址（可通过 TEST_API_URL 覆盖）
BASE_URL = os.environ.get("TEST_API_URL", "http://localhost:8000")

# 测试数据统一前缀，便于识别与清理
PREFIX = "pytest_apikey_"

# 数据库直连配置（仅用于结果核对与数据清理）
PG_CONFIG = {
    "host": os.environ.get("PG_HOST", "127.0.0.1"),
    "port": int(os.environ.get("PG_PORT", "5432")),
    "database": os.environ.get("PG_DBNAME", "sy_erp"),
    "user": os.environ.get("PG_USER", "postgres"),
    "password": os.environ.get("PG_PASSWORD", "admin"),
}

# 测试账号（与 admin/shop/shop_test.py 保持一致）
ADMIN_USER = ("admin", "admin123")
NORMAL_USER = ("deptuser", "123456")

TABLE = "x_user_api_key"

# 列表返回的期望字段
EXPECTED_FIELDS = {"id", "name", "key", "status", "description", "create_time", "expire_time"}


class TestProfileApiKeyAPI:
    """API 密钥接口测试类"""

    def setup_method(self):
        """测试方法前置处理"""
        self.base_url = BASE_URL
        self.timeout = 30.0

    def teardown_method(self):
        """测试方法后置处理：物理删除本次测试产生的密钥"""
        deleted = asyncio.run(self._cleanup_test_data())
        print(f"[teardown] 清理 x_user_api_key {deleted} 行")

    # ==================== 内部工具 ====================

    async def _login(self, username: str, password: str) -> dict:
        """登录并返回扁平化的用户信息（含 token）"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/admin/auth/login",
                json={"username": username, "password": password},
            )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["code"] == 200, body
        data = body["data"]
        return {**data.get("user", {}), "token": data["token"]}

    def _headers(self, token: str = None) -> dict:
        """构造带 token 的请求头"""
        return {"Authorization": f"Bearer {token}"} if token else {}

    async def _post(self, path: str, payload: dict, token: str = None) -> httpx.Response:
        """POST JSON 请求"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.post(
                f"{self.base_url}{path}", json=payload, headers=self._headers(token)
            )

    async def _ok(self, path: str, payload: dict, token: str) -> dict:
        """POST 并断言业务成功，返回 data"""
        response = await self._post(path, payload, token)
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["code"] == 200, body
        return body["data"]

    def _new_name(self, suffix: str = "") -> str:
        """生成测试专用密钥名称"""
        return f"{PREFIX}{suffix}_{uuid.uuid4().hex[:8]}"

    def _future_time(self, days: int = 30) -> str:
        """生成未来时间字符串"""
        return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")

    async def _create_key(self, token: str, suffix: str = "", wrapped: bool = True, **extra) -> dict:
        """创建一条测试密钥并返回完整记录"""
        payload = {
            "name": self._new_name(suffix),
            "description": "pytest 描述",
            "expire_time": self._future_time(),
            **extra,
        }
        body = {"data": payload} if wrapped else payload
        return await self._ok("/admin/profile/create-api-key", body, token)

    async def _fetchrow(self, sql: str, *args):
        """直连数据库查询单行"""
        conn = await asyncpg.connect(**PG_CONFIG)
        try:
            return await conn.fetchrow(sql, *args)
        finally:
            await conn.close()

    async def _cleanup_test_data(self) -> int:
        """物理删除本次测试产生的密钥，返回删除行数"""
        conn = await asyncpg.connect(**PG_CONFIG)
        try:
            result = await conn.execute(f"DELETE FROM {TABLE} WHERE name LIKE $1", f"{PREFIX}%")
        finally:
            await conn.close()
        return int(str(result).split()[-1])

    # ==================== 鉴权 ====================

    def test_01_requires_auth(self):
        """未携带 token 时 API 密钥 4 个接口均返回 401"""
        async def run():
            return await asyncio.gather(
                self._post("/admin/profile/get-api-keys", {}),
                self._post("/admin/profile/create-api-key", {"name": self._new_name()}),
                self._post("/admin/profile/toggle-api-key-status", {"id": 1, "status": 0}),
                self._post("/admin/profile/delete-api-key", {"id": 1}),
            )

        for response in asyncio.run(run()):
            assert response.status_code == 401, response.text

    # ==================== 创建 ====================

    def test_02_create_api_key_success(self):
        """创建成功：返回完整密钥，落库归属为当前登录用户"""
        async def run():
            admin = await self._login(*ADMIN_USER)
            data = await self._create_key(admin["token"], "create")
            row = await self._fetchrow(f"SELECT * FROM {TABLE} WHERE id = $1", data["id"])
            return data, row, admin

        data, row, admin = asyncio.run(run())

        assert data["id"], data
        assert data["name"].startswith(PREFIX)
        assert isinstance(data["key"], str) and len(data["key"]) >= 32, data
        assert data["status"] == 1, data
        assert data["description"] == "pytest 描述", data
        assert data["create_time"], data
        assert data["expire_time"], data

        assert row is not None, "创建后应落库"
        assert row["user_id"] == admin["id"], row
        assert row["key"] == data["key"], row
        assert row["status"] == 1, row

    def test_03_create_api_key_validation(self):
        """创建校验：名称必填 / 超长、过期时间必填 / 格式非法 / 早于当前时间均 400"""
        async def run():
            admin = await self._login(*ADMIN_USER)
            token = admin["token"]
            cases = {
                "缺名称": {"data": {"expire_time": self._future_time()}},
                "空名称": {"data": {"name": "   ", "expire_time": self._future_time()}},
                "名称超长": {"data": {"name": "a" * 256, "expire_time": self._future_time()}},
                "缺过期时间": {"data": {"name": self._new_name("noexp")}},
                "过期时间格式非法": {"data": {"name": self._new_name("badfmt"), "expire_time": "不是时间"}},
                "过期时间早于当前": {
                    "data": {
                        "name": self._new_name("past"),
                        "expire_time": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
                    }
                },
            }
            responses = {}
            for label, payload in cases.items():
                responses[label] = await self._post("/admin/profile/create-api-key", payload, token)
            return responses

        for label, response in asyncio.run(run()).items():
            assert response.status_code == 400, f"{label}: {response.text}"
            assert response.json()["code"] == 400, f"{label}: {response.text}"

    def test_04_create_api_key_accepts_direct_payload(self):
        """请求体兼容：不经 data 包裹直接传参同样可创建"""
        async def run():
            admin = await self._login(*ADMIN_USER)
            return await self._create_key(admin["token"], "direct", wrapped=False)

        data = asyncio.run(run())
        assert data["id"], data
        assert data["name"].startswith(PREFIX), data

    # ==================== 列表 ====================

    def test_05_get_api_keys_fields_and_isolation(self):
        """列表字段完整；严格本人隔离，任何用户（含管理员）均看不到他人密钥"""
        async def run():
            admin = await self._login(*ADMIN_USER)
            normal = await self._login(*NORMAL_USER)

            admin_key = await self._create_key(admin["token"], "admin")
            normal_key = await self._create_key(normal["token"], "normal")

            admin_list = await self._ok("/admin/profile/get-api-keys", {}, admin["token"])
            normal_list = await self._ok("/admin/profile/get-api-keys", {}, normal["token"])
            return admin_key, normal_key, admin_list, normal_list

        admin_key, normal_key, admin_list, normal_list = asyncio.run(run())

        assert isinstance(admin_list, list) and isinstance(normal_list, list)

        # 字段完整性
        for item in admin_list:
            assert EXPECTED_FIELDS.issubset(item.keys()), item

        admin_ids = {item["id"] for item in admin_list}
        normal_ids = {item["id"] for item in normal_list}

        assert admin_key["id"] in admin_ids
        assert normal_key["id"] in normal_ids
        # 严格本人隔离：双方都看不到对方的密钥
        assert normal_key["id"] not in admin_ids, "管理员不应看到他人密钥"
        assert admin_key["id"] not in normal_ids, "普通用户不应看到他人密钥"
        assert all(item["id"] != normal_key["id"] for item in admin_list), admin_list
        assert all(item["id"] != admin_key["id"] for item in normal_list), normal_list

    def test_06_get_api_keys_skips_other_owner_rows_in_db(self):
        """库中确实存在归属他人的记录时，本人列表不含该记录"""
        async def run():
            admin = await self._login(*ADMIN_USER)
            normal = await self._login(*NORMAL_USER)

            key = await self._create_key(admin["token"], "ownercheck")
            row = await self._fetchrow(f"SELECT user_id FROM {TABLE} WHERE id = $1", key["id"])
            normal_list = await self._ok("/admin/profile/get-api-keys", {}, normal["token"])
            return key, row, admin, normal_list

        key, row, admin, normal_list = asyncio.run(run())
        assert row is not None, "记录应落库"
        assert row["user_id"] == admin["id"], row
        assert key["id"] not in {item["id"] for item in normal_list}, normal_list

    # ==================== 切换状态 ====================

    def test_07_toggle_api_key_status_success(self):
        """切换状态：0 / 1 均生效并同步落库"""
        async def run():
            admin = await self._login(*ADMIN_USER)
            key = await self._create_key(admin["token"], "toggle")

            off = await self._post(
                "/admin/profile/toggle-api-key-status", {"id": key["id"], "status": 0}, admin["token"]
            )
            row_off = await self._fetchrow(f"SELECT status FROM {TABLE} WHERE id = $1", key["id"])

            on = await self._post(
                "/admin/profile/toggle-api-key-status",
                {"data": {"id": key["id"], "status": 1}},
                admin["token"],
            )
            row_on = await self._fetchrow(f"SELECT status FROM {TABLE} WHERE id = $1", key["id"])
            return off, row_off, on, row_on

        off, row_off, on, row_on = asyncio.run(run())
        assert off.status_code == 200, off.text
        assert off.json()["code"] == 200, off.text
        assert row_off["status"] == 0, row_off

        assert on.status_code == 200, on.text
        assert on.json()["code"] == 200, on.text
        assert row_on["status"] == 1, row_on

    def test_08_toggle_api_key_status_validation(self):
        """状态校验：ID 缺失 400、ID 非法 400、状态值非法 400、记录不存在 404"""
        async def run():
            admin = await self._login(*ADMIN_USER)
            token = admin["token"]
            key = await self._create_key(token, "toggleval")

            missing_id = await self._post("/admin/profile/toggle-api-key-status", {"status": 0}, token)
            bad_id = await self._post(
                "/admin/profile/toggle-api-key-status", {"id": "abc", "status": 0}, token
            )
            bad_status = await self._post(
                "/admin/profile/toggle-api-key-status", {"id": key["id"], "status": 5}, token
            )
            empty_status = await self._post(
                "/admin/profile/toggle-api-key-status", {"id": key["id"]}, token
            )
            not_found = await self._post(
                "/admin/profile/toggle-api-key-status", {"id": 999999999, "status": 0}, token
            )
            row = await self._fetchrow(f"SELECT status FROM {TABLE} WHERE id = $1", key["id"])
            return missing_id, bad_id, bad_status, empty_status, not_found, row

        missing_id, bad_id, bad_status, empty_status, not_found, row = asyncio.run(run())
        for label, response in {
            "缺少ID": missing_id,
            "ID非法": bad_id,
            "状态值非法": bad_status,
            "缺少状态值": empty_status,
        }.items():
            assert response.status_code == 400, f"{label}: {response.text}"
            assert response.json()["code"] == 400, f"{label}: {response.text}"
        assert not_found.status_code == 404, not_found.text
        # 校验失败的请求不应改动数据
        assert row["status"] == 1, row

    def test_09_toggle_api_key_status_forbidden(self):
        """越权：切换他人密钥返回 403（双向验证），且库中状态不变"""
        async def run():
            admin = await self._login(*ADMIN_USER)
            normal = await self._login(*NORMAL_USER)

            admin_key = await self._create_key(admin["token"], "forbid")
            normal_key = await self._create_key(normal["token"], "forbid")

            normal_on_admin = await self._post(
                "/admin/profile/toggle-api-key-status",
                {"id": admin_key["id"], "status": 0},
                normal["token"],
            )
            admin_on_normal = await self._post(
                "/admin/profile/toggle-api-key-status",
                {"id": normal_key["id"], "status": 0},
                admin["token"],
            )
            admin_row = await self._fetchrow(f"SELECT status FROM {TABLE} WHERE id = $1", admin_key["id"])
            normal_row = await self._fetchrow(
                f"SELECT status FROM {TABLE} WHERE id = $1", normal_key["id"]
            )
            return normal_on_admin, admin_on_normal, admin_row, normal_row

        normal_on_admin, admin_on_normal, admin_row, normal_row = asyncio.run(run())
        for label, response in {"普通用户改管理员密钥": normal_on_admin, "管理员改普通用户密钥": admin_on_normal}.items():
            assert response.status_code == 403, f"{label}: {response.text}"
            assert response.json()["code"] == 403, f"{label}: {response.text}"
        assert admin_row["status"] == 1, "越权操作不应改动数据"
        assert normal_row["status"] == 1, "越权操作不应改动数据"

    # ==================== 删除 ====================

    def test_10_delete_api_key_success(self):
        """删除成功：记录消失，重复删除返回 404"""
        async def run():
            admin = await self._login(*ADMIN_USER)
            key = await self._create_key(admin["token"], "delete")

            first = await self._post("/admin/profile/delete-api-key", {"id": key["id"]}, admin["token"])
            row = await self._fetchrow(f"SELECT id FROM {TABLE} WHERE id = $1", key["id"])
            second = await self._post(
                "/admin/profile/delete-api-key", {"data": {"id": key["id"]}}, admin["token"]
            )
            return first, row, second

        first, row, second = asyncio.run(run())
        assert first.status_code == 200, first.text
        assert first.json()["code"] == 200, first.text
        assert row is None, "删除后记录应不存在"
        assert second.status_code == 404, second.text

    def test_11_delete_api_key_validation(self):
        """删除校验：ID 缺失 400、记录不存在 404"""
        async def run():
            admin = await self._login(*ADMIN_USER)
            token = admin["token"]
            missing_id = await self._post("/admin/profile/delete-api-key", {}, token)
            not_found = await self._post("/admin/profile/delete-api-key", {"id": 999999999}, token)
            return missing_id, not_found

        missing_id, not_found = asyncio.run(run())
        assert missing_id.status_code == 400, missing_id.text
        assert not_found.status_code == 404, not_found.text

    def test_12_delete_api_key_forbidden(self):
        """越权：删除他人密钥返回 403（双向验证），且记录保留"""
        async def run():
            admin = await self._login(*ADMIN_USER)
            normal = await self._login(*NORMAL_USER)

            admin_key = await self._create_key(admin["token"], "delforbid")
            normal_key = await self._create_key(normal["token"], "delforbid")

            normal_del_admin = await self._post(
                "/admin/profile/delete-api-key", {"id": admin_key["id"]}, normal["token"]
            )
            admin_del_normal = await self._post(
                "/admin/profile/delete-api-key", {"id": normal_key["id"]}, admin["token"]
            )
            admin_row = await self._fetchrow(f"SELECT id FROM {TABLE} WHERE id = $1", admin_key["id"])
            normal_row = await self._fetchrow(f"SELECT id FROM {TABLE} WHERE id = $1", normal_key["id"])
            return normal_del_admin, admin_del_normal, admin_row, normal_row

        normal_del_admin, admin_del_normal, admin_row, normal_row = asyncio.run(run())
        for label, response in {"普通用户删管理员密钥": normal_del_admin, "管理员删普通用户密钥": admin_del_normal}.items():
            assert response.status_code == 403, f"{label}: {response.text}"
            assert response.json()["code"] == 403, f"{label}: {response.text}"
        assert admin_row is not None, "越权删除不应生效"
        assert normal_row is not None, "越权删除不应生效"

    # ==================== 全链路闭环 ====================

    def test_13_normal_user_full_flow(self):
        """普通用户闭环：创建 → 归属本人 → 列表可见 → 切换 → 删除 → 列表不可见"""
        async def run():
            normal = await self._login(*NORMAL_USER)
            token = normal["token"]

            created = await self._create_key(token, "flow")
            owner_row = await self._fetchrow(f"SELECT user_id FROM {TABLE} WHERE id = $1", created["id"])

            listed = await self._ok("/admin/profile/get-api-keys", {}, token)
            visible = any(item["id"] == created["id"] for item in listed)

            toggled = await self._post(
                "/admin/profile/toggle-api-key-status", {"id": created["id"], "status": 0}, token
            )
            deleted = await self._post("/admin/profile/delete-api-key", {"id": created["id"]}, token)
            listed_after = await self._ok("/admin/profile/get-api-keys", {}, token)
            still_visible = any(item["id"] == created["id"] for item in listed_after)
            row = await self._fetchrow(f"SELECT user_id FROM {TABLE} WHERE id = $1", created["id"])
            return created, normal, owner_row, visible, toggled, deleted, still_visible, row

        created, normal, owner_row, visible, toggled, deleted, still_visible, row = asyncio.run(run())
        assert owner_row is not None and owner_row["user_id"] == normal["id"], "创建归属应为当前登录用户"
        assert visible, "创建后应在本人列表中可见"
        assert toggled.status_code == 200, toggled.text
        assert deleted.status_code == 200, deleted.text
        assert not still_visible, "删除后不应在列表中可见"
        assert row is None, "删除后记录应不存在"
