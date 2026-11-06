<template>
  <el-drawer :model-value="visible" :title="drawerTitle" size="900px"
    class="permission-group-dialog permission-group-drawer" destroy-on-close @update:model-value="handleVisibleChange"
    @open="handleOpen">
    <div class="dialog-toolbar">
      <div class="toolbar-left"></div>
      <el-button type="primary" :disabled="!menu" @click="handleAdd">
        <el-icon>
          <Plus />
        </el-icon>
        新建权限组
      </el-button>
    </div>

    <template v-if="groups.length">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="权限组" name="group">
          <el-table v-loading="loading" :data="groups" row-key="id" border stripe size="small" height="100%">
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column prop="title" label="权限组名称" min-width="150" show-overflow-tooltip />
            <el-table-column label="操作权限" width="90" align="center">
              <template #default="{ row }">{{ row.permissionCount || 0 }}</template>
            </el-table-column>
            <el-table-column label="字段权限" width="90" align="center">
              <template #default="{ row }">{{ row.fieldCount || 0 }}</template>
            </el-table-column>
            <el-table-column label="数据范围" width="90" align="center">
              <template #default="{ row }">{{ row.dataScopeCount || 0 }}</template>
            </el-table-column>
            <el-table-column label="绑定主体" width="90" align="center">
              <template #default="{ row }">{{ row.subjectCount || 0 }}</template>
            </el-table-column>
            <el-table-column label="状态" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">
                  {{ row.status === 1 ? "启用" : "禁用" }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <div class="cell-actions">
                  <el-tooltip content="操作权限" placement="top">
                    <el-link type="primary" underline="never" @click="openPermission(row)">
                      <el-icon>
                        <Key />
                      </el-icon>
                    </el-link>
                  </el-tooltip>
                  <el-tooltip content="字段权限" placement="top">
                    <el-link type="primary" underline="never" @click="openField(row)">
                      <el-icon>
                        <Grid />
                      </el-icon>
                    </el-link>
                  </el-tooltip>
                  <el-tooltip content="数据权限" placement="top">
                    <el-link type="primary" underline="never" @click="openDataScope(row)">
                      <el-icon>
                        <DataLine />
                      </el-icon>
                    </el-link>
                  </el-tooltip>
                  <el-tooltip content="绑定主体" placement="top">
                    <el-link type="primary" underline="never" @click="openSubject(row)">
                      <el-icon>
                        <User />
                      </el-icon>
                    </el-link>
                  </el-tooltip>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="操作权限" name="permission">
          <el-table v-loading="loading" :data="permissionRows" row-key="id" border size="small" height="100%">
            <el-table-column prop="title" label="权限组" width="180" show-overflow-tooltip />
            <el-table-column label="已授权权限点" min-width="360">
              <template #default="{ row }">
                <el-tag v-for="code in row.permissions" :key="code" size="small" effect="plain" class="code-tag">
                  {{ code }}
                </el-tag>
                <span v-if="!row.permissions.length" class="dialog-tip">未授权任何权限点</span>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="字段权限" name="field">
          <el-table v-loading="loading" :data="fieldRows" row-key="key" border size="small" height="100%">
            <el-table-column prop="group" label="权限组" width="180" show-overflow-tooltip />
            <el-table-column prop="module" label="模块" width="110" />
            <el-table-column prop="field" label="字段" min-width="140" show-overflow-tooltip />
            <el-table-column prop="visible" label="可见" width="80" align="center" />
            <el-table-column prop="editable" label="可编辑" width="90" align="center" />
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="数据范围" name="data">
          <el-table v-loading="loading" :data="scopeRows" row-key="key" border size="small" height="100%">
            <el-table-column prop="group" label="权限组" width="180" show-overflow-tooltip />
            <el-table-column prop="module" label="模块" width="110" />
            <el-table-column prop="scope" label="范围" min-width="140" />
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="主体绑定" name="subject">
          <el-table v-loading="loading" :data="subjectRows" row-key="key" border size="small" height="100%">
            <el-table-column prop="group" label="权限组" width="180" show-overflow-tooltip />
            <el-table-column prop="subjectTypeLabel" label="主体类型" width="110" />
            <el-table-column prop="subjectName" label="主体" min-width="180" show-overflow-tooltip />
            <el-table-column label="操作" width="80" align="center" fixed="right">
              <template #default="{ row }">
                <el-tooltip content="解绑" placement="top">
                  <el-link type="danger" underline="never" @click="handleDeleteSubject(row)">
                    <el-icon>
                      <Delete />
                    </el-icon>
                  </el-link>
                </el-tooltip>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </template>

    <div v-else class="placeholder">当前菜单下暂无可配置的权限组。</div>

    <template #footer>
      <el-button @click="handleVisibleChange(false)">关闭</el-button>
    </template>
  </el-drawer>

  <GroupFormDialog v-model:visible="formVisible" :group="currentGroup" :menu-options="menuOptions" menu-bound
    :loading="formSubmitting" @submit="handleSubmit" />

  <GroupPermissionDialog v-model:visible="permissionVisible" :group="currentGroup" />

  <GroupFieldDialog v-model:visible="fieldVisible" :group="currentGroup" />

  <GroupDataScopeDialog v-model:visible="dataScopeVisible" :group="currentGroup" />

  <GroupSubjectDialog v-model:visible="subjectVisible" :group="currentGroup" />
</template>

<script setup>
import { computed, watch, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Plus, Key, Grid, DataLine, User, Delete } from "@element-plus/icons-vue";
import GroupFormDialog from "./GroupFormDialog.vue";
import GroupPermissionDialog from "./GroupPermissionDialog.vue";
import GroupFieldDialog from "./GroupFieldDialog.vue";
import GroupDataScopeDialog from "./GroupDataScopeDialog.vue";
import GroupSubjectDialog from "./GroupSubjectDialog.vue";
import {
  DATA_SCOPE_OPTIONS,
  SUBJECT_TYPE_OPTIONS,
  createGroup,
  deleteGroupSubject,
  getGroupDetail,
  getGroupList,
  getMenuOptions,
} from "../permissionGroupApi";

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  // 所属菜单权限点编码（与路由 meta.permission 一致，如 nav:shop）
  menuCode: {
    type: String,
    default: "",
  },
  // 菜单名称（仅用于标题展示）
  menuTitle: {
    type: String,
    default: "",
  },
  // 业务模块（路由 meta 声明，优先于菜单权限点推导值）
  menuModule: {
    type: String,
    default: "",
  },
});

