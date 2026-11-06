/**
 * 菜单权限组对齐
 *
 * 菜单可见性取自用户「全部可用权限组」的并集，但操作/字段/数据权限只来自
 * 「激活组」。因此进入某菜单前必须把激活组切到该菜单下的可用组，否则页面
 * 接口会因缺少操作权限而报 403（如「缺少权限: dashboard:view」）。
 *
 * 路由守卫在导航时对齐；页面接口若仍因缺少操作权限失败，可再次调用本方法
 * 自愈（对齐后重试），避免「已授权仍 403」。
 */

import { getLoginUser, setLoginUser } from "@/utils/permission";
import {
  getUserGroups,
  activateUserGroup,
  getUserInfo,
} from "@/views/permission_group/permissionGroupApi";

// 记录离开各菜单时用户选中的权限组，回到该菜单时优先还原其选择
const lastGroupByMenu = {};

/**
 * 将激活权限组对齐到目标菜单下的可用组
 *
 * @param {string} menuCode 目标菜单权限码（如 nav:dashboard）
 * @param {string} [fromMenuCode] 离开的菜单权限码，用于记忆用户在该菜单选中的组
 * @returns {Promise<number|null>} 对齐后的激活组ID；无需对齐或失败返回当前（可能为 null）
 */
export async function alignGroupForMenu(menuCode, fromMenuCode) {
  if (!menuCode || (getLoginUser() || {}).isAdmin) {
    return null;
  }
  try {
    const res = await getUserGroups();
    if (!res || res.code !== 200) {
      return null;
    }
    const items = (res.data && res.data.items) || [];
    const activeGroupId = res.data && res.data.activeGroupId;

    // 离开旧菜单前记住它当前生效的组
    if (
      fromMenuCode &&
      items.some((group) => group.id === activeGroupId && group.menuCode === fromMenuCode)
    ) {
      lastGroupByMenu[fromMenuCode] = activeGroupId;
    }

    const candidates = items.filter((group) => group.menuCode === menuCode);
    if (!candidates.length || candidates.some((group) => group.id === activeGroupId)) {
      return activeGroupId;
    }
    const preferred = candidates.find((group) => group.id === lastGroupByMenu[menuCode]);
    const target =
      preferred || [...candidates].sort((a, b) => (a.sort || 0) - (b.sort || 0))[0];

    const activated = await activateUserGroup(target.id);
    if (!activated || activated.code !== 200) {
      console.warn(
        "菜单权限组自动对齐失败，页面可能因缺少操作权限而报 403:",
        (activated && activated.message) || "未知错误",
      );
      return activeGroupId;
    }
    // 同步本地登录态，使页面挂载时即按新组权限渲染（避免按钮级权限判断失真）
    const info = await getUserInfo();
    if (info.code === 200 && info.data) {
      setLoginUser({ ...(getLoginUser() || {}), ...info.data });
    }
    return target.id;
  } catch (error) {
    console.error("菜单权限组自动对齐失败:", error);
    return null;
  }
}
