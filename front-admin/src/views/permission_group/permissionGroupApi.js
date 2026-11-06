/**
 * 权限组模块前端 API 定义与公共常量
 *
 * 后端接口（admin/permission_group/permission_group_route.py）全部为 POST，
 * 统一走 request.js，由 request.js 自动注入 token 并做 camelCase ↔ snake_case 转换。
 * 后端控制器统一从请求体的 data 字段取参，故此处统一包装为 { data: {...} }。
 */

import request from "@/utils/request";

// 权限组接口路径（与 permission_group_route.py 的路由一一对应）
export const PERMISSION_GROUP_API = {
  GET_GROUP_LIST: "/admin/permission-group/get-group-list",
  GET_GROUP_DETAIL: "/admin/permission-group/get-group-detail",
  CREATE_GROUP: "/admin/permission-group/create-group",
  UPDATE_GROUP: "/admin/permission-group/update-group",
  DELETE_GROUP: "/admin/permission-group/delete-group",
  GET_GROUP_PERMISSIONS: "/admin/permission-group/get-group-permissions",
  GRANT_GROUP_PERMISSIONS: "/admin/permission-group/grant-group-permissions",
  GET_FIELD_CATALOG: "/admin/permission-group/get-field-catalog",
  SET_GROUP_FIELDS: "/admin/permission-group/set-group-fields",
  SET_GROUP_DATA_SCOPE: "/admin/permission-group/set-group-data-scope",
  BIND_GROUP_SUBJECTS: "/admin/permission-group/bind-group-subjects",
  DELETE_GROUP_SUBJECT: "/admin/permission-group/delete-group-subject",
  GET_BINDABLE_SUBJECTS: "/admin/permission-group/get-bindable-subjects",
  GET_MENU_OPTIONS: "/admin/permission-group/get-menu-options",
  GET_USER_GROUPS: "/admin/permission-group/get-user-groups",
  ACTIVATE_USER_GROUP: "/admin/permission-group/activate-user-group",
};

// 当前登录用户权限上下文（切换权限组后刷新登录态）
export const GET_USER_INFO_API = "/admin/auth/get-user-info";

// 权限清单树（复用组织管理端点，用于按模块勾选操作权限点）
export const PERMISSION_TREE_API = "/admin/organization/get-permission-tree";

// 数据权限范围选项（与后端 DATA_SCOPES 一致）
export const DATA_SCOPE_OPTIONS = [
  { value: "all", label: "全部数据" },
  { value: "dept", label: "本部门" },
  { value: "dept_and_sub", label: "本部门及下级" },
  { value: "self", label: "仅本人" },
  { value: "custom", label: "自定义部门" },
  { value: "none", label: "无数据" },
];

// 主体绑定类型选项（与后端 SUBJECT_TYPES 一致）
export const SUBJECT_TYPE_OPTIONS = [
  { value: "dept", label: "部门" },
  { value: "role", label: "角色" },
  { value: "user", label: "人员" },
];

/**
 * 查询权限组列表
 * @param {Object} payload { page, limit, keyword, menuId, module, status }
 * @returns {Promise<Object>} { code, data: { items, total } }
 */
export function getGroupList(payload = {}) {
  return request.post(PERMISSION_GROUP_API.GET_GROUP_LIST, { data: payload });
}

/**
 * 查询权限组详情
 * @param {number} id 权限组ID
 * @returns {Promise<Object>} 权限组详情
 */
export function getGroupDetail(id) {
  return request.post(PERMISSION_GROUP_API.GET_GROUP_DETAIL, { data: { id } });
}

/**
 * 创建权限组
 * @param {Object} payload 权限组数据
 * @returns {Promise<Object>} 新建权限组
 */
export function createGroup(payload) {
  return request.post(PERMISSION_GROUP_API.CREATE_GROUP, { data: payload });
}

/**
 * 更新权限组
 * @param {Object} payload 权限组数据（含 id）
 * @returns {Promise<Object>} 更新后的权限组详情
 */
export function updateGroup(payload) {
  return request.post(PERMISSION_GROUP_API.UPDATE_GROUP, { data: payload });
}

/**
 * 删除权限组
 * @param {number} id 权限组ID
 * @returns {Promise<Object>} 删除结果
 */
export function deleteGroup(id) {
  return request.post(PERMISSION_GROUP_API.DELETE_GROUP, { data: { id } });
}

/**
 * 查询权限组已授权的操作权限点
 * @param {number} groupId 权限组ID
 * @returns {Promise<Object>} { permissionIds, codes }
 */
export function getGroupPermissions(groupId) {
  return request.post(PERMISSION_GROUP_API.GET_GROUP_PERMISSIONS, {
    data: { groupId },
  });
}

/**
 * 覆盖式保存权限组的操作权限点
 * @param {number} groupId 权限组ID
 * @param {Array<number>} permissionIds 权限点ID列表
 * @returns {Promise<Object>} 保存结果
 */
