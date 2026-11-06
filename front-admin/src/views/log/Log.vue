<template>
  <el-container class="admin-user-container log-container">
    <el-main class="admin-user-main log-main">
      <el-card class="admin-user-card log-card" :class="{ 'is-filter-open': showAdvancedSearch }">
        <template #header>
          <div v-if="selectedRows.length === 0" class="card-header">
            <span>
              <el-button v-permission="'log:clean'" type="danger" @click="handleClean" class="action-btn">
                <el-icon>
                  <Delete />
                </el-icon>
                清理历史日志
              </el-button>
            </span>
            <div class="header-actions">
              <el-input v-model="keyword" placeholder="搜索日志内容" clearable class="search-input"
                @keyup.enter="handleSearch">
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
                <el-button type="primary" @click="openSortSettings" class="action-btn">
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
                    {{ showAdvancedSearch ? '收起' : '筛选' }}
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
            <el-button type="danger" v-permission="'log:delete'" @click="handleDeleteSelected">
              <el-icon>
                <Delete />
              </el-icon>
              删除
            </el-button>
          </div>
        </template>

        <div class="main-content">
          <div class="table-area">
            <el-table v-loading="loading" :data="tableData" border stripe class="log-table" height="100%"
              @selection-change="handleSelectionChange" @row-dblclick="handleView">
              <el-table-column type="selection" width="46" header-class-name="selection-header" />
              <!-- 数据列：按「字段设置」配置动态渲染（顺序 / 宽度 / 固定 / 显隐） -->
              <template v-for="col in columnConfig" :key="col.value">
                <el-table-column :label="col.label" :width="col.flexible ? undefined : col.width"
                  :min-width="col.flexible ? col.width : undefined" :fixed="col.fixed || false"
                  :align="col.align || 'left'" :show-overflow-tooltip="useTooltip(col.value)">
                  <template #header>
                    <div class="col-header">
                      <span class="col-header-label">{{ col.label }}</span>
                      <el-popover v-model:visible="headerMenuVisible[col.value]" trigger="click"
                        placement="bottom-start" :width="220" popper-class="col-header-menu-popper">
                        <template #reference>
                          <span class="col-header-menu-trigger" :class="{ 'has-state': !!headerStateMap[col.value] }"
                            title="列操作" @click.stop="onHeaderMenuTrigger(col.value)">
                            <el-icon v-if="headerStateMap[col.value] === 'asc'" class="col-header-menu-sort">
                              <SortUp />
                            </el-icon>
                            <el-icon v-else-if="headerStateMap[col.value] === 'desc'" class="col-header-menu-sort">
                              <SortDown />
                            </el-icon>
                            <el-icon v-else-if="headerStateMap[col.value] === 'filter'" class="col-header-menu-sort">
                              <Filter />
                            </el-icon>
                            <span v-else-if="headerStateMap[col.value] === 'filter-asc'"
                              class="col-header-menu-sort col-header-menu-sort--combo">
                              <el-icon>
                                <Filter />
                              </el-icon>
                              <el-icon class="col-header-menu-sort-arrow">
                                <CaretTop />
                              </el-icon>
                            </span>
                            <span v-else-if="headerStateMap[col.value] === 'filter-desc'"
                              class="col-header-menu-sort col-header-menu-sort--combo">
                              <el-icon>
                                <Filter />
                              </el-icon>
                              <el-icon class="col-header-menu-sort-arrow">
                                <CaretBottom />
                              </el-icon>
                            </span>
                            <el-icon class="col-header-menu-btn">
                              <MoreFilled />
                            </el-icon>
                          </span>
                        </template>
                        <div class="col-header-menu">
                          <div class="col-header-menu-item"
                            :class="{ 'is-checked': getSortDirection(col.value) === 'asc' }"
                            @click="onHeaderSort(col.value, 'asc')">
                            <el-icon>
                              <SortUp />
                            </el-icon>
                            <span>升序</span>
                            <el-icon v-if="getSortDirection(col.value) === 'asc'" class="col-header-menu-check">
                              <Check />
                            </el-icon>
                          </div>
                          <div class="col-header-menu-item"
                            :class="{ 'is-checked': getSortDirection(col.value) === 'desc' }"
                            @click="onHeaderSort(col.value, 'desc')">
                            <el-icon>
                              <SortDown />
                            </el-icon>
                            <span>降序</span>
                            <el-icon v-if="getSortDirection(col.value) === 'desc'" class="col-header-menu-check">
                              <Check />
                            </el-icon>
                          </div>
                          <div class="col-header-menu-divider"></div>
                          <div class="col-header-menu-item" :class="{ 'is-checked': isFrozen(col.value) }"
                            @click="onHeaderFreeze(col.value)">
                            <el-icon>
                              <Lock />
                            </el-icon>
                            <span>冻结列</span>
                            <el-icon v-if="isFrozen(col.value)" class="col-header-menu-check">
                              <Check />
                            </el-icon>
                          </div>
                          <div class="col-header-menu-item" @click="onHeaderHide(col.value)">
                            <el-icon>
                              <Hide />
                            </el-icon>
                            <span>隐藏此列</span>
                          </div>
                          <div class="col-header-menu-divider"></div>
                          <div class="col-header-menu-filter">
                            <div class="col-header-menu-filter-head">
                              <el-icon class="col-header-menu-filter-icon">
                                <Filter />
                              </el-icon>
                              <span class="col-header-menu-filter-title">筛选</span>
                              <el-select v-model="filterOperator" class="col-header-menu-filter-operator"
                                :teleported="false">
                                <el-option label="等于" value="eq" />
                                <el-option label="不等于" value="ne" />
                                <el-option label="包含" value="contains" />
                                <el-option label="不包含" value="not_contains" />
                                <el-option label="大于" value="gt" />
                                <el-option label="小于" value="lt" />
                                <el-option label="大于等于" value="gte" />
                                <el-option label="小于等于" value="lte" />
                                <el-option label="为空" value="is_null" />
                                <el-option label="不为空" value="is_not_null" />
                              </el-select>
                            </div>
                            <el-input v-if="!isNoValueOperator" v-model="filterValue" clearable
                              class="col-header-menu-filter-value" placeholder="请输入筛选值" />
                            <el-button type="primary" class="col-header-menu-filter-btn"
                              @click="onHeaderFilter(col.value)">
                              筛选
                            </el-button>
                          </div>
                        </div>
                      </el-popover>
                    </div>
                  </template>
                  <template #default="{ row }">
                    <el-tag v-if="col.value === 'level'" :type="levelTagType(row.level)" size="small">
                      {{ row.level }}
                    </el-tag>
                    <span v-else-if="col.value === 'createTime'">{{ formatTime(row.createTime) }}</span>
                    <span v-else>{{ row[col.value] ?? '-' }}</span>
                  </template>
                </el-table-column>
              </template>
              <el-table-column label="操作" width="120" fixed="right">
                <template #header>
                  <span>操作&nbsp;</span>
                  <el-link @click="columnSettingsVisible = true" underline="never" title="字段设置"
                    style="margin-left: 8px">
                    <el-icon>
                      <Setting />
                    </el-icon>
                  </el-link>
                </template>
                <template #default="{ row }">
                  <div class="cell-actions">
                    <el-tooltip content="详情" placement="top">
                      <span>
                        <el-link type="primary" underline="never" @click="handleView(row)">
                          <el-icon>
                            <View />
                          </el-icon>
                        </el-link>
                      </span>
                    </el-tooltip>
                    <el-tooltip content="删除" placement="top">
                      <span v-permission="'log:delete'">
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

            <el-pagination class="log-pagination" :current-page="currentPage" :page-size="pageSize" :total="total"
              :page-sizes="PAGE_SIZES" layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleSizeChange" @current-change="handleCurrentChange" />
          </div>
        </div>
      </el-card>
    </el-main>

    <!-- 筛选面板：条件构造器（组 / 条件 + 字段 + 操作符 + 值） -->
    <el-aside width="320px" class="advanced-search-aside" v-if="showAdvancedSearch">
      <FilterPanel v-model:filterGroups="filterGroups" v-model:groupsLogic="groupsLogic"
        :field-groups="LOG_FIELD_GROUPS" :field-options="LOG_FIELD_OPTIONS" :current-preset-name="currentPresetName"
        :preset-names="presetNames" @apply="applyFilter" @reset="resetFilter" @save="handleFilterPresetSave"
        @save-as="handleFilterPresetSaveAs" />
    </el-aside>
  </el-container>

  <el-dialog v-model="detailVisible" title="日志详情" width="70%">
    <el-descriptions v-if="currentRow" :column="2" border>
      <el-descriptions-item label="ID">{{ currentRow.id }}</el-descriptions-item>
      <el-descriptions-item label="级别">{{ currentRow.level }}</el-descriptions-item>
      <el-descriptions-item label="模块">{{ currentRow.module || "-" }}</el-descriptions-item>
      <el-descriptions-item label="记录器">{{ currentRow.logger || "-" }}</el-descriptions-item>
      <el-descriptions-item label="函数">{{ currentRow.func || "-" }}</el-descriptions-item>
      <el-descriptions-item label="行号">{{ currentRow.line || "-" }}</el-descriptions-item>
      <el-descriptions-item label="请求方法">{{ currentRow.requestMethod || "-" }}</el-descriptions-item>
      <el-descriptions-item label="请求ID">{{ currentRow.requestId || "-" }}</el-descriptions-item>
      <el-descriptions-item label="请求路径" :span="2">
        {{ currentRow.requestPath || "-" }}
      </el-descriptions-item>
      <el-descriptions-item label="客户端IP">{{ currentRow.clientIp || "-" }}</el-descriptions-item>
      <el-descriptions-item label="用户ID">{{ currentRow.userId ?? "-" }}</el-descriptions-item>
      <el-descriptions-item label="创建时间" :span="2">
        {{ formatTime(currentRow.createTime) }}
      </el-descriptions-item>
      <el-descriptions-item label="日志内容" :span="2">
        <div class="detail-message">{{ currentRow.message || "-" }}</div>
      </el-descriptions-item>
    </el-descriptions>
    <div v-if="currentRow && currentRow.excInfo" class="exc-info">
      <div class="exc-title">异常堆栈</div>
      <pre class="exc-content">{{ currentRow.excInfo }}</pre>
    </div>
  </el-dialog>

  <!-- 列表排序设置对话框（排序规则持久化到 localStorage） -->
  <SortSettings v-model:visible="showSortDialog" :sort-rules="sortRules" :field-options="SORT_FIELD_OPTIONS"
    @save="saveSortRules" />

  <!-- 列表字段设置（自定义显示列） -->
  <ColumnSettings v-model:visible="columnSettingsVisible" :fields="columnConfig.map((item) => item.value)"
    :field-config="columnConfig" :catalog="columnCatalog" :storage-key="COLUMN_SETTINGS_KEY"
    @save="saveColumnSettings" />
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  Search, Delete, View, Sort, Filter, ArrowDown, Setting,
  SortUp, SortDown, MoreFilled, Lock, Hide, Check, CaretTop, CaretBottom,
} from "@element-plus/icons-vue";
import request from "@/utils/request";
import { isAdmin as checkIsAdmin } from "@/utils/permission";
import ColumnSettings from "@/components/table/ColumnSettings.vue";
import FilterPanel from "@/components/table/FilterPanel.vue";
import SortSettings from "@/components/table/SortSettings.vue";
import "./style/log.css";

