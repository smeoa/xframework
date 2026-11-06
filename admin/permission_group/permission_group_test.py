"""权限组接口测试

覆盖权限组主表增删改查、操作权限点授权、字段权限、数据权限、主体绑定、
菜单选项，以及当前用户权限组的自助查询与按组互斥切换。

测试数据统一使用 code 前缀 pytest_pg_ / 名称前缀 pytest_pg_，teardown 中
物理删除清理，不污染 12 组种子权限组；涉及普通用户激活组的用例在 teardown
中还原 deptuser 的原始激活组。

数据准备说明：
- 管理员：admin / admin123（bcrypt，is_admin=True）
- 普通用户：deptuser / 123456（明文回退分支，dept_id=1，无角色）

前置：后端已启动（含本模块，改完代码要重启才注册新路由）。
"""

import asyncio
import os
import uuid
from typing import Any, Dict, List, Optional

import asyncpg
import httpx

# 后端服务基址（可通过 TEST_API_URL 覆盖）
BASE_URL = os.environ.get("TEST_API_URL", "http://localhost:8000")
# 测试数据统一前缀
CODE_PREFIX = "pytest_pg_"
TITLE_PREFIX = "pytest_pg_"
CODE_LIKE = CODE_PREFIX + "%"

PG_CONFIG = {
    "host": os.environ.get("PG_HOST", "127.0.0.1"),
    "port": int(os.environ.get("PG_PORT", "5432")),
    "database": os.environ.get("PG_DBNAME", "sy_erp"),
    "user": os.environ.get("PG_USER", "postgres"),
    "password": os.environ.get("PG_PASSWORD", "admin"),
}
PG_PREFIX = os.environ.get("PG_PREFIX", "x_")

GROUP_TABLE = f"{PG_PREFIX}permission_group"
GROUP_PERMISSION_TABLE = f"{PG_PREFIX}permission_group_permission"
GROUP_FIELD_TABLE = f"{PG_PREFIX}permission_group_field"
GROUP_DATA_TABLE = f"{PG_PREFIX}permission_group_data"
GROUP_SUBJECT_TABLE = f"{PG_PREFIX}permission_group_subject"
USER_GROUP_TABLE = f"{PG_PREFIX}user_permission_group"
PERMISSION_TABLE = f"{PG_PREFIX}permission"
DEPT_TABLE = f"{PG_PREFIX}dept"
ROLE_TABLE = f"{PG_PREFIX}role"

# 登录账号
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
NON_ADMIN_USERNAME = "deptuser"
NON_ADMIN_PASSWORD = "123456"
NON_ADMIN_USER_ID = 5
NON_ADMIN_DEPT_ID = 1

MANAGE_PERMISSION = "org:role:grant"
# 种子数据中的 6 组权限组（店铺 / 商品 / 待采集 各 2 组）
SEED_GROUP_COUNT = 6
# 不存在的记录ID（用于"数据不存在"分支）
MISSING_ID = 99999999

# 用于字段权限用例的模块与合法/非法字段
SHOP_MODULE = "shop"
SHOP_MENU_CODE = "nav:shop"
# 菜单可见性用例使用的第二个菜单（普通用户默认没有该菜单下的权限组）
LOG_MENU_CODE = "nav:log"
LOG_MENU_PATH = "/log"
SHOP_VALID_FIELDS = ("platform_code", "shop_name")
SHOP_INVALID_FIELD = "not_exist_field"
# 未登记业务表的模块（用于字段目录异常分支）
UNKNOWN_MODULE = "not_exist_module"


