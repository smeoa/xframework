"""权限组控制器

对外提供权限组的增删改查、操作权限点 / 字段权限 / 数据权限配置、
主体（部门 / 角色 / 人员）绑定，以及当前用户的可用权限组查询与激活切换。
"""

import logging
from typing import Any, Dict, List

from fastapi import Request

from framework.core.auth import get_current_user
from framework.core.controller import Controller
from .permission_group_model import PermissionGroupModel

logger = logging.getLogger(__name__)


class PermissionGroupController(Controller):
    def __init__(self, request: Request):
        super().__init__(request)
        self.model = PermissionGroupModel()

    async def _operator_id(self) -> int:
        """获取当前操作人用户ID（用于自动写入 create_by / update_by）

        Returns:
            当前登录用户ID，未取到时为 0
        """
        current_user = await get_current_user(self.request)
        return int(current_user.get("id") or 0)

    # ==================== 权限组主表 ====================

    async def get_group_list(self):
        """查询权限组列表

        Returns:
            分页的权限组列表
        """
        try:
            data = (await self.request.json()).get("data", {})
            result = await self.model.get_group_list(data)
            return self.success(result)
        except Exception as e:
            logger.error(f"查询权限组列表失败: {str(e)}")
            return self.error(message=str(e))

    async def get_group_detail(self):
        """查询权限组详情

        Returns:
            权限组详情（含权限点 / 字段 / 数据 / 主体绑定）
        """
        try:
            data = (await self.request.json()).get("data", {})
            group_id = data.get("id") or data.get("group_id")
            if not group_id:
                return self.error(message="权限组ID不能为空")
            result = await self.model.get_group_detail(group_id)
            return self.success(result)
        except Exception as e:
            logger.error(f"查询权限组详情失败: {str(e)}")
            return self.error(message=str(e))

    async def create_group(self):
        """创建权限组

        Returns:
            新建权限组信息
        """
        try:
            data = (await self.request.json()).get("data", {})
            if not data:
                return self.error(message="创建数据不能为空")
            result = await self.model.create_group(data, await self._operator_id())
            return self.success(result)
        except Exception as e:
            logger.error(f"创建权限组失败: {str(e)}")
            return self.error(message=str(e))

    async def update_group(self):
        """更新权限组

        Returns:
            更新后的权限组详情
        """
        try:
            data = (await self.request.json()).get("data", {})
            group_id = data.get("id") or data.get("group_id")
            if not group_id:
                return self.error(message="权限组ID不能为空")
            result = await self.model.update_group(group_id, data, await self._operator_id())
            return self.success(result)
        except Exception as e:
            logger.error(f"更新权限组失败: {str(e)}")
            return self.error(message=str(e))

    async def delete_group(self):
        """删除权限组

        Returns:
            删除结果
        """
        try:
            data = (await self.request.json()).get("data", {})
            group_id = data.get("id") or data.get("group_id")
            if not group_id:
                return self.error(message="权限组ID不能为空")
            await self.model.delete_group(group_id)
            return self.success(None, "删除成功")
        except Exception as e:
            logger.error(f"删除权限组失败: {str(e)}")
            return self.error(message=str(e))

    # ==================== 组-操作权限点 ====================

    async def get_group_permissions(self):
        """查询权限组已授权的操作权限点

        Returns:
            权限点ID与权限码
        """
        try:
            data = (await self.request.json()).get("data", {})
            group_id = data.get("id") or data.get("group_id")
            if not group_id:
                return self.error(message="权限组ID不能为空")
            result = await self.model.get_group_permissions(group_id)
            return self.success(result)
        except Exception as e:
            logger.error(f"查询权限组权限点失败: {str(e)}")
            return self.error(message=str(e))

    async def grant_group_permissions(self):
        """覆盖式保存权限组的操作权限点

        Returns:
            保存后的权限点
        """
        try:
            data = (await self.request.json()).get("data", {})
            group_id = data.get("id") or data.get("group_id")
            if not group_id:
                return self.error(message="权限组ID不能为空")
            permission_ids: List[Any] = data.get("permission_ids", [])
            result = await self.model.grant_group_permissions(
                group_id, permission_ids, await self._operator_id()
            )
            return self.success(result, "授权成功")
        except Exception as e:
            logger.error(f"授权权限组失败: {str(e)}")
            return self.error(message=str(e))

    # ==================== 组-字段权限 ====================

    async def get_field_catalog(self):
        """查询模块可配置的字段目录

        Returns:
            字段目录（字段名 + 中文名）
        """
        try:
            data = (await self.request.json()).get("data", {})
            module = data.get("module")
            if not module:
                return self.error(message="业务模块不能为空")
            result = await self.model.get_field_catalog(module)
            return self.success(result)
        except Exception as e:
            logger.error(f"查询字段目录失败: {str(e)}")
            return self.error(message=str(e))

    async def set_group_fields(self):
        """覆盖式保存权限组的字段权限

        Returns:
            保存后的字段权限列表
        """
        try:
            data = (await self.request.json()).get("data", {})
            group_id = data.get("id") or data.get("group_id")
            if not group_id:
                return self.error(message="权限组ID不能为空")
            result = await self.model.set_group_fields(
                group_id, data.get("module"), data.get("fields", []), await self._operator_id()
            )
            return self.success(result, "保存成功")
        except Exception as e:
            logger.error(f"保存字段权限失败: {str(e)}")
            return self.error(message=str(e))

    # ==================== 组-数据权限 ====================

    async def set_group_data_scope(self):
        """覆盖式保存权限组的数据权限范围

        Returns:
            保存后的数据权限配置
        """
        try:
            data = (await self.request.json()).get("data", {})
            group_id = data.get("id") or data.get("group_id")
            if not group_id:
                return self.error(message="权限组ID不能为空")
            result = await self.model.set_group_data_scope(
                group_id,
                data.get("module"),
                data.get("scope"),
                data.get("custom_dept_ids", []),
                await self._operator_id(),
            )
            return self.success(result, "保存成功")
        except Exception as e:
            logger.error(f"保存数据权限失败: {str(e)}")
            return self.error(message=str(e))

    # ==================== 组-主体绑定 ====================

    async def bind_group_subjects(self):
        """覆盖式保存权限组的主体绑定

        Returns:
            保存后的主体绑定列表
        """
        try:
            data = (await self.request.json()).get("data", {})
            group_id = data.get("id") or data.get("group_id")
            if not group_id:
                return self.error(message="权限组ID不能为空")
            result = await self.model.bind_group_subjects(
                group_id, data.get("subjects", []), await self._operator_id()
            )
            return self.success(result, "绑定成功")
        except Exception as e:
            logger.error(f"绑定权限组主体失败: {str(e)}")
            return self.error(message=str(e))

    async def delete_group_subject(self):
        """解绑权限组的单个主体

        Returns:
            解绑结果
        """
        try:
            data = (await self.request.json()).get("data", {})
            group_id = data.get("id") or data.get("group_id")
            if not group_id:
                return self.error(message="权限组ID不能为空")
            await self.model.delete_group_subject(
                group_id, data.get("subject_type"), data.get("subject_id")
            )
            return self.success(None, "解绑成功")
        except Exception as e:
            logger.error(f"解绑权限组主体失败: {str(e)}")
            return self.error(message=str(e))

    async def get_bindable_subjects(self):
        """查询可绑定的主体选项

        Returns:
            {depts, roles, users}
        """
        try:
            result = await self.model.get_bindable_subjects()
            return self.success(result)
        except Exception as e:
            logger.error(f"查询可绑定主体失败: {str(e)}")
            return self.error(message=str(e))

    async def get_menu_options(self):
        """查询可归属的菜单选项

        Returns:
            菜单列表（含业务模块）
        """
        try:
            result = await self.model.get_menu_options()
            return self.success(result)
        except Exception as e:
            logger.error(f"查询菜单选项失败: {str(e)}")
            return self.error(message=str(e))

    # ==================== 当前用户的权限组 ====================

    async def get_user_groups(self):
        """查询当前用户可用的权限组

        Returns:
            {items, active_group_id}
        """
        try:
            current_user = await get_current_user(self.request)
            result = await self.model.get_user_groups(current_user)
            return self.success(result)
        except Exception as e:
            logger.error(f"查询当前用户权限组失败: {str(e)}")
            return self.error(message=str(e))

    async def activate_user_group(self):
        """切换当前用户激活的权限组（按组互斥）

        Returns:
            {active_group_id}
        """
        try:
            data = (await self.request.json()).get("data", {})
            current_user = await get_current_user(self.request)
            group_id = data.get("group_id") or data.get("id")
            result = await self.model.activate_user_group(current_user, group_id)
            return self.success(result, "切换成功")
        except Exception as e:
            logger.error(f"切换权限组失败: {str(e)}")
            return self.error(message=str(e))
