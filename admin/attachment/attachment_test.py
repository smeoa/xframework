"""附件管理接口鉴权与权限边界测试

覆盖：
- 未登录访问 → 401（全局 require_login）
- 伪造 token → 401
- 非管理员（无 attachment:* 权限）→ 403，detail 含缺失权限码
- 管理员访问读接口 → 200

注：下载/预览为 GET /download/{id}、GET /preview/{id}（并非 download-attachment/*）。
"""

from typing import List, Tuple

import pytest
import requests

BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/admin/auth/login"

# 需要 attachment:* 权限的 POST 接口（路径, 权限码）
GUARDED_POST_ENDPOINTS: List[Tuple[str, str]] = [
    ("/admin/attachment/get-attachment", "attachment:list"),
    ("/admin/attachment/get-attachment-list", "attachment:list"),
    ("/admin/attachment/create-attachment", "attachment:create"),
    ("/admin/attachment/update-attachment", "attachment:update"),
    ("/admin/attachment/update-by-data-id", "attachment:update"),
    ("/admin/attachment/delete-attachment", "attachment:delete"),
    ("/admin/attachment/destroy-attachment", "attachment:delete"),
    ("/admin/attachment/batch-all-attachment", "attachment:delete"),
    ("/admin/attachment/batch-attachment", "attachment:delete"),
    ("/admin/attachment/upload-attachment", "attachment:upload"),
]

# 需要 attachment:download 权限的 GET 接口
GUARDED_GET_PATHS: List[str] = [
    "/admin/attachment/download/1",
    "/admin/attachment/preview/1",
]

_LOGIN_CACHE = {}


def _token(username: str, password: str) -> str:
    key = (username, password)
    if key not in _LOGIN_CACHE:
        resp = requests.post(LOGIN_URL, json={"username": username, "password": password}, timeout=30)
        assert resp.status_code == 200, resp.text
        _LOGIN_CACHE[key] = resp.json()["data"]["token"]
    return _LOGIN_CACHE[key]


def _post(path: str, token: str = None, payload=None) -> requests.Response:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return requests.post(f"{BASE_URL}{path}", headers=headers,
                         json=payload if payload is not None else {}, timeout=30)


def _get(path: str, token: str = None) -> requests.Response:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return requests.get(f"{BASE_URL}{path}", headers=headers, timeout=30)


class TestAttachmentPermissionGuard:
    """附件接口鉴权 + 权限边界"""

    @pytest.mark.parametrize("path,perm", GUARDED_POST_ENDPOINTS)
    def test_post_requires_login(self, path, perm):
        """未携带 token → 401"""
        resp = _post(path)
        assert resp.status_code == 401, resp.text

    @pytest.mark.parametrize("path", GUARDED_GET_PATHS)
    def test_get_requires_login(self, path):
        """下载/预览未携带 token → 401"""
        resp = _get(path)
        assert resp.status_code == 401, resp.text

    def test_forged_token_rejected(self):
        """伪造 token → 401"""
        resp = _post("/admin/attachment/get-attachment-list", token="forged.invalid.token")
        assert resp.status_code == 401, resp.text

    @pytest.mark.parametrize("path,perm", GUARDED_POST_ENDPOINTS)
    def test_post_forbidden_for_non_admin(self, path, perm):
        """非管理员（无 attachment:* 权限）→ 403 且 detail 含权限码"""
        token = _token("deptuser", "123456")
        resp = _post(path, token=token)
        assert resp.status_code == 403, resp.text
        assert perm in resp.json().get("detail", ""), resp.text

    @pytest.mark.parametrize("path", GUARDED_GET_PATHS)
    def test_get_forbidden_for_non_admin(self, path):
        """非管理员访问下载/预览 → 403"""
        token = _token("deptuser", "123456")
        resp = _get(path, token=token)
        assert resp.status_code == 403, resp.text
        assert "attachment:download" in resp.json().get("detail", ""), resp.text

    def test_admin_can_list_attachments(self):
        """管理员有 attachment:list → 列表接口返回 200"""
        token = _token("admin", "admin123")
        resp = _post("/admin/attachment/get-attachment-list", token=token, payload={"page": 1, "limit": 10})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["code"] == 200, body
