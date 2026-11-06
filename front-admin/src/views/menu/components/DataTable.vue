<template>
  <div class="admin-user-table">
    <el-table
      :data="tableData"
      class="admin-table"
      v-loading="loading"
      ref="tableRef"
      row-key="id"
      width="100%"
      height="100%"
      @selection-change="handleSelectionChange"
      @row-dblclick="handleRowDblclick"
      border
    >
      <el-table-column type="selection" width="40" resizable />
      <template v-for="field in fieldConfig">
        <el-table-column
          v-if="visibleFields.includes(field.value)"
          :prop="field.value"
          :label="field.label"
          resizable
          :min-width="field.width"
          :fixed="field.fixed || false"
        >
          <template #header>
            <div class="col-header">
              <span class="col-header-label">{{ field.label }}</span>
              <el-popover
                v-model:visible="headerMenuVisible[field.value]"
                trigger="click"
                placement="bottom-start"
                :width="220"
                popper-class="col-header-menu-popper"
              >
                <template #reference>
                  <span
                    class="col-header-menu-trigger"
                    :class="{ 'has-state': !!headerStateMap[field.value] }"
                    title="列操作"
                    @click.stop="onHeaderMenuTrigger(field.value)"
                  >
                    <el-icon
                      v-if="headerStateMap[field.value] === 'asc'"
                      class="col-header-menu-sort"
                    >
                      <SortUp />
                    </el-icon>
                    <el-icon
                      v-else-if="headerStateMap[field.value] === 'desc'"
                      class="col-header-menu-sort"
                    >
                      <SortDown />
                    </el-icon>
                    <el-icon
                      v-else-if="headerStateMap[field.value] === 'filter'"
                      class="col-header-menu-sort"
                    >
                      <Filter />
                    </el-icon>
                    <span
                      v-else-if="headerStateMap[field.value] === 'filter-asc'"
                      class="col-header-menu-sort col-header-menu-sort--combo"
                    >
                      <el-icon>
                        <Filter />
                      </el-icon>
                      <el-icon class="col-header-menu-sort-arrow">
                        <CaretTop />
                      </el-icon>
                    </span>
                    <span
                      v-else-if="headerStateMap[field.value] === 'filter-desc'"
                      class="col-header-menu-sort col-header-menu-sort--combo"
                    >
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
                  <div
                    class="col-header-menu-item"
                    :class="{ 'is-checked': getSortDirection(field.value) === 'asc' }"
                    @click="onHeaderSort(field.value, 'asc')"
                  >
                    <el-icon>
                      <SortUp />
                    </el-icon>
                    <span>升序</span>
                    <el-icon
                      v-if="getSortDirection(field.value) === 'asc'"
                      class="col-header-menu-check"
                    >
                      <Check />
                    </el-icon>
                  </div>
                  <div
                    class="col-header-menu-item"
                    :class="{ 'is-checked': getSortDirection(field.value) === 'desc' }"
                    @click="onHeaderSort(field.value, 'desc')"
                  >
                    <el-icon>
                      <SortDown />
                    </el-icon>
                    <span>降序</span>
                    <el-icon
                      v-if="getSortDirection(field.value) === 'desc'"
                      class="col-header-menu-check"
                    >
                      <Check />
                    </el-icon>
                  </div>
                  <div class="col-header-menu-divider"></div>
                  <div
                    class="col-header-menu-item"
                    :class="{ 'is-checked': isFrozen(field.value) }"
                    @click="onHeaderFreeze(field.value)"
                  >
                    <el-icon>
                      <Lock />
                    </el-icon>
                    <span>冻结列</span>
                    <el-icon
                      v-if="isFrozen(field.value)"
                      class="col-header-menu-check"
                    >
                      <Check />
                    </el-icon>
                  </div>
                  <div
                    class="col-header-menu-item"
                    @click="onHeaderHide(field.value)"
                  >
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
                      <el-select
                        v-model="filterOperator"
                        class="col-header-menu-filter-operator"
                        :teleported="false"
                      >
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
                    <el-input
                      v-if="!isNoValueOperator"
                      v-model="filterValue"
                      clearable
                      class="col-header-menu-filter-value"
                      placeholder="请输入筛选值"
                    />
                    <el-button
                      type="primary"
                      class="col-header-menu-filter-btn"
                      @click="onHeaderFilter(field.value)"
                    >
                      筛选
                    </el-button>
                  </div>
                </div>
              </el-popover>
            </div>
          </template>
          <template #default="{ row }">
            <template v-if="field.value === 'type'">
              <el-tag :type="getTypeTagType(row.type)">
                {{ getTypeLabel(row.type) }}
              </el-tag>
            </template>
            <template v-else-if="field.value === 'status'">
              <el-switch
                v-model="row.status"
                :active-value="1"
                :inactive-value="0"
                @change="handleStatusChange(row)"
              />
            </template>
            <template v-else-if="field.value === 'createTime'">
              <span :title="formatDate(row.createTime)">{{
                formatRelativeTime(row.createTime)
              }}</span>
            </template>
            <template v-else-if="field.value === 'updateTime'">
              <span :title="formatDate(row.updateTime)">{{
                formatRelativeTime(row.updateTime)
              }}</span>
            </template>
            <template v-else>
              <span>{{ row[field.value] ?? "-" }}</span>
            </template>
          </template>
        </el-table-column>
      </template>
      <el-table-column label="操作" width="120" fixed="right">
        <template #header>
          <span>操作&nbsp;</span>
          <el-link
            @click="handleFieldSettings"
            underline="never"
            title="字段设置"
          >
            <el-icon>
              <Setting />
            </el-icon>
          </el-link>
        </template>
        <template #default="{ row }">
          <div class="cell-actions">
            <el-link
              type="primary"
              @click="handleEdit(row)"
              title="编辑"
              underline="never"
            >
              <el-icon>
                <Edit />
              </el-icon>
            </el-link>
            <el-link
              type="danger"
              @click="handleDelete(row)"
              title="删除"
              class="action-btn-small"
              underline="never"
            >
              <el-icon>
                <Delete />
              </el-icon>
            </el-link>
          </div>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination
      :current-page="currentPage"
      :page-size="pageSize"
      :total="total"
      :page-sizes="pageSizes"
      layout="total, sizes, prev, pager, next, jumper"
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
      class="pagination-wrapper"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, nextTick } from "vue";
