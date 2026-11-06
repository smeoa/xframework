"""个人设置控制器模块

负责个人资料（x_user）、登录记录（x_user_login）与 API 密钥（x_user_api_key）相关接口。

API 密钥属个人凭证，鉴权与数据隔离规则为严格本人隔离：
所有用户（含管理员）仅可查询与操作本人数据，服务端强制以当前登录用户作为归属条件。
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import HTTPException

from framework.core.auth import get_current_user
from framework.core.controller import Controller

from admin.profile.profile_model import ProfileModel

logger = logging.getLogger(__name__)


class ProfileController(Controller):
    """个人设置控制器"""

    # 兼容 data 包裹与直接传参时用于识别业务参数的字段名
    BUSINESS_KEYS = ("id", "name", "description", "expire_time", "expireTime", "status")

    def __init__(self, request):
        super().__init__(request)
        self.profile_model = ProfileModel()

    # ==================== 通用工具 ====================

    def _unwrap(self, data: Any) -> Dict[str, Any]:
        """兼容前端以 data 包裹请求体与直接传参两种形式

        Args:
            data: 原始请求体

        Returns:
            业务参数字典
        """
        if not isinstance(data, dict):
            return {}
        inner = data.get("data")
        if isinstance(inner, dict) and not any(key in data for key in self.BUSINESS_KEYS):
            return inner
        return data

    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """把字符串 / datetime / 时间戳解析为 naive 本地时间

        数据库列为 timestamp without time zone，带时区的输入统一换算为本地时间后去掉时区。

        Args:
            value: 原始值

        Returns:
            datetime 或 None（无法解析时）
        """
        if value is None:
            return None
        if isinstance(value, datetime):
            return self._to_naive(value)

        text = str(value).strip()
        if not text:
            return None

        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue

        try:
            return self._to_naive(datetime.fromisoformat(text.replace("Z", "+00:00")))
        except ValueError:
            return None

    def _to_naive(self, value: datetime) -> datetime:
        """把带时区的 datetime 转成 naive 本地时间

        Args:
            value: datetime

        Returns:
            naive datetime
        """
        if value.tzinfo is None:
            return value
        return value.astimezone().replace(tzinfo=None)

    async def _get_owned_key(self, payload: Dict[str, Any]):
        """校验密钥 ID、存在性与归属

        Args:
            payload: 业务参数字典

        Returns:
            (error_response, key_id, owner_user_id)：校验通过时 error_response 为 None
        """
        current_user = await get_current_user(self.request)

        key_id = payload.get("id")
        if key_id is None or str(key_id).strip() == "":
            return self.error(400, "ID不能为空"), None, None
        try:
            key_id = int(key_id)
        except (TypeError, ValueError):
            return self.error(400, "ID格式不正确"), None, None

        record = await self.profile_model.get_api_key_owner(key_id)
        if not record:
            return self.error(404, "记录不存在"), None, None

        if record["user_id"] != current_user["id"]:
            return self.error(403, "无权访问该记录"), None, None

        return None, key_id, record["user_id"]

    # ==================== 个人资料 ====================

    async def get_profile(self):
        """获取个人资料"""
        return await self.profile_model.get_profile()

    async def update_profile(self):
        """更新个人资料"""
        data = await self._get_request_data()
        return await self.profile_model.update_profile(data.get("data", {}))

    async def change_password(self):
        """修改密码"""
        data = await self._get_request_data()
        return await self.profile_model.change_password(data.get("data", {}))

    async def get_login_logs(self):
        """获取登录记录（支持筛选 / 排序）"""
        data = await self._get_request_data()
        page = data.get("page", 1)
        limit = data.get("limit", 10)
        filter_conditions = data.get("filter", [])
        sort_rules = data.get("sort", [])
        return await self.profile_model.get_login_logs(page, limit, filter_conditions, sort_rules)

    async def get_notification_settings(self):
        """获取通知设置"""
        return await self.profile_model.get_notification_settings()

    async def update_notification_settings(self):
        """获取通知设置"""
        data = await self._get_request_data()
        return await self.profile_model.update_notification_settings(data.get("data", {}))

    async def get_interface_settings(self):
        """获取界面设置"""
        return await self.profile_model.get_interface_settings()

    async def update_interface_settings(self):
        """获取界面设置"""
        data = await self._get_request_data()
        return await self.profile_model.update_interface_settings(data.get("data", {}))

    # ==================== API 密钥 ====================

    async def get_api_keys(self):
        """获取当前登录用户的 API 密钥列表

        未登录返回 401，仅返回本人数据。

        Returns:
            密钥列表响应
        """
        try:
            current_user = await get_current_user(self.request)
            result = await self.profile_model.get_api_keys(current_user["id"])
            return self.success(result.get("data"))
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取API密钥列表失败: {str(e)}", exc_info=True)
            return self.error(message=str(e))

    async def create_api_key(self):
        """创建 API 密钥

        强制归属当前登录用户；名称必填且不超过 255 字符；
        过期时间可空，填写时须为合法时间且晚于当前时间。

        Returns:
            创建结果响应（含完整密钥）
        """
        try:
            current_user = await get_current_user(self.request)
            data = await self._get_request_data()
            payload = self._unwrap(data)

            name = str(payload.get("name") or "").strip()
            if not name:
                return self.error(400, "密钥名称不能为空")
            if len(name) > 255:
                return self.error(400, "密钥名称长度不能超过255个字符")

            description = payload.get("description")
            if description is not None:
                description = str(description).strip() or None

            expire_time = self._parse_datetime(payload.get("expire_time"))
            if expire_time is None:
                return self.error(400, "过期时间不能为空或格式不正确")
            if expire_time <= datetime.now():
                return self.error(400, "过期时间必须晚于当前时间")

            result = await self.profile_model.create_api_key(current_user["id"], name, description, expire_time)
            if result.get("code") != 200:
                return self.error(result.get("code", 400), result.get("message", "创建失败"))
            return self.success(result.get("data"), "创建成功")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"创建API密钥失败: {str(e)}", exc_info=True)
            return self.error(message=str(e))

    async def toggle_api_key_status(self):
        """切换 API 密钥状态

        仅可操作本人密钥；记录不存在返回 404，越权返回 403。

        Returns:
            更新结果响应
        """
        try:
            data = await self._get_request_data()
            payload = self._unwrap(data)

            error_response, key_id, owner_user_id = await self._get_owned_key(payload)
            if error_response is not None:
                return error_response

            status = payload.get("status")
            if isinstance(status, bool):
                return self.error(400, "状态值不合法，仅支持 0 或 1")
            try:
                status = int(status)
            except (TypeError, ValueError):
                return self.error(400, "状态值不合法，仅支持 0 或 1")
            if status not in (0, 1):
                return self.error(400, "状态值不合法，仅支持 0 或 1")

            result = await self.profile_model.toggle_api_key_status(owner_user_id, key_id, status)
            if result.get("code") != 200:
                return self.error(result.get("code", 400), result.get("message", "状态切换失败"))
            return self.success(None, "状态切换成功")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"切换API密钥状态失败: {str(e)}", exc_info=True)
            return self.error(message=str(e))

    async def delete_api_key(self):
        """删除 API 密钥

        仅可删除本人密钥；记录不存在返回 404，越权返回 403。

        Returns:
            删除结果响应
        """
        try:
            data = await self._get_request_data()
            payload = self._unwrap(data)

            error_response, key_id, owner_user_id = await self._get_owned_key(payload)
            if error_response is not None:
                return error_response

            result = await self.profile_model.delete_api_key(owner_user_id, key_id)
            if result.get("code") != 200:
                return self.error(result.get("code", 400), result.get("message", "删除失败"))
            return self.success(None, "删除成功")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"删除API密钥失败: {str(e)}", exc_info=True)
            return self.error(message=str(e))