// ==================== 常量定义 ====================
const PAGE_SIZES = [20, 50, 100];
const DEFAULT_PAGE_SIZE = 20;
const DEFAULT_PAGE = 1;
const MIN_CLEAN_DAYS = 7;
const LEVEL_OPTIONS = [
  { value: "DEBUG", label: "DEBUG" },
  { value: "INFO", label: "INFO" },
  { value: "WARNING", label: "WARNING" },
  { value: "ERROR", label: "ERROR" },
  { value: "CRITICAL", label: "CRITICAL" },
];
const API_ENDPOINTS = {
  LIST: "/admin/log/get-log-list",
  DELETE: "/admin/log/delete-log",
  BATCH_DELETE: "/admin/log/batch-log",
  CLEAN: "/admin/log/clean-log",
};
// 保存的筛选条件：后台各列表页共用接口（admin/filter_preset），page 传 "log"
const FILTER_PRESET_API = {
  list: "/admin/filter-preset/list",
  save: "/admin/filter-preset/save",
  update: "/admin/filter-preset/update",
  delete: "/admin/filter-preset/delete",
};

// 列目录（value 与表格单元格渲染 key 对应；flexible 列用 min-width）
const LOG_COLUMN_CATALOG = [
  { value: "id", label: "ID", width: 80 },
  { value: "level", label: "级别", width: 100 },
  { value: "message", label: "日志内容", width: 320, flexible: true },
  { value: "module", label: "模块", width: 150 },
  { value: "logger", label: "记录器", width: 180 },
  { value: "requestMethod", label: "方法", width: 90 },
  { value: "requestPath", label: "请求路径", width: 220 },
  { value: "clientIp", label: "客户端IP", width: 140 },
  { value: "userId", label: "用户ID", width: 90, adminOnly: true },
  { value: "createTime", label: "创建时间", width: 180 },
];