import {
  Edit,
  Delete,
  Setting,
  SortUp,
  SortDown,
  MoreFilled,
  Lock,
  Hide,
  Check,
  Filter,
  CaretTop,
  CaretBottom,
} from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import request, { camelToSnake } from "@/utils/request";

const props = defineProps({
  tableData: { type: Array, required: true, default: () => [] },
  visibleFields: { type: Array, required: true, default: () => [] },
  fieldConfig: { type: Array, required: true, default: () => [] },
  loading: { type: Boolean, default: false },
  currentPage: { type: Number, default: 1 },
  pageSize: { type: Number, default: 20 },
  total: { type: Number, default: 0 },
  pageSizes: { type: Array, default: () => [20, 50, 100] },
  sortRules: { type: Array, required: true, default: () => [] },
  // 筛选面板的筛选条件：用于列头菜单回显与列头状态图标
  filterGroups: { type: Array, default: () => [] },
});

const emit = defineEmits([
  "selectionChange",
  "rowDblclick",
  "edit",
  "delete",
  "fieldSettings",
  "sizeChange",
  "currentChange",
  "headerSort",
  "headerFreeze",
  "headerHide",
  "headerFilter",
]);

const tableRef = ref(null);

const getTypeLabel = (type) => {
  const typeMap = { 1: "目录", 2: "菜单" };
  return typeMap[type] || type;
};

const getTypeTagType = (type) => {
  const typeMap = { 1: "info", 2: "success" };
  return typeMap[type] || "default";
};

const getSortDirection = (field) => {
  // 列字段为响应体的 camelCase（createTime），排序规则存的是数据库列名（create_time）
  const dbField = camelToSnake(field);
  const rule = props.sortRules.find(
    (r) => r.field === dbField || r.field === field,
  );
  if (!rule) return "";
  return rule.direction;
};

// ==================== 列头菜单 ====================
// 该列在筛选面板中已有的筛选条件（同一字段只取第一条）
const getFieldCondition = (field) => {
  const snakeField = camelToSnake(field);
  for (const group of props.filterGroups || []) {
    const cond = (group.conditions || []).find((item) => item.field === snakeField);
    if (cond) return cond;
  }
  return null;
};

