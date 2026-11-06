/**
 * 首页解析工具
 *
 * 用户的「首页」不是固定的 /dashboard，而是其第一个可访问菜单：
 * 按后端返回的菜单树（已按当前权限组过滤）取第一个能匹配到前端路由的叶子路径。
 */

import request from "@/utils/request";

/**
 * 解析当前登录用户第一个可访问的菜单路径
 * @param {import("vue-router").Router} router 路由实例（用于过滤已注册路由）
 * @returns {Promise<string|null>} 首个可访问路径，无可访问菜单返回 null
 */
export async function resolveHomePath(router) {
  const knownPaths = new Set(
    router
      .getRoutes()
      .filter((item) => item.path && !item.path.includes(":"))
      .map((item) => item.path)
  );
  try {
    const res = await request.post("/admin/menu/get-user-menu-tree", {});
    const tree = res && res.code === 200 ? res.data || [] : [];
    const paths = [];
    const walk = (nodes) => {
      (nodes || []).forEach((node) => {
        if (node.children && node.children.length) {
          walk(node.children);
        } else if (node.path && knownPaths.has(node.path)) {
          paths.push(node.path);
        }
      });
    };
    walk(tree);
    return paths.length ? paths[0] : null;
  } catch (error) {
    console.error("获取菜单树失败:", error);
    return null;
  }
}
