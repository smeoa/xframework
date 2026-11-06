<template>
  <el-dialog
    header="字段设置"
    v-model="dialogVisible"
    width="800px"
    class="field-settings-dialog"
    :show-close="false"
  >
    <template #header>
      字段设置
      <div class="close-btn">
        <el-button @click="handleCancel" title="关闭" text>
          <el-icon>
            <Close />
          </el-icon>
        </el-button>
      </div>
    </template>
    <el-form class="field-settings-form">
      <el-scrollbar class="width-order-container" height="400px">
        <div class="field-list-header">
          <div class="field-cell index-cell">序号</div>
          <div class="field-cell name-cell">字段名</div>
          <div class="field-cell visible-cell">显示</div>
          <div class="field-cell width-cell">宽度(px)</div>
          <div class="field-cell fixed-cell">固定</div>
          <div class="field-cell action-cell">操作</div>
        </div>
        <div class="field-list-body" ref="fieldListBody">
          <div
            v-for="(row, index) in sortedFieldList"
            :key="row.value"
            class="field-list-item"
          >
            <div class="field-cell index-cell">{{ index + 1 }}</div>
            <div class="field-cell name-cell">{{ row.label }}</div>
            <div class="field-cell visible-cell">
              <el-switch v-model="row.visible" size="small" />
            </div>
            <div class="field-cell width-cell">
              <el-input-number
                v-model="row.width"
                :min="50"
                :max="500"
                :step="10"
                controls-position="right"
                style="width: 120px"
              />
            </div>
            <div class="field-cell fixed-cell">
              <el-select
                v-model="row.fixed"
                placeholder="不固定"
                style="width: 120px"
              >
                <el-option label="不固定" value="" />
                <el-option label="左固定" value="left" />
                <el-option label="右固定" value="right" />
              </el-select>
            </div>
            <div class="field-cell action-cell">
              <el-button
                type="primary"
                link
                size="small"
                :disabled="index === 0"
                @click="moveField(index, -1)"
                title="上移"
              >
                <el-icon>
                  <ArrowUp />
                </el-icon>
              </el-button>
              <el-button
                type="primary"
                link
                size="small"
                :disabled="index === sortedFieldList.length - 1"
                @click="moveField(index, 1)"
                title="下移"
              >
                <el-icon>
                  <ArrowDown />
                </el-icon>
              </el-button>
              <div
                class="sortable-handle"
                style="
                  margin-left: 4px;
                  color: var(--td-text-color-placeholder);
                  cursor: move;
                  display: inline-block;
                "
              >
                <i class="iconfont x-tuodong2"></i>
              </div>
            </div>
          </div>
        </div>
      </el-scrollbar>
    </el-form>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleReset">重置默认配置</el-button>
        <el-button type="primary" @click="handleSave" size="default"
          >保存设置</el-button
        >
        <el-button @click="handleCancel">取消</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from "vue";
import { ArrowUp, ArrowDown, Close } from "@element-plus/icons-vue";
import Sortable from "sortablejs";

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  fields: {
    type: Array,
    default: () => [
      "id",
      "username",
      "name",
      "phone",
      "email",
      "deptId",
      "status",
      "lastLoginTime",
      "lastLoginIp",
      "createdTime",
      "updatedTime",
    ],
  },
  fieldConfig: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(["update:visible", "save"]);

const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => {
    if (!value) emit("update:visible", value);
  },
});

