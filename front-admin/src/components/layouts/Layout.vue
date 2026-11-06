<template>
  <el-container class="layout-container">
    <el-aside width="232px" class="sidebar">
      <div class="logo">
        <h2>xf</h2>
      </div>
      <el-menu
        v-if="apiMenuTree.length"
        :default-active="activeMenu"
        router
        :unique-opened="true"
      >
        <template v-for="item in apiMenuTree" :key="item.id">
          <el-sub-menu
            v-if="item.type === 1 && item.children && item.children.length > 0"
            :index="item.path || String(item.id)"
          >
            <template #title>
              <el-icon>
                <component :is="item.icon || 'Menu'" />
              </el-icon>
              <span>{{ item.name }}</span>
            </template>
            <el-menu-item
              v-for="child in item.children"
              :key="child.id"
              :index="child.path"
            >
              <el-icon>
                <component :is="child.icon || 'Menu'" />
              </el-icon>
              <span>{{ child.name }}</span>
            </el-menu-item>
          </el-sub-menu>
          <el-menu-item v-else :index="item.path || String(item.id)">
            <el-icon>
              <component :is="item.icon || 'Menu'" />
            </el-icon>
            <span>{{ item.name }}</span>
          </el-menu-item>
        </template>
      </el-menu>
      <div v-else class="menu-empty">当前无可用菜单</div>
    </el-aside>
    <el-container class="main-container">
      <el-header class="header">
        <div class="header-left">
          <span>{{ currentRoute.meta.title }}<template v-if="pageSubtitle">（{{ pageSubtitle }}）</template></span>
          <el-select
            v-if="menuGroups.length"
            v-model="selectedGroupId"
            class="group-select"
            placeholder="当前菜单未激活权限组"
            :disabled="groupSwitching"
            @change="handleGroupChange"
          >
            <template #prefix>
              <el-icon v-if="groupSwitching" class="is-loading">
                <Loading />
              </el-icon>
              <el-icon v-else>
                <Switch />
              </el-icon>
            </template>
            <el-option
              v-for="group in menuGroups"
              :key="group.id"
              :label="group.title"
              :value="group.id"
            />
          </el-select>
          <!-- 切换态提示：切换中 / 管理员不参与切换 / 未绑定权限组 -->
          <el-tag v-if="groupSwitching" class="group-status" type="warning" effect="plain">
            切换中…
          </el-tag>
          <el-tag v-else-if="adminUser" class="group-status" type="info" effect="plain">
            全量权限
          </el-tag>
          <el-tag v-else-if="!userGroups.length" class="group-status" type="info" effect="plain">
            未绑定权限组
          </el-tag>
        </div>
        <div class="header-right">
          <el-button
            v-permission="'nav:permission-group'"
            text
            title="权限组配置"
            style="margin-right: 8px"
            @click="menuGroupVisible = true"
          >
            <el-icon>
              <Lock />
            </el-icon>
          </el-button>
          <MessageNotification style="margin-right: 8px" />
          <el-button @click="toggleFullscreen" style="margin-right: 8px" text>
            <el-icon>
              <FullScreen />
            </el-icon>
          </el-button>
          <el-dropdown>
            <span class="user-info">
              <el-avatar :size="32" icon="UserFilled" />
              <span class="username">{{ userName }}</span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="$router.push('/profile')">个人设置</el-dropdown-item>
                <el-dropdown-item @click="handleLogout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="layout-main">
        <el-scrollbar
          class="main-scrollbar"
          :class="{ 'main-scrollbar--scrollable': mainScrollable }"
        >
          <div class="content-wrapper">
            <!-- keep-alive 缓存各菜单页实例：切走再切回时保留其最后一次打开的状态（筛选/分页/滚动/弹窗等），
                 不重新挂载即不重新取数；切换权限组时 viewKey 变化重建 keep-alive，清空缓存令页面按新权限重挂载 -->
            <router-view v-slot="{ Component }">
              <keep-alive :key="viewKey" :max="20">
                <component :is="Component" :key="currentRoute.name" />
              </keep-alive>
            </router-view>
          </div>
        </el-scrollbar>
      </el-main>
    </el-container>

    <GroupMenuConfigDialog
      v-model:visible="menuGroupVisible"
      :menu-code="currentRoute.meta.permission || ''"
      :menu-title="currentRoute.meta.title || ''"
      :menu-module="currentRoute.meta.module || ''"
    />
  </el-container>
