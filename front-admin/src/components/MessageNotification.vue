<template>
  <div class="message-notification">
    <!-- 消息图标 -->
    <el-button @click="drawerVisible = true" text title="消息中心">
      <div class="message-icon">
        <el-icon class="icon">
          <Bell />
        </el-icon>
        <el-badge v-if="unreadCount > 0" :value="unreadCount" class="badge" />
      </div>
    </el-button>
    <!-- 消息中心抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      title="消息中心"
      direction="rtl"
      size="800px"
      :show-close="false"
    >
      <template #header>
        消息中心
        <div style="display: flex; justify-content: flex-end">
          <el-button @click="drawerVisible = false" title="关闭" text>
            <el-icon>
              <Close />
            </el-icon>
          </el-button>
        </div>
      </template>
      <div class="message-center">
        <!-- 消息中心头部 -->
        <div class="message-header">
          <div class="message-header-actions">
            <el-select
              v-model="activeCategory"
              placeholder="全部"
              class="category-select"
            >
              <el-option label="全部" value="all" />
              <el-option label="系统通知" value="system" />
              <el-option label="下载通知" value="download" />
              <el-option label="异常提醒" value="warning" />
            </el-select>
          </div>
          <div class="message-header-actions">
            <el-checkbox v-model="onlyUnread" label="只看未读" />
            <el-button type="primary" @click="markAllAsRead"
              >全部标记为已读</el-button
            >
          </div>
        </div>

        <!-- 消息列表 -->
        <el-scrollbar class="message-list">
          <div v-if="filteredMessages.length === 0" class="empty-message">
            暂无通知
          </div>
          <div v-else class="message-list-content">
            <div
              v-for="message in filteredMessages"
              :key="message.id"
              class="message-item"
              :class="{ unread: !message.read }"
            >
              <!-- 悬停显示的复制按钮：复制该条消息正文到剪贴板 -->
              <el-icon
                class="message-copy"
                title="复制"
                @click.stop="copyContent(message.content)"
              >
                <CopyDocument />
              </el-icon>
              <div class="message-content">
                <div class="message-time">
                  {{ formatTime(message.timestamp) }}
                </div>
                <div class="message-body">{{ message.content }}</div>
                <div class="message-footer">
                  <el-button
                    v-if="message.downloadUrl"
                    type="primary"
                    @click.stop="handleDownload(message.downloadUrl)"
                  >
                    立即下载
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </el-scrollbar>
        <!-- 分页 -->
        <div class="message-pagination">
          <el-pagination
            layout="prev, pager, next"
            :total="messages.length"
            :page-size="10"
            :current-page="currentPage"
            @current-change="handlePageChange"
            size="small"
          />
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from "vue";
import { Bell, Warning, Download, CopyDocument } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import wsManager from "@/utils/wsManager";
import request from "@/utils/request";
import { downloadFileWithToken } from "@/utils/fileUtils";

const messages = ref([]);
const activeCategory = ref("all");
const onlyUnread = ref(false);
const currentPage = ref(1);
const pageSize = ref(10);
const drawerVisible = ref(false);

// 监听分类和未读状态变化
watch([activeCategory, onlyUnread], async () => {
  await fetchMessages();
});

// 未读消息数量
const unreadCount = computed(() => {
  return messages.value.filter((msg) => !msg.read).length;
});

// 过滤后的消息
const filteredMessages = computed(() => {
  let result = [...messages.value];

  // 按分类过滤
  if (activeCategory.value !== "all") {
    result = result.filter((msg) => msg.type === activeCategory.value);
  }

  // 按未读状态过滤
  if (onlyUnread.value) {
    result = result.filter((msg) => !msg.read);
  }

  // 按时间倒序排序
  result.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

  // 分页
  const startIndex = (currentPage.value - 1) * pageSize.value;
  const endIndex = startIndex + pageSize.value;
  result = result.slice(startIndex, endIndex);

  return result;
});

// 获取指定类型的未读消息数量
const getUnreadCount = (type) => {
  return messages.value.filter((msg) => !msg.read && msg.type === type).length;
};

// 格式化时间
const formatTime = (timestamp) => {
  const date = new Date(timestamp);
  return date.toLocaleString();
};

// 标记所有消息为已读
const markAllAsRead = async () => {
  try {
    const response = await request.post("/admin/notification/mark-all-as-read");
    if (response.code === 200) {
      // 重新获取消息列表
      await fetchMessages();
    }
  } catch (error) {
    console.error("标记已读失败:", error);
  }
};

// 处理下载（携带 token 请求后以 Blob 保存，直链无法通过后端鉴权）
const handleDownload = (url) => {
  downloadFileWithToken(url, "导出文件.xlsx");
};

// 复制消息正文到剪贴板
const copyContent = async (content) => {
  const value = String(content || "").trim();
  if (!value) {
    ElMessage.warning("暂无可复制内容");
    return;
  }
  try {
    await navigator.clipboard.writeText(value);
    ElMessage.success("已复制");
  } catch (error) {
    console.error("复制失败:", error);
    ElMessage.error("复制失败");
  }
};

