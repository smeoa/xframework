<template>
  <el-container class="menu-container">
    <el-aside width="240px" class="menu-aside">
      <el-card class="menu-aside-card">
        <template #header>
          <div class="menu-aside-header">菜单树</div>
        </template>
        <MenuTree
          :menu-tree="menuTree"
          @node-click="handleTreeNodeClick"
          @menu-updated="handleMenuUpdated"
          @add-child-menu="handleAddChildMenu"
          ref="menuTreeRef"
        />
      </el-card>
    </el-aside>
    <el-main class="menu-main" style="padding: 0">
      <el-card class="menu-card" :class="{ 'is-filter-open': showAdvancedSearch }">
        <template #header>
          <div v-if="selectedRows.length === 0" class="card-header">
            <span>
              <el-button type="primary" v-permission="'sysmenu:create'" @click="handleAdd" class="action-btn">
                <el-icon>
                  <Plus />
                </el-icon>
                添加
              </el-button>
              <el-button type="primary" v-permission="'sysmenu:import'" @click="handleImport" class="action-btn">
                <i class="iconfont x-daoru"></i>
                导入
              </el-button>
              <el-button type="primary" v-permission="'sysmenu:export'" @click="handleExportBatch" class="action-btn">
                <i class="iconfont x-daochu"></i>
                导出
              </el-button>
              <el-button type="danger" v-permission="'sysmenu:delete'" @click="handleDeleteBatch" class="action-btn">
                <i class="iconfont x-shanchu"></i>
                删除
              </el-button>
            </span>
            <div class="header-actions">
              <el-input v-model="keyword" placeholder="搜索菜单" clearable class="search-input" @keyup.enter="handleSearch">
                <template #prefix>
                  <el-icon>
                    <Search />
                  </el-icon>
                </template>
              </el-input>
              <el-button @click="handleSearch" type="primary">
                <el-icon>
                  <Search />
                </el-icon>
                搜索
              </el-button>
              <el-badge :value="sortBadgeCount" :hidden="sortBadgeCount === 0" type="danger">
                <el-button type="primary" @click="showSortDialog = true" class="action-btn">
                  <el-icon>
                    <Sort />
                  </el-icon>
                  排序
                </el-button>
              </el-badge>
              <el-badge :value="filterBadgeCount" :hidden="filterBadgeCount === 0" type="danger">
                <div class="filter-split">
                  <el-button type="primary" @click="showAdvancedSearch = !showAdvancedSearch" class="action-btn">
                    <el-icon>
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
            <el-button type="primary" v-permission="'sysmenu:export'" @click="handleExportSelected">
              <el-icon>
                <Download />
              </el-icon>
              导出
            </el-button>
            <el-button type="danger" v-permission="'sysmenu:delete'" @click="handleDeleteSelected">
              <el-icon>
                <Delete />
              </el-icon>
              删除
            </el-button>
            <el-button type="warning" v-permission="'sysmenu:update'" @click="handleModifySelected">
              <el-icon>
                <Edit />
              </el-icon>
              批量修改
            </el-button>
          </div>
        </template>
        <div class="main-content">
          <div class="table-area">
            <DataTable ref="dataTableRef" :table-data="tableData" :visible-fields="visibleFields" :field-config="fieldConfig"
              :loading="loading" :current-page="currentPage" :page-size="pageSize" :total="total"
              :page-sizes="PAGE_SIZES" :sort-rules="sortRules" :filter-groups="filterGroups"
              @selectionChange="handleSelectionChange"
              @rowDblclick="handleRowDblclick" @edit="handleEdit" @delete="handleDelete"
              @fieldSettings="openFieldSettings"
              @headerSort="handleHeaderSort" @headerFreeze="handleHeaderFreeze" @headerHide="handleHeaderHide"
              @headerFilter="handleHeaderFilter"
              @sizeChange="handleSizeChange" @currentChange="handleCurrentChange" />
          </div>
        </div>
      </el-card>
    </el-main>
    <el-aside width="320px" class="advanced-search-aside" v-if="showAdvancedSearch">
      <FilterPanel
        v-model:filterGroups="filterGroups"
        v-model:groupsLogic="groupsLogic"
        :field-options="filterFieldOptions"
        @apply="applyFilter"
        @reset="resetFilter"
        :current-preset-name="currentPresetName"
        :preset-names="presetNames"
        @save="handleFilterPresetSave"
        @save-as="handleFilterPresetSaveAs"
      />
    </el-aside>
  </el-container>

  <MenuEditDialog v-model:visible="dialogVisible" v-model:display-mode="editDisplayMode" :menu="form"
    @submit="handleSubmit" />

  <Import v-model:visible="importDialogVisible" @import-success="handleImportSuccess" />

  <FieldSettings v-model:visible="fieldSettingsVisible" :fields="visibleFields" :field-config="fieldConfig"
    :field-options="fieldConfig" storage-key="menuAllFieldConfig" @save="saveFieldSettings" />

  <SortSettings v-model:visible="showSortDialog" :sort-rules="sortRules" :field-options="sortFieldOptions"
    @save="saveSortRules" />
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  Plus,
  Search,
  Filter,
  Delete,
  Edit,
  Download,
  Sort,
  ArrowDown,
} from "@element-plus/icons-vue";
import request, { camelToSnake, snakeToCamelKey } from "@/utils/request";
import { pageSubtitle } from "@/utils/pageSubtitle";
import MenuEditDialog from "./components/MenuEditDialog.vue";
import MenuTree from "./components/MenuTree.vue";
import DataTable from "./components/DataTable.vue";
import Import from "./components/Import.vue";
import FieldSettings from "./components/FieldSettings.vue";
import SortSettings from "./components/SortSettings.vue";
import FilterPanel from "./components/FilterPanel.vue";