</template>

<script setup>
import { computed, ref, onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { FullScreen, Loading, Lock, Switch } from "@element-plus/icons-vue";
import MessageNotification from "@/components/MessageNotification.vue";
import request from "@/utils/request";
import { getLoginUser, clearLoginData, setLoginUser, hasPermission } from "@/utils/permission";
// 页面 header 标题后的副标题（如当前套用的筛选条件名），由列表页写入
import { pageSubtitle } from "@/utils/pageSubtitle";
import {
  getUserGroups,
  activateUserGroup,
  getUserInfo,
} from "@/views/permission_group/permissionGroupApi";
import GroupMenuConfigDialog from "@/views/permission_group/components/GroupMenuConfigDialog.vue";

const route = useRoute();
const router = useRouter();

const isFullscreen = ref(false);
const apiMenuTree = ref([]);
const userGroups = ref([]);
const activeGroupId = ref(null);
const groupSwitching = ref(false);
const menuGroupVisible = ref(false);
// 切换权限组后自增，令 router-view 重挂载，使页面按新组权限重新渲染并重新取数
const viewKey = ref(0);

const activeMenu = computed(() => route.path);
// 兜底规则：仪表盘允许 main 区出现滚动条（内容可能超出视口），
// 其余页面 main 不显示滚动条，由页面内部表格/区域内滚动承担
const mainScrollable = computed(() => ["Dashboard"].includes(route.name));
const currentRoute = computed(() => route);
const userName = computed(() => {
  const user = getLoginUser() || {};
  return user.name || user.username || "未登录";
});

// 管理员直通全量权限，不参与权限组切换
const adminUser = computed(() => !!(getLoginUser() || {}).isAdmin);

// 只保留归属当前菜单的权限组（组 menu_code ↔ 路由 meta.permission），
// 切换器仅在当前菜单存在可选组时展示
const menuGroups = computed(() => {
  const menuCode = currentRoute.value.meta.permission;
  if (!menuCode) {
    return [];
  }
  return userGroups.value.filter((group) => group.menuCode === menuCode);
});

// 激活组不属于当前菜单时下拉回落为「未选择」，避免显示出无对应选项的裸 ID
const selectedGroupId = computed({
  get: () => {
    const id = activeGroupId.value;
    return menuGroups.value.some((group) => group.id === id) ? id : null;
  },
  set: (value) => {
    activeGroupId.value = value;
  },
});

// 拉取当前登录用户的菜单树（切换权限组后需重新拉取）
const fetchMenuTree = async () => {
  try {
    const res = await request.post("/admin/menu/get-user-menu-tree", {});
    if (res.code === 200) {
      apiMenuTree.value = res.data || [];
      return true;
    }
  } catch (error) {
    console.error("获取菜单树失败:", error);
  }
  return false;
};

onMounted(() => {
  fetchMenuTree();
  fetchUserGroups();
});

// 路由守卫在进入菜单时会自动对齐激活组，这里同步切换器的选中项
watch(
  () => route.meta.permission,
  () => {
    fetchUserGroups();
  }
);

// 查询当前用户可用的权限组与激活状态（管理员返回空，不展示切换器）
const fetchUserGroups = async () => {
  try {
    const res = await getUserGroups();
    if (res.code === 200) {
      const data = res.data || {};
      userGroups.value = data.items || [];
      activeGroupId.value = data.activeGroupId || null;
    }
  } catch (error) {
    console.error("获取可用权限组失败:", error);
  }
};

// 新权限组下当前菜单可能已不可见，落到新组的第一个可见菜单；
// 新组无任何可见菜单则退回无权限页
const resolveFallbackPath = () => {
  if (hasPermission(route.meta.permission)) {
    return null;
  }
  const knownPaths = new Set(
    router
      .getRoutes()
      .filter((item) => item.path && !item.path.includes(":"))
      .map((item) => item.path)
  );
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
  walk(apiMenuTree.value);
  return paths.length ? paths[0] : "/403";
};

// 按「组」互斥切换：同一时刻仅一个组生效；只能切换，不支持清空
const handleGroupChange = async (groupId) => {
  if (groupSwitching.value || !groupId) {
    return;
  }
  groupSwitching.value = true;
  try {
    const res = await activateUserGroup(groupId);
    if (res.code !== 200) {
      ElMessage.error(res.message || "切换权限组失败");
      await fetchUserGroups();
      return;
    }
    const info = await getUserInfo();
    if (info.code === 200 && info.data) {
      setLoginUser({ ...(getLoginUser() || {}), ...info.data });
    }
    await fetchMenuTree();
    await fetchUserGroups();
    const fallback = resolveFallbackPath();
    if (fallback) {
      await router.replace(fallback);
    } else {
      // 路由未变时主动重挂载，让页面按新组权限重渲染并重新取数
      viewKey.value += 1;
    }
    ElMessage.success("权限组已切换");
  } catch (error) {
    console.error("切换权限组失败:", error);
    await fetchUserGroups();
  } finally {
    groupSwitching.value = false;
  }
};

// 退出登录：清除本地登录态并跳转登录页
const handleLogout = () => {
  clearLoginData();
  router.push("/login");
};

// 全屏切换
const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen().catch((err) => {
      ElMessage.warning(`全屏失败: ${err.message}`);
    });
    isFullscreen.value = true;
  } else {
    if (document.exitFullscreen) {
      document.exitFullscreen();
      isFullscreen.value = false;
    }
  }
};

