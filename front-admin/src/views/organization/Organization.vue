<template>
  <el-container class="organization-container">
    <el-aside width="240px" class="organization-aside">
      <el-card class="org-aside-card">
        <template #header>
          <div class="org-tab-header">
            <el-segmented
              v-model="activeTab"
              :options="['部门', '角色']"
              @change="handleTabChange"
            />
          </div>
        </template>
        <!-- 部门树 -->
        <DepartmentTree
          v-if="activeTab === '部门'"
          :dept-tree="deptTree"
          @node-click="handleNodeClick"
          @dept-updated="handleDeptUpdated"
          @add-sub-dept="handleAddSubDept"
          @select-parent-dept="handleSelectParentDept"
          @set-manager="handleSetManager"
          ref="deptTreeRef"
        />

        <!-- 角色树 -->
        <RoleTree
          v-else-if="activeTab === '角色'"
          :role-tree="roleTree"
          @node-click="handleRoleNodeClick"
          @role-updated="handleRoleUpdated"
          @add-role="handleAddRole"
          @assign-permission="handleAssignPermission"
        />
      </el-card>
    </el-aside>
    <el-main class="org-main">
      <el-card class="org-card"
        :class="{ 'is-filter-open': activeTab === '部门' && showAdvancedSearch }">
        <template #header>
          <div v-if="activeTab === '部门'">
            <div v-if="selectedRows.length === 0" class="card-header">
              <span>
                <el-button
                  type="primary"
                  v-permission="'org:user:create'"
                  @click="handleAdd"
                  class="action-btn"
                >
                  <el-icon>
                    <Plus />
                  </el-icon>
                  新增用户
                </el-button>
                <el-button
                  type="primary"
                  v-permission="'org:user:import'"
                  @click="handleImport"
                  class="action-btn"
                >
                  <i class="iconfont x-daoru"></i>
                  导入
                </el-button>
                <el-button
                  type="primary"
                  v-permission="'org:user:export'"
                  @click="handleExportBatch"
                  class="action-btn"
                >
                  <i class="iconfont x-daochu"></i>
                  导出
                </el-button>
                <el-button
                  type="danger"
                  v-permission="'org:user:delete'"
                  @click="handleDeleteBatch"
                  class="action-btn"
                >
                  <i class="iconfont x-shanchu"></i>
                  删除
                </el-button>
              </span>
              <div class="header-actions">
                <el-input
                  v-model="keyword"
                  placeholder="搜索数据"
                  clearable
                  class="search-input"
                  @keyup.enter="handleSearch"
                >
                  <template #prefix>
                    <el-icon>
                      <Search />
                    </el-icon>
                  </template>
                  <template #append>
                    <el-link
                      @click="openSearchFieldSettings"
                      title="根据那些字段进行搜索"
                      underline="never"
                      class="settings-link"
                    >
                      <el-icon>
                        <Setting />
                      </el-icon>
                    </el-link>
                  </template>
                </el-input>
                <el-button @click="handleSearch" type="primary">
                  <el-icon>
                    <Search />
                  </el-icon>
                  搜索
                </el-button>
                <el-badge :value="sortBadgeCount" :hidden="sortBadgeCount === 0" type="danger">
                  <el-button
                    type="primary"
                    @click="showSortDialog = true"
                    class="action-btn"
                  >
                    <el-icon>
                      <Sort />
                    </el-icon>
                    排序
                  </el-button>
                </el-badge>
                <el-badge :value="filterBadgeCount" :hidden="filterBadgeCount === 0" type="danger">
                  <div class="filter-split">
                    <el-button
                      type="primary"
                      @click="showAdvancedSearch = !showAdvancedSearch"
                      class="action-btn"
                      ><el-icon>
                        <Filter />
                      </el-icon>
                      {{ showAdvancedSearch ? "收起" : "筛选" }}
                    </el-button>
                    <!-- 已保存的筛选条件：右侧下拉图标，选中即套用；每项悬停显示删除图标 -->
                    <el-dropdown trigger="click" placement="bottom-end" @command="handleFilterPresetCommand">
                      <el-button type="primary" class="action-btn filter-split-more">
                        <el-icon>
                          <ArrowDown />
                        </el-icon>
                      </el-button>
                      <template #dropdown>
                        <el-dropdown-menu>
                          <el-dropdown-item v-if="!filterPresets.length" disabled>
                            暂无保存的筛选条件
                          </el-dropdown-item>
                          <el-dropdown-item v-for="preset in filterPresets" :key="preset.id" :command="preset.id"
                            class="filter-preset-item" :class="{ 'is-active': preset.id === currentPresetId }">
                            <span class="filter-preset-item-name">{{ preset.name }}</span>
                            <el-icon class="filter-preset-item-action filter-preset-item-delete"
                              @click.stop="handleFilterPresetDelete(preset)">
                              <Delete />
                            </el-icon>
                          </el-dropdown-item>
                        </el-dropdown-menu>
                      </template>
                    </el-dropdown>
                  </div>
                </el-badge>
              </div>
            </div>
            <div v-else class="batch-action-bar">
              <div class="batch-selected-info">
                已选 {{ selectedRows.length }} 项
              </div>
              <el-button type="primary" v-permission="'org:user:export'" @click="handleExportSelected">
                <el-icon>
                  <Download />
                </el-icon>
                导出
              </el-button>
              <el-button type="danger" v-permission="'org:user:delete'" @click="handleDeleteSelected">
                <el-icon>
                  <Delete />
                </el-icon>
                删除
              </el-button>
              <el-button type="warning" v-permission="'org:user:update'" @click="handleModifySelected">
                <el-icon>
                  <Edit />
                </el-icon>
                批量修改
              </el-button>
            </div>
          </div>
          <!-- 角色管理头部 -->
          <div v-else-if="activeTab === '角色'">
            <div v-if="selectedRoleMembers.length === 0" class="card-header">
              <span>
                <el-button
                  type="primary"
                  v-permission="'org:role:create'"
                  @click="handleAddRole"
                  class="action-btn"
                >
                  <el-icon>
                    <Plus />
                  </el-icon>
                  新增角色
                </el-button>
                <el-button
                  type="primary"
                  v-permission="'org:role:grant'"
                  @click="handleAddRoleMember"
                  class="action-btn"
                >
                  <el-icon>
                    <Plus />
                  </el-icon>
                  添加成员
                </el-button>
                <el-button
                  type="primary"
                  v-permission="'org:role:import'"
                  @click="handleImportRole"
                  class="action-btn"
                >
                  <i class="iconfont x-daoru"></i>
                  导入
                </el-button>
                <el-button
                  type="primary"
                  v-permission="'org:role:export'"
                  @click="handleExportRole"
                  class="action-btn"
                >
                  <el-icon>
                    <Download />
                  </el-icon>
                  导出
                </el-button>
              </span>
              <div class="header-actions">
                <el-input
                  v-model="roleKeyword"
                  placeholder="搜索角色"
                  clearable
                  class="search-input"
                  @keyup.enter="handleRoleSearch"
                >
                  <template #prefix>
                    <el-icon>
                      <Search />
                    </el-icon>
                  </template>
                </el-input>
                <el-button @click="handleRoleSearch" type="primary">
                  <el-icon>
                    <Search />
                  </el-icon>
                  搜索
                </el-button>
              </div>
            </div>
            <div v-else class="batch-action-bar">
              <div class="batch-selected-info">
                已选 {{ selectedRoleMembers.length }} 项
              </div>
              <el-button type="danger" v-permission="'org:role:grant'" @click="handleRemoveSelectedRoleMembers">
                <el-icon>
                  <Delete />
                </el-icon>
                批量移除
              </el-button>
            </div>
          </div>

          <div v-else class="batch-action-bar">
            <div class="batch-selected-info">
              已选 {{ selectedRows.length }} 项
            </div>
            <el-button type="primary" @click="handleExportSelected">
              <el-icon>
                <Download />
              </el-icon>
              导出
            </el-button>
            <el-button type="danger" @click="handleDeleteSelected">
              <el-icon>
                <Delete />
              </el-icon>
              删除
            </el-button>
            <el-button type="warning" @click="handleModifySelected">
              <el-icon>
                <Edit />
              </el-icon>
              批量修改
            </el-button>
          </div>
        </template>
        <!-- 主内容区域 -->
        <div class="main-content">
          <!-- 表格区域 -->
          <div class="table-area">
            <div class="table-resizer"></div>
            <!-- 用户表格 -->
            <UserTable
              v-if="activeTab === '部门'"
              :table-data="tableData"
              :visible-fields="visibleFields"
              :field-config="userFieldConfig"
              :loading="loading"
              :current-page="currentPage"
              :page-size="pageSize"
              :total="total"
              :sort-rules="sortRules"
              :filter-groups="filterGroups"
              :header-db-field-map="USER_HEADER_DB_FIELD_MAP"
              @selectionChange="handleSelectionChange"
              @rowDblclick="handleRowDblclick"
              @edit="handleEdit"
              @delete="handleDelete"
              @copyUser="handleCopyUser"
              @enableUser="handleEnableUser"
              @disableUser="handleDisableUser"
              @fieldSettings="openFieldSettings"
              @sizeChange="handleSizeChange"
              @currentChange="handleCurrentChange"
              @sortRulesChange="handleSortRulesChange"
              @headerSort="handleHeaderSort"
              @headerFreeze="handleHeaderFreeze"
              @headerHide="handleHeaderHide"
              @headerFilter="handleHeaderFilter"
            />

            <!-- 角色成员表格 -->
            <RoleMemberTable
              v-else-if="activeTab === '角色'"
              :role-members="roleMembers"
              :role-loading="roleLoading"
              :role-current-page="roleCurrentPage"
              :role-page-size="rolePageSize"
              :role-total="roleTotal"
              :selected-role="selectedRole"
              :visible-fields="roleVisibleFields"
              :field-config="roleFieldConfig"
              :sort-rules="roleSortRules"
              :filter-groups="roleFilterGroups"
              :header-db-field-map="ROLE_HEADER_DB_FIELD_MAP"
              @member-selection-change="handleRoleMemberSelectionChange"
              @remove-member="handleRemoveRoleMember"
              @size-change="handleRoleSizeChange"
              @current-change="handleRoleCurrentChange"
              @headerSort="handleRoleHeaderSort"
              @headerFilter="handleRoleHeaderFilter"
            />
          </div>
        </div>
      </el-card>
    </el-main>
    <el-aside width="320px" class="advanced-search-aside" v-if="activeTab === '部门' && showAdvancedSearch">
      <FilterPanel
        v-model:filterGroups="filterGroups"
        v-model:groupsLogic="groupsLogic"
        :dept-tree="deptTree"
        @apply="applyFilter"
        @reset="resetFilter"
        :current-preset-name="currentPresetName"
        :preset-names="presetNames"
        @save="handleFilterPresetSave"
        @save-as="handleFilterPresetSaveAs"
      />
    </el-aside>
  </el-container>

  <!-- 字段设置对话框 -->
  <FieldSettingsDialog
    v-model:visible="fieldSettingsVisible"
    :fields="visibleFields"
    :field-config="userFieldConfig"
    @save="saveFieldSettings"
  />

  <!-- 搜索字段设置对话框 -->
  <SearchFieldSettingsDialog
    v-model:visible="searchFieldSettingsVisible"
    :fields="searchFields"
    :fieldOptions="searchFieldOptions"
    @save="saveSearchFieldSettings"
  />

  <!-- 用户编辑对话框 -->
  <UserEditDialog
    v-model:visible="dialogVisible"
    v-model:display-mode="editDisplayMode"
    :user="form"
    :dept-tree="deptTree"
    @submit="handleSubmit"
  />

  <!-- 排序设置对话框 -->
  <SortSettingsDialog
    v-model:visible="showSortDialog"
    :sort-rules="sortRules"
    @save="saveSortRules"
  />

  <!-- 详细信息视图 -->
  <UserDetailView
    v-model:visible="detailVisible"
    v-model:display-mode="detailDisplayMode"
    v-model:current-row="currentDetailRow"
    v-model:current-index="currentDetailIndex"
    :data="tableData"
    @edit="handleDetailEdit"
    @delete="handleDetailDelete"
  />

  <!-- 导入对话框 -->
  <Import
    v-model:visible="importVisible"
    @import-success="handleImportSuccess"
  />

  <!-- 批量修改对话框 -->
  <BatchModify
    v-model:visible="batchModifyVisible"
    :display-mode="batchModifyDisplayMode"
    :selected-rows="selectedUsers"
    @submit="handleBatchModifySubmit"
  />

  <!-- 添加部门对话框 -->
  <SelectParentDept
    v-model:visible="addDeptVisible"
    :dept-tree="deptTree"
    :current-dept="currentDept"
    @submit="handleAddDeptSubmit"
  />

  <!-- 选择用户对话框 -->
  <SelectUser
    v-model:visible="selectUserVisible"
    @select-save="handleSelectUserSave"
    @select-close="handleSelectUserClose"
  />

  <!-- 添加角色成员对话框 -->
  <AddRoleMemberDialog
    v-model:visible="addRoleMemberVisible"
    :role-id="selectedRole?.id"
    :available-users="availableUsers"
    :dept-tree="deptTree"
    :total="availableUsers.length"
    @add-success="handleAddRoleMemberSuccess"
  />
  
  <!-- 角色编辑对话框 -->
  <RoleEditDialog
    v-model:visible="roleDialogVisible"
    v-model:display-mode="roleDisplayMode"
    :role="roleForm"
    :role-tree="roleTree"
    @submit="handleRoleSubmit"
  />

  <!-- 角色权限分配对话框 -->
  <RolePermissionDialog
    v-model:visible="permissionDialogVisible"
    :role="permissionRole"
  />
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  Plus,
  Search,
  Filter,
  Setting,
  Edit,
  Delete,
  Download,
  Sort,
  ArrowDown,
} from "@element-plus/icons-vue";
import request from "@/utils/request";
import { pageSubtitle } from "@/utils/pageSubtitle";
import DepartmentTree from "./components/DepartmentTree.vue";
import RoleTree from "./components/RoleTree.vue";
import UserTable from "./components/UserTable.vue";
import RoleMemberTable from "./components/RoleMemberTable.vue";
import FieldSettingsDialog from "./components/FieldSettingsDialog.vue";
import SearchFieldSettingsDialog from "./components/SearchFieldSettingsDialog.vue";
import FilterPanel from "./components/FilterPanel.vue";
import SortSettingsDialog from "./components/SortSettingsDialog.vue";
import UserDetailView from "./components/UserDetailView.vue";
import UserEditDialog from "./components/UserEditDialog.vue";
import Import from "./components/Import.vue";
import BatchModify from "./components/BatchModify.vue";
import SelectParentDept from "./components/SelectParentDept.vue";
import SelectUser from "./components/SelectUser.vue";
import AddRoleMemberDialog from "./components/AddRoleMemberDialog.vue";
import RoleEditDialog from "./components/RoleEditDialog.vue";
import RolePermissionDialog from "./components/RolePermissionDialog.vue";
import "./style/organization.css";

