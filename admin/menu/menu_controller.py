from fastapi import Request, BackgroundTasks
from framework.core.auth import get_current_user
from framework.core.controller import Controller
from .menu_model import MenuModel
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


class MenuController(Controller):
    def __init__(self, request: Request):
        super().__init__(request)
        self.model = MenuModel()

    async def get_menu_tree(self):
        """获取菜单树

        Returns:
            菜单树结构
        """
        try:
            menu_tree = await self.model.get_menu_tree()
            return self.success(menu_tree)
        except Exception as e:
            logger.error(f"获取菜单树失败: {str(e)}")
            return self.error(message=str(e))

    async def get_user_menu_tree(self):
        """获取当前登录用户可见的菜单树

        Returns:
            过滤后的菜单树结构
        """
        try:
            current_user = await get_current_user(self.request)
            menu_tree = await self.model.get_user_menu_tree(
                current_user.get("permissions"), current_user.get("is_admin", False)
            )
            return self.success(menu_tree)
        except Exception as e:
            logger.error(f"获取用户菜单树失败: {str(e)}")
            return self.error(message=str(e))

    async def get_menu_list(self):
        """获取菜单列表

        Returns:
            菜单列表
        """
        try:
            data = await self.request.json()
            menu_list = await self.model.get_menu_list(data)
            return self.success(menu_list)
        except Exception as e:
            logger.error(f"获取菜单列表失败: {str(e)}")
            return self.error(message=str(e))

    async def create_menu(self):
        """创建菜单

        Returns:
            创建结果
        """
        try:
            data = (await self.request.json()).get("data", {})
            if not data:
                return self.error(message="创建数据不能为空")
            result = await self.model.create_menu(data)
            return self.success(result)
        except Exception as e:
            logger.error(f"创建菜单失败: {str(e)}")
            return self.error(message=str(e))

    async def update_menu(self):
        """更新菜单

        Returns:
            更新结果
        """
        try:
            data = (await self.request.json()).get("data", {})
            if not data:
                return self.error(message="更新数据不能为空")

            menu_id = data.get("id")
            if not menu_id:
                return self.error(message="菜单ID不能为空")

            result = await self.model.update_menu(menu_id, data)
            if not result:
                return self.error(code=404, message="菜单不存在")
            return self.success(result)
        except Exception as e:
            logger.error(f"更新菜单失败: {str(e)}")
            return self.error(message=str(e))

    async def delete_menu(self):
        """删除菜单

        Returns:
            删除结果
        """
        try:
            data = (await self.request.json()).get("data", {})
            if not data or not data.get("id"):
                return self.error(message="菜单ID不能为空")
            menu_id = data.get("id")
            await self.model.delete_menu(menu_id)
            return self.success()
        except Exception as e:
            logger.error(f"删除菜单失败: {str(e)}")
            return self.error(message=str(e))

    async def destroy_menu(self):
        """物理删除菜单

        Returns:
            删除结果
        """
        try:
            data = (await self.request.json()).get("data", {})
            if not data or not data.get("id"):
                return self.error(message="菜单ID不能为空")
            menu_id = data.get("id")
            await self.model.destroy_menu(menu_id)
            return self.success()
        except Exception as e:
            logger.error(f"物理删除菜单失败: {str(e)}")
            return self.error(message=str(e))

    async def batch_all_menu(self):
        """删除所有符合筛选条件的数据

        Returns:
            删除结果
        """
        try:
            data = await self.request.json()
            result = await self.model.batch_all_menu(data)
            return self.success({"affected": result})
        except Exception as e:
            logger.error(f"批量删除失败: {str(e)}")
            return self.error(message=str(e))

    async def batch_menu(self):
        """批量删除指定ID的数据

        Returns:
            删除结果
        """
        try:
            data = await self.request.json()
            result = await self.model.batch_menu(data)
            return self.success({"affected": result})
        except Exception as e:
            logger.error(f"批量删除失败: {str(e)}")
            return self.error(message=str(e))

    async def batch_update_menus(self):
        """批量更新多个菜单

        Returns:
            更新结果
        """
        try:
            data = (await self.request.json()).get("data", [])

            if isinstance(data, list):
                if not data:
                    return self.error(message="更新数据不能为空")

                success_count = 0
                for item in data:
                    menu_id = item.get("id")
                    if menu_id:
                        await self.model.update_menu(menu_id, item)
                        success_count += 1

                return self.success({"affected": success_count})
            elif isinstance(data, dict):
                ids = data.get("ids", [])
                if not ids:
                    return self.error(message="更新数据不能为空")

                update_data = {k: v for k, v in data.items() if k != "ids"}
                if not update_data:
                    return self.error(message="更新数据不能为空")

                affected = await self.model.batch_update_menu(ids, data)
                return self.success({"affected": affected})
            else:
                return self.error(message="更新数据格式错误")
        except Exception as e:
            logger.error(f"批量更新菜单失败: {str(e)}")
            return self.error(message=str(e))

    async def export_menu(self, background_tasks: BackgroundTasks):
        """导出菜单数据为Excel文件

        Returns:
            导出任务信息
        """
        try:
            data = await self.request.json()
            user_id = data.get("user_id", "unknown")
            task_id = str(uuid.uuid4())

            background_tasks.add_task(self._export_task, user_id, task_id, data)

            return self.success({"message": "后台正在处理导出任务", "task_id": task_id, "status": "processing"})
        except Exception as e:
            logger.error(f"导出失败: {str(e)}")
            return self.error(message=str(e))

    async def _export_task(self, user_id, task_id, data):
        """后台导出任务"""
        try:
            logger.info(f"开始导出任务: {task_id}")
            export_result = await self.model.export_menu(data)

            from admin.ws.ws_route import export_files, EXPORT_DIR
            import time
            import os

            file_path = os.path.join(EXPORT_DIR, f"{task_id}.xlsx")

            with open(file_path, "wb") as f:
                f.write(export_result.get("data"))

            export_files[task_id] = {
                "file_path": file_path,
                "filename": export_result.get("filename", "menus.xlsx"),
                "created_at": time.time(),
            }

            file_url = f"http://localhost:8000/ws/download/{task_id}"

            from admin.ws.ws_service import send_message_to_user
            from admin.notification.notification_model import NotificationModel

            await send_message_to_user(
                user_id,
                {
                    "type": "export_complete",
                    "task_id": task_id,
                    "message": "导出任务已完成",
                    "file_url": file_url,
                    "data": {
                        "filename": export_result.get("filename", "menus.xlsx"),
                        "size": export_result.get("size", 0),
                    },
                },
            )

            notification_model = NotificationModel()
            await notification_model.create_message(
                title="导出文件准备完成",
                content=f"【菜单】导出文件已准备完成。文件下载链接将于24小时后失效",
                type="success",
                subtype="export",
                download_url=file_url,
            )

            logger.info(f"导出任务完成: {task_id}")
        except Exception as e:
            logger.error(f"导出任务失败: {str(e)}")
            from admin.ws.ws_service import send_message_to_user
            await send_message_to_user(
                user_id, {"type": "export_error", "task_id": task_id, "message": f"导出任务失败: {str(e)}"}
            )

    async def import_menu(self):
        """导入菜单数据

        Returns:
            导入结果
        """
        try:
            form_data = await self.request.form()
            file = form_data.get("file")
            if not file:
                return self.error(message="请选择要导入的文件")

            import_mode = form_data.get("import_mode", "insert")

            import json
            field_mapping_str = form_data.get("field_mapping")
            field_mapping = json.loads(field_mapping_str) if field_mapping_str else {}

            result = await self.model.import_menu(file, import_mode, field_mapping)
            return self.success(result)
        except Exception as e:
            logger.error(f"导入失败: {str(e)}")
            return self.error(message=str(e))