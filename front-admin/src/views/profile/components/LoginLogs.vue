<template>
  <!-- 登录记录：主卡片 + 右侧筛选面板（展开时与卡片拼合） -->
  <div class="login-logs-layout">
    <el-card shadow="hover" class="login-logs-card" :class="{ 'is-filter-open': showAdvancedSearch }">
      <template #header>
        <div class="card-header">
          <span>登录记录</span>
          <div class="header-actions">
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
            <el-tooltip content="字段设置" placement="top">
              <el-button class="action-btn" @click="columnSettingsVisible = true">
                <el-icon>
                  <Setting />
                </el-icon>
              </el-button>
            </el-tooltip>
          </div>
        </div>
      </template>

      <div class="main-content">
        <div class="table-area">
          <el-table v-loading="loading" :data="tableData" border stripe class="login-logs-table" height="100%">
            <!-- 数据列：按列目录动态渲染（顺序 / 宽度 / 固定 / 显隐） -->
            <template v-for="col in columnConfig" :key="col.value">
              <el-table-column :label="col.label" :width="col.flexible ? undefined : col.width"
                :min-width="col.flexible ? col.width : undefined" :fixed="col.fixed || false"
                :align="col.align || 'left'" :show-overflow-tooltip="true">
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
                        <!-- 排序 / 筛选仅对有 DB 列的列开放 -->
                        <template v-if="dbFieldOf(col.value)">
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
                        </template>
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
                        <template v-if="dbFieldOf(col.value)">
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
                        </template>
                      </div>
                    </el-popover>
                  </div>
                </template>
                <template #default="{ row }">
                  <el-tag v-if="col.value === 'status'" :type="row.status === 1 ? 'success' : 'danger'">
                    {{ row.status === 1 ? "成功" : "失败" }}
                  </el-tag>
                  <span v-else>{{ row[col.value] ?? '-' }}</span>
                </template>
              </el-table-column>
            </template>
          </el-table>

          <div class="pagination-wrapper">
            <el-pagination :current-page="currentPage" :page-size="pageSize" :page-sizes="PAGE_SIZES"
              layout="total, sizes, prev, pager, next, jumper" :total="total" @size-change="handleSizeChange"
              @current-change="handleCurrentChange" />
          </div>
        </div>
      </div>
    </el-card>

    <!-- 筛选面板：条件构造器（组 / 条件 + 字段 + 操作符 + 值） -->
    <el-aside width="320px" class="advanced-search-aside" v-if="showAdvancedSearch">
      <FilterPanel v-model:filterGroups="filterGroups" v-model:groupsLogic="groupsLogic"
        :field-groups="LOGIN_LOG_FIELD_GROUPS" :current-preset-name="currentPresetName" :preset-names="presetNames"
        @apply="applyFilter" @reset="resetFilter" @save="handleFilterPresetSave" @save-as="handleFilterPresetSaveAs" />
    </el-aside>
  </div>

  <!-- 列表排序设置对话框（排序规则持久化到 localStorage） -->
  <SortSettings v-model:visible="showSortDialog" :sort-rules="sortRules" :field-options="SORT_FIELD_OPTIONS"
    @save="saveSortRules" />

  <!-- 列表字段设置（隐藏列的恢复入口，与日志 / 商品页一致） -->
  <ColumnSettings v-model:visible="columnSettingsVisible" :fields="columnConfig.map((item) => item.value)"
    :field-config="columnConfig" :catalog="LOGIN_LOG_COLUMN_CATALOG" :storage-key="COLUMN_SETTINGS_KEY"
    @save="saveColumnSettings" />
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  Sort, Filter, ArrowDown, Setting, Delete,
  SortUp, SortDown, MoreFilled, Lock, Hide, Check, CaretTop, CaretBottom,
} from "@element-plus/icons-vue";
import request from "@/utils/request";
import FilterPanel from "@/components/table/FilterPanel.vue";
import SortSettings from "@/components/table/SortSettings.vue";
import ColumnSettings from "@/components/table/ColumnSettings.vue";

// ==================== 常量定义 ====================
const PAGE_SIZES = [10, 20, 50];
const DEFAULT_PAGE_SIZE = 10;
const DEFAULT_PAGE = 1;

const API_ENDPOINTS = { LIST: "/admin/profile/get-login-logs" };

// 保存的筛选条件：后台各列表页共用接口（admin/filter_preset），page 传 "login_log"
const FILTER_PRESET_API = {
  list: "/admin/filter-preset/list",
  save: "/admin/filter-preset/save",
  update: "/admin/filter-preset/update",
  delete: "/admin/filter-preset/delete",
};
const PRESET_PAGE = "login_log";

// 列目录（value 与表格单元格渲染 key 对应；flexible 列用 min-width）
const LOGIN_LOG_COLUMN_CATALOG = [
  { value: "loginTime", label: "登录时间", width: 200 },
  { value: "ip", label: "登录IP", width: 150 },
  { value: "device", label: "登录设备", width: 180 },
  { value: "browser", label: "浏览器", width: 200 },
  { value: "os", label: "操作系统", width: 150 },
  { value: "status", label: "登录状态", width: 100 },
  { value: "errorMessage", label: "错误信息", width: 200, flexible: true },
];

// 列头可排序 / 可筛选的「列 key → 数据库列」映射（x_user_login 真实列）
// 登录设备 / 浏览器 / 操作系统 / 错误信息 后端无对应列，不参与排序与筛选
const HEADER_DB_FIELD_MAP = {
  loginTime: "login_time",
  ip: "ip",
  status: "status",
};

