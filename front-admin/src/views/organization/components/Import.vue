<template>
  <!-- 导入弹窗 -->
  <el-dialog
    header="用户导入"
    v-model="dialogVisible"
    :title="dialogTitle"
    :width="fullscreen ? '100%' : '1000px'"
    :fullscreen="fullscreen"
    :show-close="false"
    class="import-dialog"
  >
    <template #header>
      <span class="dialog-title">{{ dialogTitle }}</span>
      <div class="dialog-header-actions">
        <el-button @click="toggleFullscreen" title="全屏" text>
          <el-icon>
            <FullScreen />
          </el-icon>
        </el-button>
        <el-button @click="handleCancel" title="关闭" text>
          <el-icon>
            <Close />
          </el-icon>
        </el-button>
      </div>
    </template>
    <!-- 步骤指示器 -->
    <el-steps :active="currentStep" finish-status="success">
      <el-step title="选择Excel" />
      <el-step title="预览数据" />
      <el-step title="配置表单" />
      <el-step title="导入数据" />
    </el-steps>

    <!-- 第一步：选择Excel -->
    <div v-if="currentStep === 0" class="content-section">
      <div class="import-mode-container">
        <el-form label-width="80px" class="import-mode-form">
          <el-form-item label="导入模式" class="import-mode-item">
            <el-select
              v-model="importMode"
              placeholder="请选择导入模式"
              class="import-mode-select"
            >
              <el-option label="仅新增数据" value="insert" />
              <el-option label="仅更新数据" value="update" />
              <el-option label="更新和新增数据" value="insert_update" />
            </el-select>
          </el-form-item>

          <el-form-item class="download-template-item" label-width="0px">
            <el-button
              link
              type="primary"
              @click="downloadTemplate"
              :icon="Download"
            >
              下载导入模板
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <div
        class="upload-area"
        @dragover.prevent
        @drop.prevent="handleDrop"
        @click="triggerFileInput"
        :class="{ dragover: isDragover }"
      >
        <input
          ref="fileInput"
          type="file"
          accept=".xlsx,.xls"
          class="file-input-hidden"
          @change="handleFileChange"
        />
        <div class="upload-content">
          <el-icon class="upload-icon">
            <UploadFilled />
          </el-icon>
          <p>将文件拖拽到区域，或点击添加</p>
          <p class="tip">
            支持 .xlsx 格式文件，行数不超过10万行，列数不超过500列
          </p>
          <p class="tip">推荐使用标准模板</p>
        </div>
        <div v-if="selectedFile" class="file-info">
          <el-icon>
            <Document />
          </el-icon>
          <span>{{ selectedFile.name }}</span>
          <el-button
            link
            size="small"
            @click="clearFile"
            :disabled="isPreviewing"
            >移除</el-button
          >
          <el-button link size="small" v-if="isPreviewing" disabled>
            <el-icon class="is-loading"
              ><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024">
                <path
                  fill="currentColor"
                  d="M988 548c-19.9 0-36-16.1-36-36 0-59.4-11.6-116.4-33.6-168.6-22.1-52.2-53.7-99.8-94.4-138.6-40.8-38.8-91.3-72.8-148.7-98.8-57.4-26-121.3-40.6-185-40.6-63.6 0-127.3 14.6-185 40.6-57.4 26-107.9 60-148.7 98.8-40.8 38.8-72.3 86.4-94.4 138.6-22 52.2-33.6 109.2-33.6 168.6 0 20 16.1 36 36 36s36-16.1 36-36c0-53.2 10.8-103.5 30.5-149.6 19.7-46.1 46.2-86.9 78.8-120.9 32.6-34 69.9-62.3 111.4-84 41.5-21.7 87-33 135.5-33s94 11.3 135.5 33c41.5 21.7 78.8 49.9 111.4 84 32.6 34 59.1 74.8 78.8 120.9C949.2 444.5 960 494.8 960 548c0 20 16.1 36 36 36s36-16.1 36-36c0-19.9-16.1-36-36-36z"
                ></path></svg
            ></el-icon>
            解析中...
          </el-button>
        </div>
      </div>
    </div>

    <!-- 第二步：预览数据 -->
    <div v-if="currentStep === 1" class="content-section">
      <div class="preview-container">
        <el-alert title="数据预览" type="info" :closable="false" show-icon />
        <el-table
          v-loading="isPreviewing"
          :data="previewData"
          class="preview-table"
          border
          max-height="420px"
        >
          <el-table-column
            v-for="(column, index) in previewColumns"
            :key="index"
            :prop="column?.prop || ''"
            :label="column?.label || ''"
            width="120"
          />
        </el-table>
        <div v-if="previewData.length === 0" class="empty-preview">
          <el-empty description="暂无数据预览" />
        </div>
      </div>
    </div>

    <!-- 第三步：配置表单 -->
    <div v-if="currentStep === 2" class="content-section">
      <div class="config-container">
        <el-alert
          title="字段映射配置"
          type="info"
          :closable="false"
          show-icon
        />
        <el-form
          :model="fieldMapping"
          label-width="120px"
          class="field-mapping-form"
        >
          <el-form-item
            v-for="field in organizationUserFields"
            :key="field.prop"
            :label="field.label"
          >
            <el-select
              v-model="fieldMapping[field.prop]"
              placeholder="请选择对应列"
              class="field-mapping-select"
            >
              <el-option value="" label="不导入" />
              <el-option
                v-for="(column, index) in previewColumns"
                :key="index"
                :value="column?.prop || ''"
                :label="column?.label || ''"
              />
            </el-select>
          </el-form-item>
        </el-form>
      </div>
    </div>
    <!-- 第四步：导入数据 -->
    <div v-if="currentStep === 3" class="content-section">
      <div class="import-container">
        <el-alert title="导入进度" type="success" :closable="false" show-icon />
        <div v-if="!importComplete" class="progress-container">
          <el-progress :percentage="importProgress" :status="importStatus" />
          <p class="progress-text">{{ importMessage }}</p>
        </div>
        <div v-else class="import-result">
          <el-result
            :icon="importSuccess ? 'success' : 'error'"
            :title="importSuccess ? '导入成功' : '导入失败'"
            :sub-title="
              importSuccess
                ? `共处理 ${importStats.total} 条数据，成功 ${importStats.success} 条，失败 ${importStats.failure} 条`
                : '导入过程中出现错误，请检查文件格式或网络连接'
            "
          >
            <template #extra>
              <div v-if="importSuccess" class="success-info">
                <el-card shadow="hover" class="result-card">
                  <template #header>
                    <div class="card-header">
                      <span>导入结果详情</span>
                    </div>
                  </template>
                  <div class="result-details">
                    <div class="result-item">
                      <span class="label">总数据量:</span>
                      <span class="value">{{ importStats.total }}</span>
                    </div>
                    <div class="result-item">
                      <span class="label">成功导入:</span>
                      <span class="value success">{{
                        importStats.success
                      }}</span>
                    </div>
                    <div class="result-item">
                      <span class="label">导入失败:</span>
                      <span class="value error">{{ importStats.failure }}</span>
                    </div>
                    <div class="result-item" v-if="importStats.success > 0">
                      <span class="label">成功率:</span>
                      <span class="value"
                        >{{
                          Math.round(
                            (importStats.success / importStats.total) * 100,
                          )
                        }}%</span
                      >
                    </div>
                    <div class="result-item" v-if="importStats.message">
                      <span class="label">提示:</span>
                      <span class="value">{{ importStats.message }}</span>
                    </div>
                    <div
                      v-if="importStats.errors && importStats.errors.length > 0"
                      class="error-list"
                    >
                      <div class="error-title">
                        <span>错误详情:</span>
                        <el-button
                          link
                          type="danger"
                          @click="exportErrorDetails"
                          :icon="Download"
                          class="export-error-btn"
                        >
                          导出错误信息
                        </el-button>
                      </div>
                      <el-collapse>
                        <el-collapse-item
                          v-for="(error, index) in importStats.errors"
                          :key="index"
                          :title="`第 ${error.row} 行: ${error.message}`"
                        >
                          <div class="error-detail">
                            <div class="error-data">
                              数据: {{ JSON.stringify(error.data) }}
                            </div>
                          </div>
                        </el-collapse-item>
                      </el-collapse>
                    </div>
                  </div>
                </el-card>
              </div>
              <div v-else class="error-info">
                <el-card shadow="hover" class="result-card">
                  <template #header>
                    <div class="card-header">
                      <span>导入失败原因</span>
                    </div>
                  </template>
                  <div class="error-details">
                    <p>{{ importMessage }}</p>
                    <p>请检查文件格式是否正确，网络连接是否正常后重试</p>
                  </div>
                </el-card>
              </div>
            </template>
          </el-result>
        </div>
      </div>
    </div>
    <template #footer>
      <div v-if="currentStep === 0">
        <el-button
          type="primary"
          @click="nextStep"
          :disabled="!selectedFile || isPreviewing"
          >下一步</el-button
        >
        <el-button @click="handleCancel" :disabled="isPreviewing"
          >取消</el-button
        >
      </div>
      <div v-else-if="currentStep === 1">
        <el-button @click="prevStep">上一步</el-button>
        <el-button
          type="primary"
          @click="nextStep"
          :disabled="previewData.length === 0 || !selectedFile"
          >下一步</el-button
        >
      </div>
      <div v-else-if="currentStep === 2">
        <el-button @click="prevStep">上一步</el-button>
        <el-button type="primary" @click="nextStep">下一步</el-button>
      </div>
      <div v-else-if="currentStep === 3">
        <el-button v-if="!importComplete" @click="cancelImport"
          >取消导入</el-button
        >
        <el-button v-else @click="handleCancel">完成</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from "vue";
