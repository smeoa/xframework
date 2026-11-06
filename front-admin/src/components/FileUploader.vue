<template>
  <div
    class="file-uploader"
    ref="uploaderRef"
    @mouseenter="isHovering = true"
    @mouseleave="isHovering = false"
  >
    <div class="upload-zone" @click="triggerFileInput">
      <input
        ref="fileInputRef"
        type="file"
        :accept="accept"
        :multiple="maxCount !== 1"
        @change="handleFileChange"
        style="display: none"
      />
      <div class="upload-content">
        <el-icon class="upload-icon">
          <Plus />
        </el-icon>
        <span class="upload-text">点击或鼠标悬停 Ctrl+V 粘贴附件</span>
      </div>
    </div>

    <div class="file-list" v-if="fileList.length > 0">
      <div
        v-for="(file, index) in fileList"
        :key="file.uid || index"
        class="file-item"
        :class="{
          'is-uploading': file.uploading,
        }"
      >
        <FileIcon :file-type="file.fileType" :size="24" />
        <div class="file-info">
          <div
            class="file-name"
            :title="file.title || file.filename"
            @click="previewFile(file)"
          >
            {{ file.title || file.filename || "未命名" }}
          </div>
          <div class="file-meta">
            <span v-if="file.fileSize" class="file-size">{{
              formatFileSize(file.fileSize)
            }}</span>
            <el-progress
              v-if="file.uploading"
              :percentage="Number((file.percentage || 0).toFixed(1))"
              :stroke-width="3"
              :show-text="false"
              class="upload-progress"
            />
            <span v-else-if="file.fileType" class="file-type">{{
              getFileTypeLabel(file.fileType)
            }}</span>
          </div>
        </div>
        <div class="file-actions">
          <el-button
            type="primary"
            :icon="Download"
            size="small"
            text
            @click.stop="downloadFile(file)"
            :disabled="file.uploading"
          />
          <el-button
            type="danger"
            :icon="Delete"
            size="small"
            text
            @click.stop="deleteFile(index)"
            :disabled="file.uploading"
          />
        </div>
      </div>
    </div>

    <Transition name="fade">
      <div v-if="showPasteTip" class="paste-toast">
        <el-icon>
          <SuccessFilled />
        </el-icon>
        <span>检测到附件，正在上传...</span>
      </div>
    </Transition>

    <!-- 文件预览弹窗 -->
    <FilePreview
      v-model:visible="previewVisible"
      :url="previewFileUrl"
      :file-name="previewFileName"
      :file-size="previewFileSize"
      title="文件预览"
      :show-info="true"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from "vue";
import { Plus, Delete, Download, SuccessFilled } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import request from "@/utils/request";
import FileIcon from "@/components/FileIcon.vue";
import FilePreview from "@/components/FilePreview.vue";

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => [],
  },
  maxCount: {
    type: Number,
    default: 0,
  },
  showInfo: {
    type: Boolean,
    default: true,
  },
  pasteEnabled: {
    type: Boolean,
    default: true,
  },
  uploadApi: {
    type: String,
    default: "/admin/attachment/upload-attachment",
  },
  module: {
    type: String,
    default: "common",
  },
  accept: {
    type: String,
    default: "*",
  },
  maxSize: {
    type: Number,
    default: 50,
  },
});

const emit = defineEmits([
  "update:modelValue",
  "change",
  "upload-success",
  "upload-error",
]);

const fileList = ref([]);
const fileInputRef = ref(null);
const uploaderRef = ref(null);
const showPasteTip = ref(false);
const isHovering = ref(false);
const previewVisible = ref(false);
const previewFileUrl = ref("");
const previewFileName = ref("");
const previewFileSize = ref(0);

const getFileTypeLabel = (fileType) => {
  if (!fileType) return "";
  if (fileType.startsWith("image/")) return "图片";
  if (fileType.startsWith("video/")) return "视频";
  if (fileType.startsWith("audio/")) return "音频";
  if (fileType.includes("pdf")) return "PDF";
  if (fileType.includes("word") || fileType.includes("document")) return "Word";
  if (fileType.includes("excel") || fileType.includes("spreadsheet"))
    return "Excel";
  if (fileType.includes("powerpoint") || fileType.includes("presentation"))
    return "PPT";
  if (
    fileType.includes("zip") ||
    fileType.includes("rar") ||
    fileType.includes("tar")
  )
    return "压缩包";
  return fileType.split("/")[1]?.toUpperCase() || "文件";
};

watch(
  () => props.modelValue,
  (val) => {
    if (Array.isArray(val)) {
      const uploading = fileList.value.filter((file) => file.uploading);
      fileList.value = [...val, ...uploading];
    }
  },
  { immediate: true, deep: true },
);

const triggerFileInput = () => {
  fileInputRef.value?.click();
};

const handleFileChange = (e) => {
  const files = Array.from(e.target.files);
  if (files.length) {
    uploadFiles(files);
  }
  e.target.value = "";
};

const uploadFiles = async (files) => {
  const uploadingCount = fileList.value.filter((file) => file.uploading).length;

  if (props.maxCount > 0) {
    const remaining = props.maxCount - fileList.value.length + uploadingCount;

    if (remaining <= 0) {
      ElMessage.warning(`最多只能上传 ${props.maxCount} 个附件`);
      return;
    }

    if (files.length > remaining) {
      ElMessage.warning(`最多还能上传 ${remaining} 个附件`);
      files = files.slice(0, remaining);
    }
  }

  if (files.length === 0) return;

  await Promise.all(files.map((file) => uploadFile(file)));
};

