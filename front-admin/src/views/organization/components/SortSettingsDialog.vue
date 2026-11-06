<template>
  <el-dialog
    header="字段排序设置"
    v-model="dialogVisible"
    width="450px"
    class="sort-settings-dialog"
    :show-close="false"
  >
    <template #header>
      <span class="dialog-title">字段排序设置</span>
      <div class="close-btn">
        <el-button @click="handleCancel" title="关闭" text>
          <el-icon>
            <Close />
          </el-icon>
        </el-button>
      </div>
    </template>
    <div style="padding: 20px 20px">
      <!-- 添加排序规则按钮 -->
      <el-button
        type="primary"
        @click="addSortRule"
        style="margin-bottom: 16px"
      >
        <el-icon>
          <Plus />
        </el-icon>
        添加排序规则
      </el-button>
      <!-- 排序规则列表 -->
      <div v-if="internalSortRules.length > 0" style="margin-bottom: 20px">
        <div ref="sortableList" style="min-height: 50px">
          <div
            v-for="(rule, idx) in internalSortRules"
            :key="rule.id"
            style="
              display: flex;
              align-items: center;
              margin-bottom: 8px;
              border-radius: 4px;
              transition: all 0.2s ease;
            "
            :style="{
              'border-color': draggingIndex === idx ? 'var(--brand-color)' : '#e4e7ed',
              'background-color': draggingIndex === idx ? '#ecf5ff' : '#ffffff',
              'box-shadow':
                draggingIndex === idx
                  ? '0 2px 12px 0 rgba(var(--brand-color-rgb),  0.15)'
                  : 'none',
              transform: draggingIndex === idx ? 'translateY(-2px)' : 'none',
            }"
          >
            <!-- 字段选择 -->
            <el-select
              v-model="rule.field"
              placeholder="选择字段"
              style="flex: 1; margin-right: 8px"
            >
              <el-option label="ID" value="id" />
              <el-option label="用户名" value="username" />
              <el-option label="真实姓名" value="name" />
              <el-option label="手机号" value="phone" />
              <el-option label="邮箱" value="email" />
              <el-option label="状态" value="status" />
              <el-option label="最后登录时间" value="last_login_time" />
              <el-option label="创建时间" value="create_time" />
              <el-option label="更新时间" value="update_time" />
              <el-option label="部门" value="dept_id" />
            </el-select>
            <!-- 排序方向 -->
            <div style="display: flex; align-items: center; margin-right: 8px">
              <el-button
                :type="rule.direction === 'asc' ? 'primary' : 'default'"
                @click="setSortDirection(rule.id, 'asc')"
              >
                升序
              </el-button>
              <el-button
                :type="rule.direction === 'desc' ? 'primary' : 'default'"
                @click="setSortDirection(rule.id, 'desc')"
              >
                降序
              </el-button>
            </div>
            <!-- 拖动图标 -->
            <div
              class="sortable-handle"
              style="margin-right: 8px; color: var(--td-text-color-placeholder); cursor: move"
            >
              <i class="iconfont x-tuodong2"></i>
            </div>
            <!-- 删除按钮 -->
            <el-button type="danger" @click="removeSortRule(rule.id)">
              <el-icon>
                <Delete />
              </el-icon>
            </el-button>
          </div>
        </div>
      </div>
      <div v-else style="text-align: center; color: var(--td-text-color-placeholder); padding: 20px">
        暂无排序规则
      </div>
    </div>
    <template #footer>
      <div class="dialog-footer">
        <el-button type="primary" @click="applySort">排序</el-button>
        <el-button @click="removeAllSortRules">删除全部</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, computed } from "vue";
import { ElMessage } from "element-plus";
import { Plus, Delete, Close } from "@element-plus/icons-vue";
import Sortable from "sortablejs";

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  sortRules: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(["update:visible", "save"]);

const internalSortRules = ref([]);
const draggingIndex = ref(-1);
const sortableList = ref(null);
let sortableInstance = null;