// ==================== 常量定义 ====================
const PAGE_SIZES = [20, 50, 100];
const DEFAULT_PAGE_SIZE = 20;
const DEFAULT_PAGE = 1;
const LOCAL_STORAGE_KEYS = {
  VISIBLE_FIELDS: "organizationVisibleFields",
  FIELD_CONFIG: "organizationFieldConfig",
  SEARCH_FIELDS: "organizationSearchFields",
  SORT_RULES: "organizationSortRules",
};
const API_ENDPOINTS = {
  DEPT_TREE: "/admin/organization/get-dept-tree",
  USER_LIST: "/admin/organization/get-user-list",
  ROLE_TREE: "/admin/organization/get-role-tree",
  ROLE_MEMBER_LIST: "/admin/organization/get-members",
  CREATE_USER: "/admin/organization/create-user",
  UPDATE_USER: "/admin/organization/update-user",
  DELETE_USER: "/admin/organization/delete-user",
  EXPORT_USER: "/admin/organization/export-users",
  BATCH_UPDATE_USER: "/admin/organization/update-users-batch",
  BATCH_DELETE_USER: "/admin/organization/delete-users-selected",
  BATCH_ALL_DELETE_USER: "/admin/organization/delete-users-batch",
  CREATE_DEPT: "/admin/organization/create-dept",
  UPDATE_DEPT: "/admin/organization/update-dept",
  DELETE_DEPT: "/admin/organization/delete-department",
  CREATE_ROLE: "/admin/organization/create-role",
  UPDATE_ROLE: "/admin/organization/update-role",
  DELETE_ROLE: "/admin/organization/delete-role",
  ADD_ROLE_MEMBER: "/admin/organization/add-members",
  REMOVE_ROLE_MEMBER: "/admin/organization/remove-member",
  EXPORT_ROLE_MEMBERS: "/admin/organization/export-role-members",
};
// 保存的筛选条件：后台各列表页共用接口（admin/filter_preset），page 传本页面标识
const FILTER_PRESET_PAGE = "organization";
const FILTER_PRESET_API = {
  list: "/admin/filter-preset/list",
  save: "/admin/filter-preset/save",
  update: "/admin/filter-preset/update",
  delete: "/admin/filter-preset/delete",
};