const uploadFile = async (file) => {
  if (props.maxSize > 0 && file.size > props.maxSize * 1024 * 1024) {
    ElMessage.warning(`${file.name} 文件大小超过 ${props.maxSize}MB 限制`);
    return;
  }

  const uid = Date.now() + Math.random();

  const item = {
    uid,
    filename: file.name,
    title: file.name,
    file,
    uploading: true,
    percentage: 0,
  };

  fileList.value.push(item);

  try {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("module", props.module);

    const interval = setInterval(() => {
      const f = fileList.value.find((i) => i.uid === uid);
      if (f && f.percentage < 90) {
        f.percentage =
          Math.round((f.percentage + Math.random() * 15) * 10) / 10;
      }
    }, 300);

    const res = await request.post(props.uploadApi, formData, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 120000,
    });

    clearInterval(interval);

    if (res.code === 200) {
      const f = fileList.value.find((i) => i.uid === uid);
      if (f) {
        f.uid = res.data.id;
        f.id = res.data.id;
        f.storagePath = res.data.storagePath;
        f.filename = res.data.filename || file.name;
        f.title = res.data.title || file.name;
        f.fileSize = res.data.fileSize || file.size;
        f.fileType = res.data.fileType || file.type;
        f.uploading = false;
        f.percentage = 100;
      }
      emit("upload-success", res.data);
      updateModelValue();
    } else {
      throw new Error(res.message || "上传失败");
    }
  } catch (error) {
    console.error("上传失败:", error);
    ElMessage.error(error.message || "附件上传失败");

    const idx = fileList.value.findIndex((i) => i.uid === uid);
    if (idx !== -1) {
      fileList.value.splice(idx, 1);
    }

    emit("upload-error", error);
  }
};

const deleteFile = (index) => {
  fileList.value.splice(index, 1);
  updateModelValue();
  ElMessage.success("附件已删除");
};

const downloadFile = (file) => {
  if (file.storagePath) {
    window.open(file.storagePath, "_blank");
  } else if (file.url) {
    window.open(file.url, "_blank");
  }
};

const previewFile = (file) => {
  previewFileUrl.value = file.storagePath || file.url || "";
  previewFileName.value = file.filename || file.title || "文件";
  previewFileSize.value = file.fileSize || 0;
  previewVisible.value = true;
};

const updateModelValue = () => {
  const result = fileList.value
    .filter((file) => !file.uploading)
    .map((file, index) => ({
      uid: file.uid,
      id: file.id || file.uid,
      filename: file.filename,
      title: file.title,
      url: file.url,
      storagePath: file.storagePath,
      fileType: file.fileType,
      fileSize: file.fileSize,
      sortOrder: index,
    }));

  emit("update:modelValue", result);
  emit("change", result);
};

const formatFileSize = (bytes) => {
  if (!bytes) return "";
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
};

const handlePaste = async (e) => {
  if (!props.pasteEnabled || !isHovering.value) return;

  const items = e.clipboardData?.items;
  if (!items) return;

  const files = [];
  for (const item of items) {
    if (item.kind === "file") {
      const file = item.getAsFile();
      if (file) files.push(file);
    }
  }

  if (files.length > 0) {
    e.preventDefault();
    showPasteTip.value = true;
    setTimeout(() => {
      showPasteTip.value = false;
    }, 2500);
    ElMessage.info(`检测到 ${files.length} 个附件，正在上传...`);
    await uploadFiles(files);
  }
};

onMounted(() => {
  document.addEventListener("paste", handlePaste);
});

onUnmounted(() => {
  document.removeEventListener("paste", handlePaste);
});
</script>

<style scoped>
.file-uploader {
  width: 100%;
}

.upload-zone {
  position: relative;
  border: 1px dashed #dcdfe6;
  border-radius: 4px;
  height: 32px;
  line-height: 32px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #fafafa;
  display: flex;
  align-items: center;
  justify-content: center;
}

.upload-zone:hover {
  border-color: var(--brand-color);
  background: #ecf5ff;
  color: var(--td-text-color-brand);
}

.upload-content {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--td-text-color-placeholder);
}

.upload-icon {
  font-size: 12px;
  color: var(--td-text-color-brand);
}

.upload-text {
  font-weight: 500;
}

.file-list {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-item {
  display: flex;
  align-items: center;
  padding: 0px 12px;
  background: #fafafa;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.file-item:hover {
  background: #f5f7fa;
  border-color: #dcdfe6;
}

.file-item.is-uploading {
  background: #f0f9ff;
  border-color: var(--brand-color);
}

.file-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border-radius: 4px;
  color: var(--td-text-color-brand);
  margin-right: 12px;
  flex-shrink: 0;
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--td-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 28px;
  height: 28px;
  cursor: pointer;
}

.file-name:hover {
  color: var(--td-text-color-brand);
}

.file-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 0px;
  line-height: 20px;
}

.file-size {
  font-size: 12px;
  color: var(--td-text-color-placeholder);
}

.file-type {
  font-size: 12px;
  color: var(--td-text-color-disabled);
}

.upload-progress {
  flex: 1;
  max-width: 100px;
}

.file-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: 12px;
  flex-shrink: 0;
}

.file-actions .el-button {
  padding: 0;
  height: auto;
}

.paste-toast {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 24px;
  background: linear-gradient(135deg, #56c08d 0%, #2ba471 100%);
  color: var(--td-text-color-anti);
  border-radius: 30px;
  font-size: 14px;
  font-weight: 500;
  box-shadow: 0 8px 30px rgba(103, 194, 58, 0.4);
  z-index: 10000;
  backdrop-filter: blur(10px);
}

.fade-enter-active,
.fade-leave-active {
  transition: all 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-20px);
}

@media (max-width: 768px) {
  .file-item {
    padding: 8px 8px;
  }

  .file-icon {
    width: 32px;
    height: 32px;
    margin-right: 8px;
  }

  .file-actions {
    margin-left: 8px;
  }
}
</style>
