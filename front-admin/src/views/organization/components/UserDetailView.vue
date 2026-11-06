<template>
  <!-- 详细信息弹窗 -->
  <el-dialog
    header="用户详细信息"
    v-model="dialogVisible"
    :title="`${currentRow?.username}`"
    :width="fullscreen ? '100%' : '1000px'"
    :fullscreen="fullscreen"
    :show-close="false"
    class="detail-dialog label-top"
  >
    <template #header>
      <span class="dialog-title">{{ currentRow?.username }}</span>
      <div class="dialog-header-actions">
        <el-button @click="toggleFullscreen" title="全屏" text>
          <el-icon>
            <FullScreen />
          </el-icon>
        </el-button>
        <el-button @click="switchDisplayMode('drawer')" title="切换为抽屉" text>
          <i class="iconfont x-youchouti"></i>
        </el-button>
        <el-button @click="handleClose" title="关闭" text>
          <el-icon>
            <Close />
          </el-icon>
        </el-button>
      </div>
    </template>
    <div class="dialog-body">
      <div class="detail-container">
        <div class="detail-actions">
          <el-button @click="emit('edit', currentRow)" text>
            <el-icon class="btn-icon">
              <Edit />
            </el-icon>
            编辑
          </el-button>
          <el-button @click="emit('delete', currentRow)" text>
            <el-icon class="btn-icon">
              <Delete />
            </el-icon>
            删除
          </el-button>
          <el-button @click="prevDetail" :disabled="currentIndex <= 0" text>
            <el-icon>
              <ArrowLeft />
            </el-icon>
          </el-button>
          <el-button
            @click="nextDetail"
            :disabled="currentIndex >= data.length - 1"
            text
          >
            <el-icon>
              <ArrowRight />
            </el-icon>
          </el-button>
        </div>
        <el-scrollbar class="detail-content">
          <el-form :model="currentRow" class="form-layout">
            <div class="form-row">
              <el-form-item label="用户名" prop="username" class="form-item w1">
                <el-input
                  v-model="currentRow.username"
                  placeholder="请输入用户名"
                  :value="currentRow.username || '-'"
                />
              </el-form-item>
              <el-form-item label="真实姓名" prop="name" class="form-item w1">
                <el-input
                  v-model="currentRow.name"
                  placeholder="请输入真实姓名"
                  :value="currentRow.name || '-'"
                />
              </el-form-item>
              <el-form-item label="手机号" prop="phone" class="form-item w1">
                <el-input
                  v-model="currentRow.phone"
                  placeholder="请输入手机号"
                  :value="currentRow.phone || '-'"
                />
              </el-form-item>
            </div>
            <div class="form-row">
              <el-form-item label="邮箱" prop="email" class="form-item w1">
                <el-input
                  v-model="currentRow.email"
                  placeholder="请输入邮箱"
                  :value="currentRow.email || '-'"
                />
              </el-form-item>
              <el-form-item label="部门" prop="deptId" class="form-item w1">
                <el-input
                  v-model="currentDeptNameValue"
                  placeholder="部门"
                  readonly
                />
              </el-form-item>
              <el-form-item label="头像" prop="avatar" class="form-item w1">
                <el-input
                  v-model="currentRow.avatar"
                  placeholder="请输入头像URL"
                  :value="currentRow.avatar || '-'"
                />
              </el-form-item>
              <el-form-item label="状态" prop="status" class="form-item w1">
                <el-switch
                  v-model="currentRow.status"
                  :active-value="1"
                  :inactive-value="0"
                  :value="currentRow.status || '-'"
                />
              </el-form-item>
            </div>
            <div class="form-row">
              <el-form-item
                label="最后登录时间"
                prop="lastLoginTime"
                class="form-item w1"
              >
                <el-input
                  v-model="currentRow.lastLoginTime"
                  placeholder="最后登录时间"
                  :value="currentRow.lastLoginTime || '-'"
                />
              </el-form-item>
              <el-form-item
                label="最后登录IP"
                prop="lastLoginIp"
                class="form-item w1"
              >
                <el-input
                  v-model="currentRow.lastLoginIp"
                  placeholder="最后登录IP"
                  :value="currentRow.lastLoginIp || '-'"
                />
              </el-form-item>
            </div>
            <div class="form-row">
              <el-form-item label="图片" prop="images" class="form-item w1">
                <div
                  class="detail-image-container"
                  v-if="currentRow.images && currentRow.images.length > 0"
                >
                  <el-image
                    v-for="(img, idx) in currentRow.images"
                    :key="img.id || idx"
                    :src="img.url || img.storagePath"
                    fit="cover"
                    class="detail-image-item"
                    @click="openImagePreview(idx)"
                  >
                    <template #placeholder>
                      <div class="image-placeholder">
                        <el-icon class="is-loading">
                          <Picture />
                        </el-icon>
                      </div>
                    </template>
                  </el-image>
                </div>
                <span v-else class="empty-text">无图片</span>
              </el-form-item>
              <el-form-item
                label="附件"
                prop="attachments"
                class="form-item w1"
              >
                <div
                  v-if="
                    currentRow.attachments && currentRow.attachments.length > 0
                  "
                  class="attachment-list"
                >
                  <div
                    v-for="(file, idx) in currentRow.attachments"
                    :key="file.id || idx"
                    class="attachment-item"
                  >
                    <div class="attachment-info" @click="openFilePreview(file)">
                      <FileIcon :file-type="file.fileType" :size="20" />
                      <span
                        class="attachment-name"
                        :title="file.filename || '附件'"
                      >
                        {{ file.filename || "附件" }}
                      </span>
                      <span v-if="file.fileSize" class="attachment-size">
                        {{ formatFileSize(file.fileSize) }}
                      </span>
                    </div>
                    <el-button
                      type="primary"
                      text
                      :icon="Download"
                      class="download-btn"
                      @click="downloadAttachment(file)"
                      title="下载"
                    />
                  </div>
                </div>
                <span v-else class="empty-text">无附件</span>
              </el-form-item>
            </div>
          </el-form>
        </el-scrollbar>
      </div>
    </div>
  </el-dialog>

  <!-- 详细信息抽屉 -->
  <el-drawer
    v-model="drawerVisible"
    header="用户详细信息"
    direction="rtl"
    :size="fullscreen ? '100%' : '1000px'"
    :show-close="false"
    class="user-detail-drawer label-top"
  >
    <template #header>
      <span class="dialog-title">{{ currentRow?.username }}</span>
      <div class="dialog-header-actions">
        <el-button @click="toggleFullscreen" title="全屏" text>
          <el-icon>
            <FullScreen />
          </el-icon>
        </el-button>
        <el-button @click="switchDisplayMode('dialog')" title="切换为弹窗" text>
          <i class="iconfont x-tanchuang"></i>
        </el-button>
        <el-button @click="handleClose" title="关闭" text>
          <el-icon>
            <Close />
          </el-icon>
        </el-button>
      </div>
    </template>
    <div class="drawer-body">
      <div class="detail-container">
        <div class="detail-actions">
          <el-button @click="emit('edit', currentRow)" text>
            <el-icon class="btn-icon">
              <Edit />
            </el-icon>
            编辑
          </el-button>
          <el-button @click="emit('delete', currentRow)" text>
            <el-icon class="btn-icon">
              <Delete />
            </el-icon>
            删除
          </el-button>
          <el-button @click="prevDetail" :disabled="currentIndex <= 0" text>
            <el-icon>
              <ArrowLeft />
            </el-icon>
          </el-button>
          <el-button
            @click="nextDetail"
            :disabled="currentIndex >= data.length - 1"
            text
          >
            <el-icon>
              <ArrowRight />
            </el-icon>
          </el-button>
        </div>
        <div class="detail-content">
          <el-form :model="currentRow" class="form-layout">
            <div class="form-row">
              <el-form-item label="用户名" prop="username" class="form-item">
                <el-input
                  v-model="currentRow.username"
                  placeholder="请输入用户名"
                  :value="currentRow.username || '-'"
                />
              </el-form-item>
              <el-form-item label="真实姓名" prop="name" class="form-item">
                <el-input
                  v-model="currentRow.name"
                  placeholder="请输入真实姓名"
                  :value="currentRow.name || '-'"
                />
              </el-form-item>
              <el-form-item label="手机号" prop="phone" class="form-item">
                <el-input
                  v-model="currentRow.phone"
                  placeholder="请输入手机号"
                  :value="currentRow.phone || '-'"
                />
              </el-form-item>
            </div>
            <div class="form-row">
              <el-form-item label="邮箱" prop="email" class="form-item">
                <el-input
                  v-model="currentRow.email"
                  placeholder="请输入邮箱"
                  :value="currentRow.email || '-'"
                />
              </el-form-item>
              <el-form-item label="部门" prop="deptId" class="form-item">
                <el-input
                  v-model="currentDeptNameValue"
                  placeholder="部门"
                  readonly
                />
              </el-form-item>
              <el-form-item label="头像" prop="avatar" class="form-item">
                <el-input
                  v-model="currentRow.avatar"
                  placeholder="请输入头像URL"
                  :value="currentRow.avatar || '-'"
                />
              </el-form-item>
              <el-form-item label="状态" prop="status" class="form-item">
                <el-switch
                  v-model="currentRow.status"
                  :active-value="1"
                  :inactive-value="0"
                  :value="currentRow.status || '-'"
                />
              </el-form-item>
            </div>
            <div class="form-row">
              <el-form-item
                label="最后登录时间"
                prop="lastLoginTime"
                class="form-item"
              >
                <el-input
                  v-model="currentRow.lastLoginTime"
                  placeholder="最后登录时间"
                  :value="currentRow.lastLoginTime || '-'"
                />
              </el-form-item>
              <el-form-item
                label="最后登录IP"
                prop="lastLoginIp"
                class="form-item"
              >
                <el-input
                  v-model="currentRow.lastLoginIp"
                  placeholder="最后登录IP"
                  :value="currentRow.lastLoginIp || '-'"
                />
              </el-form-item>
            </div>
            <div class="form-row">
              <el-form-item label="图片" prop="images" class="form-item w1">
                <div
                  class="detail-image-container"
                  v-if="currentRow.images && currentRow.images.length > 0"
                >
                  <el-image
                    v-for="(img, idx) in currentRow.images"
                    :key="img.id || idx"
                    :src="img.url || img.storagePath"
                    fit="cover"
                    class="detail-image-item"
                    @click="openImagePreview(idx)"
                  >
                    <template #placeholder>
                      <div class="image-placeholder">
                        <el-icon class="is-loading">
                          <Picture />
                        </el-icon>
                      </div>
                    </template>
                  </el-image>
                </div>
                <span v-else class="empty-text">无图片</span>
              </el-form-item>
              <el-form-item
                label="附件"
                prop="attachments"
                class="form-item w1"
              >
                <div
                  v-if="
                    currentRow.attachments && currentRow.attachments.length > 0
                  "
                  class="attachment-list"
                >
                  <div
                    v-for="(file, idx) in currentRow.attachments"
                    :key="file.id || idx"
                    class="attachment-item"
                  >
                    <div class="attachment-info" @click="openFilePreview(file)">
                      <FileIcon :file-type="file.fileType" :size="20" />
                      <span
                        class="attachment-name"
                        :title="file.filename || '附件'"
                      >
                        {{ file.filename || "附件" }}
                      </span>
                      <span v-if="file.fileSize" class="attachment-size">
                        {{ formatFileSize(file.fileSize) }}
                      </span>
                    </div>
                    <el-button
                      type="primary"
                      text
                      :icon="Download"
                      class="download-btn"
                      @click="downloadAttachment(file)"
                      title="下载"
                    />
                  </div>
                </div>
                <span v-else class="empty-text">无附件</span>
              </el-form-item>
            </div>
          </el-form>
        </div>
      </div>
    </div>
  </el-drawer>

  <!-- 通用文件预览组件 -->
  <FilePreview
    v-model:visible="filePreviewVisible"
    :url="previewFileUrl"
    :filename="previewFileName"
    :filesize="previewFileSize"
    :title="previewFileName"
    :show-info="true"
  />

  <!-- 独立图片查看器 -->
  <el-image-viewer
    v-if="showImageViewer"
    :url-list="previewImageList"
    :initial-index="previewImageIndex"
    :hide-on-click-modal="true"
    @close="showImageViewer = false"
  />
