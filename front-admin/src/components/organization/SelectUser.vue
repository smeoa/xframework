<template>
  <el-dialog
    header="选择用户"
    v-model="dialogVisible"
    width="700px"
    style="min-height: 500px"
    @close="handleClose"
  >
    <el-input
      placeholder="输入关键字进行过滤"
      v-model="filterText"
      style="margin-bottom: 20px"
    >
    </el-input>
    <el-scrollbar style="height: 400px">
      <el-tree
        class="filter-tree"
        :data="deptTree"
        :props="defaultProps"
        default-expand-all
        :filter-node-method="filterNode"
        :highlight-current="true"
        ref="tree"
        @node-click="onNodeClick"
        :expand-on-click-node="false"
      >
        <template #default="{ node, data }">
          <div class="tree-node-content">
            <span :class="{ 'node-disabled': data.id === currentDeptId }">
              {{ data.name }}
            </span>
            <span v-if="data.id === currentDeptId" class="disabled-tip"
              >(当前部门)</span
            >
          </div>
        </template>
        <template
          #default="{ node, data }"
          v-if="showUsers && data.children && data.children.length === 0"
        >
          <div class="tree-node-content">
            <span>{{ data.name }}</span>
            <el-link
              size="small"
              @click.stop="showDeptUsers(data.id, data.name)"
              >查看用户</el-link
            >
          </div>
        </template>
      </el-tree>

      <!-- 用户列表 -->
      <div v-if="showUsers && selectedDeptId" class="user-list">
        <h4 style="margin: 8px 0">{{ selectedDeptName }} - 用户列表</h4>
        <el-table v-loading="loading" :data="users" style="width: 100%" @row-click="onUserClick">
          <el-table-column prop="name" label="姓名" width="120" />
          <el-table-column prop="phone" label="手机" width="150" />
          <el-table-column prop="email" label="邮箱" />
          <el-table-column label="操作" width="80">
            <template #default="{ row }">
              <el-button type="primary" size="small" @click="selectUser(row)"
                >选择</el-button
              >
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-scrollbar>
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSave">确定</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.select-user-dialog {
  .el-dialog__body {
    padding: 20px;
  }
}
</style>

<script setup>
import { ref, computed, watch, onMounted } from "vue";
import { ElMessage } from "element-plus";
import request from "@/utils/request";

// 定义组件属性
const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  currentDeptId: {
    type: [String, Number],
    default: null,
  },
  currentDeptName: {
    type: String,
    default: "",
  },
  showUsers: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: "选择用户",
  },
});

// 定义组件事件
const emit = defineEmits(["update:visible", "save", "close"]);

// 响应式数据
const filterText = ref("");
const deptTree = ref([]);
const selectedNode = ref(null);
const selectedUser = ref(null);
const treeRef = ref(null);
const users = ref([]);
// 表格加载状态
const loading = ref(false);
const selectedDeptId = ref(null);
const selectedDeptName = ref("");

// 对话框标题
const dialogTitle = computed(() => props.title);

// 使用computed属性实现v-model双向绑定
const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit("update:visible", value),
});

// 树节点配置
const defaultProps = {
  children: "children",
  label: "name",
  id: "id",
};

// 监听过滤文本变化
watch(filterText, (val) => {
  if (treeRef.value) {
    treeRef.value.filter(val);
  }
});

// 节点过滤方法
const filterNode = (value, data) => {
  if (!value) return true;
  return data.name.toLowerCase().includes(value.toLowerCase());
};

// 节点点击事件
const onNodeClick = (data, node) => {
  if (data.id === props.currentDeptId) {
    return;
  }
  selectedNode.value = data;
};

// 显示部门用户
const showDeptUsers = async (deptId, deptName) => {
  selectedDeptId.value = deptId;
  selectedDeptName.value = deptName;
  await fetchUsers(deptId);
};

// 获取部门用户
const fetchUsers = async (deptId) => {
  loading.value = true;
  try {
    const res = await request.post("organization/users", {
      deptId,
    });
    if (res.code === 200) {
      users.value = res.data || [];
    }
  } catch (error) {
    console.error("获取用户失败:", error);
    ElMessage.error("获取用户失败");
  } finally {
    loading.value = false;
  }
};

// 用户点击事件
const onUserClick = (row) => {
  selectedUser.value = row;
};

// 选择用户
const selectUser = (row) => {
  selectedUser.value = row;
  emit("save", row);
  handleClose();
};

// 保存选择
const handleSave = () => {
  if (props.showUsers) {
    if (!selectedUser.value) {
      ElMessage.warning({
        message: "请选择用户",
        type: "warning",
      });
      return;
    }
    emit("save", selectedUser.value);
  } else {
    if (!selectedNode.value) {
      ElMessage.warning({
        message: "请选择上级部门",
        type: "warning",
      });
      return;
    }
    emit("save", selectedNode.value);
  }
  handleClose();
};

// 关闭对话框
const handleClose = () => {
  emit("update:visible", false);
  emit("close");
  // 重置状态
  filterText.value = "";
  selectedNode.value = null;
  selectedUser.value = null;
  users.value = [];
  selectedDeptId.value = null;
  selectedDeptName.value = "";
};

// 获取部门树数据
const fetchDeptTree = async () => {
  try {
    const res = await request.post("/admin/organization/get-dept-tree");
    if (res.code === 200) {
      deptTree.value = res.data || [];
    }
  } catch (error) {
    console.error("获取部门树失败:", error);
    ElMessage.error("获取部门树失败");
  }
};

// 组件挂载时获取数据
onMounted(async () => {
  await fetchDeptTree();
});
</script>

<style scoped>
.filter-tree {
  margin-top: 8px;
}

.tree-node-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.node-disabled {
  color: var(--td-text-color-placeholder);
  cursor: not-allowed;
}

.disabled-tip {
  font-size: 12px;
  color: var(--td-text-color-placeholder);
  margin-left: 8px;
}

.filter-tree :deep(.el-tree-node__content) {
  height: 36px;
  line-height: 36px;
}

.filter-tree
  :deep(
    .el-tree--highlight-current
      .el-tree-node.is-current
      > .el-tree-node__content
  ) {
  background-color: var(--brand-color);
  color: var(--td-text-color-anti);
}
</style>