const emit = defineEmits(["update:visible"]);

// 数据范围 / 主体类型 的 value → label 映射
const SCOPE_LABELS = new Map(DATA_SCOPE_OPTIONS.map((item) => [item.value, item.label]));
const SUBJECT_TYPE_LABELS = new Map(SUBJECT_TYPE_OPTIONS.map((item) => [item.value, item.label]));

const loading = ref(false);
const activeTab = ref("group");
const menuOptions = ref([]);
const menu = ref(null);
const groups = ref([]);
// 各权限组明细（permissions / fields / scopes / subjects），支撑统计摘要与 4 个明细 Tab
const details = ref([]);
const currentGroup = ref(null);
const formVisible = ref(false);
const formSubmitting = ref(false);
const permissionVisible = ref(false);
const fieldVisible = ref(false);
const dataScopeVisible = ref(false);
const subjectVisible = ref(false);

// 业务模块：优先路由 meta 声明，其次菜单权限点推导值
const moduleName = computed(
  () => props.menuModule || (menu.value && menu.value.businessModule) || ""
);
const drawerTitle = computed(() => {
  const name = props.menuTitle || props.menuCode || "当前菜单";
  return `权限组配置 - ${name}`;
});

const permissionRows = computed(() =>
  details.value.map((item) => ({
    id: item.id,
    title: item.title,
    permissions: item.permissions,
  }))
);

const fieldRows = computed(() => {
  const rows = [];
  details.value.forEach((group) => {
    group.fields.forEach((field) => {
      const visible = Number(field.visible) === 1;
      rows.push({
        key: `${group.id}-${field.id}`,
        group: group.title,
        module: field.module,
        field: field.fieldLabel || field.field,
        visible: visible ? "是" : "否",
        editable: visible && Number(field.editable) === 1 ? "是" : "否",
      });
    });
  });
  return rows;
});

const scopeRows = computed(() => {
  const rows = [];
  details.value.forEach((group) => {
    group.scopes.forEach((scope) => {
      rows.push({
        key: `${group.id}-${scope.id}`,
        group: group.title,
        module: scope.module,
        scope: SCOPE_LABELS.get(scope.scope) || scope.scope,
      });
    });
  });
  return rows;
});

