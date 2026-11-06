from framework.core.model import Model
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AttachmentModel(Model):
    def __init__(self):
        super().__init__("attachment")

    async def get_attachment(self, attachment_id):
        """获取单个附件

        Args:
            attachment_id: 附件ID

        Returns:
            附件信息
        """
        try:
            # 基础过滤条件（排除已软删除的附件）
            filter = [
                {
                    "group_logic": "and",
                    "condition_logic": "and",
                    "conditions": [
                        {"field": "id", "operator": "eq", "value": attachment_id},
                        {"field": "is_deleted", "operator": "eq", "value": 0},
                    ],
                }
            ]

            attachments = await self.get_list(filter=filter)
            if attachments:
                return attachments[0]
            else:
                return None
        except Exception as e:
            logger.error(f"获取附件失败: {str(e)}")
            return None

    async def get_attachment_list(self, request):
        """获取附件列表

        Args:
            request: 请求对象

        Returns:
            附件列表
        """
        try:
            # 从请求中获取参数
            try:
                request_data = await request.json()
            except:
                # 处理GET请求的查询参数
                request_data = {}
                # 从query参数中获取数据
                if hasattr(request, "query_params"):
                    request_data["page"] = int(request.query_params.get("page", 1))
                    request_data["limit"] = int(request.query_params.get("limit", 10))
                    request_data["keyword"] = request.query_params.get("keyword", "")
                    request_data["file_type"] = request.query_params.get("file_type", "")

            # 提取参数
            page = request_data.get("page", 1)
            limit = request_data.get("limit", 10)
            keyword = request_data.get("keyword", "")
            file_type = request_data.get("file_type", "")
            filter_conditions = request_data.get("filter", [])
            sort_rules = request_data.get("sort", [])
            searchFields = request_data.get("searchFields", [])

            # 基础过滤条件（排除已软删除的附件）
            base_filter = [
                {
                    "group_logic": "and",
                    "condition_logic": "and",
                    "conditions": [
                        {"field": "is_deleted", "operator": "eq", "value": 0},
                        {"field": "status", "operator": "ne", "value": "deleted"},
                    ],
                }
            ]

            # 添加文件类型过滤
            if file_type:
                base_filter.append(
                    {
                        "group_logic": "and",
                        "condition_logic": "and",
                        "conditions": [{"field": "file_type", "operator": "eq", "value": file_type}],
                    }
                )

            # 添加搜索条件
            if keyword:
                # 构建搜索条件
                search_conditions = []

                # 如果有指定搜索字段，只搜索这些字段
                if searchFields and len(searchFields) > 0:
                    for field in searchFields:
                        # 对于ID字段，使用类型转换后进行contains搜索
                        if field == "id":
                            # 使用类型转换，将ID转换为字符串后进行LIKE搜索
                            search_conditions.append(
                                {
                                    "field": f"CAST({field} AS TEXT)",
                                    "operator": "contains",
                                    "value": keyword,
                                }
                            )
                        else:
                            search_conditions.append(
                                {
                                    "field": field,
                                    "operator": "contains",
                                    "value": keyword,
                                }
                            )
                else:
                    # 默认搜索字段
                    search_conditions = [
                        {"field": "filename", "operator": "contains", "value": keyword},
                        {
                            "field": "description",
                            "operator": "contains",
                            "value": keyword,
                        },
                    ]

                if search_conditions:
                    base_filter.append(
                        {
                            "group_logic": "and",
                            "condition_logic": "or",
                            "conditions": search_conditions,
                        }
                    )

            # 合并传入的过滤条件
            if filter_conditions:
                base_filter.extend(filter_conditions)

            # 构建排序规则
            if not sort_rules:
                sort_rules = [{"field": "upload_time", "direction": "desc"}]

            # 获取附件列表
            attachment_list = await self.get_list(
                filter=base_filter,
                page=page,
                limit=limit,
                sort_rules=sort_rules,
                fields="*",
            )

            return attachment_list
        except Exception as e:
            logger.error(f"获取附件列表失败: {str(e)}")
            return {"items": [], "total": 0}

    async def create_attachment(self, data):
        """创建附件

        Args:
            data: 附件数据

        Returns:
            创建结果
        """
        # 确保数据包含必要字段
        if "upload_time" not in data:
            data["upload_time"] = datetime.now()
        if "status" not in data:
            data["status"] = "normal"
        if "access_permission" not in data:
            data["access_permission"] = "private"
        # 创建附件
        attachment_id = await self.create(data)
        # 获取完整的附件信息，包括data_id
        attachment = await self.get_attachment(attachment_id)
        if attachment:
            return {
                "id": attachment_id,
                "filename": data.get("filename"),
                "storage_path": data.get("storage_path"),
                "data_id": attachment.get("data_id"),
            }
        return {
            "id": attachment_id,
            "filename": data.get("filename"),
            "storage_path": data.get("storage_path"),
        }

    async def update_attachment(self, attachment_id, data):
        """更新附件

        Args:
            attachment_id: 附件ID
            data: 更新数据

        Returns:
            更新结果
        """
        # 更新附件
        await self.update_by_id(attachment_id, data)
        # 返回更新后的附件信息
        return await self.get_attachment(attachment_id)

    async def delete_attachment(self, attachment_id):
        """删除附件

        Args:
            attachment_id: 附件ID
        """
        try:
            # 软删除附件
            await self.update_by_id(attachment_id, {"is_deleted": 1})
        except Exception as e:
            # 数据库表不存在时忽略错误
            logger.error(f"删除附件失败: {str(e)}")

    async def destroy_attachment(self, attachment_id):
        """物理删除附件

        Args:
            attachment_id: 附件ID
        """
        try:
            # 物理删除附件
            await self.destroy_by_id(attachment_id)
        except Exception as e:
            # 数据库表不存在时忽略错误
            logger.error(f"物理删除附件失败: {str(e)}")

    async def batch_all_attachment(self, data):
        """删除所有符合筛选条件的附件

        Args:
            data: 包含过滤条件的数据

        Returns:
            删除的记录数
        """
        # 获取过滤条件
        raw_filter = data.get("filter", [])
        # 获取搜索关键词
        keyword = data.get("keyword", "")
        # 获取搜索字段
        searchFields = data.get("searchFields", [])

        # 处理过滤条件格式
        processed_filter = []
        for group in raw_filter:
            if isinstance(group, dict):
                # 转换用户提供的格式到内部格式
                group_logic = group.get("group_logic", group.get("groupLogic", "and"))
                condition_logic = group.get("condition_logic", group.get("condLogic", "and"))
                conditions = group.get("conditions", group.get("cond", []))
                # 处理conditions
                processed_conditions = []
                for condition in conditions:
                    if isinstance(condition, dict):
                        processed_conditions.append(
                            {
                                "field": condition.get("field"),
                                "operator": condition.get("operator", condition.get("method")),
                                "value": condition.get("value"),
                            }
                        )
                processed_filter.append(
                    {
                        "group_logic": group_logic,
                        "condition_logic": condition_logic,
                        "conditions": processed_conditions,
                    }
                )

        # 处理搜索关键词
        if keyword and searchFields:
            search_conditions = []
            for field in searchFields:
                search_conditions.append({"field": field, "operator": "contains", "value": keyword})
            if search_conditions:
                # 添加搜索条件到过滤条件中
                if not processed_filter:
                    processed_filter = []
                # 创建一个新的过滤组用于搜索条件
                search_group = {
                    "group_logic": "and",
                    "condition_logic": "or",
                    "conditions": search_conditions,
                }
                processed_filter.append(search_group)

        # 验证过滤条件
        if not processed_filter:
            return 0

        # 批量删除
        return await self.delete(filter=processed_filter)

    async def batch_attachment(self, data):
        """批量删除指定ID的附件

        Args:
            data: 包含ID列表的数据

        Returns:
            删除的记录数
        """
        # 直接从请求体中获取ids参数
        ids = data.get("ids", [])

        # 验证ID列表
        if not ids:
            return 0

        # 构建过滤条件
        # 使用单个group，包含所有ID的in条件
        filter_conditions = [
            {
                "group_logic": "and",
                "condition_logic": "and",
                "conditions": [{"field": "id", "operator": "in", "value": ids}],
            }
        ]

        # 批量删除
        return await self.delete(filter=filter_conditions)

    async def batch_update_attachment(self, ids, data):
        """批量更新指定ID的附件

        Args:
            ids: 要更新的附件ID列表
            data: 包含更新数据的字典

        Returns:
            更新的记录数
        """
        if not ids:
            return 0

        # 移除ids字段，只保留要更新的字段
        update_data = {k: v for k, v in data.items() if k != "ids"}
        if not update_data:
            return 0

        # 构建过滤条件
        filter_conditions = [
            {
                "group_logic": "and",
                "condition_logic": "and",
                "conditions": [{"field": "id", "operator": "in", "value": ids}],
            }
        ]

        # 批量更新
        return await self.update(filter=filter_conditions, data=update_data)
