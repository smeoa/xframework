import framework
from framework.core.model import Model
from framework.core.function import build_tree, build_export_filename


class OrganizationModel(Model):

    def __init__(self):
        super().__init__("dept")
        # 显式设置 foreign_key_fields 为空列表，避免系统尝试访问不存在的 dept_id 字段
        self.foreign_key_fields = []
        self.user_model = Model("user")
        # 为 user_model 设置外键字段映射
        self.user_model.foreign_key_fields = [
            {
                "field": "dept_id",
                "ref_table": "dept",
                "ref_field": "id",
                "alias_field": "dept_name",
                "display_field": "name",
            },
        ]
        self.role_model = Model("role")
        # 显式设置 foreign_key_fields 为空列表，避免系统尝试访问不存在的外键字段
        self.role_model.foreign_key_fields = []
        self.user_role_model = Model("user_role")  # 用户角色关联表
        # 显式设置 foreign_key_fields 为空列表，避免系统尝试访问不存在的外键字段
        self.user_role_model.foreign_key_fields = []
        self.permission_model = Model("permission")  # 权限点表
        self.permission_model.foreign_key_fields = []
        self.role_permission_model = Model("role_permission")  # 角色权限关联表
        self.role_permission_model.foreign_key_fields = []

    async def get_dept_tree(self, request):
        """获取部门树形结构

        Args:
            request: 请求对象

        Returns:
            部门树形结构
        """
        filter = [
            {
                "group_logic": "and",
                "condition_logic": "and",
                "conditions": [{"field": "is_deleted", "operator": "eq", "value": 0}],
            }
        ]
        # 按 sort 升序返回，保证拖拽调整排序后的顺序与前端展示一致
        depts = await self.get_list(
            filter=filter,
            fields="id, pid, name, code, status, sort",
            sort_rules=[
                {"field": "sort", "direction": "asc"},
                {"field": "id", "direction": "asc"},
            ],
        )
        return build_tree(depts, parent_field="pid", id_field="id")

    async def get_user_list(self, request):
        """获取用户列表

        Args:
            request: 请求对象

        Returns:
            用户列表
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

            # 前端标准契约是 { data: {...} }，需先解包；顶层参数用于兼容 GET 回退分支
            data = request_data.get("data") or request_data

            # 提取参数
            page = data.get("page", 1)
            limit = data.get("limit", 10)
            keyword = data.get("keyword", "")
            dept_id = data.get("dept_id") or data.get("deptId")
            filter_conditions = data.get("filter", [])
            sort_rules = data.get("sort_rules") or data.get("sort", [])
            searchFields = data.get("search_fields") or data.get("searchFields", [])

            # 获取外键字段映射
            fk_field_map = {}
            if hasattr(self, 'foreign_key_fields') and self.foreign_key_fields:
                fk_field_map = {fk["field"]: fk["alias_field"] for fk in self.foreign_key_fields}

            # 基础过滤条件
            base_filter = [
                {
                    "group_logic": "and",
                    "condition_logic": "and",
                    "conditions": [{"field": "is_deleted", "operator": "eq", "value": 0}],
                }
            ]

            # 添加部门过滤条件
            if dept_id:
                base_filter.append(
                    {
                        "group_logic": "and",
                        "condition_logic": "and",
                        "conditions": [{"field": "dept_id", "operator": "eq", "value": dept_id}],
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
                            search_conditions.append(
                                {"field": f"CAST({field} AS TEXT)", "operator": "contains", "value": keyword}
                            )
                        # 对于外键字段，搜索关联表的显示字段
                        elif field in fk_field_map:
                            alias_field = fk_field_map[field]
                            search_conditions.append({"field": alias_field, "operator": "contains", "value": keyword})
                        else:
                            search_conditions.append({"field": field, "operator": "contains", "value": keyword})
                else:
                    # 默认搜索字段
                    search_conditions = [
                        {"field": "username", "operator": "contains", "value": keyword},
                        {"field": "name", "operator": "contains", "value": keyword},
                        {"field": "phone", "operator": "contains", "value": keyword},
                        {"field": "email", "operator": "contains", "value": keyword},
                    ]
                    # 添加外键字段的搜索
                    for field, alias_field in fk_field_map.items():
                        search_conditions.append({"field": alias_field, "operator": "contains", "value": keyword})

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

            # 获取用户列表
            pagination = await self.user_model.get_list(
                page=page,
                limit=limit,
                sort_rules=sort_rules or [{"field": "id", "direction": "asc"}],
                filter=base_filter,
                fields="*",
            )

            # 为每个用户添加部门名称
            if pagination.get("items"):
                for user in pagination["items"]:
                    dept_id = user.get("dept_id")
                    if dept_id:
                        # 获取部门信息
                        dept = await self.get_first(
                            filter=[
                                {
                                    "group_logic": "and",
                                    "condition_logic": "and",
                                    "conditions": [
                                        {
                                            "field": "id",
                                            "operator": "eq",
                                            "value": dept_id,
                                        }
                                    ],
                                }
                            ]
                        )
                        if dept:
                            user["dept_name"] = dept.get("name")
                        else:
                            user["dept_name"] = None
                    else:
                        user["dept_name"] = None

            return pagination
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"获取用户列表失败: {str(e)}")
            return {"items": [], "total": 0}

    async def create_dept(self, data):
        """创建部门

        Args:
            data: 部门数据

        Returns:
            创建结果
        """
        # 确保数据包含 title 字段
        if "title" not in data:
            data["title"] = data.get("name")
        # 从数据库创建部门
        dept_id = await self.create(data)
        return {"id": dept_id, "name": data.get("name")}

    async def update_dept(self, dept_id, data):
        """更新部门

        Args:
            dept_id: 部门ID
            data: 更新数据

        Returns:
            更新结果
        """
        # 从数据库更新部门
        await self.update_by_id(dept_id, data)
        # 返回更新后的部门信息
        return await self.get_dept(dept_id)

    async def get_dept(self, dept_id):
        """获取单个部门

        Args:
            dept_id: 部门ID

        Returns:
            部门信息
        """
        try:
            # 基础过滤条件
            filter = [
                {
                    "group_logic": "and",
                    "condition_logic": "and",
                    "conditions": [
                        {"field": "id", "operator": "eq", "value": dept_id},
                        {"field": "is_deleted", "operator": "eq", "value": 0},
                    ],
                }
            ]

            depts = await self.get_list(filter=filter, fields="*")
            if depts:
                return depts[0]
            else:
                return None
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"获取部门失败: {str(e)}")
            return None

    async def delete_dept(self, dept_id):
        """删除部门

        Args:
            dept_id: 部门ID
        """
        # 软删除部门
        await self.update_by_id(dept_id, {"is_deleted": 1})

    async def create_user(self, data):
        """创建用户

        Args:
            data: 用户数据

        Returns:
            创建结果
        """
        # 确保数据包含 title 字段
        if "title" not in data:
            data["title"] = data.get("name")

        # 保存原始数据中的 dept_id
        dept_id = data.get("dept_id")

        # 从数据库创建用户
        try:
            user_id = await self.user_model.create(data)
            return {"id": user_id, "name": data.get("name"), "username": data.get("username")}
        except Exception as e:
            # 如果 dept_id 字段不存在，尝试移除该字段后再创建
            if "dept_id" in data:
                del data["dept_id"]
                user_id = await self.user_model.create(data)
                # 尝试更新用户的 dept_id（如果表中有该字段）
                try:
                    if dept_id is not None:
                        await self.user_model.update_by_id(user_id, {"dept_id": dept_id})
                except Exception:
                    pass
                return {"id": user_id, "name": data.get("name"), "username": data.get("username")}
            raise e

    async def update_user(self, user_id, data):
        """更新用户

        Args:
            user_id: 用户ID
            data: 更新数据

        Returns:
            更新结果
        """
        # 从数据库更新用户
        await self.user_model.update_by_id(user_id, data)
        # 返回更新后的用户信息
        return await self.get_user(user_id)

    async def get_user(self, user_id):
        """获取单个用户

        Args:
            user_id: 用户ID

        Returns:
            用户信息
        """
        try:
            # 基础过滤条件
            filter = [
                {
                    "group_logic": "and",
                    "condition_logic": "and",
                    "conditions": [
                        {"field": "id", "operator": "eq", "value": user_id},
                        {"field": "is_deleted", "operator": "eq", "value": 0},
                    ],
                }
            ]

            users = await self.user_model.get_list(filter=filter, fields="*")
            if users:
                user = users[0]
                # 添加部门名称
                dept_id = user.get("dept_id")
                if dept_id:
                    dept = await self.get_first(
                        filter=[
                            {
                                "group_logic": "and",
                                "condition_logic": "and",
                                "conditions": [
                                    {
                                        "field": "id",
                                        "operator": "eq",
                                        "value": dept_id,
                                    }
                                ],
                            }
                        ]
                    )
                    if dept:
                        user["dept_name"] = dept.get("name")
                    else:
                        user["dept_name"] = None
                else:
                    user["dept_name"] = None
                return user
            else:
                return None
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"获取用户失败: {str(e)}")
            return None

    async def delete_user(self, user_id):
        """删除用户

        Args:
            user_id: 用户ID
        """
        # 软删除用户
        await self.user_model.update_by_id(user_id, {"is_deleted": 1})

    async def destroy_user(self, user_id):
        """物理删除用户

        Args:
            user_id: 用户ID
        """
        try:
            # 物理删除用户
            await self.user_model.destroy_by_id(user_id)
        except Exception as e:
            # 数据库表不存在时忽略错误
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"物理删除用户失败: {str(e)}")

    async def batch_delete_users(self, user_ids):
        """批量删除用户

        Args:
            user_ids: 用户ID列表

        Returns:
            删除的记录数
        """
        if not user_ids:
            return 0

        # 构建过滤条件
        filter_conditions = [
            {
                "group_logic": "and",
                "condition_logic": "and",
                "conditions": [{"field": "id", "operator": "in", "value": user_ids}],
            }
        ]

        # 批量软删除
        return await self.user_model.update(filter=filter_conditions, data={"is_deleted": 1})

    async def batch_all_users(self, data):
        """删除所有符合筛选条件的数据

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
                    {"group_logic": group_logic, "condition_logic": condition_logic, "conditions": processed_conditions}
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
                search_group = {"group_logic": "and", "condition_logic": "or", "conditions": search_conditions}
                processed_filter.append(search_group)

        # 验证过滤条件
        if not processed_filter:
            return 0

        # 批量删除
        return await self.user_model.delete(filter=processed_filter)

    async def batch_update_users(self, user_ids, data):
        """批量更新用户

        Args:
            user_ids: 用户ID列表
            data: 更新数据

        Returns:
            更新的记录数
        """
        if not user_ids:
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
                "conditions": [{"field": "id", "operator": "in", "value": user_ids}],
            }
        ]

        # 批量更新
        return await self.user_model.update(filter=filter_conditions, data=update_data)

    async def import_users(self, file, import_mode, field_mapping):
        """导入用户

        Args:
            file: Excel文件
            import_mode: 导入模式 (insert, update, insert_update)
            field_mapping: 字段映射

        Returns:
            导入结果
        """
        try:
            from openpyxl import load_workbook
            from io import BytesIO

            # 读取Excel文件
            wb = load_workbook(BytesIO(await file.read()))
            ws = wb.active

            # 获取表头
            headers = []
            for cell in ws[1]:
                headers.append(cell.value)

            # 读取数据
            data = []
            for row in ws.iter_rows(min_row=2):
                row_data = {}
                for idx, cell in enumerate(row):
                    if idx < len(headers):
                        # 使用与前端一致的列标识格式：column1, column2, ...
                        column_key = f"column{idx + 1}"
                        row_data[column_key] = cell.value
                data.append(row_data)

            # 处理导入数据
            success = 0
            failure = 0
            errors = []

            for row_idx, row in enumerate(data, 2):  # 从第2行开始计数（第1行是表头）
                try:
                    # 根据字段映射转换数据
                    user_data = {}

                    # 使用前端传递的字段映射
                    for field, column in field_mapping.items():
                        if column and column in row:
                            value = row[column]
                            # 处理状态字段
                            if field == "status":
                                if isinstance(value, str):
                                    user_data[field] = value == "启用" or value == "1" or value.lower() == "true"
                                else:
                                    user_data[field] = bool(value)
                            # 处理字符串字段，确保类型正确
                            elif field in ["username", "name", "phone", "email"]:
                                if value is not None:
                                    user_data[field] = str(value)
                            # 处理其他字段
                            else:
                                user_data[field] = value

                    # 检查是否有有效数据
                    if not user_data:
                        failure += 1
                        errors.append({"row": row_idx, "data": row, "message": "没有可导入的有效数据，请检查字段映射"})
                        continue

                    # 确保数据包含必要字段
                    if "title" not in user_data:
                        user_data["title"] = user_data.get("name", "")
                    if "password" not in user_data:
                        user_data["password"] = "123456"  # 默认密码

                    # 根据导入模式处理
                    if import_mode == "insert":
                        # 仅新增
                        try:
                            await self.create_user(user_data)
                            success += 1
                        except Exception as e:
                            failure += 1
                            errors.append({"row": row_idx, "data": row, "message": f"新增失败: {str(e)}"})
                    elif import_mode == "update":
                        # 仅更新
                        if "id" in user_data and user_data["id"]:
                            try:
                                await self.update_user(user_data["id"], user_data)
                                success += 1
                            except Exception as e:
                                failure += 1
                                errors.append({"row": row_idx, "data": row, "message": f"更新失败: {str(e)}"})
                        else:
                            failure += 1
                            errors.append({"row": row_idx, "data": row, "message": "更新模式需要ID字段"})
                    elif import_mode == "insert_update":
                        # 更新和新增
                        if "id" in user_data and user_data["id"]:
                            # 尝试更新
                            try:
                                await self.update_user(user_data["id"], user_data)
                                success += 1
                            except Exception as update_error:
                                # 更新失败，尝试新增
                                try:
                                    await self.create_user(user_data)
                                    success += 1
                                except Exception as create_error:
                                    failure += 1
                                    errors.append(
                                        {
                                            "row": row_idx,
                                            "data": row,
                                            "message": f"更新和新增都失败: {str(create_error)}",
                                        }
                                    )
                        else:
                            # 无ID，新增
                            try:
                                await self.create_user(user_data)
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
                    error_message = str(e)
                    logger.error(f"导入数据失败 (第{row_idx}行): {error_message}")
                    failure += 1
                    errors.append({"row": row_idx, "data": row, "message": error_message})

            return {"success": success, "failure": failure, "total": len(data), "errors": errors}
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"导入失败: {str(e)}")
            raise

    async def export_users(self, data):
        """导出用户

        Args:
            data: 包含过滤条件的数据

        Returns:
            导出结果信息
        """
        try:
            from openpyxl import Workbook
            from openpyxl.utils import get_column_letter
            from io import BytesIO

            # 获取过滤条件
            raw_filter = data.get("filter", [])
            # 获取搜索关键词
            keyword = data.get("keyword", "")
            # 获取搜索字段
            searchFields = data.get("searchFields", [])
            # 获取排序规则
            sort = data.get("sort", [])

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
                        {"group_logic": group_logic, "condition_logic": condition_logic, "conditions": processed_conditions}
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
                    search_group = {"group_logic": "and", "condition_logic": "or", "conditions": search_conditions}
                    processed_filter.append(search_group)

            # 处理ids字段，按照id过滤
            ids = data.get("ids", [])
            if ids:
                # 添加id过滤条件
                if not processed_filter:
                    processed_filter = []
                id_filter = {
                    "group_logic": "and",
                    "condition_logic": "and",
                    "conditions": [{"field": "id", "operator": "in", "value": ids}],
                }
                processed_filter.append(id_filter)

            # 基础过滤条件
            base_filter = [
                {
                    "group_logic": "and",
                    "condition_logic": "and",
                    "conditions": [{"field": "is_deleted", "operator": "eq", "value": 0}],
                }
            ]

            # 合并处理后的过滤条件
            if processed_filter:
                base_filter.extend(processed_filter)

            # 获取所有数据
            items = await self.user_model.get_list(fields="*", filter=base_filter, sort_rules=sort)

            # 创建Excel工作簿
            wb = Workbook()
            ws = wb.active
            ws.title = "用户数据"

            # 定义表头
            headers = {
                "id": "ID",
                "username": "用户名",
                "name": "真实姓名",
                "phone": "手机号",
                "email": "邮箱",
                "status": "状态",
                "dept_id": "部门ID",
                "created_at": "创建时间",
                "updated_at": "更新时间",
            }

            # 写入表头
            header_keys = list(headers.keys())
            for col_idx, key in enumerate(header_keys, 1):
                col_letter = get_column_letter(col_idx)
                ws[f"{col_letter}1"] = headers[key]

            # 写入数据
            # 处理 items 可能是列表或字典的情况
            if isinstance(items, list):
                data_items = items
            elif isinstance(items, dict) and "items" in items:
                data_items = items.get("items", [])
            else:
                data_items = []

            for row_idx, item in enumerate(data_items, 2):
                for col_idx, key in enumerate(header_keys, 1):
                    col_letter = get_column_letter(col_idx)
                    value = item.get(key)
                    # 处理状态字段
                    if key == "status":
                        ws[f"{col_letter}{row_idx}"] = "启用" if value else "禁用"
                    else:
                        ws[f"{col_letter}{row_idx}"] = value or ""

            # 调整列宽
            for col_idx, key in enumerate(header_keys, 1):
                col_letter = get_column_letter(col_idx)
                ws.column_dimensions[col_letter].width = 15

            # 保存到内存
            output = BytesIO()
            wb.save(output)
            output.seek(0)

            # 生成唯一文件名
            filename = build_export_filename("用户列表")
            file_size = len(output.getvalue())

            return {"filename": filename, "size": file_size, "message": "导出成功", "data": output.getvalue()}
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"导出失败: {str(e)}")
            raise

    async def export_users_selected(self, data):
        """导出选中用户

        Args:
            data: 包含用户ID列表的数据

        Returns:
            导出结果信息
        """
        try:
            from openpyxl import Workbook
            from openpyxl.utils import get_column_letter
            from io import BytesIO

            # 获取用户ID列表
            user_ids = data.get("ids", [])

            if not user_ids:
                return {"filename": "", "size": 0, "message": "没有选中的用户", "data": b""}

            # 构建过滤条件
            filter_conditions = [
                {
                    "group_logic": "and",
                    "condition_logic": "and",
                    "conditions": [
                        {"field": "id", "operator": "in", "value": user_ids},
                        {"field": "is_deleted", "operator": "eq", "value": 0},
                    ],
                }
            ]

            # 获取所有数据
            items = await self.user_model.get_list(fields="*", filter=filter_conditions)

            # 创建Excel工作簿
            wb = Workbook()
            ws = wb.active
            ws.title = "用户数据"

            # 定义表头
            headers = {
                "id": "ID",
                "username": "用户名",
                "name": "真实姓名",
                "phone": "手机号",
                "email": "邮箱",
                "status": "状态",
                "dept_id": "部门ID",
                "created_at": "创建时间",
                "updated_at": "更新时间",
            }

            # 写入表头
            header_keys = list(headers.keys())
            for col_idx, key in enumerate(header_keys, 1):
                col_letter = get_column_letter(col_idx)
                ws[f"{col_letter}1"] = headers[key]

            # 写入数据
            # 处理 items 可能是列表或字典的情况
            if isinstance(items, list):
                data_items = items
            elif isinstance(items, dict) and "items" in items:
                data_items = items.get("items", [])
            else:
                data_items = []

            for row_idx, item in enumerate(data_items, 2):
                for col_idx, key in enumerate(header_keys, 1):
                    col_letter = get_column_letter(col_idx)
                    value = item.get(key)
                    # 处理状态字段
                    if key == "status":
                        ws[f"{col_letter}{row_idx}"] = "启用" if value else "禁用"
                    else:
                        ws[f"{col_letter}{row_idx}"] = value or ""

            # 调整列宽
            for col_idx, key in enumerate(header_keys, 1):
                col_letter = get_column_letter(col_idx)
                ws.column_dimensions[col_letter].width = 15

            # 保存到内存
            output = BytesIO()
            wb.save(output)
            output.seek(0)

            # 生成唯一文件名
            filename = build_export_filename("选中用户列表")
            file_size = len(output.getvalue())

            return {"filename": filename, "size": file_size, "message": "导出成功", "data": output.getvalue()}
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"导出失败: {str(e)}")
            raise

    async def get_role_tree(self, request):
        """获取角色树

        Args:
            request: 请求对象

        Returns:
            角色树
        """
        # 基础过滤条件
        base_filter = [
            {
                "group_logic": "and",
                "condition_logic": "and",
                "conditions": [{"field": "is_deleted", "operator": "eq", "value": 0}],
            }
        ]

        # 从request获取过滤条件
        try:
            request_filter = await self.get_request_filter(request)
            if request_filter:
                base_filter.extend(request_filter)
        except Exception:
            pass

        roles = await self.role_model.get_list(filter=base_filter, sort_rules=[{"field": "id", "direction": "asc"}])

        # 由于角色表没有pid字段，直接返回角色列表
        return roles

    async def get_members(self, request):
        """获取角色成员

        Args:
            request: 请求对象

        Returns:
            角色成员
        """
        try:
            # 获取请求数据
            request_data = await request.json()
            # 前端标准契约是 { data: {...} }，需先解包；顶层参数用于兼容未解包请求
            data = request_data.get("data") or request_data
            role_id = data.get("role_id")
            page = data.get("page", 1)
            limit = data.get("limit", 20)
            keyword = data.get("keyword", "")
            filter_conditions = data.get("filter", [])
            sort_rules = data.get("sort_rules") or data.get("sort", [])

            if not role_id:
                return {"items": [], "total": 0}

            # 构建用户角色关联查询
            # 这里简化处理，实际应该使用 JOIN 查询
            # 先获取角色下的用户ID
            user_role_filter = [
                {
                    "group_logic": "and",
                    "condition_logic": "and",
                    "conditions": [{"field": "role_id", "operator": "eq", "value": role_id}],
                }
            ]

            user_roles = await self.user_role_model.get_list(filter=user_role_filter, fields="user_id")
            user_ids = [ur.get("user_id") for ur in user_roles if ur.get("user_id")]

            if not user_ids:
                return {"items": [], "total": 0}

            # 构建用户查询条件
            user_filter = [
                {
                    "group_logic": "and",
                    "condition_logic": "and",
                    "conditions": [
                        {"field": "id", "operator": "in", "value": user_ids},
                        {"field": "is_deleted", "operator": "eq", "value": 0},
                    ],
                }
            ]

            # 添加关键词搜索
            if keyword:
                user_filter.append(
                    {
                        "group_logic": "and",
                        "condition_logic": "or",
                        "conditions": [
                            {"field": "username", "operator": "contains", "value": keyword},
                            {"field": "name", "operator": "contains", "value": keyword},
                            {"field": "phone", "operator": "contains", "value": keyword},
                            {"field": "email", "operator": "contains", "value": keyword},
                        ],
                    }
                )

            # 合并传入的过滤条件
            if filter_conditions:
                user_filter.extend(filter_conditions)

            # 获取用户列表
            pagination = await self.user_model.get_list(
                page=page,
                limit=limit,
                sort_rules=sort_rules or [{"field": "id", "direction": "asc"}],
                filter=user_filter,
                fields="*",
            )

            return pagination
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"获取角色成员失败: {str(e)}")
            return {"items": [], "total": 0}

    async def get_available_users(self, request):
        """获取可用用户

        Args:
            request: 请求对象

        Returns:
            可用用户
        """
        try:
            # 获取请求数据
            request_data = await request.json()
            data = request_data.get("data", {})
            role_id = data.get("role_id")
            page = data.get("page", 1)
            limit = data.get("limit", 20)
            keyword = data.get("keyword", "")

            # 构建基础过滤条件
            user_filter = [
                {
                    "group_logic": "and",
                    "condition_logic": "and",
                    "conditions": [{"field": "is_deleted", "operator": "eq", "value": 0}],
                }
            ]

            # 如果指定了角色ID，排除该角色下的用户
            if role_id:
                # 先获取角色下的用户ID
                user_role_filter = [
                    {
                        "group_logic": "and",
                        "condition_logic": "and",
                        "conditions": [{"field": "role_id", "operator": "eq", "value": role_id}],
                    }
                ]

                user_roles = await self.user_role_model.get_list(filter=user_role_filter, fields="user_id")
                existing_user_ids = [ur.get("user_id") for ur in user_roles if ur.get("user_id")]

                if existing_user_ids:
                    user_filter.append(
                        {
                            "group_logic": "and",
                            "condition_logic": "and",
                            "conditions": [{"field": "id", "operator": "not_in", "value": existing_user_ids}],
                        }
                    )

            # 添加关键词搜索
            if keyword:
                user_filter.append(
                    {
                        "group_logic": "and",
                        "condition_logic": "or",
                        "conditions": [
                            {"field": "username", "operator": "contains", "value": keyword},
                            {"field": "name", "operator": "contains", "value": keyword},
                            {"field": "phone", "operator": "contains", "value": keyword},
                            {"field": "email", "operator": "contains", "value": keyword},
                        ],
                    }
                )

            # 获取用户列表
            pagination = await self.user_model.get_list(
                page=page,
                limit=limit,
                filter=user_filter,
                fields="*",
            )

            return pagination
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"获取可用用户失败: {str(e)}")
            return {"items": [], "total": 0}

    async def add_members(self, request):
        """添加角色成员

        Args:
            request: 请求对象

        Returns:
            添加结果
        """
        try:
            # 获取请求数据
            request_data = await request.json()
            data = request_data.get("data", {})
            role_id = data.get("role_id")
            user_ids = data.get("user_ids", [])

            if not role_id or not user_ids:
                return {"code": 400, "message": "角色ID和用户ID不能为空"}

            # 批量添加用户角色关联
            for user_id in user_ids:
                # 检查是否已存在关联
                existing_filter = [
                    {
                        "group_logic": "and",
                        "condition_logic": "and",
                        "conditions": [
                            {"field": "role_id", "operator": "eq", "value": role_id},
                            {"field": "user_id", "operator": "eq", "value": user_id},
                        ],
                    }
                ]

                existing = await self.user_role_model.get_list(filter=existing_filter)
                if not existing:
                    await self.user_role_model.create({"role_id": role_id, "user_id": user_id})

            return {"code": 200, "message": "添加成功"}
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"添加角色成员失败: {str(e)}")
            return {"code": 500, "message": str(e)}

    async def remove_member(self, request):
        """移除角色成员

        Args:
            request: 请求对象

        Returns:
            移除结果
        """
        try:
            # 获取请求数据
            request_data = await request.json()
            data = request_data.get("data", {})
            user_id = data.get("user_id")
            role_id = data.get("role_id")

            if not role_id or not user_id:
                return {"code": 400, "message": "角色ID和用户ID不能为空"}

            # 移除用户角色关联
            filter_conditions = [
                {
                    "group_logic": "and",
                    "condition_logic": "and",
                    "conditions": [
                        {"field": "role_id", "operator": "eq", "value": role_id},
                        {"field": "user_id", "operator": "eq", "value": user_id},
                    ],
                }
            ]

            await self.user_role_model.delete(filter=filter_conditions)

            return {"code": 200, "message": "移除成功"}
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"移除角色成员失败: {str(e)}")
            return {"code": 500, "message": str(e)}

    async def remove_members_batch(self, request):
        """批量移除角色成员

        Args:
            request: 请求对象

        Returns:
            移除结果
        """
        try:
            # 获取请求数据
            request_data = await request.json()
            data = request_data.get("data", {})
            user_ids = data.get("user_ids", [])
            role_id = data.get("role_id")

            if not role_id or not user_ids:
                return {"code": 400, "message": "角色ID和用户ID列表不能为空"}

            # 批量移除用户角色关联
            filter_conditions = [
                {
                    "group_logic": "and",
                    "condition_logic": "and",
                    "conditions": [
                        {"field": "role_id", "operator": "eq", "value": role_id},
                        {"field": "user_id", "operator": "in", "value": user_ids},
                    ],
                }
            ]

            await self.user_role_model.delete(filter=filter_conditions)

            return {"code": 200, "message": "批量移除成功"}
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"批量移除角色成员失败: {str(e)}")
            return {"code": 500, "message": str(e)}

    async def import_roles(self, request):
        """导入角色

        Args:
            request: 请求对象

        Returns:
            导入结果
        """
        try:
            from openpyxl import load_workbook
            from io import BytesIO

            # 读取Excel文件
            form_data = await request.form()
            file = form_data.get("file")
            if not file:
                return {"success": 0, "failure": 0, "total": 0, "errors": ["请选择要导入的文件"]}

            # 读取Excel文件
            wb = load_workbook(BytesIO(await file.read()))
            ws = wb.active

            # 获取表头
            headers = []
            for cell in ws[1]:
                headers.append(cell.value)

            # 读取数据
            data = []
            for row in ws.iter_rows(min_row=2):
                row_data = {}
                for idx, cell in enumerate(row):
                    if idx < len(headers):
                        # 使用与前端一致的列标识格式：column1, column2, ...
                        column_key = f"column{idx + 1}"
                        row_data[column_key] = cell.value
                data.append(row_data)

            # 处理导入数据
            success = 0
            failure = 0
            errors = []

            for row_idx, row in enumerate(data, 2):  # 从第2行开始计数（第1行是表头）
                try:
                    # 简化处理，直接使用 row 数据
                    role_data = {}
                    if "column1" in row and row["column1"]:
                        role_data["name"] = row["column1"]
                    if "column2" in row and row["column2"]:
                        role_data["code"] = row["column2"]

                    # 检查是否有有效数据
                    if not role_data:
                        failure += 1
                        errors.append({"row": row_idx, "data": row, "message": "没有可导入的有效数据"})
                        continue

                    # 确保数据包含必要字段
                    if "title" not in role_data:
                        role_data["title"] = role_data.get("name", "")

                    # 创建角色
                    await self.role_model.create(role_data)
                    success += 1
                except Exception as e:
                    import logging

                    logger = logging.getLogger(__name__)
                    error_message = str(e)
                    logger.error(f"导入数据失败 (第{row_idx}行): {error_message}")
                    failure += 1
                    errors.append({"row": row_idx, "data": row, "message": error_message})

            return {"success": success, "failure": failure, "total": len(data), "errors": errors}
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"导入失败: {str(e)}")
            raise

    async def export_roles(self, data):
        """导出角色

        Args:
            data: 包含筛选条件的数据

        Returns:
            导出结果信息
        """
        try:
            from openpyxl import Workbook
            from openpyxl.utils import get_column_letter
            from io import BytesIO

            # 获取请求数据
            request_data = data
            role_ids = request_data.get("role_ids", [])

            # 构建过滤条件
            base_filter = [
                {
                    "group_logic": "and",
                    "condition_logic": "and",
                    "conditions": [{"field": "is_deleted", "operator": "eq", "value": 0}],
                }
            ]

            if role_ids:
                base_filter.append(
                    {
                        "group_logic": "and",
                        "condition_logic": "and",
                        "conditions": [{"field": "id", "operator": "in", "value": role_ids}],
                    }
                )

            # 获取所有数据
            items = await self.role_model.get_list(fields="*", filter=base_filter)

            # 创建Excel工作簿
            wb = Workbook()
            ws = wb.active
            ws.title = "角色数据"

            # 定义表头
            headers = {
                "id": "ID",
                "name": "角色名称",
                "code": "角色代码",
                "status": "状态",
                "created_at": "创建时间",
                "updated_at": "更新时间",
            }

            # 写入表头
            header_keys = list(headers.keys())
            for col_idx, key in enumerate(header_keys, 1):
                col_letter = get_column_letter(col_idx)
                ws[f"{col_letter}1"] = headers[key]

            # 写入数据
            # 处理 items 可能是列表或字典的情况
            if isinstance(items, list):
                data_items = items
            elif isinstance(items, dict) and "items" in items:
                data_items = items.get("items", [])
            else:
                data_items = []

            for row_idx, item in enumerate(data_items, 2):
                for col_idx, key in enumerate(header_keys, 1):
                    col_letter = get_column_letter(col_idx)
                    value = item.get(key)
                    # 处理状态字段
                    if key == "status":
                        ws[f"{col_letter}{row_idx}"] = "启用" if value else "禁用"
                    else:
                        ws[f"{col_letter}{row_idx}"] = value or ""

            # 调整列宽
            for col_idx, key in enumerate(header_keys, 1):
                col_letter = get_column_letter(col_idx)
                ws.column_dimensions[col_letter].width = 15

            # 保存到内存
            output = BytesIO()
            wb.save(output)
            output.seek(0)

            # 生成唯一文件名
            filename = build_export_filename("角色列表")
            file_size = len(output.getvalue())

            return {"filename": filename, "size": file_size, "message": "导出成功", "data": output.getvalue()}
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"导出失败: {str(e)}")
            raise

    async def export_role_members(self, data):
        """导出指定角色的成员

        Args:
            data: 包含 role_id 与 keyword 的数据

        Returns:
            导出结果信息
        """
        try:
            from openpyxl import Workbook
            from openpyxl.utils import get_column_letter
            from io import BytesIO

            role_id = data.get("role_id")
            keyword = data.get("keyword", "")

            data_items = []

            if role_id:
                # 先获取角色下的用户ID
                user_role_filter = [
                    {
                        "group_logic": "and",
                        "condition_logic": "and",
                        "conditions": [{"field": "role_id", "operator": "eq", "value": role_id}],
                    }
                ]
                user_roles = await self.user_role_model.get_list(filter=user_role_filter, fields="user_id")
                user_ids = [ur.get("user_id") for ur in user_roles if ur.get("user_id")]

                if user_ids:
                    # 构建用户查询条件
                    user_filter = [
                        {
                            "group_logic": "and",
                            "condition_logic": "and",
                            "conditions": [
                                {"field": "id", "operator": "in", "value": user_ids},
                                {"field": "is_deleted", "operator": "eq", "value": 0},
                            ],
                        }
                    ]

                    # 添加关键词搜索
                    if keyword:
                        user_filter.append(
                            {
                                "group_logic": "and",
                                "condition_logic": "or",
                                "conditions": [
                                    {"field": "username", "operator": "contains", "value": keyword},
                                    {"field": "name", "operator": "contains", "value": keyword},
                                    {"field": "phone", "operator": "contains", "value": keyword},
                                    {"field": "email", "operator": "contains", "value": keyword},
                                ],
                            }
                        )

                    items = await self.user_model.get_list(fields="*", filter=user_filter)

                    if isinstance(items, list):
                        data_items = items
                    elif isinstance(items, dict) and "items" in items:
                        data_items = items.get("items", [])

            # 创建Excel工作簿
            wb = Workbook()
            ws = wb.active
            ws.title = "角色成员"

            # 定义表头
            headers = {
                "id": "ID",
                "username": "用户名",
                "name": "真实姓名",
                "phone": "手机号",
                "email": "邮箱",
                "status": "状态",
                "dept_id": "部门ID",
                "created_at": "创建时间",
            }

            # 写入表头
            header_keys = list(headers.keys())
            for col_idx, key in enumerate(header_keys, 1):
                col_letter = get_column_letter(col_idx)
                ws[f"{col_letter}1"] = headers[key]

            # 写入数据
            for row_idx, item in enumerate(data_items, 2):
                for col_idx, key in enumerate(header_keys, 1):
                    col_letter = get_column_letter(col_idx)
                    value = item.get(key)
                    # 处理状态字段
                    if key == "status":
                        ws[f"{col_letter}{row_idx}"] = "启用" if value else "禁用"
                    else:
                        ws[f"{col_letter}{row_idx}"] = value or ""

            # 调整列宽
            for col_idx, key in enumerate(header_keys, 1):
                col_letter = get_column_letter(col_idx)
                ws.column_dimensions[col_letter].width = 15

            # 保存到内存
            output = BytesIO()
            wb.save(output)
            output.seek(0)

            # 生成唯一文件名
            filename = build_export_filename("角色成员列表")
            file_size = len(output.getvalue())

            return {"filename": filename, "size": file_size, "message": "导出成功", "data": output.getvalue()}
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"导出角色成员失败: {str(e)}")
            raise

    async def create_role(self, data):
        """创建角色

        Args:
            data: 角色数据

        Returns:
            创建结果
        """
        name = (data.get("name") or "").strip()
        code = (data.get("code") or "").strip()
        if not name:
            raise Exception("角色名称不能为空")
        if not code:
            raise Exception("角色代码不能为空")

        # 角色代码唯一性校验
        if await self.get_role_by_code(code):
            raise Exception(f"角色代码已存在: {code}")

        role_data = {
            "title": name,
            "name": name,
            "code": code,
            "description": data.get("description"),
            "status": data.get("status", 1),
        }
        role_id = await self.role_model.create(role_data)
        return await self.get_role(role_id)

    async def get_role_by_code(self, code):
        """按角色代码查询角色

        Args:
            code: 角色代码

        Returns:
            角色信息或None
        """
        roles = await self.role_model.get_list(
            filter=[
                {
                    "group_logic": "and",
                    "condition_logic": "and",
                    "conditions": [
                        {"field": "code", "operator": "eq", "value": code},
                        {"field": "is_deleted", "operator": "eq", "value": 0},
                    ],
                }
            ],
            fields="*",
        )
        return roles[0] if roles else None

    async def update_role(self, role_id, data):
        """更新角色

        Args:
            role_id: 角色ID
            data: 更新数据

        Returns:
            更新结果
        """
        role = await self.get_role(role_id)
        if not role:
            raise Exception("角色不存在")

        # 仅保留 x_role 真实存在的字段（该表无 pid / sort_order / is_system）
        role_data = {
            "name": data.get("name"),
            "code": data.get("code"),
            "description": data.get("description"),
            "status": data.get("status"),
        }
        role_data = {k: v for k, v in role_data.items() if v is not None}

        if not role_data:
            raise Exception("更新数据不能为空")

        name = role_data.get("name")
        if name is not None:
            name = name.strip()
            if not name:
                raise Exception("角色名称不能为空")
            role_data["name"] = name
            role_data["title"] = name

        code = role_data.get("code")
        if code is not None:
            code = code.strip()
            if not code:
                raise Exception("角色代码不能为空")
            if code != role.get("code") and await self.get_role_by_code(code):
                raise Exception(f"角色代码已存在: {code}")
            role_data["code"] = code

        await self.role_model.update_by_id(role_id, role_data)
        return await self.get_role(role_id)

    async def get_role(self, role_id):
        """获取单个角色

        Args:
            role_id: 角色ID

        Returns:
            角色信息
        """
        try:
            roles = await self.role_model.get_list(
                filter=[
                    {
                        "group_logic": "and",
                        "condition_logic": "and",
                        "conditions": [
                            {"field": "id", "operator": "eq", "value": role_id},
                            {"field": "is_deleted", "operator": "eq", "value": 0},
                        ],
                    }
                ],
                fields="*",
            )
            return roles[0] if roles else None
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"获取角色失败: {str(e)}")
            return None

    async def delete_role(self, role_id):
        """删除角色

        Args:
            role_id: 角色ID
        """
        role = await self.get_role(role_id)
        if not role:
            raise Exception("角色不存在")
        if role.get("code") == "admin":
            raise Exception("超级管理员角色不允许删除")

        # 软删除角色
        await self.role_model.update_by_id(role_id, {"is_deleted": 1})
        # 同时删除角色关联的用户角色关系
        await self.user_role_model.delete(
            filter=[
                {
                    "group_logic": "and",
                    "condition_logic": "and",
                    "conditions": [{"field": "role_id", "operator": "eq", "value": role_id}],
                }
            ]
        )
        # 同时删除角色关联的权限关系
        await self.role_permission_model.delete(
            filter=[
                {
                    "group_logic": "and",
                    "condition_logic": "and",
                    "conditions": [{"field": "role_id", "operator": "eq", "value": role_id}],
                }
            ]
        )

    async def get_permission_tree(self, request):
        """获取权限清单树

        Args:
            request: 请求对象

        Returns:
            权限点树形结构
        """
        permissions = await self.permission_model.get_list(
            filter=[
                {
                    "group_logic": "and",
                    "condition_logic": "and",
                    "conditions": [
                        {"field": "is_deleted", "operator": "eq", "value": 0},
                        {"field": "status", "operator": "eq", "value": 1},
                    ],
                }
            ],
            fields="id, pid, title, code, module, type, path, icon, sort",
            sort_rules=[{"field": "sort", "direction": "asc"}],
        )
        return build_tree(permissions, parent_field="pid", id_field="id")

    async def get_role_permissions(self, role_id):
        """获取角色已授权的权限点

        Args:
            role_id: 角色ID

        Returns:
            包含 permission_ids 与 codes 的字典
        """
        role = await self.get_role(role_id)
        if not role:
            raise Exception("角色不存在")

        relations = await self.role_permission_model.get_list(
            filter=[
                {
                    "group_logic": "and",
                    "condition_logic": "and",
                    "conditions": [
                        {"field": "role_id", "operator": "eq", "value": role_id},
                        {"field": "is_deleted", "operator": "eq", "value": 0},
                    ],
                }
            ],
            fields="permission_id",
        )
        permission_ids = [r.get("permission_id") for r in relations if r.get("permission_id")]

        codes = []
        if permission_ids:
            permissions = await self.permission_model.get_list(
                filter=[
                    {
                        "group_logic": "and",
                        "condition_logic": "and",
                        "conditions": [
                            {"field": "id", "operator": "in", "value": permission_ids},
                            {"field": "is_deleted", "operator": "eq", "value": 0},
                        ],
                    }
                ],
                fields="code",
            )
            codes = [p.get("code") for p in permissions if p.get("code")]

        return {"role_id": role_id, "permission_ids": permission_ids, "codes": codes}

    async def grant_role_permissions(self, role_id, permission_ids):
        """保存角色授权（覆盖式）

        Args:
            role_id: 角色ID
            permission_ids: 权限点ID列表

        Returns:
            保存结果
        """
        role = await self.get_role(role_id)
        if not role:
            raise Exception("角色不存在")

        permission_ids = [int(pid) for pid in (permission_ids or []) if pid]

        # 校验权限点均有效
        if permission_ids:
            valid = await self.permission_model.get_list(
                filter=[
                    {
                        "group_logic": "and",
                        "condition_logic": "and",
                        "conditions": [
                            {"field": "id", "operator": "in", "value": permission_ids},
                            {"field": "is_deleted", "operator": "eq", "value": 0},
                        ],
                    }
                ],
                fields="id",
            )
            valid_ids = {p.get("id") for p in valid}
            invalid = [pid for pid in permission_ids if pid not in valid_ids]
            if invalid:
                raise Exception(f"存在无效权限点: {invalid}")

        # 覆盖式：先清空旧授权，再写入新授权
        await self.role_permission_model.delete(
            filter=[
                {
                    "group_logic": "and",
                    "condition_logic": "and",
                    "conditions": [{"field": "role_id", "operator": "eq", "value": role_id}],
                }
            ]
        )

        for permission_id in permission_ids:
            await self.role_permission_model.create({"role_id": role_id, "permission_id": permission_id})

        return {"role_id": role_id, "count": len(permission_ids)}

