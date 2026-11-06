import { createRouter, createWebHistory } from "vue-router";
import Layout from "@/components/layouts/Layout.vue";
import { hasPermission } from "@/utils/permission";
import { resolveHomePath } from "@/utils/homePath";
import { alignGroupForMenu } from "@/utils/groupAlign";

const routes = [
  {
    path: "/login",
    name: "Login",
    component: () => import("@/views/auth/Login.vue"),
    meta: { title: "登录" },
  },
  {
    path: "/403",
    name: "Forbidden",
    component: () => import("@/views/error/Forbidden.vue"),
    meta: { title: "无访问权限" },
  },
  {
    path: "/",
    component: Layout,
    redirect: "/dashboard",
    children: [
      {
        path: "dashboard",
        name: "Dashboard",
        component: () => import("@/views/dashboard/index.vue"),
        meta: { title: "仪表盘", icon: "Odometer", permission: "nav:dashboard", module: "dashboard" },
      },
      {
        path: "demo",
        name: "Demo",
        component: () => import("@/views/demo/Demo.vue"),
        meta: { title: "Demo 示例", icon: "Star", permission: "nav:demo", module: "demo" },
      },
      {
        path: "organization",
        name: "Organization",
        component: () => import("@/views/organization/Organization.vue"),
        meta: { title: "组织管理", icon: "UserFilled", permission: "nav:organization", module: "organization" },
      },
      {
        path: "permission-group",
        name: "PermissionGroup",
        component: () => import("@/views/permission_group/PermissionGroup.vue"),
        meta: { title: "权限组管理", icon: "Lock", permission: "nav:permission-group", module: "permission_group" },
      },
      {
        path: "menu",
        name: "Menu",
        component: () => import("@/views/menu/Menu.vue"),
        meta: { title: "菜单管理", icon: "Menu", permission: "nav:menu", module: "sysmenu" },
      },

      {
        path: "profile",
        name: "Profile",
        component: () => import("@/views/profile/Profile.vue"),
        meta: { title: "个人设置", icon: "Setting", module: "profile" },
      },
      {
        path: "log",
        name: "Log",
        component: () => import("@/views/log/Log.vue"),
        meta: { title: "日志管理", icon: "Document", permission: "nav:log", module: "log" },
      },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to, from) => {
  document.title = to.meta.title
    ? `${to.meta.title} - xf`
    : "xf";

  const isPublicPage = to.path === "/login" || to.path === "/403";

  // 未登录时跳转登录页（登录页/无权限页本身除外）
  if (!isPublicPage && !localStorage.getItem("token")) {
    return "/login";
  }

  // 已登录用户访问登录页时，回到该账号第一个可访问菜单（而非固定 /dashboard）
  if (to.path === "/login" && localStorage.getItem("token")) {
    return (await resolveHomePath(router)) || "/403";
  }

  // 路由级权限拦截：meta.permission 存在且未授权时跳转无权限页
  if (!isPublicPage && !hasPermission(to.meta.permission)) {
    return "/403";
  }

  // 进入菜单前对齐激活组（详见 utils/groupAlign.js 注释）
  if (!isPublicPage) {
    await alignGroupForMenu(
      to.meta && to.meta.permission,
      from && from.meta && from.meta.permission,
    );
  }

  return true;
});

export default router;
