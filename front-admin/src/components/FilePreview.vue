<template>
  <el-dialog v-model="dialogVisible" :title="dialogTitle" width="100%" destroy-on-close :close-on-click-modal="false"
    :show-close="false" @closed="handleClosed" class="file-preview-dialog">
    <template #header>
      <span class="dialog-title">{{ dialogTitle }}</span>
      <div class="dialog-header-actions">
        <el-button type="primary" @click="downloadFile">
          <el-icon><Download /></el-icon> 下载
        </el-button>
        <el-button @click="handleClose" title="关闭" text>
          <el-icon><Close /></el-icon>
        </el-button>
      </div>
    </template>
    <div class="preview-container">
      <!-- 图片预览 -->
      <div v-if="isImage" class="preview-content image-preview">
        <div class="image-wrapper" v-if="!imageLoadError">
          <el-image ref="imageRef" :src="processedUrl" :initial-index="0" :preview-src-list="processedUrls"
            fit="contain" :hide-on-click-modal="true" :preview-teleported="false" :loading="imageLoading"
            style="width: 100%; height: 100%" @load="handleImageLoad" @error="handleImageError">
            <template #placeholder>
              <div class="image-placeholder">
                <el-icon class="is-loading">
                  <Loading />
                </el-icon>
                <span>加载中...</span>
              </div>
            </template>
            <template #error>
              <div class="image-error">
                <el-icon>
                  <PictureFilled />
                </el-icon>
                <span>图片加载失败</span>
                <el-button size="small" type="primary" @click="retryLoadImage">重新加载</el-button>
              </div>
            </template>
          </el-image>
        </div>
        <div v-else class="image-error-state">
          <el-icon :size="64">
            <PictureFilled />
          </el-icon>
          <p>图片加载失败</p>
          <p class="error-hint" v-if="errorMessage">{{ errorMessage }}</p>
          <div class="error-actions">
            <el-button type="primary" @click="retryLoadImage">重新加载</el-button>
            <el-button @click="openInNewTab">在新标签页打开</el-button>
          </div>
        </div>
      </div>

      <!-- 视频预览 -->
      <div v-else-if="isVideo" class="preview-content video-preview">
        <video ref="videoRef" :src="processedUrl" controls autoplay style="max-width: 100%; max-height: 70vh">
          您的浏览器不支持视频播放
        </video>
      </div>

      <!-- 音频预览 -->
      <div v-else-if="isAudio" class="preview-content audio-preview">
        <div class="audio-player">
          <div class="audio-icon">
            <el-icon :size="64">
              <Microphone />
            </el-icon>
          </div>
          <div class="audio-info">
            <p class="audio-filename">{{ displayFileName }}</p>
            <audio ref="audioRef" :src="processedUrl" controls style="width: 100%">
              您的浏览器不支持音频播放
            </audio>
          </div>
        </div>
      </div>

      <!-- PDF预览 -->
      <div v-else-if="isPdf" class="preview-content pdf-preview">
        <iframe :src="processedUrl" style="width: 100%; height: 70vh; border: none" @error="handlePdfError"></iframe>
      </div>

      <!-- Office文档预览 -->
      <div v-else-if="isOffice" class="preview-content office-preview">
        <div class="office-preview-content">
          <div class="office-icon">
            <el-icon :size="64">
              <Document v-if="fileType === 'doc' || fileType === 'docx'" />
              <Grid v-else-if="fileType === 'xls' || fileType === 'xlsx'" />
              <Files v-else />
            </el-icon>
          </div>
          <p class="office-filename">{{ displayFileName }}</p>
          <p class="office-hint">该文件类型不支持在线预览</p>
        </div>
      </div>

      <!-- 其他文件 -->
      <div v-else class="preview-content other-preview">
        <div class="other-preview-content">
          <el-icon :size="64" style="color: var(--td-text-color-placeholder)">
            <Files />
          </el-icon>
          <p class="other-filename">{{ displayFileName }}</p>
          <p class="other-hint">该文件类型不支持在线预览</p>
        </div>
      </div>

      <!-- 预览信息 -->
      <div v-if="showInfo && isImage" class="preview-info">
        <div class="info-left">
          <span class="file-name" :title="displayFileName">{{
            displayFileName
            }}</span>
          <span v-if="imageLoadSuccess" class="image-dimensions">{{ imageInfo.naturalWidth }} × {{
            imageInfo.naturalHeight
            }}</span>
        </div>
        <div class="info-right">
          <span class="file-size">{{ formattedFileSize }}</span>
          <el-button size="small" type="primary" text @click="handleZoomIn">
            <el-icon>
              <ZoomIn />
            </el-icon>
          </el-button>
          <el-button size="small" type="primary" text @click="handleZoomOut">
            <el-icon>
              <ZoomOut />
            </el-icon>
          </el-button>
          <el-button size="small" type="primary" text @click="handleRotate">
            <el-icon>
              <RefreshRight />
            </el-icon>
          </el-button>
        </div>
      </div>
    </div>

  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import {
  Download,
  Document,
  Grid,
  Files,
  Microphone,
  PictureFilled,
  Loading,
  ZoomIn,
  ZoomOut,
  RefreshRight,
  Close,
} from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import {
  cleanUrl,
  downloadFile as utilDownloadFile,
  openInNewTab as utilOpenInNewTab,
  formatFileSize,
  getFileNameFromUrl,
  getFileExtension,
  isImage as checkIsImage,
  isVideo as checkIsVideo,
  isAudio as checkIsAudio,
  isPdf as checkIsPdf,
  isOffice as checkIsOffice,
  removeUuidFromFilename,
} from "@/utils/fileUtils";

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  url: {
    type: String,
    default: "",
  },
  urls: {
    type: Array,
    default: () => [],
  },
  fileName: {
    type: String,
    default: "",
  },
  fileSize: {
    type: [Number, String],
    default: 0,
  },
  title: {
    type: String,
    default: "文件预览",
  },
  showInfo: {
    type: Boolean,
    default: true,
  },
});