</template>

<script setup>
import { ref, computed, watch } from "vue";
import { ElMessage, ElImage, ElImageViewer } from "element-plus";
import {
  FullScreen,
  Edit,
  Delete,
  ArrowLeft,
  ArrowRight,
  Picture,
  Close,
  Download,
} from "@element-plus/icons-vue";
import FilePreview from "@/components/FilePreview.vue";
import FileIcon from "@/components/FileIcon.vue";
import { formatFileSize } from "@/utils/fileUtils";

const { visible, displayMode, currentRow, currentIndex, data } = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  displayMode: {
    type: String,
    default: "dialog",
    validator: (value) => ["dialog", "drawer"].includes(value),
  },
  currentRow: {
    type: Object,
    default: null,
  },
  currentIndex: {
    type: Number,
    default: -1,
  },
  data: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits([
  "update:visible",
  "update:displayMode",
  "update:currentRow",
  "update:currentIndex",
  "edit",
  "delete",
]);

const currentDeptNameValue = computed(() => {
  return currentRow?.deptName || currentRow?.dept_name || "-";
});

const dialogVisible = computed({
  get: () => visible && displayMode === "dialog",
  set: (value) => {
    if (!value && displayMode === "dialog") {
      emit("update:visible", false);
    }
  },
});

const drawerVisible = computed({
  get: () => visible && displayMode === "drawer",
  set: (value) => {
    if (!value && displayMode === "drawer") {
      emit("update:visible", false);
    }
  },
});