// 列头可排序 / 可筛选的「列 key → 数据库列」映射（x_log 真实列）
const HEADER_DB_FIELD_MAP = {
  id: "id",
  level: "level",
  message: "message",
  module: "module",
  logger: "logger",
  requestMethod: "request_method",
  requestPath: "request_path",
  clientIp: "client_ip",
  userId: "user_id",
  createTime: "create_time",
};

// 筛选面板字段分组（x_log 可筛列，均为普通列）
const LOG_FIELD_GROUPS = [
  {
    label: "日志-基础信息",
    fields: [
      { label: "ID", value: "id" },
      { label: "级别", value: "level" },
      { label: "模块", value: "module" },
      { label: "记录器", value: "logger" },
      { label: "函数", value: "func" },
      { label: "行号", value: "line" },
      { label: "备注", value: "remark" },
    ],
  },
  {
    label: "日志-内容",
    fields: [
      { label: "日志内容", value: "message" },
      { label: "异常堆栈", value: "exc_info" },
    ],
  },
  {
    label: "日志-请求",
    fields: [
      { label: "请求方法", value: "request_method" },
      { label: "请求路径", value: "request_path" },
      { label: "请求ID", value: "request_id" },
      { label: "客户端IP", value: "client_ip" },
      { label: "用户ID", value: "user_id" },
    ],
  },
  {
    label: "日志-时间",
    fields: [
      { label: "创建时间", value: "create_time" },
      { label: "更新时间", value: "update_time" },
    ],
  },
];
// 级别声明为下拉多选（含选项的字段在筛选面板中为「包含任一」多选）
const LOG_FIELD_OPTIONS = { level: LEVEL_OPTIONS };