const emit = defineEmits(["update:visible", "closed"]);

const dialogVisible = ref(false);
const imageRef = ref(null);
const videoRef = ref(null);
const audioRef = ref(null);
const imageLoading = ref(false);
const imageLoadError = ref(false);
const imageLoadSuccess = ref(false);
const errorMessage = ref("");
const imageInfo = ref({ naturalWidth: 0, naturalHeight: 0 });

// 监听 visible 变化
watch(
  () => props.visible,
  (val) => {
    dialogVisible.value = val;
    if (val) {
      imageLoadError.value = false;
      imageLoadSuccess.value = false;
      errorMessage.value = "";
      imageInfo.value = { naturalWidth: 0, naturalHeight: 0 };
      setTimeout(() => {
        if (videoRef.value) {
          videoRef.value.currentTime = 0;
        }
        if (audioRef.value) {
          audioRef.value.currentTime = 0;
        }
      }, 100);
    }
  },
  { immediate: true },
);

watch(dialogVisible, (val) => {
  emit("update:visible", val);
});

const dialogTitle = computed(() => {
  if (props.fileName) {
    // 去掉文件名中的 UUID 和查询参数部分
    return removeUuidFromFilename(props.fileName);
  }
  return "文件预览";
});



// 处理 URL，确保正确编码
const processUrl = (url) => cleanUrl(url);

const processedUrl = computed(() => {
  return cleanUrl(props.url);
});

const processedUrls = computed(() => {
  if (props.urls && props.urls.length > 0) {
    return props.urls.map((url) => cleanUrl(url));
  }
  if (props.url) {
    return [cleanUrl(props.url)];
  }
  return [];
});

const fileType = computed(() => {
  const ext = getFileExtension(props.fileName) || getFileExtension(props.url);
  return ext.toLowerCase();
});

const isImage = computed(() => checkIsImage(props.fileName || props.url));
const isVideo = computed(() => checkIsVideo(props.fileName || props.url));
const isAudio = computed(() => checkIsAudio(props.fileName || props.url));
const isPdf = computed(() => checkIsPdf(props.fileName || props.url));
const isOffice = computed(() => checkIsOffice(props.fileName || props.url));

// 显示文件名（处理编码问题并去掉UUID）
const displayFileName = computed(() => {
  let filename = "";

  // 优先使用 fileName，如果存在则处理
  if (props.fileName) {
    filename = props.fileName;
  } else if (props.url) {
    // 从 URL 中提取文件名
    filename = getFileNameFromUrl(props.url) || "未知文件";
  } else {
    filename = "未知文件";
  }

  // 去掉文件名中的 UUID 和查询参数部分
  return removeUuidFromFilename(filename);
});

