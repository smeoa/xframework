"""系统日志控制器模块

负责日志表（x_log）的业务逻辑：列表、详情、删除、批量删除、按天清理、统计。

数据隔离规则与既有模块一致：
管理员可访问全部日志；非管理员只允许看到/操作 user_id = 自己的日志（系统日志 user_id 可能为空，
这类记录只有管理员能看）。

写入不在这里：日志由 framework/core/log_db.py 按 .env 的 LOG_LEVEL 过滤后异步落库。
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, Request

from framework.core.auth import get_current_user
from framework.core.config import config
from framework.core.controller import Controller
from framework.core import log_db

from .log_model import LogModel

logger = logging.getLogger(__name__)

# 清理日志的最低下限：少于 7 天不让清，防止误删刚发生的故障证据
MIN_CLEAN_DAYS = 7


class LogController(Controller):
    """系统日志控制器"""

    SEARCH_FIELDS = ["message", "logger", "module", "request_path"]

    def __init__(self, request: Request) -> None:
        """初始化控制器

        Args:
            request: FastAPI 请求对象
        """
        super().__init__(request)
        self.model = LogModel()

    # ==================== 查询 ====================

    async def list(self):
        """获取日志列表

        数据隔离：非管理员强制追加 user_id = 当前用户id，并忽略前端传入的 user_id 条件。

        Returns:
            列表响应
        """
        try:
            current_user = await get_current_user(self.request)
            data = await self._get_request_data()

            page = data.get("page", 1)
            limit = data.get("limit", 20)
            keyword = data.get("keyword", "")
            search_fields = data.get("searchFields", [])
            filter_conditions = data.get("filter", [])
            sort_rules = data.get("sort", [])

            base_filter: List[Dict[str, Any]] = [
                {
                    "group_logic": "and",
                    "condition_logic": "and",
                    "conditions": [{"field": "is_deleted", "operator": "eq", "value": 0}],
                }
            ]

            if keyword:
                if not search_fields:
                    search_fields = self.SEARCH_FIELDS
                base_filter.append(
                    {
                        "group_logic": "and",
                        "condition_logic": "or",
                        "conditions": [
                            {"field": field, "operator": "contains", "value": keyword}
                            for field in search_fields
                        ],
                    }
                )

            if current_user["is_admin"]:
                if filter_conditions:
                    base_filter.extend(filter_conditions)
            else:
                base_filter.extend(self._strip_user_id_conditions(filter_conditions))
                base_filter.append(
                    {
                        "group_logic": "and",
                        "condition_logic": "and",
                        "conditions": [
                            {"field": "user_id", "operator": "eq", "value": current_user["id"]}
                        ],
                    }
                )

            if not sort_rules:
                sort_rules = [{"field": "create_time", "direction": "desc"}]

            result = await self.model.get_log_list(
                filter=base_filter, page=page, limit=limit, sort_rules=sort_rules, fields="*"
            )
            if isinstance(result, dict) and "items" in result:
                return self.success(result)

            items = result if isinstance(result, list) else []
            return self.success({"items": items, "total": len(items)})
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取日志列表失败: {str(e)}", exc_info=True)
            return self.error(message=str(e))

    async def detail(self):
        """获取日志详情

        非管理员访问他人（或系统）日志返回 403。

        Returns:
            详情响应
        """
        try:
            current_user = await get_current_user(self.request)
            data = await self._get_request_data()
            payload = self._unwrap(data)

            log_id = payload.get("id")
            if not log_id:
                return self.error(400, "ID不能为空")

            record = await self.model.get_log_detail(log_id)
            if not record:
                return self.error(404, "记录不存在")

            if not current_user["is_admin"] and record.get("user_id") != current_user["id"]:
                return self.error(403, "无权访问该记录")

            return self.success(record)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取日志详情失败: {str(e)}", exc_info=True)
            return self.error(message=str(e))

    async def stats(self):
        """日志统计：按级别计数 + 落库组件运行态

        Returns:
            统计响应
        """
        try:
            current_user = await get_current_user(self.request)

            counts: Dict[str, int] = {}
            for level in LogModel.LEVEL_LIST:
                conditions: List[Dict[str, Any]] = [
                    {"field": "level", "operator": "eq", "value": level},
                    {"field": "is_deleted", "operator": "eq", "value": 0},
                ]
                if not current_user["is_admin"]:
                    conditions.append(
                        {"field": "user_id", "operator": "eq", "value": current_user["id"]}
                    )
                rows = await self.model.get_log_list(
                    filter=[{"group_logic": "and", "condition_logic": "and", "conditions": conditions}],
                    fields="id",
                )
                if isinstance(rows, dict):
                    rows = rows.get("items", [])
                counts[level] = len(rows) if isinstance(rows, list) else 0

            return self.success({"levels": counts, "writer": log_db.stats()})
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取日志统计失败: {str(e)}", exc_info=True)
            return self.error(message=str(e))

    # ==================== 写入（外部程序） ====================

    # 单次最多接收多少条，防止外部程序一次灌爆
    MAX_BATCH = 200

    async def write_log(self):
        """外部程序写入日志（采集脚本 / 定时任务等）

        入参（两种形式都支持）：
            {"logs": [{"level": "INFO", "message": "...", "logger": "1688.collect",
                       "excInfo": "...", "requestId": "..."}, ...]}      批量
            {"level": "INFO", "message": "..."}                          单条

        规则：
            - level 必须是 DEBUG/INFO/WARNING/ERROR/CRITICAL，非法直接 400；
            - 低于 `.env` 里 LOG_LEVEL 的记录**不落库**（逐条在 details 里说明），
              与后端自身日志的口径保持一致；
            - user_id 强制取当前登录用户，忽略传入值（数据隔离与其它模块一致）；
            - 消息超长截断，最多一次 MAX_BATCH 条。

        Returns:
            写入结果响应（accepted / written / dropped / details）
        """
        try:
            current_user = await get_current_user(self.request)
            data = await self._get_request_data()
            payload = self._unwrap(data)

            raw_items = payload.get("logs")
            if raw_items is None:
                raw_items = [payload]
            if not isinstance(raw_items, list) or not raw_items:
                return self.error(400, "logs 不能为空")
            if len(raw_items) > self.MAX_BATCH:
                return self.error(400, "单次最多写入 %d 条" % self.MAX_BATCH)

            min_level_name = config.get("LOG_LEVEL", "INFO")
            min_level = log_db._level_of(min_level_name)

            details: List[Dict[str, Any]] = []
            to_insert: List[Dict[str, Any]] = []
            dropped = 0
            now = datetime.now(timezone.utc)

            for index, item in enumerate(raw_items):
                if not isinstance(item, dict):
                    return self.error(400, "logs[%d] 必须是对象" % index)

                level_name = str(item.get("level") or "INFO").upper()
                if level_name not in LogModel.LEVEL_LIST:
                    return self.error(400, "logs[%d] 级别非法: %s" % (index, level_name))

                message = item.get("message")
                if not message or not str(message).strip():
                    return self.error(400, "logs[%d] message 不能为空" % index)
                message = str(message)
                if len(message) > log_db.MAX_MESSAGE_LEN:
                    message = message[: log_db.MAX_MESSAGE_LEN] + "...(截断)"

                if log_db._level_of(level_name) < min_level:
                    dropped += 1
                    details.append({"index": index, "level": level_name, "written": False,
                                    "reason": "低于配置级别 %s" % min_level_name.upper()})
                    continue

                to_insert.append(
                    {
                        "level": level_name,
                        "logger": str(item.get("logger") or "external")[:128],
                        "module": str(item.get("module") or "external")[:128],
                        "func": str(item.get("func") or "")[:128],
                        "line": int(item.get("line") or 0),
                        "message": message,
                        "exc_info": item.get("excInfo") or item.get("exc_info"),
                        "request_id": str(item.get("requestId") or item.get("request_id") or "")[:64] or None,
                        "request_path": str(item.get("requestPath") or item.get("request_path") or "")[:255] or None,
                        "request_method": str(item.get("requestMethod") or item.get("request_method") or "")[:16] or None,
                        "client_ip": str(item.get("clientIp") or item.get("client_ip") or "")[:64] or None,
                        "user_id": current_user["id"],
                        "create_time": now,
                    }
                )
                details.append({"index": index, "level": level_name, "written": True, "reason": None})

            written = await log_db.insert_now(to_insert)

            # 写入动作本身也留一条审计（走正常日志通道，便于追踪是谁在灌日志）
            logger.info("外部写入日志 %d 条（级别阈值 %s，丢弃 %d 条），操作人 %s"
                        % (written, min_level_name.upper(), dropped, current_user["username"]))

            return self.success(
                {"accepted": len(raw_items), "written": written, "dropped": dropped, "details": details},
                "已接收",
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"外部写入日志失败: {str(e)}", exc_info=True)
            return self.error(message=str(e))

    # ==================== 删除 ====================

    async def delete(self):
        """删除单条日志（软删除）

        Returns:
            删除结果响应
        """
        try:
            current_user = await get_current_user(self.request)
            data = await self._get_request_data()
            payload = self._unwrap(data)

            log_id = payload.get("id")
            if not log_id:
                return self.error(400, "ID不能为空")

            record = await self.model.get_log_detail(log_id)
            if not record:
                return self.error(404, "记录不存在")

            if not current_user["is_admin"] and record.get("user_id") != current_user["id"]:
                return self.error(403, "无权删除该记录")

            await self.model.delete_log(log_id, current_user["id"])
            return self.success(None, "删除成功")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"删除日志失败: {str(e)}", exc_info=True)
            return self.error(message=str(e))

    async def batch_log(self):
        """批量删除指定ID的日志

        Returns:
            删除结果响应
        """
        try:
            current_user = await get_current_user(self.request)
            data = await self._get_request_data()
            payload = self._unwrap(data)

            ids = payload.get("ids") or []
            if not isinstance(ids, list) or not ids:
                return self.error(400, "ID列表不能为空")

            isolate = self._isolate_user_id(current_user)
            matched = await self.model.get_log_list(
                filter=[
                    {
                        "group_logic": "and",
                        "condition_logic": "and",
                        "conditions": [
                            {"field": "id", "operator": "in", "value": ids},
                            {"field": "is_deleted", "operator": "eq", "value": 0},
                            *([{"field": "user_id", "operator": "eq", "value": isolate}] if isolate is not None else []),
                        ],
                    }
                ],
                fields="id",
            )
            if isinstance(matched, dict):
                matched = matched.get("items", [])
            matched_ids = [item["id"] for item in matched] if isinstance(matched, list) else []
            if not matched_ids:
                return self.success({"deleted": 0}, "没有可删除的记录")

            deleted = await self.model.soft_delete_by_ids(matched_ids, isolate)
            return self.success({"deleted": deleted}, "批量删除成功")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"批量删除日志失败: {str(e)}", exc_info=True)
            return self.error(message=str(e))

    async def batch_all_log(self):
        """按筛选条件批量软删除日志

        无任何筛选条件时拒绝执行，避免误清空全表。

        Returns:
            删除结果响应
        """
        try:
            current_user = await get_current_user(self.request)
            data = await self._get_request_data()

            raw_filter = data.get("filter") or []
            has_filter = any(
                isinstance(group, dict) and group.get("conditions") for group in raw_filter
            )
            has_keyword = bool(data.get("keyword")) and bool(data.get("searchFields"))
            has_ids = bool(data.get("ids"))
            if not (has_filter or has_keyword or has_ids):
                return self.error(400, "请至少提供一个筛选条件")

            isolate = self._isolate_user_id(current_user)
            filter_conditions = self._build_filter(data, isolate)

            matched = await self.model.get_log_list(filter=filter_conditions, fields="id")
            if isinstance(matched, dict):
                matched = matched.get("items", [])
            if not isinstance(matched, list) or not matched:
                return self.success({"deleted": 0}, "没有符合条件的记录")

            deleted = await self.model.soft_delete_by_ids([item["id"] for item in matched], isolate)
            return self.success({"deleted": deleted}, "批量删除成功")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"批量删除日志失败: {str(e)}", exc_info=True)
            return self.error(message=str(e))

    async def clean_log(self):
        """清理 N 天前的日志（物理删除，仅管理员，最少 7 天）

        Returns:
            清理结果响应
        """
        try:
            current_user = await get_current_user(self.request)
            if not current_user["is_admin"]:
                return self.error(403, "仅管理员可清理日志")

            data = await self._get_request_data()
            payload = self._unwrap(data)
            days = payload.get("beforeDays", payload.get("before_days", 30))
            try:
                days = int(days)
            except Exception:
                return self.error(400, "天数格式不正确")
            if days < MIN_CLEAN_DAYS:
                return self.error(400, "最少需要保留 %d 天" % MIN_CLEAN_DAYS)

            before = datetime.now(timezone.utc) - timedelta(days=days)
            deleted = await self.model.clean_old_logs(before)
            logger.warning(f"清理 {days} 天前的日志，共删除 {deleted} 条（操作人 {current_user['id']}）")
            return self.success({"deleted": deleted, "beforeDays": days}, "清理完成")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"清理日志失败: {str(e)}", exc_info=True)
            return self.error(message=str(e))

    # ==================== 内部工具 ====================

    def _isolate_user_id(self, current_user: Dict[str, Any]) -> Optional[int]:
        """返回数据隔离用户ID：管理员 None（全部），非管理员自身ID"""
        return None if current_user["is_admin"] else current_user["id"]

    def _unwrap(self, data: Any) -> Dict[str, Any]:
        """兼容前端以 data 包裹请求体与直接传参两种形式"""
        if not isinstance(data, dict):
            return {}
        inner = data.get("data")
        return inner if isinstance(inner, dict) else data

    def _strip_user_id_conditions(self, filter_conditions: Any) -> List[Dict[str, Any]]:
        """剔除过滤条件中所有 user_id 条件（用于非管理员数据隔离）"""
        if not isinstance(filter_conditions, list):
            return []
        cleaned: List[Dict[str, Any]] = []
        for group in filter_conditions:
            if not isinstance(group, dict):
                continue
            conditions = group.get("conditions", [])
            if not isinstance(conditions, list):
                continue
            remaining = [
                cond for cond in conditions if isinstance(cond, dict) and cond.get("field") != "user_id"
            ]
            if not remaining:
                continue
            new_group = dict(group)
            new_group["conditions"] = remaining
            cleaned.append(new_group)
        return cleaned

    def _build_filter(self, data: Dict[str, Any], user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """构建批量操作的过滤条件（固定 is_deleted=0，非管理员强制 user_id）"""
        processed: List[Dict[str, Any]] = [
            {
                "group_logic": "and",
                "condition_logic": "and",
                "conditions": [{"field": "is_deleted", "operator": "eq", "value": 0}],
            }
        ]

        for group in data.get("filter") or []:
            if not isinstance(group, dict):
                continue
            conditions = [
                {
                    "field": cond.get("field"),
                    "operator": cond.get("operator", cond.get("method")),
                    "value": cond.get("value"),
                }
                for cond in (group.get("conditions") or [])
                if isinstance(cond, dict)
                and not (user_id is not None and cond.get("field") == "user_id")
            ]
            if conditions:
                processed.append(
                    {
                        "group_logic": group.get("group_logic", group.get("groupLogic", "and")),
                        "condition_logic": group.get("condition_logic", group.get("condLogic", "and")),
                        "conditions": conditions,
                    }
                )

        keyword = data.get("keyword")
        search_fields = data.get("searchFields") or []
        if keyword and search_fields:
            processed.append(
                {
                    "group_logic": "and",
                    "condition_logic": "or",
                    "conditions": [
                        {"field": field, "operator": "contains", "value": keyword}
                        for field in search_fields
                    ],
                }
            )

        ids = data.get("ids") or []
        if ids:
            processed.append(
                {
                    "group_logic": "and",
                    "condition_logic": "and",
                    "conditions": [{"field": "id", "operator": "in", "value": ids}],
                }
            )

        if user_id is not None:
            processed.append(
                {
                    "group_logic": "and",
                    "condition_logic": "and",
                    "conditions": [{"field": "user_id", "operator": "eq", "value": user_id}],
                }
            )

        return processed
