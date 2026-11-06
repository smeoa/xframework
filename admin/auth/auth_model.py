from datetime import datetime
from typing import Any, Dict, Optional

import bcrypt

from framework.core.model import Model
from framework.core.auth import is_admin

__all__ = ["AuthModel", "is_admin"]


class AuthModel(Model):
    """认证模型

    负责用户查询与密码校验，管理员判定复用 framework.core.auth.is_admin。
    """

    def __init__(self):
        """初始化模型"""
        super().__init__("user")

    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名查询可登录用户

        Args:
            username: 用户名

        Returns:
            用户记录（含 id/username/name/password）或 None
        """
        filter = [
            {
                "group_logic": "and",
                "condition_logic": "and",
                "conditions": [
                    {"field": "username", "operator": "eq", "value": username},
                    {"field": "is_deleted", "operator": "eq", "value": 0},
                    {"field": "status", "operator": "eq", "value": 1},
                ],
            }
        ]
        return await self.get_first(filter=filter, fields="*")

    def verify_password(self, plain: str, stored: str) -> bool:
        """校验密码

        bcrypt 哈希（以 $2 开头）使用 bcrypt 校验，其余按明文比对（兼容历史数据）。

        Args:
            plain: 用户输入的明文密码
            stored: 数据库中存储的密码

        Returns:
            校验是否通过
        """
        if not plain or not stored:
            return False

        if stored.startswith("$2"):
            try:
                return bcrypt.checkpw(plain.encode("utf-8"), stored.encode("utf-8"))
            except Exception:
                return False

        return plain == stored

    async def update_last_login(self, user_id: int) -> int:
        """更新最后登录时间

        Args:
            user_id: 用户ID

        Returns:
            更新的记录数
        """
        return await self.update_by_id(user_id, {"last_login_time": datetime.now()})