const subjectRows = computed(() => {
  const rows = [];
  details.value.forEach((group) => {
    group.subjects.forEach((subject) => {
      rows.push({
        key: `${group.id}-${subject.id}`,
        groupId: group.id,
        group: group.title,
        subjectType: subject.subjectType,
        subjectTypeLabel: SUBJECT_TYPE_LABELS.get(subject.subjectType) || subject.subjectType,
        subjectId: subject.subjectId,
        subjectName: subject.subjectName || subject.subjectCode || subject.subjectId,
      });
    });
  });
  return rows;
});

// 加载当前菜单及其下属权限组
const handleOpen = async () => {
  activeTab.value = "group";
  try {
    const menuRes = await getMenuOptions();
    menuOptions.value = menuRes.code === 200 ? menuRes.data || [] : [];
    menu.value = menuOptions.value.find((item) => item.code === props.menuCode) || null;
    if (!menu.value) {
      groups.value = [];
      details.value = [];
      ElMessage.warning(`菜单 ${props.menuCode || ""} 未关联可配置的权限组`);
      return;
    }
    await fetchGroups();
  } catch (error) {
    ElMessage.error("加载菜单权限组失败");
  }
};

const fetchGroups = async () => {
  if (!menu.value) {
    return;
  }
  loading.value = true;
  try {
    const res = await getGroupList({ page: 1, limit: 200, menuId: menu.value.id });
    if (res.code !== 200) {
      ElMessage.error(res.message || "获取权限组失败");
      return;
    }
    groups.value = res.data?.items || [];
    await fetchDetails();
  } finally {
    loading.value = false;
  }
};

// 逐组拉取明细（后端 get-group-detail 已聚合权限点 / 字段 / 数据范围 / 主体）
const fetchDetails = async () => {
  const items = groups.value || [];
  if (!items.length) {
    details.value = [];
    return;
  }
  details.value = await Promise.all(
    items.map(async (item) => {
      const empty = { id: item.id, title: item.title, permissions: [], fields: [], scopes: [], subjects: [] };
      try {
        const res = await getGroupDetail(item.id);
        if (res.code !== 200) {
          return empty;
        }
        const detail = res.data || {};
        return {
          id: item.id,
          title: item.title,
          permissions: (detail.permissions && detail.permissions.codes) || [],
          fields: detail.fields || [],
          scopes: detail.dataScopes || [],
          subjects: detail.subjects || [],
        };
      } catch (error) {
        return empty;
      }
    })
  );
};

const handleVisibleChange = (value) => {
  emit("update:visible", value);
};

const handleAdd = () => {
  if (!menu.value) {
    return;
  }
  currentGroup.value = { menuId: menu.value.id, module: moduleName.value };
  formVisible.value = true;
};

const openPermission = (row) => {
  currentGroup.value = { ...row };
  permissionVisible.value = true;
};

const openField = (row) => {
  currentGroup.value = { ...row };
  fieldVisible.value = true;
};

const openDataScope = (row) => {
  currentGroup.value = { ...row };
  dataScopeVisible.value = true;
};

const openSubject = (row) => {
  currentGroup.value = { ...row };
  subjectVisible.value = true;
};

// 解绑主体绑定列表中的单条记录
const handleDeleteSubject = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定解绑主体「${row.subjectName}」吗？解绑后该主体将不再享有此权限组。`,
      "提示",
      { confirmButtonText: "确定", cancelButtonText: "取消", type: "warning" },
    );
  } catch {
    return;
  }
  try {
    const res = await deleteGroupSubject(row.groupId, row.subjectType, row.subjectId);
    if (res.code === 200) {
      ElMessage.success("解绑成功");
      await fetchGroups();
    } else {
      ElMessage.error(res.message || "解绑失败");
    }
  } catch (error) {
    ElMessage.error("解绑失败，请稍后重试");
  }
};

const handleSubmit = async (payload) => {
  formSubmitting.value = true;
  try {
    const res = await createGroup(payload);
    if (res.code === 200) {
      ElMessage.success("创建成功");
      formVisible.value = false;
      await fetchGroups();
    } else {
      ElMessage.error(res.message || "创建失败");
    }
  } catch (error) {
    ElMessage.error("创建失败，请稍后重试");
  } finally {
    formSubmitting.value = false;
  }
};

// 子对话框关闭后刷新统计（权限点 / 字段 / 数据范围 / 主体的数量可能已变化）
watch([permissionVisible, fieldVisible, dataScopeVisible, subjectVisible], (values) => {
  if (values.some((value) => value)) {
    return;
  }
  if (props.visible && menu.value) {
    fetchGroups();
  }
});
</script>

<style>
@import "../style/permission_group.css";

.permission-group-dialog .toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>
