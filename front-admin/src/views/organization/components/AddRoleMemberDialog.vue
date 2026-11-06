<template>
  <el-dialog title="添加成员" v-model="dialogVisible" width="800px" :show-close="false">
    <template #header>
      <span class="dialog-title">添加成员</span>
      <div class="dialog-header-actions">
        <el-button @click="handleCancel" title="关闭" text>
          <el-icon>
            <Close />
          </el-icon>
        </el-button>
      </div>
    </template>
    <!-- 已选成员标签 -->
    <div class="selected-tags">
      <el-tag v-for="user in selectedUsers" :key="user.id" closable @close="removeSelectedUser(user)"
        style="margin-right: 8px">
        <span class="tag-avatar" :style="{ backgroundColor: getAvatarColor(user.name) }">{{ user.name.charAt(0)
          }}</span>
        {{ user.name }}
      </el-tag>
    </div>

    <!-- 搜索框 -->
    <el-input v-model="searchKeyword" placeholder="搜索(多个关键词用空格隔开)" style="margin: 16px 20px 8px 20px;width: 760px;"
      clearable>
      <template #prefix>
        <el-icon>
          <Search />
        </el-icon>
      </template>
    </el-input>

    <!-- 左右分栏布局 -->
    <div class="user-select-container" style="display: flex; gap: 20px; height: 400px">
      <!-- 左侧：部门树 -->
      <div class="all-users" style="
          flex: 1;
          border: 1px solid #eaeaea;
          border-radius: 4px;
          overflow: hidden;
          display: flex;
          flex-direction: column;
        ">
        <!-- 全部成员选项 -->
        <div class="all-members-option" :class="{ active: selectedDeptIds.length === 0 }" @click="clearDeptSelection"
          style="
            padding: 12px;
            cursor: pointer;
            border-bottom: 1px solid #eaeaea;
          ">
          全部成员
        </div>

        <!-- 部门树 -->
        <el-scrollbar style="flex: 1">
          <div class="dept-tree-container" style="padding: 8px">
            <el-tree :data="deptTree" node-key="id" default-expand-all @node-click="handleDeptClick"
              :expand-on-click-node="false" :props="{
                children: 'children',
                label: 'name',
              }" highlight-current check-strictly ref="deptTreeRef">
              <template #default="{ node, data }">
                <span class="dept-node" @click.stop>
                  <span class="dept-icon" style="margin-right: 4px">📁</span>
                  {{ node.label }}
                </span>
              </template>
            </el-tree>
          </div>
        </el-scrollbar>
      </div>

      <!-- 右侧：成员列表 -->
      <div class="selected-users" style="
          flex: 1;
          border: 1px solid #eaeaea;
          border-radius: 4px;
          overflow: hidden;
          display: flex;
          flex-direction: column;
        ">
        <div class="section-header" style="
            padding: 6px 16px 6px 16px !important;
            border-bottom: 1px solid #eaeaea;
            font-weight: 500;
            display: flex;
            justify-content: space-between;
            align-items: center;
          ">
          <span>已选 {{ selectedUsers.length }}/{{ total }}</span>
          <el-checkbox v-model="selectAll" style="margin: 0"> </el-checkbox>
        </div>
        <el-scrollbar style="flex: 1">
          <div class="user-list">
            <div class="user-item" v-for="user in displayUsers" :key="user.id" @click="toggleUserSelection(user)">
              <div class="user-info">
                <span class="user-avatar" :style="{ backgroundColor: getAvatarColor(user.name) }">{{ user.name.charAt(0)
                  }}</span>
                <div class="user-details">
                  <div class="user-name">{{ user.name }}</div>
                </div>
              </div>
              <el-checkbox v-model="userSelectedMap[user.id]" @change="(val) => handleUserCheckboxChange(val, user)" />
            </div>
            <div class="empty-state" v-if="displayUsers.length === 0">
              暂无成员
            </div>
          </div>
        </el-scrollbar>
      </div>
    </div>
    <template #footer>
      <el-button type="primary" @click="handleConfirm">确定</el-button>
      <el-button @click="dialogVisible = false">取消</el-button>      
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, computed, nextTick } from "vue";
import { Search } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import request from "@/utils/request";

const deptTreeRef = ref(null);
// Props
const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  roleId: {
    type: [Number, String],
    default: null,
  },
  availableUsers: {
    type: Array,
    default: () => [],
  },
  deptTree: {
    type: Array,
    default: () => [],
  },
  total: {
    type: Number,
    default: 0,
  },
});

// Emits
const emit = defineEmits(["update:visible", "selection-change", "confirm", "add-success"]);

// Local refs
const dialogVisible = ref(props.visible);
const selectedUsers = ref([]);
const searchKeyword = ref("");
const selectedDeptIds = ref([]);
const userSelectedMap = ref({});