// ==================== 工具函数 ====================
// 时间格式化函数
const formatDate = (dateStr) => {
  if (!dateStr) return "-";
  const date = new Date(dateStr);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  const seconds = String(date.getSeconds()).padStart(2, "0");
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
};

// 相对时间格式化函数（可选）
const formatRelativeTime = (dateStr) => {
  if (!dateStr) return "-";
  const date = new Date(dateStr);
  const now = new Date();
  const diff = now - date;

  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (minutes < 1) return "刚刚";
  if (minutes < 60) return `${minutes}分钟前`;
  if (hours < 24) return `${hours}小时前`;
  if (days < 7) return `${days}天前`;

  return formatDate(dateStr);
};

// 错误处理工具函数
const handleRequestError = (error, defaultMessage) => {
  if (error.response?.data?.detail === "Method Not Allowed") {
    ElMessage.error("请求方法错误，请检查 API 接口配置");
  } else {
    ElMessage.error(error.message || defaultMessage);
  }
};

// 创建空表单工厂函数
const createEmptyForm = () => ({
  id: null,
  username: "",
  password: "",
  name: "",
  phone: "",
  email: "",
  deptId: null,
  deptName: "",
  avatar: "",
  images: [],
  attachments: [],
  status: 1,
  lastLoginTime: null,
  lastLoginIp: null,
  createdTime: null,
  updatedTime: null,
});

// ==================== 计算属性 ====================
const sortBadgeCount = computed(() => sortRules.value.length);
const filterBadgeCount = computed(() =>
  filterGroups.value.reduce((sum, group) => sum + group.conditions.length, 0)
);
const hasSelectedRows = computed(() => selectedRows.value.length > 0);

// ==================== 选项卡状态 ====================
const tabOptions = ref(["部门", "角色"]);
const activeTab = ref("部门");
const deptTree = ref([]);
const deptTreeRef = ref(null);

// ==================== 表格状态 ====================
const tableData = ref([]);
const loading = ref(false);
const currentPage = ref(DEFAULT_PAGE);
const pageSize = ref(DEFAULT_PAGE_SIZE);
const total = ref(0);
const selectedRows = ref([]);

// ==================== 搜索状态 ====================
const keyword = ref("");

// ==================== 筛选状态 ====================
const showAdvancedSearch = ref(false);
const groupsLogic = ref("and");
const filterGroups = ref([
  {
    groupLogic: "and",
    conditionLogic: "and",
    conditions: [],
  },
]);
// 当前页面已保存的筛选条件（下拉选中即套用，仅本人可见）
const filterPresets = ref([]);
// 当前生效的方案ID：null 表示未选中任何方案（此时「保存条件」为新建）
const currentPresetId = ref(null);
// 套用/保存方案时的条件快照，用于判断条件是否被改动（标题上的方案名加「*」）
const presetSnapshot = ref("");
// 当前页面已保存的方案名列表（筛选面板新建 / 另存为时用于前端查重）
const presetNames = computed(() => filterPresets.value.map((preset) => preset.name));
// 当前生效方案名：未选中方案时为空串，筛选面板据此判断「保存条件」是新建还是覆盖更新
const currentPresetName = computed(
  () => filterPresets.value.find((preset) => preset.id === currentPresetId.value)?.name || "",
);
// 条件快照：仅比对条件本身（组间关系 + 各条件），用于判断当前方案是否被改动
const filterSignature = () =>
  JSON.stringify({ logic: groupsLogic.value, groups: filterGroups.value });
// 当前方案的条件已被改动（header 上的方案名追加「*」提示）
const presetDirty = computed(
  () => currentPresetId.value !== null && presetSnapshot.value !== filterSignature(),
);
// header 标题后的方案名：套用方案时展示方案名，条件改动后追加「*」，未选中方案时清空
watch(
  [currentPresetName, presetDirty],
  ([name, dirty]) => {
    pageSubtitle.value = name ? (dirty ? `${name} *` : name) : "";
  },
  { immediate: true },
);
const searchFields = ref(["username", "name", "phone", "email"]);
const searchFieldOptions = computed(() => [
  { value: "username", label: "用户名" },
  { value: "name", label: "真实姓名" },
  { value: "phone", label: "手机号" },
  { value: "email", label: "邮箱" },
  { value: "deptId", label: "部门" },
]);

// ==================== 排序状态 ====================
const showSortDialog = ref(false);
const sortRules = ref([]);