// 监听全屏变化
const handleFullscreenChange = () => {
  isFullscreen.value = !!document.fullscreenElement;
};

document.addEventListener("fullscreenchange", handleFullscreenChange);
</script>

<style scoped>
.layout-container {
  height: 100%;
}

/* --- 侧边栏 (TDesign 规格: 232px / 白底) --- */
.sidebar {
  background-color: var(--td-bg-color-container);
  overflow-x: hidden;
}

.logo {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 16px;
  background-color: var(--td-bg-color-container);
  border-bottom: 1px solid var(--td-border-level-1-color);
}

.logo h2 {
  color: var(--td-text-color-primary);
  font-size: var(--td-font-size-title-large);
  font-weight: 600;
  margin: 0;
}

/* el-menu 子项样式覆盖 */
.sidebar .el-menu {
  border-right: none;
  padding: 8px 0;
  --el-menu-bg-color: var(--td-bg-color-container);
  --el-menu-text-color: var(--td-text-color-primary);
  --el-menu-active-color: var(--td-brand-color);
  --el-menu-hover-bg-color: var(--td-bg-color-container-hover);
  --el-menu-item-height: var(--td-comp-size-l);
  --el-menu-sub-item-height: var(--td-comp-size-l);
  --el-menu-item-font-size: var(--td-font-size-body-medium);
}

.sidebar .el-menu-item,
.sidebar .el-sub-menu__title {
  height: var(--td-comp-size-l);
  line-height: var(--td-comp-size-l);
  padding: 0 8px 0 16px !important;
  margin: 0;
  border-radius: var(--td-radius-default);
  font-size: var(--td-font-size-body-medium);
  font-weight: 400;
  color: var(--td-text-color-primary);
}

/* el-sub-menu__title 由 Element Plus 内部渲染，不继承本组件 scoped 作用域，
   必须用 :deep 命中；仅对齐左内边距，右侧保留 EP 默认值以容纳展开箭头 */
.sidebar :deep(.el-sub-menu__title) {
  padding-left: 16px !important;
}

/* 展开箭头右移贴近菜单右缘（EP 默认 right: 20px） */
.sidebar :deep(.el-sub-menu__title .el-sub-menu__icon-arrow) {
  right: 4px;
}

.sidebar .el-menu-item:hover,
.sidebar .el-sub-menu__title:hover {
  background-color: var(--td-bg-color-container-hover) !important;
  color: var(--td-text-color-primary) !important;
}

.sidebar .el-menu-item.is-active {
  background-color: var(--td-brand-color-light) !important;
  color: var(--td-brand-color) !important;
}

