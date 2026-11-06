from fastapi import APIRouter, BackgroundTasks, Depends, Request
from framework.core.auth import require_permission
from .menu_controller import MenuController

router = APIRouter(prefix="/admin/menu", tags=["菜单管理"])


@router.post("/get-menu-tree", dependencies=[Depends(require_permission("sysmenu:list"))])
async def get_menu_tree(request: Request):
    """获取菜单树"""
    controller = MenuController(request)
    return await controller.get_menu_tree()


@router.post("/get-user-menu-tree")
async def get_user_menu_tree(request: Request):
    """获取当前登录用户可见的菜单树（侧边栏使用，仅需登录）"""
    controller = MenuController(request)
    return await controller.get_user_menu_tree()


@router.post("/get-menu-list", dependencies=[Depends(require_permission("sysmenu:list"))])
async def get_menu_list(request: Request):
    """获取菜单列表"""
    controller = MenuController(request)
    return await controller.get_menu_list()


@router.post("/create-menu", dependencies=[Depends(require_permission("sysmenu:create"))])
async def create_menu(request: Request):
    """创建菜单"""
    controller = MenuController(request)
    return await controller.create_menu()


@router.post("/update-menu", dependencies=[Depends(require_permission("sysmenu:update"))])
async def update_menu(request: Request):
    """更新菜单"""
    controller = MenuController(request)
    return await controller.update_menu()


@router.post("/delete-menu", dependencies=[Depends(require_permission("sysmenu:delete"))])
async def delete_menu(request: Request):
    """删除菜单"""
    controller = MenuController(request)
    return await controller.delete_menu()


@router.post("/destroy-menu", dependencies=[Depends(require_permission("sysmenu:delete"))])
async def destroy_menu(request: Request):
    """物理删除菜单"""
    controller = MenuController(request)
    return await controller.destroy_menu()


@router.post("/batch-all-menu", dependencies=[Depends(require_permission("sysmenu:delete"))])
async def batch_all_menu(request: Request):
    """删除所有符合筛选条件的数据"""
    controller = MenuController(request)
    return await controller.batch_all_menu()


@router.post("/batch-menu", dependencies=[Depends(require_permission("sysmenu:delete"))])
async def batch_menu(request: Request):
    """批量删除指定ID的数据"""
    controller = MenuController(request)
    return await controller.batch_menu()


@router.post("/batch-update-menus", dependencies=[Depends(require_permission("sysmenu:update"))])
async def batch_update_menus(request: Request):
    """批量更新多个菜单"""
    controller = MenuController(request)
    return await controller.batch_update_menus()


@router.post("/export-menu", dependencies=[Depends(require_permission("sysmenu:export"))])
async def export_menu(request: Request, background_tasks: BackgroundTasks):
    """导出菜单数据为Excel文件"""
    controller = MenuController(request)
    return await controller.export_menu(background_tasks)


@router.post("/import-menu", dependencies=[Depends(require_permission("sysmenu:import"))])
async def import_menu(request: Request):
    """导入菜单数据"""
    controller = MenuController(request)
    return await controller.import_menu()
