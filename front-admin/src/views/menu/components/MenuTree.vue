<template>
  <el-tree
    style="max-width: 290px"
    :data="menuTree"
    draggable
    default-expand-all
    node-key="id"
    @node-click="handleNodeClick"
    @node-drop="handleDrop"
    :expand-on-click-node="false"
    :allow-drag="allowDrag"
    :allow-drop="allowDrop"
    ref="treeRef"
  >
    <template #default="{ node, data }">
      <div class="tree-node-content">
        <div style="flex-grow: 1">
          <el-icon v-if="data.icon" style="margin-right: 4px; vertical-align: middle;">
            <component :is="data.icon" />
          </el-icon>
          {{ data.name }}
        </div>
        <div style="margin-left: auto; margin-right: 8px">
          <el-dropdown trigger="click" style="line-height: 40px">
            <div class="el-dropdown-link">
              <i class="iconfont x-gengduo"></i>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="handleRename(node, data)">
                  修改名称
                </el-dropdown-item>
                <el-dropdown-item @click="handleAddChild(node, data)">
                  添加子菜单
                </el-dropdown-item>
                <el-dropdown-item @click="handleChangeParent(node, data)">
                  调整上级菜单
                </el-dropdown-item>
                <el-dropdown-item @click="handleDelete(node, data)">
                  删除
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </template>
    <template #empty>
      <div style="text-align: center; padding: 20px; color: var(--td-text-color-placeholder)">
        暂无菜单数据
      </div>
    </template>
  </el-tree>
</template>

<script setup>
import { ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import request from "@/utils/request";

const props = defineProps({
  menuTree: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(["node-click", "menu-updated"]);

const treeRef = ref(null);

defineExpose({ treeRef });

const handleNodeClick = (data) => {
  emit("node-click", data);
};

const handleRename = async (node, data) => {
  try {
    const { value: newName } = await ElMessageBox.prompt(
      "请输入新的菜单名称",
      "修改菜单名称",
      {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        inputValue: data.name,
        inputValidator: (value) => {
          if (!value || value.trim() === "") return "菜单名称不能为空";
          return true;
        },
      },
    );
    const res = await request.post("/admin/menu/update-menu", {
      data: { id: data.id, name: newName.trim() },
    });
    if (res.code === 200) {
      ElMessage.success("修改成功");
      emit("menu-updated");
    }
  } catch (error) {
    if (error !== "cancel") {
      console.error("修改菜单名称失败:", error);
      ElMessage.error("修改失败");
    }
  }
};

const handleAddChild = (node, data) => {
  emit("add-child-menu", data);
};

const handleChangeParent = (node, data) => {
  ElMessageBox.prompt(
    "请输入新的上级菜单ID（留空为顶级菜单）",
    "调整上级菜单",
    {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      inputPattern: /^\d*$/,
      inputErrorMessage: "请输入数字ID",
    },
  ).then(async ({ value }) => {
    try {
      const res = await request.post("/admin/menu/update-menu", {
        data: { id: data.id, pid: value ? parseInt(value) : null },
      });
      if (res.code === 200) {
        ElMessage.success("调整成功");
        emit("menu-updated");
      }
    } catch (error) {
      if (error !== "cancel") {
        console.error("调整上级菜单失败:", error);
        ElMessage.error("调整失败");
      }
    }
  }).catch(() => {});
};

const handleDelete = async (node, data) => {
  try {
    await ElMessageBox.confirm(
      "确定要删除该菜单吗？删除后该菜单下的所有子菜单也会被删除！",
      "警告",
      {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "danger",
      },
    );
    const res = await request.post("/admin/menu/delete-menu", {
      data: { id: data.id },
    });
    if (res.code === 200) {
      ElMessage.success("删除成功");
      emit("menu-updated");
    }
  } catch (error) {
    if (error !== "cancel") {
      console.error("删除菜单失败:", error);
      ElMessage.error("删除失败");
    }
  }
};

const handleDrop = async (draggedNode, dropNode, dropType) => {
  try {
    const data = { id: draggedNode.data.id };
    if (dropType === "inner") {
      data.pid = dropNode.data.id;
    } else {
      // before/after — sort within the same parent
      data.pid = dropNode.data.pid || null;
      data.sort = dropType === "before"
        ? (dropNode.data.sort || 0) - 1
        : (dropNode.data.sort || 0) + 1;
    }
    const res = await request.post("/admin/menu/update-menu", { data });
    if (res.code === 200) {
      ElMessage.success("调整成功");
      emit("menu-updated");
    } else {
      ElMessage.error("调整失败");
    }
  } catch (error) {
    console.error("拖拽调整失败:", error);
    ElMessage.error("调整失败");
  }
};

const allowDrop = (draggedNode, dropNode, type) => {
  if (type === "inner") {
    return !isChildOf(dropNode, draggedNode);
  }
  return true;
};

const isChildOf = (node, parentNode) => {
  if (!node.parent) return false;
  if (node.parent === parentNode) return true;
  return isChildOf(node.parent, parentNode);
};

const allowDrag = (node) => {
  return node.parent !== null;
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

:deep(.el-tree-node.is-current > .el-tree-node__content) {
  background-color: #ecf5ff;
  color: var(--td-text-color-brand);
}

:deep(.el-tree-node.is-current > .el-tree-node__content:hover) {
  background-color: #dbeafe;
}

:deep(.el-tree-node__content) {
  height: 40px !important;
  line-height: 40px !important;
}
</style>