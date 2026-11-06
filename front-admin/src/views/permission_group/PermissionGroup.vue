<template>
  <el-card class="permission-group-card">
    <template #header>
      <div class="card-header">
        <div class="header-actions">
          <el-button @click="fetchData">
            <el-icon>
              <Refresh />
            </el-icon>
            刷新
          </el-button>
        </div>
        <div class="header-filters">
          <el-input v-model="keyword" placeholder="搜索名称或编码" clearable class="search-input"
            @keyup.enter="handleSearch">
            <template #prefix>
              <el-icon>
                <Search />
              </el-icon>
            </template>
          </el-input>
          <el-select v-model="filterMenuId" placeholder="所属菜单" clearable class="filter-select" @change="handleSearch">
            <el-option v-for="menu in menuOptions" :key="menu.id" :label="menu.title" :value="menu.id" />
          </el-select>
          <el-select v-model="filterModule" placeholder="业务模块" clearable class="filter-select" @change="handleSearch">
            <el-option v-for="item in moduleOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
          <el-select v-model="filterStatus" placeholder="状态" clearable class="filter-select" @change="handleSearch">
            <el-option label="启用" :value="1" />
            <el-option label="禁用" :value="0" />
          </el-select>
          <el-button type="primary" @click="handleSearch">
            <el-icon>
              <Search />
            </el-icon>
            搜索
          </el-button>
        </div>
      </div>
    </template>

    <el-table v-loading="loading" :data="tableData" row-key="id" border stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="title" label="权限组名称" min-width="150" show-overflow-tooltip />
      <el-table-column label="所属菜单" min-width="130" show-overflow-tooltip>
        <template #default="{ row }">
          <span>{{ row.menuTitle || "-" }}</span>
          <el-tag v-if="row.menuCode" size="small" type="info" class="menu-code-tag">{{ row.menuCode }}</el-tag>
        </template>
      </el-table-column>
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
      <el-table-column prop="sort" label="排序" width="70" align="center" />
      <el-table-column label="状态" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">
            {{ row.status === 1 ? "启用" : "禁用" }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" min-width="140" show-overflow-tooltip />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <div class="cell-actions">
            <el-tooltip content="操作权限" placement="top">
              <span v-permission="'org:role:grant'">
                <el-link type="primary" underline="never" @click="openPermission(row)">
                  <el-icon>
                    <Key />
                  </el-icon>
                </el-link>
              </span>
            </el-tooltip>
            <el-tooltip content="字段权限" placement="top">
              <span v-permission="'org:role:grant'">
                <el-link type="primary" underline="never" @click="openField(row)">
                  <el-icon>
                    <Grid />
                  </el-icon>
                </el-link>
              </span>
            </el-tooltip>
            <el-tooltip content="数据权限" placement="top">
              <span v-permission="'org:role:grant'">
                <el-link type="primary" underline="never" @click="openDataScope(row)">
                  <el-icon>
                    <DataLine />
                  </el-icon>
                </el-link>
              </span>
            </el-tooltip>
            <el-tooltip content="绑定主体" placement="top">
              <span v-permission="'org:role:grant'">
                <el-link type="primary" underline="never" @click="openSubject(row)">
                  <el-icon>
                    <User />
                  </el-icon>
                </el-link>
              </span>
            </el-tooltip>
            <el-tooltip content="编辑" placement="top">
              <span v-permission="'org:role:grant'">
                <el-link type="primary" underline="never" @click="handleEdit(row)">
                  <el-icon>
                    <Edit />
                  </el-icon>
                </el-link>
              </span>
            </el-tooltip>
            <el-tooltip content="删除" placement="top">
              <span v-permission="'org:role:grant'">
                <el-link type="danger" underline="never" @click="handleDelete(row)">
                  <el-icon>
                    <Delete />
                  </el-icon>
                </el-link>
              </span>
            </el-tooltip>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-wrap">
      <el-pagination :current-page="currentPage" :page-size="pageSize" :page-sizes="PAGE_SIZES" :total="total"
        layout="total, sizes, prev, pager, next, jumper" @size-change="handleSizeChange"
        @current-change="handleCurrentChange" />
    </div>
  </el-card>

  <GroupFormDialog v-model:visible="formVisible" :group="currentGroup" :menu-options="menuOptions"
    :loading="formSubmitting" @submit="handleSubmit" />

  <GroupPermissionDialog v-model:visible="permissionVisible" :group="currentGroup" />

  <GroupFieldDialog v-model:visible="fieldVisible" :group="currentGroup" />

  <GroupDataScopeDialog v-model:visible="dataScopeVisible" :group="currentGroup" />

  <GroupSubjectDialog v-model:visible="subjectVisible" :group="currentGroup" />
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Search, Refresh, Key, Grid, DataLine, User, Edit, Delete } from "@element-plus/icons-vue";
import GroupFormDialog from "./components/GroupFormDialog.vue";
import GroupPermissionDialog from "./components/GroupPermissionDialog.vue";
import GroupFieldDialog from "./components/GroupFieldDialog.vue";
import GroupDataScopeDialog from "./components/GroupDataScopeDialog.vue";
import GroupSubjectDialog from "./components/GroupSubjectDialog.vue";
import {
  createGroup,
  deleteGroup,
  getGroupList,
  getMenuOptions,
  updateGroup,
} from "./permissionGroupApi";

