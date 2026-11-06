<template>
  <el-dialog :model-value="visible" title="操作权限配置" width="720px" class="permission-group-dialog" destroy-on-close
    @update:model-value="handleVisibleChange" @open="handleOpen">
    <div class="dialog-toolbar">
      <el-input v-model="keyword" placeholder="搜索权限名称或权限码" clearable class="search-input">
        <template #prefix>
          <el-icon>
            <Search />
          </el-icon>
        </template>
      </el-input>
      <div class="toolbar-right">
        <el-button @click="handleCheckAll">全选</el-button>
        <el-button @click="handleClearAll">清空</el-button>
        <span class="dialog-tip">已选 {{ checkedCount }} 项</span>
      </div>
    </div>

    <div class="dialog-tip tip-block">
      权限组「{{ groupTitle }}」归属业务模块 {{ moduleLabel }}，可勾选该模块下的操作权限点；菜单准入已按权限组所属菜单自动绑定（绑定主体后即可访问该菜单）；勾选内容叠加在绑定主体的 RBAC 权限之上。
    </div>

    <div class="tree-wrap" v-loading="loading">
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
          <div class="empty-node">该模块暂无可用权限点</div>
        </template>
      </el-tree>
    </div>

    <template #footer>
      <el-button @click="handleVisibleChange(false)">取消</el-button>
      <el-button type="primary" :loading="saving" @click="handleSubmit">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch, nextTick } from "vue";
import { Search } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import {
  getGroupPermissions,
  getPermissionTree,
  grantGroupPermissions,
} from "../permissionGroupApi";

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  group: {
    type: Object,
    default: null,
  },
});

const emit = defineEmits(["update:visible"]);

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

const moduleName = computed(() => (props.group && props.group.module) || "");
const moduleLabel = computed(() => moduleName.value || "未指定");
const groupTitle = computed(() => (props.group && props.group.title) || "");

// id -> 节点 映射，用于向上追溯父级并校正历史勾选
const nodeMap = computed(() => {
  const map = new Map();
  const walk = (nodes) => {
    (nodes || []).forEach((node) => {
      map.set(node.id, node);
      walk(node.children);
    });
  };
  walk(permissionTree.value);
  return map;
});

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

// 仅保留与权限组业务模块一致的节点：
// 菜单准入（type=1）由权限组所属菜单自动维护，不在树上展示；
// 操作权限点按自身 module 判定，父级分组仅作结构承载
const pruneByModule = (nodes, module) => {
  const result = [];
  (nodes || []).forEach((node) => {
    if (Number(node.type) === 1) return;
    const children = pruneByModule(node.children, module);
    if (node.module === module || children.length) {
      result.push({ ...node, children });
    }
  });
  return result;
};

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
  checkedCount.value = treeRef.value ? treeRef.value.getCheckedKeys().length : 0;
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

const handleOpen = async () => {
  if (!props.group || !props.group.id) return;
  keyword.value = "";
  loading.value = true;
  try {
    const [treeRes, grantedRes] = await Promise.all([
      getPermissionTree(),
      getGroupPermissions(props.group.id),
    ]);

    if (treeRes.code === 200) {
      permissionTree.value = pruneByModule(treeRes.data || [], moduleName.value);
    } else {
      permissionTree.value = [];
      ElMessage.error(treeRes.message || "获取权限清单失败");
    }

    // 历史脏数据可能含跨模块权限点，按当前树节点校正，避免保存时报错
    const granted = grantedRes.code === 200 ? grantedRes.data?.permissionIds || [] : [];
    const validIds = granted.filter((id) => nodeMap.value.has(id));

    await nextTick();
    if (treeRef.value) {
      treeRef.value.setCheckedKeys(validIds);
    }
    syncCount();
  } catch (error) {
    ElMessage.error("加载操作权限失败");
  } finally {
    loading.value = false;
  }
};

const handleVisibleChange = (value) => {
  emit("update:visible", value);
};

const handleSubmit = async () => {
  if (!props.group || !props.group.id) {
    ElMessage.warning("请先选择权限组");
    return;
  }
  const permissionIds = treeRef.value ? treeRef.value.getCheckedKeys() : [];
  saving.value = true;
  try {
    const res = await grantGroupPermissions(props.group.id, permissionIds);
    if (res.code === 200) {
      ElMessage.success(`保存成功，共授权 ${permissionIds.length} 个权限点`);
      emit("update:visible", false);
    } else {
      ElMessage.error(res.message || "保存失败");
    }
  } catch (error) {
    ElMessage.error("保存失败，请稍后重试");
  } finally {
    saving.value = false;
  }
};
</script>