import { ElMessage } from "element-plus";
import {
  UploadFilled,
  Document,
  FullScreen,
  Close,
  Download,
} from "@element-plus/icons-vue";
import request from "@/utils/request";

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["update:visible", "import-success"]);

const dialogTitle = computed(() => "导入用户");

const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit("update:visible", value),
});

// 导入步骤
const currentStep = ref(0);
const fullscreen = ref(false);

// 导入模式
const importMode = ref("insert");

// 文件相关
const fileInput = ref(null);
const selectedFile = ref(null);
const isDragover = ref(false);
const isPreviewing = ref(false);

// 预览数据
const previewData = ref([]);
const previewColumns = ref([]);

// 字段映射
const fieldMapping = ref({});

// 导入进度
const importProgress = ref(0);
const importMessage = ref("准备导入...");
const importStatus = ref("");
const importComplete = ref(false);
const importSuccess = ref(false);
const importStats = ref({
  success: 0,
  failure: 0,
  total: 0,
});

// 组织用户字段
const organizationUserFields = [
  { prop: "username", label: "用户名" },
  { prop: "password", label: "密码" },
  { prop: "name", label: "真实姓名" },
  { prop: "phone", label: "手机号" },
  { prop: "email", label: "邮箱" },
  { prop: "avatar", label: "头像" },
  { prop: "status", label: "状态" },
  { prop: "deptId", label: "部门ID" },
];