const PAGE_SIZES = [20, 50, 100];
const DEFAULT_PAGE_SIZE = 20;
const DEFAULT_PAGE = 1;
const LOCAL_STORAGE_KEYS = {
  VISIBLE_FIELDS: "menuVisibleFields",
  FIELD_CONFIG: "menuFieldConfig",
};
const API_ENDPOINTS = {
  LIST: "/admin/menu/get-menu-list",
  CREATE: "/admin/menu/create-menu",
  UPDATE: "/admin/menu/update-menu",
  DELETE: "/admin/menu/delete-menu",
  EXPORT: "/admin/menu/export-menu",
  BATCH_UPDATE: "/admin/menu/batch-update-menus",
  BATCH_DELETE: "/admin/menu/batch-menu",
  BATCH_ALL_DELETE: "/admin/menu/batch-all-menu",
  TREE: "/admin/menu/get-menu-tree",
};
// 保存的筛选条件：后台各列表页共用接口（admin/filter_preset），page 传本页面标识
const FILTER_PRESET_PAGE = "menu";
const FILTER_PRESET_API = {
  list: "/admin/filter-preset/list",
  save: "/admin/filter-preset/save",
  update: "/admin/filter-preset/update",
  delete: "/admin/filter-preset/delete",
};

const LOCAL_STORAGE_KEYS_FULL = {
  VISIBLE_FIELDS: "menuVisibleFields",
  FIELD_CONFIG: "menuFieldConfig",
  SEARCH_FIELDS: "menuSearchFields",
  SORT_RULES: "menuSortRules",
};

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

const handleRequestError = (error, defaultMessage) => {
  if (error.response?.data?.detail === "Method Not Allowed") {
    ElMessage.error("请求方法错误，请检查 API 接口配置");
  } else {
    ElMessage.error(error.message || defaultMessage);
  }
};

const createEmptyForm = () => ({
  id: null,
  name: "",
  path: "",
  icon: "",
  sort: 0,
  type: 1,
  status: 1,
  pid: null,
});

const hasSelectedRows = computed(() => selectedRows.value.length > 0);
const sortBadgeCount = computed(() => sortRules.value.length);
const filterBadgeCount = computed(() =>
  filterGroups.value.reduce((sum, group) => sum + group.conditions.length, 0)
);

const menuTree = ref([]);
const menuTreeRef = ref(null);
const selectedMenuId = ref(null);

const tableData = ref([]);
const tableRef = ref(null);
const loading = ref(false);
const currentPage = ref(DEFAULT_PAGE);
const pageSize = ref(DEFAULT_PAGE_SIZE);
const total = ref(0);
const selectedRows = ref([]);

const keyword = ref("");
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