// ==================== 字段设置状态 ====================
const fieldSettingsVisible = ref(false);
const searchFieldSettingsVisible = ref(false);
const visibleFields = ref([
  "id",
  "name",
  "username",
  "phone",
  "email",
  "deptName",
  "avatar",
  "images",
  "attachments",
  "status",
  "createdTime",
  "updatedTime",
  "lastLoginTime",
  "lastLoginIp",
]);
const userFieldConfig = ref([
  { value: "id", label: "ID", width: 60, fixed: "" },
  { value: "name", label: "姓名", width: 120, fixed: "" },
  { value: "username", label: "用户名", width: 120, fixed: "" },
  { value: "phone", label: "手机号", width: 130, fixed: "" },
  { value: "email", label: "邮箱", width: 180, fixed: "" },
  { value: "deptName", label: "部门", width: 150, fixed: "" },
  { value: "avatar", label: "头像", width: 80, fixed: "" },
  { value: "images", label: "图片", width: 140, fixed: "" },
  { value: "attachments", label: "附件", width: 160, fixed: "" },
  { value: "status", label: "状态", width: 70, fixed: "" },
  { value: "createdTime", label: "创建时间", width: 180, fixed: "" },
  { value: "updatedTime", label: "更新时间", width: 180, fixed: "" },
  { value: "lastLoginTime", label: "最后登录", width: 180, fixed: "" },
  { value: "lastLoginIp", label: "最后登录IP", width: 180, fixed: "" },
]);

// 角色成员表格字段配置
const roleVisibleFields = ref(["id", "name", "username", "phone", "email"]);
const roleFieldConfig = ref([
  { value: "id", label: "ID", width: 60 },
  { value: "name", label: "姓名", width: 120 },
  { value: "username", label: "用户名", width: 120 },
  { value: "phone", label: "手机号", width: 130 },
  { value: "email", label: "邮箱", width: 180 },
]);
const roleSortRules = ref([]);
// 角色成员表列头筛选条件（与用户表筛选分开维护）
const roleFilterGroups = ref([
  { groupLogic: "and", conditionLogic: "and", conditions: [] },
]);
// 角色成员列头可映射到数据库列的字段
const ROLE_HEADER_DB_FIELD_MAP = {
  id: "id",
  name: "name",
  username: "username",
  phone: "phone",
  email: "email",
};

// ==================== 表单状态 ====================
const dialogVisible = ref(false);
const editDisplayMode = ref("dialog");
const form = ref(createEmptyForm());

// ==================== 详情查看状态 ====================
const detailVisible = ref(false);
const detailDisplayMode = ref("dialog");
const currentDetailRow = ref(null);
const currentDetailIndex = ref(-1);

// ==================== 导入状态 ====================
const importVisible = ref(false);

// ==================== 批量修改状态 ====================
const batchModifyVisible = ref(false);
const batchModifyDisplayMode = ref("dialog");

// ==================== 部门相关状态 ====================
const addDeptVisible = ref(false);
const addDeptForm = ref({ name: "" });
const currentParentDept = ref(null);
const currentDept = ref(null);
const selectedDeptId = ref(null);

// ==================== 选择用户状态 ====================
const selectUserVisible = ref(false);
const selectedDeptForManager = ref(null);

// ==================== 角色相关状态 ====================
const roleTree = ref([]);
const roleMembers = ref([]);
const roleLoading = ref(false);
const roleCurrentPage = ref(1);
const rolePageSize = ref(20);
const roleTotal = ref(0);
const roleKeyword = ref("");
const selectedRole = ref(null);
const selectedRoleMembers = ref([]);
const roleDialogVisible = ref(false);
const roleDisplayMode = ref("dialog");
const roleDialogTitle = ref("");
const permissionDialogVisible = ref(false);
const permissionRole = ref(null);
const roleForm = ref({
  id: null,
  name: "",
  code: "",
  pid: null,
  description: "",
  status: 1,
});
const currentParentRole = ref(null);

// 添加角色成员相关状态
const addRoleMemberVisible = ref(false);
const availableUsers = ref([]);
const loadingAvailableUsers = ref(false);
const availableUserCurrentPage = ref(1);
const availableUserPageSize = ref(20);
const availableUserTotal = ref(0);
const selectedAvailableUsers = ref([]);

// ==================== 其他数据 ====================
const selectedUsers = computed(() => {
  return tableData.value.filter((row) =>
    selectedRows.value.find((sel) => sel.id === row.id),
  );
});

// 处理排序规则变化
const handleSortRulesChange = (rules) => {
  sortRules.value = rules;
  saveSortRules(rules);
};

// ==================== 列头菜单 ====================
// 可映射到数据库列的字段（其余为合成列 / 表中不存在，列头菜单仅提供「冻结列 / 隐藏此列」）
const USER_HEADER_DB_FIELD_MAP = {
  id: "id",
  name: "name",
  username: "username",
  phone: "phone",
  email: "email",
  status: "status",
  createdTime: "create_time",
  updatedTime: "update_time",
  lastLoginTime: "last_login_time",
};

// 列头冻结 / 隐藏后整体落盘（同步字段设置弹窗的完整配置，保证隐藏列可恢复）
const persistUserColumnConfig = (config, visible) => {
  userFieldConfig.value = config;
  visibleFields.value = visible;
  localStorage.setItem(LOCAL_STORAGE_KEYS.FIELD_CONFIG, JSON.stringify(config));
  localStorage.setItem(LOCAL_STORAGE_KEYS.VISIBLE_FIELDS, JSON.stringify(visible));
  const savedFull = localStorage.getItem("organizationAllFieldConfig");
  if (savedFull) {
    try {
      const full = JSON.parse(savedFull);
      if (Array.isArray(full)) {
        localStorage.setItem(
          "organizationAllFieldConfig",
          JSON.stringify(
            full.map((item) => {
              const current = config.find((c) => c.value === item.value);
              return {
                ...item,
                ...(current
                  ? { width: current.width, fixed: current.fixed }
                  : {}),
                visible: visible.includes(item.value),
              };
            }),
          ),
        );
      }
    } catch (e) {
      console.error("同步字段配置失败:", e);
    }
  }
};

const handleHeaderSort = (fieldValue, direction) => {
  const dbField = USER_HEADER_DB_FIELD_MAP[fieldValue];
  // 再次点击已选中的排序方向 -> 取消该列排序
  if (!dbField || !direction) {
    saveSortRules([]);
    return;
  }
  saveSortRules([{ field: dbField, direction }]);
};

const handleHeaderFreeze = (fieldValue) => {
  const next = userFieldConfig.value.map((item) =>
    item.value === fieldValue
      ? { ...item, fixed: item.fixed ? "" : "left" }
      : item,
  );
  persistUserColumnConfig(next, [...visibleFields.value]);
  ElMessage.success(
    next.find((item) => item.value === fieldValue)?.fixed
      ? "已冻结该列"
      : "已取消冻结",
  );
};

const handleHeaderHide = (fieldValue) => {
  // 保留该列配置，仅从可见字段中移除，字段设置弹窗仍可重新开启该列
  const visible = visibleFields.value.filter((item) => item !== fieldValue);
  persistUserColumnConfig(userFieldConfig.value.map((item) => ({ ...item })), visible);
  ElMessage.success("已隐藏该列");
};

const handleHeaderFilter = ({ field, operator, value }) => {
  const dbField = USER_HEADER_DB_FIELD_MAP[field];
  if (!dbField) return;
  const groups = deepClone(filterGroups.value) || [];
  if (!groups.length) {
    groups.push({ groupLogic: "and", conditionLogic: "and", conditions: [] });
  }
  if (!Array.isArray(groups[0].conditions)) groups[0].conditions = [];
  const conditions = groups[0].conditions;
  const index = conditions.findIndex((cond) => cond.field === dbField);
  const noValueOperator = ["is_null", "is_not_null"].includes(operator);
  const isEmpty = !noValueOperator && String(value ?? "").trim() === "";
  if (isEmpty) {
    if (index > -1) conditions.splice(index, 1);
  } else if (index > -1) {
    conditions[index] = { field: dbField, operator, value };
  } else {
    conditions.push({ field: dbField, operator, value });
  }
  filterGroups.value = groups;
  currentPresetId.value = null;
  presetSnapshot.value = "";
  currentPage.value = 1;
  fetchUsers();
};