// 触发文件选择
const triggerFileInput = () => {
  fileInput.value?.click();
};

// 处理文件拖拽
const handleDrop = (e) => {
  isDragover.value = false;
  const files = e.dataTransfer.files;
  if (files.length > 0) {
    handleFile(files[0]);
  }
};

// 处理文件选择
const handleFileChange = (e) => {
  const files = e.target.files;
  if (files.length > 0) {
    handleFile(files[0]);
  }
};

// 处理文件
const handleFile = (file) => {
  // 清除之前的状态
  previewColumns.value = [];
  previewData.value = [];
  fieldMapping.value = {};

  // 检查文件类型
  const fileName = file.name.toLowerCase();
  const isExcelFile =
    fileName.endsWith(".xlsx") ||
    fileName.endsWith(".xls") ||
    fileName.endsWith(".xlsm") ||
    fileName.endsWith(".xltm");

  if (!isExcelFile) {
    ElMessage.error("请选择Excel文件 (.xlsx, .xls, .xlsm, .xltm)");
    return;
  }

  // 检查文件大小（限制为10MB）
  const maxSize = 10 * 1024 * 1024; // 10MB
  if (file.size > maxSize) {
    ElMessage.error("文件大小不能超过10MB");
    return;
  }

  selectedFile.value = file;
  // 自动开始预览数据
  previewFile(file);
};