const fieldSettingsVisible = ref(false);
const showSortDialog = ref(false);
const sortRules = ref([]);
const visibleFields = ref([
  "id",
  "name",
  "path",
  "icon",
  "type",
  "status",
  "createTime",
  "updateTime",
]);
const fieldConfig = ref([
  { value: "id", label: "ID", width: 60, fixed: "" },
  { value: "name", label: "菜单名称", width: 140, fixed: "" },
  { value: "path", label: "路径", width: 160, fixed: "" },
  { value: "icon", label: "图标", width: 100, fixed: "" },
  { value: "type", label: "类型", width: 80, fixed: "" },
  { value: "status", label: "状态", width: 70, fixed: "" },
  { value: "createTime", label: "创建时间", width: 160, fixed: "" },
  { value: "updateTime", label: "更新时间", width: 160, fixed: "" },
]);

// 筛选/排序字段使用数据库列名：request.js 只转换键名，作为字段名出现的值会原样透传给后端
const MENU_DB_FIELD_OPTIONS = [
  { value: "id", label: "ID" },
  { value: "name", label: "菜单名称" },
  { value: "path", label: "路径" },
  { value: "component", label: "组件" },
  { value: "icon", label: "图标" },
  { value: "sort", label: "排序" },
  { value: "type", label: "类型" },
  { value: "permission", label: "权限标识" },
  { value: "status", label: "状态" },
  { value: "create_time", label: "创建时间" },
  { value: "update_time", label: "更新时间" },
];
const sortFieldOptions = MENU_DB_FIELD_OPTIONS;
// 时间列筛选时字符串值无法绑定（框架未按列类型转换），暂不纳入筛选字段
const filterFieldOptions = MENU_DB_FIELD_OPTIONS.filter(
  (option) => !["create_time", "update_time"].includes(option.value),
);

const form = ref(createEmptyForm());
const dialogVisible = ref(false);
const editDisplayMode = ref("dialog");

const importDialogVisible = ref(false);
const dataTableRef = ref(null);

watch(showAdvancedSearch, () => {
  nextTick(() => {
    dataTableRef.value?.doLayout?.();
  });
});

const fetchMenuTree = async () => {
  try {
    const res = await request.post(API_ENDPOINTS.TREE, {});
    if (res.code === 200) {
      menuTree.value = res.data || [];
    }
  } catch (error) {
    console.error("获取菜单树失败:", error);
  }
};

