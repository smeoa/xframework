<template>
  <div
    class="smart-uploader"
    ref="uploaderRef"
    @mouseenter="isHovering = true"
    @mouseleave="isHovering = false"
  >
    <!-- 主上传区域 -->
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
        <span class="upload-text">点击或鼠标悬停Ctrl+V 粘贴图片</span>
      </div>
    </div>

    <!-- 图片列表 -->
    <div class="image-grid" v-if="imageList.length > 0">
      <div
        v-for="(image, index) in imageList"
        :key="image.uid || index"
        class="image-card"
        :class="{
          'is-uploading': image.uploading,
          'is-primary': image.isPrimary && selectable,
        }"
        draggable="true"
        @dragstart="onDragStart($event, index)"
        @dragenter="onDragEnter($event, index)"
        @dragover="onDragOver"
        @dragend="onDragEnd"
      >
        <!-- 图片预览 -->
        <div class="image-preview" @click="openPreview(index)">
          <img
            v-if="image.url || image.storagePath"
            :src="image.url || image.storagePath"
            class="preview-img"
            loading="lazy"
          />
          <div v-else class="preview-placeholder">
            <el-icon class="placeholder-icon">
              <Picture />
            </el-icon>
          </div>

          <!-- 上传进度遮罩 -->
          <div v-if="image.uploading" class="upload-overlay">
            <el-progress
              type="circle"
              :percentage="Number((image.percentage || 0).toFixed(1))"
              :width="70"
              :stroke-width="6"
              :color="uploadProgressColor"
            >
              <template #default>
                <span class="progress-text"
                  >{{ Number((image.percentage || 0).toFixed(1)) }}%</span
                >
              </template>
            </el-progress>
          </div>
        </div>

        <!-- 图片信息 -->
        <div v-if="showInfo" class="image-info">
          <div class="info-row">
            <span class="info-name" :title="image.title || image.filename">
              {{ image.title || image.filename || "未命名" }}
            </span>
          </div>
          <div class="info-meta">
            <span v-if="image.fileSize" class="info-size">{{
              formatFileSize(image.fileSize)
            }}</span>
            <span v-if="image.isPrimary && selectable" class="info-primary"
              >主图</span
            >
            <el-button
              type="danger"
              :icon="Delete"
              size="small"
              text
              @click.stop="deleteImage(index)"
              class="delete-btn-inline"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 大图预览 -->
    <el-image-viewer
      v-if="showPreview"
      :url-list="previewImages"
      :initial-index="previewIndex"
      :hide-on-click-modal="false"
      @close="closePreview"
    />

    <!-- 粘贴提示 -->
    <Transition name="fade">
      <div v-if="showPasteTip" class="paste-toast">
        <el-icon>
          <SuccessFilled />
        </el-icon>
        <span>检测到图片，正在上传...</span>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from "vue";
import {
  Plus,
  Upload,
  Picture,
  Delete,
  View,
  FullScreen,
  Rank,
  Star,
  InfoFilled,
  DocumentCopy,
  SuccessFilled,
} from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import request from "@/utils/request";

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => [],
  },
  maxCount: {
    type: Number,
    default: 0,
  },
  selectable: {
    type: Boolean,
    default: true,
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
    default: "image/jpeg,image/png,image/gif,image/webp",
  },
  maxSize: {
    type: Number,
    default: 10,
  },
});

const emit = defineEmits([
  "update:modelValue",
  "change",
  "upload-success",
  "upload-error",
]);

const imageList = ref([]);
const fileInputRef = ref(null);
const uploaderRef = ref(null);
const showPreview = ref(false);
const previewIndex = ref(0);
const showPasteTip = ref(false);
const isHovering = ref(false);

const previewImages = computed(() => {
  return imageList.value
    .filter((img) => !img.uploading && (img.url || img.storagePath))
    .map((img) => img.url || img.storagePath);
});

const uploadProgressColor = computed(() => {
  return "var(--brand-color)";
});

