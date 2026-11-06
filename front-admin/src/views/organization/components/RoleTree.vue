<template>
  <el-tree style="max-width: 290px" :data="roleTree" default-expand-all node-key="id" :expand-on-click-node="false"
    highlight-current ref="roleTreeRef">
    <template #default="{ node, data }">
      <div class="tree-node-content">
        <div @click="handleRoleNodeClick(data, node, $event)" style="flex-grow: 1">
          {{ data.name }}
        </div>
        <div style="margin-left: auto; margin-right: 8px">
          <el-dropdown trigger="click" style="line-height: 40px">
            <div class="el-dropdown-link">
              <i class="iconfont x-gengduo"></i>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="handleRenameRole(node, data)">
                  修改名称
                </el-dropdown-item>
                <el-dropdown-item @click="handleAssignPermission(data)">
                  权限分配
                </el-dropdown-item>
                <el-dropdown-item @click="handleDeleteRole(node, data)">
                  删除
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </template>
    <template #empty>
      <div class="empty-node" style="text-align: center; padding: 20px">
        <el-button type="primary" @click="handleAddRole"> 添加角色 </el-button>
      </div>
    </template>
  </el-tree>
</template>

<script setup>
import { ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import request from "@/utils/request";

// Props
const props = defineProps({
  roleTree: {
    type: Array,
    default: () => [],
  },
});

// Emits
const emit = defineEmits(["node-click", "role-updated", "add-role", "assign-permission"]);

// Refs
const roleTreeRef = ref(null);

// 方法
const handleRoleNodeClick = (data, node, event) => {
  emit("node-click", data, node, event);
};

const handleAddRole = () => {
  emit("add-role");
};

const handleAssignPermission = (data) => {
  emit("assign-permission", data);
};



const handleRenameRole = async (node, data) => {
  try {
    const { value: newName } = await ElMessageBox.prompt(
      "请输入新的角色名称",
      "修改角色名称",
      {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        inputValue: data.name,
        inputValidator: (value) => {
          if (!value || value.trim() === "") {
            return "角色名称不能为空";
          }
          return true;
        },
      },
    );

    // 调用API修改角色名称
    const res = await request.post("/admin/organization/update-role", {
      data: {
        id: data.id,
        name: newName.trim(),
      },
    });

    if (res.code === 200) {
      ElMessage.success("修改成功");
      emit("role-updated");
    }
  } catch (error) {
    if (error !== "cancel") {
      console.error("修改角色名称失败:", error);
      ElMessage.error("修改失败");
    }
  }
};

const handleDeleteRole = async (node, data) => {
  try {
    await ElMessageBox.confirm("确定要删除该角色吗？删除后无法恢复！", "警告", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "danger",
    });

    const res = await request.post("/admin/organization/delete-role", {
      data: { id: data.id },
    });
    if (res.code === 200) {
      ElMessage.success("删除成功");
      emit("role-updated");
    }
  } catch (error) {
    if (error !== "cancel") {
      console.error("删除角色失败:", error);
      ElMessage.error("删除失败");
    }
  }
};
</script>

<style scoped>
.tree-node-content {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 0 8px;
}

:deep(.el-tree-node__content:hover) {
  background-color: #f5f7fa;
}

.empty-node {
  text-align: center;
  padding: 20px;
}

:deep(.el-tree-node__content) {
  height: 40px;
  line-height: 40px;
}

.empty-node {
  text-align: center;
  padding: 20px;
}
</style>