const fetchData = async () => {
  loading.value = true;
  try {
    const data = {
      page: currentPage.value,
      limit: pageSize.value,
      keyword: keyword.value,
      sort: sortRules.value,
      filter: filterGroups.value,
    };
    const res = await request.post(API_ENDPOINTS.LIST, data);
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

const handleSearch = () => {
  currentPage.value = 1;
  fetchData();
};

const handleTreeNodeClick = (data) => {
  if (data && data.id) {
    if (selectedMenuId.value === data.id) {
      selectedMenuId.value = null;
      if (menuTreeRef.value && menuTreeRef.value.treeRef) {
        menuTreeRef.value.treeRef.setCurrentKey(null);
      }
    } else {
      selectedMenuId.value = data.id;
      if (menuTreeRef.value && menuTreeRef.value.treeRef) {
        menuTreeRef.value.treeRef.setCurrentKey(data.id);
      }
    }
    keyword.value = "";
    currentPage.value = 1;
    fetchData();
  } else {
    selectedMenuId.value = null;
    tableData.value = [];
    total.value = 0;
  }
};

const handleMenuUpdated = () => {
  fetchMenuTree();
  fetchData();
};

const handleAddChildMenu = (parent) => {
  form.value = { ...createEmptyForm(), pid: parent.id };
  dialogVisible.value = true;
};

const openFieldSettings = () => {
  fieldSettingsVisible.value = true;
};

const saveFieldSettings = (fieldsConfig) => {
  localStorage.setItem(
    LOCAL_STORAGE_KEYS_FULL.VISIBLE_FIELDS,
    JSON.stringify(fieldsConfig.map((item) => item.value)),
  );
  localStorage.setItem(
    LOCAL_STORAGE_KEYS_FULL.FIELD_CONFIG,
    JSON.stringify(fieldsConfig),
  );
  visibleFields.value = fieldsConfig
    .filter((item) => item.value)
    .map((item) => item.value);
  fieldConfig.value = fieldsConfig;
  ElMessage.success("字段设置已保存");
};

const saveSortRules = (rules) => {
  sortRules.value = rules;
  localStorage.setItem(LOCAL_STORAGE_KEYS_FULL.SORT_RULES, JSON.stringify(rules));
  currentPage.value = 1;
  fetchData();
};

// ==================== 列头菜单操作 ====================
// 字段设置弹窗读取「全量字段配置」缓存（menuAllFieldConfig）渲染字段清单，
// 列头操作需同步该缓存，避免弹窗读到过期的冻结 / 可见状态（缓存不存在时不臆造目录）
const ALL_FIELD_CONFIG_KEY = "menuAllFieldConfig";

const syncAllFieldConfig = (fieldValue, patch) => {
  let allConfig = null;
  try {
    const raw = localStorage.getItem(ALL_FIELD_CONFIG_KEY);
    allConfig = raw ? JSON.parse(raw) : null;
  } catch (error) {
    allConfig = null;
  }
  // 缓存不存在时以当前 fieldConfig 为基准创建，保证「隐藏此列」的状态可跨刷新恢复
  if (!Array.isArray(allConfig) || !allConfig.length) {
    allConfig = fieldConfig.value.map((item) => ({
      value: item.value,
      label: item.label,
      width: item.width,
      fixed: item.fixed,
      visible: item.visible ?? visibleFields.value.includes(item.value),
    }));
  }
  localStorage.setItem(
    ALL_FIELD_CONFIG_KEY,
    JSON.stringify(
      allConfig.map((item) =>
        item.value === fieldValue ? { ...item, ...patch } : item,
      ),
    ),
  );
};

// 列头操作后按当前字段配置整体落盘（表格据此恢复宽度 / 固定 / 顺序）
const persistFieldConfig = () => {
  localStorage.setItem(
    LOCAL_STORAGE_KEYS_FULL.FIELD_CONFIG,
    JSON.stringify(fieldConfig.value),
  );
};

// 列头菜单：升序 / 降序（覆盖为单字段排序规则）；direction 为空表示取消排序
const handleHeaderSort = (fieldValue, direction) => {
  if (!direction) {
    saveSortRules([]);
    return;
  }
  saveSortRules([
    {
      id: Date.now() + Math.random(),
      field: camelToSnake(fieldValue),
      direction,
    },
  ]);
};

// 列头菜单：冻结列（未冻结 -> 左固定；已冻结 -> 取消固定）
const handleHeaderFreeze = (fieldValue) => {
  fieldConfig.value = fieldConfig.value.map((item) =>
    item.value === fieldValue
      ? { ...item, fixed: item.fixed ? "" : "left" }
      : item,
  );
  persistFieldConfig();
  const fixed =
    fieldConfig.value.find((item) => item.value === fieldValue)?.fixed || "";
  syncAllFieldConfig(fieldValue, { fixed });
  ElMessage.success(fixed ? "已冻结该列" : "已取消冻结");
};

// 列头菜单：隐藏此列
const handleHeaderHide = (fieldValue) => {
  visibleFields.value = visibleFields.value.filter(
    (item) => item !== fieldValue,
  );
  localStorage.setItem(
    LOCAL_STORAGE_KEYS_FULL.VISIBLE_FIELDS,
    JSON.stringify(visibleFields.value),
  );
  // 保留字段配置中的该字段并标记为不可见，保证字段设置弹窗仍可重新开启该列
  fieldConfig.value = fieldConfig.value.map((item) =>
    item.value === fieldValue ? { ...item, visible: false } : item,
  );
  persistFieldConfig();
  syncAllFieldConfig(fieldValue, { visible: false });
  ElMessage.success("已隐藏该列");
};

// 列头菜单：写入该列筛选条件（与筛选面板同步：同字段覆盖，不重复追加）
const handleHeaderFilter = ({ field, operator, value }) => {
  const snakeField = camelToSnake(field);
  const groups = deepClone(filterGroups.value) || [];
  if (!groups.length) {
    groups.push({ groupLogic: "and", conditionLogic: "and", conditions: [] });
  }
  if (!Array.isArray(groups[0].conditions)) groups[0].conditions = [];
  const conditions = groups[0].conditions;
  const index = conditions.findIndex((cond) => cond.field === snakeField);
  // 「为空 / 不为空」无需值；其余操作符值为空视为移除该字段条件
  const noValueOperator = ["is_null", "is_not_null"].includes(operator);
  const isEmpty = !noValueOperator && String(value ?? "").trim() === "";
  if (isEmpty) {
    if (index > -1) conditions.splice(index, 1);
  } else if (index > -1) {
    conditions[index] = { field: snakeField, operator, value };
  } else {
    conditions.push({ field: snakeField, operator, value });
  }
  filterGroups.value = groups;
  // 手动改动条件后解除与已保存方案的绑定（header 方案名由 watch 联动清空）
  currentPresetId.value = null;
  presetSnapshot.value = "";
  currentPage.value = 1;
  fetchData();
};

const loadFieldSettings = () => {
  const defaultVisible = [...visibleFields.value];
  const defaultConfig = [...fieldConfig.value];

  // 被列头「隐藏此列」显式隐藏的字段（menuAllFieldConfig 中 visible:false）：
  // 补全默认列时需跳过，否则默认列隐藏后刷新会重新出现
  const hiddenFields = new Set();
  try {
    const rawAllConfig = localStorage.getItem(ALL_FIELD_CONFIG_KEY);
    const allConfig = rawAllConfig ? JSON.parse(rawAllConfig) : [];
    if (Array.isArray(allConfig)) {
      allConfig.forEach((item) => {
        if (item.visible === false) hiddenFields.add(item.value);
      });
    }
  } catch (e) {
    console.error("加载全量字段配置失败:", e);
  }

  const savedVisible = localStorage.getItem(LOCAL_STORAGE_KEYS_FULL.VISIBLE_FIELDS);
  if (savedVisible) {
    try {
      const fields = JSON.parse(savedVisible);
      if (Array.isArray(fields)) {
        // 历史版本按 snake_case 存入（如 create_time），统一迁移为 camelCase 后去重
        visibleFields.value = [...new Set(fields.map(snakeToCamelKey))];
        defaultVisible.forEach((field) => {
          if (!visibleFields.value.includes(field) && !hiddenFields.has(field)) {
            visibleFields.value.push(field);
          }
        });
      }
    } catch (e) {
      console.error("加载字段设置失败:", e);
    }
  }

  const savedConfig = localStorage.getItem(LOCAL_STORAGE_KEYS_FULL.FIELD_CONFIG);
  if (savedConfig) {
    try {
      const config = JSON.parse(savedConfig);
      if (Array.isArray(config)) {
        // 历史版本按 snake_case 存入，统一迁移为 camelCase 后按 value 去重
        const migratedConfig = [];
        config.forEach((item) => {
          const value = snakeToCamelKey(item.value);
          if (!migratedConfig.some((saved) => saved.value === value)) {
            migratedConfig.push({ ...item, value });
          }
        });
        fieldConfig.value = migratedConfig;
        defaultConfig.forEach((defaultItem) => {
          const exists = fieldConfig.value.find(
            (item) => item.value === defaultItem.value,
          );
          if (!exists) {
            fieldConfig.value.push(defaultItem);
          }
        });
      }
    } catch (e) {
      console.error("加载字段配置失败:", e);
    }
  }

  const savedSort = localStorage.getItem(LOCAL_STORAGE_KEYS_FULL.SORT_RULES);
  if (savedSort) {
    try {
      const rules = JSON.parse(savedSort);
      if (Array.isArray(rules)) {
        // 历史版本排序字段为 camelCase（如 createTime），统一迁移为数据库列名
        sortRules.value = rules.map((rule) => ({
          ...rule,
          field: camelToSnake(rule.field),
        }));
      }
    } catch (e) {
      console.error("加载排序规则失败:", e);
    }
  }
};

onMounted(() => {
  loadFieldSettings();
  loadFilterPresets();
  fetchMenuTree();
  fetchData();
});

onUnmounted(() => {
  pageSubtitle.value = "";
});

const handleAdd = () => {
  form.value = createEmptyForm();
  dialogVisible.value = true;
};

const handleEdit = (row) => {
  form.value = { ...row };
  dialogVisible.value = true;
};

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm("确定要删除该菜单吗？", "提示", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    });
    const res = await request.post(API_ENDPOINTS.DELETE, {
      data: { id: row.id },
    });
    if (res.code === 200) {
      ElMessage.success("删除成功");
      fetchData();
      fetchMenuTree();
    }
  } catch (error) {
    if (error !== "cancel") {
      handleRequestError(error, "删除失败");
    }
  }
};