// 格式化文件大小
const formattedFileSize = computed(() => {
  return formatFileSize(props.fileSize);
});

// 图片加载成功
const handleImageLoad = (event) => {
  imageLoadError.value = false;
  imageLoadSuccess.value = true;
  imageLoading.value = false;

  // 获取图片尺寸
  if (event && event.target) {
    imageInfo.value = {
      naturalWidth: event.target.naturalWidth || 0,
      naturalHeight: event.target.naturalHeight || 0,
    };
  }
};

// 图片加载失败
const handleImageError = (error) => {
  imageLoadError.value = true;
  imageLoading.value = false;
  imageLoadSuccess.value = false;

  // 提取错误信息
  if (error && error.target && error.target.error) {
    switch (error.target.error.code) {
      case 1:
        errorMessage.value = "图片不存在";
        break;
      case 2:
        errorMessage.value = "图片加载超时";
        break;
      case 3:
        errorMessage.value = "图片格式不正确";
        break;
      case 4:
        errorMessage.value = "图片解码失败";
        break;
      default:
        errorMessage.value = "图片加载失败";
    }
  } else {
    errorMessage.value = "图片加载失败";
  }
};

// 重新加载图片
const retryLoadImage = () => {
  imageLoadError.value = false;
  imageLoading.value = true;
  errorMessage.value = "";

  // 强制重新加载图片
  if (imageRef.value) {
    imageRef.value.$el.querySelector("img")?.removeAttribute("src");
    setTimeout(() => {
      imageRef.value.$el
        .querySelector("img")
        ?.setAttribute("src", processedUrl.value);
    }, 100);
  }
};

// 在新标签页打开
const openInNewTab = () => {
  utilOpenInNewTab(props.url);
};

// PDF加载错误
const handlePdfError = () => {
  errorMessage.value = "PDF加载失败";
};

// 缩放
const handleZoomIn = () => {
  if (imageRef.value) {
    const imgEl = imageRef.value.$el.querySelector(".el-image__inner");
    if (imgEl) {
      const currentTransform = imgEl.style.transform || "";
      imgEl.style.transform =
        currentTransform.replace(/scale\([^)]*\)/, "") + " scale(1.2)";
    }
  }
};

const handleZoomOut = () => {
  if (imageRef.value) {
    const imgEl = imageRef.value.$el.querySelector(".el-image__inner");
    if (imgEl) {
      const currentTransform = imgEl.style.transform || "";
      imgEl.style.transform =
        currentTransform.replace(/scale\([^)]*\)/, "") + " scale(0.8)";
    }
  }
};

// 旋转
const handleRotate = () => {
  if (imageRef.value) {
    const imgEl = imageRef.value.$el.querySelector(".el-image__inner");
    if (imgEl) {
      const currentTransform = imgEl.style.transform || "";
      // 移除现有的旋转
      const withoutRotate = currentTransform.replace(/rotate\([^)]*\)/g, "");
      imgEl.style.transform = withoutRotate + " rotate(90deg)";
    }
  }
};

// 下载文件
const downloadFile = () => {
  if (!props.url) {
    ElMessage.warning("文件链接不存在");
    return;
  }
  utilDownloadFile(props.url, props.fileName);
};

// 点击关闭按钮
const handleClose = () => {
  dialogVisible.value = false;
};

// 处理对话框关闭
const handleClosed = () => {
  if (videoRef.value) {
    videoRef.value.pause();
  }
  if (audioRef.value) {
    audioRef.value.pause();
  }
  emit("closed");
};

// 暴露方法供父组件调用
defineExpose({
  downloadFile,
  retryLoadImage,
  openInNewTab,
});
</script>

<style scoped>
.dialog-title {
  font-size: 16px;
  line-height: 24px;
}

.dialog-header-actions {
  gap: 8px;
  float: right;
}

/* 确保对话框在遮罩之上 */
.file-preview-dialog {
  z-index: 2600 !important;
}

/* 覆盖 Element Plus 组件库的 z-index */
.file-preview-dialog :deep(.el-dialog) {
  z-index: 2600 !important;
}

.file-preview-dialog :deep(.el-overlay) {
  z-index: 2599 !important;
}

