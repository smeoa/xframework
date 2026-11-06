<template>
  <el-card shadow="hover" class="api-card">
    <template #header>
      <div class="card-header">
        <span>API 密钥列表</span>
        <el-button type="primary" @click="handleCreateApiKey">
          <el-icon>
            <Plus />
          </el-icon>
          创建密钥
        </el-button>
      </div>
    </template>
    <el-scrollbar class="card-scrollbar">
      <div class="api-content">
        <el-table v-loading="loading" :data="apiKeys" style="width: 100%">
          <el-table-column
            prop="name"
            label="密钥名称"
            width="200"
            show-overflow-tooltip
          />
          <el-table-column prop="key" label="API 密钥" min-width="260">
            <template #default="scope">
              <span class="api-key">
                {{ scope.row.key.slice(0, 10) }}...{{
                  scope.row.key.slice(-10)
                }}
              </span>
              <el-link
                size="small"
                @click="showApiKey(scope.row)"
                style="margin-left: 8px"
              >
                查看
              </el-link>
            </template>
          </el-table-column>
          <el-table-column prop="createTime" label="创建时间" width="180">
            <template #default="scope">
              {{ formatDateTime(scope.row.createTime) }}
            </template>
          </el-table-column>
          <el-table-column prop="expireTime" label="过期时间" width="180">
            <template #default="scope">
              {{ formatDateTime(scope.row.expireTime) }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="90">
            <template #default="scope">
              <el-tag :type="scope.row.status === 1 ? 'success' : 'danger'">
                {{ scope.row.status === 1 ? "活跃" : "禁用" }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="110" fixed="right">
            <template #default="scope">
              <div class="row-actions">
                <el-link size="small" @click="toggleApiKeyStatus(scope.row)">
                  {{ scope.row.status === 1 ? "禁用" : "启用" }}
                </el-link>
                <el-link
                  size="small"
                  @click="deleteApiKey(scope.row)"
                  style="color: var(--td-error-color)"
                >
                  删除
                </el-link>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <div
          class="api-tip"
          style="
            margin-top: 20px;
            padding: 16px;
            background: #f0f9eb;
            border-radius: 4px;
          "
        >
          <el-icon class="tip-icon">
            <Warning />
          </el-icon>
          <span
            >API 密钥是访问系统 API
            的重要凭证，请妥善保管。创建后请立即复制密钥，关闭对话框后将无法再次查看完整密钥。</span
          >
        </div>
      </div>
    </el-scrollbar>
  </el-card>

  <!-- 创建API密钥对话框 -->
  <el-dialog v-model="createDialogVisible" title="创建 API 密钥" width="500px">
    <el-form :model="apiKeyForm" label-width="100px">
      <el-form-item label="密钥名称" required>
        <el-input v-model="apiKeyForm.name" placeholder="请输入密钥名称" />
      </el-form-item>
      <el-form-item label="过期时间" required>
        <el-date-picker
          v-model="apiKeyForm.expireTime"
          type="datetime"
          value-format="YYYY-MM-DD HH:mm:ss"
          placeholder="选择过期时间"
          style="width: 100%"
        />
      </el-form-item>
      <el-form-item label="描述">
        <el-input
          v-model="apiKeyForm.description"
          type="textarea"
          placeholder="请输入密钥描述"
          :rows="3"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmCreateApiKey">确定</el-button>
      </span>
    </template>
  </el-dialog>

  <!-- 查看API密钥对话框 -->
  <el-dialog v-model="viewDialogVisible" title="查看 API 密钥" width="500px">
    <div class="api-key-detail">
      <div class="detail-item">
        <span class="detail-label">密钥名称：</span>
        <span class="detail-value">{{ currentApiKey.name }}</span>
      </div>
      <div class="detail-item">
        <span class="detail-label">API 密钥：</span>
        <div class="key-display">
          <span class="key-value">{{ currentApiKey.key }}</span>
          <el-link size="small" @click="copyApiKey(currentApiKey.key)">
            <el-icon>
              <DocumentCopy />
            </el-icon>
            复制
          </el-link>
        </div>
      </div>
      <div class="detail-item">
        <span class="detail-label">创建时间：</span>
        <span class="detail-value">{{ formatDateTime(currentApiKey.createTime) }}</span>
      </div>
      <div class="detail-item">
        <span class="detail-label">过期时间：</span>
        <span class="detail-value">{{ formatDateTime(currentApiKey.expireTime) }}</span>
      </div>
      <div class="detail-item">
        <span class="detail-label">状态：</span>
        <el-tag :type="currentApiKey.status === 1 ? 'success' : 'danger'">
          {{ currentApiKey.status === 1 ? "活跃" : "禁用" }}
        </el-tag>
      </div>
    </div>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="viewDialogVisible = false">关闭</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { Plus, Warning, DocumentCopy } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import request from "@/utils/request";

const apiKeys = ref([]);
// 表格加载状态
const loading = ref(false);
const createDialogVisible = ref(false);
const viewDialogVisible = ref(false);
const apiKeyForm = ref({
  name: "",
  expireTime: "",
  description: "",
});
const currentApiKey = ref({});

onMounted(() => {
  loadApiKeys();
});

// 后端返回 ISO 时间（2026-09-18T10:00:00），展示时转为空格分隔的秒级格式
const formatDateTime = (value) => {
  if (!value) {
    return "-";
  }
  return String(value).replace("T", " ").slice(0, 19);
};

const loadApiKeys = async () => {
  loading.value = true;
  try {
    const response = await request.post("/admin/profile/get-api-keys");
    if (response.code === 200) {
      apiKeys.value = response.data || [];
    } else {
      ElMessage.error(response.message || "获取API密钥失败");
    }
  } catch (error) {
    console.error("获取API密钥失败:", error);
    ElMessage.error("获取API密钥失败");
  } finally {
    loading.value = false;
  }
};

const handleCreateApiKey = () => {
  apiKeyForm.value = {
    name: "",
    expireTime: "",
    description: "",
  };
  createDialogVisible.value = true;
};

const confirmCreateApiKey = async () => {
  if (!apiKeyForm.value.name) {
    ElMessage.error("请输入密钥名称");
    return;
  }

  if (!apiKeyForm.value.expireTime) {
    ElMessage.error("请选择过期时间");
    return;
  }

  try {
    const response = await request.post("/admin/profile/create-api-key", {
      data: apiKeyForm.value,
    });
    if (response.code === 200) {
      ElMessage.success("API密钥创建成功");
      createDialogVisible.value = false;
      // 显示新创建的密钥
      currentApiKey.value = response.data;
      viewDialogVisible.value = true;
      loadApiKeys();
    } else {
      ElMessage.error(response.message || "创建失败，请重试");
    }
  } catch (error) {
    console.error("创建API密钥失败:", error);
    ElMessage.error("创建失败，请重试");
  }
};

const showApiKey = (apiKey) => {
  currentApiKey.value = { ...apiKey };
  viewDialogVisible.value = true;
};

const toggleApiKeyStatus = async (apiKey) => {
  try {
    const response = await request.post(
      "/admin/profile/toggle-api-key-status",
      {
        id: apiKey.id,
        status: apiKey.status === 1 ? 0 : 1,
      },
    );
    if (response.code === 200) {
      ElMessage.success("状态更新成功");
      loadApiKeys();
    } else {
      ElMessage.error(response.message || "更新失败，请重试");
    }
  } catch (error) {
    console.error("更新API密钥状态失败:", error);
    ElMessage.error("更新失败，请重试");
  }
};

const deleteApiKey = async (apiKey) => {
  try {
    await ElMessageBox.confirm(
      `确定删除 API 密钥「${apiKey.name}」吗？删除后不可恢复。`,
      "删除确认",
      {
        type: "warning",
        confirmButtonText: "确定",
        cancelButtonText: "取消",
      },
    );
  } catch {
    // 用户取消删除
    return;
  }

  try {
    const response = await request.post("/admin/profile/delete-api-key", {
      id: apiKey.id,
    });
    if (response.code === 200) {
      ElMessage.success("API密钥删除成功");
      loadApiKeys();
    } else {
      ElMessage.error(response.message || "删除失败，请重试");
    }
  } catch (error) {
    console.error("删除API密钥失败:", error);
    ElMessage.error("删除失败，请重试");
  }
};

const copyApiKey = (key) => {
  navigator.clipboard
    .writeText(key)
    .then(() => {
      ElMessage.success("复制成功");
    })
    .catch(() => {
      ElMessage.error("复制失败");
    });
};
</script>

<style scoped>
.api-key-management {
  padding: 20px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 20px;
  color: var(--td-text-color-primary);
}

/* 卡片高度自适应父容器：纵向 flex 撑满，头部固定、主体滚动 */
.api-card {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
  margin-bottom: 0;
}

/* body 占满剩余高度，内容超出时在卡片内部出现滚动条 */
.api-card :deep(.el-card__body) {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* body 作为滚动区域外壳：占满剩余高度，内边距下移到滚动内容上，
   避免滚动条宽度占用内容盒（滚动条由 el-scrollbar 自绘） */
.api-card :deep(.el-card__body) {
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

/* 内边距已由滚动容器提供，此处不再叠加，使表格与卡片头部左对齐 */
.api-content {
  padding: 0;
}

.api-key {
  color: var(--td-text-color-secondary);
}

/* 操作列：链接之间留出间距，避免紧贴 */
.row-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.api-tip {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.tip-icon {
  color: var(--td-success-color);
  margin-top: 2px;
}

.api-key-detail {
  padding: 20px 0;
}

.detail-item {
  margin-bottom: 16px;
  display: flex;
  align-items: flex-start;
}

.detail-label {
  width: 100px;
  font-weight: 500;
  color: var(--td-text-color-secondary);
  flex-shrink: 0;
}

.detail-value {
  flex: 1;
  color: var(--td-text-color-primary);
}

.key-display {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
}

.key-value {
  color: var(--td-text-color-secondary);
  word-break: break-all;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
