<template>
  <!-- 批量修改弹窗 -->
  <el-dialog
    v-model="dialogVisible"
    :title="dialogTitle"
    :width="fullscreen ? '100%' : '1000px'"
    :fullscreen="fullscreen"
    :show-close="false"
    class="batch-modify-dialog"
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
    <div class="dialog-body">
      <!-- 字段选择控件 -->
      <div class="field-selector">
        <el-button @click="handleCopyHeaders" text>
          <el-icon>
            <Document />
          </el-icon>
          复制数据
        </el-button>
        <el-button @click="handlePasteData" text>
          <el-icon>
            <Upload />
          </el-icon>
          粘贴数据
        </el-button>
        <el-popover
          v-model:visible="showFieldSelector"
          placement="bottom"
          width="400"
        >
          <template #reference>
            <el-button text>
              <el-icon>
                <Check />
              </el-icon>
              选择字段
            </el-button>
          </template>
          <div class="field-selector-content">
            <h4 class="field-selector-title">选择要显示的字段</h4>
            <el-checkbox-group v-model="selectedFields">
              <el-checkbox
                v-for="field in availableFields"
                :key="field.value"
                :label="field.value"
              >
                {{ field.label }}
              </el-checkbox>
            </el-checkbox-group>
            <div class="field-selector-footer">
              <el-button type="primary" @click="confirmFieldSelection"
                >确定</el-button
              >
              <el-button @click="showFieldSelector = false">取消</el-button>
            </div>
          </div>
        </el-popover>
      </div>

      <!-- 表格形式的批量编辑 -->
      <div class="batch-edit-table">
        <el-table :data="selectedRows" class="batch-table" border>
          <el-table-column type="index" label="序号" width="60" />
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column
            v-for="field in selectedFields"
            :key="field"
            :prop="field"
            :label="getFieldLabel(field)"
          >
            <template #default="{ row }">
              <el-input
                v-if="field !== 'status'"
                v-model="row[field]"
                @dblclick="handleDoubleClick"
                size="small"
              />
              <el-switch
                v-else
                v-model="row[field]"
                :active-value="1"
                :inactive-value="0"
                @dblclick="handleDoubleClick"
              />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80" fixed="right">
            <template #default="{ $index }">
              <el-button
                type="danger"
                size="small"
                @click="handleDeleteRow($index)"
                text
              >
                <el-icon>
                  <Delete />
                </el-icon>
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleCancel">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定修改</el-button>
      </div>
    </template>
  </el-dialog>

  <!-- 批量修改抽屉 -->
  <el-drawer
    v-model="drawerVisible"
    :title="dialogTitle"
    direction="rtl"
    :size="fullscreen ? '100%' : '1200px'"
    :show-close="false"
    class="batch-modify-drawer"
  >
    <template #header>
      {{ dialogTitle }}
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
    <div class="drawer-body">
      <el-divider class="dialog-divider" />

      <!-- 字段选择控件 -->
      <div class="field-selector">
        <el-button type="primary" @click="handleCopyHeaders" text>
          <el-icon>
            <Document />
          </el-icon>
          复制数据
        </el-button>
        <el-button type="primary" @click="handlePasteData" text>
          <el-icon>
            <Upload />
          </el-icon>
          粘贴数据
        </el-button>
        <el-popover
          v-model:visible="showFieldSelector"
          placement="bottom"
          width="400"
        >
          <template #reference>
            <el-button type="primary" text>
              <el-icon>
                <Check />
              </el-icon>
              选择字段
            </el-button>
          </template>
          <div class="field-selector-content">
            <h4 class="field-selector-title">选择要显示的字段</h4>
            <el-checkbox-group v-model="selectedFields">
              <el-checkbox
                v-for="field in availableFields"
                :key="field.value"
                :label="field.value"
              >
                {{ field.label }}
              </el-checkbox>
            </el-checkbox-group>
            <div class="field-selector-footer">
              <el-button @click="showFieldSelector = false">取消</el-button>
              <el-button type="primary" @click="confirmFieldSelection"
                >确定</el-button
              >
            </div>
          </div>
        </el-popover>
      </div>

      <!-- 表格形式的批量编辑 -->
      <div class="batch-edit-table">
        <el-table :data="selectedRows" class="batch-table" border>
          <el-table-column type="index" label="序号" width="60" />
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column
            v-for="field in selectedFields"
            :key="field"
            :prop="field"
            :label="getFieldLabel(field)"
          >
            <template #default="{ row }">
              <el-input
                v-if="field !== 'status'"
                v-model="row[field]"
                @dblclick="handleDoubleClick"
                size="small"
              />
              <el-switch
                v-else
                v-model="row[field]"
                :active-value="1"
                :inactive-value="0"
                @dblclick="handleDoubleClick"
              />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80" fixed="right">
            <template #default="{ $index }">
              <el-button
                type="danger"
                size="small"
                @click="handleDeleteRow($index)"
                text
              >
                <el-icon>
                  <Delete />
                </el-icon>
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleCancel">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定修改</el-button>
      </div>
    </template>
  </el-drawer>
