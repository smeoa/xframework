"""菜单接口鉴权与操作权限测试

鉴权链路（framework/core/auth.py）：
- 全部 admin 路由挂载全局 ``require_login``：未携带凭据 → 401；
  凭据支持 ``Authorization: Bearer <JWT>``（/admin/auth/login 下发）与 ``X-API-Key``。
- 各接口在路由上额外声明 ``require_permission("sysmenu:*")``：
  普通用户缺少对应权限码 → 403；管理员（is_admin=True）直通全量权限。

本套件只验证「登录校验 + 操作权限拦截」边界：
- 写接口（创建/更新/删除/批量/导入/导出）仅验证 401/403，
  不做管理员实调用，避免污染菜单种子数据；
- 只读接口额外验证管理员实调用返回 200 及数据结构。

账号：admin / admin123（管理员）、deptuser / 123456（普通用户，无 sysmenu:* 权限）。
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
    ("/admin/menu/get-menu-tree", "sysmenu:list"),
    ("/admin/menu/get-menu-list", "sysmenu:list"),
    ("/admin/menu/create-menu", "sysmenu:create"),
    ("/admin/menu/update-menu", "sysmenu:update"),
    ("/admin/menu/delete-menu", "sysmenu:delete"),
    ("/admin/menu/destroy-menu", "sysmenu:delete"),
    ("/admin/menu/batch-all-menu", "sysmenu:delete"),
    ("/admin/menu/batch-menu", "sysmenu:delete"),
    ("/admin/menu/batch-update-menus", "sysmenu:update"),
    ("/admin/menu/export-menu", "sysmenu:export"),
    ("/admin/menu/import-menu", "sysmenu:import"),
]

# 只读接口：管理员实调用应返回 200
READ_ENDPOINTS: List[str] = [
    "/admin/menu/get-menu-tree",
    "/admin/menu/get-menu-list",
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


class TestMenuAPI:
    """菜单管理接口：登录校验 + 操作权限测试"""

    # ==================== 未登录 → 401 ====================

    @pytest.mark.parametrize("path,perm", GUARDED_ENDPOINTS)
    def test_requires_login(self, path: str, perm: str):
        """未携带凭据访问菜单接口 → 401"""
        response = _post(path)
        assert response.status_code == 401, response.text
        assert response.json().get("detail")

    def test_forged_token_rejected(self):
        """伪造 token → 401"""
        response = _post("/admin/menu/get-menu-tree", token="forged.invalid.token")
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
        response = _post(path, token=admin_token(), payload={"data": {"page": 1, "limit": 20}})
        assert response.status_code == 200, response.text
        assert response.json()["code"] == 200

    def test_admin_get_menu_tree_shape(self):
        """管理员获取菜单树：返回非空列表且含 permission 字段"""
        response = _post("/admin/menu/get-menu-tree", token=admin_token())
        assert response.status_code == 200, response.text
        data = response.json()["data"]
        assert isinstance(data, list)
        assert data, "菜单树不应为空"
        assert "permission" in data[0]

    def test_admin_get_menu_list_shape(self):
        """管理员获取菜单列表：返回 items / total"""
        response = _post(
            "/admin/menu/get-menu-list", token=admin_token(), payload={"data": {"page": 1, "limit": 20}}
        )
        assert response.status_code == 200, response.text
        data = response.json()["data"]
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)

    # ==================== 仅需登录的接口（无操作权限要求） ====================

    def test_get_user_menu_tree_requires_login_only(self):
        """侧边栏菜单树仅需登录：未登录 401，普通用户（无 sysmenu:list）可访问 200"""
        assert _post("/admin/menu/get-user-menu-tree").status_code == 401

        response = _post("/admin/menu/get-user-menu-tree", token=non_admin_token())
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["code"] == 200
        assert isinstance(body["data"], list)
