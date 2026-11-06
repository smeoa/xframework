from framework.core.model import Model


class DemoModel(Model):
    """demo 示例模型：新模块复制本文件后改表名与字段即可"""

    def __init__(self):
        super().__init__("demo")

    async def get_demo_list(self, data):
        """分页查询列表（keyword 模糊匹配 name/description）"""
        page = data.get("page", 1)
        limit = data.get("limit", 20)
        keyword = data.get("keyword", "")
        filter_conditions = data.get("filter", [])
        sort_rules = data.get("sort", [])

        base_filter = [
            {
                "group_logic": "and",
                "condition_logic": "and",
                "conditions": [{"field": "is_deleted", "operator": "eq", "value": 0}],
            }
        ]

        if keyword:
            base_filter.append(
                {
                    "group_logic": "and",
                    "condition_logic": "or",
                    "conditions": [
                        {"field": "name", "operator": "contains", "value": keyword},
                        {"field": "description", "operator": "contains", "value": keyword},
                    ],
                }
            )

        if filter_conditions:
            base_filter.extend(filter_conditions)

        return await self.get_list(
            fields="id, data_id, name, description, sort, status, create_time, update_time, remark",
            filter=base_filter,
            sort_rules=sort_rules if sort_rules else [{"field": "sort", "direction": "asc"}, {"field": "id", "direction": "asc"}],
            limit=limit,
            page=page,
        )

    async def get_demo(self, demo_id):
        filter_conditions = [
            {
                "group_logic": "and",
                "condition_logic": "and",
                "conditions": [
                    {"field": "id", "operator": "eq", "value": demo_id},
                    {"field": "is_deleted", "operator": "eq", "value": 0},
                ],
            }
        ]
        items = await self.get_list(filter=filter_conditions)
        if isinstance(items, dict) and "items" in items:
            items = items["items"]
        return items[0] if items else None

    async def create_demo(self, data):
        demo_id = await self.create(
            {
                "name": data.get("name"),
                "description": data.get("description", ""),
                "sort": data.get("sort", 0),
                "status": data.get("status", 1),
                "remark": data.get("remark", ""),
                "create_by": data.get("create_by", 0),
                "update_by": data.get("update_by", 0),
                "is_deleted": 0,
            }
        )
        return {"id": demo_id}

    async def update_demo(self, demo_id, data):
        update_data = {
            "name": data.get("name"),
            "description": data.get("description"),
            "sort": data.get("sort"),
            "status": data.get("status"),
            "remark": data.get("remark"),
            "update_by": data.get("update_by"),
        }
        update_data = {k: v for k, v in update_data.items() if v is not None}
        await self.update_by_id(demo_id, update_data)
        return await self.get_demo(demo_id)

    async def delete_demo(self, demo_id):
        """软删除"""
        await self.update_by_id(demo_id, {"is_deleted": 1})

    async def destroy_demo(self, demo_id):
        """物理删除"""
        await self.destroy_by_id(demo_id)

    async def batch_demo(self, data):
        """批量软删除指定 ID"""
        ids = data.get("ids", [])
        if not ids:
            return 0
        filter_conditions = [
            {
                "group_logic": "and",
                "condition_logic": "and",
                "conditions": [{"field": "id", "operator": "in", "value": ids}],
            }
        ]
        return await self.update({"is_deleted": 1}, filter_conditions)
