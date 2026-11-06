from fastapi import APIRouter, BackgroundTasks, Depends, Request
from framework.core.auth import require_permission
from .organization_controller import OrganizationController

router = APIRouter(prefix="/admin/organization", tags=["组织管理"])


# 部门相关路由
@router.post("/get-dept-tree", dependencies=[Depends(require_permission("org:dept:list"))])
async def get_dept_tree(request: Request):
    """获取部门树形结构

    Returns:
        部门树形结构
    """
    controller = OrganizationController(request)
    return await controller.get_dept_tree()


@router.post("/create-dept", dependencies=[Depends(require_permission("org:dept:create"))])
async def create_dept(request: Request):
    """创建部门

    Returns:
        创建结果
    """
    controller = OrganizationController(request)
    return await controller.create_dept()


@router.post("/update-dept", dependencies=[Depends(require_permission("org:dept:update"))])
async def update_dept(request: Request):
    """更新部门

    Returns:
        更新结果
    """
    controller = OrganizationController(request)
    return await controller.update_dept()


@router.post("/delete-dept", dependencies=[Depends(require_permission("org:dept:delete"))])
async def delete_dept(request: Request):
    """删除部门

    Returns:
        删除结果
    """
    controller = OrganizationController(request)
    return await controller.delete_dept()


@router.post("/get-dept", dependencies=[Depends(require_permission("org:dept:list"))])
async def get_dept(request: Request):
    """获取单个部门

    Returns:
        部门信息
    """
    controller = OrganizationController(request)
    return await controller.get_dept()


# 用户相关路由
@router.post("/get-user-list", dependencies=[Depends(require_permission("org:user:list"))])
async def get_user_list(request: Request):
    """获取用户列表

    Returns:
        用户列表
    """
    controller = OrganizationController(request)
    return await controller.get_user_list()


@router.post("/create-user", dependencies=[Depends(require_permission("org:user:create"))])
async def create_user(request: Request):
    """创建用户

    Returns:
        创建结果
    """
    controller = OrganizationController(request)
    return await controller.create_user()


@router.post("/update-user", dependencies=[Depends(require_permission("org:user:update"))])
async def update_user(request: Request):
    """更新用户

    Returns:
        更新结果
    """
    controller = OrganizationController(request)
    return await controller.update_user()


@router.post("/delete-user", dependencies=[Depends(require_permission("org:user:delete"))])
async def delete_user(request: Request):
    """删除用户

    Returns:
        删除结果
    """
    controller = OrganizationController(request)
    return await controller.delete_user()


@router.post("/destroy-user", dependencies=[Depends(require_permission("org:user:delete"))])
async def destroy_user(request: Request):
    """物理删除用户

    Returns:
        删除结果
    """
    controller = OrganizationController(request)
    return await controller.destroy_user()


@router.post("/get-user", dependencies=[Depends(require_permission("org:user:list"))])
async def get_user(request: Request):
    """获取单个用户

    Returns:
        用户信息
    """
    controller = OrganizationController(request)
    return await controller.get_user()


@router.post("/import-users", dependencies=[Depends(require_permission("org:user:import"))])
async def import_users(request: Request):
    """导入用户

    Returns:
        导入结果
    """
    controller = OrganizationController(request)
    return await controller.import_users()


@router.post("/export-users", dependencies=[Depends(require_permission("org:user:export"))])
async def export_users(request: Request, background_tasks: BackgroundTasks):
    """导出用户

    Returns:
        导出结果
    """
    controller = OrganizationController(request)
    return await controller.export_users(background_tasks)


@router.post("/export-users-selected", dependencies=[Depends(require_permission("org:user:export"))])
async def export_users_selected(request: Request, background_tasks: BackgroundTasks):
    """导出选中用户

    Returns:
        导出结果
    """
    controller = OrganizationController(request)
    return await controller.export_users_selected(background_tasks)


@router.post("/delete-users-batch", dependencies=[Depends(require_permission("org:user:delete"))])
async def delete_users_batch(request: Request):
    """批量删除所有符合条件的用户

    Returns:
        删除结果
    """
    controller = OrganizationController(request)
    return await controller.delete_users_batch()


@router.post("/delete-users-selected", dependencies=[Depends(require_permission("org:user:delete"))])
async def delete_users_selected(request: Request):
    """批量删除选中的用户

    Returns:
        删除结果
    """
    controller = OrganizationController(request)
    return await controller.delete_users_selected()