class TestPermissionGroupAPI:
    """权限组 API 测试类"""

    def setup_method(self):
        """测试方法前置处理：登录管理员、记录普通用户原始激活组"""
        self.base_url = BASE_URL
        self.timeout = 30.0
        self._created_group_ids: List[int] = []
        self._temp_permission_ids: List[int] = []
        self._admin_token: Optional[str] = None
        self._non_admin_token: Optional[str] = None
        self._orig_active_group_id = asyncio.run(self._capture_active_group())

    def teardown_method(self):
        """测试方法后置处理：物理清理临时数据 + 还原普通用户激活组"""
        asyncio.run(self._cleanup_test_data())

    # ==================== 测试基建 ====================

    async def _login(self, username: str, password: str) -> Dict[str, Any]:
        """登录并返回 data 段"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/admin/auth/login",
                json={"username": username, "password": password},
            )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["code"] == 200, body
        return body["data"]

    async def admin_token(self) -> str:
        """获取管理员 token（同一用例内复用）"""
        if not self._admin_token:
            data = await self._login(ADMIN_USERNAME, ADMIN_PASSWORD)
            self._admin_token = data["token"]
        return self._admin_token

    async def non_admin_token(self) -> str:
        """获取普通用户 token（同一用例内复用）"""
        if not self._non_admin_token:
            data = await self._login(NON_ADMIN_USERNAME, NON_ADMIN_PASSWORD)
            self._non_admin_token = data["token"]
        return self._non_admin_token

    @staticmethod
    def _headers(token: Optional[str] = None) -> Dict[str, str]:
        return {"Authorization": f"Bearer {token}"} if token else {}

    async def _post(
        self, path: str, data: Optional[Dict[str, Any]] = None, token: Optional[str] = None
    ) -> httpx.Response:
        """POST 调用（统一封装 {"data": ...} 请求体）"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.post(
                f"{self.base_url}{path}",
                json={"data": data if data is not None else {}},
                headers=self._headers(token),
            )

    @staticmethod
    def _new_code() -> str:
        return f"{CODE_PREFIX}{uuid.uuid4().hex[:10]}"

    @staticmethod
    def _new_title() -> str:
        return f"{TITLE_PREFIX}{uuid.uuid4().hex[:8]}"

    async def _create_group(self, token: str, menu_code: str = SHOP_MENU_CODE, **overrides) -> int:
        """通过接口创建一个临时权限组，返回其ID"""
        payload: Dict[str, Any] = {
            "code": overrides.pop("code", None) or self._new_code(),
            "title": overrides.pop("title", None) or self._new_title(),
            "menu_code": menu_code,
        }
        payload.update(overrides)
        response = await self._post("/admin/permission-group/create-group", payload, token)
        body = response.json()
        assert body["code"] == 200, body
        group_id = int(body["data"]["id"])
        self._created_group_ids.append(group_id)
        return group_id

    async def _permission_ids(self, module: str, perm_type: int = 2, limit: int = 3) -> List[int]:
        """直连数据库取指定模块的权限点ID"""
        conn = await asyncpg.connect(**PG_CONFIG)
        try:
            rows = await conn.fetch(
                f"SELECT id FROM {PERMISSION_TABLE} WHERE module = $1 AND type = $2 "
                f"AND is_deleted = 0 AND status = 1 ORDER BY id LIMIT {int(limit)}",
                module,
                perm_type,
            )
            return [int(r["id"]) for r in rows]
        finally:
            await conn.close()

    async def _group_menu_id(self, token: str, group_id: int) -> int:
        """取权限组归属菜单ID（菜单准入会自动补全该权限点，断言时需纳入）"""
        detail = (
            await self._post("/admin/permission-group/get-group-detail", {"id": group_id}, token)
        ).json()
        return int(detail["data"]["menu_id"])

    async def _create_menu_without_module(self) -> int:
        """直连数据库插入一个不含业务模块的临时菜单权限点，返回其ID

        用于覆盖「菜单未关联业务模块」分支（种子菜单均已关联模块，无法直接构造）。
        """
        conn = await asyncpg.connect(**PG_CONFIG)
        try:
            perm_id = await conn.fetchval(
                f"INSERT INTO {PERMISSION_TABLE} (pid, title, code, type, status, is_deleted) "
                "VALUES (1, $1, $2, 1, 1, 0) RETURNING id",
                f"{TITLE_PREFIX}无模块菜单",
                f"{CODE_PREFIX}menu_{uuid.uuid4().hex[:8]}",
            )
            self._temp_permission_ids.append(int(perm_id))
            return int(perm_id)
        finally:
            await conn.close()

    def _collect_menu_paths(self, nodes: List[Dict[str, Any]]) -> List[str]:
        """递归收集菜单树中的叶子路径"""
        paths: List[str] = []
        for node in nodes or []:
            children = node.get("children") or []
            if children:
                paths.extend(self._collect_menu_paths(children))
            elif node.get("path"):
                paths.append(str(node["path"]))
        return paths

    async def _capture_active_group(self) -> Optional[int]:
        """记录普通用户当前激活的权限组ID，用于用例结束后还原"""
        conn = await asyncpg.connect(**PG_CONFIG)
        try:
            return await conn.fetchval(
                f"SELECT group_id FROM {USER_GROUP_TABLE} "
                "WHERE user_id = $1 AND is_active = 1 AND is_deleted = 0 "
                "ORDER BY activate_time DESC NULLS LAST, id DESC LIMIT 1",
                NON_ADMIN_USER_ID,
            )
        finally:
            await conn.close()

    async def _cleanup_test_data(self) -> None:
        """物理删除临时权限组及其子表数据，并还原普通用户激活组"""
        conn = await asyncpg.connect(**PG_CONFIG)
        try:
            # 编码自动维护后新建组可能带「pg:模块:序号」自动编码，故按 code 前缀
            # 与用例内记录的实际ID取并集，避免遗漏清理
            group_ids = {
                int(r["id"])
                for r in await conn.fetch(
                    f"SELECT id FROM {GROUP_TABLE} WHERE code LIKE $1", CODE_LIKE
                )
            }
            group_ids.update(int(gid) for gid in self._created_group_ids)
            group_ids = sorted(group_ids)
            if group_ids:
                for table in (
                    GROUP_PERMISSION_TABLE,
                    GROUP_FIELD_TABLE,
                    GROUP_DATA_TABLE,
                    GROUP_SUBJECT_TABLE,
                    USER_GROUP_TABLE,
                ):
                    await conn.execute(
                        f"DELETE FROM {table} WHERE group_id = ANY($1::bigint[])", group_ids
                    )
                await conn.execute(
                    f"DELETE FROM {GROUP_TABLE} WHERE id = ANY($1::bigint[])", group_ids
                )

            # 还原普通用户激活组
            await conn.execute(
                f"UPDATE {USER_GROUP_TABLE} SET is_active = 0, update_time = CURRENT_TIMESTAMP "
                "WHERE user_id = $1 AND is_deleted = 0",
                NON_ADMIN_USER_ID,
            )
            if self._orig_active_group_id:
                await conn.execute(
                    f"UPDATE {USER_GROUP_TABLE} SET is_active = 1, activate_time = CURRENT_TIMESTAMP, "
                    "update_time = CURRENT_TIMESTAMP WHERE user_id = $1 AND group_id = $2 AND is_deleted = 0",
                    NON_ADMIN_USER_ID,
                    int(self._orig_active_group_id),
                )

            # 清理「菜单未关联业务模块」用例插入的临时权限点
            if self._temp_permission_ids:
                await conn.execute(
                    f"DELETE FROM {PERMISSION_TABLE} WHERE id = ANY($1::bigint[])",
                    [int(pid) for pid in self._temp_permission_ids],
                )
        finally:
            await conn.close()

    # ==================== 权限组主表：列表 ====================

    async def async_test_get_group_list(self):
        """测试权限组列表返回种子数据与分页结构 (POST)"""
        token = await self.admin_token()
        response = await self._post("/admin/permission-group/get-group-list", {"page": 1, "limit": 50}, token)
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 200
        data = body["data"]
        assert isinstance(data["items"], list)
        assert data["total"] >= SEED_GROUP_COUNT
        first = data["items"][0]
        for key in (
            "id", "code", "title", "menu_id", "module", "sort", "status",
            "menu_title", "menu_code", "permission_count", "field_count", "data_scope_count", "subject_count",
        ):
            assert key in first, f"列表项缺少字段: {key}"

    async def async_test_get_group_list_pagination(self):
        """测试权限组列表分页参数生效（边界：limit=5） (POST)"""
        token = await self.admin_token()
        response = await self._post("/admin/permission-group/get-group-list", {"page": 1, "limit": 5}, token)
        body = response.json()
        assert body["code"] == 200
        assert len(body["data"]["items"]) <= 5

    async def async_test_get_group_list_keyword(self):
        """测试权限组列表按关键字过滤（命中新建的临时组） (POST)"""
        token = await self.admin_token()
        title = self._new_title()
        await self._create_group(token, title=title)

        response = await self._post(
            "/admin/permission-group/get-group-list", {"page": 1, "limit": 50, "keyword": title}, token
        )
        body = response.json()
        assert body["code"] == 200
        items = body["data"]["items"]
        assert len(items) >= 1
        assert any(item["title"] == title for item in items)
        for item in items:
            assert title in (item["title"] or "") or title in (item["code"] or "")

    async def async_test_get_group_list_status(self):
        """测试权限组列表按状态过滤（边界：status=0 停用） (POST)"""
        token = await self.admin_token()
        title = self._new_title()
        await self._create_group(token, title=title, status=0)

        response = await self._post(
            "/admin/permission-group/get-group-list", {"page": 1, "limit": 50, "status": 0}, token
        )
        body = response.json()
        assert body["code"] == 200
        items = body["data"]["items"]
        assert all(int(item["status"]) == 0 for item in items)
        assert any(item["title"] == title for item in items)

    async def async_test_get_group_list_menu_filter(self):
        """测试权限组列表按所属菜单过滤 (POST)"""
        token = await self.admin_token()
        group_id = await self._create_group(token)
        detail = (await self._post("/admin/permission-group/get-group-detail", {"id": group_id}, token)).json()
        menu_id = detail["data"]["menu_id"]

        response = await self._post(
            "/admin/permission-group/get-group-list", {"page": 1, "limit": 50, "menu_id": menu_id}, token
        )
        body = response.json()
        assert body["code"] == 200
        items = body["data"]["items"]
        assert len(items) >= 1
        assert all(int(item["menu_id"]) == int(menu_id) for item in items)

    async def async_test_get_group_list_module_filter(self):
        """测试权限组列表按业务模块过滤 (POST)"""
        token = await self.admin_token()
        group_id = await self._create_group(token)
        detail = (await self._post("/admin/permission-group/get-group-detail", {"id": group_id}, token)).json()
        module = detail["data"]["module"]

        response = await self._post(
            "/admin/permission-group/get-group-list", {"page": 1, "limit": 50, "module": module}, token
        )
        body = response.json()
        assert body["code"] == 200
        items = body["data"]["items"]
        assert len(items) >= 1
        assert all(item["module"] == module for item in items)
        assert any(int(item["id"]) == group_id for item in items)

    async def async_test_get_group_list_data_scope_count(self):
        """测试权限组列表返回数据范围数量（保存后计数同步） (POST)"""
        token = await self.admin_token()
        group_id = await self._create_group(token)
        await self._post(
            "/admin/permission-group/set-group-data-scope",
            {"id": group_id, "module": SHOP_MODULE, "scope": "all"},
            token,
        )

        response = await self._post(
            "/admin/permission-group/get-group-list", {"page": 1, "limit": 50}, token
        )
        body = response.json()
        assert body["code"] == 200
        target = next(item for item in body["data"]["items"] if int(item["id"]) == group_id)
        assert int(target["data_scope_count"]) >= 1

    # ==================== 权限组主表：详情 ====================

    async def async_test_get_group_detail(self):
        """测试权限组详情返回子配置与菜单信息 (POST)"""
        token = await self.admin_token()
        group_id = await self._create_group(token)

        response = await self._post("/admin/permission-group/get-group-detail", {"id": group_id}, token)
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 200
        data = body["data"]
        assert int(data["id"]) == group_id
        assert data["module"] == SHOP_MODULE
        assert data["menu"]["code"] == SHOP_MENU_CODE
        assert data["permissions"]["permission_ids"] == []
        assert data["fields"] == []
        assert data["data_scopes"] == []
        assert data["subjects"] == []

    async def async_test_get_group_detail_missing_id(self):
        """测试权限组详情缺ID返回400 (POST)"""
        token = await self.admin_token()
        response = await self._post("/admin/permission-group/get-group-detail", {}, token)
        body = response.json()
        assert body["code"] == 400
        assert body["message"] == "权限组ID不能为空"

    async def async_test_get_group_detail_not_found(self):
        """测试权限组详情查询不存在的数据返回400 (POST)"""
        token = await self.admin_token()
        response = await self._post("/admin/permission-group/get-group-detail", {"id": MISSING_ID}, token)
        body = response.json()
        assert body["code"] == 400
        assert body["message"] == "权限组不存在"

    # ==================== 权限组主表：创建 ====================

    async def async_test_create_group_by_menu_code(self):
        """测试按菜单码创建权限组并自动推导业务模块 (POST)"""
        token = await self.admin_token()
        code = self._new_code()
        title = self._new_title()
        response = await self._post(
            "/admin/permission-group/create-group",
            {"code": code, "title": title, "menu_code": SHOP_MENU_CODE, "sort": 9, "description": "pytest"},
            token,
        )
        body = response.json()
        assert body["code"] == 200
        data = body["data"]
        self._created_group_ids.append(int(data["id"]))
        assert data["code"] == code
        assert data["title"] == title
        assert data["module"] == SHOP_MODULE
        assert int(data["status"]) == 1
        assert int(data["sort"]) == 9

    async def async_test_create_group_by_menu_id(self):
        """测试按菜单ID创建权限组（显式指定 module） (POST)"""
        token = await self.admin_token()
        menus = (await self._post("/admin/permission-group/get-menu-options", {}, token)).json()
        shop_menu = next(m for m in menus["data"] if m["code"] == SHOP_MENU_CODE)

        code = self._new_code()
        response = await self._post(
            "/admin/permission-group/create-group",
            {"code": code, "title": self._new_title(), "menu_id": int(shop_menu["id"]), "module": SHOP_MODULE},
            token,
        )
        body = response.json()
        assert body["code"] == 200
        self._created_group_ids.append(int(body["data"]["id"]))
        assert int(body["data"]["menu_id"]) == int(shop_menu["id"])

    async def async_test_create_group_auto_code(self):
        """测试创建权限组缺编码时按「pg:模块:序号」自动生成 (POST)"""
        token = await self.admin_token()
        response = await self._post(
            "/admin/permission-group/create-group",
            {"code": "", "title": self._new_title(), "menu_code": SHOP_MENU_CODE},
            token,
        )
        body = response.json()
        assert body["code"] == 200
        data = body["data"]
        self._created_group_ids.append(int(data["id"]))
        assert data["module"] == SHOP_MODULE
        assert data["code"].startswith(f"pg:{SHOP_MODULE}:")

    async def async_test_create_group_empty_title(self):
        """测试创建权限组缺名称返回400 (POST)"""
        token = await self.admin_token()
        response = await self._post(
            "/admin/permission-group/create-group",
            {"code": self._new_code(), "title": "", "menu_code": SHOP_MENU_CODE},
            token,
        )
        body = response.json()
        assert body["code"] == 400
        assert body["message"] == "权限组名称不能为空"

    async def async_test_create_group_duplicate_code(self):
        """测试创建权限组编码重复返回400 (POST)"""
        token = await self.admin_token()
        code = self._new_code()
        await self._create_group(token, code=code)

        response = await self._post(
            "/admin/permission-group/create-group",
            {"code": code, "title": self._new_title(), "menu_code": SHOP_MENU_CODE},
            token,
        )
        body = response.json()
        assert body["code"] == 400
        assert "权限组编码已存在" in body["message"]

    async def async_test_create_group_menu_not_found(self):
        """测试创建权限组菜单不存在返回400 (POST)"""
        token = await self.admin_token()
        response = await self._post(
            "/admin/permission-group/create-group",
            {"code": self._new_code(), "title": self._new_title(), "menu_code": "nav:not-exist"},
            token,
        )
        body = response.json()
        assert body["code"] == 400
        assert "菜单不存在" in body["message"]

    async def async_test_create_group_menu_required(self):
        """测试创建权限组未指定菜单返回400 (POST)"""
        token = await self.admin_token()
        response = await self._post(
            "/admin/permission-group/create-group",
            {"code": self._new_code(), "title": self._new_title()},
            token,
        )
        body = response.json()
        assert body["code"] == 400
        assert body["message"] == "菜单不能为空"

    async def async_test_create_group_module_not_resolvable(self):
        """测试菜单未关联业务模块且未显式指定 module 返回400 (POST)"""
        token = await self.admin_token()
        # 种子菜单均已关联模块，此处直连数据库构造一个无模块的临时菜单
        menu_id = await self._create_menu_without_module()
        response = await self._post(
            "/admin/permission-group/create-group",
            {"code": self._new_code(), "title": self._new_title(), "menu_id": menu_id},
            token,
        )
        body = response.json()
        assert body["code"] == 400
        assert "未关联业务模块" in body["message"]

    # ==================== 权限组主表：更新 ====================

    async def async_test_update_group(self):
        """测试更新权限组基本信息 (POST)"""
        token = await self.admin_token()
        group_id = await self._create_group(token)
        new_title = self._new_title()

        response = await self._post(
            "/admin/permission-group/update-group",
            {"id": group_id, "title": new_title, "sort": 3, "status": 0, "description": "pytest更新"},
            token,
        )
        body = response.json()
        assert body["code"] == 200
        data = body["data"]
        assert data["title"] == new_title
        assert int(data["sort"]) == 3
        assert int(data["status"]) == 0
        assert data["description"] == "pytest更新"

    async def async_test_update_group_duplicate_code(self):
        """测试更新权限组编码与其它组冲突返回400 (POST)"""
        token = await self.admin_token()
        first_id = await self._create_group(token)
        second_detail = (
            await self._post(
                "/admin/permission-group/get-group-detail", {"id": await self._create_group(token)}, token
            )
        ).json()

        response = await self._post(
            "/admin/permission-group/update-group",
            {"id": first_id, "code": second_detail["data"]["code"]},
            token,
        )
        body = response.json()
        assert body["code"] == 400
        assert "权限组编码已存在" in body["message"]

    async def async_test_update_group_missing_id(self):
        """测试更新权限组缺ID返回400 (POST)"""
        token = await self.admin_token()
        response = await self._post("/admin/permission-group/update-group", {"title": "x"}, token)
        body = response.json()
        assert body["code"] == 400
        assert body["message"] == "权限组ID不能为空"

    async def async_test_update_group_not_found(self):
        """测试更新不存在的权限组返回400 (POST)"""
        token = await self.admin_token()
        response = await self._post(
            "/admin/permission-group/update-group", {"id": MISSING_ID, "title": "x"}, token
        )
        body = response.json()
        assert body["code"] == 400
        assert body["message"] == "权限组不存在"

    # ==================== 权限组主表：删除 ====================

    async def async_test_delete_group(self):
        """测试删除权限组后详情不可查、列表不含 (POST)"""
        token = await self.admin_token()
        title = self._new_title()
        group_id = await self._create_group(token, title=title)

        response = await self._post("/admin/permission-group/delete-group", {"id": group_id}, token)
        body = response.json()
        assert body["code"] == 200
        assert body["message"] == "删除成功"

        detail = (await self._post("/admin/permission-group/get-group-detail", {"id": group_id}, token)).json()
        assert detail["code"] == 400
        assert detail["message"] == "权限组不存在"

        listed = (
            await self._post(
                "/admin/permission-group/get-group-list", {"page": 1, "limit": 50, "keyword": title}, token
            )
        ).json()
        assert listed["data"]["total"] == 0

    async def async_test_delete_group_cascade(self):
        """测试删除权限组级联清理子表与用户激活记录 (POST)"""
        token = await self.admin_token()
        group_id = await self._create_group(token)
        perm_ids = await self._permission_ids(SHOP_MODULE)
        await self._post(
            "/admin/permission-group/grant-group-permissions",
            {"id": group_id, "permission_ids": perm_ids},
            token,
        )
        await self._post(
            "/admin/permission-group/set-group-fields",
            {"id": group_id, "module": SHOP_MODULE, "fields": [{"field": SHOP_VALID_FIELDS[0]}]},
            token,
        )
        await self._post(
            "/admin/permission-group/set-group-data-scope",
            {"id": group_id, "module": SHOP_MODULE, "scope": "all"},
            token,
        )
        await self._post(
            "/admin/permission-group/bind-group-subjects",
            {"id": group_id, "subjects": [{"subject_type": "user", "subject_id": NON_ADMIN_USER_ID}]},
            token,
        )

        response = await self._post("/admin/permission-group/delete-group", {"id": group_id}, token)
        assert response.json()["code"] == 200

        conn = await asyncpg.connect(**PG_CONFIG)
        try:
            for table in (
                GROUP_PERMISSION_TABLE,
                GROUP_FIELD_TABLE,
                GROUP_DATA_TABLE,
                GROUP_SUBJECT_TABLE,
                USER_GROUP_TABLE,
            ):
                remaining = await conn.fetchval(
                    f"SELECT COUNT(*) FROM {table} WHERE group_id = $1", group_id
                )
                assert remaining == 0, f"{table} 残留 {remaining} 行"
        finally:
            await conn.close()

    async def async_test_delete_group_missing_id(self):
        """测试删除权限组缺ID返回400 (POST)"""
        token = await self.admin_token()
        response = await self._post("/admin/permission-group/delete-group", {}, token)
        body = response.json()
        assert body["code"] == 400
        assert body["message"] == "权限组ID不能为空"

    async def async_test_delete_group_not_found(self):
        """测试删除不存在的权限组返回400 (POST)"""
        token = await self.admin_token()
        response = await self._post("/admin/permission-group/delete-group", {"id": MISSING_ID}, token)
        body = response.json()
        assert body["code"] == 400
        assert body["message"] == "权限组不存在"

    # ==================== 组-操作权限点 ====================

    async def async_test_get_group_permissions_empty(self):
        """测试新建权限组未授权时权限点为空 (POST)"""
        token = await self.admin_token()
        group_id = await self._create_group(token)
        response = await self._post("/admin/permission-group/get-group-permissions", {"id": group_id}, token)
        body = response.json()
        assert body["code"] == 200
        assert body["data"]["permission_ids"] == []
        assert body["data"]["codes"] == []

    async def async_test_grant_group_permissions(self):
        """测试覆盖式授予同模块权限点并返回权限码 (POST)"""
        token = await self.admin_token()
        group_id = await self._create_group(token)
        perm_ids = await self._permission_ids(SHOP_MODULE)
        assert perm_ids, "未取到 shop 模块权限点"

        response = await self._post(
            "/admin/permission-group/grant-group-permissions",
            {"id": group_id, "permission_ids": perm_ids},
            token,
        )
        body = response.json()
        assert body["code"] == 200
        assert body["message"] == "授权成功"
        # 菜单准入由所属菜单自动补全，返回集 = 请求权限点 ∪ 菜单权限点
        menu_id = await self._group_menu_id(token, group_id)
        expected = sorted(set(perm_ids) | {menu_id})
        assert sorted(body["data"]["permission_ids"]) == expected
        assert len(body["data"]["codes"]) == len(expected)

        # 覆盖式：再次授权应替换而非累加（自动补全的菜单准入仍保留）
        again = await self._post(
            "/admin/permission-group/grant-group-permissions",
            {"id": group_id, "permission_ids": perm_ids[:1]},
            token,
        )
        assert sorted(again.json()["data"]["permission_ids"]) == sorted({perm_ids[0], menu_id})

    async def async_test_grant_group_permissions_group_node_allowed(self):
        """测试授权分组节点（type=0）不参与模块一致性拦截 (POST)"""
        token = await self.admin_token()
        group_id = await self._create_group(token)
        group_nodes = await self._permission_ids(SHOP_MODULE, perm_type=0, limit=5)
        assert group_nodes, "未取到分组节点"

        response = await self._post(
            "/admin/permission-group/grant-group-permissions",
            {"id": group_id, "permission_ids": group_nodes},
            token,
        )
        body = response.json()
        assert body["code"] == 200
        # 菜单准入自动补全，分组节点与菜单权限点一并生效
        menu_id = await self._group_menu_id(token, group_id)
        assert sorted(body["data"]["permission_ids"]) == sorted(set(group_nodes) | {menu_id})

    async def async_test_grant_group_permissions_cross_module(self):
        """测试授权跨模块权限点被拦截返回400 (POST)"""
        token = await self.admin_token()
        group_id = await self._create_group(token)
        product_perm_ids = await self._permission_ids("product")
        assert product_perm_ids, "未取到 product 模块权限点"

        response = await self._post(
            "/admin/permission-group/grant-group-permissions",
            {"id": group_id, "permission_ids": product_perm_ids},
            token,
        )
        body = response.json()
        assert body["code"] == 400
        assert f"权限点与权限组模块({SHOP_MODULE})不一致" in body["message"]

    async def async_test_grant_group_permissions_invalid(self):
        """测试授权不存在的权限点返回400 (POST)"""
        token = await self.admin_token()
        group_id = await self._create_group(token)
        response = await self._post(
            "/admin/permission-group/grant-group-permissions",
            {"id": group_id, "permission_ids": [MISSING_ID]},
            token,
        )
        body = response.json()
        assert body["code"] == 400
        assert "存在无效权限点" in body["message"]

    async def async_test_grant_group_permissions_missing_id(self):
        """测试授权缺权限组ID返回400 (POST)"""
        token = await self.admin_token()
        response = await self._post(
            "/admin/permission-group/grant-group-permissions", {"permission_ids": []}, token
        )
        body = response.json()
        assert body["code"] == 400
        assert body["message"] == "权限组ID不能为空"

    # ==================== 组-字段权限 ====================

    async def async_test_get_field_catalog(self):
        """测试字段目录返回业务列并排除系统列 (POST)"""
        token = await self.admin_token()
        response = await self._post("/admin/permission-group/get-field-catalog", {"module": SHOP_MODULE}, token)
        body = response.json()
        assert body["code"] == 200
        fields = {item["field"]: item["field_label"] for item in body["data"]}
        assert SHOP_VALID_FIELDS[0] in fields
        assert fields[SHOP_VALID_FIELDS[0]] == "平台编码"
        for system_column in ("id", "data_id", "is_deleted", "create_time", "update_time", "user_id"):
            assert system_column not in fields

    async def async_test_get_field_catalog_missing_module(self):
        """测试字段目录缺业务模块返回400 (POST)"""
        token = await self.admin_token()
        response = await self._post("/admin/permission-group/get-field-catalog", {}, token)
        body = response.json()
        assert body["code"] == 400
        assert body["message"] == "业务模块不能为空"

    async def async_test_get_field_catalog_invalid_module(self):
        """测试字段目录传入未登记模块返回400 (POST)"""
        token = await self.admin_token()
        response = await self._post(
            "/admin/permission-group/get-field-catalog", {"module": UNKNOWN_MODULE}, token
        )
        body = response.json()
        assert body["code"] == 400
        assert "模块未登记业务表" in body["message"]

    async def async_test_set_group_fields(self):
        """测试保存字段权限：可见性写入并回填中文名 (POST)"""
        token = await self.admin_token()
        group_id = await self._create_group(token)
        fields = [
            {"field": SHOP_VALID_FIELDS[0], "visible": 0},
            {"field": SHOP_VALID_FIELDS[1], "visible": 1, "editable": 0},
        ]
        response = await self._post(
            "/admin/permission-group/set-group-fields",
            {"id": group_id, "module": SHOP_MODULE, "fields": fields},
            token,
        )
        body = response.json()
        assert body["code"] == 200
        assert body["message"] == "保存成功"
        saved = {item["field"]: item for item in body["data"]}
        assert int(saved[SHOP_VALID_FIELDS[0]]["visible"]) == 0
        assert int(saved[SHOP_VALID_FIELDS[1]]["visible"]) == 1
        assert int(saved[SHOP_VALID_FIELDS[1]]["editable"]) == 0
        assert saved[SHOP_VALID_FIELDS[0]]["field_label"] == "平台编码"
        assert all(item["module"] == SHOP_MODULE for item in body["data"])

    async def async_test_set_group_fields_replace(self):
        """测试字段权限为覆盖式保存 (POST)"""
        token = await self.admin_token()
        group_id = await self._create_group(token)
        await self._post(
            "/admin/permission-group/set-group-fields",
            {"id": group_id, "module": SHOP_MODULE, "fields": [{"field": SHOP_VALID_FIELDS[0]}]},
            token,
        )
        response = await self._post(
            "/admin/permission-group/set-group-fields",
            {"id": group_id, "module": SHOP_MODULE, "fields": [{"field": SHOP_VALID_FIELDS[1]}]},
            token,
        )
        body = response.json()
        assert body["code"] == 200
        assert [item["field"] for item in body["data"]] == [SHOP_VALID_FIELDS[1]]

    async def async_test_set_group_fields_out_of_catalog(self):
        """测试保存不在模块目录内的字段返回400 (POST)"""
        token = await self.admin_token()
        group_id = await self._create_group(token)
        response = await self._post(
            "/admin/permission-group/set-group-fields",
            {"id": group_id, "module": SHOP_MODULE, "fields": [{"field": SHOP_INVALID_FIELD}]},
            token,
        )
        body = response.json()
        assert body["code"] == 400
        assert f"字段不在模块 {SHOP_MODULE} 目录内" in body["message"]

    async def async_test_set_group_fields_missing_id(self):
        """测试保存字段权限缺权限组ID返回400 (POST)"""
        token = await self.admin_token()
        response = await self._post(
            "/admin/permission-group/set-group-fields", {"module": SHOP_MODULE, "fields": []}, token
        )
        body = response.json()
        assert body["code"] == 400
        assert body["message"] == "权限组ID不能为空"

    # ==================== 组-数据权限 ====================

    async def async_test_set_group_data_scope_all(self):
        """测试保存数据范围为全部 (POST)"""
        token = await self.admin_token()
        group_id = await self._create_group(token)
        response = await self._post(
            "/admin/permission-group/set-group-data-scope",
            {"id": group_id, "module": SHOP_MODULE, "scope": "all"},
            token,
        )
        body = response.json()
        assert body["code"] == 200
        assert body["message"] == "保存成功"
        assert body["data"]["scope"] == "all"
        assert not body["data"]["custom_dept_ids"]

    async def async_test_set_group_data_scope_custom(self):
        """测试保存自定义数据范围携带部门 (POST)"""
        token = await self.admin_token()
        group_id = await self._create_group(token)
        response = await self._post(
            "/admin/permission-group/set-group-data-scope",
            {"id": group_id, "module": SHOP_MODULE, "scope": "custom", "custom_dept_ids": [2]},
            token,
        )
        body = response.json()
        assert body["code"] == 200
        assert body["data"]["scope"] == "custom"
        assert list(body["data"]["custom_dept_ids"]) == [2]

        detail = (await self._post("/admin/permission-group/get-group-detail", {"id": group_id}, token)).json()
        assert detail["data"]["data_scopes"][0]["scope"] == "custom"

    async def async_test_set_group_data_scope_invalid(self):
        """测试保存非法数据范围返回400 (POST)"""
        token = await self.admin_token()
        group_id = await self._create_group(token)
        response = await self._post(
            "/admin/permission-group/set-group-data-scope",
            {"id": group_id, "module": SHOP_MODULE, "scope": "invalid_scope"},
            token,
        )
        body = response.json()
        assert body["code"] == 400
        assert "数据范围非法" in body["message"]

    async def async_test_set_group_data_scope_custom_without_dept(self):
        """测试自定义数据范围未选部门返回400 (POST)"""
        token = await self.admin_token()
        group_id = await self._create_group(token)
        response = await self._post(
            "/admin/permission-group/set-group-data-scope",
            {"id": group_id, "module": SHOP_MODULE, "scope": "custom", "custom_dept_ids": []},
            token,
        )
        body = response.json()
        assert body["code"] == 400
        assert body["message"] == "自定义数据范围必须选择部门"

    async def async_test_set_group_data_scope_custom_invalid_dept(self):
        """测试自定义数据范围含无效部门返回400 (POST)"""
        token = await self.admin_token()
        group_id = await self._create_group(token)
        response = await self._post(
            "/admin/permission-group/set-group-data-scope",
            {"id": group_id, "module": SHOP_MODULE, "scope": "custom", "custom_dept_ids": [MISSING_ID]},
            token,
        )
        body = response.json()
        assert body["code"] == 400
        assert "存在无效部门" in body["message"]

    async def async_test_set_group_data_scope_missing_id(self):
        """测试保存数据权限缺权限组ID返回400 (POST)"""
        token = await self.admin_token()
        response = await self._post(
            "/admin/permission-group/set-group-data-scope", {"module": SHOP_MODULE, "scope": "all"}, token
        )
        body = response.json()
        assert body["code"] == 400
        assert body["message"] == "权限组ID不能为空"

    # ==================== 组-主体绑定 ====================

    async def async_test_get_bindable_subjects(self):
        """测试可绑定主体选项返回部门/角色/人员 (POST)"""
        token = await self.admin_token()
        response = await self._post("/admin/permission-group/get-bindable-subjects", {}, token)
        body = response.json()
        assert body["code"] == 200
        data = body["data"]
        assert isinstance(data["depts"], list) and data["depts"]
        assert isinstance(data["roles"], list) and data["roles"]
        assert isinstance(data["users"], list) and data["users"]

    async def async_test_bind_group_subjects(self):
        """测试绑定三类主体并回填主体显示名 (POST)"""
        token = await self.admin_token()
        group_id = await self._create_group(token)
        subjects = [
            {"subject_type": "dept", "subject_id": 2},
            {"subject_type": "role", "subject_id": 7},
            {"subject_type": "user", "subject_id": NON_ADMIN_USER_ID},
        ]
        response = await self._post(
            "/admin/permission-group/bind-group-subjects",
            {"id": group_id, "subjects": subjects},
            token,
        )
        body = response.json()
        assert body["code"] == 200
        assert body["message"] == "绑定成功"
        assert len(body["data"]) == 3
        keys = {(item["subject_type"], item["subject_id"]) for item in body["data"]}
        assert keys == {("dept", 2), ("role", 7), ("user", NON_ADMIN_USER_ID)}
        assert all(item["subject_name"] for item in body["data"])

    async def async_test_bind_group_subjects_dedupe(self):
        """测试重复主体去重（边界：同一主体提交两次） (POST)"""
        token = await self.admin_token()
        group_id = await self._create_group(token)
        response = await self._post(
            "/admin/permission-group/bind-group-subjects",
            {
                "id": group_id,
                "subjects": [
                    {"subject_type": "dept", "subject_id": 2},
                    {"subject_type": "dept", "subject_id": 2},
                ],
            },
            token,
        )
        body = response.json()
        assert body["code"] == 200
        assert len(body["data"]) == 1

    async def async_test_bind_group_subjects_invalid_type(self):
        """测试绑定非法主体类型返回400 (POST)"""
        token = await self.admin_token()
        group_id = await self._create_group(token)
        response = await self._post(
            "/admin/permission-group/bind-group-subjects",
            {"id": group_id, "subjects": [{"subject_type": "group", "subject_id": 1}]},
            token,
        )
        body = response.json()
        assert body["code"] == 400
        assert "主体类型非法" in body["message"]

    async def async_test_bind_group_subjects_empty_id(self):
        """测试绑定主体缺ID返回400 (POST)"""
        token = await self.admin_token()
        group_id = await self._create_group(token)
        response = await self._post(
            "/admin/permission-group/bind-group-subjects",
            {"id": group_id, "subjects": [{"subject_type": "dept", "subject_id": None}]},
            token,
        )
        body = response.json()
        assert body["code"] == 400
        assert body["message"] == "主体ID不能为空"

    async def async_test_bind_group_subjects_not_found(self):
        """测试绑定不存在的主体返回400 (POST)"""
        token = await self.admin_token()
        group_id = await self._create_group(token)
        response = await self._post(
            "/admin/permission-group/bind-group-subjects",
            {"id": group_id, "subjects": [{"subject_type": "dept", "subject_id": MISSING_ID}]},
            token,
        )
        body = response.json()
        assert body["code"] == 400
        assert "dept 主体不存在" in body["message"]

    async def async_test_bind_group_subjects_missing_id(self):
        """测试绑定主体缺权限组ID返回400 (POST)"""
        token = await self.admin_token()
        response = await self._post(
            "/admin/permission-group/bind-group-subjects", {"subjects": []}, token
        )
        body = response.json()
        assert body["code"] == 400
        assert body["message"] == "权限组ID不能为空"

    # ==================== 菜单选项 ====================

    async def async_test_get_menu_options(self):
        """测试菜单选项返回菜单权限点与推导的业务模块 (POST)"""
        token = await self.admin_token()
        response = await self._post("/admin/permission-group/get-menu-options", {}, token)
        body = response.json()
        assert body["code"] == 200
        menus = body["data"]
        assert isinstance(menus, list) and menus
        shop_menu = next((m for m in menus if m["code"] == SHOP_MENU_CODE), None)
        assert shop_menu is not None
        assert shop_menu["business_module"] == SHOP_MODULE

    # ==================== 当前用户权限组（自助） ====================

    async def async_test_get_user_groups_admin(self):
        """测试管理员查询权限组返回空且不参与切换 (POST)"""
        token = await self.admin_token()
        response = await self._post("/admin/permission-group/get-user-groups", {}, token)
        body = response.json()
        assert body["code"] == 200
        assert body["data"]["items"] == []
        assert body["data"]["active_group_id"] is None

    async def async_test_get_user_groups_normal_user(self):
        """测试普通用户查询可用权限组（含绑定后的临时组） (POST)"""
        admin_token = await self.admin_token()
        group_id = await self._create_group(admin_token)
        await self._post(
            "/admin/permission-group/bind-group-subjects",
            {"id": group_id, "subjects": [{"subject_type": "user", "subject_id": NON_ADMIN_USER_ID}]},
            admin_token,
        )

        token = await self.non_admin_token()
        response = await self._post("/admin/permission-group/get-user-groups", {}, token)
        body = response.json()
        assert body["code"] == 200
        items = body["data"]["items"]
        target = next((item for item in items if int(item["id"]) == group_id), None)
        assert target is not None
        assert target["is_active"] == 0
        assert "permission_count" in target

    async def async_test_menu_visibility_covers_all_available_groups(self):
        """测试菜单可见性并入全部可用权限组（而非仅激活组） (POST)"""
        admin_token = await self.admin_token()
        # 新建一个归属「日志管理」菜单的临时组并绑定普通用户（不激活）
        log_group_id = await self._create_group(admin_token, menu_code=LOG_MENU_CODE)
        await self._post(
            "/admin/permission-group/bind-group-subjects",
            {"id": log_group_id, "subjects": [{"subject_type": "user", "subject_id": NON_ADMIN_USER_ID}]},
            admin_token,
        )

        token = await self.non_admin_token()
        info = (await self._post("/admin/auth/get-user-info", {}, token)).json()
        assert info["code"] == 200
        assert LOG_MENU_CODE in info["data"]["permissions"]

        tree = (await self._post("/admin/menu/get-user-menu-tree", {}, token)).json()
        assert tree["code"] == 200
        assert LOG_MENU_PATH in self._collect_menu_paths(tree["data"])

    async def async_test_activate_user_group(self):
        """测试普通用户按组互斥切换激活权限组 (POST)"""
        admin_token = await self.admin_token()
        group_id = await self._create_group(admin_token)
        await self._post(
            "/admin/permission-group/bind-group-subjects",
            {"id": group_id, "subjects": [{"subject_type": "user", "subject_id": NON_ADMIN_USER_ID}]},
            admin_token,
        )

        token = await self.non_admin_token()
        response = await self._post(
            "/admin/permission-group/activate-user-group", {"group_id": group_id}, token
        )
        body = response.json()
        assert body["code"] == 200
        assert body["message"] == "切换成功"
        assert int(body["data"]["active_group_id"]) == group_id

        listed = (await self._post("/admin/permission-group/get-user-groups", {}, token)).json()
        assert int(listed["data"]["active_group_id"]) == group_id
        target = next(item for item in listed["data"]["items"] if int(item["id"]) == group_id)
        assert target["is_active"] == 1
        # 互斥：其余可用组均未激活
        assert all(
            item["is_active"] == 0 for item in listed["data"]["items"] if int(item["id"]) != group_id
        )

    async def async_test_activate_user_group_empty_rejected(self):
        """测试普通用户传空组ID被拒绝返回400（不支持清空） (POST)"""
        token = await self.non_admin_token()
        response = await self._post("/admin/permission-group/activate-user-group", {"group_id": None}, token)
        body = response.json()
        assert body["code"] == 400
        assert body["message"] == "请选择要激活的权限组"

    async def async_test_activate_user_group_not_available(self):
        """测试普通用户切换未绑定的权限组返回400 (POST)"""
        admin_token = await self.admin_token()
        group_id = await self._create_group(admin_token)

        token = await self.non_admin_token()
        response = await self._post(
            "/admin/permission-group/activate-user-group", {"group_id": group_id}, token
        )
        body = response.json()
        assert body["code"] == 400
        assert body["message"] == "该权限组不在当前用户的可用范围内"

    async def async_test_activate_user_group_admin_rejected(self):
        """测试管理员切换权限组被拒绝返回400 (POST)"""
        token = await self.admin_token()
        response = await self._post(
            "/admin/permission-group/activate-user-group", {"group_id": 1}, token
        )
        body = response.json()
        assert body["code"] == 400
        assert body["message"] == "管理员不支持权限组切换"

    # ==================== 鉴权 ====================

    async def async_test_manage_endpoint_requires_permission(self):
        """测试普通用户无授权权限点访问管理端点返回403 (POST)"""
        token = await self.non_admin_token()
        response = await self._post("/admin/permission-group/get-group-list", {"page": 1, "limit": 10}, token)
        assert response.status_code == 403

    async def async_test_manage_endpoint_requires_login(self):
        """测试未登录访问管理端点返回401 (POST)"""
        response = await self._post("/admin/permission-group/get-group-list", {"page": 1, "limit": 10})
        assert response.status_code == 401

    async def async_test_self_service_requires_login(self):
        """测试未登录访问自助端点返回401 (POST)"""
        response = await self._post("/admin/permission-group/get-user-groups", {})
        assert response.status_code == 401

    async def async_test_forged_token_rejected(self):
        """测试伪造 token 访问权限组端点返回401 (POST)"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/admin/permission-group/get-user-groups",
                json={"data": {}},
                headers={"Authorization": "Bearer abc.def.ghi"},
            )
        assert response.status_code == 401

    # ==================== 测试入口 ====================

    def test_get_group_list(self):
        asyncio.run(self.async_test_get_group_list())

    def test_get_group_list_pagination(self):
        asyncio.run(self.async_test_get_group_list_pagination())

    def test_get_group_list_keyword(self):
        asyncio.run(self.async_test_get_group_list_keyword())

    def test_get_group_list_status(self):
        asyncio.run(self.async_test_get_group_list_status())

    def test_get_group_list_menu_filter(self):
        asyncio.run(self.async_test_get_group_list_menu_filter())

    def test_get_group_list_module_filter(self):
        asyncio.run(self.async_test_get_group_list_module_filter())

    def test_get_group_list_data_scope_count(self):
        asyncio.run(self.async_test_get_group_list_data_scope_count())

    def test_get_group_detail(self):
        asyncio.run(self.async_test_get_group_detail())

    def test_get_group_detail_missing_id(self):
        asyncio.run(self.async_test_get_group_detail_missing_id())

    def test_get_group_detail_not_found(self):
        asyncio.run(self.async_test_get_group_detail_not_found())

    def test_create_group_by_menu_code(self):
        asyncio.run(self.async_test_create_group_by_menu_code())

    def test_create_group_by_menu_id(self):
        asyncio.run(self.async_test_create_group_by_menu_id())

    def test_create_group_auto_code(self):
        asyncio.run(self.async_test_create_group_auto_code())

    def test_create_group_empty_title(self):
        asyncio.run(self.async_test_create_group_empty_title())

    def test_create_group_duplicate_code(self):
        asyncio.run(self.async_test_create_group_duplicate_code())

    def test_create_group_menu_not_found(self):
        asyncio.run(self.async_test_create_group_menu_not_found())

    def test_create_group_menu_required(self):
        asyncio.run(self.async_test_create_group_menu_required())

    def test_create_group_module_not_resolvable(self):
        asyncio.run(self.async_test_create_group_module_not_resolvable())

    def test_update_group(self):
        asyncio.run(self.async_test_update_group())

    def test_update_group_duplicate_code(self):
        asyncio.run(self.async_test_update_group_duplicate_code())

    def test_update_group_missing_id(self):
        asyncio.run(self.async_test_update_group_missing_id())

    def test_update_group_not_found(self):
        asyncio.run(self.async_test_update_group_not_found())

    def test_delete_group(self):
        asyncio.run(self.async_test_delete_group())

    def test_delete_group_cascade(self):
        asyncio.run(self.async_test_delete_group_cascade())

    def test_delete_group_missing_id(self):
        asyncio.run(self.async_test_delete_group_missing_id())

    def test_delete_group_not_found(self):
        asyncio.run(self.async_test_delete_group_not_found())

    def test_get_group_permissions_empty(self):
        asyncio.run(self.async_test_get_group_permissions_empty())

    def test_grant_group_permissions(self):
        asyncio.run(self.async_test_grant_group_permissions())

    def test_grant_group_permissions_group_node_allowed(self):
        asyncio.run(self.async_test_grant_group_permissions_group_node_allowed())

    def test_grant_group_permissions_cross_module(self):
        asyncio.run(self.async_test_grant_group_permissions_cross_module())

    def test_grant_group_permissions_invalid(self):
        asyncio.run(self.async_test_grant_group_permissions_invalid())

    def test_grant_group_permissions_missing_id(self):
        asyncio.run(self.async_test_grant_group_permissions_missing_id())

    def test_get_field_catalog(self):
        asyncio.run(self.async_test_get_field_catalog())

    def test_get_field_catalog_missing_module(self):
        asyncio.run(self.async_test_get_field_catalog_missing_module())

    def test_get_field_catalog_invalid_module(self):
        asyncio.run(self.async_test_get_field_catalog_invalid_module())

    def test_set_group_fields(self):
        asyncio.run(self.async_test_set_group_fields())

    def test_set_group_fields_replace(self):
        asyncio.run(self.async_test_set_group_fields_replace())

    def test_set_group_fields_out_of_catalog(self):
        asyncio.run(self.async_test_set_group_fields_out_of_catalog())

    def test_set_group_fields_missing_id(self):
        asyncio.run(self.async_test_set_group_fields_missing_id())

    def test_set_group_data_scope_all(self):
        asyncio.run(self.async_test_set_group_data_scope_all())

    def test_set_group_data_scope_custom(self):
        asyncio.run(self.async_test_set_group_data_scope_custom())

    def test_set_group_data_scope_invalid(self):
        asyncio.run(self.async_test_set_group_data_scope_invalid())

    def test_set_group_data_scope_custom_without_dept(self):
        asyncio.run(self.async_test_set_group_data_scope_custom_without_dept())

    def test_set_group_data_scope_custom_invalid_dept(self):
        asyncio.run(self.async_test_set_group_data_scope_custom_invalid_dept())

    def test_set_group_data_scope_missing_id(self):
        asyncio.run(self.async_test_set_group_data_scope_missing_id())

    def test_get_bindable_subjects(self):
        asyncio.run(self.async_test_get_bindable_subjects())

    def test_bind_group_subjects(self):
        asyncio.run(self.async_test_bind_group_subjects())

    def test_bind_group_subjects_dedupe(self):
        asyncio.run(self.async_test_bind_group_subjects_dedupe())

    def test_bind_group_subjects_invalid_type(self):
        asyncio.run(self.async_test_bind_group_subjects_invalid_type())

    def test_bind_group_subjects_empty_id(self):
        asyncio.run(self.async_test_bind_group_subjects_empty_id())

    def test_bind_group_subjects_not_found(self):
        asyncio.run(self.async_test_bind_group_subjects_not_found())

    def test_bind_group_subjects_missing_id(self):
        asyncio.run(self.async_test_bind_group_subjects_missing_id())

    def test_get_menu_options(self):
        asyncio.run(self.async_test_get_menu_options())

    def test_get_user_groups_admin(self):
        asyncio.run(self.async_test_get_user_groups_admin())

    def test_get_user_groups_normal_user(self):
        asyncio.run(self.async_test_get_user_groups_normal_user())

    def test_menu_visibility_covers_all_available_groups(self):
        asyncio.run(self.async_test_menu_visibility_covers_all_available_groups())

    def test_activate_user_group(self):
        asyncio.run(self.async_test_activate_user_group())

    def test_activate_user_group_empty_rejected(self):
        asyncio.run(self.async_test_activate_user_group_empty_rejected())

    def test_activate_user_group_not_available(self):
        asyncio.run(self.async_test_activate_user_group_not_available())

    def test_activate_user_group_admin_rejected(self):
        asyncio.run(self.async_test_activate_user_group_admin_rejected())

    def test_manage_endpoint_requires_permission(self):
        asyncio.run(self.async_test_manage_endpoint_requires_permission())

    def test_manage_endpoint_requires_login(self):
        asyncio.run(self.async_test_manage_endpoint_requires_login())

    def test_self_service_requires_login(self):
        asyncio.run(self.async_test_self_service_requires_login())

    def test_forged_token_rejected(self):
        asyncio.run(self.async_test_forged_token_rejected())