// 预览文件
const previewFile = (file) => {
  console.log("开始预览文件:", file.name, file.type, file.size);

  // 设置加载状态
  isPreviewing.value = true;

  // 文件类型和大小检查已在 handleFile 函数中完成

  // 使用xlsx库来预览Excel文件
  import("xlsx")
    .then((XLSX) => {
      console.log("xlsx库加载成功");
      const reader = new FileReader();
      reader.onload = (e) => {
        console.log("文件读取完成，开始解析");
        try {
          const data = new Uint8Array(e.target.result);
          console.log("文件数据长度:", data.length);

          // 尝试解析Excel文件
          const workbook = XLSX.read(data, { type: "array" });
          console.log(
            "Excel文件解析成功，工作表数量:",
            workbook.SheetNames.length,
          );

          const firstSheetName = workbook.SheetNames[0];
          console.log("第一个工作表名称:", firstSheetName);

          const worksheet = workbook.Sheets[firstSheetName];
          console.log("工作表获取成功");

          const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
          console.log("工作表转换为JSON成功，行数:", jsonData.length);

          if (jsonData.length > 0) {
            // 获取表头
            const headers = jsonData[0];
            console.log("表头:", headers);

            previewColumns.value = headers.map((header, index) => ({
              prop: `column${index + 1}`,
              label: header || `列${index + 1}`,
            }));

            // 获取数据
            previewData.value = [];
            for (let i = 1; i < Math.min(jsonData.length, 20); i++) {
              // 只预览前20行
              const row = {};
              headers.forEach((header, index) => {
                row[`column${index + 1}`] = jsonData[i][index] || "";
              });
              previewData.value.push(row);
            }
            console.log("预览数据准备完成，行数:", previewData.value.length);
          } else {
            console.log("Excel文件为空");
            ElMessage.warning("Excel文件为空");
            previewColumns.value = [];
            previewData.value = [];
          }

          // 初始化字段映射
          initFieldMapping();
          console.log("字段映射初始化完成");
        } catch (error) {
          console.error("预览文件失败:", error);
          ElMessage.error(`预览文件失败: ${error.message || "请检查文件格式"}`);
          // 降级为模拟数据，确保用户可以继续操作
          previewColumns.value = [
            { prop: "column1", label: "用户名" },
            { prop: "column2", label: "密码" },
            { prop: "column3", label: "真实姓名" },
            { prop: "column4", label: "手机号" },
            { prop: "column5", label: "邮箱" },
          ];

          previewData.value = [
            {
              column1: "user1",
              column2: "123456",
              column3: "用户1",
              column4: "13800138001",
              column5: "user1@example.com",
            },
            {
              column1: "user2",
              column2: "123456",
              column3: "用户2",
              column4: "13800138002",
              column5: "user2@example.com",
            },
            {
              column1: "user3",
              column2: "123456",
              column3: "用户3",
              column4: "13800138003",
              column5: "user3@example.com",
            },
          ];

          // 初始化字段映射
          initFieldMapping();
        } finally {
          // 结束加载状态
          isPreviewing.value = false;
        }
      };
      reader.onerror = () => {
        console.error("文件读取失败");
        ElMessage.error("读取文件失败，请检查文件是否损坏");
        // 降级为模拟数据
        previewColumns.value = [
          { prop: "column1", label: "用户名" },
          { prop: "column2", label: "密码" },
          { prop: "column3", label: "真实姓名" },
          { prop: "column4", label: "手机号" },
          { prop: "column5", label: "邮箱" },
        ];

        previewData.value = [
          {
            column1: "user1",
            column2: "123456",
            column3: "用户1",
            column4: "13800138001",
            column5: "user1@example.com",
          },
          {
            column1: "user2",
            column2: "123456",
            column3: "用户2",
            column4: "13800138002",
            column5: "user2@example.com",
          },
          {
            column1: "user3",
            column2: "123456",
            column3: "用户3",
            column4: "13800138003",
            column5: "user3@example.com",
          },
        ];

        // 初始化字段映射
        initFieldMapping();

        // 结束加载状态
        isPreviewing.value = false;
      };
      reader.readAsArrayBuffer(file);
      console.log("开始读取文件...");
    })
    .catch((error) => {
      console.error("加载xlsx库失败:", error);
      ElMessage.error("加载文件预览库失败，使用模拟数据");
      // 降级为模拟数据
      previewColumns.value = [
        { prop: "column1", label: "用户名" },
        { prop: "column2", label: "密码" },
        { prop: "column3", label: "真实姓名" },
        { prop: "column4", label: "手机号" },
        { prop: "column5", label: "邮箱" },
      ];

      previewData.value = [
        {
          column1: "user1",
          column2: "123456",
          column3: "用户1",
          column4: "13800138001",
          column5: "user1@example.com",
        },
        {
          column1: "user2",
          column2: "123456",
          column3: "用户2",
          column4: "13800138002",
          column5: "user2@example.com",
        },
        {
          column1: "user3",
          column2: "123456",
          column3: "用户3",
          column4: "13800138003",
          column5: "user3@example.com",
        },
      ];

      // 初始化字段映射
      initFieldMapping();

      // 结束加载状态
      isPreviewing.value = false;
    });
};

