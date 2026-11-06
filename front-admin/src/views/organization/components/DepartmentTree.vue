<template>
  <el-tree
    style="max-width: 290px"
    :allow-drop="allowDrop"
    :allow-drag="allowDrag"
    :data="deptTree"
    draggable
    default-expand-all
    node-key="id"
    @node-click="handleNodeClick"
    @node-drag-start="handleDragStart"
    @node-drop="handleDrop"
    :expand-on-click-node="false"
    ref="treeRef"
  >
    <template #default="{ node, data }">
      <div class="tree-node-content">
        <div style="flex-grow: 1">
          {{ data.name }}
        </div>
        <div style="margin-left: auto; margin-right: 8px">
          <el-dropdown trigger="click" style="line-height: 40px">
            <div class="el-dropdown-link">
              <i class="iconfont x-gengduo"></i>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="handleRenameDept(node, data)">
                  修改名称
                </el-dropdown-item>
                <el-dropdown-item @click="handleAddSubDept(node, data)">
                  添加子部门
                </el-dropdown-item>
                <el-dropdown-item @click="handleSelectParentDept(node, data)">
                  调整上级部门
                </el-dropdown-item>
                <el-dropdown-item @click="handleSetManager(node, data)">
                  设置负责人
                </el-dropdown-item>
                <el-dropdown-item @click="handleDeleteDept(node, data)">
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
        <el-form label-width="70" style="max-width: 600px">
          <el-form-item label="公司名称">
            <el-input v-model="companyName" />
          </el-form-item>
          <el-form-item label="">
            <el-button type="primary" @click="saveCompanyName">
              保存
            </el-button>
          </el-form-item>
        </el-form>
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
  deptTree: {
    type: Array,
    default: () => [],
  },
});

// Emits
const emit = defineEmits(["node-click", "dept-updated"]);

// Refs
const treeRef = ref(null);
const companyName = ref("");

// 暴露内部ref给父组件
defineExpose({
  treeRef,
});

// 方法
const handleNodeClick = (data, node, event) => {
  emit("node-click", data, node, event);
};

const handleRenameDept = async (node, data) => {
  try {
    const { value: newName } = await ElMessageBox.prompt(
      "请输入新的部门名称",
      "修改部门名称",
      {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        inputValue: data.name,
        inputValidator: (value) => {
          if (!value || value.trim() === "") {
            return "部门名称不能为空";
          }
          return true;
        },
      },
    );

    // 调用API修改部门名称
    const res = await request.post("/admin/organization/update-dept", {
      data: {
        id: data.id,
        name: newName.trim(),
      },
    });

    if (res.code === 200) {
      ElMessage.success("修改成功");
      emit("dept-updated");
    }
  } catch (error) {
    if (error !== "cancel") {
      console.error("修改部门名称失败:", error);
      ElMessage.error("修改失败");
    }
  }
};

const handleAddSubDept = (node, data) => {
  emit("add-sub-dept", node, data);
};

const handleSelectParentDept = (node, data) => {
  emit("select-parent-dept", node, data);
};

const handleSetManager = (node, data) => {
  emit("set-manager", node, data);
};

const handleDeleteDept = async (node, data) => {
  try {
    await ElMessageBox.confirm(
      "确定要删除该部门吗？删除后该部门下的所有子部门也会被删除！",
      "警告",
      {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "danger",
      },
    );

    // 调用API删除部门
    const res = await request.post("/admin/organization/delete-dept", {
      data: { id: data.id },
    });

    if (res.code === 200) {
      ElMessage.success("删除成功");
      emit("dept-updated");
    }
  } catch (error) {
    if (error !== "cancel") {
      console.error("删除部门失败:", error);
      ElMessage.error("删除失败");
    }
  }
};

const saveCompanyName = async () => {
  if (!companyName.value || companyName.value.trim() === "") {
    ElMessage.warning("公司名称不能为空");
    return;
  }

  try {
    // 调用API创建公司
    const res = await request.post("/admin/organization/create-dept", {
      data: {
        name: companyName.value.trim(),
        pid: null,
      },
    });

    if (res.code === 200) {
      ElMessage.success("保存成功");
      emit("dept-updated");
    }
  } catch (error) {
    console.error("保存公司名称失败:", error);
    ElMessage.error("保存失败");
  }
};

const handleDragStart = (node, ev) => {
  console.log("drag start", node);
};

// 根级部门的父ID（后端 build_tree 将 pid 为 null / 0 均视为根节点）
const ROOT_PID = 0;

const normalizePid = (pid) => (pid === null || pid === undefined ? ROOT_PID : pid);

const handleDrop = async (draggedNode, dropNode, dropType) => {
  try {
    const draggedId = draggedNode.data.id;
    // node-drop 触发时 el-tree 已完成节点移动（draggedNode.parent 已被置空），
    // 因此按落点位置取调整后的同级节点顺序
    const container = dropType === "inner" ? dropNode : dropNode.parent;
    const siblings = (container?.childNodes || []).map((node) => node.data);
    if (!siblings.some((item) => item.id === draggedId)) return;

    const targetPid =
      dropType === "inner" ? dropNode.data.id : normalizePid(dropNode.data.pid);

    // 按新的同级顺序重算 sort（步长 10），避免相邻节点 sort 相同导致 ±1 失效
    const updates = siblings.map((item, index) => {
      const data = { id: item.id, sort: (index + 1) * 10 };
      if (item.id === draggedId && normalizePid(item.pid) !== targetPid) {
        data.pid = targetPid;
      }
      return { data, changed: item.id === draggedId || item.sort !== data.sort };
    });

    for (const { data, changed } of updates) {
      if (!changed) continue;
      const res = await request.post("/admin/organization/update-dept", { data });
      if (res.code !== 200) {
        throw new Error(res.message || "调整失败");
      }
    }

    ElMessage.success("调整成功");
    emit("dept-updated");
  } catch (error) {
    console.error("拖拽调整失败:", error);
    ElMessage.error("调整失败");
    emit("dept-updated");
  }
};

const allowDrop = (draggedNode, dropNode, type) => {
  // 不允许拖到自己的子节点中
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
  // 根节点不允许拖动
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

.empty-node {
  text-align: center;
}

:deep(.el-tree-node__content) {
  height: 40px;
  line-height: 40px;
}
</style>
