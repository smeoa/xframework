<template>
  <el-card shadow="hover" class="settings-card">
    <template #header>
      <div class="card-header">
        <span>通知偏好</span>
      </div>
    </template>

    <el-scrollbar class="card-scrollbar">
      <div class="settings-content">
        <!-- 系统通知 -->
        <div class="setting-group">
          <h4 class="group-title">系统通知</h4>
          <el-divider />
          <div class="setting-item">
            <span class="setting-label">登录通知</span>
            <el-switch v-model="notificationSettings.loginNotification" />
          </div>
          <div class="setting-item">
            <span class="setting-label">操作审核通知</span>
            <el-switch v-model="notificationSettings.auditNotification" />
          </div>
          <div class="setting-item">
            <span class="setting-label">系统更新通知</span>
            <el-switch
              v-model="notificationSettings.systemUpdateNotification"
            />
          </div>
        </div>

        <!-- 邮件通知 -->
        <div class="setting-group" style="margin-top: 32px">
          <h4 class="group-title">邮件通知</h4>
          <el-divider />
          <div class="setting-item">
            <span class="setting-label">账户安全提醒</span>
            <el-switch v-model="notificationSettings.emailSecurity" />
          </div>
          <div class="setting-item">
            <span class="setting-label">业务审批提醒</span>
            <el-switch v-model="notificationSettings.emailApproval" />
          </div>
          <div class="setting-item">
            <span class="setting-label">系统公告</span>
            <el-switch v-model="notificationSettings.emailAnnouncement" />
          </div>
        </div>

        <!-- 消息提醒 -->
        <div class="setting-group" style="margin-top: 32px">
          <h4 class="group-title">消息提醒</h4>
          <el-divider />
          <div class="setting-item">
            <span class="setting-label">桌面通知</span>
            <el-switch v-model="notificationSettings.desktopNotification" />
          </div>
          <div class="setting-item">
            <span class="setting-label">声音提醒</span>
            <el-switch v-model="notificationSettings.soundNotification" />
          </div>
        </div>
      </div>
    </el-scrollbar>

    <template #footer>
      <div class="action-buttons">
        <el-button type="primary" @click="handleSave">保存设置</el-button>
        <el-button @click="handleReset">恢复默认</el-button>
      </div>
    </template>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from "vue";
import request from "@/utils/request";

const notificationSettings = ref({
  loginNotification: true,
  auditNotification: true,
  systemUpdateNotification: true,
  emailSecurity: true,
  emailApproval: true,
  emailAnnouncement: false,
  desktopNotification: true,
  soundNotification: false,
});

const defaultSettings = {
  loginNotification: true,
  auditNotification: true,
  systemUpdateNotification: true,
  emailSecurity: true,
  emailApproval: true,
  emailAnnouncement: false,
  desktopNotification: true,
  soundNotification: false,
};

onMounted(() => {
  loadNotificationSettings();
});

const loadNotificationSettings = async () => {
  try {
    const response = await request.post(
      "/admin/profile/get-notification-settings",
    );
    if (response.code === 200) {
      notificationSettings.value = response.data;
    }
  } catch (error) {
    console.error("获取通知设置失败:", error);
  }
};

const handleSave = async () => {
  try {
    const response = await request.post(
      "/admin/profile/update-notification-settings",
      {
        data: notificationSettings.value,
      },
    );
    if (response.code === 200) {
      ElMessage.success("保存成功");
    }
  } catch (error) {
    console.error("保存通知设置失败:", error);
    ElMessage.error("保存失败，请重试");
  }
};

const handleReset = () => {
  notificationSettings.value = { ...defaultSettings };
};
</script>

<style scoped>
.notification-settings {
  padding: 20px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 20px;
  color: var(--td-text-color-primary);
}

/* 卡片高度自适应父容器：纵向 flex 撑满，头部固定、主体滚动 */
.settings-card {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
  margin-bottom: 0;
}

/* body 作为滚动区域外壳：占满剩余高度，内边距下移到滚动内容上，
   避免滚动条宽度占用内容盒（滚动条由 el-scrollbar 自绘） */
.settings-card :deep(.el-card__body) {
  flex: 1;
  min-height: 0;
  padding: 0;
  overflow: hidden;
}

/* 滚动容器铺满 body，滚动条贴卡片右缘 */
.card-scrollbar {
  height: 100%;
}

.card-scrollbar :deep(.el-scrollbar__view) {
  padding: var(--td-comp-paddingTB-l) 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.settings-content {
  padding: 20px;
}

.setting-group {
  margin-bottom: 20px;
}

.group-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--td-text-color-primary);
  margin-bottom: 8px;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.setting-item:last-child {
  border-bottom: none;
}

.setting-label {
  font-size: 14px;
  color: var(--td-text-color-secondary);
}

.action-buttons {
  display: flex;
  gap: 8px;
}
</style>