export function grantGroupPermissions(groupId, permissionIds) {
  return request.post(PERMISSION_GROUP_API.GRANT_GROUP_PERMISSIONS, {
    data: { groupId, permissionIds },
  });
}

/**
 * 查询模块可配置的字段目录
 * @param {string} module 业务模块
 * @returns {Promise<Object>} [{ field, fieldLabel }]
 */
export function getFieldCatalog(module) {
  return request.post(PERMISSION_GROUP_API.GET_FIELD_CATALOG, { data: { module } });
}

/**
 * 覆盖式保存权限组的字段权限
 * @param {number} groupId 权限组ID
 * @param {string} module 业务模块
 * @param {Array<Object>} fields [{ field, fieldLabel, visible, editable }]
 * @returns {Promise<Object>} 保存后的字段权限列表
 */
export function setGroupFields(groupId, module, fields) {
  return request.post(PERMISSION_GROUP_API.SET_GROUP_FIELDS, {
    data: { groupId, module, fields },
  });
}

/**
 * 覆盖式保存权限组的数据权限范围
 * @param {number} groupId 权限组ID
 * @param {string} module 业务模块
 * @param {string} scope 数据范围
 * @param {Array<number>} customDeptIds 自定义部门ID列表
 * @returns {Promise<Object>} 保存后的数据权限配置
 */
export function setGroupDataScope(groupId, module, scope, customDeptIds = []) {
  return request.post(PERMISSION_GROUP_API.SET_GROUP_DATA_SCOPE, {
    data: { groupId, module, scope, customDeptIds },
  });
}

/**
 * 覆盖式保存权限组的主体绑定
 * @param {number} groupId 权限组ID
 * @param {Array<Object>} subjects [{ subjectType, subjectId }]
 * @returns {Promise<Object>} 保存后的主体绑定列表
 */
export function bindGroupSubjects(groupId, subjects) {
  return request.post(PERMISSION_GROUP_API.BIND_GROUP_SUBJECTS, {
    data: { groupId, subjects },
  });
}

/**
 * 解绑权限组的单个主体
 * @param {number} groupId 权限组ID
 * @param {string} subjectType 主体类型（dept / role / user）
 * @param {number} subjectId 主体ID
 * @returns {Promise<Object>} 解绑结果
 */
export function deleteGroupSubject(groupId, subjectType, subjectId) {
  return request.post(PERMISSION_GROUP_API.DELETE_GROUP_SUBJECT, {
    data: { groupId, subjectType, subjectId },
  });
}

/**
 * 查询可绑定的主体选项
 * @returns {Promise<Object>} { depts, roles, users }
 */
export function getBindableSubjects() {
  return request.post(PERMISSION_GROUP_API.GET_BINDABLE_SUBJECTS, { data: {} });
}

/**
 * 查询可归属的菜单选项
 * @returns {Promise<Object>} 菜单列表（含 businessModule）
 */
export function getMenuOptions() {
  return request.post(PERMISSION_GROUP_API.GET_MENU_OPTIONS, { data: {} });
}

/**
 * 查询当前用户的可用权限组
 * @returns {Promise<Object>} { items, activeGroupId }
 */
export function getUserGroups() {
  return request.post(PERMISSION_GROUP_API.GET_USER_GROUPS, { data: {} });
}

/**
 * 切换当前用户激活的权限组（按组互斥；只能切换，不支持清空）
 * @param {number} groupId 目标权限组ID
 * @returns {Promise<Object>} { activeGroupId }
 */
export function activateUserGroup(groupId) {
  return request.post(PERMISSION_GROUP_API.ACTIVATE_USER_GROUP, {
    data: { groupId },
  });
}

/**
 * 查询当前登录用户的权限上下文（切换权限组后刷新登录态）
 * @returns {Promise<Object>} 用户权限上下文
 */
export function getUserInfo() {
  return request.post(GET_USER_INFO_API, { data: {} });
}

/**
 * 查询权限清单树（含 module，便于按权限组业务模块过滤）
 * @returns {Promise<Object>} 权限点树形结构
 */
export function getPermissionTree() {
  return request.post(PERMISSION_TREE_API, {});
}

/**
 * 将部门扁平列表转换为 el-tree 所需的树结构
 * @param {Array<Object>} depts 部门列表（含 id/pid/name/title/code）
 * @returns {Array<Object>} 部门树
 */
export function buildDeptTree(depts = []) {
  const nodes = (depts || []).map((dept) => ({
    id: dept.id,
    label: dept.name || dept.title || dept.code || String(dept.id),
    pid: dept.pid,
    children: [],
  }));
  const nodeMap = new Map(nodes.map((node) => [node.id, node]));
  const roots = [];
  nodes.forEach((node) => {
    const parent = node.pid != null ? nodeMap.get(node.pid) : null;
    if (parent) {
      parent.children.push(node);
    } else {
      roots.push(node);
    }
  });
  return roots;
}