// ==================== 数据获取 ====================
const fetchdeptTree = async () => {
  try {
    const res = await request.post(API_ENDPOINTS.DEPT_TREE, {});
    if (res.code === 200) {
      deptTree.value = res.data || [];
    }
  } catch (error) {
    console.error("获取部门树失败:", error);
  }
};

const fetchUsers = async () => {
  loading.value = true;

  try {
    const data = {
      page: currentPage.value,
      limit: pageSize.value,
      keyword: keyword.value,
      filter: filterGroups.value,
      sortRules: sortRules.value,
      searchFields: searchFields.value,
      deptId: selectedDeptId.value,
    };

    const res = await request.post(API_ENDPOINTS.USER_LIST, { data });

    if (res.code === 200) {
      tableData.value = res.data?.items || [];
      total.value = res.data?.total || 0;
    }
  } catch (error) {
    handleRequestError(error, "获取数据失败");
  } finally {
    loading.value = false;
  }
};

const fetchRoleTree = async () => {
  try {
    const res = await request.post(API_ENDPOINTS.ROLE_TREE, {});
    if (res.code === 200) {
      roleTree.value = res.data || [];
    }
  } catch (error) {
    console.error("获取角色树失败:", error);
  }
};

const fetchRoleMembers = async () => {
  if (!selectedRole.value) {
    roleMembers.value = [];
    return;
  }
  roleLoading.value = true;

  try {
    const data = {
      page: roleCurrentPage.value,
      limit: rolePageSize.value,
      roleId: selectedRole.value.id,
      keyword: roleKeyword.value,
      filter: roleFilterGroups.value,
      sortRules: roleSortRules.value,
    };

    const res = await request.post(API_ENDPOINTS.ROLE_MEMBER_LIST, data);

    if (res.code === 200) {
      roleMembers.value = res.data?.items || [];
      roleTotal.value = res.data?.total || 0;
    }
  } catch (error) {
    handleRequestError(error, "获取角色成员失败");
  } finally {
    roleLoading.value = false;
  }
};

// 角色成员列头：升序 / 降序（再次点击已选中的方向 -> 取消排序）
const handleRoleHeaderSort = (fieldValue, direction) => {
  const dbField = ROLE_HEADER_DB_FIELD_MAP[fieldValue];
  if (!dbField || !direction) {
    roleSortRules.value = [];
  } else {
    roleSortRules.value = [{ field: dbField, direction }];
  }
  roleCurrentPage.value = 1;
  fetchRoleMembers();
};

// 角色成员列头：应用筛选（同字段覆盖，清空值移除条件）
const handleRoleHeaderFilter = ({ field, operator, value }) => {
  const dbField = ROLE_HEADER_DB_FIELD_MAP[field];
  if (!dbField) return;
  const conditions = roleFilterGroups.value[0].conditions;
  const index = conditions.findIndex((cond) => cond.field === dbField);
  const noValueOperator = ["is_null", "is_not_null"].includes(operator);
  const isEmpty = !noValueOperator && String(value ?? "").trim() === "";
  if (isEmpty) {
    if (index > -1) conditions.splice(index, 1);
  } else if (index > -1) {
    conditions[index] = { field: dbField, operator, value };
  } else {
    conditions.push({ field: dbField, operator, value });
  }
  roleFilterGroups.value = [
    { ...roleFilterGroups.value[0], conditions: [...conditions] },
  ];
  roleCurrentPage.value = 1;
  fetchRoleMembers();
};

const handleSearch = () => {
  currentPage.value = 1;
  fetchUsers();
};

const handleRoleSearch = () => {
  roleCurrentPage.value = 1;
  fetchRoleMembers();
};

const openFieldSettings = () => {
  fieldSettingsVisible.value = true;
};

const openSearchFieldSettings = () => {
  searchFieldSettingsVisible.value = true;
};

const saveFieldSettings = (fieldsConfig) => {
  localStorage.setItem(
    LOCAL_STORAGE_KEYS.VISIBLE_FIELDS,
    JSON.stringify(fieldsConfig.map((item) => item.value)),
  );
  localStorage.setItem(
    LOCAL_STORAGE_KEYS.FIELD_CONFIG,
    JSON.stringify(fieldsConfig),
  );
  visibleFields.value = fieldsConfig
    .filter((item) => item.value)
    .map((item) => item.value);
  userFieldConfig.value = fieldsConfig;
  ElMessage.success("字段设置已保存");
};

const saveSearchFieldSettings = (fields) => {
  localStorage.setItem(
    LOCAL_STORAGE_KEYS.SEARCH_FIELDS,
    JSON.stringify(fields),
  );
  searchFields.value = fields;
  ElMessage.success("搜索字段设置已保存");
};

const saveSortRules = (rules) => {
  sortRules.value = rules;
  localStorage.setItem(LOCAL_STORAGE_KEYS.SORT_RULES, JSON.stringify(rules));
  currentPage.value = 1;
  fetchUsers();
};

// 从本地存储加载字段设置
const loadFieldSettings = () => {
  // 默认值
  const defaultVisible = [
    "id",
    "name",
    "username",
    "phone",
    "email",
    "deptName",
    "avatar",
    "images",
    "attachments",
    "status",
    "createdTime",
    "updatedTime",
    "lastLoginTime",
    "lastLoginIp",
  ];
  const defaultConfig = [
    { value: "id", label: "ID", width: 60, fixed: "" },
    { value: "name", label: "姓名", width: 120, fixed: "" },
    { value: "username", label: "用户名", width: 120, fixed: "" },
    { value: "phone", label: "手机号", width: 130, fixed: "" },
    { value: "email", label: "邮箱", width: 180, fixed: "" },
    { value: "deptName", label: "部门", width: 150, fixed: "" },
    { value: "avatar", label: "头像", width: 80, fixed: "" },
    { value: "images", label: "图片", width: 140, fixed: "" },
    { value: "attachments", label: "附件", width: 160, fixed: "" },
    { value: "status", label: "状态", width: 70, fixed: "" },
    { value: "createdTime", label: "创建时间", width: 180, fixed: "" },
    { value: "updatedTime", label: "更新时间", width: 180, fixed: "" },
    { value: "lastLoginTime", label: "最后登录", width: 180, fixed: "" },
    { value: "lastLoginIp", label: "最后登录IP", width: 180, fixed: "" },
  ];

  // 加载可见字段
  const savedVisible = localStorage.getItem(LOCAL_STORAGE_KEYS.VISIBLE_FIELDS);
  if (savedVisible) {
    try {
      const fields = JSON.parse(savedVisible);
      if (Array.isArray(fields) && fields.length > 0) {
        visibleFields.value = fields;
      } else {
        visibleFields.value = defaultVisible;
      }
    } catch (e) {
      console.error("加载字段设置失败:", e);
      visibleFields.value = defaultVisible;
    }
  } else {
    visibleFields.value = defaultVisible;
  }

  // 加载字段配置
  const savedConfig = localStorage.getItem(LOCAL_STORAGE_KEYS.FIELD_CONFIG);
  if (savedConfig) {
    try {
      const config = JSON.parse(savedConfig);
      if (Array.isArray(config) && config.length > 0) {
        userFieldConfig.value = config;
      } else {
        userFieldConfig.value = defaultConfig;
      }
    } catch (e) {
      console.error("加载字段配置失败:", e);
      userFieldConfig.value = defaultConfig;
    }
  } else {
    userFieldConfig.value = defaultConfig;
  }

  // 加载搜索字段
  const savedSearch = localStorage.getItem(LOCAL_STORAGE_KEYS.SEARCH_FIELDS);
  if (savedSearch) {
    try {
      const fields = JSON.parse(savedSearch);
      if (Array.isArray(fields)) {
        searchFields.value = fields;
      }
    } catch (e) {
      console.error("加载搜索字段设置失败:", e);
    }
  }

  // 加载排序规则
  const savedSort = localStorage.getItem(LOCAL_STORAGE_KEYS.SORT_RULES);
  if (savedSort) {
    try {
      const rules = JSON.parse(savedSort);
      if (Array.isArray(rules)) {
        sortRules.value = rules;
      }
    } catch (e) {
      console.error("加载排序规则失败:", e);
    }
  }
};

