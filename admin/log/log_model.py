"""系统日志模型模块

负责日志表（log）的数据库读写，仅包含数据库逻辑，不含业务逻辑。
表名由基类自动拼接 PG_PREFIX（x_），即 x_log。
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from framework.core.model import Model, FilterGroup, SortRule


class LogModel(Model):
    """系统日志模型

    表：log（基类自动拼接 x_ 前缀，即 x_log）
    """

    # 写入方是 framework/core/log_db.py；这里只负责查询与清理
    LEVEL_LIST = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    def __init__(self) -> None:
        """初始化模型"""
        super().__init__("log")
        # 列名 → 数据库类型（条件构造器按列类型转换取值），实例级缓存
        self._column_types: Optional[Dict[str, str]] = None

    async def get_column_types(self) -> Dict[str, str]:
        """表列名 → information_schema.data_type 映射（按模型实例缓存）"""
        if self._column_types is None:
            self._column_types = await self.db.get_table_column_types(self.table_name)
        return self._column_types

    def _coerce_filter_values(self, filter: Optional[list]) -> Optional[list]:
        """把过滤条件里的字符串取值按列类型转为 asyncpg 可绑定的 Python 类型

        前端只产出字符串，直接绑定到 timestamp/date 等列会触发 asyncpg 类型错误，
        这里复用框架的 _coerce_column_value 按真实列类型转换（如 create_time）。
        """
        column_types = self._column_types or {}
        if not isinstance(filter, list) or not column_types:
            return filter

        for group in filter:
            if not isinstance(group, dict):
                continue
            for condition in group.get("conditions") or []:
                if not isinstance(condition, dict):
                    continue
                column_type = column_types.get(condition.get("field"))
                if not column_type:
                    continue
                value = condition.get("value")
                if isinstance(value, list):
                    condition["value"] = [self._coerce_column_value(v, column_type) for v in value]
                else:
                    condition["value"] = self._coerce_column_value(value, column_type)
        return filter

    async def get_log_list(
        self,
        filter: Optional[Union[list, List[FilterGroup]]] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        sort_rules: Optional[Union[list, List[SortRule]]] = None,
        fields: str = "*",
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """查询日志列表

        Args:
            filter: 过滤条件
            page: 页码
            limit: 每页条数
            sort_rules: 排序规则
            fields: 字段选择

        Returns:
            记录列表，或包含 items 与 total 的字典
        """
        await self.get_column_types()
        return await self.get_list(
            filter=self._coerce_filter_values(filter),
            page=page,
            limit=limit,
            sort_rules=sort_rules,
            fields=fields,
        )

    async def get_log_detail(self, log_id: int) -> Optional[Dict[str, Any]]:
        """根据ID查询日志（排除已软删除记录）

        Args:
            log_id: 记录ID

        Returns:
            记录字典或 None
        """
        filter = [
            {
                "group_logic": "and",
                "condition_logic": "and",
                "conditions": [
                    {"field": "id", "operator": "eq", "value": log_id},
                    {"field": "is_deleted", "operator": "eq", "value": 0},
                ],
            }
        ]
        return await self.get_first(filter=filter, fields="*")

    async def delete_log(self, log_id: int, user_id: int) -> int:
        """软删除日志并写入完整审计信息

        Args:
            log_id: 记录ID
            user_id: 操作人ID

        Returns:
            受影响行数
        """
        now = datetime.now(timezone.utc)
        filter = [
            {
                "group_logic": "and",
                "condition_logic": "and",
                "conditions": [{"field": "id", "operator": "eq", "value": log_id}],
            }
        ]
        return await self.update(
            {"is_deleted": 1, "delete_time": now, "delete_by": user_id,
             "update_by": user_id, "update_time": now},
            filter,
        )

    async def soft_delete_by_ids(self, ids: List[int], user_id: Optional[int] = None) -> int:
        """按ID列表批量软删除

        Args:
            ids: 记录ID列表
            user_id: 数据隔离用户ID，非 None 时仅删该用户的记录

        Returns:
            实际删除行数
        """
        if not ids:
            return 0
        now = datetime.now(timezone.utc)
        conditions: List[Dict[str, Any]] = [{"field": "id", "operator": "in", "value": ids}]
        if user_id is not None:
            conditions.append({"field": "user_id", "operator": "eq", "value": user_id})

        await self.update(
            {"is_deleted": 1, "delete_time": now, "delete_by": user_id,
             "update_by": user_id, "update_time": now},
            [{"group_logic": "and", "condition_logic": "and", "conditions": conditions}],
        )
        return len(ids)

    async def clean_old_logs(self, before: datetime, user_id: Optional[int] = None) -> int:
        """物理清理指定时间之前的日志

        日志表会持续增长，过期数据用软删除没有意义（查的时候还得再过滤），
        所以这里直接物理删除；调用方（控制器）负责校验天数下限与管理员权限。

        Args:
            before: 清理该时间点之前的记录
            user_id: 数据隔离用户ID，非 None 时仅清理该用户的记录

        Returns:
            实际删除行数
        """
        conditions: List[Dict[str, Any]] = [{"field": "create_time", "operator": "lt", "value": before}]
        if user_id is not None:
            conditions.append({"field": "user_id", "operator": "eq", "value": user_id})

        result = await self.get_log_list(
            filter=[{"group_logic": "and", "condition_logic": "and", "conditions": conditions}],
            fields="id",
        )
        if isinstance(result, dict):
            result = result.get("items", [])
        if not isinstance(result, list) or not result:
            return 0

        rows = [{"id": item["id"]} for item in result]
        deleted = 0
        for row in rows:
            deleted += await self.delete(
                [{"group_logic": "and", "condition_logic": "and",
                  "conditions": [{"field": "id", "operator": "eq", "value": row["id"]}]}]
            )
        return deleted
