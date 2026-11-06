"""认证接口测试

覆盖登录成功、密码错误、空值校验、普通用户登录与伪造 token 拦截。
"""

import asyncio
import os

import httpx

# 后端服务基址（与既有测试保持一致，可通过 TEST_API_URL 覆盖）
BASE_URL = os.environ.get("TEST_API_URL", "http://localhost:8000")
# 测试数据统一前缀，便于识别与清理
TITLE_PREFIX = "pytest_collect_"


class TestAuthAPI:
    """认证API测试类"""

    def setup_method(self):
        """测试方法前置处理"""
        self.base_url = BASE_URL
        self.timeout = 30.0

    async def async_test_login_admin_success(self):
        """测试管理员正确密码登录 (POST)"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/admin/auth/login",
                json={"username": "admin", "password": "admin123"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert isinstance(data["data"], dict)
        assert data["data"]["token"]
        assert isinstance(data["data"]["token"], str)
        assert data["data"]["user"]["username"] == "admin"
        assert data["data"]["user"]["id"] == 1
        assert data["data"]["user"]["is_admin"] is True

    async def async_test_login_wrong_password(self):
        """测试错误密码登录返回401 (POST)"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/admin/auth/login",
                json={"username": "admin", "password": "wrong_password_123"},
            )
        assert response.status_code == 401
        data = response.json()
        assert data["code"] == 401

    async def async_test_login_empty_username(self):
        """测试空用户名登录返回400 (POST)"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/admin/auth/login",
                json={"username": "", "password": "admin123"},
            )
        assert response.status_code == 400
        assert response.json()["code"] == 400

    async def async_test_login_empty_password(self):
        """测试空密码登录返回400 (POST)"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/admin/auth/login",
                json={"username": "admin", "password": ""},
            )
        assert response.status_code == 400
        assert response.json()["code"] == 400

    async def async_test_login_normal_user(self):
        """测试普通用户登录（明文密码回退分支）(POST)"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/admin/auth/login",
                json={"username": "deptuser", "password": "123456"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["token"]
        assert data["data"]["user"]["username"] == "deptuser"
        assert data["data"]["user"]["id"] == 5
        assert data["data"]["user"]["is_admin"] is False

    async def async_test_forged_token_rejected(self):
        """测试伪造 token 访问受保护接口返回401 (POST)"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/admin/collectqueue/get-collect-list",
                json={"page": 1, "limit": 10, "keyword": TITLE_PREFIX},
                headers={"Authorization": "Bearer abc.def.ghi"},
            )
        assert response.status_code == 401

    # ==================== 测试入口 ====================

    def test_login_admin_success(self):
        """测试管理员正确密码登录"""
        asyncio.run(self.async_test_login_admin_success())

    def test_login_wrong_password(self):
        """测试错误密码登录返回401"""
        asyncio.run(self.async_test_login_wrong_password())

    def test_login_empty_username(self):
        """测试空用户名登录返回400"""
        asyncio.run(self.async_test_login_empty_username())

    def test_login_empty_password(self):
        """测试空密码登录返回400"""
        asyncio.run(self.async_test_login_empty_password())

    def test_login_normal_user(self):
        """测试普通用户登录"""
        asyncio.run(self.async_test_login_normal_user())

    def test_forged_token_rejected(self):
        """测试伪造 token 被拒绝"""
        asyncio.run(self.async_test_forged_token_rejected())