// 处理分页变更
const handlePageChange = (page) => {
  currentPage.value = page;
};

// 从后台API获取消息列表
const fetchMessages = async () => {
  try {
    const response = await request.post(
      "/admin/notification/get-message-list",
      {
        type: activeCategory.value,
        onlyUnread: onlyUnread.value,
      },
    );
    if (response.code === 200) {
      messages.value = Array.isArray(response.data) ? response.data : [];
    }
  } catch (error) {
    console.error("获取消息列表失败:", error);
    messages.value = [];
  }
};

// 处理下拉菜单显示/隐藏
const handleDropdownVisibleChange = (visible) => {
  if (visible) {
    // 标记所有消息为已读
    markAllAsRead();
  }
};

// 传输层/握手类 WS 消息：不携带业务通知，不触发消息列表刷新
// （否则服务端每 30s 的心跳 ping、连接抖动时的 user_left 都会产生一次无意义的列表查询）
const WS_PLUMBING_TYPES = new Set([
  "ping",
  "pong",
  "echo",
  "broadcast",
  "private",
  "user_left",
  "register_success",
]);

// 处理 WebSocket 消息：仅业务消息（任务完成/失败/进度等）才拉取最新消息列表
const handleWebSocketMessage = (message) => {
  const type = String(message?.type || "");
  if (!type || WS_PLUMBING_TYPES.has(type)) return;
  fetchMessages();
};

// 初始化 WebSocket 连接
let offMessage = null;

onMounted(async () => {
  // connect 为幂等调用：复用单例已有连接，并在已连接时补发注册消息
  wsManager.connect();
  offMessage = wsManager.onMessage(handleWebSocketMessage);
  wsManager.enableExportNotifications();
  // 从后台API获取消息列表
  await fetchMessages();
});

onUnmounted(() => {
  // 仅退订本组件的消息处理，共享连接由 wsManager 单例统一维护，不能在此断开
  if (offMessage) {
    offMessage();
    offMessage = null;
  }
});
</script>

<style scoped>
.message-notification {
  position: relative;
}

/* 按钮 hover/按下不显示底色块，颜色变化由 .message-icon 负责 */
.message-notification .el-button.is-text:not(.is-disabled):hover,
.message-notification .el-button.is-text:not(.is-disabled):active {
  background-color: transparent;
}

.message-icon {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 14px;
  color: var(--td-text-color-secondary);
  transition: color 0.3s;
}

.message-icon:hover {
  color: var(--td-text-color-brand);
}

.badge {
  position: absolute;
  top: 0;
  right: 0;
}

/* 角标居中吸附消息图标右上角（el-badge 无默认插槽时角标为静态定位，需显式绝对定位，避免撑开容器并向右外溢） */
.message-notification .badge :deep(.el-badge__content) {
  position: absolute;
  top: 0;
  right: 0;
  transform: translate(50%, -50%);
  font-size: 9px;
}

.message-center {
  width: 800px;
  height: calc(100vh - 61px);
  display: flex;
  flex-direction: column;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #ebeef5;
  background-color: #f5f7fa;
}

.message-header .message-title {
  font-weight: bold;
  font-size: 16px;
  color: var(--td-text-color-primary);
}

.message-header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.category-select {
  width: 120px;
}

.message-pagination {
  padding: 16px 20px;
  border-top: 1px solid #ebeef5;
  display: flex;
  justify-content: flex-end;
  background-color: #f5f7fa;
}

/* 消息列表交由 el-scrollbar 承担滚动，原生滚动条由组件隐藏；
   flex-basis 置 0 让列表独占「头部 + 分页」之外的剩余高度，头部与分页因此不被压缩 */
.message-list {
  flex: 1 1 0;
  min-height: 0;
}

.empty-message {
  text-align: center;
  padding: 40px 0;
  color: var(--td-text-color-placeholder);
}

.message-list-content {
  padding: 8px 0;
}

.message-item {
  position: relative;
  padding: 16px 20px;
  border-bottom: 1px solid #ebeef5;
  cursor: pointer;
  transition: background-color 0.3s;
}

.message-item:hover {
  background-color: #f5f7fa;
}

.message-item.unread {
  background-color: #ecf5ff;
}

/* 复制按钮默认隐藏，悬停消息条目时显示（绝对定位到右上角，与时间行对齐） */
.message-copy {
  position: absolute;
  top: 16px;
  right: 20px;
  font-size: 14px;
  color: var(--td-text-color-secondary);
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.2s, color 0.2s;
}

.message-item:hover .message-copy {
  opacity: 1;
}

.message-copy:hover {
  color: var(--td-text-color-brand);
}

.message-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.message-time {
  font-size: 12px;
  color: var(--td-text-color-placeholder);
}

.message-body {
  font-size: 14px;
  color: var(--td-text-color-secondary);
  line-height: 1.5;
}

.message-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 5px;
}
</style>