const fullscreen = ref(false);
const filePreviewVisible = ref(false);
const previewFileUrl = ref("");
const previewFileName = ref("");
const previewFileSize = ref(0);
const showImageViewer = ref(false);
const previewImageList = ref([]);
const previewImageIndex = ref(0);

const openImagePreview = (index) => {
  previewImageList.value = (currentRow?.images || []).map(
    (img) => img.url || img.storagePath,
  );
  previewImageIndex.value = index;
  showImageViewer.value = true;
};

const openFilePreview = (file) => {
  previewFileUrl.value = file.url || file.storagePath;
  previewFileName.value = file.filename || "附件";
  previewFileSize.value = file.fileSize || 0;
  filePreviewVisible.value = true;
};

// 切换全屏
const toggleFullscreen = () => {
  fullscreen.value = !fullscreen.value;
};

// 切换显示方式（弹窗/抽屉）
const switchDisplayMode = (mode) => {
  if (!visible) {
    emit("update:visible", true);
  }
  emit("update:displayMode", mode);
};

// 处理关闭
const handleClose = () => {
  emit("update:visible", false);
};

// 查看上一条
const prevDetail = () => {
  if (currentIndex > 0) {
    const newIndex = currentIndex - 1;
    emit("update:currentIndex", newIndex);
    emit("update:currentRow", data[newIndex]);
  } else {
    ElMessage.warning("已经是第一条");
  }
};