@router.post("/update-users-batch", dependencies=[Depends(require_permission("org:user:update"))])
async def update_users_batch(request: Request):
    """批量修改用户状态

    Returns:
        更新结果
    """
    controller = OrganizationController(request)
    return await controller.update_users_batch()


# 角色相关路由
@router.post("/get-role-tree", dependencies=[Depends(require_permission("org:role:list"))])
async def get_role_tree(request: Request):
    """获取角色树

    Returns:
        角色树
    """
    controller = OrganizationController(request)
    return await controller.get_role_tree()


@router.post("/get-members", dependencies=[Depends(require_permission("org:role:list"))])
async def get_members(request: Request):
    """获取角色成员

    Returns:
        角色成员
    """
    controller = OrganizationController(request)
    return await controller.get_members()


@router.post("/get-available-users", dependencies=[Depends(require_permission("org:role:list"))])
async def get_available_users(request: Request):
    """获取可用用户

    Returns:
        可用用户
    """
    controller = OrganizationController(request)
    return await controller.get_available_users()


@router.post("/add-members", dependencies=[Depends(require_permission("org:role:grant"))])
async def add_members(request: Request):
    """添加角色成员

    Returns:
        添加结果
    """
    controller = OrganizationController(request)
    return await controller.add_members()


@router.post("/remove-member", dependencies=[Depends(require_permission("org:role:grant"))])
async def remove_member(request: Request):
    """移除角色成员

    Returns:
        移除结果
    """
    controller = OrganizationController(request)
    return await controller.remove_member()


@router.post("/remove-members-batch", dependencies=[Depends(require_permission("org:role:grant"))])
async def remove_members_batch(request: Request):
    """批量移除角色成员

    Returns:
        移除结果
    """
    controller = OrganizationController(request)
    return await controller.remove_members_batch()


@router.post("/import-roles", dependencies=[Depends(require_permission("org:role:import"))])
async def import_roles(request: Request):
    """导入角色

    Returns:
        导入结果
    """
    controller = OrganizationController(request)
    return await controller.import_roles()


@router.post("/export-roles", dependencies=[Depends(require_permission("org:role:export"))])
async def export_roles(request: Request, background_tasks: BackgroundTasks):
    """导出角色

    Returns:
        导出结果
    """
    controller = OrganizationController(request)
    return await controller.export_roles(background_tasks)


@router.post("/export-role-members", dependencies=[Depends(require_permission("org:role:export"))])
async def export_role_members(request: Request, background_tasks: BackgroundTasks):
    """导出角色成员

    Returns:
        导出结果
    """
    controller = OrganizationController(request)
    return await controller.export_role_members(background_tasks)


@router.post("/create-role", dependencies=[Depends(require_permission("org:role:create"))])
async def create_role(request: Request):
    """创建角色

    Returns:
        创建结果
    """
    controller = OrganizationController(request)
    return await controller.create_role()


@router.post("/update-role", dependencies=[Depends(require_permission("org:role:update"))])
async def update_role(request: Request):
    """更新角色

    Returns:
        更新结果
    """
    controller = OrganizationController(request)
    return await controller.update_role()


@router.post("/delete-role", dependencies=[Depends(require_permission("org:role:delete"))])
async def delete_role(request: Request):
    """删除角色

    Returns:
        删除结果
    """
    controller = OrganizationController(request)
    return await controller.delete_role()


@router.post("/get-permission-tree", dependencies=[Depends(require_permission("org:role:grant"))])
async def get_permission_tree(request: Request):
    """获取权限清单树

    Returns:
        权限点树形结构
    """
    controller = OrganizationController(request)
    return await controller.get_permission_tree()


@router.post("/get-role-permissions", dependencies=[Depends(require_permission("org:role:grant"))])
async def get_role_permissions(request: Request):
    """获取角色已授权的权限点

    Returns:
        角色权限信息
    """
    controller = OrganizationController(request)
    return await controller.get_role_permissions()


@router.post("/grant-role-permissions", dependencies=[Depends(require_permission("org:role:grant"))])
async def grant_role_permissions(request: Request):
    """保存角色授权

    Returns:
        保存结果
    """
    controller = OrganizationController(request)
    return await controller.grant_role_permissions()
