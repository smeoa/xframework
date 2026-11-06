from fastapi import APIRouter, Request
from admin.profile.profile_controller import ProfileController

router = APIRouter(prefix="/admin/profile", tags=["个人设置"])


@router.post("/get-profile")
async def get_profile_handler(request: Request):
    """获取个人资料"""
    controller = ProfileController(request)
    return await controller.get_profile()


@router.post("/update-profile")
async def update_profile_handler(request: Request):
    """更新个人资料"""
    controller = ProfileController(request)
    return await controller.update_profile()


@router.post("/change-password")
async def change_password_handler(request: Request):
    """修改密码"""
    controller = ProfileController(request)
    return await controller.change_password()


@router.post("/get-login-logs")
async def get_login_logs_handler(request: Request):
    """获取登录记录"""
    controller = ProfileController(request)
    return await controller.get_login_logs()


@router.post("/get-notification-settings")
async def get_notification_settings_handler(request: Request):
    """获取通知设置"""
    controller = ProfileController(request)
    return await controller.get_notification_settings()


@router.post("/update-notification-settings")
async def update_notification_settings_handler(request: Request):
    """更新通知设置"""
    controller = ProfileController(request)
    return await controller.update_notification_settings()


@router.post("/get-interface-settings")
async def get_interface_settings_handler(request: Request):
    """获取界面设置"""
    controller = ProfileController(request)
    return await controller.get_interface_settings()


@router.post("/update-interface-settings")
async def update_interface_settings_handler(request: Request):
    """更新界面设置"""
    controller = ProfileController(request)
    return await controller.update_interface_settings()


@router.post("/get-api-keys")
async def get_api_keys_handler(request: Request):
    """获取API密钥列表"""
    controller = ProfileController(request)
    return await controller.get_api_keys()


@router.post("/create-api-key")
async def create_api_key_handler(request: Request):
    """创建API密钥"""
    controller = ProfileController(request)
    return await controller.create_api_key()


@router.post("/toggle-api-key-status")
async def toggle_api_key_status_handler(request: Request):
    """切换API密钥状态"""
    controller = ProfileController(request)
    return await controller.toggle_api_key_status()


@router.post("/delete-api-key")
async def delete_api_key_handler(request: Request):
    """删除API密钥"""
    controller = ProfileController(request)
    return await controller.delete_api_key()
