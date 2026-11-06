from fastapi import APIRouter, Depends, Request
from framework.core.auth import require_permission
from .demo_controller import DemoController

router = APIRouter(prefix="/admin/demo", tags=["demo示例"])


@router.post("/get-demo-list", dependencies=[Depends(require_permission("demo:list"))])
async def get_demo_list(request: Request):
    """获取demo列表"""
    return await DemoController(request).get_demo_list()


@router.post("/get-demo", dependencies=[Depends(require_permission("demo:list"))])
async def get_demo(request: Request):
    """获取demo详情"""
    return await DemoController(request).get_demo()


@router.post("/create-demo", dependencies=[Depends(require_permission("demo:create"))])
async def create_demo(request: Request):
    """创建demo"""
    return await DemoController(request).create_demo()


@router.post("/update-demo", dependencies=[Depends(require_permission("demo:update"))])
async def update_demo(request: Request):
    """更新demo"""
    return await DemoController(request).update_demo()


@router.post("/delete-demo", dependencies=[Depends(require_permission("demo:delete"))])
async def delete_demo(request: Request):
    """删除demo（软删除）"""
    return await DemoController(request).delete_demo()


@router.post("/destroy-demo", dependencies=[Depends(require_permission("demo:delete"))])
async def destroy_demo(request: Request):
    """物理删除demo"""
    return await DemoController(request).destroy_demo()


@router.post("/batch-demo", dependencies=[Depends(require_permission("demo:delete"))])
async def batch_demo(request: Request):
    """批量删除demo"""
    return await DemoController(request).batch_demo()