// 使用computed属性实现v-model双向绑定
const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => {
    emit("update:visible", value);
    // 当对话框变为可见时，重新初始化SortableJS
    if (value) {
      // 在下一个DOM更新周期初始化SortableJS
      setTimeout(() => {
        destroySortable();
        initSortable();
      }, 100);
    }
  },
});

// 为排序规则添加唯一ID
const ensureSortRulesHaveIds = (rules) => {
  return rules.map((rule) => ({
    ...rule,
    id: rule.id || Date.now() + Math.random(),
  }));
};

// 初始化内部排序规则
internalSortRules.value = ensureSortRulesHaveIds([...props.sortRules]);

// 监听外部sortRules变化
watch(
  () => props.sortRules,
  (newVal) => {
    internalSortRules.value = ensureSortRulesHaveIds([...newVal]);
  },
  { deep: true },
);

// 排序相关方法
const addSortRule = () => {
  internalSortRules.value.push({
    id: Date.now() + Math.random(),
    field: "id",
    direction: "asc",
  });
};

const removeSortRule = (ruleId) => {
  internalSortRules.value = internalSortRules.value.filter(
    (rule) => rule.id !== ruleId,
  );
};

const removeAllSortRules = () => {
  internalSortRules.value = [];
};

const setSortDirection = (ruleId, direction) => {
  // 创建新数组，避免直接修改原数组元素导致的响应式问题
  const newRules = internalSortRules.value.map((rule) => {
    if (rule.id === ruleId) {
      return {
        ...rule,
        direction,
      };
    }
    return rule;
  });
  internalSortRules.value = newRules;
};

const applySort = () => {
  emit("save", [...internalSortRules.value]);
  dialogVisible.value = false;
  ElMessage.success("排序规则已应用");
};

// 初始化SortableJS
const initSortable = () => {
  if (sortableList.value && !sortableInstance) {
    sortableInstance = new Sortable(sortableList.value, {
      handle: ".sortable-handle", // 拖动句柄
      animation: 150, // 动画持续时间
      ghostClass: "sortable-ghost", // 拖动时的幽灵元素类
      chosenClass: "sortable-chosen", // 选中元素的类
      dragClass: "sortable-drag", // 拖动元素的类
      onStart: function (evt) {
        draggingIndex.value = evt.oldIndex;
        console.log("Sortable onStart:", evt.oldIndex);
      },
      onEnd: function (evt) {
        console.log("Sortable onEnd:", evt.oldIndex, "->", evt.newIndex);
        if (evt.oldIndex !== evt.newIndex) {
          // 重新排序数组 - 使用展开运算符创建新数组确保Vue检测到变化
          const newRules = [...internalSortRules.value];
          const movedItem = newRules.splice(evt.oldIndex, 1)[0];
          newRules.splice(evt.newIndex, 0, movedItem);
          internalSortRules.value = newRules;
          console.log("Updated internalSortRules:", internalSortRules.value);
        }
        draggingIndex.value = -1;
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

// 生命周期钩子
onMounted(() => {
  initSortable();
});

onUnmounted(() => {
  destroySortable();
});

// 监听internalSortRules长度变化，重新初始化SortableJS
// 只在排序规则数量变化时重新初始化，避免属性变化时的频繁重建
watch(
  () => internalSortRules.value.length,
  () => {
    // 在下一个DOM更新周期初始化SortableJS
    setTimeout(() => {
      destroySortable();
      initSortable();
    }, 100);
  },
);

const handleCancel = () => {
  dialogVisible.value = false;
};

// 监听dialogVisible变化，当对话框显示时初始化SortableJS
watch(
  () => props.visible,
  (newVal) => {
    if (newVal) {
      // 在下一个DOM更新周期初始化SortableJS
      setTimeout(() => {
        console.log("Dialog visible, initializing SortableJS...");
        destroySortable();
        initSortable();
      }, 100);
    }
  },
);
</script>

<style scoped>
.sort-settings-dialog {
  .close-btn {
    float: right;
  }
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