watch(
  () => props.modelValue,
  (val) => {
    if (Array.isArray(val)) {
      const uploading = imageList.value.filter((img) => img.uploading);
      imageList.value = [...val, ...uploading];
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
  // 过滤正在上传的项目
  const uploadingCount = imageList.value.filter((img) => img.uploading).length;

  if (props.maxCount > 0) {
    const remaining = props.maxCount - imageList.value.length + uploadingCount;

    if (remaining <= 0) {
      ElMessage.warning(`最多只能上传 ${props.maxCount} 张图片`);
      return;
    }

    if (files.length > remaining) {
      ElMessage.warning(`最多还能上传 ${remaining} 张图片`);
      files = files.slice(0, remaining);
    }
  }

  if (files.length === 0) return;

  // 并行上传所有文件
  await Promise.all(files.map((file) => uploadFile(file)));
};

const uploadFile = async (file) => {
  if (!file.type.startsWith("image/")) {
    ElMessage.warning(`${file.name} 不是图片文件`);
    return;
  }

  if (file.size > props.maxSize * 1024 * 1024) {
    ElMessage.warning(`${file.name} 文件大小超过 ${props.maxSize}MB 限制`);
    return;
  }

  const uid = Date.now() + Math.random();
  const tempUrl = URL.createObjectURL(file);

  const item = {
    uid,
    filename: file.name,
    title: file.name,
    url: tempUrl,
    file,
    uploading: true,
    percentage: 0,
    isPrimary: imageList.value.filter((img) => !img.uploading).length === 0,
  };

  imageList.value.push(item);

  try {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("module", props.module);

    const interval = setInterval(() => {
      const img = imageList.value.find((i) => i.uid === uid);
      if (img && img.percentage < 90) {
        img.percentage =
          Math.round((img.percentage + Math.random() * 15) * 10) / 10;
      }
    }, 300);

    const res = await request.post(props.uploadApi, formData, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 60000,
    });

    clearInterval(interval);

    if (res.code === 200) {
      const img = imageList.value.find((i) => i.uid === uid);
      if (img) {
        img.uid = res.data.id;
        img.id = res.data.id;
        img.storagePath = res.data.storagePath;
        img.filename = res.data.filename || file.name;
        img.title = res.data.title || file.name;
        img.fileSize = res.data.fileSize || file.size;
        img.fileType = res.data.fileType || file.type;
        img.uploading = false;
        img.percentage = 100;
        URL.revokeObjectURL(tempUrl);
        img.url = res.data.storagePath;
      }
      emit("upload-success", res.data);
      updateModelValue();
    } else {
      throw new Error(res.message || "上传失败");
    }
  } catch (error) {
    console.error("上传失败:", error);
    ElMessage.error(error.message || "图片上传失败");

    const idx = imageList.value.findIndex((i) => i.uid === uid);
    if (idx !== -1) {
      URL.revokeObjectURL(tempUrl);
      imageList.value.splice(idx, 1);
    }

    emit("upload-error", error);
  }
};

const openPreview = (index) => {
  previewIndex.value = index;
  showPreview.value = true;
};

const closePreview = () => {
  showPreview.value = false;
};

const deleteImage = (index) => {
  const item = imageList.value[index];
  if (!item) return;

  // 释放对象 URL
  if (item.url?.startsWith("blob:")) {
    URL.revokeObjectURL(item.url);
  }

  // 如果删除的是主图，设置下一个为主图
  if (item.isPrimary && imageList.value.length > 1) {
    const nextIdx = index === 0 ? 1 : index - 1;
    if (imageList.value[nextIdx]) {
      imageList.value[nextIdx].isPrimary = true;
    }
  }

  // 直接删除
  imageList.value.splice(index, 1);
  updateModelValue();
  ElMessage.success("图片已删除");
};

const togglePrimary = (index) => {
  imageList.value.forEach((img, i) => {
    img.isPrimary = i === index;
  });
  updateModelValue();
  ElMessage.success(
    imageList.value[index]?.isPrimary ? "已设为主图" : "已取消主图",
  );
};

const updateModelValue = () => {
  const result = imageList.value
    .filter((img) => !img.uploading)
    .map((img, index) => ({
      uid: img.uid,
      id: img.id || img.uid,
      filename: img.filename,
      title: img.title,
      url: img.url,
      storagePath: img.storagePath,
      fileType: img.fileType,
      fileSize: img.fileSize,
      sortOrder: index,
      isPrimary: img.isPrimary || (props.selectable && index === 0),
    }));

  emit("update:modelValue", result);
  emit("change", result);
};

// 拖拽排序
let draggedIndex = -1;

const onDragStart = (e, index) => {
  draggedIndex = index;
  e.dataTransfer.effectAllowed = "move";
  e.dataTransfer.setData("text/plain", index.toString());

  // 延迟添加样式，让浏览器先处理拖动开始
  requestAnimationFrame(() => {
    e.target.classList.add("is-dragging");
  });
};

const onDragEnter = (e, index) => {
  e.preventDefault();
  if (draggedIndex === -1 || draggedIndex === index) return;

  const draggedItem = imageList.value[draggedIndex];
  if (!draggedItem) return;

  // 从原位置移除
  imageList.value.splice(draggedIndex, 1);
  // 插入到新位置
  imageList.value.splice(index, 0, draggedItem);

  // 更新拖动索引
  draggedIndex = index;
};

const onDragOver = (e) => {
  e.preventDefault();
  e.dataTransfer.dropEffect = "move";
};

const onDragEnd = (e) => {
  draggedIndex = -1;
  e.target.classList.remove("is-dragging");
  updateModelValue();
};

const formatFileSize = (bytes) => {
  if (!bytes) return "";
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
};

const handlePaste = async (e) => {
  // 只在鼠标悬停在组件上方时响应
  if (!props.pasteEnabled || !isHovering.value) return;

  const items = e.clipboardData?.items;
  if (!items) return;

  const imageFiles = [];
  for (const item of items) {
    if (item.type.startsWith("image/")) {
      const file = item.getAsFile();
      if (file) imageFiles.push(file);
    }
  }

  if (imageFiles.length > 0) {
    e.preventDefault();
    showPasteTip.value = true;
    setTimeout(() => {
      showPasteTip.value = false;
    }, 2500);
    ElMessage.info(`检测到 ${imageFiles.length} 张图片，正在上传...`);
    await uploadFiles(imageFiles);
  }
};

onMounted(() => {
  document.addEventListener("paste", handlePaste);
});

onUnmounted(() => {
  document.removeEventListener("paste", handlePaste);

  imageList.value.forEach((img) => {
    if (img.url?.startsWith("blob:")) {
      URL.revokeObjectURL(img.url);
    }
  });
});
</script>

<style scoped>
/* 基础容器 */
.smart-uploader {
  width: 100%;
}

/* 上传区域 */
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

.upload-zone:hover .upload-icon {
  color: var(--td-text-color-brand);
}

.upload-text {
  font-weight: 500;
}

/* 图片网格 */
.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 20px;
  margin-top: 24px;
}

