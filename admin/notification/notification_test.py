import requests

# 测试基础URL
BASE_URL = "http://localhost:8000/admin/notification"
LOGIN_URL = "http://localhost:8000/admin/auth/login"

# 消息通知接口仅需登录（无 require_permission），故用管理员 token 覆盖正常路径
_TOKEN = None


def _auth_token() -> str:
    """登录取 token（进程内缓存）"""
    global _TOKEN
    if _TOKEN is None:
        resp = requests.post(LOGIN_URL, json={"username": "admin", "password": "admin123"}, timeout=30)
        resp.raise_for_status()
        _TOKEN = resp.json()["data"]["token"]
    return _TOKEN


def _post(path: str, payload=None) -> requests.Response:
    return requests.post(
        f"{BASE_URL}{path}",
        json=payload if payload is not None else {},
        headers={"Authorization": f"Bearer {_auth_token()}"},
        timeout=30,
    )


class TestNotificationAPI:
    """消息通知API测试类"""

    def test_requires_login(self):
        """未携带 token 返回 401"""
        resp = requests.post(f"{BASE_URL}/get-message-list", json={"type": "all"}, timeout=30)
        assert resp.status_code == 401, resp.text

    def test_get_message_list_all(self):
        """测试获取所有消息列表"""
        response = _post("/get-message-list", {"type": "all", "only_unread": False})
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "success"
        assert isinstance(data["data"], list)

    def test_get_message_list_system(self):
        """测试获取系统通知列表"""
        response = _post("/get-message-list", {"type": "system", "only_unread": False})
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "success"
        assert isinstance(data["data"], list)

    def test_get_message_list_download(self):
        """测试获取下载通知列表"""
        response = _post("/get-message-list", {"type": "download", "only_unread": False})
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "success"
        assert isinstance(data["data"], list)

    def test_get_message_list_warning(self):
        """测试获取异常提醒列表"""
        response = _post("/get-message-list", {"type": "warning", "only_unread": False})
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "success"
        assert isinstance(data["data"], list)

    def test_get_message_list_only_unread(self):
        """测试获取未读消息列表"""
        response = _post("/get-message-list", {"type": "all", "only_unread": True})
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "success"
        assert isinstance(data["data"], list)

    def test_mark_all_as_read(self):
        """测试标记所有消息为已读"""
        response = _post("/mark-all-as-read")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "success"
        assert data["data"]["success"] is True

    def test_mark_messages_as_read(self):
        """测试标记指定消息为已读"""
        # 先获取消息列表，获取一个消息ID
        response = _post("/get-message-list", {"type": "all", "only_unread": False})
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        if not data["data"]:
            return  # 无消息时无需标记，跳过

        # 获取第一个消息的ID
        message_id = data["data"][0]["id"]

        # 测试标记指定消息为已读
        response = _post("/mark-messages-as-read", {"message_ids": [message_id]})
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "success"
        assert data["data"]["success"] is True

    def test_mark_messages_as_read_empty(self):
        """测试标记已读时消息ID为空"""
        response = _post("/mark-messages-as-read", {"message_ids": []})
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 400
        assert data["message"] == "message_ids is required"
        assert data["data"]["success"] is False
