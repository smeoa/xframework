<template>
  <el-dialog title="权限分配" v-model="dialogVisible" width="800px" :show-close="false">
    <template #header>
      <span class="dialog-title">权限分配 - {{ roleName }}</span>
      <div class="dialog-header-actions">
        <el-button @click="handleCancel" title="关闭" text>
          <el-icon>
            <Close />
          </el-icon>
        </el-button>
      </div>
    </template>

    <el-alert v-if="isAdminRole" type="warning" :closable="false" show-icon class="permission-alert"
      title="该角色编码为 admin，后端按超级管理员直通全部权限，此处的授权不会影响其实际权限。" />

    <div class="permission-toolbar">
      <el-input v-model="keyword" placeholder="搜索权限名称或权限码" clearable class="permission-search">
        <template #prefix>
          <el-icon>
            <Search />
          </el-icon>
        </template>
      </el-input>
      <el-button @click="handleCheckAll">全选</el-button>
      <el-button @click="handleClearAll">清空</el-button>
      <span class="permission-count">已选 {{ checkedCount }} / {{ totalCount }}</span>
    </div>

    <el-scrollbar class="permission-body" v-loading="loading">
      <el-tree ref="treeRef" :data="permissionTree" node-key="id" show-checkbox check-strictly default-expand-all
        :expand-on-click-node="false" :props="treeProps" :filter-node-method="filterNode" @check="handleCheck">
        <template #default="{ data }">
          <span class="perm-node">
            <el-tag size="small" effect="plain" :type="tagType(data.type)">{{ typeLabel(data.type) }}</el-tag>
            <span class="perm-title">{{ data.title }}</span>
            <span class="perm-code">{{ data.code }}</span>
          </span>
        </template>
        <template #empty>
          <div class="empty-node">暂无权限数据</div>
        </template>
      </el-tree>
    </el-scrollbar>

    <template #footer>
      <el-button type="primary" :loading="saving" @click="handleSubmit">保存</el-button>
      <el-button @click="handleCancel">取消</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch, nextTick } from "vue";
import { Search, Close } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import request from "@/utils/request";

const API_ENDPOINTS = {
  PERMISSION_TREE: "/admin/organization/get-permission-tree",
  ROLE_PERMISSIONS: "/admin/organization/get-role-permissions",
  GRANT_ROLE_PERMISSIONS: "/admin/organization/grant-role-permissions",
};

// Props
const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  role: {
    type: Object,
    default: () => ({ id: null, name: "", code: "" }),
  },
});

// Emits
const emit = defineEmits(["update:visible"]);

// Local refs
const dialogVisible = ref(props.visible);
const treeRef = ref(null);
const permissionTree = ref([]);
const keyword = ref("");
const loading = ref(false);
const saving = ref(false);
const checkedCount = ref(0);
// 程序化设置勾选时暂停级联，避免与用户点击的级联逻辑互相触发
const suspendCheck = ref(false);

const treeProps = {
  label: "title",
  children: "children",
};

const roleName = computed(() => props.role?.name || "");
const isAdminRole = computed(() => props.role?.code === "admin");

// id -> 节点 映射，用于向上追溯父级
const nodeMap = computed(() => {
  const map = new Map();
  const walk = (nodes) => {
    (nodes || []).forEach((node) => {
      map.set(node.id, node);
      if (node.children && node.children.length) {
        walk(node.children);
      }
    });
  };
  walk(permissionTree.value);
  return map;
});

const totalCount = computed(() => nodeMap.value.size);

const typeLabel = (type) => {
  if (type === 0) return "分组";
  if (type === 1) return "菜单";
  return "操作";
};

const tagType = (type) => {
  if (type === 0) return "info";
  if (type === 1) return "warning";
  return "success";
};

// 收集全部子孙节点 id
const collectDescendantIds = (node) => {
  const ids = [];
  const walk = (nodes) => {
    (nodes || []).forEach((child) => {
      ids.push(child.id);
      walk(child.children);
    });
  };
  walk(node.children);
  return ids;
};

// 收集全部祖先节点 id
const collectAncestorIds = (node) => {
  const ids = [];
  let current = node;
  while (current && current.pid) {
    const parent = nodeMap.value.get(current.pid);
    if (!parent) break;
    ids.push(parent.id);
    current = parent;
  }
  return ids;
};

const syncCount = () => {
  const tree = treeRef.value;
  checkedCount.value = tree ? tree.getCheckedKeys().length : 0;
};

