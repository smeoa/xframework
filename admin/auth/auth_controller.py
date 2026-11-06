from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt
from fastapi import Request

from framework.core.auth import get_current_user, get_user_context
from framework.core.controller import Controller

from .auth_model import AuthModel


class AuthController(Controller):
    """认证控制器"""

    def __init__(self, request: Request):
        """初始化控制器

        Args:
            request: 请求对象
        """
        super().__init__(request)
        self.model = AuthModel()

    async def login(self) -> Any:
        """用户登录

        Returns:
            登录结果响应（token 与用户信息）
        """
        data: Dict[str, Any] = await self._get_request_data()
        username: str = str(data.get("username") or "").strip()
        password: str = str(data.get("password") or "")

        if not username or not password:
            return self.error(400, "用户名和密码不能为空")

        user = await self.model.get_user_by_username(username)
        if not user or not self.model.verify_password(password, str(user.get("password") or "")):
            return self.error(401, "用户名或密码错误")

        user_id: int = user["id"]
        expire_minutes: int = int(self.config.get("JWT_EXPIRE_MINUTES", 1440))
        payload: Dict[str, Any] = {
            "user_id": user_id,
            "username": user["username"],
            "exp": datetime.now(timezone.utc) + timedelta(minutes=expire_minutes),
        }
        token: str = jwt.encode(payload, self.config.get("JWT_SECRET"), algorithm="HS256")

        await self.model.update_last_login(user_id)

        context: Dict[str, Any] = await get_user_context(user_id, str(user["username"]))

        return self.success(
            {
                "token": token,
                "user": {**context, "name": user.get("name")},
            },
            "登录成功",
        )

    async def get_user_info(self) -> Any:
        """查询当前登录用户的权限上下文（用于切换权限组后刷新登录态）

        Returns:
            当前用户权限上下文（含权限码 / 字段权限 / 数据权限 / 激活权限组）
        """
        current_user: Dict[str, Any] = await get_current_user(self.request)
        return self.success(current_user, "查询成功")
