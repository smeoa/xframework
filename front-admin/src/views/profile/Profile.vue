<template>
  <el-container style="padding: 0">
    <el-main style="min-height: 0">
      <el-card
        shadow="hover"
        class="profile-card"
        style="height: 100%; display: flex; flex-direction: column"
      >
        <template #header>
          <div class="card-header">
            <h2 class="title">个人设置</h2>
          </div>
        </template>

        <div class="profile-content" style="flex: 1; display: flex; gap: 20px">
          <!-- 左侧导航 -->
          <div class="sidebar" style="width: 200px; flex-shrink: 0">
            <el-menu
              :default-active="activeTab"
              class="profile-menu"
              @select="handleTabChange"
            >
              <el-menu-item index="profile">
                <el-icon><User /></el-icon>
                <span>个人资料</span>
              </el-menu-item>
              <el-menu-item index="security">
                <el-icon><Lock /></el-icon>
                <span>账号安全</span>
              </el-menu-item>
              <el-menu-item index="login-logs">
                <el-icon><Clock /></el-icon>
                <span>登录记录</span>
              </el-menu-item>
              <el-menu-item index="notification">
                <el-icon><Bell /></el-icon>
                <span>通知设置</span>
              </el-menu-item>
              <el-menu-item index="preference">
                <el-icon><Setting /></el-icon>
                <span>界面偏好</span>
              </el-menu-item>
              <el-menu-item index="api-key">
                <el-icon><Key /></el-icon>
                <span>API 密钥</span>
              </el-menu-item>
            </el-menu>
          </div>

          <!-- 右侧内容 -->
          <div
            class="content"
            style="flex: 1; background: #ffffff; border: 0px solid #e4e7ed"
          >
            <component :is="activeComponent" />
          </div>
        </div>
      </el-card>
    </el-main>
  </el-container>
</template>

<script setup>
import { ref, computed } from "vue";
import { User, Lock, Clock, Bell, Setting, Key } from "@element-plus/icons-vue";

// 导入子组件
import ProfileInfo from "./components/ProfileInfo.vue";
import AccountSecurity from "./components/AccountSecurity.vue";
import LoginLogs from "./components/LoginLogs.vue";
import NotificationSettings from "./components/NotificationSettings.vue";
import InterfacePreference from "./components/InterfacePreference.vue";
import ApiKeyManagement from "./components/ApiKeyManagement.vue";

const activeTab = ref("profile");

const activeComponent = computed(() => {
  const components = {
    profile: ProfileInfo,
    security: AccountSecurity,
    "login-logs": LoginLogs,
    notification: NotificationSettings,
    preference: InterfacePreference,
    "api-key": ApiKeyManagement,
  };
  return components[activeTab.value] || ProfileInfo;
});

const handleTabChange = (tab) => {
  activeTab.value = tab;
};
</script>

<style scoped>
.el-main {
  padding: 0;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.profile-menu {
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.profile-menu .el-menu-item {
  height: 48px;
  line-height: 48px;
  margin: 4px 8px;
  border-radius: 4px;
}

.profile-menu .el-menu-item:hover {
  background-color: #ecf5ff;
}

.profile-menu .el-menu-item.is-active {
  background-color: var(--brand-color);
  color: var(--td-text-color-anti);
}

/* el-card__body 默认是普通块级元素，导致 .profile-content 的 flex:1 失效（高度由内容决定）。
   改为纵向 flex 并撑满卡片，让右侧内容区获得确定高度，从而实现子卡片高度自适应。
   必须限定为直接子级（>），否则会命中内部子卡片的 body（如账号安全页的表格被压扁） */
.profile-card > :deep(.el-card__body) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.profile-content {
  min-height: 0;
}

/* flex 子项默认 min-width:auto，会被右侧内容（如宽表格）撑宽导致整卡片溢出被裁剪，需允许收缩 */
.content {
  min-width: 0;
  min-height: 0;
  /* 纵向 flex：让各页签根卡片获得确定高度，实现高度自适应与卡片内滚动 */
  display: flex;
  flex-direction: column;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .profile-content {
    flex-direction: column;
  }

  .sidebar {
    width: 100% !important;
  }

  .profile-menu {
    display: flex;
    overflow-x: auto;
  }

  .profile-menu .el-menu-item {
    min-width: 100px;
  }
}
</style>