const PAGE_SIZES = [20, 50, 100];
const DEFAULT_PAGE_SIZE = 20;

const loading = ref(false);
const tableData = ref([]);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(DEFAULT_PAGE_SIZE);
const keyword = ref("");
const filterMenuId = ref(null);
const filterModule = ref(null);
const filterStatus = ref(null);

const menuOptions = ref([]);
const currentGroup = ref(null);

// 业务模块筛选项（由菜单选项推导去重）
const moduleOptions = computed(() => {
  const modules = new Set();
  menuOptions.value.forEach((menu) => {
    if (menu.businessModule) {
      modules.add(menu.businessModule);
    }
  });
  return Array.from(modules).map((value) => ({ value, label: value }));
});

const formVisible = ref(false);
const formSubmitting = ref(false);
const permissionVisible = ref(false);
const fieldVisible = ref(false);
const dataScopeVisible = ref(false);
const subjectVisible = ref(false);

const fetchMenuOptions = async () => {
  try {
    const res = await getMenuOptions();
    if (res.code === 200) {
      menuOptions.value = res.data || [];
    }
  } catch (error) {
    ElMessage.error("获取菜单选项失败");
  }
};

const fetchData = async () => {
  loading.value = true;
  try {
    const res = await getGroupList({
      page: currentPage.value,
      limit: pageSize.value,
      keyword: keyword.value,
      menuId: filterMenuId.value,
      module: filterModule.value,
      status: filterStatus.value,
    });
    if (res.code === 200) {
      tableData.value = res.data?.items || [];
      total.value = res.data?.total || 0;
    } else {
      ElMessage.error(res.message || "获取权限组列表失败");
    }
  } catch (error) {
    ElMessage.error("获取权限组列表失败");
  } finally {
    loading.value = false;
  }
};

const handleSearch = () => {
  currentPage.value = 1;
  fetchData();
};

const handleSizeChange = (val) => {
  pageSize.value = val;
  fetchData();
};

const handleCurrentChange = (val) => {
  currentPage.value = val;
  fetchData();
};

const handleEdit = (row) => {
  currentGroup.value = { ...row };
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

// 4 个配置弹窗全部关闭后刷新列表（权限点 / 字段 / 主体的数量可能已变化）
watch([permissionVisible, fieldVisible, dataScopeVisible, subjectVisible], (values) => {
  if (values.some((value) => value)) {
    return;
  }
  fetchData();
});

const handleSubmit = async (payload) => {
  formSubmitting.value = true;
  try {
    const res = payload.id ? await updateGroup(payload) : await createGroup(payload);
    if (res.code === 200) {
      ElMessage.success(payload.id ? "更新成功" : "创建成功");
      formVisible.value = false;
      await fetchData();
    } else {
      ElMessage.error(res.message || "保存失败");
    }
  } catch (error) {
    ElMessage.error("保存失败，请稍后重试");
  } finally {
    formSubmitting.value = false;
  }
};

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定删除权限组「${row.title}」吗？删除后其权限配置与用户激活记录将一并清除。`,
      "提示",
      { confirmButtonText: "确定", cancelButtonText: "取消", type: "warning" },
    );
  } catch {
    return;
  }
  try {
    const res = await deleteGroup(row.id);
    if (res.code === 200) {
      ElMessage.success("删除成功");
      await fetchData();
    } else {
      ElMessage.error(res.message || "删除失败");
    }
  } catch (error) {
    ElMessage.error("删除失败，请稍后重试");
  }
};

onMounted(() => {
  fetchMenuOptions();
  fetchData();
});
</script>

<style>
@import "./style/permission_group.css";
</style>
