"""组织管理接口鉴权与操作权限测试

鉴权链路（framework/core/auth.py）：
- 全部 admin 路由挂载全局 ``require_login``：未携带凭据 → 401；
  凭据支持 ``Authorization: Bearer <JWT>``（/admin/auth/login 下发）与 ``X-API-Key``。
- 各接口在路由上额外声明 ``require_permission("org:*")``：
  普通用户缺少对应权限码 → 403；管理员（is_admin=True）直通全量权限。

覆盖 部门 / 用户 / 角色 三组接口的 401（未登录）、403（无权限）边界，
并对只读接口验证管理员实调用 200。
写接口（创建/更新/删除/批量/导入/导出）仅验证边界，不做管理员实调用，避免污染组织数据。

账号：admin / admin123（管理员）、deptuser / 123456（普通用户，无 org:* 权限）。
前置：后端已启动。
"""

from typing import Any, Dict, List, Optional, Tuple

import requests
import pytest

BASE_URL = "http://localhost:8000"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
NON_ADMIN_USERNAME = "deptuser"
NON_ADMIN_PASSWORD = "123456"

# 需登录且需操作权限的接口：(路径, 所需权限码)
GUARDED_ENDPOINTS: List[Tuple[str, str]] = [
    # 部门
    ("/admin/organization/get-dept-tree", "org:dept:list"),
    ("/admin/organization/get-dept", "org:dept:list"),
    ("/admin/organization/create-dept", "org:dept:create"),
    ("/admin/organization/update-dept", "org:dept:update"),
    ("/admin/organization/delete-dept", "org:dept:delete"),
    # 用户
    ("/admin/organization/get-user-list", "org:user:list"),
    ("/admin/organization/get-user", "org:user:list"),
    ("/admin/organization/create-user", "org:user:create"),
    ("/admin/organization/update-user", "org:user:update"),
    ("/admin/organization/delete-user", "org:user:delete"),
    ("/admin/organization/destroy-user", "org:user:delete"),
    ("/admin/organization/import-users", "org:user:import"),
    ("/admin/organization/export-users", "org:user:export"),
    ("/admin/organization/export-users-selected", "org:user:export"),
    ("/admin/organization/delete-users-batch", "org:user:delete"),
    ("/admin/organization/delete-users-selected", "org:user:delete"),
    ("/admin/organization/update-users-batch", "org:user:update"),
    # 角色
    ("/admin/organization/get-role-tree", "org:role:list"),
    ("/admin/organization/get-members", "org:role:list"),
    ("/admin/organization/get-available-users", "org:role:list"),
    ("/admin/organization/add-members", "org:role:grant"),
    ("/admin/organization/remove-member", "org:role:grant"),
    ("/admin/organization/remove-members-batch", "org:role:grant"),
    ("/admin/organization/get-permission-tree", "org:role:grant"),
    ("/admin/organization/get-role-permissions", "org:role:grant"),
    ("/admin/organization/grant-role-permissions", "org:role:grant"),
    ("/admin/organization/import-roles", "org:role:import"),
    ("/admin/organization/export-roles", "org:role:export"),
    ("/admin/organization/export-role-members", "org:role:export"),
    ("/admin/organization/create-role", "org:role:create"),
    ("/admin/organization/update-role", "org:role:update"),
    ("/admin/organization/delete-role", "org:role:delete"),
]

# 只读接口：管理员实调用应返回 200
READ_ENDPOINTS: List[str] = [
    "/admin/organization/get-dept-tree",
    "/admin/organization/get-user-list",
    "/admin/organization/get-role-tree",
    "/admin/organization/get-members",
    "/admin/organization/get-available-users",
    "/admin/organization/get-permission-tree",
]


def _post(
    path: str, token: Optional[str] = None, payload: Optional[Dict[str, Any]] = None
) -> requests.Response:
    """发起 POST 请求（可携带 Bearer token）"""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return requests.post(
        f"{BASE_URL}{path}", headers=headers, json=payload if payload is not None else {}, timeout=30
    )


_LOGIN_CACHE: Dict[str, str] = {}


def _token(username: str, password: str) -> str:
    """登录并缓存 token（同一次测试会话内复用）"""
    if username not in _LOGIN_CACHE:
        response = _post("/admin/auth/login", payload={"username": username, "password": password})
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["code"] == 200, body
        _LOGIN_CACHE[username] = body["data"]["token"]
    return _LOGIN_CACHE[username]


def admin_token() -> str:
    """管理员 token"""
    return _token(ADMIN_USERNAME, ADMIN_PASSWORD)


def non_admin_token() -> str:
    """普通用户 token"""
    return _token(NON_ADMIN_USERNAME, NON_ADMIN_PASSWORD)


class TestOrganizationAPI:
    """组织管理接口：登录校验 + 操作权限测试"""

    # ==================== 未登录 → 401 ====================

    @pytest.mark.parametrize("path,perm", GUARDED_ENDPOINTS)
    def test_requires_login(self, path: str, perm: str):
        """未携带凭据访问组织接口 → 401"""
        response = _post(path)
        assert response.status_code == 401, response.text
        assert response.json().get("detail")

    def test_forged_token_rejected(self):
        """伪造 token → 401"""
        response = _post("/admin/organization/get-dept-tree", token="forged.invalid.token")
        assert response.status_code == 401, response.text

    # ==================== 普通用户无权限 → 403 ====================

    @pytest.mark.parametrize("path,perm", GUARDED_ENDPOINTS)
    def test_forbidden_for_non_admin(self, path: str, perm: str):
        """普通用户缺少对应操作权限 → 403，且响应指明所需权限码"""
        response = _post(path, token=non_admin_token())
        assert response.status_code == 403, response.text
        assert perm in response.json().get("detail", "")

    # ==================== 管理员放行 → 200 ====================

    @pytest.mark.parametrize("path", READ_ENDPOINTS)
    def test_admin_allowed_on_read(self, path: str):
        """管理员（全量权限）访问只读接口 → 200"""
        response = _post(path, token=admin_token(), payload={"data": {"page": 1, "limit": 5}})
        assert response.status_code == 200, response.text
        assert response.json()["code"] == 200

    def test_admin_get_dept_tree_shape(self):
        """部门树：返回列表"""
        response = _post("/admin/organization/get-dept-tree", token=admin_token())
        assert response.status_code == 200, response.text
        assert isinstance(response.json()["data"], list)

    def test_admin_get_user_list_shape(self):
        """用户列表：返回 items / total"""
        response = _post(
            "/admin/organization/get-user-list", token=admin_token(), payload={"data": {"page": 1, "limit": 5}}
        )
        assert response.status_code == 200, response.text
        data = response.json()["data"]
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)

    def test_admin_get_role_tree_shape(self):
        """角色树：返回列表"""
        response = _post("/admin/organization/get-role-tree", token=admin_token())
        assert response.status_code == 200, response.text
        assert isinstance(response.json()["data"], list)

    def test_admin_get_members_shape(self):
        """角色成员：返回 items / total"""
        response = _post("/admin/organization/get-members", token=admin_token())
        assert response.status_code == 200, response.text
        data = response.json()["data"]
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)

    def test_admin_get_permission_tree_shape(self):
        """权限树：返回列表"""
        response = _post("/admin/organization/get-permission-tree", token=admin_token())
        assert response.status_code == 200, response.text
        assert isinstance(response.json()["data"], list)
