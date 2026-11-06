from fastapi import Request, BackgroundTasks, UploadFile, File, Form
from framework.core.controller import Controller
from framework.core.auth import get_current_user
from .organization_model import OrganizationModel
from admin.ws.ws_service import send_message_to_user
from admin.notification.notification_model import NotificationModel
import logging
import uuid

logger = logging.getLogger(__name__)


class OrganizationController(Controller):
    def __init__(self, request: Request):
        super().__init__(request)
        self.model = OrganizationModel()
        self.notification_model = NotificationModel()

    async def get_dept_tree(self):
        """获取部门树形结构

        Returns:
            部门树形结构
        """
        try:
            dept_tree = await self.model.get_dept_tree(self.request)
            return self.success(dept_tree)
        except Exception as e:
            logger.error(f"获取部门树形结构失败: {str(e)}")
            return self.error(message=str(e))

    async def get_user_list(self):
        """获取用户列表

        Returns:
            用户列表
        """
        try:
            user_paginate = await self.model.get_user_list(self.request)
            return self.success(user_paginate)
        except Exception as e:
            logger.error(f"获取用户列表失败: {str(e)}")
            return self.error(message=str(e))

    async def create_dept(self):
        """创建部门

        Returns:
            创建结果
        """
        try:
            data = (await self.request.json()).get("data", {})
            if not data:
                return self.error(message="创建数据不能为空")
            result = await self.model.create_dept(data)
            return self.success(result)
        except Exception as e:
            logger.error(f"创建部门失败: {str(e)}")
            return self.error(message=str(e))

    async def update_dept(self):
        """更新部门

        Returns:
            更新结果
        """
        try:
            data = (await self.request.json()).get("data", {})
            if not data:
                return self.error(message="更新数据不能为空")
            dept_id = data.get("id")
            if not dept_id:
                return self.error(message="部门ID不能为空")
            result = await self.model.update_dept(dept_id, data)
            return self.success(result)
        except Exception as e:
            logger.error(f"更新部门失败: {str(e)}")
            return self.error(message=str(e))

    async def delete_dept(self):
        """删除部门

        Returns:
            删除结果
        """
        try:
            data = (await self.request.json()).get("data", {})
            if not data or not data.get("id"):
                return self.error(message="部门ID不能为空")
            dept_id = data.get("id")
            await self.model.delete_dept(dept_id)
            return self.success()
        except Exception as e:
            logger.error(f"删除部门失败: {str(e)}")
            return self.error(message=str(e))

    async def get_dept(self):
        """获取单个部门

        Returns:
            部门信息
        """
        try:
            data = (await self.request.json()).get("data", {})
            dept_id = data.get("id")
            if not dept_id:
                return self.error(message="部门ID不能为空")
            dept = await self.model.get_dept(dept_id)
            if not dept:
                return self.error(code=404, message="部门不存在")
            return self.success(dept)
        except Exception as e:
            logger.error(f"获取部门失败: {str(e)}")
            return self.error(message=str(e))

    async def create_user(self):
        """创建用户

        Returns:
            创建结果
        """
        try:
            data = (await self.request.json()).get("data", {})
            if not data:
                return self.error(message="创建数据不能为空")
            result = await self.model.create_user(data)
            return self.success(result)
        except Exception as e:
            logger.error(f"创建用户失败: {str(e)}")
            return self.error(message=str(e))

    async def update_user(self):
        """更新用户

        Returns:
            更新结果
        """
        try:
            data = (await self.request.json()).get("data", {})
            if not data:
                return self.error(message="更新数据不能为空")

            # 检查是否是批量更新
            ids = data.get("ids")
            if ids:
                # 批量更新
                result = await self.model.batch_update_users(ids, data)
                return self.success({"affected": result})
            else:
                # 单个更新
                user_id = data.get("id")
                if not user_id:
                    return self.error(message="用户ID不能为空")
                result = await self.model.update_user(user_id, data)
                return self.success(result)
        except Exception as e:
            logger.error(f"更新用户失败: {str(e)}")
            return self.error(message=str(e))

    async def delete_user(self):
        """删除用户

        Returns:
            删除结果
        """
        try:
            data = (await self.request.json()).get("data", {})
            if not data or not data.get("id"):
                return self.error(message="用户ID不能为空")
            user_id = data.get("id")
            await self.model.delete_user(user_id)
            return self.success()
        except Exception as e:
            logger.error(f"删除用户失败: {str(e)}")
            return self.error(message=str(e))

    async def destroy_user(self):
        """物理删除用户

        Returns:
            删除结果
        """
        try:
            data = (await self.request.json()).get("data", {})
            if not data or not data.get("id"):
                return self.error(message="用户ID不能为空")
            user_id = data.get("id")
            await self.model.destroy_user(user_id)
            return self.success()
        except Exception as e:
            logger.error(f"物理删除用户失败: {str(e)}")
            return self.error(message=str(e))

    async def get_user(self):
        """获取单个用户

        Returns:
            用户信息
        """
        try:
            data = (await self.request.json()).get("data", {})
            user_id = data.get("id")
            if not user_id:
                return self.error(message="用户ID不能为空")
            user = await self.model.get_user(user_id)
            if not user:
                return self.error(code=404, message="用户不存在")
            return self.success(user)
        except Exception as e:
            logger.error(f"获取用户失败: {str(e)}")
            return self.error(message=str(e))

    async def import_users(self):
        """导入用户

        Returns:
            导入结果
        """
        try:
            # 获取上传的文件
            form_data = await self.request.form()
            file = form_data.get("file")
            if not file:
                return self.error(message="请选择要导入的文件")

            # 获取导入模式
            import_mode = form_data.get("import_mode", "insert")

            # 获取字段映射
            import json

            field_mapping_str = form_data.get("field_mapping")
            field_mapping = json.loads(field_mapping_str) if field_mapping_str else {}

            # 调用模型的导入方法
            result = await self.model.import_users(file, import_mode, field_mapping)
            return self.success(result)
        except Exception as e:
            logger.error(f"导入用户失败: {str(e)}")
            return self.error(message=str(e))

    async def export_users(self, background_tasks: BackgroundTasks):
        """导出用户

        Returns:
            导出任务信息
        """
        try:
            data = await self.request.json()
            user_id = data.get("user_id", "unknown")
            task_id = str(uuid.uuid4())

            # 添加后台任务
            background_tasks.add_task(self._export_users_task, user_id, task_id, data)

            return self.success({"message": "后台正在处理导出任务", "task_id": task_id, "status": "processing"})
        except Exception as e:
            logger.error(f"导出用户失败: {str(e)}")
            return self.error(message=str(e))

    async def _export_users_task(self, user_id, task_id, data):
        """后台导出用户任务"""
        try:
            logger.info(f"开始导出用户任务: {task_id}")
            # 执行导出操作
            export_result = await self.model.export_users(data)

            # 存储导出的文件到临时目录
            from admin.ws.ws_route import export_files, EXPORT_DIR
            import time
            import os

            # 生成临时文件路径
            file_path = os.path.join(EXPORT_DIR, f"{task_id}.xlsx")

            # 将文件内容写入临时文件
            with open(file_path, "wb") as f:
                f.write(export_result.get("data"))

            # 存储文件信息
            export_files[task_id] = {
                "file_path": file_path,
                "filename": export_result.get("filename", "users.xlsx"),
                "created_at": time.time(),
            }

            # 构建文件下载链接
            file_url = f"http://localhost:8000/ws/download/{task_id}"

            # 发送WebSocket通知
            await send_message_to_user(
                user_id,
                {
                    "type": "export_complete",
                    "task_id": task_id,
                    "message": "导出任务已完成",
                    "file_url": file_url,
                    "data": {
                        "filename": export_result.get("filename", "users.xlsx"),
                        "size": export_result.get("size", 0),
                    },
                },
            )

            # 同时新建notification消息
            await self.notification_model.create_message(
                title="导出文件准备完成",
                content=f"【用户】导出文件已准备完成。文件下载链接将于24小时后失效",
                type="success",
                subtype="export",
                download_url=file_url,
            )

            logger.info(f"导出用户任务完成: {task_id}")
        except Exception as e:
            logger.error(f"导出用户任务失败: {str(e)}")
            # 发送错误通知
            await send_message_to_user(
                user_id, {"type": "export_error", "task_id": task_id, "message": f"导出任务失败: {str(e)}"}
            )

    async def export_users_selected(self, background_tasks: BackgroundTasks):
        """导出选中用户

        Returns:
            导出任务信息
        """
        try:
            data = await self.request.json()
            user_id = data.get("user_id", "unknown")
            task_id = str(uuid.uuid4())

            # 添加后台任务
            background_tasks.add_task(self._export_users_selected_task, user_id, task_id, data)

            return self.success({"message": "后台正在处理导出任务", "task_id": task_id, "status": "processing"})
        except Exception as e:
            logger.error(f"导出选中用户失败: {str(e)}")
            return self.error(message=str(e))

    async def _export_users_selected_task(self, user_id, task_id, data):
        """后台导出选中用户任务"""
        try:
            logger.info(f"开始导出选中用户任务: {task_id}")
            # 执行导出操作
            export_result = await self.model.export_users_selected(data)

            # 存储导出的文件到临时目录
            from admin.ws.ws_route import export_files, EXPORT_DIR
            import time
            import os

            # 生成临时文件路径
            file_path = os.path.join(EXPORT_DIR, f"{task_id}.xlsx")

            # 将文件内容写入临时文件
            with open(file_path, "wb") as f:
                f.write(export_result.get("data"))

            # 存储文件信息
            export_files[task_id] = {
                "file_path": file_path,
                "filename": export_result.get("filename", "users_selected.xlsx"),
                "created_at": time.time(),
            }

            # 构建文件下载链接
            file_url = f"http://localhost:8000/ws/download/{task_id}"

            # 发送WebSocket通知
            await send_message_to_user(
                user_id,
                {
                    "type": "export_complete",
                    "task_id": task_id,
                    "message": "导出任务已完成",
                    "file_url": file_url,
                    "data": {
                        "filename": export_result.get("filename", "users_selected.xlsx"),
                        "size": export_result.get("size", 0),
                    },
                },
            )

            # 同时新建notification消息
            await self.notification_model.create_message(
                title="导出文件准备完成",
                content=f"【用户】导出文件已准备完成。文件下载链接将于24小时后失效",
                type="success",
                subtype="export",
                download_url=file_url,
            )

            logger.info(f"导出选中用户任务完成: {task_id}")
        except Exception as e:
            logger.error(f"导出选中用户任务失败: {str(e)}")
            # 发送错误通知
            await send_message_to_user(
                user_id, {"type": "export_error", "task_id": task_id, "message": f"导出任务失败: {str(e)}"}
            )

    async def delete_users_batch(self):
        """批量删除所有符合条件的用户

        Returns:
            删除结果
        """
        try:
            data = await self.request.json()
            result = await self.model.batch_all_users(data)
            return self.success({"affected": result})
        except Exception as e:
            logger.error(f"批量删除用户失败: {str(e)}")
            return self.error(message=str(e))

    async def delete_users_selected(self):
        """批量删除选中的用户

        Returns:
            删除结果
        """
        try:
            # 尝试从请求体获取数据
            try:
                data = await self.request.json()
            except Exception as json_error:
                # 如果无法解析JSON，尝试从表单数据获取
                from fastapi import Form
                import json

                data = {}
                # 处理表单数据
                form_data = await self.request.form()
                if form_data:
                    # 尝试解析ids字段
                    ids_str = form_data.get("ids")
                    if ids_str:
                        try:
                            data["ids"] = json.loads(ids_str)
                        except:
                            pass
            result = await self.model.batch_delete_users(data.get("ids", []))
            return self.success({"affected": result})
        except Exception as e:
            logger.error(f"批量删除选中用户失败: {str(e)}")
            return self.error(message=str(e))

    async def update_users_batch(self):
        """批量修改用户状态

        Returns:
            更新结果
        """
        try:
            data = await self.request.json()
            user_ids = data.get("ids", [])
            if not user_ids:
                return self.error(message="用户ID列表不能为空")
            affected = await self.model.batch_update_users(user_ids, data)
            return self.success({"affected": affected})
        except Exception as e:
            logger.error(f"批量更新用户失败: {str(e)}")
            return self.error(message=str(e))

    async def get_role_tree(self):
        """获取角色树

        Returns:
            角色树
        """
        try:
            role_tree = await self.model.get_role_tree(self.request)
            return self.success(role_tree)
        except Exception as e:
            logger.error(f"获取角色树失败: {str(e)}")
            return self.error(message=str(e))

    async def get_members(self):
        """获取角色成员

        Returns:
            角色成员
        """
        try:
            members = await self.model.get_members(self.request)
            return self.success(members)
        except Exception as e:
            logger.error(f"获取角色成员失败: {str(e)}")
            return self.error(message=str(e))

    async def get_available_users(self):
        """获取可用用户

        Returns:
            可用用户
        """
        try:
            users = await self.model.get_available_users(self.request)
            return self.success(users)
        except Exception as e:
            logger.error(f"获取可用用户失败: {str(e)}")
            return self.error(message=str(e))

    async def add_members(self):
        """添加角色成员

        Returns:
            添加结果
        """
        try:
            result = await self.model.add_members(self.request)
            if result.get("code") == 200:
                return self.success()
            else:
                return self.error(message=result.get("message"))
        except Exception as e:
            logger.error(f"添加角色成员失败: {str(e)}")
            return self.error(message=str(e))

    async def remove_member(self):
        """移除角色成员

        Returns:
            移除结果
        """
        try:
            result = await self.model.remove_member(self.request)
            if result.get("code") == 200:
                return self.success()
            else:
                return self.error(message=result.get("message"))
        except Exception as e:
            logger.error(f"移除角色成员失败: {str(e)}")
            return self.error(message=str(e))

    async def remove_members_batch(self):
        """批量移除角色成员

        Returns:
            移除结果
        """
        try:
            result = await self.model.remove_members_batch(self.request)
            if result.get("code") == 200:
                return self.success()
            else:
                return self.error(message=result.get("message"))
        except Exception as e:
            logger.error(f"批量移除角色成员失败: {str(e)}")
            return self.error(message=str(e))

    async def import_roles(self):
        """导入角色

        Returns:
            导入结果
        """
        try:
            result = await self.model.import_roles(self.request)
            return self.success(result)
        except Exception as e:
            logger.error(f"导入角色失败: {str(e)}")
            return self.error(message=str(e))

    async def export_roles(self, background_tasks: BackgroundTasks):
        """导出角色

        Returns:
            导出任务信息
        """
        try:
            data = await self.request.json()
            user_id = data.get("user_id", "unknown")
            task_id = str(uuid.uuid4())

            # 添加后台任务
            background_tasks.add_task(self._export_roles_task, user_id, task_id, data)

            return self.success({"message": "后台正在处理导出任务", "task_id": task_id, "status": "processing"})
        except Exception as e:
            logger.error(f"导出角色失败: {str(e)}")
            return self.error(message=str(e))

    async def _export_roles_task(self, user_id, task_id, data):
        """后台导出角色任务"""
        try:
            logger.info(f"开始导出角色任务: {task_id}")
            # 执行导出操作
            export_result = await self.model.export_roles(data)

            # 存储导出的文件到临时目录
            from admin.ws.ws_route import export_files, EXPORT_DIR
            import time
            import os

            # 生成临时文件路径
            file_path = os.path.join(EXPORT_DIR, f"{task_id}.xlsx")

            # 将文件内容写入临时文件
            with open(file_path, "wb") as f:
                f.write(export_result.get("data"))

            # 存储文件信息
            export_files[task_id] = {
                "file_path": file_path,
                "filename": export_result.get("filename", "roles.xlsx"),
                "created_at": time.time(),
            }

            # 构建文件下载链接
            file_url = f"http://localhost:8000/ws/download/{task_id}"

            # 发送WebSocket通知
            await send_message_to_user(
                user_id,
                {
                    "type": "export_complete",
                    "task_id": task_id,
                    "message": "导出任务已完成",
                    "file_url": file_url,
                    "data": {
                        "filename": export_result.get("filename", "roles.xlsx"),
                        "size": export_result.get("size", 0),
                    },
                },
            )

            # 同时新建notification消息
            await self.notification_model.create_message(
                title="导出文件准备完成",
                content=f"【角色】导出文件已准备完成。文件下载链接将于24小时后失效",
                type="success",
                subtype="export",
                download_url=file_url,
            )

            logger.info(f"导出角色任务完成: {task_id}")
        except Exception as e:
            logger.error(f"导出角色任务失败: {str(e)}")
            # 发送错误通知
            await send_message_to_user(
                user_id, {"type": "export_error", "task_id": task_id, "message": f"导出任务失败: {str(e)}"}
            )

    async def export_role_members(self, background_tasks: BackgroundTasks):
        """导出角色成员

        Returns:
            导出任务信息
        """
        try:
            current_user = await get_current_user(self.request)
            data = await self.request.json()
            user_id = str(current_user["id"])
            task_id = str(uuid.uuid4())

            # 添加后台任务
            background_tasks.add_task(self._export_role_members_task, user_id, task_id, data)

            return self.success({"message": "后台正在处理导出任务", "task_id": task_id, "status": "processing"})
        except Exception as e:
            logger.error(f"导出角色成员失败: {str(e)}")
            return self.error(message=str(e))

    async def _export_role_members_task(self, user_id, task_id, data):
        """后台导出角色成员任务"""
        try:
            logger.info(f"开始导出角色成员任务: {task_id}")
            # 执行导出操作
            export_result = await self.model.export_role_members(data)

            # 存储导出的文件到临时目录
            from admin.ws.ws_route import export_files, EXPORT_DIR
            import time
            import os

            # 生成临时文件路径
            file_path = os.path.join(EXPORT_DIR, f"{task_id}.xlsx")

            # 将文件内容写入临时文件
            with open(file_path, "wb") as f:
                f.write(export_result.get("data"))

            # 存储文件信息
            export_files[task_id] = {
                "file_path": file_path,
                "filename": export_result.get("filename", "role_members.xlsx"),
                "created_at": time.time(),
            }

            # 构建文件下载链接
            file_url = f"http://localhost:8000/ws/download/{task_id}"

            # 发送WebSocket通知
            await send_message_to_user(
                user_id,
                {
                    "type": "export_complete",
                    "task_id": task_id,
                    "message": "导出任务已完成",
                    "file_url": file_url,
                    "data": {
                        "filename": export_result.get("filename", "role_members.xlsx"),
                        "size": export_result.get("size", 0),
                    },
                },
            )

            # 同时新建notification消息
            await self.notification_model.create_message(
                title="导出文件准备完成",
                content=f"【角色成员】导出文件已准备完成。文件下载链接将于24小时后失效",
                type="success",
                subtype="export",
                download_url=file_url,
            )

            logger.info(f"导出角色成员任务完成: {task_id}")
        except Exception as e:
            logger.error(f"导出角色成员任务失败: {str(e)}")
            # 发送错误通知
            await send_message_to_user(
                user_id, {"type": "export_error", "task_id": task_id, "message": f"导出任务失败: {str(e)}"}
            )

    async def create_role(self):
        """创建角色

        Returns:
            创建结果
        """
        try:
            data = (await self.request.json()).get("data", {})
            if not data:
                return self.error(message="创建数据不能为空")
            result = await self.model.create_role(data)
            return self.success(result)
        except Exception as e:
            logger.error(f"创建角色失败: {str(e)}")
            return self.error(message=str(e))

    async def update_role(self):
        """更新角色

        Returns:
            更新结果
        """
        try:
            data = (await self.request.json()).get("data", {})
            if not data:
                return self.error(message="更新数据不能为空")
            role_id = data.get("id")
            if not role_id:
                return self.error(message="角色ID不能为空")
            result = await self.model.update_role(role_id, data)
            return self.success(result)
        except Exception as e:
            logger.error(f"更新角色失败: {str(e)}")
            return self.error(message=str(e))

    async def delete_role(self):
        """删除角色

        Returns:
            删除结果
        """
        try:
            data = (await self.request.json()).get("data", {})
            if not data or not data.get("id"):
                return self.error(message="角色ID不能为空")
            role_id = data.get("id")
            await self.model.delete_role(role_id)
            return self.success()
        except Exception as e:
            logger.error(f"删除角色失败: {str(e)}")
            return self.error(message=str(e))

    async def get_permission_tree(self):
        """获取权限清单树

        Returns:
            权限点树形结构
        """
        try:
            tree = await self.model.get_permission_tree(self.request)
            return self.success(tree)
        except Exception as e:
            logger.error(f"获取权限清单失败: {str(e)}")
            return self.error(message=str(e))

    async def get_role_permissions(self):
        """获取角色已授权的权限点

        Returns:
            角色权限信息
        """
        try:
            data = (await self.request.json()).get("data", {})
            role_id = data.get("role_id") or data.get("id")
            if not role_id:
                return self.error(message="角色ID不能为空")
            result = await self.model.get_role_permissions(role_id)
            return self.success(result)
        except Exception as e:
            logger.error(f"获取角色权限失败: {str(e)}")
            return self.error(message=str(e))

    async def grant_role_permissions(self):
        """保存角色授权

        Returns:
            保存结果
        """
        try:
            data = (await self.request.json()).get("data", {})
            role_id = data.get("role_id") or data.get("id")
            if not role_id:
                return self.error(message="角色ID不能为空")
            permission_ids = data.get("permission_ids", [])
            result = await self.model.grant_role_permissions(role_id, permission_ids)
            return self.success(result)
        except Exception as e:
            logger.error(f"保存角色授权失败: {str(e)}")
            return self.error(message=str(e))
