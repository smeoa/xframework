"""认证授权模块

本模块提供用户认证和权限校验功能，包括登录验证、Token 管理、权限校验等。

权限模型（RBAC + 权限组）：
    x_user --x_user_role--> x_role --x_role_permission--> x_permission
    code='admin' 的角色视为超级管理员，默认拥有全量权限码。

权限组（叠加层级，与 RBAC 并存）：
    x_permission_group（菜单下的业务权限场景）
      ├─ x_permission_group_permission（组-操作权限点）
      ├─ x_permission_group_field（组-字段权限：可见/可编辑）
      ├─ x_permission_group_data（组-数据权限：数据范围 scope）
      └─ x_permission_group_subject（组-主体绑定：部门/角色/人员）
    x_user_permission_group 记录用户当前激活的组，同一用户最多一条 is_active=1，实现按组互斥切换。

数据权限在后端 SQL 注入：由 resolve_allowed_user_ids() 解析出「可见数据的归属用户ID集合」，
模型层据此强制追加 user_id 条件（None=不限制；[]=无任何数据）。

请求凭据支持两种（优先级：X-API-Key > Authorization: Bearer <JWT>）：
- JWT：登录后由 /admin/auth/login 下发；
- API 密钥：x_user_api_key.key，供外部系统调用接口，权限等价于密钥归属用户。
"""

import json
import jwt
from fastapi import Request, HTTPException
from typing import Callable, Dict, Any, List, Optional
import logging

from .config import config
from .db import db

logger = logging.getLogger(__name__)


class AuthError(Exception):
    pass


# API 密钥请求头名称（外部系统以 X-API-Key 携带 x_user_api_key.key 调用接口）
API_KEY_HEADER = "X-API-Key"