// 计算过滤后的用户列表
const filteredUsers = computed(() => {
  let users = [...props.availableUsers];

  // 按部门过滤
  if (selectedDeptIds.value.length > 0) {
    users = users.filter((user) => {
      // 确保类型一致
      return selectedDeptIds.value.some(deptId =>
        String(deptId) === String(user.deptId)
      );
    });
  }

  // 按搜索关键词过滤
  if (searchKeyword.value.trim()) {
    const keywords = searchKeyword.value
      .trim()
      .split(" ")
      .filter((k) => k);
    users = users.filter((user) => {
      return keywords.some((keyword) => {
        return (
          user.name.includes(keyword) ||
          user.username.includes(keyword) ||
          user.deptName.includes(keyword)
        );
      });
    });
  }

  return users;
});

// 计算要显示的用户列表（右侧）
const displayUsers = computed(() => {
  return filteredUsers.value;
});

// 计算全选状态
const selectAll = computed({
  get: () => {
    if (filteredUsers.value.length === 0) return false;
    return filteredUsers.value.every((user) => {
      return userSelectedMap.value[user.id];
    });
  },
  set: (val) => {
    handleSelectAll(val);
  },
});

// Watch for props changes
watch(
  () => props.visible,
  (newVal) => {
    dialogVisible.value = newVal;
  },
);

// Watch for dialogVisible changes
watch(dialogVisible, (newVal) => {
  emit("update:visible", newVal);
  if (!newVal) {
    selectedUsers.value = [];
  }
});

// Watch for filteredUsers changes
watch(
  filteredUsers,
  (newUsers) => {
    // 确保userSelectedMap中包含所有当前显示的用户
    const currentMap = { ...userSelectedMap.value };
    newUsers.forEach((user) => {
      if (currentMap[user.id] === undefined) {
        currentMap[user.id] = false;
      }
    });
    // 使用扩展运算符确保Vue能够检测到变化
    userSelectedMap.value = { ...currentMap };
  },
  { deep: true },
);

// Watch for selectedUsers changes
watch(
  selectedUsers,
  (newUsers) => {
    // 更新userSelectedMap以反映最新的选中状态
    const newMap = { ...userSelectedMap.value };
    // 先将所有用户设置为未选中
    Object.keys(newMap).forEach((key) => {
      newMap[key] = false;
    });
    // 再将选中的用户设置为选中
    newUsers.forEach((user) => {
      newMap[user.id] = true;
    });
    // 使用扩展运算符确保Vue能够检测到变化
    userSelectedMap.value = { ...newMap };
  },
  { deep: true },
);

// Methods
const handleConfirm = async () => {
  if (selectedUsers.value.length === 0) {
    ElMessage.warning("请至少选择一个用户");
    return;
  }

  if (props.roleId === null || props.roleId === undefined) {
    ElMessage.warning("请先选择一个角色");
    return;
  }

  try {
    const userIds = selectedUsers.value.map(user => user.id);
    const res = await request.post("/admin/organization/add-members", {
      data: {
        roleId: props.roleId,
        userIds: userIds
      }
    });

    if (res.code === 200) {
      ElMessage.success(`成功添加 ${selectedUsers.value.length} 个成员`);
      emit("add-success");
      dialogVisible.value = false;
    } else {
      ElMessage.error(`添加失败: ${res.message || "未知错误"}`);
    }
  } catch (error) {
    console.error("添加成员失败:", error);
    ElMessage.error("添加失败，请稍后重试");
  }
};

// 生成头像颜色
const getAvatarColor = (name) => {
  const colors = [
    "var(--brand-color)",
    "#2BA471",
    "#E37318",
    "#D54941",
    "#909399",
    "#722ED1",
    "#13C2C2",
    "#FAAD14",
    "#F7BA2A",
    "#52C41A",
  ];
  let sum = 0;
  for (let i = 0; i < name.length; i++) {
    sum += name.charCodeAt(i);
  }
  return colors[sum % colors.length];
};

// 切换用户选择状态
const toggleUserSelection = (user) => {
  const index = selectedUsers.value.findIndex((u) => u.id === user.id);
  if (index > -1) {
    selectedUsers.value.splice(index, 1);
    userSelectedMap.value = {
      ...userSelectedMap.value,
      [user.id]: false,
    };
  } else {
    selectedUsers.value.push(user);
    userSelectedMap.value = {
      ...userSelectedMap.value,
      [user.id]: true,
    };
  }
  emit("selection-change", selectedUsers.value);
};

// 处理复选框变化
const handleUserCheckboxChange = (val, user) => {
  const index = selectedUsers.value.findIndex((u) => u.id === user.id);
  if (val && index === -1) {
    selectedUsers.value.push(user);
  } else if (!val && index > -1) {
    selectedUsers.value.splice(index, 1);
  }
  userSelectedMap.value = {
    ...userSelectedMap.value,
    [user.id]: val,
  };
  emit("selection-change", selectedUsers.value);
};

