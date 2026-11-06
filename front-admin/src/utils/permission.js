/**
 * 前端权限工具
 *
 * 统一读取本地登录态（localStorage.user，登录接口已返回
 * isAdmin/roles/permissions/fieldPermissions/dataScopes/groupId 等），
 * 供路由守卫、v-permission 指令与页面逻辑使用。
 */

/**
 * 获取本地登录用户信息
 * @returns {Object|null} 用户信息，未登录或解析失败返回 null
 */
export function getLoginUser() {
  try {
    const raw = localStorage.getItem("user");
    return raw ? JSON.parse(raw) : null;
  } catch (error) {
    return null;
  }
}

/**
 * 是否为超级管理员
 * @returns {boolean} 是否管理员
 */
export function isAdmin() {
  const user = getLoginUser();
  return !!(user && user.isAdmin);
}

/**
 * 获取当前用户权限码列表
 * @returns {Array<string>} 权限码数组
 */
export function getPermissions() {
  const user = getLoginUser();
  const permissions = user && user.permissions;
  return Array.isArray(permissions) ? permissions : [];
}

/**
 * 是否拥有某个权限码（管理员直通；权限码为空视为不限制）
 * @param {string} code 权限码
 * @returns {boolean} 是否有权限
 */
export function hasPermission(code) {
  if (!code) {
    return true;
  }
  if (isAdmin()) {
    return true;
  }
  return getPermissions().includes(code);
}

/**
 * 是否拥有任意一个权限码（多码为「或」关系，管理员直通）
 * @param {string|Array<string>} codes 权限码或权限码数组
 * @returns {boolean} 是否有权限
 */
export function hasAnyPermission(codes) {
  const list = Array.isArray(codes) ? codes : [codes];
  if (!list.length) {
    return true;
  }
  if (isAdmin()) {
    return true;
  }
  const owned = getPermissions();
  return list.some((code) => owned.includes(code));
}

/**
 * 获取当前用户激活的权限组信息
 * @returns {Object|null} { groupId, groupCode, groupTitle }，未激活返回 null
 */
export function getActiveGroup() {
  const user = getLoginUser();
  if (!user || !user.groupId) {
    return null;
  }
  return {
    groupId: user.groupId,
    groupCode: user.groupCode,
    groupTitle: user.groupTitle,
  };
}

/**
 * 获取当前用户激活的权限组ID
 * @returns {number|null} 权限组ID
 */
export function getActiveGroupId() {
  const group = getActiveGroup();
  return group ? group.groupId : null;
}

/**
 * 获取字段权限配置（模块 -> 字段 -> { visible, editable }）
 * @returns {Object} 字段权限配置
 */
export function getFieldPermissions() {
  const user = getLoginUser();
  const fieldPermissions = user && user.fieldPermissions;
  return fieldPermissions && typeof fieldPermissions === "object" ? fieldPermissions : {};
}

/**
 * 获取数据权限配置（模块 -> { scope, customDeptIds }）
 * @returns {Object} 数据权限配置
 */
export function getDataScopes() {
  const user = getLoginUser();
  const dataScopes = user && user.dataScopes;
  return dataScopes && typeof dataScopes === "object" ? dataScopes : {};
}

/**
 * 字段名归一为 camelCase 键
 *
 * request.js 会把响应中所有对象键转为 camelCase，故后端 snake_case 字段名
 * （如 shop_name）在 fieldPermissions 中对应 shopName，查询前需统一转换。
 * @param {string} field 字段名
 * @returns {string} camelCase 字段名
 */
export function toFieldKey(field) {
  if (typeof field !== "string") {
    return field;
  }
  return field.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
}

/**
 * 字段是否可见（管理员直通；未声明默认可见）
 * @param {string} module 业务模块
 * @param {string} field 字段名
 * @returns {boolean} 是否可见
 */
export function isFieldVisible(module, field) {
  if (!module || !field || isAdmin()) {
    return true;
  }
  const conf = (getFieldPermissions()[module] || {})[toFieldKey(field)];
  if (!conf) {
    return true;
  }
  return !!conf.visible;
}

/**
 * 字段是否可编辑（管理员直通；未声明默认可编辑；不可见则不可编辑）
 * @param {string} module 业务模块
 * @param {string} field 字段名
 * @returns {boolean} 是否可编辑
 */
export function isFieldEditable(module, field) {
  if (!module || !field || isAdmin()) {
    return true;
  }
  const conf = (getFieldPermissions()[module] || {})[toFieldKey(field)];
  if (!conf) {
    return true;
  }
  return !!conf.visible && !!conf.editable;
}

/**
 * 获取指定模块的数据权限范围
 * @param {string} module 业务模块
 * @returns {Object} { scope, customDeptIds }，未配置默认 self
 */
export function getDataScope(module) {
  const conf = (module && getDataScopes()[module]) || null;
  if (!conf) {
    return { scope: "self", customDeptIds: [] };
  }
  return {
    scope: conf.scope || "self",
    customDeptIds: Array.isArray(conf.customDeptIds) ? conf.customDeptIds : [],
  };
}

/**
 * 更新本地登录用户信息（切换权限组后刷新权限上下文）
 * @param {Object} user 用户信息
 * @returns {void}
 */
export function setLoginUser(user) {
  if (!user) {
    return;
  }
  localStorage.setItem("user", JSON.stringify(user));
}

/**
 * 写入登录态
 * @param {Object} data 登录接口 data 字段，含 token 与 user
 * @returns {void}
 */
export function setLoginData(data) {
  if (!data) {
    return;
  }
  if (data.token) {
    localStorage.setItem("token", data.token);
  }
  if (data.user) {
    localStorage.setItem("user", JSON.stringify(data.user));
  }
}

/**
 * 清除登录态
 * @returns {void}
 */
export function clearLoginData() {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
}
