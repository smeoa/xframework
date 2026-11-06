"""权限组数据模型

权限组 = 某个菜单下的一个业务权限场景，向「部门 / 角色 / 人员」三类主体绑定，
组内组合「操作权限点 + 字段权限 + 数据权限」，是现有 RBAC 之上的叠加授权层。

涉及表：
- x_permission_group            权限组主表
- x_permission_group_permission 组-操作权限点
- x_permission_group_field      组-字段权限（可见 / 可编辑）
- x_permission_group_data       组-数据权限（scope + 自定义部门）
- x_permission_group_subject    组-主体绑定（dept / role / user）
- x_user_permission_group       用户激活组（每用户至多一条 is_active=1，实现按组互斥切换）

数据权限 scope 取值：all=全部 / dept=本部门 / dept_and_sub=本部门及下级 /
self=本人 / custom=自定义部门 / none=无数据。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from framework.core.auth import get_user_group_ids
from framework.core.model import Model

# 权限点类型：0=分组（仅树结构承载）
TYPE_GROUP = 0

# 绑定主体类型
SUBJECT_DEPT = "dept"
SUBJECT_ROLE = "role"
SUBJECT_USER = "user"
SUBJECT_TYPES = (SUBJECT_DEPT, SUBJECT_ROLE, SUBJECT_USER)

# 数据权限范围
SCOPE_ALL = "all"
SCOPE_DEPT = "dept"
SCOPE_DEPT_AND_SUB = "dept_and_sub"
SCOPE_SELF = "self"
SCOPE_CUSTOM = "custom"
SCOPE_NONE = "none"
DATA_SCOPES = (SCOPE_ALL, SCOPE_DEPT, SCOPE_DEPT_AND_SUB, SCOPE_SELF, SCOPE_CUSTOM, SCOPE_NONE)

# 业务模块 -> 业务表（字段权限目录取该表的业务列）
MODULE_TABLES: Dict[str, str] = {
    "shop": "shop",
    "collectqueue": "collect_queue",
    "product": "product_detail_origin",
}

# 字段权限目录需排除的系统列由 _system_columns() 自动识别（所有登记业务表共有的审计族列），
# 无需人工维护；业务字段中文名优先取 FIELD_LABELS，其次取数据库列注释（见 _comment_label）。

# 业务字段中文名（显式覆盖；未登记时回退为数据库列注释，再回退为字段名）
FIELD_LABELS: Dict[str, Dict[str, str]] = {
    "shop": {
        "platform_code": "平台编码",
        "platform_id": "平台ID",
        "shop_name": "店铺名称",
        "shop_id": "平台店铺ID",
        "shop_alias": "店铺别名",
        "shop_account": "店铺账号",
        "access_token": "访问令牌",
        "refresh_token": "刷新令牌",
        "app_key": "应用Key",
        "app_secret": "应用密钥",
        "expires_in": "令牌有效期",
        "scope": "授权范围",
        "third_auth_date": "三方授权时间",
        "third_auth_pass_date": "三方授权通过时间",
        "status": "状态",
        "remark": "备注",
        "owner": "负责人",
        "supplier_id": "供应商ID",
        "supplier_no": "供应商编号",
        "supplier_name": "供应商名称",
        "supplier_status_id": "供应商状态",
        "cur_level": "当前层级",
        "grade": "等级",
        "verify": "认证",
        "review_score": "评价分",
        "seller_score": "卖家分",
        "is_power_seller": "实力卖家",
        "store_name": "平台店铺名称",
        "store_head_img": "店铺头像",
        "store_url": "店铺链接",
    },
    "collectqueue": {
        "title": "标题",
        "price": "价格",
        "currency": "币种",
        "site": "站点",
        "url": "链接",
        "image": "图片",
        "status": "状态",
        "fail_reason": "失败原因",
    },
    "product": {
        "data_id": "原始产品汇总ID",
        "source_site": "采集来源站点",
        "source_platform": "来源平台",
        "source_goods_id": "平台商品ID",
        "source_url": "采集来源链接",
        "subject": "商品标题",
        "category_id": "类目ID",
        "category_name": "类目名称",
        "unit": "单位",
        "price": "价格",
        "stocks": "库存",
        "weight": "重量",
        "cube_l": "长",
        "cube_w": "宽",
        "cube_h": "高",
        "video": "视频地址",
        "text": "描述文本",
        "html": "描述HTML",
        "properties": "属性",
        "keywords": "关键词",
        "main_images": "主图",
        "detail_images": "详情图",
        "videos": "视频列表",
        "skus": "SKU列表",
        "tags": "产品标签",
        "exts": "扩展",
        "custom_fields": "自定义字段",
        "raw": "原始数据",
    },
}


class PermissionGroupModel(Model):
    """权限组模型：管理权限组及其权限点 / 字段 / 数据 / 主体绑定 / 用户激活组"""

    def __init__(self):
        super().__init__("permission_group")
        # 显式置空外键映射，避免 Model 自动 JOIN 不存在的字段
        self.foreign_key_fields = []

        self.group_permission_model = Model("permission_group_permission")
        self.group_permission_model.foreign_key_fields = []

        self.group_field_model = Model("permission_group_field")
        self.group_field_model.foreign_key_fields = []

        self.group_data_model = Model("permission_group_data")
        self.group_data_model.foreign_key_fields = []
        self.group_data_model.jsonb_fields = ["custom_dept_ids"]

        self.group_subject_model = Model("permission_group_subject")
        self.group_subject_model.foreign_key_fields = []

        self.user_group_model = Model("user_permission_group")
        self.user_group_model.foreign_key_fields = []

        self.permission_model = Model("permission")
        self.permission_model.foreign_key_fields = []

        self.role_model = Model("role")
        self.role_model.foreign_key_fields = []

        self.dept_model = Model("dept")
        self.dept_model.foreign_key_fields = []

        self.user_model = Model("user")
        self.user_model.foreign_key_fields = []

    # ==================== 内部工具 ====================

    @staticmethod
    def _where(conditions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """构造 and 过滤组

        Args:
            conditions: 条件列表

        Returns:
            Model 可识别的过滤条件
        """
        return [{"group_logic": "and", "condition_logic": "and", "conditions": conditions}]

    @staticmethod
    def _not_deleted(field: str = "is_deleted") -> Dict[str, Any]:
        """软删除过滤条件"""
        return {"field": field, "operator": "eq", "value": 0}

    async def _count_by_group(self, table: str, group_ids: List[int]) -> Dict[int, int]:
        """统计各权限组的子表记录数

        Args:
            table: 子表全名（含前缀）
            group_ids: 权限组ID列表

        Returns:
            {group_id: 记录数}
        """
        if not group_ids:
            return {}
        rows = await self.db.fetch_all(
            f"SELECT group_id, COUNT(*) AS cnt FROM {table} "
            "WHERE group_id = ANY($1::bigint[]) AND is_deleted = 0 GROUP BY group_id",
            [group_ids],
        )
        return {int(r["group_id"]): int(r["cnt"]) for r in rows}

    async def _get_menu(self, menu_id: Optional[int]) -> Optional[Dict[str, Any]]:
        """按菜单权限点ID查询菜单

        Args:
            menu_id: 菜单权限点ID

        Returns:
            菜单信息或 None
        """
        if not menu_id:
            return None
        return await self.permission_model.get_first(
            filter=self._where(
                [
                    {"field": "id", "operator": "eq", "value": menu_id},
                    {"field": "is_deleted", "operator": "eq", "value": 0},
                ]
            ),
            fields="id, title, code, module, path, type",
        )

    async def _resolve_menu_id(self, payload: Dict[str, Any]) -> int:
        """解析权限组归属菜单ID

        Args:
            payload: 请求数据，支持 menu_id 或 menu_code

        Returns:
            菜单权限点ID

        Raises:
            Exception: 菜单不存在
        """
        menu_id = payload.get("menu_id")
        if menu_id:
            menu = await self._get_menu(int(menu_id))
            if not menu:
                raise Exception("菜单不存在")
            return int(menu["id"])

        menu_code = payload.get("menu_code")
        if menu_code:
            menu = await self.permission_model.get_first(
                filter=self._where(
                    [
                        {"field": "code", "operator": "eq", "value": menu_code},
                        {"field": "is_deleted", "operator": "eq", "value": 0},
                    ]
                ),
                fields="id, code, type",
            )
            if not menu:
                raise Exception(f"菜单不存在: {menu_code}")
            return int(menu["id"])

        raise Exception("菜单不能为空")

    async def _resolve_module(self, menu_id: int) -> str:
        """解析权限组所属业务模块（按菜单自动推导，不依赖前端传值）

        Args:
            menu_id: 菜单权限点ID

        Returns:
            业务模块编码

        Raises:
            Exception: 菜单未关联业务模块
        """
        menu = await self._get_menu(menu_id)
        menu_code = (menu or {}).get("code") or ""
        # 业务模块以菜单权限点自身的 module 为准（由 init_permission 维护）
        module = (menu or {}).get("module")
        if not module:
            raise Exception(f"菜单 {menu_code} 未关联业务模块")
        return module

    async def _generate_group_code(self, module: str) -> str:
        """自动生成权限组编码（pg:模块:序号）

        Args:
            module: 业务模块编码

        Returns:
            该模块下未被占用的编码
        """
        prefix = f"pg:{module}:"
        rows = await self.db.fetch_all(
            f"SELECT code FROM {self.db_prefix}permission_group "
            "WHERE module = $1 AND is_deleted = 0 AND code LIKE $2",
            [module, f"{prefix}%"],
        )
        used = {
            int(tail)
            for tail in ((row["code"] or "")[len(prefix):] for row in rows)
            if tail.isdigit()
        }
        seq = 1
        while seq in used:
            seq += 1
        return f"{prefix}{seq:03d}"

    @staticmethod
    def _is_audit_column(name: str) -> bool:
        """判断列名是否属于审计族（主键 / 归属 / 软删除 / 操作人 / 操作时间）

        Args:
            name: 列名

        Returns:
            是否属于审计族
        """
        return (
            name in {"id", "data_id", "user_id", "is_deleted"}
            or name.endswith("_by")
            or name.endswith("_time")
        )

    async def _system_columns(self) -> set:
        """自动识别字段权限目录需排除的系统列

        取所有登记业务表列名的交集（避免误伤某些表特有的业务列，如 claim_time /
        locked_by），再按审计族命名规则过滤。

        Returns:
            系统列名集合
        """
        common: Optional[set] = None
        for table in set(MODULE_TABLES.values()):
            rows = await self.db.fetch_all(
                "SELECT column_name FROM information_schema.columns WHERE table_name = $1",
                [f"{self.db_prefix}{table}"],
            )
            cols = {r["column_name"] for r in rows}
            common = cols if common is None else (common & cols)
        return {c for c in (common or set()) if self._is_audit_column(c)}

    async def _column_comments(self, table: str) -> Dict[str, str]:
        """查询数据表的列注释

        Args:
            table: 表全名（含前缀）

        Returns:
            {列名: 注释}
        """
        rows = await self.db.fetch_all(
            "SELECT a.attname AS column_name, col_description(a.attrelid, a.attnum) AS comment "
            "FROM pg_catalog.pg_attribute a "
            "JOIN pg_catalog.pg_class c ON c.oid = a.attrelid "
            "JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace "
            "WHERE c.relname = $1 AND n.nspname = current_schema() "
            "AND a.attnum > 0 AND NOT a.attisdropped ORDER BY a.attnum",
            [table],
        )
        return {r["column_name"]: r["comment"] for r in rows if r.get("comment")}

    @staticmethod
    def _comment_label(comment: Optional[str]) -> str:
        """从列注释中裁剪出简短中文名（去掉括号补充说明等）

        Args:
            comment: 列注释

        Returns:
            裁剪后的中文名，注释为空时返回空串
        """
        text = (comment or "").strip()
        if not text:
            return ""
        cut = len(text)
        for sep in ("（", "(", "：", ":", "，", ","):
            idx = text.find(sep)
            if idx > 0:
                cut = min(cut, idx)
        return text[:cut].strip()

    async def _get_group(self, group_id: int) -> Optional[Dict[str, Any]]:
        """查询未删除的权限组

        Args:
            group_id: 权限组ID

        Returns:
            权限组或 None
        """
        return await self.get_first(
            filter=self._where(
                [
                    {"field": "id", "operator": "eq", "value": group_id},
                    self._not_deleted(),
                ]
            ),
            fields="*",
        )

    async def _require_group(self, group_id: Any) -> Dict[str, Any]:
        """校验权限组存在

        Args:
            group_id: 权限组ID

        Returns:
            权限组记录

        Raises:
            Exception: 权限组不存在
        """
        if not group_id:
            raise Exception("权限组ID不能为空")
        group = await self._get_group(int(group_id))
        if not group:
            raise Exception("权限组不存在")
        return group

    # ==================== 权限组主表 ====================

    async def get_group_list(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """查询权限组列表（分页）

        Args:
            data: 请求数据（page / limit / keyword / menu_id / module / status）

        Returns:
            包含 items 与 total 的字典
        """
        groups: List[Dict[str, Any]] = self._where([self._not_deleted()])
        keyword = (data.get("keyword") or "").strip()
        if keyword:
            groups.append(
                {
                    "group_logic": "and",
                    "condition_logic": "or",
                    "conditions": [
                        {"field": "title", "operator": "contains", "value": keyword},
                        {"field": "code", "operator": "contains", "value": keyword},
                    ],
                }
            )
        if data.get("menu_id"):
            groups.append({"group_logic": "and", "condition_logic": "and", "conditions": [
                {"field": "menu_id", "operator": "eq", "value": data["menu_id"]}]})
        if data.get("module"):
            groups.append({"group_logic": "and", "condition_logic": "and", "conditions": [
                {"field": "module", "operator": "eq", "value": data["module"]}]})
        if data.get("status") not in (None, ""):
            groups.append({"group_logic": "and", "condition_logic": "and", "conditions": [
                {"field": "status", "operator": "eq", "value": data["status"]}]})

        page = int(data.get("page") or 1)
        limit = int(data.get("limit") or 20)

        result = await self.get_list(
            filter=groups,
            fields="id, code, title, menu_id, module, sort, status, description, create_time, update_time",
            sort_rules=[{"field": "sort", "direction": "asc"}, {"field": "id", "direction": "asc"}],
            page=page,
            limit=limit,
        )
        if not isinstance(result, dict):
            return {"items": [], "total": 0}

        items: List[Dict[str, Any]] = result.get("items", [])
        await self._decorate_groups(items)
        result["items"] = items
        return result

    async def _decorate_groups(self, items: List[Dict[str, Any]]) -> None:
        """为权限组列表补充菜单名称与子表统计

        Args:
            items: 权限组列表（原地修改）
        """
        if not items:
            return

        group_ids = [int(item["id"]) for item in items if item.get("id")]
        menu_ids = list({int(item["menu_id"]) for item in items if item.get("menu_id")})

        menus: Dict[int, Dict[str, Any]] = {}
        if menu_ids:
            rows = await self.permission_model.get_list(
                filter=self._where(
                    [
                        {"field": "id", "operator": "in", "value": menu_ids},
                        self._not_deleted(),
                    ]
                ),
                fields="id, title, code",
            )
            menus = {int(r["id"]): r for r in rows}

        prefix = self.db_prefix
        permission_counts = await self._count_by_group(f"{prefix}permission_group_permission", group_ids)
        field_counts = await self._count_by_group(f"{prefix}permission_group_field", group_ids)
        data_scope_counts = await self._count_by_group(f"{prefix}permission_group_data", group_ids)
        subject_counts = await self._count_by_group(f"{prefix}permission_group_subject", group_ids)

        for item in items:
            menu = menus.get(int(item.get("menu_id") or 0), {})
            group_id = int(item["id"])
            item["menu_title"] = menu.get("title")
            item["menu_code"] = menu.get("code")
            item["permission_count"] = permission_counts.get(group_id, 0)
            item["field_count"] = field_counts.get(group_id, 0)
            item["data_scope_count"] = data_scope_counts.get(group_id, 0)
            item["subject_count"] = subject_counts.get(group_id, 0)

    async def get_group_detail(self, group_id: Any) -> Dict[str, Any]:
        """查询权限组详情（含权限点 / 字段 / 数据 / 主体绑定）

        Args:
            group_id: 权限组ID

        Returns:
            权限组详情

        Raises:
            Exception: 权限组不存在
        """
        group = await self._require_group(group_id)
        gid = int(group["id"])

        group["menu"] = await self._get_menu(group.get("menu_id"))
        group["permissions"] = await self.get_group_permissions(gid)
        group["fields"] = await self._list_group_fields(gid)
        group["data_scopes"] = await self._list_group_data_scopes(gid)
        group["subjects"] = await self._list_group_subjects(gid)
        return group

    async def create_group(self, data: Dict[str, Any], operator_id: int = 0) -> Dict[str, Any]:
        """创建权限组

        Args:
            data: 权限组数据（title / menu_id 或 menu_code / module / sort / status / description）；
                code 可省略，省略时按「pg:模块:序号」自动生成；
                module 可省略，省略时按菜单权限点推导
            operator_id: 操作人用户ID（自动写入 create_by / update_by）

        Returns:
            新建权限组信息

        Raises:
            Exception: 参数或数据校验失败
        """
        code = (data.get("code") or "").strip()
        title = (data.get("title") or "").strip()
        if not title:
            raise Exception("权限组名称不能为空")

        menu_id = await self._resolve_menu_id(data)
        # 业务模块：优先采用调用方（前端路由 meta 声明）传入的 module，
        # 未传时按菜单权限点推导（无前端路由的菜单走此兜底）
        module = (data.get("module") or "").strip() or await self._resolve_module(menu_id)

        # 权限组编码自动维护：未传时按「pg:模块:序号」生成
        if not code:
            code = await self._generate_group_code(module)

        exists = await self.get_first(
            filter=self._where(
                [
                    {"field": "code", "operator": "eq", "value": code},
                    self._not_deleted(),
                ]
            ),
            fields="id",
        )
        if exists:
            raise Exception(f"权限组编码已存在: {code}")

        payload = {
            "code": code,
            "title": title,
            "menu_id": menu_id,
            "module": module,
            "sort": int(data.get("sort") or 0),
            "status": int(data.get("status") if data.get("status") is not None else 1),
            "description": data.get("description"),
            "create_by": operator_id,
            "update_by": operator_id,
        }
        group_id = await self.create(payload)
        return {"id": group_id, **payload}

    async def update_group(self, group_id: Any, data: Dict[str, Any], operator_id: int = 0) -> Dict[str, Any]:
        """更新权限组

        Args:
            group_id: 权限组ID
            data: 权限组数据
            operator_id: 操作人用户ID（自动写入 update_by）

        Returns:
            更新后的权限组详情

        Raises:
            Exception: 参数或数据校验失败
        """
        group = await self._require_group(group_id)
        gid = int(group["id"])

        payload: Dict[str, Any] = {}

        code = (data.get("code") or "").strip()
        if code and code != group.get("code"):
            exists = await self.get_first(
                filter=self._where(
                    [
                        {"field": "code", "operator": "eq", "value": code},
                        {"field": "id", "operator": "ne", "value": gid},
                        self._not_deleted(),
                    ]
                ),
                fields="id",
            )
            if exists:
                raise Exception(f"权限组编码已存在: {code}")
            payload["code"] = code

        title = (data.get("title") or "").strip()
        if title:
            payload["title"] = title

        if data.get("menu_id") or data.get("menu_code"):
            payload["menu_id"] = await self._resolve_menu_id(data)

        # 业务模块随菜单自动维护：菜单变更时优先采用调用方传入值，否则按菜单推导
        if payload.get("menu_id"):
            payload["module"] = (data.get("module") or "").strip() or await self._resolve_module(
                int(payload["menu_id"])
            )

        if data.get("sort") is not None:
            payload["sort"] = int(data["sort"])
        if data.get("status") is not None:
            payload["status"] = int(data["status"])
        if data.get("description") is not None:
            payload["description"] = data["description"]

        if payload:
            payload["update_by"] = operator_id
            payload["update_time"] = datetime.now()
            await self.update_by_id(gid, payload)

        return await self.get_group_detail(gid)

    async def delete_group(self, group_id: Any) -> None:
        """删除权限组（软删除，并清理子表与用户激活记录）

        Args:
            group_id: 权限组ID
        """
        group = await self._require_group(group_id)
        gid = int(group["id"])
        prefix = self.db_prefix

        for table in (
            f"{prefix}permission_group_permission",
            f"{prefix}permission_group_field",
            f"{prefix}permission_group_data",
            f"{prefix}permission_group_subject",
            f"{prefix}user_permission_group",
        ):
            await self.db.execute(f"DELETE FROM {table} WHERE group_id = $1", [gid])

        await self.delete(self._where([{"field": "id", "operator": "eq", "value": gid}]))

    # ==================== 组-操作权限点 ====================

    async def get_group_permissions(self, group_id: Any) -> Dict[str, Any]:
        """查询权限组已授权的操作权限点

        Args:
            group_id: 权限组ID

        Returns:
            包含 permission_ids 与 codes 的字典
        """
        relations = await self.group_permission_model.get_list(
            filter=self._where(
                [
                    {"field": "group_id", "operator": "eq", "value": group_id},
                    self._not_deleted(),
                ]
            ),
            fields="permission_id",
        )
        permission_ids = [int(r["permission_id"]) for r in relations if r.get("permission_id")]

        codes: List[str] = []
        if permission_ids:
            rows = await self.permission_model.get_list(
                filter=self._where(
                    [
                        {"field": "id", "operator": "in", "value": permission_ids},
                        self._not_deleted(),
                    ]
                ),
                fields="code",
            )
            codes = [r["code"] for r in rows if r.get("code")]

        return {"permission_ids": permission_ids, "codes": codes}

    @staticmethod
    def _in_group_scope(permission: Dict[str, Any], module: str) -> bool:
        """判断权限点是否落在权限组的业务模块范围内

        分组节点（type=0）仅用于树结构承载，不参与授权语义；其余权限点按其
        自身 module 判定（菜单权限点与操作权限点的 module 同源，均由
        init_permission 维护）。

        Args:
            permission: 权限点记录（含 code/module/type）
            module: 权限组业务模块

        Returns:
            是否在权限组可授权范围内
        """
        if int(permission.get("type") or 0) == TYPE_GROUP:
            return True
        return permission.get("module") == module

    async def grant_group_permissions(
        self, group_id: Any, permission_ids: List[Any], operator_id: int = 0
    ) -> Dict[str, Any]:
        """覆盖式保存权限组的操作权限点与菜单准入

        菜单准入由权限组的所属菜单（menu_id）自动维护，无需客户端传值：
        保存时始终把该菜单权限点纳入授权范围。
        其余权限点必须存在且落在权限组的业务模块范围内（module 与权限组一致），
        分组节点仅作树结构承载。

        Args:
            group_id: 权限组ID
            permission_ids: 权限点ID列表（菜单准入无需包含，由 menu_id 自动补全）
            operator_id: 操作人用户ID（自动写入 create_by / update_by）

        Returns:
            保存结果（含生效的权限码）

        Raises:
            Exception: 权限点无效或跨模块
        """
        group = await self._require_group(group_id)
        gid = int(group["id"])
        module = group.get("module")

        ids = [int(pid) for pid in (permission_ids or []) if pid]
        # 菜单准入自动维护：权限组归属的菜单始终纳入授权，客户端无需勾选
        menu_id = group.get("menu_id")
        if menu_id and int(menu_id) not in ids:
            ids.append(int(menu_id))
        if ids:
            rows = await self.permission_model.get_list(
                filter=self._where(
                    [
                        {"field": "id", "operator": "in", "value": ids},
                        self._not_deleted(),
                    ]
                ),
                fields="id, code, module, type",
            )
            valid = {int(r["id"]): r for r in rows}
            invalid = [pid for pid in ids if pid not in valid]
            if invalid:
                raise Exception(f"存在无效权限点: {invalid}")
            if module:
                cross = [valid[pid]["code"] for pid in ids if not self._in_group_scope(valid[pid], module)]
                if cross:
                    raise Exception(f"权限点与权限组模块({module})不一致: {cross}")

        await self.db.execute(
            f"DELETE FROM {self.db_prefix}permission_group_permission WHERE group_id = $1", [gid]
        )
        for pid in ids:
            await self.db.execute(
                f"INSERT INTO {self.db_prefix}permission_group_permission "
                "(group_id, permission_id, create_by, update_by) VALUES ($1, $2, $3, $3)",
                [gid, pid, operator_id],
            )
        return await self.get_group_permissions(gid)

    # ==================== 组-字段权限 ====================

    async def _list_group_fields(self, group_id: int) -> List[Dict[str, Any]]:
        """查询权限组的字段权限配置

        Args:
            group_id: 权限组ID

        Returns:
            字段权限列表
        """
        return await self.group_field_model.get_list(
            filter=self._where(
                [
                    {"field": "group_id", "operator": "eq", "value": group_id},
                    self._not_deleted(),
                ]
            ),
            fields="id, group_id, module, field, field_label, visible, editable",
            sort_rules=[{"field": "module", "direction": "asc"}, {"field": "id", "direction": "asc"}],
        )

    async def set_group_fields(
        self, group_id: Any, module: str, fields: List[Dict[str, Any]], operator_id: int = 0
    ) -> List[Dict[str, Any]]:
        """覆盖式保存权限组的字段权限

        字段中文名与系统列判定均由后端自动维护：中文名取自字段目录（FIELD_LABELS >
        列注释 > 字段名），前端传入的 field_label 被忽略。

        Args:
            group_id: 权限组ID
            module: 业务模块
            fields: [{field, visible, editable}]
            operator_id: 操作人用户ID（自动写入 create_by / update_by）

        Returns:
            保存后的字段权限列表

        Raises:
            Exception: 字段不在模块目录内
        """
        group = await self._require_group(group_id)
        gid = int(group["id"])

        module = (module or group.get("module") or "").strip()
        if not module:
            raise Exception("业务模块不能为空")

        catalog = {item["field"]: item["field_label"] for item in await self.get_field_catalog(module)}

        await self.db.execute(
            f"DELETE FROM {self.db_prefix}permission_group_field WHERE group_id = $1 AND module = $2",
            [gid, module],
        )
        for item in fields or []:
            field = (item.get("field") or "").strip()
            if not field:
                continue
            if catalog and field not in catalog:
                raise Exception(f"字段不在模块 {module} 目录内: {field}")
            await self.db.execute(
                f"INSERT INTO {self.db_prefix}permission_group_field "
                "(group_id, module, field, field_label, visible, editable, create_by, update_by) "
                "VALUES ($1, $2, $3, $4, $5, $6, $7, $7)",
                [
                    gid,
                    module,
                    field,
                    catalog.get(field) or field,
                    int(item.get("visible") if item.get("visible") is not None else 1),
                    int(item.get("editable") if item.get("editable") is not None else 1),
                    operator_id,
                ],
            )
        return await self._list_group_fields(gid)

    async def get_field_catalog(self, module: str) -> List[Dict[str, Any]]:
        """查询模块的可配置字段目录（取自业务表的业务列）

        系统列由 _system_columns() 自动识别，业务字段中文名按「FIELD_LABELS 显式覆盖 >
        数据库列注释 > 字段名」推导，无需人工维护。

        Args:
            module: 业务模块

        Returns:
            [{field, field_label}] 列表

        Raises:
            Exception: 模块未登记业务表
        """
        module = (module or "").strip()
        table = MODULE_TABLES.get(module)
        if not table:
            raise Exception(f"模块未登记业务表，无法获取字段目录: {module}")

        full_table = f"{self.db_prefix}{table}"
        rows = await self.db.fetch_all(
            "SELECT column_name FROM information_schema.columns WHERE table_name = $1 ORDER BY ordinal_position",
            [full_table],
        )
        comments = await self._column_comments(full_table)
        labels = FIELD_LABELS.get(module, {})
        system_columns = await self._system_columns()
        return [
            {
                "field": r["column_name"],
                "field_label": labels.get(r["column_name"])
                or self._comment_label(comments.get(r["column_name"]))
                or r["column_name"],
            }
            for r in rows
            if r["column_name"] not in system_columns
        ]

    # ==================== 组-数据权限 ====================

    async def _list_group_data_scopes(self, group_id: int) -> List[Dict[str, Any]]:
        """查询权限组的数据权限配置

        Args:
            group_id: 权限组ID

        Returns:
            数据权限列表
        """
        return await self.group_data_model.get_list(
            filter=self._where(
                [
                    {"field": "group_id", "operator": "eq", "value": group_id},
                    self._not_deleted(),
                ]
            ),
            fields="id, group_id, module, scope, custom_dept_ids",
            sort_rules=[{"field": "module", "direction": "asc"}],
        )

    async def set_group_data_scope(
        self, group_id: Any, module: str, scope: str, custom_dept_ids: List[Any], operator_id: int = 0
    ) -> Dict[str, Any]:
        """覆盖式保存权限组在指定模块上的数据权限范围

        Args:
            group_id: 权限组ID
            module: 业务模块
            scope: 数据范围（all / dept / dept_and_sub / self / custom / none）
            custom_dept_ids: scope=custom 时的自定义部门ID列表
            operator_id: 操作人用户ID（自动写入 create_by / update_by）

        Returns:
            保存后的数据权限配置

        Raises:
            Exception: 数据范围或自定义部门非法
        """
        group = await self._require_group(group_id)
        gid = int(group["id"])

        module = (module or group.get("module") or "").strip()
        if not module:
            raise Exception("业务模块不能为空")

        scope = (scope or "").strip()
        if scope not in DATA_SCOPES:
            raise Exception(f"数据范围非法: {scope or '空'}，可选: {', '.join(DATA_SCOPES)}")

        dept_ids = [int(did) for did in (custom_dept_ids or []) if did]
        if scope == SCOPE_CUSTOM:
            if not dept_ids:
                raise Exception("自定义数据范围必须选择部门")
            rows = await self.dept_model.get_list(
                filter=self._where(
                    [
                        {"field": "id", "operator": "in", "value": dept_ids},
                        self._not_deleted(),
                    ]
                ),
                fields="id",
            )
            valid = {int(r["id"]) for r in rows}
            invalid = [did for did in dept_ids if did not in valid]
            if invalid:
                raise Exception(f"存在无效部门: {invalid}")
        else:
            dept_ids = []

        await self.db.execute(
            f"DELETE FROM {self.db_prefix}permission_group_data WHERE group_id = $1 AND module = $2",
            [gid, module],
        )
        await self.db.execute(
            f"INSERT INTO {self.db_prefix}permission_group_data "
            "(group_id, module, scope, custom_dept_ids, create_by, update_by) "
            "VALUES ($1, $2, $3, $4::jsonb, $5, $5)",
            [gid, module, scope, self._to_json(dept_ids), operator_id],
        )
        scopes = await self._list_group_data_scopes(gid)
        return next((s for s in scopes if s.get("module") == module), {})

    @staticmethod
    def _to_json(value: Any) -> str:
        """序列化为 JSONB 可写入的字符串"""
        import json

        return json.dumps(value, ensure_ascii=False)

    # ==================== 组-主体绑定 ====================

    async def _list_group_subjects(self, group_id: int) -> List[Dict[str, Any]]:
        """查询权限组的主体绑定（含主体显示名）

        Args:
            group_id: 权限组ID

        Returns:
            主体绑定列表
        """
        rows = await self.db.fetch_all(
            f"SELECT id, group_id, subject_type, subject_id FROM {self.db_prefix}permission_group_subject "
            "WHERE group_id = $1 AND is_deleted = 0 ORDER BY subject_type, subject_id",
            [group_id],
        )
        if not rows:
            return []

        by_type: Dict[str, List[int]] = {t: [] for t in SUBJECT_TYPES}
        for row in rows:
            subject_type = row.get("subject_type")
            if subject_type in by_type:
                by_type[subject_type].append(int(row["subject_id"]))

        names: Dict[str, Dict[int, Dict[str, Any]]] = {}
        if by_type[SUBJECT_DEPT]:
            depts = await self.dept_model.get_list(
                filter=self._where(
                    [
                        {"field": "id", "operator": "in", "value": by_type[SUBJECT_DEPT]},
                        self._not_deleted(),
                    ]
                ),
                fields="id, title, name, code",
            )
            names[SUBJECT_DEPT] = {
                int(d["id"]): {"name": d.get("name") or d.get("title"), "code": d.get("code")} for d in depts
            }
        if by_type[SUBJECT_ROLE]:
            roles = await self.role_model.get_list(
                filter=self._where(
                    [
                        {"field": "id", "operator": "in", "value": by_type[SUBJECT_ROLE]},
                        self._not_deleted(),
                    ]
                ),
                fields="id, title, name, code",
            )
            names[SUBJECT_ROLE] = {
                int(r["id"]): {"name": r.get("name") or r.get("title"), "code": r.get("code")} for r in roles
            }
        if by_type[SUBJECT_USER]:
            users = await self.user_model.get_list(
                filter=self._where(
                    [
                        {"field": "id", "operator": "in", "value": by_type[SUBJECT_USER]},
                        self._not_deleted(),
                    ]
                ),
                fields="id, name, username, dept_id",
            )
            names[SUBJECT_USER] = {
                int(u["id"]): {"name": u.get("name") or u.get("username"), "code": u.get("username")}
                for u in users
            }

        result: List[Dict[str, Any]] = []
        for row in rows:
            subject_type = row.get("subject_type")
            subject_id = int(row["subject_id"])
            info = names.get(subject_type, {}).get(subject_id, {})
            result.append(
                {
                    "id": row.get("id"),
                    "subject_type": subject_type,
                    "subject_id": subject_id,
                    "subject_name": info.get("name"),
                    "subject_code": info.get("code"),
                }
            )
        return result

    async def bind_group_subjects(
        self, group_id: Any, subjects: List[Dict[str, Any]], operator_id: int = 0
    ) -> List[Dict[str, Any]]:
        """覆盖式保存权限组的主体绑定（部门 / 角色 / 人员）

        Args:
            group_id: 权限组ID
            subjects: [{subject_type, subject_id}]
            operator_id: 操作人用户ID（自动写入 create_by / update_by）

        Returns:
            保存后的主体绑定列表

        Raises:
            Exception: 主体类型或主体非法
        """
        group = await self._require_group(group_id)
        gid = int(group["id"])

        items: List[Dict[str, Any]] = []
        seen = set()
        for item in subjects or []:
            subject_type = (item.get("subject_type") or "").strip()
            subject_id = item.get("subject_id")
            if subject_type not in SUBJECT_TYPES:
                raise Exception(f"主体类型非法: {subject_type or '空'}，可选: {', '.join(SUBJECT_TYPES)}")
            if not subject_id:
                raise Exception("主体ID不能为空")
            key = (subject_type, int(subject_id))
            if key in seen:
                continue
            seen.add(key)
            items.append({"subject_type": subject_type, "subject_id": int(subject_id)})

        for subject_type in SUBJECT_TYPES:
            ids = [i["subject_id"] for i in items if i["subject_type"] == subject_type]
            if not ids:
                continue
            model = {
                SUBJECT_DEPT: self.dept_model,
                SUBJECT_ROLE: self.role_model,
                SUBJECT_USER: self.user_model,
            }[subject_type]
            rows = await model.get_list(
                filter=self._where(
                    [
                        {"field": "id", "operator": "in", "value": ids},
                        self._not_deleted(),
                    ]
                ),
                fields="id",
            )
            valid = {int(r["id"]) for r in rows}
            invalid = [i for i in ids if i not in valid]
            if invalid:
                raise Exception(f"{subject_type} 主体不存在: {invalid}")

        await self.db.execute(
            f"DELETE FROM {self.db_prefix}permission_group_subject WHERE group_id = $1", [gid]
        )
        for item in items:
            await self.db.execute(
                f"INSERT INTO {self.db_prefix}permission_group_subject "
                "(group_id, subject_type, subject_id, create_by, update_by) VALUES ($1, $2, $3, $4, $4)",
                [gid, item["subject_type"], item["subject_id"], operator_id],
            )
        return await self._list_group_subjects(gid)

    async def delete_group_subject(self, group_id: Any, subject_type: Any, subject_id: Any) -> None:
        """解绑权限组的单个主体（部门 / 角色 / 人员）

        Args:
            group_id: 权限组ID
            subject_type: 主体类型（dept / role / user）
            subject_id: 主体ID

        Raises:
            Exception: 主体类型非法或绑定不存在
        """
        group = await self._require_group(group_id)
        gid = int(group["id"])

        stype = (subject_type or "").strip()
        if stype not in SUBJECT_TYPES:
            raise Exception(f"主体类型非法: {stype or '空'}，可选: {', '.join(SUBJECT_TYPES)}")
        if not subject_id:
            raise Exception("主体ID不能为空")
        sid = int(subject_id)

        row = await self.db.fetch_one(
            f"SELECT id FROM {self.db_prefix}permission_group_subject "
            "WHERE group_id = $1 AND subject_type = $2 AND subject_id = $3 AND is_deleted = 0",
            [gid, stype, sid],
        )
        if not row:
            raise Exception("主体绑定不存在")

        await self.db.execute(
            f"DELETE FROM {self.db_prefix}permission_group_subject "
            "WHERE group_id = $1 AND subject_type = $2 AND subject_id = $3",
            [gid, stype, sid],
        )

    async def get_bindable_subjects(self) -> Dict[str, Any]:
        """查询可绑定的主体选项（部门 / 角色 / 人员）

        Returns:
            {depts, roles, users}
        """
        depts = await self.dept_model.get_list(
            filter=self._where([self._not_deleted()]),
            fields="id, title, name, code, pid",
            sort_rules=[{"field": "sort", "direction": "asc"}],
        )
        roles = await self.role_model.get_list(
            filter=self._where([self._not_deleted()]),
            fields="id, title, name, code",
            sort_rules=[{"field": "id", "direction": "asc"}],
        )
        users = await self.user_model.get_list(
            filter=self._where([self._not_deleted()]),
            fields="id, title, name, username, dept_id",
            sort_rules=[{"field": "id", "direction": "asc"}],
        )
        return {"depts": depts, "roles": roles, "users": users}

    async def get_menu_options(self) -> List[Dict[str, Any]]:
        """查询可归属的菜单权限点（type=1）

        Returns:
            菜单列表（含推导出的业务模块）
        """
        menus = await self.permission_model.get_list(
            filter=self._where(
                [
                    {"field": "type", "operator": "eq", "value": 1},
                    {"field": "status", "operator": "eq", "value": 1},
                    self._not_deleted(),
                ]
            ),
            fields="id, pid, title, code, module, path, sort",
            sort_rules=[{"field": "sort", "direction": "asc"}],
        )
        for menu in menus:
            menu["business_module"] = menu.get("module") or ""
        return menus

    # ==================== 当前用户的权限组 ====================

    async def get_user_groups(self, current_user: Dict[str, Any]) -> Dict[str, Any]:
        """查询当前用户可用的权限组与激活状态

        Args:
            current_user: 当前登录用户（含 id / dept_id / group_id）

        Returns:
            {items, active_group_id}
        """
        # 管理员直通全量权限，不参与权限组切换
        if current_user.get("is_admin"):
            return {"items": [], "active_group_id": None}

        user_id = int(current_user["id"])
        group_ids = await get_user_group_ids(user_id, current_user.get("dept_id"))
        if not group_ids:
            return {"items": [], "active_group_id": None}

        rows = await self.get_list(
            filter=self._where(
                [
                    {"field": "id", "operator": "in", "value": group_ids},
                    {"field": "status", "operator": "eq", "value": 1},
                    self._not_deleted(),
                ]
            ),
            fields="id, code, title, menu_id, module, sort, description",
            sort_rules=[{"field": "sort", "direction": "asc"}, {"field": "id", "direction": "asc"}],
        )
        items = rows if isinstance(rows, list) else []
        await self._decorate_groups(items)

        active_group_id = current_user.get("group_id")
        for item in items:
            item["is_active"] = 1 if active_group_id and int(item["id"]) == int(active_group_id) else 0

        return {"items": items, "active_group_id": active_group_id}

    async def activate_user_group(self, current_user: Dict[str, Any], group_id: Any) -> Dict[str, Any]:
        """切换当前用户激活的权限组（按组互斥）

        同一用户在同一时刻至多激活一个权限组；只能切换到另一个组，不支持清空。

        Args:
            current_user: 当前登录用户
            group_id: 目标权限组ID（必填）

        Returns:
            {active_group_id}

        Raises:
            Exception: 未选择权限组 / 管理员不支持切换 / 权限组不在该用户的可用范围内
        """
        # 管理员直通全量权限，不参与权限组切换
        if current_user.get("is_admin"):
            raise Exception("管理员不支持权限组切换")

        user_id = int(current_user["id"])

        if not group_id:
            raise Exception("请选择要激活的权限组")

        target_id = int(group_id)
        available = await get_user_group_ids(user_id, current_user.get("dept_id"))
        if target_id not in available:
            raise Exception("该权限组不在当前用户的可用范围内")

        row = await self.db.fetch_one(
            f"SELECT id FROM {self.db_prefix}user_permission_group "
            "WHERE user_id = $1 AND group_id = $2 AND is_deleted = 0 LIMIT 1",
            [user_id, target_id],
        )

        queries = [
            (
                f"UPDATE {self.db_prefix}user_permission_group SET is_active = 0, update_time = CURRENT_TIMESTAMP "
                "WHERE user_id = $1 AND is_deleted = 0",
                [user_id],
            )
        ]
        if row:
            queries.append(
                (
                    f"UPDATE {self.db_prefix}user_permission_group "
                    "SET is_active = 1, activate_time = CURRENT_TIMESTAMP, update_time = CURRENT_TIMESTAMP "
                    "WHERE id = $1",
                    [int(row["id"])],
                )
            )
        else:
            queries.append(
                (
                    f"INSERT INTO {self.db_prefix}user_permission_group (user_id, group_id, is_active, activate_time) "
                    "VALUES ($1, $2, 1, CURRENT_TIMESTAMP)",
                    [user_id, target_id],
                )
            )

        await self.db.execute_batch(queries)
        return {"active_group_id": target_id}
