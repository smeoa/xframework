from fastapi import HTTPException, Request
from .notification_model import (
    NotificationModel,
)


class NotificationController:
    """消息通知控制器"""

    def __init__(self, request: Request):
        """初始化控制器

        Args:
            request: 请求对象
        """
        self.request = request
        self.model = NotificationModel()

    async def get_message_list(self):
        """获取消息列表

        Returns:
            消息列表响应
        """
        try:
            # 从请求体中获取参数
            body = await self.request.json()
            type = body.get("type", "all")
            only_unread = body.get("only_unread", False)

            # 获取消息列表
            messages = await self.model.get_message_list(type, only_unread)

            # 构建响应
            return {"code": 200, "message": "success", "data": messages}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def mark_all_as_read(self):
        """标记所有消息为已读

        Returns:
            操作结果响应
        """
        try:
            # 标记所有消息为已读
            success = await self.model.mark_all_as_read()

            # 构建响应
            return {"code": 200, "message": "success", "data": {"success": success}}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def mark_messages_as_read(self):
        """标记指定消息为已读

        Returns:
            操作结果响应
        """
        try:
            # 从请求体中获取参数
            body = await self.request.json()
            message_ids = body.get("message_ids", [])

            # 验证参数
            if not message_ids:
                return {
                    "code": 400,
                    "message": "message_ids is required",
                    "data": {"success": False},
                }

            # 标记指定消息为已读
            success = await self.model.mark_messages_as_read(message_ids)

            # 构建响应
            return {"code": 200, "message": "success", "data": {"success": success}}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