const handleSubmit = async (menuData) => {
  try {
    let res;
    if (menuData.id) {
      res = await request.post(API_ENDPOINTS.UPDATE, {
        data: menuData,
      });
    } else {
      res = await request.post(API_ENDPOINTS.CREATE, {
        data: menuData,
      });
    }
    if (res.code === 200) {
      ElMessage.success(menuData.id ? "更新成功" : "创建成功");
      fetchData();
      fetchMenuTree();
    }
  } catch (error) {
    handleRequestError(error, menuData.id ? "更新失败" : "创建失败");
  }
};

const handleSizeChange = (val) => {
  pageSize.value = val;
  fetchData();
};

const handleCurrentChange = (val) => {
  currentPage.value = val;
  fetchData();
};

const handleSelectionChange = (val) => {
  selectedRows.value = val;
};

const handleRowDblclick = (row) => {
  handleEdit(row);
};

const handleImport = () => {
  importDialogVisible.value = true;
};

const handleImportSuccess = async () => {
  ElMessage.success("导入完成");
  await fetchData();
  await fetchMenuTree();
};

const handleExportBatch = async () => {
  try {
    loading.value = true;
    const params = {
      keyword: keyword.value,
      userId: "current_user",
    };
    const res = await request.post(API_ENDPOINTS.EXPORT, params);
    ElMessage.success("导出任务已提交到后台处理，导出完成后会收到通知");
  } catch (error) {
    handleRequestError(error, "导出失败");
  } finally {
    loading.value = false;
  }
};