// 可选排序列（与后端排序白名单口径一致）
const SORT_FIELD_OPTIONS = [
  { value: "id", label: "ID" },
  { value: "level", label: "级别" },
  { value: "module", label: "模块" },
  { value: "logger", label: "记录器" },
  { value: "request_method", label: "请求方法" },
  { value: "request_path", label: "请求路径" },
  { value: "client_ip", label: "客户端IP" },
  { value: "user_id", label: "用户ID" },
  { value: "create_time", label: "创建时间" },
  { value: "update_time", label: "更新时间" },
];

// 列设置 / 排序规则本地缓存键
const COLUMN_SETTINGS_KEY = "logColumnSettingsV1";
const SORT_RULES_STORAGE_KEY = "logSortRulesV1";
const DEFAULT_SORT_RULES = [{ field: "create_time", direction: "desc" }];

// ==================== 工具函数 ====================
const deepClone = (value) => (value === undefined || value === null ? null : JSON.parse(JSON.stringify(value)));

const handleRequestError = (error, defaultMessage) => {
  if (error?.response?.data?.detail === "Method Not Allowed") {
    ElMessage.error("请求方法错误，请检查 API 接口配置");
  } else {
    ElMessage.error(error?.detail || error?.message || defaultMessage);
  }
};

// 级别对应的标签颜色
const levelTagType = (level) => {
  const types = {
    DEBUG: "info",
    INFO: "success",
    WARNING: "warning",
    ERROR: "danger",
    CRITICAL: "danger",
  };
  return types[level] || "info";
};

// 日志表存的是 naive UTC 时间，展示时补上时区标识后转本地时间
const formatTime = (value) => {
  if (!value) {
    return "-";
  }
  const text = String(value).replace(" ", "T").replace(/\.(\d{3})\d*/, ".$1");
  const hasZone = /[zZ]$|[+-]\d{2}:?\d{2}$/.test(text);
  const date = new Date(hasZone ? text : `${text}Z`);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }
  const pad = (num) => String(num).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
};

// ==================== 表格状态 ====================
const tableData = ref([]);
const loading = ref(false);
const currentPage = ref(DEFAULT_PAGE);
const pageSize = ref(DEFAULT_PAGE_SIZE);
const total = ref(0);
const selectedRows = ref([]);

// ==================== 查询条件 ====================
const keyword = ref("");
const isAdmin = ref(checkIsAdmin());

// ==================== 详情状态 ====================
const detailVisible = ref(false);
const currentRow = ref(null);

// ==================== 自定义显示列（字段设置） ====================
const columnSettingsVisible = ref(false);
// 用户保存的完整列配置（含隐藏列）
const savedColumnConfig = ref(null);

// 当前用户可见的列目录（非管理员不展示用户ID列）
const columnCatalog = computed(() =>
  LOG_COLUMN_CATALOG.filter((item) => !item.adminOnly || isAdmin.value),
);

const loadColumnConfig = () => {
  let saved = null;
  try {
    const raw = localStorage.getItem(COLUMN_SETTINGS_KEY);
    const parsed = raw ? JSON.parse(raw) : null;
    if (Array.isArray(parsed) && parsed.length) saved = parsed;
  } catch (e) {
    console.error("加载字段设置失败:", e);
  }
  savedColumnConfig.value = saved;
};

// 列目录 + 用户配置 → 完整列配置（含隐藏列，保持自定义顺序 / 宽度 / 固定）
const fullColumnConfig = computed(() => {
  const catalog = columnCatalog.value;
  const saved = savedColumnConfig.value;
  const byValue = new Map(catalog.map((item) => [item.value, item]));
  const list = [];
  if (saved) {
    saved.forEach((item) => {
      const base = byValue.get(item.value);
      if (!base) return;
      list.push({
        ...base,
        width: item.width ?? base.width,
        fixed: item.fixed ?? base.fixed,
        visible: item.visible !== false,
      });
    });
    // 列目录新增但历史配置缺失的列，追加到末尾并默认可见
    catalog.forEach((base) => {
      if (!list.some((item) => item.value === base.value)) list.push({ ...base, visible: true });
    });
  } else {
    catalog.forEach((base) => list.push({ ...base, visible: true }));
  }
  return list;
});