// 表格选中事件
const handleSelectionChange = (val) => {
  selectedRows.value = val;
};

// 选项卡切换
const handleTabChange = () => {
  // 切换选项卡时可以添加一些重置逻辑
};

// 部门树节点点击
const handleNodeClick = (data, node) => {
  if (data && data.id) {
    // 如果点击的是已选中的部门，则取消选中
    if (selectedDeptId.value === data.id) {
      selectedDeptId.value = null;
      // 清除部门树的选中效果
      if (deptTreeRef.value && deptTreeRef.value.treeRef) {
        deptTreeRef.value.treeRef.setCurrentKey(null);
      }
    } else {
      selectedDeptId.value = data.id;
      // 设置部门树的选中效果
      if (deptTreeRef.value && deptTreeRef.value.treeRef) {
        deptTreeRef.value.treeRef.setCurrentKey(data.id);
      }
    }
    keyword.value = "";
    currentPage.value = 1;
    fetchUsers();
  } else {
    selectedDeptId.value = null;
    tableData.value = [];
    total.value = 0;
  }
};

// 部门更新后刷新
const handleDeptUpdated = () => {
  fetchdeptTree();
};

// 添加子部门
const handleAddSubDept = (parent) => {
  currentParentDept.value = parent;
  addDeptVisible.value = true;
  addDeptForm.value = { name: "", pid: parent.id };
};

// 选择上级部门
const handleSelectParentDept = (node) => {
  currentDept.value = node;
};

// 设置部门负责人
const handleSetManager = (node) => {
  selectedDeptForManager.value = node;
  selectUserVisible.value = true;
};

// 添加部门提交
const handleAddDeptSubmit = async (data) => {
  try {
    let res;
    if (data.id) {
      res = await request.post(API_ENDPOINTS.UPDATE_DEPT, {
        data: {
          id: data.id,
          name: data.name,
          pid: data.pid,
        },
      });
    } else {
      res = await request.post(API_ENDPOINTS.CREATE_DEPT, {
        data: {
          name: data.name,
          pid: data.pid,
        },
      });
    }

    if (res.code === 200) {
      ElMessage.success(data.id ? "更新成功" : "创建成功");
      fetchdeptTree();
      addDeptVisible.value = false;
    }
  } catch (error) {
    handleRequestError(error, data.id ? "更新失败" : "创建失败");
  }
};

// 处理选择用户保存（设置部门负责人）
const handleSelectUserSave = (selectedUser) => {
  request
    .post("/admin/organization/update-dept", {
      data: {
        id: selectedDeptForManager.value.id,
        managerId: selectedUser.id,
      },
    })
    .then((res) => {
      if (res.code === 200) {
        ElMessage.success("设置成功");
        fetchdeptTree();
      } else {
        ElMessage.error("设置失败");
      }
    })
    .catch((error) => {
      console.error("设置部门负责人失败:", error);
      ElMessage.error("设置失败");
    });
  selectUserVisible.value = false;
  selectedDeptForManager.value = null;
};

const handleSelectUserClose = () => {
  selectUserVisible.value = false;
  selectedDeptForManager.value = null;
};

// 角色树节点点击
const handleRoleNodeClick = (node) => {
  if (node && node.id) {
    selectedRole.value = node;
    roleKeyword.value = "";
    roleCurrentPage.value = 1;
    fetchRoleMembers();
  } else {
    roleMembers.value = [];
    roleTotal.value = 0;
  }
};

// 角色更新后刷新
const handleRoleUpdated = () => {
  fetchRoleTree();
};

// 角色权限分配
const handleAssignPermission = (role) => {
  if (!role || !role.id) return;
  permissionRole.value = role;
  permissionDialogVisible.value = true;
};

// 添加角色
const handleAddRole = () => {
  roleDialogVisible.value = true;
  roleDialogTitle.value = "新增角色";
  roleForm.value = {
    id: null,
    name: "",
    code: "",
    pid: null,
    description: "",
    status: 1,
  };
};

// 获取可用用户
const fetchAvailableUsers = async () => {
  try {
    const res = await request.post(API_ENDPOINTS.USER_LIST, {
      data: {
        page: 1,
        limit: 1000, // 获取足够多的用户
        status: 1 // 只获取状态正常的用户
      }
    });
    if (res.code === 200) {
      availableUsers.value = res.data?.items || [];
    }
  } catch (error) {
    console.error("获取可用用户失败:", error);
    ElMessage.error("获取用户列表失败");
  }
};

// 添加角色成员
const handleAddRoleMember = async () => {
  if (!selectedRole.value) {
    ElMessage.warning("请先选择一个角色");
    return;
  }
  // 获取可用用户
  await fetchAvailableUsers();
  addRoleMemberVisible.value = true;
};

// 添加角色成员成功
const handleAddRoleMemberSuccess = () => {
  fetchRoleMembers();
};

// 处理角色成员选择变化
const handleRoleMemberSelectionChange = (val) => {
  selectedRoleMembers.value = val;
};

// 移除角色成员
const handleRemoveRoleMember = (member) => {
  try {
    ElMessageBox.confirm(
      `确定要将 ${member.name} 从角色 "${selectedRole.value.name}" 中移除吗？`,
      "提示",
      {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      },
    ).then(async () => {
      const res = await request.post(API_ENDPOINTS.REMOVE_ROLE_MEMBER, {
        data: {
          roleId: selectedRole.value.id,
          userId: member.id,
        },
      });
      if (res.code === 200) {
        ElMessage.success("移除成功");
        fetchRoleMembers();
      }
    });
  } catch (error) {
    if (error !== "cancel") {
      handleRequestError(error, "移除失败");
    }
  }
};

// 移除选中的角色成员
const handleRemoveSelectedRoleMembers = async () => {
  if (selectedRoleMembers.value.length === 0) {
    ElMessage.warning("请先选择要移除的成员");
    return;
  }
  try {
    await ElMessageBox.confirm(
      `确定要移除选中的 ${selectedRoleMembers.value.length} 个成员吗？`,
      "警告",
      {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "danger",
      },
    );

    const ids = selectedRoleMembers.value.map((row) => row.id);
    const res = await request.post(API_ENDPOINTS.REMOVE_ROLE_MEMBER, {
      roleId: selectedRole.value.id,
      userIds: ids,
    });
    if (res.code === 200) {
      ElMessage.success(`移除成功 ${selectedRoleMembers.value.length} 个成员`);
      await fetchRoleMembers();
      selectedRoleMembers.value = [];
    }
  } catch (error) {
    if (error !== "cancel") {
      handleRequestError(error, "移除失败");
    }
  }
};

// 处理角色大小变化
const handleRoleSizeChange = (size) => {
  rolePageSize.value = size;
  fetchRoleMembers();
};