# 免登录白名单：精确路径，或以 * 结尾表示前缀匹配
WHITELIST_PATTERNS = (
    "/",
    "/health",
    "/health/detail",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/ws/*",
    "/admin/auth/login",
)

# 数据权限范围取值
SCOPE_ALL = "all"  # 全部数据
SCOPE_DEPT = "dept"  # 本部门
SCOPE_DEPT_AND_SUB = "dept_and_sub"  # 本部门及下级部门
SCOPE_SELF = "self"  # 仅本人
SCOPE_CUSTOM = "custom"  # 自定义部门
SCOPE_NONE = "none"  # 无任何数据
DATA_SCOPES = (SCOPE_ALL, SCOPE_DEPT, SCOPE_DEPT_AND_SUB, SCOPE_SELF, SCOPE_CUSTOM, SCOPE_NONE)

# 绑定主体类型
SUBJECT_DEPT = "dept"
SUBJECT_ROLE = "role"
SUBJECT_USER = "user"

# 匿名用户信息（白名单路径未携带 token 时使用）
ANONYMOUS_USER: Dict[str, Any] = {
    "id": None,
    "username": None,
    "is_admin": False,
    "roles": [],
    "permissions": [],
    "dept_id": None,
    "group_id": None,
    "group_code": None,
    "group_title": None,
    "group_permissions": [],
    "field_permissions": {},
    "data_scopes": {},
}


def is_whitelisted(path: str) -> bool:
    """判断请求路径是否免登录

    Args:
        path: 请求路径

    Returns:
        是否在白名单内
    """
    for pattern in WHITELIST_PATTERNS:
        if pattern.endswith("*"):
            if path.startswith(pattern[:-1]):
                return True
        elif path == pattern:
            return True
    return False


def _prefix() -> str:
    """业务表统一前缀"""
    return str(config.get("PG_PREFIX", "") or "")


async def get_current_user(request: Request) -> Dict[str, Any]:
    """获取当前登录用户信息

    从请求头中提取并验证用户身份，同一次请求内结果会被缓存到 request.state。

    Args:
        request: FastAPI 请求对象

    Returns:
        用户信息字典，含 id / username / is_admin / dept_id / roles / permissions
        以及激活权限组信息：group_id / group_code / group_title /
        group_permissions / field_permissions / data_scopes

    Raises:
        HTTPException: 未授权或 token 无效
    """
    cached = getattr(request.state, "auth_user", None)
    if cached:
        return cached  # type: ignore[no-any-return]

    user_info = await _load_user_from_request(request)
    request.state.auth_user = user_info
    return user_info


async def require_login(request: Request) -> Dict[str, Any]:
    """统一登录校验依赖

    白名单路径直接放行（携带有效 token 时仍解析用户信息），其余路径必须登录。

    Args:
        request: FastAPI 请求对象

    Returns:
        用户信息字典

    Raises:
        HTTPException: 未登录或 token 无效
    """
    if is_whitelisted(request.url.path):
        cached = getattr(request.state, "auth_user", None)
        if cached:
            return cached  # type: ignore[no-any-return]
        has_credential = request.headers.get("Authorization", "").startswith("Bearer ") or (
            request.headers.get(API_KEY_HEADER) or ""
        ).strip()
        if has_credential:
            try:
                return await get_current_user(request)
            except HTTPException:
                pass
        request.state.auth_user = dict(ANONYMOUS_USER)
        return dict(ANONYMOUS_USER)

    return await get_current_user(request)


def require_permission(*codes: str) -> Callable[..., Any]:
    """生成操作权限校验依赖

    多个权限码之间为「或」关系，命中任意一个即放行；管理员直接放行。

    用法:
        @router.post("/create", dependencies=[Depends(require_permission("product:create"))])

    Args:
        *codes: 权限码

    Returns:
        可被 FastAPI Depends 调用的校验函数
    """

    async def _checker(request: Request) -> Dict[str, Any]:
        current_user = await get_current_user(request)
        if not codes or current_user.get("is_admin"):
            return current_user
        owned = set(current_user.get("permissions") or [])
        if owned.intersection(codes):
            return current_user
        logger.warning(
            f"越权访问: user={current_user.get('username')} path={request.url.path} need={'/'.join(codes)}"
        )
        raise HTTPException(status_code=403, detail=f"缺少权限: {'/'.join(codes)}")

    return _checker


def has_permission(current_user: Dict[str, Any], *codes: str) -> bool:
    """判断用户是否拥有指定权限（用于控制器内部逻辑分支）

    Args:
        current_user: 当前用户信息
        *codes: 权限码，任一命中即返回 True

    Returns:
        是否有权限
    """
    if current_user.get("is_admin"):
        return True
    return bool(set(current_user.get("permissions") or []).intersection(codes))


async def is_admin(user_id: int) -> bool:
    """判断用户是否为管理员

    Args:
        user_id: 用户ID

    Returns:
        是否为管理员
    """
    try:
        prefix: str = _prefix()
        sql = (
            f"SELECT r.code FROM {prefix}user_role ur "
            f"JOIN {prefix}role r ON r.id = ur.role_id "
            "WHERE ur.user_id = $1 AND ur.is_deleted = 0 "
            "AND r.is_deleted = 0 AND r.status = 1 AND r.code = 'admin' LIMIT 1"
        )
        row = await db.fetch_one(sql, [user_id])
        return row is not None
    except Exception as e:
        logger.error(f"管理员判定失败 user_id={user_id}: {str(e)}", exc_info=True)
        return False


async def get_user_role_codes(user_id: int) -> List[str]:
    """查询用户已启用的角色码

    Args:
        user_id: 用户ID

    Returns:
        角色码列表
    """
    prefix: str = _prefix()
    sql = (
        f"SELECT r.code FROM {prefix}user_role ur "
        f"JOIN {prefix}role r ON r.id = ur.role_id "
        "WHERE ur.user_id = $1 AND ur.is_deleted = 0 "
        "AND r.is_deleted = 0 AND r.status = 1"
    )
    rows = await db.fetch_all(sql, [user_id])
    return [str(row["code"]) for row in rows if row.get("code")]


async def get_user_permissions(user_id: int, admin: Optional[bool] = None) -> List[str]:
    """查询用户拥有的权限码列表

    管理员返回全量启用权限码，普通用户按「用户-角色-权限」链路查询。

    Args:
        user_id: 用户ID
        admin: 已知的管理员标记，传入可省去一次判定查询

    Returns:
        权限码列表
    """
    prefix: str = _prefix()
    if admin is None:
        admin = await is_admin(user_id)

    if admin:
        rows = await db.fetch_all(
            f"SELECT code FROM {prefix}permission WHERE is_deleted = 0 AND status = 1"
        )
        return [str(row["code"]) for row in rows if row.get("code")]

    sql = (
        f"SELECT DISTINCT p.code FROM {prefix}user_role ur "
        f"JOIN {prefix}role r ON r.id = ur.role_id AND r.is_deleted = 0 AND r.status = 1 "
        f"JOIN {prefix}role_permission rp ON rp.role_id = ur.role_id AND rp.is_deleted = 0 "
        f"JOIN {prefix}permission p ON p.id = rp.permission_id AND p.is_deleted = 0 AND p.status = 1 "
        "WHERE ur.user_id = $1 AND ur.is_deleted = 0"
    )
    rows = await db.fetch_all(sql, [user_id])
    return [str(row["code"]) for row in rows if row.get("code")]


# ==================== 权限组（叠加层级） ====================


async def get_user_dept_id(user_id: int) -> Optional[int]:
    """查询用户所属部门ID

    Args:
        user_id: 用户ID

    Returns:
        部门ID，未设置返回 None
    """
    try:
        prefix: str = _prefix()
        row = await db.fetch_one(
            f"SELECT dept_id FROM {prefix}user WHERE id = $1 AND is_deleted = 0 LIMIT 1", [user_id]
        )
        if row and row.get("dept_id") is not None:
            return int(row["dept_id"])
        return None
    except Exception as e:
        logger.error(f"查询用户部门失败 user_id={user_id}: {str(e)}", exc_info=True)
        return None


async def get_user_group_ids(user_id: int, dept_id: Optional[int] = None) -> List[int]:
    """查询用户可用的权限组ID列表

    按「人员 / 角色 / 部门」三类绑定主体分别解析后合并去重：
    - 人员：subject_type='user' 且 subject_id = 用户ID
    - 角色：subject_type='role' 且用户已启用该角色
    - 部门：subject_type='dept' 且 subject_id = 用户所属部门

    Args:
        user_id: 用户ID
        dept_id: 已知的部门ID，传入可省去一次查询

    Returns:
        可用权限组ID列表（升序）
    """
    prefix: str = _prefix()
    if dept_id is None:
        dept_id = await get_user_dept_id(user_id)

    sql_user = (
        f"SELECT DISTINCT s.group_id FROM {prefix}permission_group_subject s "
        f"JOIN {prefix}permission_group g ON g.id = s.group_id AND g.is_deleted = 0 AND g.status = 1 "
        "WHERE s.is_deleted = 0 AND s.subject_type = 'user' AND s.subject_id = $1"
    )

    sql_role = (
        f"SELECT DISTINCT s.group_id FROM {prefix}permission_group_subject s "
        f"JOIN {prefix}permission_group g ON g.id = s.group_id AND g.is_deleted = 0 AND g.status = 1 "
        f"JOIN {prefix}user_role ur ON ur.role_id = s.subject_id AND ur.is_deleted = 0 "
        f"JOIN {prefix}role r ON r.id = ur.role_id AND r.is_deleted = 0 AND r.status = 1 "
        "WHERE s.is_deleted = 0 AND s.subject_type = 'role' AND ur.user_id = $1"
    )

    group_ids: set = set()
    rows = await db.fetch_all(sql_user, [user_id])
    group_ids.update(int(r["group_id"]) for r in rows)
    rows = await db.fetch_all(sql_role, [user_id])
    group_ids.update(int(r["group_id"]) for r in rows)

    if dept_id is not None:
        sql_dept = (
            f"SELECT DISTINCT s.group_id FROM {prefix}permission_group_subject s "
            f"JOIN {prefix}permission_group g ON g.id = s.group_id AND g.is_deleted = 0 AND g.status = 1 "
            "WHERE s.is_deleted = 0 AND s.subject_type = 'dept' AND s.subject_id = $1"
        )
        rows = await db.fetch_all(sql_dept, [dept_id])
        group_ids.update(int(r["group_id"]) for r in rows)

    return sorted(group_ids)


async def get_active_group(user_id: int) -> Optional[Dict[str, Any]]:
    """查询用户当前激活的权限组

    同一用户在 x_user_permission_group 中最多一条 is_active=1，即按组互斥切换。

    Args:
        user_id: 用户ID

    Returns:
        权限组信息（id/code/title/menu_id/module），无激活组返回 None
    """
    try:
        prefix: str = _prefix()
        row = await db.fetch_one(
            f"SELECT g.id, g.code, g.title, g.menu_id, g.module "
            f"FROM {prefix}user_permission_group ug "
            f"JOIN {prefix}permission_group g ON g.id = ug.group_id AND g.is_deleted = 0 AND g.status = 1 "
            "WHERE ug.user_id = $1 AND ug.is_active = 1 AND ug.is_deleted = 0 "
            "ORDER BY ug.activate_time DESC NULLS LAST, ug.id DESC LIMIT 1",
            [user_id],
        )
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"查询激活权限组失败 user_id={user_id}: {str(e)}", exc_info=True)
        return None


async def resolve_group_permissions(group_id: int) -> List[str]:
    """解析权限组授予的权限码（组内权限点 ∪ 归属菜单权限点及其父级）

    权限组向上归属菜单权限点（menu_id）。若组内未显式包含该菜单权限点，
    激活后侧边栏会因缺少菜单权限码而隐藏本组所属菜单，故此处统一并集。

    Args:
        group_id: 权限组ID

    Returns:
        权限码列表
    """
    prefix: str = _prefix()
    sql = (
        "WITH RECURSIVE grp_menu AS ("
        f"  SELECT p.id AS perm_id FROM {prefix}permission_group g "
        f"  JOIN {prefix}permission p ON p.id = g.menu_id AND p.is_deleted = 0 AND p.status = 1 "
        "  WHERE g.id = $1 AND g.is_deleted = 0"
        "  UNION ALL"
        "  SELECT parent.id FROM grp_menu gm "
        f"  JOIN {prefix}permission child ON child.id = gm.perm_id "
        f"  JOIN {prefix}permission parent ON parent.id = child.pid "
        "  AND parent.is_deleted = 0 AND parent.status = 1"
        ") "
        "SELECT DISTINCT code FROM ("
        f"  SELECT p.code AS code FROM {prefix}permission_group_permission gp "
        f"  JOIN {prefix}permission p ON p.id = gp.permission_id AND p.is_deleted = 0 AND p.status = 1 "
        "  WHERE gp.group_id = $1 AND gp.is_deleted = 0"
        "  UNION"
        f"  SELECT p.code AS code FROM {prefix}permission p "
        "  JOIN grp_menu gm ON gm.perm_id = p.id "
        "  WHERE p.is_deleted = 0 AND p.status = 1"
        ") t WHERE code IS NOT NULL"
    )
    rows = await db.fetch_all(sql, [group_id])
    return [str(r["code"]) for r in rows if r.get("code")]


async def resolve_available_group_menu_permissions(group_ids: List[int]) -> List[str]:
    """解析用户「全部可用权限组」授予的菜单权限码

    菜单可见性需覆盖用户的全部可用权限组，而非仅当前激活组：
    否则激活某个组后，其余菜单会因缺少菜单权限码而从侧边栏消失，
    用户既进不去那些菜单，也就无法切换到那些菜单下挂载的权限组。

    Args:
        group_ids: 用户可用的权限组ID列表

    Returns:
        菜单权限码列表（去重）
    """
    if not group_ids:
        return []
    prefix: str = _prefix()
    rows = await db.fetch_all(
        f"SELECT DISTINCT p.code FROM {prefix}permission_group g "
        f"JOIN {prefix}permission p ON p.id = g.menu_id AND p.is_deleted = 0 AND p.status = 1 "
        "WHERE g.id = ANY($1::bigint[]) AND g.is_deleted = 0 AND g.status = 1",
        [list(group_ids)],
    )
    return [str(r["code"]) for r in rows if r.get("code")]


async def resolve_group_fields(group_id: int) -> Dict[str, Dict[str, Dict[str, int]]]:
    """解析权限组的字段权限

    Args:
        group_id: 权限组ID

    Returns:
        模块 -> 字段 -> {"visible": 0/1, "editable": 0/1}
    """
    prefix: str = _prefix()
    rows = await db.fetch_all(
        f"SELECT module, field, visible, editable FROM {prefix}permission_group_field "
        "WHERE group_id = $1 AND is_deleted = 0",
        [group_id],
    )
    result: Dict[str, Dict[str, Dict[str, int]]] = {}
    for r in rows:
        module = str(r["module"])
        result.setdefault(module, {})[str(r["field"])] = {
            "visible": int(r["visible"] or 0),
            "editable": int(r["editable"] or 0),
        }
    return result


async def resolve_group_data_scopes(group_id: int) -> Dict[str, Dict[str, Any]]:
    """解析权限组的数据权限范围

    Args:
        group_id: 权限组ID

    Returns:
        模块 -> {"scope": 范围, "custom_dept_ids": [部门ID]}
    """
    prefix: str = _prefix()
    rows = await db.fetch_all(
        f"SELECT module, scope, custom_dept_ids FROM {prefix}permission_group_data "
        "WHERE group_id = $1 AND is_deleted = 0",
        [group_id],
    )
    result: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        dept_ids = r.get("custom_dept_ids")
        if isinstance(dept_ids, str):
            try:
                dept_ids = json.loads(dept_ids)
            except (ValueError, TypeError):
                dept_ids = []
        result[str(r["module"])] = {
            "scope": str(r.get("scope") or SCOPE_DEPT),
            "custom_dept_ids": [int(x) for x in (dept_ids or [])],
        }
    return result


async def get_dept_subtree_ids(dept_id: int) -> List[int]:
    """查询部门及其全部下级部门ID（含自身）

    Args:
        dept_id: 部门ID

    Returns:
        部门ID列表
    """
    prefix: str = _prefix()
    sql = (
        f"WITH RECURSIVE sub AS ("
        f"SELECT id FROM {prefix}dept WHERE id = $1 AND is_deleted = 0 "
        f"UNION ALL "
        f"SELECT d.id FROM {prefix}dept d JOIN sub ON d.pid = sub.id WHERE d.is_deleted = 0"
        f") SELECT id FROM sub"
    )
    rows = await db.fetch_all(sql, [dept_id])
    return [int(r["id"]) for r in rows]


async def get_user_ids_by_depts(dept_ids: List[int]) -> List[int]:
    """查询指定部门下的用户ID集合

    Args:
        dept_ids: 部门ID列表

    Returns:
        用户ID列表
    """
    if not dept_ids:
        return []
    prefix: str = _prefix()
    rows = await db.fetch_all(
        f"SELECT id FROM {prefix}user WHERE is_deleted = 0 AND dept_id = ANY($1::bigint[])",
        [list(dept_ids)],
    )
    return [int(r["id"]) for r in rows]


async def resolve_allowed_user_ids(current_user: Dict[str, Any], module: str) -> Optional[List[int]]:
    """解析当前用户在指定模块下可见数据的归属用户ID集合（数据权限 SQL 注入依据）

    Args:
        current_user: 当前用户信息（get_current_user 返回值）
        module: 模块标识，如 shop

    Returns:
        None 表示不限制（全部数据）；[] 表示无任何数据；其余为可见数据归属的用户ID列表
    """
    if current_user.get("is_admin"):
        return None

    user_id = current_user.get("id")
    dept_id = current_user.get("dept_id")
    scope_conf = (current_user.get("data_scopes") or {}).get(module)

    # 未配置数据范围：回退「本人」
    if not scope_conf:
        return [int(user_id)] if user_id else []

    scope = str(scope_conf.get("scope") or SCOPE_SELF)
    if scope == SCOPE_ALL:
        return None
    if scope == SCOPE_NONE:
        return []
    if scope == SCOPE_SELF:
        return [int(user_id)] if user_id else []
    if scope == SCOPE_CUSTOM:
        return await get_user_ids_by_depts(list(scope_conf.get("custom_dept_ids") or []))
    if scope == SCOPE_DEPT:
        if dept_id is None:
            return [int(user_id)] if user_id else []
        return await get_user_ids_by_depts([int(dept_id)])
    if scope == SCOPE_DEPT_AND_SUB:
        if dept_id is None:
            return [int(user_id)] if user_id else []
        return await get_user_ids_by_depts(await get_dept_subtree_ids(int(dept_id)))
    return [int(user_id)] if user_id else []


def get_field_permission(current_user: Dict[str, Any], module: str, field: str) -> Dict[str, bool]:
    """获取当前用户对指定模块字段的可见/可编辑权限

    未在激活权限组中声明的字段默认全部可见且可编辑。

    Args:
        current_user: 当前用户信息
        module: 模块标识
        field: 字段名

    Returns:
        {"visible": bool, "editable": bool}
    """
    if current_user.get("is_admin"):
        return {"visible": True, "editable": True}
    conf = (current_user.get("field_permissions") or {}).get(module, {}).get(field)
    if not conf:
        return {"visible": True, "editable": True}
    return {"visible": bool(conf.get("visible")), "editable": bool(conf.get("editable"))}


async def get_user_context(user_id: int, username: str) -> Dict[str, Any]:
    """组装用户权限上下文（RBAC ∪ 激活权限组）

    管理员直通全量权限，不加载权限组；普通用户叠加激活权限组授予的
    操作权限、字段权限与数据权限范围。
    其中菜单可见性（权限码）覆盖用户的「全部可用权限组」，
    而非仅激活组，以免激活一个组后其余菜单从侧边栏消失。

    Args:
        user_id: 用户ID
        username: 用户名

    Returns:
        用户权限上下文字典（供登录返回与请求鉴权复用）
    """
    roles = await get_user_role_codes(user_id)
    admin = "admin" in roles
    dept_id = await get_user_dept_id(user_id)
    permissions = await get_user_permissions(user_id, admin=admin)

    group_id: Optional[int] = None
    group_code: Optional[str] = None
    group_title: Optional[str] = None
    group_permissions: List[str] = []
    field_permissions: Dict[str, Dict[str, Dict[str, int]]] = {}
    data_scopes: Dict[str, Dict[str, Any]] = {}

    # 管理员直通全量权限，不加载权限组
    if not admin:
        group = await get_active_group(user_id)
        if group:
            group_id = int(group["id"])
            group_code = str(group["code"]) if group.get("code") else None
            group_title = str(group["title"]) if group.get("title") else None
            group_permissions = await resolve_group_permissions(group_id)
            field_permissions = await resolve_group_fields(group_id)
            data_scopes = await resolve_group_data_scopes(group_id)

        # 菜单可见性：并入全部可用权限组的菜单权限码
        available_group_ids = await get_user_group_ids(user_id, dept_id)
        menu_permissions = await resolve_available_group_menu_permissions(available_group_ids)
        permissions = list(dict.fromkeys(permissions + menu_permissions))

    # 权限组为叠加层：RBAC 权限 ∪ 激活权限组权限
    merged_permissions = list(dict.fromkeys(permissions + group_permissions))

    return {
        "id": user_id,
        "username": username,
        "is_admin": admin,
        "dept_id": dept_id,
        "roles": roles,
        "permissions": merged_permissions,
        "group_id": group_id,
        "group_code": group_code,
        "group_title": group_title,
        "group_permissions": group_permissions,
        "field_permissions": field_permissions,
        "data_scopes": data_scopes,
    }


async def _load_user_from_request(request: Request) -> Dict[str, Any]:
    """从请求头解析并校验身份（不走缓存）

    支持两种凭据，优先级：X-API-Key > Authorization: Bearer <JWT>。

    Args:
        request: FastAPI 请求对象

    Returns:
        用户信息字典

    Raises:
        HTTPException: 未授权或凭据无效
    """
    api_key = (request.headers.get(API_KEY_HEADER) or "").strip()
    if api_key:
        user_info = await _load_user_by_api_key(api_key)
        if not user_info:
            raise HTTPException(status_code=401, detail="API 密钥无效、已禁用或已过期")
        return user_info

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录或 token 无效")

    token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="未登录或 token 无效")

    try:
        user_info = await _verify_token(token)
        if not user_info:
            raise HTTPException(status_code=401, detail="token 已过期或无效")
        return user_info
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"认证失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=401, detail="认证失败")


async def _load_user_by_api_key(api_key: str) -> Optional[Dict[str, Any]]:
    """按 API 密钥解析用户上下文

    密钥需存在、已启用（status=1）、未过期，且归属用户可登录（未删除且启用）。

    Args:
        api_key: x_user_api_key.key

    Returns:
        用户信息字典；密钥无效时返回 None
    """
    try:
        prefix: str = _prefix()
        sql = (
            f"SELECT k.user_id, u.username FROM {prefix}user_api_key k "
            f"JOIN {prefix}user u ON u.id = k.user_id AND u.is_deleted = 0 AND u.status = 1 "
            "WHERE k.key = $1 AND k.status = 1 "
            "AND (k.expire_time IS NULL OR k.expire_time > NOW()) LIMIT 1"
        )
        row = await db.fetch_one(sql, [api_key])
        if not row or row.get("user_id") is None:
            return None
        return await get_user_context(int(row["user_id"]), str(row["username"]))
    except Exception as e:
        logger.error(f"API 密钥认证失败: {str(e)}", exc_info=True)
        return None


async def _verify_token(token: str) -> Optional[Dict[str, Any]]:
    """验证 token 有效性

    Args:
        token: 访问令牌

    Returns:
        用户信息或 None
    """
    try:
        payload: Dict[str, Any] = jwt.decode(token, config.get("JWT_SECRET"), algorithms=["HS256"])
        user_id: int = payload["user_id"]
        username: str = payload["username"]
    except jwt.ExpiredSignatureError:
        logger.warning("token 已过期")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"token 无效: {str(e)}")
        return None
    except KeyError as e:
        logger.warning(f"token 缺少必要字段: {str(e)}")
        return None

    return await get_user_context(user_id, username)
