from fastapi import Request, UploadFile, File, Form, BackgroundTasks
from typing import Optional
import uuid
from datetime import datetime
from framework.core.controller import Controller
from .attachment_model import AttachmentModel
import logging
import qiniu
import shutil

logger = logging.getLogger(__name__)


class AttachmentController(Controller):
    def __init__(self, request: Request):
        super().__init__(request)
        self.attachment_model = AttachmentModel()

    def _get_signed_url(self, storage_key: str, expires: int = 3600) -> str:
        """生成带签名的七牛云访问URL

        Args:
            storage_key: 七牛云存储的key
            expires: 过期时间（秒）

        Returns:
            带签名的访问URL
        """
        qiniu_access_key = self.config.get("QINIU_ACCESS_KEY", "")
        qiniu_secret_key = self.config.get("QINIU_SECRET_KEY", "")
        qiniu_domain = self.config.get("QINIU_DOMAIN", "")

        import qiniu

        auth = qiniu.Auth(qiniu_access_key, qiniu_secret_key)
        base_url = f"http://{qiniu_domain}/{storage_key}"
        private_url = auth.private_download_url(base_url, expires=expires)
        return private_url

    async def get_attachment(self):
        """获取单个附件

        Returns:
            附件信息
        """
        try:
            data = (await self.request.json()).get("data", {})
            attachment_id = data.get("id")
            if not attachment_id:
                return self.error(message="附件ID不能为空")
            # 转换为整数类型
            try:
                attachment_id = int(attachment_id)
            except ValueError:
                return self.error(message="附件ID必须是数字")
            attachment = await self.attachment_model.get_attachment(attachment_id)
            if not attachment:
                return self.error(code=404, message="附件不存在")

            # 动态生成带签名的URL
            if attachment.get("storage_path"):
                attachment["storage_path"] = self._get_signed_url(attachment["storage_path"])

            return self.success(attachment)
        except Exception as e:
            logger.error(f"获取附件失败: {str(e)}")
            return self.error(message=str(e))

    async def get_attachment_list(self):
        """获取附件列表

        Returns:
            附件列表
        """
        try:
            attachment_list = await self.attachment_model.get_attachment_list(self.request)

            # 为每个附件动态生成带签名的URL
            if isinstance(attachment_list, dict) and "items" in attachment_list:
                for item in attachment_list["items"]:
                    if item.get("storage_path"):
                        item["storage_path"] = self._get_signed_url(item["storage_path"])
            elif isinstance(attachment_list, list):
                for item in attachment_list:
                    if item.get("storage_path"):
                        item["storage_path"] = self._get_signed_url(item["storage_path"])

            return self.success(attachment_list)
        except Exception as e:
            logger.error(f"获取附件列表失败: {str(e)}")
            return self.error(message=str(e))

    async def create_attachment(self):
        """创建附件

        Returns:
            创建结果
        """
        try:
            data = (await self.request.json()).get("data", {})
            if not data:
                return self.error(message="创建数据不能为空")
            result = await self.attachment_model.create_attachment(data)
            return self.success(result)
        except Exception as e:
            logger.error(f"创建附件失败: {str(e)}")
            return self.error(message=str(e))

    async def update_attachment(self):
        """更新附件

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
                result = await self.attachment_model.batch_update_attachment(ids, data)
                return self.success({"affected": result})
            else:
                # 单个更新
                attachment_id = data.get("id")
                if not attachment_id:
                    return self.error(message="附件ID不能为空")
                # 检查附件是否存在
                attachment = await self.attachment_model.get_attachment(attachment_id)
                if not attachment:
                    return self.error(code=404, message="附件不存在")
                result = await self.attachment_model.update_attachment(attachment_id, data)
                return self.success(result)
        except Exception as e:
            logger.error(f"更新附件失败: {str(e)}")
            return self.error(message=str(e))

    async def batch_update_attachments(self):
        """批量更新多个附件

        Returns:
            更新结果
        """
        try:
            data = (await self.request.json()).get("data", [])
            if not data or not isinstance(data, list):
                return self.error(message="更新数据不能为空且必须是数组格式")

            success_count = 0
            for item in data:
                attachment_id = item.get("id")
                if attachment_id:
                    await self.attachment_model.update_attachment(attachment_id, item)
                    success_count += 1

            return self.success({"affected": success_count})
        except Exception as e:
            logger.error(f"批量更新附件失败: {str(e)}")
            return self.error(message=str(e))

    async def delete_attachment(self):
        """删除附件

        Returns:
            删除结果
        """
        try:
            data = (await self.request.json()).get("data", {})
            if not data or not data.get("id"):
                return self.error(message="附件ID不能为空")
            attachment_id = data.get("id")
            # 检查附件是否存在
            attachment = await self.attachment_model.get_attachment(attachment_id)
            if not attachment:
                return self.error(code=404, message="附件不存在")
            await self.attachment_model.delete_attachment(attachment_id)
            return self.success()
        except Exception as e:
            logger.error(f"删除附件失败: {str(e)}")
            return self.error(message=str(e))

    async def destroy_attachment(self):
        """物理删除附件

        Returns:
            删除结果
        """
        try:
            data = (await self.request.json()).get("data", {})
            if not data or not data.get("id"):
                return self.error(message="附件ID不能为空")
            attachment_id = data.get("id")
            await self.attachment_model.destroy_attachment(attachment_id)
            return self.success()
        except Exception as e:
            logger.error(f"物理删除附件失败: {str(e)}")
            return self.error(message=str(e))

    async def batch_all_attachment(self):
        """删除所有符合筛选条件的附件

        Returns:
            删除结果
        """
        try:
            data = await self.request.json()
            result = await self.attachment_model.batch_all_attachment(data)
            return self.success({"affected": result})
        except Exception as e:
            logger.error(f"批量删除失败: {str(e)}")
            return self.error(message=str(e))

    async def batch_attachment(self):
        """批量删除指定ID的附件

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
            result = await self.attachment_model.batch_attachment(data)
            return self.success({"affected": result})
        except Exception as e:
            logger.error(f"批量删除失败: {str(e)}")
            return self.error(message=str(e))

    async def upload_attachment(self):
        """上传附件

        Returns:
            上传结果
        """
        try:
            # 从请求中获取文件
            form_data = await self.request.form()
            file = form_data.get("file")
            if not file:
                return self.error(message="文件不能为空")

            # 从表单数据中获取其他参数
            description = form_data.get("description", None)
            access_permission = form_data.get("access_permission", "private")
            module = form_data.get("module", None)

            # 生成文件ID和文件名
            file_id = uuid.uuid4().hex
            filename = file.filename

            # 计算文件大小
            file.file.seek(0, 2)  # 移动到文件末尾
            file_size = file.file.tell()  # 获取文件大小
            file.file.seek(0)  # 重置文件指针到开头

            file_type = file.content_type or "application/octet-stream"

            # 从配置文件中获取七牛云配置
            qiniu_access_key = self.config.get("QINIU_ACCESS_KEY", "")
            qiniu_secret_key = self.config.get("QINIU_SECRET_KEY", "")
            qiniu_bucket_name = self.config.get("QINIU_BUCKET_NAME", "")
            qiniu_domain = self.config.get("QINIU_DOMAIN", "")

            logger.debug(f"Qiniu config: ak={qiniu_access_key[:5] if qiniu_access_key else 'EMPTY'}... bucket={qiniu_bucket_name}")

            if not qiniu_access_key or not qiniu_secret_key or not qiniu_bucket_name:
                logger.error(f"Qiniu配置不完整: ak={bool(qiniu_access_key)}, sk={bool(qiniu_secret_key)}, bucket={bool(qiniu_bucket_name)}")
                return self.error(message="Qiniu配置不完整")

            # 生成七牛云上传token
            auth = qiniu.Auth(qiniu_access_key, qiniu_secret_key)
            key = f'{datetime.now().strftime("%Y%m%d")}/{file_id}_{filename}'
            token = auth.upload_token(qiniu_bucket_name, key)

            # 上传文件到七牛云
            # 先保存临时文件
            import os
            import tempfile

            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                shutil.copyfileobj(file.file, temp_file)
                temp_file_path = temp_file.name

            # 上传到七牛云
            ret, info = qiniu.put_file(token, key, temp_file_path, mime_type=file_type)

            # 删除临时文件
            os.unlink(temp_file_path)

            if ret:
                # 构建七牛云存储路径（只存储key，不存储带签名的URL）
                storage_path = key

                # 构建附件数据
                attachment_data = {
                    "filename": filename,
                    "storage_path": storage_path,
                    "file_size": file_size,
                    "file_type": file_type,
                    "upload_user_id": 1,  # 实际应该从登录用户获取
                    "description": description,
                    "access_permission": access_permission,
                    "module": module,
                }

                new_attachment = await self.attachment_model.create_attachment(attachment_data)

                if not new_attachment:
                    return self.error(message="上传失败")

                # 生成带签名的URL返回给前端
                signed_url = self._get_signed_url(storage_path)
                new_attachment["storage_path"] = signed_url
                new_attachment["key"] = key
                return self.success(new_attachment, message="上传成功")
            else:
                return self.error(message=f"七牛云上传失败: {info}")
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            exc_type = type(e).__name__
            logger.error(f"upload_attachment failed [{exc_type}]: {str(e)}\n{tb}")
            return self.error(message=f"上传失败: {str(e)}")

    async def download_attachment(self, attachment_id: int):
        """下载附件

        Returns:
            下载链接
        """
        try:
            # 获取附件信息
            attachment = await self.attachment_model.get_attachment(attachment_id)
            if not attachment:
                return self.error(code=404, message="附件不存在")

            # 从存储路径中获取key（现在数据库中存储的就是key）
            storage_key = attachment.get("storage_path", "")
            if not storage_key:
                return self.error(message="附件存储路径不存在")

            # 生成带签名的下载URL，过期时间3600秒
            private_url = self._get_signed_url(storage_key, expires=3600)

            return self.success({"url": private_url})
        except Exception as e:
            logger.error(f"获取下载链接失败: {str(e)}")
            return self.error(message=str(e))

    async def preview_attachment(self, attachment_id: int):
        """预览附件

        Returns:
            预览链接
        """
        try:
            # 获取附件信息
            attachment = await self.attachment_model.get_attachment(attachment_id)
            if not attachment:
                return self.error(code=404, message="附件不存在")

            # 从存储路径中获取key（现在数据库中存储的就是key）
            storage_key = attachment.get("storage_path", "")
            if not storage_key:
                return self.error(message="附件存储路径不存在")

            # 生成带签名的预览URL，过期时间3600秒
            private_url = self._get_signed_url(storage_key, expires=3600)

            return self.success({"url": private_url})
        except Exception as e:
            logger.error(f"获取预览链接失败: {str(e)}")
            return self.error(message=str(e))

    async def update_attachment_by_data_id(self):
        """根据data_id更新附件

        Returns:
            更新结果
        """
        try:
            data = (await self.request.json()).get("data", {})
            if not data:
                return self.error(message="更新数据不能为空")

            data_id = data.get("data_id")
            module = data.get("module")

            if not data_id:
                return self.error(message="data_id不能为空")

            if not module:
                return self.error(message="module不能为空")

            # 构建更新数据
            update_data = {"module": module}

            # 构建过滤条件
            filter_conditions = [
                {
                    "group_logic": "and",
                    "condition_logic": "and",
                    "conditions": [{"field": "data_id", "operator": "eq", "value": data_id}],
                }
            ]

            # 执行更新
            result = await self.attachment_model.update(filter=filter_conditions, data=update_data)

            return self.success({"affected": result})
        except Exception as e:
            logger.error(f"根据data_id更新附件失败: {str(e)}")
            return self.error(message=str(e))