// 处理角色页码变化
const handleRoleCurrentChange = (current) => {
  roleCurrentPage.value = current;
  fetchRoleMembers();
};

// 导入角色
const handleImportRole = () => {
  importVisible.value = true;
};

// 导出角色成员
const handleExportRole = async () => {
  if (!selectedRole.value) {
    ElMessage.warning("请先选择一个角色");
    return;
  }

  try {
    roleLoading.value = true;

    const res = await request.post(API_ENDPOINTS.EXPORT_ROLE_MEMBERS, {
      roleId: selectedRole.value.id,
      keyword: roleKeyword.value,
    });

    if (res.code === 200) {
      ElMessage.success("导出任务已提交，完成后会收到通知");
    }
  } catch (error) {
    handleRequestError(error, "导出失败");
  } finally {
    roleLoading.value = false;
  }
};

// 初始化页面
onMounted(() => {
  loadFieldSettings();
  loadFilterPresets();
  fetchdeptTree();
  fetchUsers();
  fetchRoleTree();
});

onUnmounted(() => {
  pageSubtitle.value = "";
});

const handleAdd = () => {
  form.value = createEmptyForm();
  dialogVisible.value = true;
};

const handleEdit = (row) => {
  form.value = {
    id: row.id,
    username: row.username,
    password: "",
    name: row.name,
    phone: row.phone,
    email: row.email,
    deptId: row.deptId,
    deptName: row.deptName || "",
    avatar: row.avatar,
    images: row.images || [],
    attachments: row.attachments || [],
    status: row.status,
    lastLoginTime: row.lastLoginTime,
    lastLoginIp: row.lastLoginIp,
    createdTime: row.createdTime,
    updatedTime: row.updatedTime,
  };
  dialogVisible.value = true;
};

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm("确定要删除该用户吗？", "提示", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    });
    const res = await request.post(API_ENDPOINTS.DELETE_USER, {
      data: {
        id: row.id,
      },
    });
    if (res.code === 200) {
      ElMessage.success("删除成功");
      fetchUsers();
    }
  } catch (error) {
    if (error !== "cancel") {
      handleRequestError(error, "删除失败");
    }
  }
};

const handleSubmit = async (userData) => {
  try {
    let res;
    if (userData.id) {
      res = await request.post(API_ENDPOINTS.UPDATE_USER, {
        data: {
          id: userData.id,
          username: userData.username,
          password: userData.password,
          name: userData.name,
          phone: userData.phone,
          email: userData.email,
          deptId: userData.deptId,
          avatar: userData.avatar,
          images: userData.images || [],
          attachments: userData.attachments || [],
          status: userData.status,
        },
      });
    } else {
      res = await request.post(API_ENDPOINTS.CREATE_USER, {
        data: {
          username: userData.username,
          password: userData.password,
          name: userData.name,
          phone: userData.phone,
          email: userData.email,
          deptId: userData.deptId,
          avatar: userData.avatar,
          images: userData.images || [],
          attachments: userData.attachments || [],
          status: userData.status,
        },
      });
    }

    if (res.code === 200) {
      ElMessage.success(userData.id ? "更新成功" : "创建成功");
      fetchUsers();
      dialogVisible.value = false;
    }
  } catch (error) {
    handleRequestError(error, userData.id ? "更新失败" : "创建失败");
  }
};

const handleSizeChange = (val) => {
  pageSize.value = val;
  fetchUsers();
};

const handleCurrentChange = (val) => {
  currentPage.value = val;
  fetchUsers();
};

const clearSelection = () => {
  if (selectedRows.value.length > 0) {
    selectedRows.value = [];
  }
};

// 双击表格行显示详细信息
const handleRowDblclick = (row, column, event) => {
  currentDetailRow.value = row;
  currentDetailIndex.value = tableData.value.findIndex(
    (item) => item.id === row.id,
  );
  detailVisible.value = true;
};

// 处理详细信息编辑
const handleDetailEdit = (row) => {
  handleEdit(row);
  detailVisible.value = false;
};

// 处理详细信息删除
const handleDetailDelete = async (row) => {
  await handleDelete(row);
  detailVisible.value = false;
};

// 导入功能
const handleImport = () => {
  importVisible.value = true;
};

// 处理导入成功
const handleImportSuccess = async () => {
  ElMessage.success("导入完成");
  await fetchUsers();
};

// 批量导出功能
const handleExportBatch = async () => {
  try {
    loading.value = true;

    const params = {
      keyword: keyword.value,
      filter: filterGroups.value,
      sort: sortRules.value,
    };

    const res = await request.post(API_ENDPOINTS.EXPORT_USER, params);

    if (res.code === 200) {
      ElMessage.success("导出任务已提交，完成后会收到通知");
    }
  } catch (error) {
    handleRequestError(error, "导出失败");
  } finally {
    loading.value = false;
  }
};

// 批量删除功能（删除所有筛选数据）
const handleDeleteBatch = async () => {
  const hasFilter =
    keyword.value ||
    filterGroups.value.some((group) => group.conditions.length > 0) ||
    sortRules.value.length > 0;

  if (!hasFilter) {
    ElMessage.warning("请先设置筛选条件");
    return;
  }

  try {
    await ElMessageBox.confirm("确定要删除所有符合筛选条件的数据吗？", "警告", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "danger",
    });

    loading.value = true;

    const deleteParams = {
      filter: filterGroups.value,
    };

    const res = await request.post(
      API_ENDPOINTS.BATCH_ALL_DELETE_USER,
      deleteParams,
    );

    if (res.code === 200) {
      ElMessage.success("删除成功");
      await fetchUsers();
      clearSelection();
    }
  } catch (error) {
    if (error !== "cancel") {
      handleRequestError(error, "删除失败");
    }
  } finally {
    loading.value = false;
  }
};

// 导出选中数据
const handleExportSelected = async () => {
  if (!hasSelectedRows.value) {
    ElMessage.warning("请先选择要导出的数据");
    return;
  }

  try {
    loading.value = true;

    const ids = selectedRows.value.map((row) => row.id);
    const res = await request.post(API_ENDPOINTS.EXPORT_USER, {
      ids,
    });

    if (res.code === 200) {
      ElMessage.success("导出任务已提交，完成后会收到通知");
    }
  } catch (error) {
    handleRequestError(error, "导出失败");
  } finally {
    loading.value = false;
  }
};