const handleDeleteBatch = async () => {
  const hasFilter = keyword.value;
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
    const res = await request.post(API_ENDPOINTS.BATCH_ALL_DELETE, {});
    if (res.code === 200) {
      ElMessage.success("删除成功");
      await fetchData();
      await fetchMenuTree();
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

const handleExportSelected = async () => {
  if (!hasSelectedRows.value) {
    ElMessage.warning("请先选择要导出的数据");
    return;
  }
  try {
    loading.value = true;
    const ids = selectedRows.value.map((row) => row.id);
    const res = await request.post(API_ENDPOINTS.EXPORT, { ids });
    ElMessage.success("导出任务已提交到后台处理");
  } catch (error) {
    handleRequestError(error, "导出失败");
  } finally {
    loading.value = false;
  }
};

const handleDeleteSelected = async () => {
  if (!hasSelectedRows.value) {
    ElMessage.warning("请先选择要删除的数据");
    return;
  }
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${selectedRows.value.length} 条数据吗？`, "提示", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    });
    const ids = selectedRows.value.map((row) => row.id);
    const res = await request.post(API_ENDPOINTS.BATCH_DELETE, { ids });
    if (res.code === 200) {
      ElMessage.success(`删除成功 ${selectedRows.value.length} 条数据`);
      await fetchData();
      await fetchMenuTree();
      clearSelection();
    }
  } catch (error) {
    if (error !== "cancel") {
      handleRequestError(error, "删除失败");
    }
  }
};

const handleModifySelected = () => {
  if (!hasSelectedRows.value) {
    ElMessage.warning("请先选择要修改的数据");
    return;
  }
  ElMessageBox.prompt("请输入要修改的状态值（1=启用，0=禁用）", "批量修改状态", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
  }).then(async ({ value }) => {
    try {
      const ids = selectedRows.value.map((row) => row.id);
      const res = await request.post(API_ENDPOINTS.BATCH_UPDATE, {
        data: { ids, status: parseInt(value) },
      });
      if (res.code === 200) {
        ElMessage.success(`修改成功 ${res.data.affected} 条数据`);
        await fetchData();
        clearSelection();
      }
    } catch (error) {
      handleRequestError(error, "修改失败");
    }
  }).catch(() => {});
};

const clearSelection = () => {
  if (tableRef.value) {
    tableRef.value.clearSelection();
  }
  selectedRows.value = [];
};

const applyFilter = () => {
  currentPage.value = 1;
  fetchData();
};

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
  fetchData();
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
  fetchData();
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

<style scoped>
</style>

<style>
@import "./style/menu.css";
</style>