</template>

<script setup>
import { ref, computed } from "vue";
import { ElMessage } from "element-plus";
import {
  FullScreen,
  Close,
  Check,
  Document,
  Upload,
  Delete,
} from "@element-plus/icons-vue";

const { visible, displayMode, selectedRows } = defineProps({
  visible: { type: Boolean, default: false },
  displayMode: {
    type: String,
    default: "dialog",
    validator: (value) => ["dialog", "drawer"].includes(value),
  },
  selectedRows: { type: Array, default: () => [] },
});

const emit = defineEmits(["update:visible", "submit"]);

const dialogVisible = computed({
  get: () => visible && displayMode === "dialog",
  set: (value) => {
    if (!value && displayMode === "dialog") emit("update:visible", false);
  },
});

const drawerVisible = computed({
  get: () => visible && displayMode === "drawer",
  set: (value) => {
    if (!value && displayMode === "drawer") emit("update:visible", false);
  },
});

const dialogTitle = computed(() => `批量修改 (${selectedRows.length} 条数据)`);
const fullscreen = ref(false);
const showFieldSelector = ref(false);
const availableFields = [
  { label: "用户名", value: "username" },
  { label: "真实姓名", value: "name" },
  { label: "手机号", value: "phone" },
  { label: "邮箱", value: "email" },
  { label: "状态", value: "status" },
  { label: "部门ID", value: "deptId" },
];
const selectedFields = ref(["name", "phone", "email", "status"]);

const toggleFullscreen = () => {
  fullscreen.value = !fullscreen.value;
};
const handleCancel = () => {
  emit("update:visible", false);
};
const confirmFieldSelection = () => {
  showFieldSelector.value = false;
};
const getFieldLabel = (field) => {
  const found = availableFields.find((item) => item.value === field);
  return found ? found.label : field;
};
const handleDoubleClick = (event) => {
  const target = event.target;
  if (target.tagName === "INPUT") target.focus();
};
const handleDeleteRow = (index) => {
  selectedRows.splice(index, 1);
  ElMessage.success("行已删除");
};

const handleCopyHeaders = async () => {
  try {
    const headers = [
      "ID",
      ...selectedFields.value.map((field) => getFieldLabel(field)),
    ];
    const rows = [headers.join("\t")];
    selectedRows.forEach((row) => {
      const rowData = [row.id];
      selectedFields.value.forEach((field) => {
        let value = row[field];
        if (field === "status") value = value === 1 ? "启用" : "禁用";
        rowData.push(value);
      });
      rows.push(rowData.join("\t"));
    });
    await navigator.clipboard.writeText(rows.join("\n"));
    ElMessage.success("数据已复制到剪贴板");
  } catch (error) {
    ElMessage.error("复制失败，请手动复制");
  }
};