const columnConfig = computed(() => fullColumnConfig.value.filter((item) => item.visible));

const saveColumnSettings = () => {
  loadColumnConfig();
  ElMessage.success("字段设置已保存");
};

// 列头冻结 / 隐藏后整体落盘（与 ColumnSettings 同结构）
const persistFullColumnConfig = (list) => {
  const payload = list.map((item) => ({
    value: item.value,
    label: item.label,
    width: item.width,
    fixed: item.fixed,
    visible: item.visible,
  }));
  localStorage.setItem(COLUMN_SETTINGS_KEY, JSON.stringify(payload));
  loadColumnConfig();
};

// ==================== 列头菜单 ====================
const dbFieldOf = (colValue) => HEADER_DB_FIELD_MAP[colValue] || "";

const getSortDirection = (colValue) => {
  const dbField = dbFieldOf(colValue);
  if (!dbField) return "";
  const rule = sortRules.value.find((r) => r.field === dbField);
  return rule ? rule.direction : "";
};

// 该列在筛选面板中已有的筛选条件（同一字段只取第一条）
const getFieldCondition = (colValue) => {
  const dbField = dbFieldOf(colValue);
  if (!dbField) return null;
  for (const group of filterGroups.value) {
    const cond = (group.conditions || []).find((item) => item.field === dbField);
    if (cond) return cond;
  }
  return null;
};

// 该列是否存在生效的筛选条件（「为空 / 不为空」无需值，其余必须有值才算生效）
const hasFieldFilter = (colValue) => {
  const cond = getFieldCondition(colValue);
  if (!cond) return false;
  if (["is_null", "is_not_null"].includes(cond.operator)) return true;
  const value = cond.value;
  if (Array.isArray(value)) return value.length > 0;
  return String(value ?? "").trim() !== "";
};

const headerMenuVisible = reactive({});
const filterOperator = ref("eq");
const filterValue = ref("");
const isNoValueOperator = computed(() => ["is_null", "is_not_null"].includes(filterOperator.value));

// 列头图标状态：无 / 升序 / 降序 / 筛选 / 筛选+升序 / 筛选+降序
const headerStateMap = computed(() => {
  const map = {};
  columnConfig.value.forEach((col) => {
    const direction = getSortDirection(col.value);
    const filtered = hasFieldFilter(col.value);
    if (direction && filtered) map[col.value] = `filter-${direction}`;
    else if (filtered) map[col.value] = "filter";
    else map[col.value] = direction;
  });
  return map;
});

const onHeaderMenuTrigger = (colValue) => {
  Object.keys(headerMenuVisible).forEach((key) => {
    if (key !== colValue) headerMenuVisible[key] = false;
  });
  const cond = getFieldCondition(colValue);
  filterOperator.value = cond?.operator || "eq";
  filterValue.value =
    cond && !["is_null", "is_not_null"].includes(cond.operator) && !Array.isArray(cond.value)
      ? String(cond.value ?? "")
      : "";
};

const closeHeaderMenu = (colValue) => {
  headerMenuVisible[colValue] = false;
};

const isFrozen = (colValue) =>
  Boolean(fullColumnConfig.value.find((item) => item.value === colValue)?.fixed);

const onHeaderSort = (colValue, direction) => {
  const dbField = dbFieldOf(colValue);
  if (!dbField) return;
  // 再次点击已选中的排序方向 → 取消该列排序
  const isSame = getSortDirection(colValue) === direction;
  saveSortRules(isSame ? [] : [{ field: dbField, direction }]);
  closeHeaderMenu(colValue);
};

const onHeaderFreeze = (colValue) => {
  const fixed = fullColumnConfig.value.find((item) => item.value === colValue)?.fixed ? "" : "left";
  persistFullColumnConfig(
    fullColumnConfig.value.map((item) => (item.value === colValue ? { ...item, fixed } : item)),
  );
  ElMessage.success(fixed ? "已冻结该列" : "已取消冻结");
  closeHeaderMenu(colValue);
};

const onHeaderHide = (colValue) => {
  // 保留该列配置并标记为不可见，保证字段设置弹窗仍可重新开启该列
  persistFullColumnConfig(
    fullColumnConfig.value.map((item) =>
      item.value === colValue ? { ...item, visible: false } : item,
    ),
  );
  ElMessage.success("已隐藏该列");
  closeHeaderMenu(colValue);
};