// 筛选面板字段分组（x_user_login 可筛列）
const LOGIN_LOG_FIELD_GROUPS = [
  {
    label: "登录记录",
    fields: [
      { label: "登录时间", value: "login_time" },
      { label: "登录IP", value: "ip" },
      { label: "User-Agent", value: "user_agent" },
      { label: "登录状态", value: "status" },
    ],
  },
];

// 可选排序列（与后端排序白名单口径一致）
const SORT_FIELD_OPTIONS = [
  { value: "login_time", label: "登录时间" },
  { value: "ip", label: "登录IP" },
  { value: "user_agent", label: "User-Agent" },
  { value: "status", label: "登录状态" },
];

// 列设置 / 排序规则本地缓存键
const COLUMN_SETTINGS_KEY = "loginLogColumnSettingsV1";
const SORT_RULES_STORAGE_KEY = "loginLogSortRulesV1";
const DEFAULT_SORT_RULES = [{ field: "login_time", direction: "desc" }];

// ==================== 工具函数 ====================
const deepClone = (value) =>
  value === undefined || value === null ? null : JSON.parse(JSON.stringify(value));

const handleRequestError = (error, defaultMessage) => {
  ElMessage.error(error?.detail || error?.message || defaultMessage);
};

// ==================== 表格状态 ====================
const tableData = ref([]);
const loading = ref(false);
const currentPage = ref(DEFAULT_PAGE);
const pageSize = ref(DEFAULT_PAGE_SIZE);
const total = ref(0);

// ==================== 自定义显示列 ====================
const columnSettingsVisible = ref(false);
// 用户保存的完整列配置（含隐藏列）
const savedColumnConfig = ref(null);

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
  const catalog = LOGIN_LOG_COLUMN_CATALOG;
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
  currentPresetId.value = null;
  currentPage.value = DEFAULT_PAGE;
  fetchData();
};

// ==================== 保存的筛选条件（按用户隔离） ====================
const loadFilterPresets = async () => {
  try {
    const res = await request.post(FILTER_PRESET_API.list, { page: PRESET_PAGE });
    filterPresets.value = res.code === 200 ? res.data?.items || [] : [];
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
      page: PRESET_PAGE,
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
      page: PRESET_PAGE,
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
      filter: buildQueryFilter(),
      sort: sortRules.value,
    });
    if (res.code === 200) {
      tableData.value = res.data?.items || [];
      total.value = res.data?.total || 0;
    } else {
      ElMessage.error(res.message || "获取登录记录失败");
    }
  } catch (error) {
    handleRequestError(error, "获取登录记录失败");
  } finally {
    loading.value = false;
  }
};

const handleSizeChange = (val) => {
  pageSize.value = val;
  currentPage.value = DEFAULT_PAGE;
  fetchData();
};

const handleCurrentChange = (val) => {
  currentPage.value = val;
  fetchData();
};

onMounted(() => {
  loadColumnConfig();
  restoreSortRules();
  fetchData();
  loadFilterPresets();
});
</script>

<style scoped>
/* 根容器：主卡片 + 筛选面板横向并排，铺满页签内容区 */
.login-logs-layout {
  flex: 1 1 auto;
  min-width: 0;
  min-height: 0;
  display: flex;
}

/* 主卡片：纵向铺满，头部固定、表格区域滚动、分页固定在底部 */
.login-logs-card {
  flex: 1 1 auto;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  margin-bottom: 0;
}

.login-logs-card :deep(.el-card__body) {
  flex: 1;
  min-height: 0;
  padding: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 表格 + 侧栏容器由全局 .main-content 承担 flex:1 / min-height:0，这里补齐横向排布 */
.main-content {
  flex: 1;
  min-height: 0;
  display: flex;
  gap: 8px;
  width: 100%;
}

/* 筛选面板：右侧固定宽度，与主卡片拼合（外框样式由全局 .advanced-search-aside 承担） */
.advanced-search-aside {
  width: 320px;
  height: 100%;
  flex: none;
}

/* 分页栏左右留白与表格对齐 */
.pagination-wrapper {
  padding: 0 24px;
}

/* 工具栏按钮间距 */
.action-btn {
  margin-left: 8px;
}

/* 筛选 + 已保存条件下拉：并排拼接为一个整体按钮组 */
.filter-split {
  display: inline-flex;
}

.filter-split .filter-split-more {
  margin-left: 0;
}

.filter-split-more {
  padding-left: 6px;
  padding-right: 6px;
  border-top-left-radius: 0;
  border-bottom-left-radius: 0;
}

.filter-split > .el-button:first-child {
  border-top-right-radius: 0;
  border-bottom-right-radius: 0;
}

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

/* 已保存筛选条件下拉项（teleport 到 body，需全局）：悬停时右侧显示删除图标 */
.filter-preset-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-width: 160px;
  padding-right: 8px;
}

.filter-preset-item-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 当前生效的方案：整行背景色区分，名称同步高亮 */
.filter-preset-item.is-active {
  background-color: var(--el-color-primary-light-9);
}

.filter-preset-item.is-active .filter-preset-item-name {
  color: var(--el-color-primary);
  font-weight: 600;
}

.filter-preset-item-delete {
  color: var(--el-color-danger);
}

.filter-preset-item-action {
  margin-left: 8px;
  opacity: 0;
  flex-shrink: 0;
}

.filter-preset-item:hover .filter-preset-item-action {
  opacity: 1;
}
</style>
