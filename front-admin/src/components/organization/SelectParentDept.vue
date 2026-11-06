<template>
  <el-dialog
    header="调整上级部门"
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
      </el-tree>
    </el-scrollbar>
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSave">确定</el-button>
    </template>
  </el-dialog>
</template>

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
});

// 定义组件事件
const emit = defineEmits(["update:visible", "save", "close"]);

// 响应式数据
const filterText = ref("");
const deptTree = ref([]);
const selectedNode = ref(null);
const treeRef = ref(null);

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

// 保存选择
const handleSave = () => {
  if (!selectedNode.value) {
    ElMessage.warning({
      message: "请选择上级部门",
      type: "warning",
    });
    return;
  }

  emit("save", selectedNode.value);
  handleClose();
};

// 关闭对话框
const handleClose = () => {
  emit("update:visible", false);
  emit("close");
  // 重置状态
  filterText.value = "";
  selectedNode.value = null;
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