// 初始化字段映射
const initFieldMapping = () => {
  const mapping = {};
  organizationUserFields.forEach((field) => {
    // 尝试自动匹配列
    let matchedColumn = null;
    if (previewColumns.value && previewColumns.value.length > 0) {
      matchedColumn = previewColumns.value.find((col) => {
        // 确保 col 和 col.label 存在
        return (
          col &&
          col.label &&
          (col.label.includes(field.label) || field.label.includes(col.label))
        );
      });
    }
    mapping[field.prop] = matchedColumn ? matchedColumn.prop : "";
  });
  fieldMapping.value = mapping;
};

// 清除文件
const clearFile = () => {
  selectedFile.value = null;
  previewData.value = [];
  previewColumns.value = [];
  fieldMapping.value = {};
  if (fileInput.value) {
    fileInput.value.value = "";
  }
};

// 下一步
const nextStep = () => {
  if (currentStep.value < 3) {
    currentStep.value++;
    if (currentStep.value === 3) {
      startImport();
    }
  }
};

// 上一步
const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--;
  }
};

// 开始导入
const startImport = () => {
  importComplete.value = false;
  importSuccess.value = false;
  importProgress.value = 0;
  importMessage.value = "开始导入...";
  importStatus.value = "";

  // 实际导入逻辑
  const formData = new FormData();
  formData.append("file", selectedFile.value);
  formData.append("import_mode", importMode.value);
  formData.append("field_mapping", JSON.stringify(fieldMapping.value));

  request
    .post("/admin/organization/import-users", formData, {
      onUploadProgress: (progressEvent) => {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total,
        );
        importProgress.value = percentCompleted;
        if (importProgress.value < 50) {
          importMessage.value = "正在解析文件...";
        } else if (importProgress.value < 80) {
          importMessage.value = "正在处理数据...";
        } else {
          importMessage.value = "正在保存数据...";
        }
      },
    })
    .then((res) => {
      if (res.code === 200) {
        importComplete.value = true;
        importSuccess.value = true;
        importStatus.value = "success";
        importMessage.value = "导入完成";
        importStats.value = res.data || {
          success: 0,
          failure: 0,
          total: 0,
          errors: [],
        };
        // 如果有错误，显示错误信息
        if (
          importStats.value.failure > 0 &&
          importStats.value.errors &&
          importStats.value.errors.length > 0
        ) {
          importMessage.value = `导入完成，但有 ${importStats.value.failure} 条数据失败`;
        }
        emit("import-success");
      } else {
        importComplete.value = true;
        importSuccess.value = false;
        importStatus.value = "exception";
        importMessage.value = res.message || "导入失败";
        importStats.value = { success: 0, failure: 0, total: 0, errors: [] };
      }
    })
    .catch((error) => {
      importComplete.value = true;
      importSuccess.value = false;
      importStatus.value = "exception";
      importMessage.value = error.message || "导入失败";
      importStats.value = { success: 0, failure: 0, total: 0, errors: [] };
      console.error("导入失败:", error);
    });
};

