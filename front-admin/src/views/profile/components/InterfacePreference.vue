<template>
  <el-card shadow="hover" class="preference-card">
    <template #header>
      <div class="card-header">
        <span>界面设置</span>
      </div>
    </template>

    <el-scrollbar class="card-scrollbar">
      <div class="preference-content">
        <!-- 主题设置 -->
        <div class="preference-group">
          <h4 class="group-title">主题设置</h4>
          <el-divider />
          <div class="preference-item">
            <span class="preference-label">主题模式</span>
            <el-radio-group v-model="interfaceSettings.theme">
              <el-radio label="light">浅色</el-radio>
              <el-radio label="dark">深色</el-radio>
              <el-radio label="system">跟随系统</el-radio>
            </el-radio-group>
          </div>
          <div class="preference-item">
            <span class="preference-label">主题颜色</span>
            <el-color-picker
              v-model="interfaceSettings.themeColor"
              show-alpha
            />
          </div>
        </div>

        <!-- 布局设置 -->
        <div class="preference-group" style="margin-top: 32px">
          <h4 class="group-title">布局设置</h4>
          <el-divider />
          <div class="preference-item">
            <span class="preference-label">侧边栏宽度</span>
            <el-slider
              v-model="interfaceSettings.sidebarWidth"
              :min="200"
              :max="400"
              :step="10"
            />
            <span class="slider-value"
              >{{ interfaceSettings.sidebarWidth }}px</span
            >
          </div>
          <div class="preference-item">
            <span class="preference-label">布局模式</span>
            <el-select
              v-model="interfaceSettings.layoutMode"
              placeholder="选择布局模式"
            >
              <el-option label="经典布局" value="classic" />
              <el-option label="紧凑布局" value="compact" />
              <el-option label="全屏布局" value="fullscreen" />
            </el-select>
          </div>
        </div>

        <!-- 语言设置 -->
        <div class="preference-group" style="margin-top: 32px">
          <h4 class="group-title">语言设置</h4>
          <el-divider />
          <div class="preference-item">
            <span class="preference-label">界面语言</span>
            <el-select
              v-model="interfaceSettings.language"
              placeholder="选择语言"
            >
              <el-option label="简体中文" value="zh-CN" />
              <el-option label="English" value="en-US" />
            </el-select>
          </div>
        </div>

        <!-- 其他设置 -->
        <div class="preference-group" style="margin-top: 32px">
          <h4 class="group-title">其他设置</h4>
          <el-divider />
          <div class="preference-item">
            <span class="preference-label">显示面包屑</span>
            <el-switch v-model="interfaceSettings.showBreadcrumb" />
          </div>
          <div class="preference-item">
            <span class="preference-label">显示标签页</span>
            <el-switch v-model="interfaceSettings.showTabs" />
          </div>
          <div class="preference-item">
            <span class="preference-label">启用动画效果</span>
            <el-switch v-model="interfaceSettings.enableAnimation" />
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

const interfaceSettings = ref({
  theme: "light",
  themeColor: "#1f83ea",
  sidebarWidth: 240,
  layoutMode: "classic",
  language: "zh-CN",
  showBreadcrumb: true,
  showTabs: true,
  enableAnimation: true,
});

const defaultSettings = {
  theme: "light",
  themeColor: "#1f83ea",
  sidebarWidth: 240,
  layoutMode: "classic",
  language: "zh-CN",
  showBreadcrumb: true,
  showTabs: true,
  enableAnimation: true,
};

onMounted(() => {
  loadInterfaceSettings();
});

const loadInterfaceSettings = async () => {
  try {
    const response = await request.post(
      "/admin/profile/get-interface-settings",
    );
    if (response.code === 200) {
      interfaceSettings.value = response.data;
    }
  } catch (error) {
    console.error("获取界面设置失败:", error);
  }
};

const handleSave = async () => {
  try {
    const response = await request.post(
      "/admin/profile/update-interface-settings",
      {
        data: interfaceSettings.value,
      },
    );
    if (response.code === 200) {
      ElMessage.success("保存成功");
      // 应用新设置
      applySettings();
    }
  } catch (error) {
    console.error("保存界面设置失败:", error);
    ElMessage.error("保存失败，请重试");
  }
};

const handleReset = () => {
  interfaceSettings.value = { ...defaultSettings };
};

const applySettings = () => {
  // 这里可以添加应用设置的逻辑
  // 例如切换主题、语言等
  console.log("应用新设置:", interfaceSettings.value);
};
</script>

<style scoped>
.interface-preference {
  padding: 20px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 20px;
  color: var(--td-text-color-primary);
}

/* 卡片高度自适应父容器：纵向 flex 撑满，头部固定、主体滚动 */
.preference-card {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
  margin-bottom: 0;
}

/* body 作为滚动区域外壳：占满剩余高度，内边距下移到滚动内容上，
   避免滚动条宽度占用内容盒（滚动条由 el-scrollbar 自绘） */
.preference-card :deep(.el-card__body) {
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

.preference-content {
  padding: 20px;
}

.preference-group {
  margin-bottom: 20px;
}

.group-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--td-text-color-primary);
  margin-bottom: 8px;
}

.preference-item {
  display: flex;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.preference-item:last-child {
  border-bottom: none;
}

.preference-label {
  width: 120px;
  font-size: 14px;
  color: var(--td-text-color-secondary);
}

.slider-value {
  margin-left: 8px;
  font-size: 14px;
  color: var(--td-text-color-placeholder);
  min-width: 60px;
}

.action-buttons {
  display: flex;
  gap: 8px;
}
</style>