// 该列是否存在生效的筛选条件（「为空 / 不为空」无需值，其余必须有值才算生效）
const hasFieldFilter = (field) => {
  const cond = getFieldCondition(field);
  if (!cond) return false;
  if (["is_null", "is_not_null"].includes(cond.operator)) return true;
  return String(cond.value ?? "").trim() !== "";
};

// 各列菜单展开状态（按字段名索引）
const headerMenuVisible = reactive({});
// 列头快捷筛选的草稿：同一时刻只有一个列菜单展开，字段间共用
const filterOperator = ref("eq");
const filterValue = ref("");
// 「为空 / 不为空」无需填写筛选值，与筛选弹窗保持一致
const isNoValueOperator = computed(() =>
  ["is_null", "is_not_null"].includes(filterOperator.value),
);

// 列头图标状态：无 / 升序 / 降序 / 筛选 / 筛选+升序 / 筛选+降序
const headerStateMap = computed(() => {
  const map = {};
  (props.fieldConfig || []).forEach((field) => {
    const direction = getSortDirection(field.value);
    const filtered = hasFieldFilter(field.value);
    if (direction && filtered) map[field.value] = `filter-${direction}`;
    else if (filtered) map[field.value] = "filter";
    else map[field.value] = direction;
  });
  return map;
});

// 打开列菜单：回显该列在筛选面板中已有的条件（无则重置为默认草稿）
const onHeaderMenuTrigger = (fieldValue) => {
  Object.keys(headerMenuVisible).forEach((key) => {
    if (key !== fieldValue) headerMenuVisible[key] = false;
  });
  const cond = getFieldCondition(fieldValue);
  filterOperator.value = cond?.operator || "eq";
  filterValue.value =
    cond && !["is_null", "is_not_null"].includes(cond.operator)
      ? String(cond.value ?? "")
      : "";
};

const closeHeaderMenu = (fieldValue) => {
  headerMenuVisible[fieldValue] = false;
};

// 是否已冻结（fixed 为 left / right 即视为冻结）
const isFrozen = (fieldValue) =>
  Boolean(props.fieldConfig.find((item) => item.value === fieldValue)?.fixed);

const onHeaderSort = (fieldValue, direction) => {
  // 再次点击已选中的排序方向 -> 取消该列排序
  const isSame = getSortDirection(fieldValue) === direction;
  emit("headerSort", fieldValue, isSame ? "" : direction);
  closeHeaderMenu(fieldValue);
};

const onHeaderFreeze = (fieldValue) => {
  emit("headerFreeze", fieldValue);
  closeHeaderMenu(fieldValue);
};

const onHeaderHide = (fieldValue) => {
  emit("headerHide", fieldValue);
  closeHeaderMenu(fieldValue);
};

// 列头菜单：应用筛选（与筛选面板同步，同字段覆盖）
const onHeaderFilter = (fieldValue) => {
  const operator = filterOperator.value;
  const noValue = isNoValueOperator.value;
  const raw = String(filterValue.value ?? "").trim();
  // 该列已有条件时，清空值表示移除条件，不再拦截；否则提示补全筛选值
  if (!noValue && !raw && !hasFieldFilter(fieldValue)) {
    ElMessage.warning("请输入筛选值");
    return;
  }
  emit("headerFilter", {
    field: fieldValue,
    operator,
    value: noValue ? null : raw,
  });
  closeHeaderMenu(fieldValue);
};

const formatDate = (date) => {
  if (!date) return "-";
  const d = new Date(date);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  const hours = String(d.getHours()).padStart(2, "0");
  const minutes = String(d.getMinutes()).padStart(2, "0");
  const seconds = String(d.getSeconds()).padStart(2, "0");
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
};

const formatRelativeTime = (date) => {
  if (!date) return "-";
  const now = new Date();
  const d = new Date(date);
  const diff = now - d;
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  const months = Math.floor(days / 30);
  const years = Math.floor(days / 365);
  if (seconds < 60) return "刚刚";
  if (minutes < 60) return `${minutes}分钟前`;
  if (hours < 24) return `${hours}小时前`;
  if (days < 30) return `${days}天前`;
  if (months < 12) return `${months}个月前`;
  return `${years}年前`;
};

const handleStatusChange = async (row) => {
  try {
    const res = await request.post("/admin/menu/update-menu", {
      data: { id: row.id, status: row.status },
    });
    if (res.code === 200) {
      ElMessage.success("状态已更新");
    } else {
      ElMessage.error("更新失败");
      row.status = !row.status;
    }
  } catch (error) {
    console.error("更新状态失败:", error);
    ElMessage.error("更新失败");
    row.status = !row.status;
  }
};