// 取消导入
const cancelImport = () => {
  dialogVisible.value = false;
  resetState();
};

// 切换全屏
const toggleFullscreen = () => {
  fullscreen.value = !fullscreen.value;
};

const handleCancel = () => {
  emit("update:visible", false);
};

// 下载导入模板
const downloadTemplate = () => {
  // 定义模板数据
  const templateData = [
    ["用户名", "密码", "真实姓名", "手机号", "邮箱", "部门ID", "状态"],
    [
      "user1",
      "123456",
      "用户1",
      "13800138001",
      "user1@example.com",
      "1",
      "enabled",
    ],
    [
      "user2",
      "123456",
      "用户2",
      "13800138002",
      "user2@example.com",
      "2",
      "enabled",
    ],
    [
      "user3",
      "123456",
      "用户3",
      "13800138003",
      "user3@example.com",
      "3",
      "disabled",
    ],
  ];

  // 转换为CSV格式
  const csvContent = templateData.map((row) => row.join(",")).join("\n");
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.setAttribute("href", url);
  link.setAttribute("download", "organization_user_import_template.csv");
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

// 导出错误信息为Excel
const exportErrorDetails = () => {
  import("xlsx")
    .then((XLSX) => {
      if (!importStats.value.errors || importStats.value.errors.length === 0) {
        ElMessage.warning("没有错误信息可导出");
        return;
      }

      // 准备导出数据
      const exportData = [];

      // 处理每个错误
      importStats.value.errors.forEach((error) => {
        // 保留原有数据
        const rowData = { ...error.data };
        // 在最后添加错误原因
        rowData["错误原因"] = error.message;
        exportData.push(rowData);
      });

      // 创建工作簿
      const ws = XLSX.utils.json_to_sheet(exportData);
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, "错误信息");

      // 导出Excel文件
      XLSX.writeFile(wb, "import_error_details.xlsx");
      ElMessage.success("错误信息导出成功");
    })
    .catch((error) => {
      console.error("导出错误信息失败:", error);
      ElMessage.error("导出错误信息失败");
    });
};

// 重置状态
const resetState = () => {
  currentStep.value = 0;
  importMode.value = "insert";
  selectedFile.value = null;
  isDragover.value = false;
  previewData.value = [];
  previewColumns.value = [];
  fieldMapping.value = {};
  importProgress.value = 0;
  importMessage.value = "准备导入...";
  importStatus.value = "";
  importComplete.value = false;
  importSuccess.value = false;
  importStats.value = { success: 0, failure: 0, total: 0 };
  if (fileInput.value) {
    fileInput.value.value = "";
  }
};

// 监听对话框关闭
watch(
  () => props.visible,
  (newVal) => {
    if (!newVal) {
      resetState();
    }
  },
);
</script>

<style scoped>
.import-mode-container {
  margin-bottom: 20px;
}

.upload-area {
  border: 2px dashed #d9d9d9;
  border-radius: 6px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 20px;
}

.upload-area:hover {
  border-color: var(--brand-color);
}

.upload-area.dragover {
  border-color: var(--brand-color);
  background-color: rgba(var(--brand-color-rgb),  0.08);
}

.upload-icon {
  font-size: 48px;
  color: var(--td-text-color-brand);
  margin-bottom: 16px;
}

