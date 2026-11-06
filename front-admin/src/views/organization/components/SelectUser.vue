<template>
  <el-dialog
    :title="dialogTitle"
    v-model="dialogVisible"
    width="700px"
    style="min-height: 500px"
    @close="handleClose"
  >
    <el-input
      placeholder="输入关键字进行过滤"
      v-model="filterText"
      style="margin-bottom: 20px"
      clearable
    >
    </el-input>
    <el-scrollbar style="height: 400px">
      <!-- 用户列表 -->
      <div class="user-list">
        <h4 style="margin: 8px 0">{{ selectedDeptName }} - 用户列表</h4>
        <el-table
          v-loading="loading"
          :data="filteredUsers"
          style="width: 100%"
          @row-click="onUserClick"
        >
          <el-table-column prop="name" label="姓名" width="120" />
          <el-table-column prop="phone" label="手机" width="150" />
          <el-table-column prop="email" label="邮箱" />
          <el-table-column prop="username" label="用户名" width="120" />
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
  </el-dialog>
</template>

<style scoped>
.select-user-dialog {
  .el-dialog__body {
    padding: 20px;
  }
}

.user-list {
  width: 100%;
}
</style>

<script setup>
import { ref, computed, watch } from "vue";
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
const selectedUser = ref(null);
const users = ref([]);
// 表格加载状态
const loading = ref(false);
const selectedDeptId = ref(null);
const selectedDeptName = ref("");

// 过滤后的用户列表
const filteredUsers = computed(() => {
  if (!filterText.value) return users.value;
  return users.value.filter((user) => {
    return (
      user.name?.toLowerCase().includes(filterText.value.toLowerCase()) ||
      user.phone?.toLowerCase().includes(filterText.value.toLowerCase()) ||
      user.email?.toLowerCase().includes(filterText.value.toLowerCase()) ||
      user.username?.toLowerCase().includes(filterText.value.toLowerCase())
    );
  });
});

// 对话框标题
const dialogTitle = computed(() => props.title);

// 使用computed属性实现v-model双向绑定
const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit("update:visible", value),
});

// 监听对话框显示状态，自动显示当前部门的用户列表
watch(
  () => props.visible,
  async (newVal) => {
    if (
      newVal &&
      props.showUsers &&
      props.currentDeptId &&
      props.currentDeptName
    ) {
      // 当打开对话框且需要显示用户，且有当前部门信息时，自动加载该部门的用户
      selectedDeptId.value = props.currentDeptId;
      selectedDeptName.value = props.currentDeptName;
      await fetchUsers(props.currentDeptId);
    }
  },
);

// 获取部门用户
const fetchUsers = async (deptId) => {
  loading.value = true;
  try {
    const res = await request.post("/admin/organization/get-user-list", {
      data: {
        deptId: deptId,
      },
    });
    if (res.code === 200) {
      users.value = res.data?.items || [];
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
  if (!selectedUser.value) {
    ElMessage.warning({
      message: "请选择用户",
      type: "warning",
    });
    return;
  }
  emit("save", selectedUser.value);
  handleClose();
};

// 关闭对话框
const handleClose = () => {
  emit("update:visible", false);
  emit("close");
  // 重置状态
  filterText.value = "";
  selectedUser.value = null;
  users.value = [];
  selectedDeptId.value = null;
  selectedDeptName.value = "";
};
</script>