const handlePasteData = async () => {
  try {
    const clipboardText = await navigator.clipboard.readText();
    const rows = clipboardText.trim().split("\n");
    if (rows.length === 0) {
      ElMessage.warning("剪贴板为空");
      return;
    }
    const pastedHeaders = rows[0].split("\t");
    const headerToField = {
      ID: "id",
      用户名: "username",
      真实姓名: "name",
      手机号: "phone",
      邮箱: "email",
      状态: "status",
      部门ID: "deptId",
    };
    selectedRows.forEach((row) => {
      selectedFields.value.forEach((field) => {
        if (field !== "id") row[field] = field === "status" ? 1 : "";
      });
    });
    for (let i = 1; i < rows.length; i++) {
      const cells = rows[i].split("\t");
      if (cells.length === 0) continue;
      const id = cells[0];
      const targetRow = selectedRows.find((row) => row.id.toString() === id);
      if (targetRow) {
        cells.forEach((cell, index) => {
          const header = pastedHeaders[index];
          const field = headerToField[header];
          if (field && selectedFields.value.includes(field) && field !== "id") {
            targetRow[field] =
              field === "status"
                ? cell === "启用" || cell === "1" || cell === "true"
                  ? 1
                  : 0
                : cell;
          }
        });
      }
    }
    for (let i = selectedRows.length - 1; i >= 0; i--) {
      const row = selectedRows[i];
      const hasData = selectedFields.value.some((field) => {
        if (field === "id") return false;
        if (field === "status") return true;
        return (
          row[field] !== "" && row[field] !== null && row[field] !== undefined
        );
      });
      if (!hasData) selectedRows.splice(i, 1);
    }
    ElMessage.success("数据已粘贴成功");
  } catch (error) {
    ElMessage.error("粘贴失败，请检查剪贴板数据格式");
  }
};

const handleSubmit = async () => {
  try {
    if (selectedRows.length === 0) {
      ElMessage.warning("请选择要修改的数据");
      return;
    }
    const modifiedData = selectedRows.map((row) => ({
      id: row.id,
      ...Object.fromEntries(
        selectedFields.value.map((field) => [field, row[field]]),
      ),
    }));
    emit("submit", { data: modifiedData });
    emit("update:visible", false);
  } catch (error) {
    ElMessage.error("提交失败");
  }
};
</script>

<style scoped>
.batch-modify-dialog {
  display: flex;
  flex-direction: column;
  height: 700px;
}

.batch-modify-dialog.is-fullscreen .dialog-body {
  flex: 1;
  height: calc(100vh - 120px);
}

.dialog-title {
  line-height: 24px;
}

.dialog-header-actions {
  float: right;
}

.dialog-body {
  height: 500px;
  min-height: 0;
  overflow-y: auto;
  padding: 0 0px;
}

.dialog-divider {
  margin: 0 0 20px;
}

.dialog-footer {
  display: flex;
  gap: 8px;
}

.batch-modify-drawer {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 700px;
}

.batch-modify-drawer .el-drawer__body {
  display: flex;
  flex-direction: column;
  padding: 0;
  overflow: hidden;
  height: calc(100% - 120px);
}

.batch-modify-drawer.is-fullscreen .el-drawer__body {
  flex: 1;
  height: auto;
}

.drawer-body {
  height: 100%;
  min-height: 0;
}

.field-selector {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
  margin-top: 5px;
  border-bottom: 1px solid #e4e7ed;
  padding-bottom: 5px;
  padding-left: 8px;
}

.field-selector-content {
  padding: 16px;
}

.field-selector-content .el-checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-selector-title {
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
}

.field-selector-footer {
  margin-top: 16px;
}

.batch-edit-table {
  width: 100%;
}

.batch-table {
  width: 100%;
}

:deep(.batch-table .el-table__header-wrapper) {
  background-color: #f5f7fa;
}

:deep(.batch-table .el-table__header th) {
  background-color: #f5f7fa;
  color: var(--td-text-color-secondary);
  font-weight: 60;
}

:deep(.batch-table .el-table__row) {
  height: 48px;
}

:deep(.batch-table .el-table__body tr:nth-child(even)) {
  background-color: #fafafa;
}

:deep(.batch-table .el-table__body tr:hover) {
  background-color: #ecf5ff !important;
}

:deep(.batch-table .el-input) {
  width: 100%;
}

:deep(.batch-table .el-input__inner) {
  padding: 4px 8px;
  line-height: 24px;
  height: 32px;
  font-size: 14px;
}

:deep(.batch-table .el-switch) {
  margin-top: 4px;
}

:deep(.batch-table .el-table__cell) {
  padding: 8px 0;
}
</style>
