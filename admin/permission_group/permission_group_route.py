"""权限组路由

管理类端点（权限组的配置与主体绑定）需要授权权限点；当前用户自助的
「查询我的权限组 / 切换激活组」仅依赖统一登录校验。
"""

from fastapi import APIRouter, Depends, Request

from framework.core.auth import require_permission
from .permission_group_controller import PermissionGroupController

router = APIRouter(prefix="/admin/permission-group", tags=["权限组"])

MANAGE_PERMISSION = "org:role:grant"


# ==================== 权限组主表 ====================

@router.post("/get-group-list", dependencies=[Depends(require_permission(MANAGE_PERMISSION))])
async def get_group_list(request: Request):
    """查询权限组列表

    Returns:
        分页的权限组列表
    """
    controller = PermissionGroupController(request)
    return await controller.get_group_list()


@router.post("/get-group-detail", dependencies=[Depends(require_permission(MANAGE_PERMISSION))])
async def get_group_detail(request: Request):
    """查询权限组详情

    Returns:
        权限组详情
    """
    controller = PermissionGroupController(request)
    return await controller.get_group_detail()


@router.post("/create-group", dependencies=[Depends(require_permission(MANAGE_PERMISSION))])
async def create_group(request: Request):
    """创建权限组

    Returns:
        新建权限组信息
    """
    controller = PermissionGroupController(request)
    return await controller.create_group()


@router.post("/update-group", dependencies=[Depends(require_permission(MANAGE_PERMISSION))])
async def update_group(request: Request):
    """更新权限组

    Returns:
        更新后的权限组详情
    """
    controller = PermissionGroupController(request)
    return await controller.update_group()


@router.post("/delete-group", dependencies=[Depends(require_permission(MANAGE_PERMISSION))])
async def delete_group(request: Request):
    """删除权限组

    Returns:
        删除结果
    """
    controller = PermissionGroupController(request)
    return await controller.delete_group()


# ==================== 组-操作权限点 ====================

@router.post("/get-group-permissions", dependencies=[Depends(require_permission(MANAGE_PERMISSION))])
async def get_group_permissions(request: Request):
    """查询权限组已授权的操作权限点

    Returns:
        权限点ID与权限码
    """
    controller = PermissionGroupController(request)
    return await controller.get_group_permissions()


@router.post("/grant-group-permissions", dependencies=[Depends(require_permission(MANAGE_PERMISSION))])
async def grant_group_permissions(request: Request):
    """覆盖式保存权限组的操作权限点

    Returns:
        保存后的权限点
    """
    controller = PermissionGroupController(request)
    return await controller.grant_group_permissions()


# ==================== 组-字段权限 ====================

@router.post("/get-field-catalog", dependencies=[Depends(require_permission(MANAGE_PERMISSION))])
async def get_field_catalog(request: Request):
    """查询模块可配置的字段目录

    Returns:
        字段目录
    """
    controller = PermissionGroupController(request)
    return await controller.get_field_catalog()


@router.post("/set-group-fields", dependencies=[Depends(require_permission(MANAGE_PERMISSION))])
async def set_group_fields(request: Request):
    """覆盖式保存权限组的字段权限

    Returns:
        保存后的字段权限列表
    """
    controller = PermissionGroupController(request)
    return await controller.set_group_fields()


# ==================== 组-数据权限 ====================

@router.post("/set-group-data-scope", dependencies=[Depends(require_permission(MANAGE_PERMISSION))])
async def set_group_data_scope(request: Request):
    """覆盖式保存权限组的数据权限范围

    Returns:
        保存后的数据权限配置
    """
    controller = PermissionGroupController(request)
    return await controller.set_group_data_scope()


# ==================== 组-主体绑定 ====================

@router.post("/bind-group-subjects", dependencies=[Depends(require_permission(MANAGE_PERMISSION))])
async def bind_group_subjects(request: Request):
    """覆盖式保存权限组的主体绑定

    Returns:
        保存后的主体绑定列表
    """
    controller = PermissionGroupController(request)
    return await controller.bind_group_subjects()


@router.post("/delete-group-subject", dependencies=[Depends(require_permission(MANAGE_PERMISSION))])
async def delete_group_subject(request: Request):
    """解绑权限组的单个主体

    Returns:
        解绑结果
    """
    controller = PermissionGroupController(request)
    return await controller.delete_group_subject()


@router.post("/get-bindable-subjects", dependencies=[Depends(require_permission(MANAGE_PERMISSION))])
async def get_bindable_subjects(request: Request):
    """查询可绑定的主体选项

    Returns:
        {depts, roles, users}
    """
    controller = PermissionGroupController(request)
    return await controller.get_bindable_subjects()


@router.post("/get-menu-options", dependencies=[Depends(require_permission(MANAGE_PERMISSION))])
async def get_menu_options(request: Request):
    """查询可归属的菜单选项

    Returns:
        菜单列表
    """
    controller = PermissionGroupController(request)
    return await controller.get_menu_options()


# ==================== 当前用户的权限组（自助） ====================

@router.post("/get-user-groups")
async def get_user_groups(request: Request):
    """查询当前用户可用的权限组

    Returns:
        {items, active_group_id}
    """
    controller = PermissionGroupController(request)
    return await controller.get_user_groups()


@router.post("/activate-user-group")
async def activate_user_group(request: Request):
    """切换当前用户激活的权限组（按组互斥）

    Returns:
        {active_group_id}
    """
    controller = PermissionGroupController(request)
    return await controller.activate_user_group()