const handleSelectionChange = (selection) => emit("selectionChange", selection);
const handleRowDblclick = (row) => emit("rowDblclick", row);
const handleEdit = (row) => emit("edit", row);
const handleDelete = (row) => emit("delete", row);
const handleFieldSettings = () => emit("fieldSettings");
const handleSizeChange = (size) => emit("sizeChange", size);
const handleCurrentChange = (current) => emit("currentChange", current);

const doLayout = () => {
  nextTick(() => {
    tableRef.value?.doLayout();
  });
};

defineExpose({ doLayout });
</script>

<style scoped>
.admin-user-table {
  width: 100%;
}

.cell-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.action-btn-small {
  margin-left: 0;
}

.pagination-wrapper {
  display: flex;
  margin-top: 0;
  justify-content: flex-end;
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

/* 状态图标（排序 / 筛选 / 筛选+排序）：有状态时默认展示，鼠标悬停表头时让位给操作图标 */
.col-header-menu-sort {
  display: none;
  align-items: center;
  justify-content: center;
  color: var(--td-text-color-primary, #303133);
}

.col-header-menu-trigger.has-state .col-header-menu-sort {
  display: inline-flex;
}

/* 筛选+排序组合图标：漏斗与排序箭头水平并排，避免箭头叠加遮挡漏斗轮廓 */
.col-header-menu-sort--combo {
  align-items: center;
  gap: 1px;
}

/* 组合状态加宽触发区，保证并排后的「漏斗 + 箭头」完整落在触发区内 */
.col-header-menu-trigger:has(.col-header-menu-sort--combo) {
  width: 22px;
}

/* 组合图标内漏斗略缩小，为右侧箭头让出空间 */
.col-header-menu-sort--combo > .el-icon:first-child {
  font-size: 12px;
}

/* 组合图标内排序箭头：与漏斗水平并排、垂直居中；
   仅纵向拉伸（不改变宽度），使箭头比原有的扁平三角更修长 */
.col-header-menu-sort-arrow {
  font-size: 9px;
  transform: scaleY(1.6);
}

/* 操作图标：默认隐藏，鼠标悬停表头才出现；图标旋转 90° 呈竖排三点 */
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

/* 有状态（排序 / 筛选）时悬停表头保持状态图标，不切换为操作图标 */
.col-header:hover .col-header-menu-trigger.has-state .col-header-menu-btn {
  display: none;
}

.col-header-menu {
  display: flex;
  flex-direction: column;
}

.col-header-menu-item {
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

.col-header-menu-item:hover {
  background-color: var(--td-bg-color-container-hover, #f5f7fa);
}

.col-header-menu-item.is-checked {
  color: var(--td-text-color-brand, #409eff);
}

.col-header-menu-check {
  margin-left: auto;
}

.col-header-menu-divider {
  height: 1px;
  margin: 4px 0;
  background-color: var(--td-component-stroke, #ebeef5);
}

.col-header-menu-filter {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 2px 6px 6px;
}

/* 筛选标题行：图标 + 「筛选」+ 操作符（内联文字形式） */
.col-header-menu-filter-head {
  display: flex;
  align-items: center;
  gap: 4px;
}

.col-header-menu-filter-icon {
  font-size: 14px;
  color: var(--td-text-color-secondary, #909399);
}

.col-header-menu-filter-title {
  color: var(--td-text-color-secondary, #909399);
  white-space: nowrap;
}

/* 操作符去掉下拉框描边与背景，选中值以主题色文字呈现；与「筛选」文字留出间距 */
.col-header-menu-filter-operator {
  width: 120px;
  margin-left: 4px;
}

.col-header-menu-filter-operator :deep(.el-select__wrapper) {
  padding: 0;
  min-height: 32px;
  background-color: transparent !important;
  box-shadow: none !important;
}

.col-header-menu-filter-operator :deep(.el-select__selected-item),
.col-header-menu-filter-operator :deep(.el-select__placeholder) {
  font-weight: 500;
  color: var(--td-text-color-brand, #409eff);
}

.col-header-menu-filter-value {
  width: 100%;
}

.col-header-menu-filter-btn {
  width: 100%;
}
</style>