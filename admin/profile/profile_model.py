# -*- coding: utf-8 -*-
"""
个人资料模型
@file: profile_model.py
@author: xai-admin
@describe: 个人资料数据访问层
"""

import secrets
from typing import Dict, List, Optional, Tuple, Any
from framework.core.db import db
from framework.core.model import Model

# 登录记录（x_user_login）查询相关常量
# 登录记录归属固定为 1（与个人资料 / 修改密码保持一致的口径）
LOGIN_LOG_USER_ID = 1
# 可筛选 / 可排序的列白名单：前端只产出字符串，白名单外的列不允许拼入 SQL
LOGIN_LOG_FIELDS = ("id", "ip", "user_agent", "login_time", "status")
LOGIN_LOG_SELECT_FIELDS = "id, ip, user_agent, login_time, status"
DEFAULT_LOGIN_LOG_SORT = [{"field": "login_time", "direction": "desc"}]


class LoginLogModel(Model):
    """登录记录模型（表 x_user_login），负责筛选 / 排序 / 分页查询"""

    def __init__(self) -> None:
        """初始化模型"""
        super().__init__("user_login")
        # 列名 → 数据库类型（按列类型转换取值），实例级缓存
        self._column_types: Optional[Dict[str, str]] = None

    async def get_column_types(self) -> Dict[str, str]:
        """表列名 → information_schema.data_type 映射（按模型实例缓存）"""
        if self._column_types is None:
            self._column_types = await self.db.get_table_column_types(self.table_name)
        return self._column_types

    def _sanitize_filter(self, filter_conditions: Any) -> List[Dict[str, Any]]:
        """归一筛选条件：仅保留白名单列的条件，避免任意列名拼入 SQL

        Args:
            filter_conditions: 前端传入的条件组数组

        Returns:
            归一后的条件组数组（字段已限定在 LOGIN_LOG_FIELDS 内）
        """
        if not isinstance(filter_conditions, list):
            return []

        cleaned: List[Dict[str, Any]] = []
        for group in filter_conditions:
            if not isinstance(group, dict):
                continue
            conditions = [
                {
                    "field": cond.get("field"),
                    "operator": cond.get("operator") or "eq",
                    "value": cond.get("value"),
                }
                for cond in (group.get("conditions") or [])
                if isinstance(cond, dict) and cond.get("field") in LOGIN_LOG_FIELDS
            ]
            if not conditions:
                continue
            cleaned.append(
                {
                    "group_logic": group.get("group_logic", group.get("groupLogic", "and")),
                    "condition_logic": group.get(
                        "condition_logic", group.get("conditionLogic", "and")
                    ),
                    "conditions": conditions,
                }
            )
        return cleaned

    async def get_login_logs(
        self,
        page: int = 1,
        limit: int = 10,
        filter_conditions: Optional[List[Dict[str, Any]]] = None,
        sort_rules: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """分页查询登录记录（支持筛选与排序）

        Args:
            page: 页码
            limit: 每页条数
            filter_conditions: 前端筛选条件（字段限定在白名单内）
            sort_rules: 排序规则，缺省按登录时间倒序

        Returns:
            含 items 与 total 的字典
        """
        column_types = await self.get_column_types()

        # 数据隔离条件由服务端固定拼装，不参与前端条件的白名单过滤
        groups: List[Dict[str, Any]] = [
            {
                "group_logic": "and",
                "condition_logic": "and",
                "conditions": [
                    {"field": "user_id", "operator": "eq", "value": LOGIN_LOG_USER_ID}
                ],
            }
        ]
        cleaned = self._sanitize_filter(filter_conditions)
        # 按真实列类型把字符串取值转为 asyncpg 可绑定类型（如 login_time 为 timestamp）
        for group in cleaned:
            for condition in group["conditions"]:
                column_type = column_types.get(condition["field"])
                if not column_type:
                    continue
                value = condition["value"]
                if isinstance(value, list):
                    condition["value"] = [
                        self._coerce_column_value(item, column_type) for item in value
                    ]
                else:
                    condition["value"] = self._coerce_column_value(value, column_type)
        groups.extend(cleaned)

        safe_sort = [
            {"field": rule.get("field"), "direction": rule.get("direction") or "asc"}
            for rule in (sort_rules or [])
            if isinstance(rule, dict) and rule.get("field") in LOGIN_LOG_FIELDS
        ]
        if not safe_sort:
            safe_sort = DEFAULT_LOGIN_LOG_SORT

        result = await self.get_list(
            filter=groups,
            page=page,
            limit=limit,
            sort_rules=safe_sort,
            fields=LOGIN_LOG_SELECT_FIELDS,
        )
        if isinstance(result, dict):
            return result
        return {"items": result, "total": len(result) if isinstance(result, list) else 0}


class ProfileModel:
    """个人资料数据访问模型"""

    @staticmethod
    async def get_profile():
        """获取个人资料

        Returns:
            个人资料信息
        """
        sql = """
        SELECT id, username, name, email, phone, avatar, create_time, update_time 
        FROM x_user 
        WHERE id = 1
        """
        result = await db.fetch_one(sql)
        return {"code": 200, "message": "success", "data": result}

    @staticmethod
    async def update_profile(data: Dict):
        """更新个人资料

        Args:
            data: 更新数据

        Returns:
            更新结果
        """
        user_id = data.get("id", 1)
        updates = []
        values = []
        for key, value in data.items():
            if key != "id":
                updates.append(f"{key} = ${len(values) + 1}")
                values.append(value)
        if not updates:
            return {"code": 400, "message": "没有需要更新的字段"}

        sql = f"UPDATE x_user SET {', '.join(updates)} WHERE id = ${len(values) + 1}"
        values.append(user_id)
        await db.execute(sql, values)
        return {"code": 200, "message": "更新成功"}

    @staticmethod
    async def change_password(data: Dict):
        """修改密码

        Args:
            data: 数据包含 old_password 和 new_password

        Returns:
            修改结果
        """
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        old_password = data.get("old_password", "")
        new_password = data.get("new_password", "")

        sql = "SELECT password FROM x_user WHERE id = 1"
        result = await db.fetch_one(sql)
        if not result:
            return {"code": 404, "message": "用户不存在"}

        if not pwd_context.verify(old_password, result["password"]):
            return {"code": 400, "message": "原密码错误"}

        hashed_password = pwd_context.hash(new_password)
        sql = "UPDATE x_user SET password = $1 WHERE id = $2"
        await db.execute(sql, [hashed_password, 1])
        return {"code": 200, "message": "密码修改成功"}

    @staticmethod
    async def get_login_logs(
        page: int = 1,
        limit: int = 10,
        filter_conditions: Optional[List[Dict[str, Any]]] = None,
        sort_rules: Optional[List[Dict[str, Any]]] = None,
    ):
        """获取登录记录（支持筛选与排序）

        Args:
            page: 页码
            limit: 每页条数
            filter_conditions: 前端筛选条件
            sort_rules: 排序规则

        Returns:
            登录记录列表
        """
        result = await LoginLogModel().get_login_logs(
            page=page,
            limit=limit,
            filter_conditions=filter_conditions,
            sort_rules=sort_rules,
        )
        return {
            "code": 200,
            "message": "success",
            "data": {
                "items": result.get("items", []),
                "total": result.get("total", 0),
            },
        }

    @staticmethod
    async def get_notification_settings():
        """获取通知设置

        Returns:
            通知设置
        """
        # 这里返回默认设置
        return {
            "code": 200,
            "message": "success",
            "data": {
                "email": True,
                "sms": False,
                "push": True
            }
        }

    @staticmethod
    async def update_notification_settings(data: Dict):  # pylint: disable=unused-argument
        """更新通知设置

        Args:
            data: 通知设置数据

        Returns:
            更新结果
        """
        return {"code": 200, "message": "更新成功"}

    @staticmethod
    async def get_interface_settings():
        """获取界面设置

        Returns:
            界面设置
        """
        # 这里返回默认设置
        return {
            "code": 200,
            "message": "success",
            "data": {
                "theme": "light",
                "menu_collapsed": False
            }
        }

    @staticmethod
    async def update_interface_settings(data: Dict):  # pylint: disable=unused-argument
        """更新界面设置

        Args:
            data: 界面设置数据

        Returns:
            更新结果
        """
        return {"code": 200, "message": "更新成功"}

    @staticmethod
    async def get_api_keys(user_id: int):
        """获取指定用户的 API 密钥列表

        Args:
            user_id: 当前登录用户ID

        Returns:
            API密钥列表
        """
        sql = """
        SELECT id, name, key, status, description, create_time, expire_time
        FROM x_user_api_key
        WHERE user_id = $1
        ORDER BY create_time DESC, id DESC
        """
        result = await db.fetch_all(sql, [user_id])
        return {"code": 200, "message": "success", "data": result}

    @staticmethod
    async def get_api_key_owner(key_id: int) -> Optional[Dict]:
        """查询 API 密钥归属，用于越权判定

        Args:
            key_id: 密钥ID

        Returns:
            含 id / user_id 的行，不存在返回 None
        """
        sql = "SELECT id, user_id FROM x_user_api_key WHERE id = $1"
        return await db.fetch_one(sql, [key_id])

    @staticmethod
    async def create_api_key(user_id: int, name: str, description: Optional[str], expire_time):
        """创建 API 密钥

        Args:
            user_id: 当前登录用户ID
            name: 密钥名称
            description: 密钥描述
            expire_time: 过期时间（datetime 或 None）

        Returns:
            创建结果（含完整密钥）
        """
        api_key = secrets.token_urlsafe(32)
        sql = """
        INSERT INTO x_user_api_key (user_id, name, key, status, description, expire_time, create_time)
        VALUES ($1, $2, $3, 1, $4, $5, NOW())
        RETURNING id, name, key, status, description, create_time, expire_time
        """
        result = await db.fetch_one(sql, [user_id, name, api_key, description, expire_time])
        return {"code": 200, "message": "创建成功", "data": result}

    @staticmethod
    async def toggle_api_key_status(user_id: int, key_id: int, status: int):
        """按归属更新 API 密钥状态

        Args:
            user_id: 当前登录用户ID
            key_id: 密钥ID
            status: 状态（1 启用 / 0 禁用）

        Returns:
            更新结果
        """
        sql = """
        UPDATE x_user_api_key SET status = $1, updated_at = NOW()
        WHERE id = $2 AND user_id = $3
        RETURNING id
        """
        await db.fetch_one(sql, [status, key_id, user_id])
        return {"code": 200, "message": "状态切换成功"}

    @staticmethod
    async def delete_api_key(user_id: int, key_id: int):
        """按归属删除 API 密钥

        Args:
            user_id: 当前登录用户ID
            key_id: 密钥ID

        Returns:
            删除结果
        """
        sql = "DELETE FROM x_user_api_key WHERE id = $1 AND user_id = $2 RETURNING id"
        await db.fetch_one(sql, [key_id, user_id])
        return {"code": 200, "message": "删除成功"}
