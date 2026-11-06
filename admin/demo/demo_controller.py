from fastapi import Request
from framework.core.controller import Controller
from .demo_model import DemoModel
import logging

logger = logging.getLogger(__name__)


class DemoController(Controller):
    """demo 示例控制器"""

    def __init__(self, request: Request):
        super().__init__(request)
        self.model = DemoModel()

    async def get_demo_list(self):
        try:
            data = await self.request.json()
            result = await self.model.get_demo_list(data)
            return self.success(result)
        except Exception as e:
            logger.error(f"获取demo列表失败: {str(e)}")
            return self.error(message=str(e))

    async def get_demo(self):
        try:
            data = (await self.request.json()).get("data", {})
            demo_id = data.get("id")
            if not demo_id:
                return self.error(message="ID不能为空")
            result = await self.model.get_demo(demo_id)
            if not result:
                return self.error(code=404, message="数据不存在")
            return self.success(result)
        except Exception as e:
            logger.error(f"获取demo详情失败: {str(e)}")
            return self.error(message=str(e))

    async def create_demo(self):
        try:
            data = (await self.request.json()).get("data", {})
            if not data or not data.get("name"):
                return self.error(message="name不能为空")
            result = await self.model.create_demo(data)
            return self.success(result)
        except Exception as e:
            logger.error(f"创建demo失败: {str(e)}")
            return self.error(message=str(e))

    async def update_demo(self):
        try:
            data = (await self.request.json()).get("data", {})
            demo_id = data.get("id")
            if not demo_id:
                return self.error(message="ID不能为空")
            result = await self.model.update_demo(demo_id, data)
            if not result:
                return self.error(code=404, message="数据不存在")
            return self.success(result)
        except Exception as e:
            logger.error(f"更新demo失败: {str(e)}")
            return self.error(message=str(e))

    async def delete_demo(self):
        try:
            data = (await self.request.json()).get("data", {})
            demo_id = data.get("id")
            if not demo_id:
                return self.error(message="ID不能为空")
            await self.model.delete_demo(demo_id)
            return self.success()
        except Exception as e:
            logger.error(f"删除demo失败: {str(e)}")
            return self.error(message=str(e))

    async def destroy_demo(self):
        try:
            data = (await self.request.json()).get("data", {})
            demo_id = data.get("id")
            if not demo_id:
                return self.error(message="ID不能为空")
            await self.model.destroy_demo(demo_id)
            return self.success()
        except Exception as e:
            logger.error(f"物理删除demo失败: {str(e)}")
            return self.error(message=str(e))

    async def batch_demo(self):
        try:
            data = await self.request.json()
            affected = await self.model.batch_demo(data)
            return self.success({"affected": affected})
        except Exception as e:
            logger.error(f"批量删除demo失败: {str(e)}")
            return self.error(message=str(e))