/* Element Plus 图片查看器样式覆盖 */
.file-preview-dialog :deep(.el-image-viewer__wrapper) {
  z-index: 3000 !important;
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
}

.file-preview-dialog :deep(.el-image-viewer__mask) {
  z-index: 2999 !important;
  position: fixed !important;
  background-color: rgba(0, 0, 0, 0.9) !important;
}

.file-preview-dialog :deep(.el-image-viewer__canvas) {
  z-index: 3001 !important;
  position: relative !important;
}

.file-preview-dialog :deep(.el-image-viewer__img) {
  z-index: 3002 !important;
  position: relative !important;
}

.preview-container {
  display: flex;
  flex-direction: column;
  min-height: 400px;
}

.preview-content {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

/* 图片预览 */
.image-preview {
  background-color: #f5f5f5;
  position: relative;
  z-index: 2500;
}

/* 确保 el-image viewer 在遮罩之上 */
.image-preview :deep(.el-image__viewer-wrapper) {
  z-index: 3000 !important;
}

.image-preview :deep(.el-image-viewer__wrapper) {
  z-index: 3000 !important;
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
}

.image-preview :deep(.el-image-viewer__mask) {
  z-index: 2999 !important;
  position: fixed !important;
}

.image-preview :deep(.el-image-viewer__canvas) {
  z-index: 3001 !important;
  position: relative !important;
}

.image-preview :deep(.el-image-viewer__img) {
  z-index: 3002 !important;
  position: relative !important;
}

/* Element Plus 图片查看器按钮 */
.image-preview :deep(.el-image-viewer__btn) {
  z-index: 3003 !important;
  position: relative !important;
}

.image-preview :deep(.el-image-viewer__close) {
  z-index: 3003 !important;
  position: relative !important;
}

.image-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--td-text-color-placeholder);
}

.image-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: var(--td-text-color-placeholder);
  padding: 40px;
}

.image-error .el-icon {
  font-size: 64px;
}

.image-error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: var(--td-text-color-placeholder);
  padding: 60px 20px;
}

.image-error-state .el-icon {
  color: var(--td-error-color);
}

.image-error-state .error-hint {
  font-size: 12px;
  color: var(--td-text-color-disabled);
  margin: 0;
}

.image-error-state .error-actions {
  display: flex;
  gap: 8px;
}

/* 预览信息栏 */
.preview-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background-color: #f5f7fa;
  border-top: 1px solid #e4e7ed;
  margin-top: 8px;
  border-radius: 4px;
}

.info-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: 14px;
  color: var(--td-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 300px;
}

.image-dimensions {
  font-size: 12px;
  color: var(--td-text-color-placeholder);
  flex-shrink: 0;
}

.info-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-size {
  font-size: 12px;
  color: var(--td-text-color-placeholder);
}

/* 视频预览 */
.video-preview {
  background-color: #000;
  padding: 20px;
}

.video-preview video {
  background-color: #000;
  border-radius: 8px;
}

/* 音频预览 */
.audio-preview {
  background-color: #fafafa;
  padding: 40px;
}

.audio-player {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  max-width: 500px;
  width: 100%;
}

.audio-icon {
  color: var(--td-text-color-brand);
}

.audio-info {
  width: 100%;
  text-align: center;
}

.audio-filename {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: var(--td-text-color-primary);
  word-break: break-all;
}

/* PDF预览 */
.pdf-preview {
  background-color: #f5f5f5;
  padding: 8px;
}

/* Office文档预览 */
.office-preview {
  background-color: #fafafa;
  padding: 60px 20px;
}

.office-preview-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.office-icon {
  color: var(--td-text-color-brand);
}

.office-filename {
  margin: 0;
  font-size: 16px;
  color: var(--td-text-color-primary);
  word-break: break-all;
}

.office-hint {
  margin: 0;
  font-size: 14px;
  color: var(--td-text-color-placeholder);
}

/* 其他文件 */
.other-preview {
  background-color: #fafafa;
  padding: 60px 20px;
}

.other-preview-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.other-filename {
  margin: 0;
  font-size: 16px;
  color: var(--td-text-color-primary);
  word-break: break-all;
}

.other-hint {
  margin: 0;
  font-size: 14px;
  color: var(--td-text-color-placeholder);
}
</style>