// 删除选中数据
const handleDeleteSelected = async () => {
  if (!hasSelectedRows.value) {
    ElMessage.warning("请先选择要删除的数据");
    return;
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedRows.value.length} 条数据吗？`,
      "提示",
      {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      },
    );

    const ids = selectedRows.value.map((row) => row.id);
    const res = await request.post(API_ENDPOINTS.BATCH_DELETE_USER, {
      ids,
    });
    if (res.code === 200) {
      ElMessage.success(`删除成功 ${selectedRows.value.length} 条数据`);
      await fetchUsers();
      clearSelection();
    }
  } catch (error) {
    if (error !== "cancel") {
      handleRequestError(error, "删除失败");
    }
  }
};

// 批量修改选中数据
const handleModifySelected = () => {
  if (!hasSelectedRows.value) {
    ElMessage.warning("请先选择要修改的数据");
    return;
  }
  batchModifyVisible.value = true;
};

// 处理批量修改提交
const handleBatchModifySubmit = async ({ data }) => {
  try {
    const res = await request.post(API_ENDPOINTS.BATCH_UPDATE_USER, {
      data: data,
    });
    if (res.code === 200) {
      ElMessage.success(`修改成功 ${res.data.affected} 条数据`);
      await fetchUsers();
      clearSelection();
      batchModifyVisible.value = false;
    }
  } catch (error) {
    handleRequestError(error, "修改失败");
  }
};

// 处理复制到添加页面
const handleCopyToAdd = (copiedData) => {
  form.value = {
    ...createEmptyForm(),
    username: copiedData.username,
    name: copiedData.name,
    phone: copiedData.phone,
    email: copiedData.email,
    deptId: copiedData.deptId,
    deptName: copiedData.deptName || "",
    avatar: copiedData.avatar,
    images: copiedData.images || [],
    attachments: copiedData.attachments || [],
    status: copiedData.status,
  };
  dialogVisible.value = true;
  detailVisible.value = false;
};

// 复制用户
const handleCopyUser = (row) => {
  handleCopyToAdd(row);
};

// 角色提交
const handleRoleSubmit = async (roleData) => {
  try {
    let res;
    if (roleData.id) {
      res = await request.post(API_ENDPOINTS.UPDATE_ROLE, {
        data: {
          id: roleData.id,
          name: roleData.name,
          code: roleData.code,
          description: roleData.description,
          status: roleData.status,
        },
      });
    } else {
      res = await request.post(API_ENDPOINTS.CREATE_ROLE, {
        data: {
          name: roleData.name,
          code: roleData.code,
          description: roleData.description,
          status: roleData.status,
        },
      });
    }

    if (res.code === 200) {
      ElMessage.success(roleData.id ? "更新成功" : "创建成功");
      await fetchRoleTree();
      roleDialogVisible.value = false;
    }
  } catch (error) {
    handleRequestError(error, roleData.id ? "更新失败" : "创建失败");
  }
};

// 启用用户
const handleEnableUser = async (row) => {
  try {
    const res = await request.post(API_ENDPOINTS.UPDATE_USER, {
      data: {
        id: row.id,
        status: 1,
      },
    });
    if (res.code === 200) {
      ElMessage.success("启用成功");
      fetchUsers();
    }
  } catch (error) {
    handleRequestError(error, "启用失败");
  }
};

// 禁用用户
const handleDisableUser = async (row) => {
  try {
    const res = await request.post(API_ENDPOINTS.UPDATE_USER, {
      data: {
        id: row.id,
        status: 0,
      },
    });
    if (res.code === 200) {
      ElMessage.success("禁用成功");
      fetchUsers();
    }
  } catch (error) {
    handleRequestError(error, "禁用失败");
  }
};

// 应用筛选
const applyFilter = () => {
  currentPage.value = 1;
  fetchUsers();
};

// 重置筛选
const resetFilter = () => {
  filterGroups.value = [
    {
      groupLogic: "and",
      conditionLogic: "and",
      conditions: [],
    },
  ];
  // 重置后不再绑定任何方案（header 方案名由 watch 联动清空）
  currentPresetId.value = null;
  presetSnapshot.value = "";
  currentPage.value = 1;
  fetchUsers();
};

// ==================== 保存的筛选条件（按用户 + 页面隔离） ====================
const deepClone = (value) =>
  value === undefined || value === null ? null : JSON.parse(JSON.stringify(value));

// 加载当前页面已保存的方案（列表项含名称与条件，供下拉套用）
const loadFilterPresets = async () => {
  try {
    const res = await request.post(FILTER_PRESET_API.list, {
      page: FILTER_PRESET_PAGE,
    });
    filterPresets.value = res.code === 200 ? res.data?.items || [] : [];
  } catch (error) {
    filterPresets.value = [];
  }
};

// 套用已保存方案：覆盖条件构造器内容、展开面板并立即查询
const applyFilterPreset = (preset) => {
  const groups = Array.isArray(preset.filterGroups)
    ? deepClone(preset.filterGroups)
    : [];
  filterGroups.value = groups.length
    ? groups
    : [{ groupLogic: "and", conditionLogic: "and", conditions: [] }];
  groupsLogic.value = preset.groupsLogic || "and";
  // 绑定当前方案（header 展示方案名、下拉高亮、保存条件走覆盖更新）并记录条件快照
  currentPresetId.value = preset.id;
  presetSnapshot.value = filterSignature();
  showAdvancedSearch.value = true;
  currentPage.value = 1;
  fetchUsers();
};

// 下拉选中方案（command 为方案ID）
const handleFilterPresetCommand = (presetId) => {
  const preset = filterPresets.value.find((item) => item.id === presetId);
  if (preset) applyFilterPreset(preset);
};

// 以当前条件新建方案（保存条件 / 另存为共用），成功后该方案成为当前生效方案
const createFilterPreset = async (name) => {
  try {
    const res = await request.post(FILTER_PRESET_API.save, {
      page: FILTER_PRESET_PAGE,
      name,
      groupsLogic: groupsLogic.value,
      filterGroups: filterGroups.value,
    });
    if (res.code === 200) {
      ElMessage.success("保存成功");
      const savedId = res.data?.id ?? null;
      presetSnapshot.value = filterSignature();
      // 先刷新方案列表再绑定ID，避免绑定后方案名尚未加载导致筛选面板误判为「未选中方案」
      await loadFilterPresets();
      currentPresetId.value = savedId;
    } else {
      ElMessage.error(res.message || "保存失败");
    }
  } catch (error) {
    ElMessage.error(error.message || "保存失败");
  }
};

// 用当前条件覆盖更新当前方案（名称随保存流程提交：改了名称则一并重命名）
const updateFilterPreset = async (name) => {
  if (currentPresetId.value === null) return;
  try {
    const res = await request.post(FILTER_PRESET_API.update, {
      id: currentPresetId.value,
      page: FILTER_PRESET_PAGE,
      name,
      groupsLogic: groupsLogic.value,
      filterGroups: filterGroups.value,
    });
    if (res.code === 200) {
      ElMessage.success("更新成功");
      presetSnapshot.value = filterSignature();
      await loadFilterPresets();
    } else {
      ElMessage.error(res.message || "更新失败");
    }
  } catch (error) {
    ElMessage.error(error.message || "更新失败");
  }
};

// 保存条件：已选中方案时覆盖更新（名称由筛选面板预填原名称，改名即重命名）；未选中方案时新建
const handleFilterPresetSave = async (name) => {
  if (!name) return;
  if (currentPresetId.value === null) {
    await createFilterPreset(name);
    return;
  }
  await updateFilterPreset(name);
};

// 另存为：无论当前是否选中方案，均以新名称新建方案
const handleFilterPresetSaveAs = async (name) => {
  if (name) await createFilterPreset(name);
};

// 删除已保存方案（下拉项右侧悬停图标触发，调用方已阻止冒泡以免触发套用）
const handleFilterPresetDelete = async (preset) => {
  try {
    await ElMessageBox.confirm(`确定要删除筛选条件「${preset.name}」吗？`, "提示", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    });
  } catch (error) {
    return;
  }
  try {
    const res = await request.post(FILTER_PRESET_API.delete, { id: preset.id });
    if (res.code === 200) {
      ElMessage.success("删除成功");
      // 删除的正是当前生效方案时，解除绑定（header 方案名由 watch 联动清空）
      if (preset.id === currentPresetId.value) {
        currentPresetId.value = null;
        presetSnapshot.value = "";
      }
      await loadFilterPresets();
    } else {
      ElMessage.error(res.message || "删除失败");
    }
  } catch (error) {
    ElMessage.error(error.message || "删除失败");
  }
};
</script>

<style>
@import "./style/organization.css";
</style>