// 列头菜单：应用筛选（与筛选面板同步，同字段覆盖）
const onHeaderFilter = (colValue) => {
  const dbField = dbFieldOf(colValue);
  if (!dbField) return;
  const operator = filterOperator.value;
  const noValue = isNoValueOperator.value;
  const raw = String(filterValue.value ?? "").trim();
  if (!noValue && !raw && !hasFieldFilter(colValue)) {
    ElMessage.warning("请输入筛选值");
    return;
  }
  const groups = deepClone(filterGroups.value) || [];
  if (!groups.length) groups.push({ groupLogic: "and", conditionLogic: "and", conditions: [] });
  if (!Array.isArray(groups[0].conditions)) groups[0].conditions = [];
  const conditions = groups[0].conditions;
  const index = conditions.findIndex((cond) => cond.field === dbField);
  const isEmpty = !noValue && !raw;
  if (isEmpty) {
    if (index > -1) conditions.splice(index, 1);
  } else if (index > -1) {
    conditions[index] = { field: dbField, operator, value: noValue ? null : raw };
  } else {
    conditions.push({ field: dbField, operator, value: noValue ? null : raw });
  }
  filterGroups.value = groups;
  currentPresetId.value = null;
  currentPage.value = DEFAULT_PAGE;
  fetchData();
  closeHeaderMenu(colValue);
};

// 长文本列使用悬浮提示
const useTooltip = (value) => ["message", "module", "logger", "requestPath"].includes(value);

// ==================== 排序规则 ====================
const sortRules = ref([...DEFAULT_SORT_RULES]);
const showSortDialog = ref(false);
const sortBadgeCount = computed(() => sortRules.value.length);

const openSortSettings = () => {
  showSortDialog.value = true;
};

// 去除弹窗内部生成的规则 id，仅保留 field / direction
const normalizeSortRules = (rules) =>
  (Array.isArray(rules) ? rules : [])
    .filter((rule) => rule && rule.field)
    .map((rule) => ({ field: rule.field, direction: rule.direction === "desc" ? "desc" : "asc" }));

const saveSortRules = (rules) => {
  sortRules.value = normalizeSortRules(rules);
  localStorage.setItem(SORT_RULES_STORAGE_KEY, JSON.stringify(sortRules.value));
  // 排序变更后回到第 1 页重新拉取，避免停留在越界页码
  currentPage.value = DEFAULT_PAGE;
  fetchData();
};

// 从本地缓存还原排序规则（仅接受与可选排序列匹配的字段，避免脏数据下发后端）
const restoreSortRules = () => {
  const saved = localStorage.getItem(SORT_RULES_STORAGE_KEY);
  if (!saved) return;
  let parsed;
  try {
    parsed = JSON.parse(saved);
  } catch (error) {
    return;
  }
  if (!Array.isArray(parsed)) return;
  const allowed = new Set(SORT_FIELD_OPTIONS.map((item) => item.value));
  sortRules.value = normalizeSortRules(parsed).filter((rule) => allowed.has(rule.field));
};

// ==================== 筛选面板 ====================
const showAdvancedSearch = ref(false);
const filterGroups = ref([{ groupLogic: "and", conditionLogic: "and", conditions: [] }]);
const groupsLogic = ref("and");
// 已保存的筛选条件（下拉选中即套用，仅本人可见）
const filterPresets = ref([]);
const currentPresetId = ref(null);

const filterBadgeCount = computed(() =>
  filterGroups.value.reduce((sum, g) => sum + g.conditions.length, 0),
);

const presetNames = computed(() => filterPresets.value.map((preset) => preset.name));
const currentPresetName = computed(
  () => filterPresets.value.find((preset) => preset.id === currentPresetId.value)?.name || "",
);

// 未选字段 / 未填值的条件不下发，避免空值绑定到整型列导致查询报错
const isCompleteCond = (cond) => {
  if (!cond.field) return false;
  if (cond.operator === "is_null" || cond.operator === "is_not_null") return true;
  if (Array.isArray(cond.value)) return cond.value.length > 0;
  return cond.value !== "" && cond.value !== null && cond.value !== undefined;
};

const buildQueryFilter = () =>
  filterGroups.value.map((group) => ({
    ...group,
    conditions: group.conditions.filter(isCompleteCond),
  }));

const applyFilter = () => {
  currentPage.value = DEFAULT_PAGE;
  fetchData();
};

const resetFilter = () => {
  filterGroups.value = [{ groupLogic: "and", conditionLogic: "and", conditions: [] }];
  groupsLogic.value = "and";
  keyword.value = "";
  currentPresetId.value = null;
  currentPage.value = DEFAULT_PAGE;
  fetchData();
};

// ==================== 保存的筛选条件（按用户隔离） ====================
const loadFilterPresets = async () => {
  try {
    const res = await request.post(FILTER_PRESET_API.list, { page: "log" });
    filterPresets.value = res.code === 200 ? (res.data?.items || []) : [];
  } catch (error) {
    filterPresets.value = [];
  }
};