// 查看下一条
const nextDetail = () => {
  if (currentIndex < data.length - 1) {
    const newIndex = currentIndex + 1;
    emit("update:currentIndex", newIndex);
    emit("update:currentRow", data[newIndex]);
  } else {
    ElMessage.warning("已经是最后一条");
  }
};

// 下载附件
const downloadAttachment = (attachment) => {
  const url = attachment.url || attachment.storagePath;
  const filename = attachment.filename || attachment.name || "附件";
  if (url) {
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  } else {
    ElMessage.warning("附件链接不存在");
  }
};
</script>

<style scoped>
.dialog-title {
  font-size: 16px;
  line-height: 24px;
}

.dialog-header-actions {
  float: right;
}

.dialog-body {
  flex: 1;
  overflow-y: auto;
  padding: 0 0px;
}

.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 0 0px;
}

.btn-icon {
  margin-right: 4px;
}

.detail-actions {
  padding-left: 8px;
  margin-top: 5px;
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 0px;
  padding-bottom: 5px;
}

.detail-container {
  padding: 0px 0;
}

.detail-image-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.detail-image-item {
  width: 60px;
  height: 60px;
  cursor: pointer;
  transition: all 0.3s;
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid #dcdfe6;
  background-color: #f5f7fa;
}

.detail-image-item:hover {
  transform: scale(1.05);
  border-color: var(--brand-color);
}

.image-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  color: var(--td-text-color-disabled);
}

.attachment-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 4px 0;
}

.attachment-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 8px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background-color: #fafafa;
  transition: all 0.3s;
}

.attachment-item:hover {
  border-color: #c0c4cc;
  background-color: #f5f7fa;
}

.attachment-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
  cursor: pointer;
}

.attachment-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--td-text-color-secondary);
}

.attachment-name:hover {
  color: var(--td-text-color-brand);
}

.attachment-size {
  font-size: 12px;
  color: var(--td-text-color-placeholder);
  flex-shrink: 0;
}

.download-btn {
  flex-shrink: 0;
  padding: 4px 8px;
}

.empty-text {
  color: var(--td-text-color-placeholder);
  font-size: 14px;
}
</style>
