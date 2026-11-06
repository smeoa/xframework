from framework.core.model import Model
from framework.core.function import build_export_filename


class MenuModel(Model):
    def __init__(self):
        super().__init__("menu")

    async def get_menu_tree(self, parent_id=None):
        menus = await self.get_list(
            fields="id, name, pid, path, component, icon, sort, type, permission, status",
            filter=[
                {
                    "group_logic": "and",
                    "condition_logic": "and",
                    "conditions": [{"field": "is_deleted", "operator": "eq", "value": 0}],
                }
            ],
            sort_rules=[{"field": "sort", "direction": "asc"}, {"field": "id", "direction": "asc"}],
        )

        if isinstance(menus, dict) and "items" in menus:
            menus = menus["items"]

        menu_dict = {menu["id"]: menu for menu in menus}
        menu_tree = []

        for menu in menus:
            menu_id = menu["id"]
            pid = menu["pid"]

            if "children" not in menu:
                menu["children"] = []

            if pid is None or pid == 0:
                menu_tree.append(menu)
            elif pid in menu_dict:
                if "children" not in menu_dict[pid]:
                    menu_dict[pid]["children"] = []
                menu_dict[pid]["children"].append(menu)

        return menu_tree

    async def get_user_menu_tree(self, permissions, admin=False):
        """获取当前登录用户可见的菜单树

        菜单 permission 为空表示对所有登录用户可见；非空时必须命中用户权限码。
        管理员返回全量菜单。

        Args:
            permissions: 当前用户权限码列表
            admin: 是否为管理员

        Returns:
            过滤后的菜单树
        """
        menu_tree = await self.get_menu_tree()
        if admin:
            return menu_tree
        return self._filter_menu_tree(menu_tree, set(permissions or []))

    def _filter_menu_tree(self, nodes, owned):
        """按权限码递归过滤菜单树

        规则：
        - 目录节点（type=1 且存在子菜单）本身不参与权限码判定，只要还有可见子菜单即保留，
          避免只授予子菜单权限时父目录不可见；
        - 菜单/叶子节点 permission 为空表示对所有登录用户可见，非空时必须命中用户权限码；
        - 目录下无任何可见子菜单时一并隐藏。

        Args:
            nodes: 菜单节点列表
            owned: 用户拥有的权限码集合

        Returns:
            过滤后的菜单节点列表
        """
        result = []
        for node in nodes:
            children = node.get("children") or []
            kept_children = self._filter_menu_tree(children, owned)
            is_directory = node.get("type") == 1 and bool(children)
            if is_directory:
                if not kept_children:
                    continue
            else:
                code = node.get("permission")
                if code and code not in owned:
                    continue
            filtered = dict(node)
            filtered["children"] = kept_children
            result.append(filtered)
        return result

    async def get_menu_list(self, data):
        page = data.get("page", 1)
        limit = data.get("limit", 20)
        keyword = data.get("keyword", "")
        menu_id = data.get("menu_id")
        filter_conditions = data.get("filter", [])
        sort_rules = data.get("sort", [])

        base_filter = [
            {
                "group_logic": "and",
                "condition_logic": "and",
                "conditions": [{"field": "is_deleted", "operator": "eq", "value": 0}],
            }
        ]

        if menu_id:
            base_filter[0]["conditions"].append({"field": "pid", "operator": "eq", "value": menu_id})

        if keyword:
            base_filter.append(
                {
                    "group_logic": "and",
                    "condition_logic": "or",
                    "conditions": [
                        {"field": "name", "operator": "contains", "value": keyword},
                        {"field": "path", "operator": "contains", "value": keyword},
                        {"field": "component", "operator": "contains", "value": keyword},
                    ],
                }
            )

        if filter_conditions:
            base_filter.extend(filter_conditions)

        menu_list = await self.get_list(
            fields="id, name, pid, path, component, icon, sort, type, permission, status, create_time, update_time",
            filter=base_filter,
            sort_rules=sort_rules if sort_rules else [{"field": "sort", "direction": "asc"}, {"field": "id", "direction": "asc"}],
            limit=limit,
            page=page,
        )

        if isinstance(menu_list, dict) and "items" in menu_list:
            for item in menu_list["items"]:
                item["pid"] = item.get("pid", 0)
                item["sort"] = item.get("sort", 0)
                item["type"] = item.get("type", 1)
                item["status"] = item.get("status", 1)

        return menu_list

    async def create_menu(self, data):
        create_data = {
            "title": data.get("title", data.get("name")),
            "name": data.get("name"),
            "pid": data.get("pid", 0),
            "path": data.get("path", ""),
            "component": data.get("component", ""),
            "icon": data.get("icon", ""),
            "sort": data.get("sort", 0),
            "type": data.get("type", 1),
            "permission": data.get("permission", ""),
            "status": data.get("status", 1),
            "create_by": data.get("create_by", 1),
            "update_by": data.get("update_by", 1),
            "is_deleted": 0,
        }

        menu_id = await self.create(create_data)
        return {"id": menu_id, "name": data.get("name")}

    async def update_menu(self, menu_id, data):
        update_data = {
            "name": data.get("name"),
            "pid": data.get("pid"),
            "path": data.get("path"),
            "component": data.get("component"),
            "icon": data.get("icon"),
            "sort": data.get("sort"),
            "type": data.get("type"),
            "permission": data.get("permission"),
            "status": data.get("status"),
            "update_by": data.get("update_by", 1),
        }

        update_data = {k: v for k, v in update_data.items() if v is not None}

        await self.update_by_id(menu_id, update_data)
        return await self.get_menu(menu_id)

    async def get_menu(self, menu_id):
        filter_conditions = [
            {
                "group_logic": "and",
                "condition_logic": "and",
                "conditions": [{"field": "id", "operator": "eq", "value": menu_id}],
            }
        ]

        menus = await self.get_list(filter=filter_conditions)
        if isinstance(menus, dict) and "items" in menus:
            menus = menus["items"]
        return menus[0] if menus else None

    async def delete_menu(self, menu_id):
        await self.update_by_id(menu_id, {"is_deleted": 1})

    async def destroy_menu(self, menu_id):
        await self.destroy_by_id(menu_id)

    async def batch_all_menu(self, data):
        raw_filter = data.get("filter", [])
        keyword = data.get("keyword", "")
        search_fields = data.get("searchFields", [])

        processed_filter = []
        for group in raw_filter:
            if isinstance(group, dict):
                group_logic = group.get("group_logic", group.get("groupLogic", "and"))
                condition_logic = group.get("condition_logic", group.get("condLogic", "and"))
                conditions = group.get("conditions", group.get("cond", []))
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
                    {"group_logic": group_logic, "condition_logic": condition_logic, "conditions": processed_conditions}
                )

        if keyword and search_fields:
            search_conditions = []
            for field in search_fields:
                search_conditions.append({"field": field, "operator": "contains", "value": keyword})
            if search_conditions:
                search_group = {"group_logic": "and", "condition_logic": "or", "conditions": search_conditions}
                processed_filter.append(search_group)

        if not processed_filter:
            return 0

        return await self.delete(filter=processed_filter)

    async def batch_menu(self, data):
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

        return await self.delete(filter=filter_conditions)

    async def batch_update_menu(self, ids, data):
        if not ids:
            return 0

        update_data = {k: v for k, v in data.items() if k != "ids"}
        if not update_data:
            return 0

        filter_conditions = [
            {
                "group_logic": "and",
                "condition_logic": "and",
                "conditions": [{"field": "id", "operator": "in", "value": ids}],
            }
        ]

        return await self.update(filter=filter_conditions, data=update_data)

    async def export_menu(self, data):
        try:
            from openpyxl import Workbook
            from openpyxl.utils import get_column_letter
            from io import BytesIO

            raw_filter = data.get("filter", [])
            keyword = data.get("keyword", "")
            search_fields = data.get("searchFields", [])
            sort = data.get("sort", [])

            processed_filter = []
            for group in raw_filter:
                if isinstance(group, dict):
                    group_logic = group.get("group_logic", group.get("groupLogic", "and"))
                    condition_logic = group.get("condition_logic", group.get("condLogic", "and"))
                    conditions = group.get("conditions", group.get("cond", []))
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
                        {"group_logic": group_logic, "condition_logic": condition_logic, "conditions": processed_conditions}
                    )

            if keyword and search_fields:
                search_conditions = []
                for field in search_fields:
                    search_conditions.append({"field": field, "operator": "contains", "value": keyword})
                if search_conditions:
                    search_group = {"group_logic": "and", "condition_logic": "or", "conditions": search_conditions}
                    processed_filter.append(search_group)

            ids = data.get("ids", [])
            if ids:
                if not processed_filter:
                    processed_filter = []
                id_filter = {
                    "group_logic": "and",
                    "condition_logic": "and",
                    "conditions": [{"field": "id", "operator": "in", "value": ids}],
                }
                processed_filter.append(id_filter)

            items = await self.get_list(fields="*", filter=processed_filter, sort_rules=sort)

            if isinstance(items, dict) and "items" in items:
                data_items = items.get("items", [])
            else:
                data_items = items if isinstance(items, list) else []

            wb = Workbook()
            ws = wb.active
            ws.title = "菜单数据"

            headers = {
                "id": "ID",
                "name": "菜单名称",
                "pid": "上级菜单ID",
                "path": "路径",
                "component": "组件",
                "icon": "图标",
                "sort": "排序",
                "type": "类型",
                "permission": "权限",
                "status": "状态",
                "create_time": "创建时间",
                "update_time": "更新时间",
            }

            header_keys = list(headers.keys())
            for col_idx, key in enumerate(header_keys, 1):
                col_letter = get_column_letter(col_idx)
                ws[f"{col_letter}1"] = headers[key]

            for row_idx, item in enumerate(data_items, 2):
                for col_idx, key in enumerate(header_keys, 1):
                    col_letter = get_column_letter(col_idx)
                    value = item.get(key)
                    if key == "type":
                        ws[f"{col_letter}{row_idx}"] = "目录" if value == 1 else ("菜单" if value == 2 else "按钮")
                    elif key == "status":
                        ws[f"{col_letter}{row_idx}"] = "启用" if value else "禁用"
                    else:
                        ws[f"{col_letter}{row_idx}"] = value or ""

            for col_idx, key in enumerate(header_keys, 1):
                col_letter = get_column_letter(col_idx)
                ws.column_dimensions[col_letter].width = 15

            output = BytesIO()
            wb.save(output)
            output.seek(0)

            filename = build_export_filename("菜单列表")
            file_size = len(output.getvalue())

            return {"filename": filename, "size": file_size, "message": "导出成功", "data": output.getvalue()}
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"导出失败: {str(e)}")
            raise

    async def import_menu(self, file, import_mode, field_mapping):
        try:
            from openpyxl import load_workbook
            from io import BytesIO

            wb = load_workbook(BytesIO(await file.read()))
            ws = wb.active

            headers = []
            for cell in ws[1]:
                headers.append(cell.value)

            data = []
            for row in ws.iter_rows(min_row=2):
                row_data = {}
                for idx, cell in enumerate(row):
                    if idx < len(headers):
                        column_key = f"column{idx + 1}"
                        row_data[column_key] = cell.value
                data.append(row_data)

            success = 0
            failure = 0
            errors = []

            for row_idx, row in enumerate(data, 2):
                try:
                    menu_data = {}

                    for field, column in field_mapping.items():
                        if column and column in row:
                            value = row[column]
                            if field == "status":
                                if isinstance(value, str):
                                    menu_data[field] = value == "启用" or value == "1" or value.lower() == "true"
                                else:
                                    menu_data[field] = bool(value)
                            elif field == "type":
                                if isinstance(value, str):
                                    type_map = {"目录": 1, "菜单": 2, "按钮": 3}
                                    menu_data[field] = type_map.get(value, 1)
                                else:
                                    menu_data[field] = int(value) if value else 1
                            else:
                                menu_data[field] = value

                    if not menu_data:
                        failure += 1
                        errors.append({"row": row_idx, "data": row, "message": "没有可导入的有效数据"})
                        continue

                    if "title" not in menu_data:
                        menu_data["title"] = menu_data.get("name", "")

                    if import_mode == "insert":
                        try:
                            await self.create(menu_data)
                            success += 1
                        except Exception as e:
                            failure += 1
                            errors.append({"row": row_idx, "data": row, "message": f"新增失败: {str(e)}"})
                    elif import_mode == "update":
                        if "id" in menu_data and menu_data["id"]:
                            try:
                                await self.update_by_id(menu_data["id"], menu_data)
                                success += 1
                            except Exception as e:
                                failure += 1
                                errors.append({"row": row_idx, "data": row, "message": f"更新失败: {str(e)}"})
                        else:
                            failure += 1
                            errors.append({"row": row_idx, "data": row, "message": "更新模式需要ID字段"})
                    elif import_mode == "insert_update":
                        if "id" in menu_data and menu_data["id"]:
                            try:
                                await self.update_by_id(menu_data["id"], menu_data)
                                success += 1
                            except Exception:
                                try:
                                    await self.create(menu_data)
                                    success += 1
                                except Exception as e:
                                    failure += 1
                                    errors.append({"row": row_idx, "data": row, "message": f"更新和新增都失败: {str(e)}"})
                        else:
                            try:
                                await self.create(menu_data)
                                success += 1
                            except Exception as e:
                                failure += 1
                                errors.append({"row": row_idx, "data": row, "message": f"新增失败: {str(e)}"})
                    else:
                        failure += 1
                        errors.append({"row": row_idx, "data": row, "message": f"不支持的导入模式: {import_mode}"})
                except Exception as e:
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.error(f"导入数据失败 (第{row_idx}行): {str(e)}")
                    failure += 1
                    errors.append({"row": row_idx, "data": row, "message": str(e)})

            return {"success": success, "failure": failure, "total": len(data), "errors": errors}
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"导入失败: {str(e)}")
            raise