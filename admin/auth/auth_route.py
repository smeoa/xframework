from fastapi import APIRouter, Request

from .auth_controller import AuthController

# 创建主路由
router = APIRouter(prefix="/admin/auth", tags=["认证"])


@router.post("/login")
async def login_api(request: Request):
    """用户登录

    Returns:
        登录结果
    """
    controller = AuthController(request)
    return await controller.login()


@router.post("/get-user-info")
async def get_user_info_api(request: Request):
    """查询当前登录用户的权限上下文

    Returns:
        当前用户权限上下文
    """
    controller = AuthController(request)
    return await controller.get_user_info()
