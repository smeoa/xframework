from fastapi import APIRouter, Request
from .notification_controller import NotificationController
from .notification_model import NotificationModel

# 创建主路由
router = APIRouter(prefix="/admin/notification", tags=["消息通知"])

# 创建模型实例
model = NotificationModel()


# 初始化表结构的函数，将在FastAPI启动时调用
async def init_notification_table():
    """初始化消息通知表"""
    try:
        await model.create_table()
        print("消息通知表初始化成功")
    except Exception as e:
        print(f"初始化消息通知表失败: {str(e)}")


# 导出初始化函数供主应用调用
__all__ = ["init_notification_table"]


@router.post("/get-message-list")
async def get_message_list_api(request: Request):
    """获取消息列表

    Returns:
        消息列表
    """
    controller = NotificationController(request)
    return await controller.get_message_list()


@router.post("/mark-all-as-read")
async def mark_all_as_read_api(request: Request):
    """标记所有消息为已读

    Returns:
        操作结果
    """
    controller = NotificationController(request)
    return await controller.mark_all_as_read()


@router.post("/mark-messages-as-read")
async def mark_messages_as_read_api(request: Request):
    """标记指定消息为已读

    Returns:
        操作结果
    """
    controller = NotificationController(request)
    return await controller.mark_messages_as_read()
