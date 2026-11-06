<template>
  <el-dialog
    header="搜索字段设置"
    v-model="dialogVisible"
    width="720px"
    class="field-settings-dialog"
    :show-close="false"
  >
    <template #header>
      <span class="dialog-title">搜索字段设置</span>
      <div class="close-btn">
        <el-button @click="handleCancel" title="关闭" text>
          <el-icon>
            <Close />
          </el-icon>
        </el-button>
      </div>
    </template>
    <el-form class="search-field-settings-form">
      <el-scrollbar height="400px">
        <el-form-item class="field-settings-item">
          <el-transfer
            v-model="transferValue"
            filterable
            :filter-placeholder="'搜索字段'"
            :data="transferData"
            :titles="['搜索字段', '非搜索字段']"
            style="width: 100%"
          />
        </el-form-item>
      </el-scrollbar>
    </el-form>
    <template #footer>
      <div class="dialog-footer">
        <el-button type="primary" @click="handleSave" size="default"
          >保存设置</el-button
        >
        <el-button @click="handleCancel">取消</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import { Close } from "@element-plus/icons-vue";

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  fields: {
    type: Array,
    default: () => ["id", "username", "name", "phone", "email", "status"],
  },
  fieldOptions: {
    type: Array,
    default: () => [
      { value: "id", label: "ID" },
      { value: "username", label: "用户名" },
      { value: "name", label: "真实姓名" },
      { value: "phone", label: "手机号" },
      { value: "email", label: "邮箱" },
      { value: "status", label: "状态" },
    ],
  },
});

const emit = defineEmits(["update:visible", "save"]);

const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit("update:visible", value),
});

// 转换为transfer组件需要的数据格式
const transferData = ref(
  props.fieldOptions.map((field, index) => ({
    key: field.value,
    label: field.label,
  })),
);

// 存储隐藏的字段（右侧的值）
const transferValue = ref([]);

// 监听字段变化，同步到transferValue
watch(
  () => props.fields,
  (newFields) => {
    // 计算隐藏的字段：所有字段减去显示的字段
    const allFields = props.fieldOptions.map((field) => field.value);
    const hiddenFields = allFields.filter(
      (field) => !newFields.includes(field),
    );
    transferValue.value = hiddenFields;
  },
  { immediate: true },
);

// 监听fieldOptions变化，同步更新transferData
watch(
  () => props.fieldOptions,
  (newFieldOptions) => {
    transferData.value = newFieldOptions.map((field, index) => ({
      key: field.value,
      label: field.label,
    }));
    // 重新计算隐藏字段
    const allFields = newFieldOptions.map((field) => field.value);
    const hiddenFields = allFields.filter(
      (field) => !props.fields.includes(field),
    );
    transferValue.value = hiddenFields;
  },
  { deep: true },
);

const handleCancel = () => {
  dialogVisible.value = false;
};

const handleSave = () => {
  // 计算显示的字段：所有字段减去隐藏的字段
  const allFields = props.fieldOptions.map((field) => field.value);
  const visibleFields = allFields.filter(
    (field) => !transferValue.value.includes(field),
  );
  emit("save", visibleFields);
  dialogVisible.value = false;
};
</script>

<style scoped>
.field-settings-dialog {
  .close-btn {
    float: right;
  }
}

/* 搜索字段设置弹窗样式 */
.search-field-settings-form {
  width: 100%;
  padding: 0;
  overflow: visible;
}

.field-settings-item {
  margin-bottom: 0;
}

.dialog-title {
  font-size: 16px;
  line-height: 24px;
}

/* 左右两栏等宽铺满弹窗可用宽度，中间为按钮列 */
.el-transfer {
  display: flex;
  align-items: stretch;
  height: 400px;
}

:deep(.el-transfer-panel) {
  flex: 1 1 0;
  width: auto;
  min-width: 0;
  height: 400px;
}

:deep(.el-transfer__buttons) {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
}

:deep(.el-transfer-panel__body) {
  height: 360px;
}
</style>