/* 图片卡片 */
.image-card {
  position: relative;
  background: white;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  cursor: move;
}

.image-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.image-card.is-primary {
  border: 2px solid #ffba00;
}

.image-card.is-dragging {
  opacity: 0.5;
  transform: scale(0.95) rotate(2deg);
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.2);
  z-index: 100;
}

.image-card.is-dragging * {
  pointer-events: none;
}

/* 图片预览 */
.image-preview {
  position: relative;
  aspect-ratio: 1;
  overflow: hidden;
  background: linear-gradient(145deg, #f5f7fa 0%, #e4e7ed 100%);
  cursor: move;
  transition: all 0.3s ease;
}

.preview-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.preview-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
}

.placeholder-icon {
  font-size: 32px;
  color: var(--td-text-color-disabled);
}

/* 上传遮罩 */
.upload-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.9);
}

.progress-text {
  font-size: 12px;
  font-weight: 600;
  color: var(--td-text-color-brand);
  margin-top: 8px;
}

/* 图片信息 */
.image-info {
  padding: 6px 8px;
  border-top: 1px solid #f5f5f5;
}

.info-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 4px;
}

.info-name {
  flex: 1;
  margin: 0;
  font-size: 12px;
  font-weight: 500;
  color: var(--td-text-color-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.info-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--td-text-color-placeholder);
}

.info-meta .delete-btn-inline {
  margin-left: auto;
  padding: 0;
  height: auto;
}

.info-size {
  margin: 0;
}

.info-primary {
  color: #ffba00;
  font-weight: 500;
}

.info-meta .el-button {
  padding: 0;
  height: auto;
}

/* 粘贴提示 */
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

/* 动画 */
.fade-enter-active,
.fade-leave-active {
  transition: all 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-20px);
}

.list-enter-active,
.list-leave-active {
  transition: all 0.4s ease;
}

.list-enter-from {
  opacity: 0;
  transform: scale(0.8);
}

.list-leave-to {
  opacity: 0;
  transform: scale(0.8);
}

/* 响应式 */
@media (max-width: 768px) {
  .image-grid {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 16px;
  }

  .upload-zone {
    padding: 32px 16px;
  }

  .action-btn {
    width: 38px;
    height: 38px;
    font-size: 16px;
  }
}
</style>