// 字段选项配置
const fieldOptions = [
  { value: "id", label: "ID", width: 60, fixed: "" },
  { value: "username", label: "用户名", width: 120, fixed: "" },
  { value: "name", label: "真实姓名", width: 120, fixed: "" },
  { value: "phone", label: "手机号", width: 120, fixed: "" },
  { value: "email", label: "邮箱", width: 120, fixed: "" },
  { value: "avatar", label: "头像", width: 80, fixed: "" },
  { value: "images", label: "图片", width: 140, fixed: "" },
  { value: "attachments", label: "附件", width: 160, fixed: "" },
  { value: "status", label: "状态", width: 70, fixed: "" },
  { value: "lastLoginTime", label: "最后登录时间", width: 140, fixed: "" },
  { value: "lastLoginIp", label: "最后登录IP", width: 140, fixed: "" },
  { value: "createdTime", label: "创建时间", width: 120, fixed: "" },
  { value: "updatedTime", label: "更新时间", width: 120, fixed: "" },
  { value: "deptName", label: "部门", width: 120, fixed: "" },
];

// 排序后的字段列表（用于宽度/顺序标签）
const sortedFieldList = ref([]);

let sortableInstance = null;
const fieldListBody = ref(null);

// 初始化排序后的字段列表
const initSortedFieldList = () => {
  const LOCAL_STORAGE_KEY = "organizationAllFieldConfig";
  let savedFullConfig = null;

  const savedConfigStr = localStorage.getItem(LOCAL_STORAGE_KEY);
  if (savedConfigStr) {
    try {
      savedFullConfig = JSON.parse(savedConfigStr);
    } catch (e) {
      console.error("解析保存的字段配置失败:", e);
    }
  }

  // 如果有保存的完整配置，按照保存的顺序返回，补全缺失的属性
  if (
    savedFullConfig &&
    Array.isArray(savedFullConfig) &&
    savedFullConfig.length > 0
  ) {
    sortedFieldList.value = savedFullConfig.map((savedItem) => {
      const defaultItem = fieldOptions.find(
        (item) => item.value === savedItem.value
      );
      return {
        value: savedItem.value,
        label: savedItem.label || defaultItem?.label || savedItem.value,
        width: savedItem.width ?? defaultItem?.width ?? 100,
        fixed: savedItem.fixed ?? defaultItem?.fixed ?? "",
        visible: savedItem.visible ?? props.fields.includes(savedItem.value),
      };
    });
    return;
  }

  // 没有保存过，使用默认顺序和配置
  sortedFieldList.value = fieldOptions.map((fieldOption) => {
    const savedItem = props.fieldConfig.find(
      (item) => item.value === fieldOption.value
    );
    return {
      value: fieldOption.value,
      label: fieldOption.label,
      width: savedItem?.width ?? fieldOption.width,
      fixed: savedItem?.fixed ?? fieldOption.fixed,
      visible: props.fields.includes(fieldOption.value),
    };
  });
};

// 监听字段变化，重新初始化
watch(
  () => props.fields,
  () => {
    initSortedFieldList();
  },
  { immediate: true }
);

// 上移下移字段
const moveField = (index, direction) => {
  const newIndex = index + direction;
  if (newIndex < 0 || newIndex >= sortedFieldList.value.length) return;
  const movedItem = sortedFieldList.value[index];
  sortedFieldList.value.splice(index, 1);
  sortedFieldList.value.splice(newIndex, 0, movedItem);
};

// 初始化SortableJS
const initSortable = () => {
  if (fieldListBody.value && !sortableInstance) {
    sortableInstance = new Sortable(fieldListBody.value, {
      handle: ".sortable-handle",
      animation: 150,
      ghostClass: "sortable-ghost",
      chosenClass: "sortable-chosen",
      dragClass: "sortable-drag",
      forceFallback: true,
      fallbackOnBody: true,
      swapThreshold: 0.65,
      onStart: function () {},
      onEnd: function (evt) {
        if (
          evt.oldIndex !== evt.newIndex &&
          evt.oldIndex !== null &&
          evt.newIndex !== null
        ) {
          const newList = [...sortedFieldList.value];
          const movedItem = newList.splice(evt.oldIndex, 1)[0];
          newList.splice(evt.newIndex, 0, movedItem);
          sortedFieldList.value = newList;
        }
      },
    });
  }
};

// 销毁SortableJS
const destroySortable = () => {
  if (sortableInstance) {
    sortableInstance.destroy();
    sortableInstance = null;
  }
};