// 套用已保存方案：覆盖条件构造器内容、展开面板并立即查询
const applyFilterPreset = (preset) => {
  const groups = Array.isArray(preset.filterGroups) ? deepClone(preset.filterGroups) : [];
  filterGroups.value = groups.length
    ? groups
    : [{ groupLogic: "and", conditionLogic: "and", conditions: [] }];
  groupsLogic.value = preset.groupsLogic || "and";
  currentPresetId.value = preset.id;
  showAdvancedSearch.value = true;
  currentPage.value = DEFAULT_PAGE;
  fetchData();
};

const handleFilterPresetCommand = (presetId) => {
  const preset = filterPresets.value.find((item) => item.id === presetId);
  if (preset) applyFilterPreset(preset);
};

// 以当前条件新建方案（保存条件 / 另存为共用）
const createFilterPreset = async (name) => {
  try {
    const res = await request.post(FILTER_PRESET_API.save, {
      page: "log",
      name,
      groupsLogic: groupsLogic.value,
      filterGroups: buildQueryFilter(),
    });
    if (res.code === 200) {
      ElMessage.success("保存成功");
      const savedId = res.data?.id ?? null;
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
      page: "log",
      name,
      groupsLogic: groupsLogic.value,
      filterGroups: buildQueryFilter(),
    });
    if (res.code === 200) {
      ElMessage.success("更新成功");
      await loadFilterPresets();
    } else {
      ElMessage.error(res.message || "更新失败");
    }
  } catch (error) {
    ElMessage.error(error.message || "更新失败");
  }
};

const handleFilterPresetSave = async (name) => {
  if (!name) return;
  if (currentPresetId.value === null) {
    await createFilterPreset(name);
    return;
  }
  await updateFilterPreset(name);
};

const handleFilterPresetSaveAs = async (name) => {
  if (name) await createFilterPreset(name);
};

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
      if (preset.id === currentPresetId.value) {
        currentPresetId.value = null;
      }
      await loadFilterPresets();
    } else {
      ElMessage.error(res.message || "删除失败");
    }
  } catch (error) {
    ElMessage.error(error.message || "删除失败");
  }
};

// ==================== 数据获取 ====================
const fetchData = async () => {
  loading.value = true;
  try {
    const res = await request.post(API_ENDPOINTS.LIST, {
      page: currentPage.value,
      limit: pageSize.value,
      keyword: keyword.value,
      filter: buildQueryFilter(),
      sort: sortRules.value,
    });

    if (res.code === 200) {
      tableData.value = res.data?.items || [];
      total.value = res.data?.total || 0;
    } else {
      ElMessage.error(res.message || "获取日志列表失败");
    }
  } catch (error) {
    handleRequestError(error, "获取日志列表失败");
  } finally {
    loading.value = false;
  }
};

const handleSearch = () => {
  currentPage.value = DEFAULT_PAGE;
  fetchData();
};

const handleSelectionChange = (rows) => {
  selectedRows.value = rows;
};

const handleSizeChange = (val) => {
  pageSize.value = val;
  fetchData();
};

const handleCurrentChange = (val) => {
  currentPage.value = val;
  fetchData();
};

// ==================== 详情/删除/清理 ====================
const handleView = (row) => {
  currentRow.value = row;
  detailVisible.value = true;
};

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm("确定要删除该条日志吗？", "提示", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    });
    const res = await request.post(API_ENDPOINTS.DELETE, { data: { id: row.id } });
    if (res.code === 200) {
      ElMessage.success("删除成功");
      fetchData();
    } else {
      ElMessage.error(res.message || "删除失败");
    }
  } catch (error) {
    if (error !== "cancel") {
      handleRequestError(error, "删除失败");
    }
  }
};