const filterNode = (value, data) => {
  if (!value) return true;
  const key = value.trim().toLowerCase();
  return (
    String(data.title || "").toLowerCase().includes(key) ||
    String(data.code || "").toLowerCase().includes(key)
  );
};

watch(keyword, (value) => {
  if (treeRef.value) {
    treeRef.value.filter(value);
  }
});

// 勾选联动：勾中则同时勾中祖先与子孙，取消则同时取消子孙
const handleCheck = (data) => {
  const tree = treeRef.value;
  if (!tree || suspendCheck.value) return;

  const ids = new Set(tree.getCheckedKeys());
  const isChecked = ids.has(data.id);

  suspendCheck.value = true;
  if (isChecked) {
    collectAncestorIds(data).forEach((id) => ids.add(id));
    collectDescendantIds(data).forEach((id) => ids.add(id));
  } else {
    collectDescendantIds(data).forEach((id) => ids.delete(id));
  }
  tree.setCheckedKeys([...ids]);
  suspendCheck.value = false;

  syncCount();
};

const handleCheckAll = () => {
  if (!treeRef.value) return;
  treeRef.value.setCheckedKeys([...nodeMap.value.keys()]);
  syncCount();
};

const handleClearAll = () => {
  if (!treeRef.value) return;
  treeRef.value.setCheckedKeys([]);
  syncCount();
};

// 加载权限树与角色已授权权限点
const loadData = async () => {
  if (!props.role?.id) return;

  loading.value = true;
  try {
    const [treeRes, roleRes] = await Promise.all([
      request.post(API_ENDPOINTS.PERMISSION_TREE, {}),
      request.post(API_ENDPOINTS.ROLE_PERMISSIONS, {
        data: { roleId: props.role.id },
      }),
    ]);

    if (treeRes.code === 200) {
      permissionTree.value = treeRes.data || [];
    } else {
      permissionTree.value = [];
      ElMessage.error(treeRes.message || "获取权限清单失败");
    }

    const grantedIds = roleRes.code === 200 ? roleRes.data?.permissionIds || [] : [];
    if (roleRes.code !== 200) {
      ElMessage.error(roleRes.message || "获取角色权限失败");
    }

    await nextTick();
    if (treeRef.value) {
      treeRef.value.setCheckedKeys(grantedIds);
    }
    syncCount();
  } catch (error) {
    console.error("加载角色权限失败:", error);
    ElMessage.error("加载角色权限失败，请稍后重试");
  } finally {
    loading.value = false;
  }
};

watch(
  () => props.visible,
  async (newVal) => {
    dialogVisible.value = newVal;
    if (newVal) {
      keyword.value = "";
      await loadData();
    }
  },
);

watch(dialogVisible, (newVal) => {
  emit("update:visible", newVal);
});

const handleSubmit = async () => {
  if (!props.role?.id) {
    ElMessage.warning("请先选择一个角色");
    return;
  }

  const permissionIds = treeRef.value ? treeRef.value.getCheckedKeys() : [];

  saving.value = true;
  try {
    const res = await request.post(API_ENDPOINTS.GRANT_ROLE_PERMISSIONS, {
      data: {
        roleId: props.role.id,
        permissionIds,
      },
    });

    if (res.code === 200) {
      ElMessage.success(`保存成功，共授权 ${permissionIds.length} 个权限点`);
      dialogVisible.value = false;
    } else {
      ElMessage.error(res.message || "保存失败");
    }
  } catch (error) {
    console.error("保存角色权限失败:", error);
    ElMessage.error("保存失败，请稍后重试");
  } finally {
    saving.value = false;
  }
};

const handleCancel = () => {
  dialogVisible.value = false;
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

.permission-alert {
  margin-bottom: 12px;
}

.permission-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.permission-search {
  max-width: 260px;
}

.permission-count {
  margin-left: auto;
  color: var(--td-text-color-placeholder, #909399);
  font-size: 13px;
}

.permission-body {
  height: 460px;
  border: 1px solid #eaeaea;
  border-radius: 4px;
  padding: 8px;
  box-sizing: border-box;
}

.perm-node {
  display: flex;
  align-items: center;
  gap: 8px;
  overflow: hidden;
}

.perm-title {
  color: var(--td-text-color-primary, #303133);
}

.perm-code {
  color: var(--td-text-color-placeholder, #909399);
  font-size: 12px;
}

.empty-node {
  text-align: center;
  padding: 20px;
  color: var(--td-text-color-placeholder, #909399);
}
</style>