// 从已选列表中移除用户
const removeSelectedUser = (user) => {
  const index = selectedUsers.value.findIndex((u) => u.id === user.id);
  if (index > -1) {
    selectedUsers.value.splice(index, 1);
    userSelectedMap.value = {
      ...userSelectedMap.value,
      [user.id]: false,
    };
    emit("selection-change", selectedUsers.value);
  }
};

// 清除部门选择
const clearDeptSelection = () => {
  selectedDeptIds.value = [];
  // 清空部门树的选中状态
  if (deptTreeRef.value) {
    deptTreeRef.value.setCurrentKey(null);
  }
};

// 处理全选
const handleSelectAll = (val) => {
  if (val) {
    // 全选当前过滤后的所有用户
    const filteredIds = filteredUsers.value.map((user) => user.id);
    // 先移除当前过滤后的用户，避免重复
    selectedUsers.value = selectedUsers.value.filter(
      (user) => !filteredIds.includes(user.id),
    );
    // 再添加所有过滤后的用户
    selectedUsers.value.push(...filteredUsers.value);
    // 更新userSelectedMap
    const newMap = { ...userSelectedMap.value };
    filteredUsers.value.forEach((user) => {
      newMap[user.id] = true;
    });
    userSelectedMap.value = newMap;
  } else {
    // 取消全选当前过滤后的所有用户
    const filteredIds = filteredUsers.value.map((user) => user.id);
    selectedUsers.value = selectedUsers.value.filter(
      (user) => !filteredIds.includes(user.id),
    );
    // 更新userSelectedMap
    const newMap = { ...userSelectedMap.value };
    filteredUsers.value.forEach((user) => {
      newMap[user.id] = false;
    });
    userSelectedMap.value = newMap;
  }
  emit("selection-change", selectedUsers.value);
};

// 处理部门点击
const handleDeptClick = (data) => {
  // 切换部门选择状态
  const index = selectedDeptIds.value.findIndex((id) => id === data.id);
  if (index > -1) {
    selectedDeptIds.value.splice(index, 1);
    // 清空部门树的选中状态
    if (deptTreeRef.value) {
      deptTreeRef.value.setCurrentKey(null);
    }
  } else {
    // 清空其他部门选择，只选择当前点击的部门
    selectedDeptIds.value = [data.id];
  }
};

// 处理取消
const handleCancel = () => {
  dialogVisible.value = false;
  // 清空选择
  selectedUsers.value = [];
  userSelectedMap.value = {};
  searchKeyword.value = "";
  selectedDeptIds.value = [];
  // 清空部门树的选中状态
  if (deptTreeRef.value) {
    deptTreeRef.value.setCurrentKey(null);
  }
};
</script>

<style scoped>
.dialog-title {
  font-size: 16px;
  line-height: 24px;
}

.dialog-header-actions {
  gap: 8px;
  float: right;
}

.selected-tags {
  margin-bottom: 0px;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
  flex-wrap: wrap;
  display: flex;
  min-height: 90px;
}

.tag-avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background-color: #909399;
  color: var(--td-text-color-anti);
  font-size: 12px;
  margin-right: 6px;
}

.el-tag {
  width: 146px;
  margin-bottom: 8px !important;
  text-align: left;
  justify-content: flex-start;
  height: 28px;
  position: relative;
  background-color: #e3e3e3 !important;
  color: var(--td-text-color-primary);
}

:deep(.el-tag button) {
  position: absolute;
  right: 2px;
  color: var(--td-text-color-primary);
}

:deep(.el-tag button:hover) {
  position: absolute;
  right: 2px;
  color: var(--td-text-color-primary);
  background-color: #f9f3f3 !important;
}

:deep(.el-tag__content) {
  width: 93px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.el-tag__content {
  text-align: left;
  width: 100%;
  display: inline-block;
}

.user-select-container {
  margin: 16px 20px;
}

/* 全部成员选项样式 */
.all-members-option {
  transition: all 0.2s;
}

.all-members-option:hover {
  background-color: #f5f7fa;
}

.all-members-option.active {
  background-color: #ecf5ff;
  color: var(--td-text-color-brand);
  font-weight: 500;
}

/* 部门树样式 */
.dept-tree-container {
  padding: 8px 0;
}

.dept-node {
  display: block;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.dept-node:hover {
  background-color: #f5f7fa;
}

/* 成员列表样式 */
.user-list {
  padding: 8px 0;
}

.user-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  transition: background-color 0.2s;
}

.user-item:hover {
  background-color: #f5f7fa;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.user-avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  color: var(--td-text-color-anti);
  font-size: 12px;
  font-weight: 500;
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--td-text-color-primary);
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--td-text-color-placeholder);
  font-size: 14px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

/* 确保滚动条样式一致 */
:deep(.el-scrollbar__wrap) {
  overflow-x: hidden;
}
</style>