const handleDeleteSelected = async () => {
  const ids = selectedRows.value.map((row) => row.id);
  if (ids.length === 0) {
    return;
  }
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${ids.length} 条日志吗？`, "提示", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    });
    const res = await request.post(API_ENDPOINTS.BATCH_DELETE, { ids });
    if (res.code === 200) {
      ElMessage.success(`已删除 ${res.data?.deleted ?? 0} 条日志`);
      selectedRows.value = [];
      fetchData();
    } else {
      ElMessage.error(res.message || "删除失败");
    }
  } catch (error) {
    if (error !== "cancel") {
      handleRequestError(error, "删除失败");
    }
  }
};

const handleClean = async () => {
  try {
    const { value } = await ElMessageBox.prompt(
      `清理多少天前的日志？（最少 ${MIN_CLEAN_DAYS} 天，清理后不可恢复）`,
      "清理历史日志",
      {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        inputValue: "30",
        inputPattern: /^\d+$/,
        inputErrorMessage: "请输入正整数天数",
        type: "warning",
      },
    );
    const days = Number(value);
    if (days < MIN_CLEAN_DAYS) {
      ElMessage.warning(`最少需要保留 ${MIN_CLEAN_DAYS} 天`);
      return;
    }
    const res = await request.post(API_ENDPOINTS.CLEAN, { beforeDays: days });
    if (res.code === 200) {
      ElMessage.success(`已清理 ${res.data?.deleted ?? 0} 条日志`);
      fetchData();
    } else {
      ElMessage.error(res.message || "清理失败");
    }
  } catch (error) {
    if (error !== "cancel") {
      handleRequestError(error, "清理失败");
    }
  }
};

onMounted(() => {
  loadColumnConfig();
  restoreSortRules();
  fetchData();
  loadFilterPresets();
});
</script>

<style scoped>
/* ==================== 列头菜单 ==================== */
.col-header {
  display: flex;
  align-items: center;
  width: 100%;
}

.col-header-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 列操作触发区：固定占位尺寸，避免悬停时图标出现引起列头抖动 */
.col-header-menu-trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: none;
  width: 16px;
  height: 16px;
  margin-left: 4px;
  margin-right: -8px;
  cursor: pointer;
}

.col-header-menu-sort {
  display: none;
  align-items: center;
  justify-content: center;
  color: var(--td-text-color-primary, #303133);
}

.col-header-menu-trigger.has-state .col-header-menu-sort {
  display: inline-flex;
}

.col-header-menu-sort--combo {
  align-items: center;
  gap: 1px;
}

.col-header-menu-trigger:has(.col-header-menu-sort--combo) {
  width: 22px;
}

.col-header-menu-sort--combo > .el-icon:first-child {
  font-size: 12px;
}

.col-header-menu-sort-arrow {
  font-size: 9px;
  transform: scaleY(1.6);
}

.col-header-menu-btn {
  display: none;
  cursor: pointer;
  color: var(--td-text-color-placeholder, #909399);
  transform: rotate(90deg);
}

.col-header:hover .col-header-menu-btn {
  display: inline-flex;
  color: var(--td-text-color-brand, #409eff);
}

.col-header:hover .col-header-menu-trigger.has-state .col-header-menu-btn {
  display: none;
}

/* ==================== 单元格 / 详情内容 ==================== */
.cell-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.detail-message {
  white-space: pre-wrap;
  word-break: break-all;
}

.exc-info {
  margin-top: 16px;
}

.exc-title {
  margin-bottom: 8px;
  font-weight: 600;
}

.exc-content {
  max-height: 320px;
  overflow: auto;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>

<style>
/* 列头菜单为 teleport 到 body 的 popper，样式需为全局（限定 popper-class 避免污染） */
.col-header-menu-popper .col-header-menu {
  display: flex;
  flex-direction: column;
}

.col-header-menu-popper .col-header-menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 32px;
  padding: 0 6px;
  border-radius: 4px;
  cursor: pointer;
  color: var(--td-text-color-primary, #303133);
  transition: background-color 0.15s;
}

.col-header-menu-popper .col-header-menu-item:hover {
  background-color: var(--td-bg-color-container-hover, #f5f7fa);
}

.col-header-menu-popper .col-header-menu-item.is-checked {
  color: var(--td-text-color-brand, #409eff);
}

.col-header-menu-popper .col-header-menu-check {
  margin-left: auto;
}

.col-header-menu-popper .col-header-menu-divider {
  height: 1px;
  margin: 4px 0;
  background-color: var(--td-component-stroke, #ebeef5);
}

.col-header-menu-popper .col-header-menu-filter {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 2px 6px 6px;
}

.col-header-menu-popper .col-header-menu-filter-head {
  display: flex;
  align-items: center;
  gap: 4px;
}

.col-header-menu-popper .col-header-menu-filter-icon {
  font-size: 14px;
  color: var(--td-text-color-secondary, #909399);
}

.col-header-menu-popper .col-header-menu-filter-title {
  color: var(--td-text-color-secondary, #909399);
  white-space: nowrap;
}

.col-header-menu-popper .col-header-menu-filter-operator {
  width: 120px;
  margin-left: 4px;
}

.col-header-menu-popper .col-header-menu-filter-operator .el-select__wrapper {
  padding: 0;
  min-height: 32px;
  background-color: transparent !important;
  box-shadow: none !important;
}

.col-header-menu-popper .col-header-menu-filter-operator .el-select__selected-item,
.col-header-menu-popper .col-header-menu-filter-operator .el-select__placeholder {
  font-weight: 500;
  color: var(--td-text-color-brand, #409eff);
}

.col-header-menu-popper .col-header-menu-filter-value {
  width: 100%;
}

.col-header-menu-popper .col-header-menu-filter-btn {
  width: 100%;
}
</style>