.upload-content p {
  margin: 8px 0;
  color: var(--td-text-color-secondary);
}

.upload-content .tip {
  font-size: 12px;
  color: var(--td-text-color-placeholder);
}

.file-info {
  margin-top: 16px;
  padding: 8px 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.file-info span {
  margin: 0 8px;
  flex: 1;
  text-align: left;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-preview {
  padding: 40px 0;
  text-align: center;
}

.progress-container {
  margin: 20px 0;
}

.progress-text {
  margin-top: 12px;
  text-align: center;
  color: var(--td-text-color-secondary);
}

.success-info {
  margin-top: 16px;
  text-align: left;
  width: 850px;
}

.error-info {
  margin-top: 16px;
  text-align: left;
  width: 850px;
}

.success-info p {
  margin: 8px 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-details {
  margin-top: 8px;
}

.result-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  padding: 4px 0;
  border-bottom: 1px solid #f0f0f0;
}

.result-item:last-child {
  border-bottom: none;
}

.result-item .label {
  font-weight: 500;
  color: var(--td-text-color-secondary);
}

.result-item .value {
  font-weight: 600;
  color: var(--td-text-color-primary);
}

.result-item .value.success {
  color: var(--td-success-color);
}

.result-item .value.error {
  color: var(--td-error-color);
}

.error-details {
  margin-top: 8px;
  color: var(--td-error-color);
  line-height: 1.5;
}

.error-list {
  margin-top: 16px;
  border-top: 1px solid #f0f0f0;
  padding-top: 16px;
}

.error-title {
  font-weight: 600;
  color: var(--td-error-color);
  margin-bottom: 12px;
}

.error-detail {
  padding: 8px;
  background-color: #fef0f0;
  border-radius: 4px;
  margin-top: 8px;
}

.error-data {
  font-size: 12px;
  line-height: 1.4;
  color: var(--td-text-color-secondary);
  word-break: break-all;
}

.button-group {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 32px;
}

.import-dialog {
  display: flex !important;
  flex-direction: column !important;
  height: 100% !important;
  height: 600px;
}

.import-dialog .el-dialog__body {
  display: flex;
  flex-direction: column;
  padding: 0;
  overflow: hidden;
  height: calc(100% - 120px);
}

.import-dialog.is-fullscreen .el-dialog__body {
  flex: 1;
  height: auto;
}

.import-dialog .el-steps {
  padding: 20px;
  margin: 0;
}

.content-section {
  height: 470px;
  overflow-y: auto;
  padding: 0 20px;
}

.import-dialog.is-fullscreen .content-section {
  flex: 1;
  height: calc(100vh - 230px);
  min-height: 0;
}

.preview-container,
.config-container,
.import-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.el-table {
  flex: 1;
  min-height: 0;
}

.upload-area {
  margin: 20px 0;
}

.download-template {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}

/* 响应式调整 */
@media (max-height: 600px) {
  .content-section {
    padding: 0 8px;
  }

  .upload-content {
    padding: 20px;
  }

  .upload-icon {
    font-size: 32px;
    margin-bottom: 12px;
  }
}

@media (max-width: 768px) {
  .content-section {
    padding: 0 8px;
  }

  .result-details {
    font-size: 14px;
  }
}

.dialog-title {
  font-size: 16px;
  line-height: 24px;
}

.dialog-header-actions {
  gap: 8px;
  float: right;
}

.import-mode-form {
  display: flex;
  align-items: center;
  gap: 12px;
}

.import-mode-item {
  margin: 0;
}

.import-mode-select {
  width: 190px;
}

.download-template-item {
  margin: 0;
  margin-left: auto;
}

.file-input-hidden {
  display: none;
}

.preview-table {
  width: 100%;
}

.field-mapping-form {
  padding-top: 20px;
}

.field-mapping-select {
  width: 220px;
}

.result-card {
  width: 100%;
}

.export-error-btn {
  float: right;
}

:deep(
  .import-result > div > div.el-result__extra > div > div > div.el-card__body
) {
  overflow: hidden;
}
</style>