.sidebar .el-sub-menu .el-menu {
  background-color: transparent;
}

.sidebar .el-sub-menu .el-menu-item {
  padding-left: 44px !important;
  font-size: var(--td-font-size-body-medium);
  height: var(--td-comp-size-l);
  line-height: var(--td-comp-size-l);
}

/* --- 顶栏 (TDesign 规格: 56px / 白底) --- */
.main-container {
  display: flex;
  flex-direction: column;
}

.header {
  height: 56px !important;
  background-color: var(--td-bg-color-container);
  border-bottom: 1px solid var(--td-border-level-1-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.header-left,
.header-right {
  display: flex;
  align-items: center;
}

.header-left span {
  font-size: var(--td-font-size-title-medium);
  font-weight: 600;
  color: var(--td-text-color-primary);
}

.group-select {
  width: 180px;
  margin-left: 16px;
}

/* 头部权限组状态标签：外观与同位置的权限组下拉框（.group-select）保持一致 */
.header-left .el-tag.group-status {
  width: 150px;
  height: 32px;
  margin-left: 16px;
  padding: 0 12px;
  justify-content: flex-start;
  background-color: var(--td-bg-color-secondarycontainer);
  border: none;
  border-radius: 3px;
  box-shadow: inset 0 0 0 1px #e8e8e8;
}

/* 屏蔽 .header-left span 的标题字号/字重，与下拉框内的文本一致 */
.header-left .el-tag.group-status :deep(.el-tag__content) {
  font-size: 14px;
  font-weight: 400;
}

.menu-empty {
  padding: 24px 16px;
  color: var(--td-text-color-placeholder);
  font-size: var(--td-font-size-body-small);
  line-height: 1.8;
}

/* 图标按钮 hover/按下仅改变颜色，不显示底色块 */
.header-right > .el-button.is-text:not(.is-disabled):hover,
.header-right > .el-button.is-text:not(.is-disabled):active {
  color: var(--td-brand-color);
  background-color: transparent;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.username {
  margin-left: 8px;
  color: var(--td-text-color-secondary);
  font-size: var(--td-font-size-body-medium);
}

/* --- 内容区 (TDesign 规格: padding 24px / bg #eee) --- */
/* 类名刻意避开 .main-content：各列表页存在同名全局样式（display:flex），
   若复用该名会把本 el-main 也变成 flex 容器，导致页面内容无法撑满宽度 */
.layout-main {
  background-color: var(--td-bg-color-page);
  /* 右侧不留内边距，让 el-scrollbar 贴到 main 右缘（滚动条落在 main 上） */
  padding: 24px 0 24px 24px;
  /* 原生滚动条交由内部 el-scrollbar 组件承担，避免出现双滚动条 */
  overflow: hidden;
}

/* el-scrollbar 撑满内容区，滚动由组件自绘的细滚动条承担 */
.main-scrollbar {
  height: 100%;
}

/* el-scrollbar 内部结构由 EP 渲染，需 :deep 命中；
   view 给确定高度，使 .content-wrapper 的 height:100% 生效（维持列表页表格撑满规范）。
   仪表盘例外：其内容高度随数据异步增长，若 view 固定 100%，
   EP 的 ResizeObserver（观察 view）不会重新测量，滚动到底部时 thumb 会溢出轨道被裁剪 */
.main-scrollbar:not(.main-scrollbar--scrollable) :deep(.el-scrollbar__view) {
  height: 100%;
}

/* 兜底规则：除仪表盘外，main 区不出现滚动条
   （EP 已通过 --hidden-default 隐藏原生滚动条，这里只需隐藏组件自绘的滚动条）。
   注意必须用子选择器，只隐藏 main 滚动条自身的 bar，
   否则会连带隐藏 el-table 内部 el-scrollbar 的滚动条（表格 scrollbar 需正常显示） */
.main-scrollbar:not(.main-scrollbar--scrollable) > :deep(.el-scrollbar__bar) {
  display: none;
}

/* 右侧留白改由内容容器承担（等价于原 el-main 的 24px 右内边距） */
.content-wrapper {
  padding-right: 24px;
}
</style>
