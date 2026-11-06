"""数据库模型基类模块

本模块提供数据库模型基类，封装了通用的数据库操作方法，包括查询、创建、更新、删除等功能。
"""

from typing import Dict, List, Optional, Any, Union, Tuple
from pydantic import BaseModel
from .db import db
from .config import config
from ..service import qiniu_service
from .models import (
    SortRule,
    FilterGroup,
    ListRequest,
)
import logging
import re
import json
from datetime import date, datetime, timezone
from fastapi import Request

logger = logging.getLogger(__name__)


class Model:
    """数据库模型基类，提供通用的数据库操作方法"""

    foreign_key_fields: List[Dict[str, str]] = []
    signed_url_fields: List[str] = []
    jsonb_fields: List[str] = []

    def __init__(self, table_name: str, db_instance: Optional[Any] = None) -> None:
        """初始化模型

        Args:
            table_name: 表名
            db_instance: 数据库实例，默认使用全局实例
        """
        # 获取数据库前缀配置
        self.db_prefix: str = config.get("PG_PREFIX", "")
        # 拼接表名和前缀
        self.table_name: str = f"{self.db_prefix}{table_name}"
        # 使用传入的数据库实例或全局实例
        self.db = db_instance if db_instance is not None else db
        # 表字段缓存
        self._table_fields_cache: Optional[Dict[str, Any]] = None
        self.options: Dict[str, Any] = {}

    def _parse_jsonb_field(self, value: Any) -> Any:
        """解析 JSONB 字段，确保返回正确的 Python 对象

        Args:
            value: JSONB 字段值

        Returns:
            解析后的 Python 对象（列表或字典）
        """
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            return [value]
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return parsed
                elif isinstance(parsed, dict):
                    return [parsed]
                else:
                    return []
            except (json.JSONDecodeError, TypeError):
                return []
        return []

    def transform_for_response(
        self, data: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """响应数据转换钩子

        子类可重写此方法，在返回数据前进行自定义转换
        例如：生成带签名的 URL、解析 JSONB 字段

        Args:
            data: 单条记录或记录列表

        Returns:
            转换后的数据
        """

        def convert_item(item):
            if not isinstance(item, dict):
                return item

            for field in self.jsonb_fields:
                if field in item:
                    item[field] = self._parse_jsonb_field(item[field])

            if not self.signed_url_fields:
                return item

            url_expires = config.get("QINIU_URL_EXPIRES", 3600)

            for field in self.signed_url_fields:
                value = item.get(field)

                if value and isinstance(value, str):
                    if "e=" in value or "token=" in value:
                        logger.debug(f"字段 {field} 已是签名 URL，跳过转换")
                        continue

                    try:
                        signed_url = qiniu_service.generate_signed_url(value, expires=url_expires)
                        item[field] = signed_url
                        logger.debug(f"字段 {field} 签名 URL 生成成功")
                    except Exception as e:
                        logger.warning(f"字段 {field} 签名 URL 生成失败: {str(e)}")

            return item

        if isinstance(data, list):
            return [convert_item(item) for item in data]
        elif isinstance(data, dict):
            return convert_item(data)
        return data

    def transform_for_save(self, data: Union[Dict[str, Any], BaseModel]) -> Dict[str, Any]:
        """保存数据转换钩子

        子类可重写此方法，在保存数据前进行自定义转换
        例如：将完整 URL 转换为存储 key、将 JSONB 字段序列化为 JSON 字符串

        Args:
            data: 记录数据

        Returns:
            转换后的数据
        """
        from datetime import datetime, timezone
        
        if isinstance(data, BaseModel):
            result = data.model_dump(exclude_unset=True)
        else:
            result = data.copy() if isinstance(data, dict) else {}

        # 将 aware datetime 统一转为 UTC（naive datetime 保持原样）
        for key, value in result.items():
            if isinstance(value, datetime) and value.tzinfo is not None:
                result[key] = value.astimezone(timezone.utc)

        for field in self.jsonb_fields:
            if field in result and result[field] is not None:
                value = result[field]
                if isinstance(value, (list, dict)):
                    result[field] = json.dumps(value, ensure_ascii=False)
                    logger.debug(f"字段 {field} 序列化为 JSON 字符串")

        if not self.signed_url_fields:
            return result

        qiniu_domain = config.get("qiniu.domain", "")

        for field in self.signed_url_fields:
            if field in result:
                value = result[field]

                if value and isinstance(value, str):
                    if value.startswith("http://") or value.startswith("https://"):
                        try:
                            from urllib.parse import urlparse

                            parsed = urlparse(value)
                            path = parsed.path

                            if path.startswith("/"):
                                path = path[1:]

                            if qiniu_domain and qiniu_domain in value:
                                result[field] = path
                                logger.debug(f"字段 {field} 从完整 URL 提取 key: {path}")
                            else:
                                # qiniu_domain 不匹配，无法提取key，保留原值但添加警告
                                if qiniu_domain:
                                    logger.warning(
                                        f"字段 {field} 的完整 URL {value} 与配置的域名 {qiniu_domain} 不匹配，无法提取key，建议只存储key节省空间"
                                    )
                                result[field] = path
                                logger.debug(f"字段 {field} 提取路径: {path}")
                        except Exception as e:
                            logger.warning(f"字段 {field} URL 解析失败: {str(e)}")

        return result

    async def count(self, sql: str, params: List[Any]) -> int:
        """统计记录数

        Args:
            sql: 统计 SQL 语句
            params: SQL 参数列表

        Returns:
            记录数
        """
        result = await self.db.fetch_one(sql, params)
        return result.get("count", 0) if result else 0  # type: ignore[no-any-return]

    async def get_first(
        self,
        filter: Optional[Union[list, List[FilterGroup]]] = None,
        fields: str = "*",
        sort_rules: Optional[Union[list, List[SortRule]]] = None,
    ) -> Optional[Dict[str, Any]]:
        """获取第一条记录

        Args:
            filter: 过滤条件，格式：[{group_logic: "and", condition_logic: "and",
                conditions: [{field: "status", operator: "eq", value: "1"}]
            fields: 字段选择，如 "*,!password,!token"
            sort_rules: 排序规则，格式：[{field: "id", direction: "asc"}]

        Returns:
            第一条记录或 None
        """
        logger.debug(f"开始执行 get_first，表名：{self.table_name}")
        logger.debug(f"过滤条件：{filter}")
        logger.debug(f"字段选择：{fields}")
        logger.debug(f"排序规则：{sort_rules}")

        select_sql = await self._build_select_sql(fields)
        from_sql = self._build_from_sql()
        where_sql, params = self._build_where_sql(filter)
        order_by_sql = self._build_order_by_sql(sort_rules)

        sql = f"{select_sql} FROM {from_sql} {where_sql} {order_by_sql} LIMIT 1"
        logger.debug(f"执行 SQL：{sql}")
        logger.debug(f"参数：{params}")

        data = await self.db.fetch_one(sql, params)
        logger.debug(f"查询结果：{data}")

        if data:
            # 处理排除字段 !token,!password
            if "exclude" in self.options:
                logger.debug(f"应用排除字段：{self.options['exclude']}")
                for field in self.options["exclude"]:
                    data.pop(field, None)
                    logger.debug(f"排除字段 {field}")
            logger.debug(f"处理后结果：{data}")

        # 应用响应数据转换钩子
        data = self.transform_for_response(data)

        return data

    async def exists(self, conditions: Dict[str, Any]) -> bool:
        """检查是否存在匹配条件的记录

        Args:
            conditions: 条件字典，如 {"name": "test"}，多个条件间为 AND 关系

        Returns:
            是否存在
        """
        filter_conditions = {
            "group_logic": "and",
            "condition_logic": "and",
            "conditions": [
                {"field": k, "operator": "eq", "value": v}
                for k, v in conditions.items()
            ],
        }
        result = await self.get_first(filter=[filter_conditions], fields="id")
        return result is not None

    async def get_by_id(self, id: int, fields: str = "*") -> Optional[Dict[str, Any]]:
        """根据ID获取记录

        Args:
            id: 记录ID
            fields: 字段选择，默认全部

        Returns:
            记录或None
        """
        filter = [
            {
                "group_logic": "and",
                "condition_logic": "and",
                "conditions": [{"field": "id", "operator": "eq", "value": id}],
            }
        ]
        return await self.get_first(filter=filter, fields=fields)

    async def get_request_filter(self, request: Request) -> List[Dict[str, Any]]:
        """获取默认过滤条件

        Args:
            request: 请求对象，用于获取请求参数

        Returns:
            默认过滤条件列表
        """
        # 从输入数据获取过滤条件
        raw_filter: List[Dict[str, Any]] = []
        keyword: str = ""
        search_fields: List[str] = []

        if request:
            # 尝试从不同的方法获取参数
            try:
                request_data = await request.json()
                raw_filter = request_data.get("filter", [])
                keyword = request_data.get("keyword", "")
                search_fields = request_data.get("searchFields", [])
            except Exception:
                # 如果调用方式不同，使用默认值
                pass

        # 处理过滤条件格式
        processed_filter: List[Dict[str, Any]] = []
        for group in raw_filter:
            if isinstance(group, dict):
                # 转换用户提供的格式到内部格式
                group_logic = group.get("group_logic", group.get("groupLogic", "and"))
                condition_logic = group.get("condition_logic", group.get("condLogic", "and"))
                conditions = group.get("conditions", group.get("cond", []))
                # 处理conditions
                processed_conditions: List[Dict[str, Any]] = []
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
        if keyword and search_fields:
            search_conditions: List[Dict[str, Any]] = []
            for field in search_fields:
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

        return processed_filter

    async def get_list(
        self,
        filter: Optional[Union[list, List[FilterGroup]]] = None,
        fields: str = "*",
        sort_rules: Optional[Union[list, List[SortRule]]] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        request: Optional[ListRequest] = None,
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """查询多条记录

        Args:
            filter: 过滤条件，格式：[{group_logic: "and", condition_logic: "and",
                conditions: [{field: "status", operator: "eq", value: "1"}]
            fields: 字段选择，如 "id, name, email"
            sort_rules: 排序规则，格式：[{field: "id", direction: "asc"}]
            page: 页码
            limit: 每页条数
            request: ListRequest 对象，包含完整的请求参数

        Returns:
            记录列表或包含记录列表和总记录数的字典
        """
        # 如果提供了 request 参数，使用其中的参数
        if request:
            filter = request.filter
            fields = request.fields
            sort_rules = request.sort_rules
            page = request.page
            limit = request.limit

        logger.debug(f"开始执行 get_list，表名：{self.table_name}")
        logger.debug(f"过滤条件：{filter}")
        logger.debug(f"字段选择：{fields}")
        logger.debug(f"排序规则：{sort_rules}")
        logger.debug(f"分页参数：page={page}, limit={limit}")

        select_fields = await self._build_select_sql(fields)
        from_sql = self._build_from_sql()
        where_sql, params = self._build_where_sql(filter)
        order_by_sql = self._build_order_by_sql(sort_rules)

        count_sql = f"SELECT COUNT(*) FROM {from_sql} {where_sql}"
        sql = f"{select_fields} FROM {from_sql} {where_sql} {order_by_sql}"
        logger.debug(f"执行 COUNT SQL：{count_sql}")
        logger.debug(f"执行 SELECT SQL：{sql}")
        logger.debug(f"参数：{params}")

        # 处理分页
        if limit and page:
            total = await self.count(count_sql, params)
            logger.debug(f"总记录数：{total}")

            offset = (page - 1) * limit
            sql += f" LIMIT {limit} OFFSET {offset}"
            logger.debug(f"带分页的 SQL：{sql}")

            items = await self.db.fetch_all(sql, params)
            logger.debug(f"查询结果数量：{len(items)}")
            # 处理排除字段
            if "exclude" in self.options:
                items = self._apply_exclude_fields(items)
            # 应用响应数据转换钩子
            items = self.transform_for_response(items)

            return {"items": items, "total": total}
        else:
            items = await self.db.fetch_all(sql, params)
            logger.debug(f"查询结果数量：{len(items)}")
            # 处理排除字段
            if "exclude" in self.options:
                items = self._apply_exclude_fields(items)
            # 应用响应数据转换钩子
            items = self.transform_for_response(items)
            return items

    def _apply_exclude_fields(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """应用排除字段

        Args:
            items: 记录列表

        Returns:
            应用排除字段后的记录列表
        """
        logger.debug(f"应用排除字段：{self.options['exclude']}")
        for field in self.options["exclude"]:
            for item in items:
                item.pop(field, None)
        logger.debug(f"排除字段后结果示例：{items[0] if items else '无'}")
        return items

    async def _build_select_sql(self, fields: str) -> str:
        """处理字段选择

        Args:
            fields: 字段选择字符串，支持以下格式：
                - 主表所有字段：*
                - 主表字段：id, name, status
                - 排除字段：!token,!password
                - 简单关联表字段：dept.name, dept.code 关联条件为user.dept_id = dept.id
                - 带别名的关联字段：dept.name as dept_name
                - 自定义关联条件：user.name as manager_name on dept.manager_id = dept.manager_id

        Returns:
            SQL SELECT 子句中的字段部分，可能包含 JOIN 子句
        """
        logger.debug(f"开始构建 SELECT SQL，输入字段：{fields}")

        fields = fields.strip(",")

        table_alias_index = 1
        # 初始化 options["fields"]
        self.options["fields"] = []
        # 初始化 options["exclude"]
        self.options["exclude"] = []
        # 初始化已处理的关联表
        self.options["joined_tables"] = set()

        for field in fields.split(","):
            field = field.strip()
            logger.debug(f"处理字段：{field}")
            # 处理排除字段!token,!password
            if field.startswith("!"):
                exclude_field = field[1:]
                self.options["exclude"].append(exclude_field)
                logger.debug(f"处理排除字段：{exclude_field}")
                continue

            if field == "*":
                table_alias = "main"
                field_config = {
                    "query_fields": "main.*",
                    "table_name": self.table_name,
                    "table_alias": table_alias,
                    "filter_values": None,
                }
                self.options["fields"].append(field_config)
                logger.debug("处理通配符字段，使用 main.* 查询所有表字段")
            # 处理主表字段
            elif "." not in field and " as " not in field:
                # 检查是否是外键别名字段，如果是则跳过，交给自动JOIN处理
                if self.foreign_key_fields:
                    is_fk_alias = False
                    for fk_field in self.foreign_key_fields:
                        if fk_field.get("alias_field") == field:
                            is_fk_alias = True
                            break
                    if is_fk_alias:
                        logger.debug(f"跳过外键别名字段（由自动JOIN处理）：{field}")
                        continue
                table_alias = "main"
                field_config = {
                    "query_fields": f"{table_alias}.{field}",
                    "table_name": self.table_name,
                    "table_alias": table_alias,
                    "filter_values": None,
                }
                self.options["fields"].append(field_config)
                logger.debug(f"处理主表字段：{field}")
            # field字符串有as,没有on ，则为带别名的关联字段
            elif " as " in field and " on " not in field:
                # 正则表达式匹配关联字段
                match = re.match(r"(\w+)\.(\w+)\s+as\s+(\w+)", field)
                if match:
                    table_name, field_name, alias = match.groups()
                    table_alias = f"t{table_alias_index}"
                    table_alias_index += 1
                    field_config = {
                        "query_fields": f"{table_alias}.{field_name} as {alias}",
                        "table_name": table_name,
                        "table_alias": table_alias,
                        "filter_values": f"main.id = {table_alias}.id",
                    }
                    self.options["fields"].append(field_config)
                    logger.debug(f"处理带别名的关联字段：{field}")
            # field字符串有as,有on ，则为带别名的关联字段
            elif " as " in field and " on " in field:
                # 正则表达式匹配关联字段
                match = re.match(r"(\w+)\.(\w+)\s+as\s+(\w+)\s+on\s+(.*)", field)
                if match:
                    table_name, field_name, alias, filter_values = match.groups()
                    table_alias = f"t{table_alias_index}"
                    table_alias_index += 1
                    # 表名替换成表别名
                    filter_values = filter_values.strip().replace(self.table_name, "main")
                    filter_values = filter_values.strip().replace(table_name, table_alias)
                    field_config = {
                        "query_fields": f"{table_alias}.{field_name} as {alias}",
                        "table_name": table_name,
                        "table_alias": table_alias,
                        "filter_values": filter_values,
                    }
                    self.options["fields"].append(field_config)
                    logger.debug(f"处理带自定义关联条件的字段：{field}")

        select_fields = []
        if "fields" in self.options:
            for field in self.options["fields"]:
                select_fields.append(str(field["query_fields"]))
        else:
            select_fields.append("main.*")

        # 自动添加外键字段到查询中
        if self.foreign_key_fields:
            for fk_field in self.foreign_key_fields:
                ref_table = fk_field.get("ref_table")
                ref_field = fk_field.get("ref_field")
                alias_field = fk_field.get("alias_field")
                display_field = fk_field.get("display_field")

                if not all([ref_table, ref_field, alias_field, display_field]):
                    continue

                # 添加数据库前缀
                full_ref_table = f"{self.db_prefix}{ref_table}"

                # 检查是否已经通过 JOIN 添加了该表
                table_key = f"{ref_table}"
                if table_key in self.options.get("joined_tables", set()):
                    # 已经在 fields 中定义了，使用 fields 中的配置
                    continue

                # 自动生成别名
                fk_table_alias = f"fk_{table_alias_index}"
                table_alias_index += 1

                # 添加 LEFT JOIN
                join_config = {
                    "query_fields": f"{fk_table_alias}.{display_field} as {alias_field}",
                    "table_name": full_ref_table,
                    "table_alias": fk_table_alias,
                    "filter_values": f"main.{fk_field.get('field')} = {fk_table_alias}.{ref_field}",
                }
                self.options["fields"].append(join_config)
                select_fields.append(join_config["query_fields"])
                self.options["joined_tables"].add(table_key)

        result = "SELECT " + ", ".join(select_fields)
        logger.debug(f"构建完成 SELECT SQL：{result}")
        logger.debug(f"排除字段列表：{self.options.get('exclude', [])}")
        return result

    def _build_from_sql(self) -> str:
        """构建FROM子句

        Returns:
            FROM子句
        """
        from_clause = f"{self.table_name} as main"

        # 已处理的关联表
        processed_tables = set()

        # 处理 fields 中定义的关联字段
        if "fields" in self.options:
            for field in self.options["fields"]:
                if field["table_alias"] != "main" and field.get("filter_values"):
                    table_key = f"{field['table_name']}_{field['table_alias']}"
                    if table_key not in processed_tables:
                        from_clause += (
                            f" left join {field['table_name']} as {field['table_alias']} on {field['filter_values']}"
                        )
                        processed_tables.add(table_key)

        # 自动处理外键字段的 JOIN
        if self.foreign_key_fields:
            for fk_field in self.foreign_key_fields:
                ref_table = fk_field.get("ref_table")
                ref_field = fk_field.get("ref_field")
                alias_field = fk_field.get("alias_field")

                if not all([ref_table, ref_field, alias_field]):
                    continue

                # 添加数据库前缀
                full_ref_table = f"{self.db_prefix}{ref_table}"

                # 检查是否已经在 fields 中处理
                table_key = f"{ref_table}"
                if table_key in self.options.get("joined_tables", set()):
                    continue

                # 查找自动生成的别名
                fk_table_alias = None
                for field in self.options.get("fields", []):
                    if field.get("table_name") == full_ref_table and field.get("query_fields", "").endswith(
                        f"as {alias_field}"
                    ):
                        fk_table_alias = field.get("table_alias")
                        filter_values = f"main.{fk_field.get('field')} = {fk_table_alias}.{ref_field}"
                        if table_key not in processed_tables:
                            from_clause += f" left join {full_ref_table} as {fk_table_alias} on {filter_values}"
                            processed_tables.add(table_key)
                        break

        return from_clause

    def _build_where_sql(
        self, filter: Optional[Union[list, List[FilterGroup]]], param_index: int = 1
    ) -> Tuple[str, List[Any]]:
        """构建WHERE条件

        Args:
            filter: 过滤条件
            param_index: 参数起始索引

        Returns:
            WHERE子句和参数列表
        """
        where_clause = "WHERE 1 = 1 "
        params: List[Any] = []

        # 构建外键字段映射：别名 -> (表别名, 实际字段名)
        fk_alias_to_table = {}
        if self.foreign_key_fields:
            for fk_field in self.foreign_key_fields:
                alias_field = fk_field.get("alias_field")
                display_field = fk_field.get("display_field")
                if alias_field:
                    # 查找对应的表别名
                    for field in self.options.get("fields", []):
                        if field.get("query_fields", "").endswith(f"as {alias_field}"):
                            # 存储：(表别名, 实际字段名)
                            fk_alias_to_table[alias_field] = (field.get("table_alias"), display_field)
                            logger.debug(f"外键映射: {alias_field} -> (表:{field.get('table_alias')}, 字段:{display_field})")
                            break

        logger.debug(f"_build_where_sql: fk_alias_to_table = {fk_alias_to_table}")
        logger.debug(f"_build_where_sql: options.fields = {self.options.get('fields', [])}")
        logger.debug(f"_build_where_sql: filter = {filter}")

        if filter is not None:
            for group in filter:
                group_logic = group.get("group_logic", "and")
                condition_logic = group.get("condition_logic", "and")
                conditions = group.get("conditions", [])
                if conditions:
                    condition_clause_list = []
                    # 处理嵌套条件：支持子组和普通条件混合
                    for condition in conditions:
                        if "conditions" in condition and isinstance(condition["conditions"], list):
                            sub_group_where, sub_params = self._build_where_sql(
                                [condition], param_index=param_index
                            )
                            sub_clause = sub_group_where.replace("WHERE 1 = 1 ", "").strip()
                            # 去除子组自带的 group_logic（and/or），由外层统一处理
                            if sub_clause.startswith("and "):
                                sub_clause = sub_clause[4:]
                            elif sub_clause.startswith("or "):
                                sub_clause = sub_clause[3:]
                            if sub_clause:
                                condition_clause_list.append(sub_clause)
                                params.extend(sub_params)
                                param_index += len(sub_params)
                            continue

                        field = condition.get("field")
                        operator = condition.get("operator")
                        value = condition.get("value")
                        table_prefix = "main."

                        # 检查是否为外键别名字段
                        if field in fk_alias_to_table:
                            table_alias, actual_field = fk_alias_to_table[field]
                            table_prefix = f"{table_alias}."
                            field = actual_field  # 使用实际字段名而不是别名

                        # 检查字段名是否包含函数调用（如CAST）
                        if field and ("(" in field or ")" in field):
                            # 对于包含函数的字段名，不添加表前缀
                            field_with_prefix = field
                        else:
                            # 对于普通字段名，添加表前缀
                            field_with_prefix = f"{table_prefix}{field}"

                        clause, new_params, param_index = self._build_condition_clause(
                            field_with_prefix, operator, value, param_index
                        )
                        condition_clause_list.append(clause)
                        params.extend(new_params)

                    # 在条件之间添加空格
                    group_condition_clause = f"({f' {condition_logic} '.join(condition_clause_list)})"
                    where_clause += f" {group_logic} {group_condition_clause}"

        return where_clause, params

    # information_schema.data_type 取值分类：需要按列类型把字符串值转换后再绑定的类型
    INT_COLUMN_TYPES = {
        "smallint", "integer", "bigint",
        "int2", "int4", "int8",
        "smallserial", "serial", "bigserial",
    }
    FLOAT_COLUMN_TYPES = {
        "numeric", "decimal", "real", "double precision", "float4", "float8", "money",
    }
    BOOL_COLUMN_TYPES = {"boolean", "bool"}

    @classmethod
    def _coerce_column_value(cls, value: Any, column_type: Optional[str]) -> Any:
        """按数据库列类型把字符串值转换为 asyncpg 可绑定的 Python 类型

        前端表单项只产出字符串，直接绑定到数值/布尔/时间列会触发 asyncpg 类型错误；
        转换失败时原样返回，由数据库兜底报错。
        """
        if not column_type or not isinstance(value, str):
            return value
        text = value.strip()
        if text == "":
            return value
        data_type = column_type.lower()
        try:
            if data_type in cls.INT_COLUMN_TYPES:
                return int(text)
            if data_type in cls.FLOAT_COLUMN_TYPES:
                return float(text)
            if data_type in cls.BOOL_COLUMN_TYPES:
                return text.lower() in ("1", "true", "t", "yes", "y", "on")
            if data_type.startswith("timestamp"):
                return datetime.fromisoformat(text.replace("Z", "+00:00").replace(" ", "T", 1))
            if data_type == "date":
                return date.fromisoformat(text)
        except (ValueError, TypeError):
            return value
        return value

    def _build_condition_clause(
        self, field: str, operator: str, value: Any, param_index: int, column_type: Optional[str] = None
    ) -> Tuple[str, List[Any], int]:
        """构建单个条件子句

        Args:
            field: 字段名
            operator: 操作符
            value: 值
            param_index: 参数起始索引
            column_type: 字段的数据库列类型，用于把字符串值转换为对应 Python 类型

        Returns:
            条件子句、参数列表和新的参数索引
        """
        params: List[Any] = []
        clause = ""
        
        # 统一 aware datetime 为 naive UTC（DB 列均为 timestamp 无时区）
        def ensure_timezone(dt):
            if isinstance(dt, datetime) and dt.tzinfo is not None:
                return dt.astimezone(timezone.utc).replace(tzinfo=None)
            return dt

        # 按列类型转换后统一时区
        single_value = ensure_timezone(self._coerce_column_value(value, column_type))

        # 处理单个值
        if operator == "eq":
            clause = f"{field} = ${param_index}"
            params.append(single_value)
            param_index += 1
        elif operator == "ne":
            clause = f"{field} <> ${param_index}"
            params.append(single_value)
            param_index += 1
        elif operator == "gt":
            clause = f"{field} > ${param_index}"
            params.append(single_value)
            param_index += 1
        elif operator == "gte":
            clause = f"{field} >= ${param_index}"
            params.append(single_value)
            param_index += 1
        elif operator == "lt":
            clause = f"{field} < ${param_index}"
            params.append(single_value)
            param_index += 1
        elif operator == "lte":
            clause = f"{field} <= ${param_index}"
            params.append(single_value)
            param_index += 1
        elif operator == "like":
            clause = f"{field} like ${param_index}"
            params.append(f"%{value}%")
            param_index += 1
        elif operator == "contains":
            clause = f"{field} like ${param_index}"
            params.append(f"%{value}%")
            param_index += 1
        elif operator == "not_contains":
            clause = f"{field} not like ${param_index}"
            params.append(f"%{value}%")
            param_index += 1
        elif operator == "in":
            placeholders = [f"${i}" for i in range(param_index, param_index + len(value))]
            clause = f"{field} in ({','.join(placeholders)})"
            params.extend(
                [ensure_timezone(self._coerce_column_value(v, column_type)) for v in value]
            )
            param_index += len(value)
        elif operator == "not_in":
            placeholders = [f"${i}" for i in range(param_index, param_index + len(value))]
            clause = f"{field} not in ({','.join(placeholders)})"
            params.extend(
                [ensure_timezone(self._coerce_column_value(v, column_type)) for v in value]
            )
            param_index += len(value)
        elif operator == "is_null":
            clause = f"{field} is null"
        elif operator == "is_not_null":
            clause = f"{field} is not null"
        else:
            clause = f"{field} = ${param_index}"
            params.append(single_value)
            param_index += 1

        return clause, params, param_index

    def _build_order_by_sql(self, sort_rules: Optional[Union[list, List[SortRule]]]) -> str:
        """处理排序规则

        Args:
            sort_rules: 排序规则，格式：[{field: "id", direction: "asc"}]

        Returns:
            ORDER BY子句
        """
        order_by_clause = ""
        if sort_rules:
            # 构建外键字段映射
            fk_alias_to_table = {}
            if self.foreign_key_fields:
                for fk_field in self.foreign_key_fields:
                    alias_field = fk_field.get("alias_field")
                    if alias_field:
                        for field in self.options.get("fields", []):
                            if field.get("query_fields", "").endswith(f"as {alias_field}"):
                                fk_alias_to_table[alias_field] = field.get("table_alias")
                                break

            order_by_fields = []
            for sort_rule in sort_rules:
                field = sort_rule.get("field", "")
                order = sort_rule.get("direction", "asc")
                table_prefix = "main."

                # 检查是否为外键别名字段
                if field in fk_alias_to_table:
                    table_prefix = f"{fk_alias_to_table[field]}."

                order_by_fields.append(f"{table_prefix}{field} {order}")
            order_by_clause = "ORDER BY " + ", ".join(order_by_fields)
        return order_by_clause

    def _build_limit_offset_sql(self) -> str:
        """构建LIMIT OFFSET子句

        Returns:
            LIMIT OFFSET子句
        """
        limit_offset_clause = ""
        if self.options.get("limit"):
            limit_offset_clause = f"limit {self.options['limit']}"
        if self.options.get("offset"):
            limit_offset_clause += f" offset {self.options['offset']}"
        return limit_offset_clause

    async def create(self, data: Union[Dict[str, Any], BaseModel]) -> Optional[int]:
        """创建记录

        Args:
            data: 记录数据，可以是字典或 Pydantic 模型

        Returns:
            创建的记录ID或None
        """
        # 如果是 Pydantic 模型，转换为字典
        if isinstance(data, BaseModel):
            data = data.model_dump()

        # 应用保存前的数据转换（如 URL 转 key）
        data = self.transform_for_save(data)

        if not data:
            raise Exception("创建记录失败：数据不能为空")

        fields = list(data.keys())
        values = list(data.values())
        placeholders = [f"${i+1}" for i in range(len(values))]

        sql = f"INSERT INTO {self.table_name} ({', '.join(fields)}) VALUES ({', '.join(placeholders)}) RETURNING id"

        result = await self.db.fetch_one(sql, values)
        return result.get("id") if result else None

    async def update(self, data: Union[Dict[str, Any], BaseModel], filter: Union[list, List[FilterGroup]]) -> int:
        """更新记录

        Args:
            data: 更新数据，可以是字典或 Pydantic 模型
            filter: 过滤条件

        Returns:
            更新的记录数
        """
        # 如果是 Pydantic 模型，转换为字典，只包含值不为None的字段
        if isinstance(data, BaseModel):
            data_dict = data.model_dump(exclude_unset=True)
        else:
            data_dict = data.copy() if isinstance(data, dict) else {}

        # 应用保存前的数据转换（如 URL 转 key）
        transformed_data = self.transform_for_save(data_dict)

        # 过滤掉值为None的字段
        filtered_data = {k: v for k, v in transformed_data.items() if v is not None}

        set_clause = []
        params = []
        param_index = 1

        for field, value in filtered_data.items():
            if field == "id":
                continue
            set_clause.append(f"{field} = ${param_index}")
            params.append(value)
            param_index += 1

        where_clause, where_params = self._build_where_sql(filter, param_index=param_index)
        params.extend(where_params)

        sql = f"UPDATE {self.table_name} as main SET {', '.join(set_clause)} {where_clause}"

        await self.db.execute(sql, params)
        return 0  # type: ignore[no-any-return]

    async def delete(self, filter: Union[list, List[FilterGroup]]) -> int:
        """删除记录

        Args:
            filter: 过滤条件

        Returns:
            删除的记录数
        """
        where_clause, params = self._build_where_sql(filter)

        condition = where_clause.replace("WHERE 1 = 1", "").strip()
        condition = condition.lstrip()

        if condition.upper().startswith("AND "):
            condition = condition[4:].lstrip()
        elif condition.upper().startswith("OR "):
            condition = condition[3:].lstrip()

        if condition.startswith("(") and condition.endswith(")"):
            condition = condition[1:-1].strip()

        # DELETE 语句没有表别名，需去掉条件中所有 "main." 限定符；
        # 用负向后顾避免误伤标识符内部（如 domain.main 不会被改写成 doma）
        condition = re.sub(r"(?<![A-Za-z0-9_])main\.", "", condition)

        logger.debug(f"删除操作 - 表名: {self.table_name}, 条件: {condition}, 参数: {params}")

        # 使用 db.delete 方法，它返回影响的行数
        result = await self.db.delete(self.table_name, condition, params)

        logger.debug(f"删除操作结果: {result}")
        return result

    async def update_by_id(self, id: int, data: Union[Dict[str, Any], BaseModel]) -> int:
        """根据ID更新记录

        Args:
            id: 记录ID
            data: 更新数据，可以是字典或 Pydantic 模型

        Returns:
            更新的记录数
        """
        filter = [
            {
                "group_logic": "and",
                "condition_logic": "and",
                "conditions": [{"field": "id", "operator": "eq", "value": id}],
            }
        ]
        return await self.update(data, filter)

    async def delete_by_id(self, id: int) -> int:
        """根据ID删除记录

        Args:
            id: 记录ID

        Returns:
            删除的记录数
        """
        filter = [
            {
                "group_logic": "and",
                "condition_logic": "and",
                "conditions": [{"field": "id", "operator": "eq", "value": id}],
            }
        ]
        return await self.delete(filter)

    async def destroy_by_id(self, id: int) -> int:
        """根据ID物理删除记录

        Args:
            id: 记录ID

        Returns:
            删除的记录数
        """
        return await self.delete_by_id(id)