onMounted(() => {
  initSortedFieldList();
});

onUnmounted(() => {
  destroySortable();
});

// 监听对话框显示状态，显示时重新加载配置并初始化
watch(dialogVisible, (visible) => {
  if (visible) {
    initSortedFieldList();
    requestAnimationFrame(() => {
      destroySortable();
      initSortable();
    });
  } else {
    destroySortable();
  }
});

// 当列表长度变化时，重新初始化Sortable
watch(
  () => sortedFieldList.value.length,
  () => {
    if (dialogVisible.value) {
      requestAnimationFrame(() => {
        destroySortable();
        initSortable();
      });
    }
  }
);

const handleCancel = () => {
  dialogVisible.value = false;
  destroySortable();
};

// 重置为默认配置
const handleReset = () => {
  sortedFieldList.value = fieldOptions.map((fieldOption) => {
    return {
      value: fieldOption.value,
      label: fieldOption.label,
      width: fieldOption.width,
      fixed: fieldOption.fixed,
      visible: props.fields.includes(fieldOption.value),
    };
  });
  ElMessage.success("已重置为默认配置");
};

const handleSave = () => {
  // 保存所有字段（包括可见和隐藏）的完整配置到localStorage
  const allFieldsConfig = sortedFieldList.value.map((item) => ({
    value: item.value,
    label: item.label,
    width: item.width,
    fixed: item.fixed,
    visible: item.visible,
  }));
  localStorage.setItem(
    "organizationAllFieldConfig",
    JSON.stringify(allFieldsConfig)
  );

  // 根据sortedFieldList的顺序和可见性获取最终的可见字段配置
  const sortedVisibleFields = sortedFieldList.value
    .filter((item) => item.visible)
    .map((item) => ({
      value: item.value,
      label: item.label,
      width: item.width,
      fixed: item.fixed,
    }));
  emit("save", sortedVisibleFields);
  dialogVisible.value = false;
  destroySortable();
};
</script>

<style scoped>
.field-settings-dialog {
  .close-btn {
    float: right;
  }
}

.width-order-container {
  width: 100%;
  box-sizing: border-box;
}

.field-list-header {
  display: flex;
  background-color: #f5f7fa;
  border-top: 1px solid #dcdfe6;
  border-left: 1px solid #dcdfe6;
  border-right: 1px solid #dcdfe6;
  border-bottom: 1px solid #dcdfe6;
  border-radius: 4px 4px 0 0;
  position: sticky;
  top: 0;
  z-index: 100;
}

.field-settings-form {
  width: 100%;
  padding: 0;
  overflow: visible;
}

.field-list-body {
  border-bottom: 1px solid #dcdfe6;
  border-left: none;
  border-right: none;
  border-radius: 0 0 4px 4px;
}

.field-list-item {
  display: flex;
  align-items: center;
  border-bottom: 1px solid #f0f0f0;
  background-color: #fff;
}

.field-list-item:last-child {
  border-bottom: none;
}

.field-cell {
  padding: 12px 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.index-cell {
  width: 60px;
  text-align: center;
}

.name-cell {
  flex: 1;
  min-width: 120px;
  justify-content: flex-start;
}

.width-cell {
  width: 140px;
}

.visible-cell {
  width: 80px;
}

.fixed-cell {
  width: 120px;
}

.action-cell {
  width: 160px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.sortable-ghost {
  opacity: 0.5;
  background: #ecf5ff;
  border: 2px dashed var(--brand-color);
}

.sortable-chosen {
  background: #ecf5ff;
  border-color: var(--brand-color);
}

.sortable-drag {
  opacity: 0.8;
  box-shadow: 0 4px 12px rgba(var(--brand-color-rgb),  0.3);
}

.sortable-handle {
  transition: color 0.2s;
}

.sortable-handle:hover {
  color: var(--td-text-color-brand);
}
</style>
