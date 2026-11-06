<template>
  <div class="admin-user-table">
    <el-table
      :data="roleMembers"
      class="admin-table"
      v-loading="roleLoading"
      ref="roleTableRef"
      row-key="id"
      height="100%"
      @selection-change="handleSelectionChange"
      border
    >
      <!-- 选择框列 -->
      <el-table-column type="selection" width="40" resizable />

      <template v-for="field in sortedVisibleFields" :key="field.value">
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
                    :class="{
                      'is-checked': getSortDirection(field.value) === 'asc',
                    }"
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
                    :class="{
                      'is-checked': getSortDirection(field.value) === 'desc',
                    }"
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
            <span v-if="field.value === 'deptName'">{{ row.deptName || row.dept_name || "-" }}</span>
            <template v-else-if="field.value === 'avatar'">
              <el-avatar v-if="row.avatar" :size="40" :src="row.avatar" />
              <span v-else>-</span>
            </template>
            <template
              v-else-if="
                field.value === 'images'
              "
            >
              <div
                v-if="row.images && row.images.length > 0"
                class="table-images"
              >
                <el-image
                  v-for="(img, idx) in row.images.slice(0, 3)"
                  :key="idx"
                  :src="img.url || img.storagePath"
                  :title="img.filename || '图片'"
                  fit="cover"
                  class="table-image-item"
                  @click="openImagePreview(row, idx)"
                />
                <span v-if="row.images.length > 3" class="more-count"
                  >+{{ row.images.length - 3 }}</span
                >
              </div>
              <span v-else>-</span>
            </template>
            <template
              v-else-if="field.value === 'attachments'"
            >
              <div
                v-if="row.attachments && row.attachments.length > 0"
                class="table-attachments"
              >
                <span
                  v-for="(file, idx) in row.attachments.slice(0, 2)"
                  :key="idx"
                  :title="file.filename"
                  class="attachment-tag"
                  @click="openAttachmentPreview(file)"
                >
                  <FileIcon :file-type="file.fileType" :size="14" />
                  <span class="attachment-name">{{ file.filename }}</span>
                </span>
                <span v-if="row.attachments.length > 2" class="more-count"
                  >+{{ row.attachments.length - 2 }}</span
                >
              </div>
              <span v-else>-</span>
            </template>
            <template v-else-if="field.value === 'status'">
              <el-tag :type="row.status ? 'success' : 'danger'">
                {{ row.status ? "启用" : "禁用" }}
              </el-tag>
            </template>
            <template
              v-else-if="
                field.value === 'createTime' || field.value === 'createdTime'
              "
            >
              <span :title="formatDate(row.createTime || row.createTime)">{{
                formatRelativeTime(row.createTime || row.createdTime)
              }}</span>
            </template>
            <template
              v-else-if="
                field.value === 'updateTime' || field.value === 'updatedTime'
              "
            >
              <span :title="formatDate(row.updateTime || row.updatedTime)">{{
                formatRelativeTime(row.updateTime || row.updatedTime)
              }}</span>
            </template>
            <template v-else-if="field.value === 'lastLoginTime'">
              <span :title="formatDate(row.lastLoginTime)">{{
                formatRelativeTime(row.lastLoginTime)
              }}</span>
            </template>
            <template v-else>
              <span>{{ row[field.value] ?? "-" }}</span>
            </template>
          </template>
        </el-table-column>
      </template>

      <!-- 操作列 -->
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <div class="cell-actions">
            <el-link
              type="danger"
              @click="handleRemove(row)"
              title="移除"
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

    <el-image-viewer
      v-if="showImageViewer"
      :url-list="previewImageList"
      :initial-index="previewImageIndex"
      :hide-on-click-modal="true"
      @close="showImageViewer = false"
    />

    <!-- 文件预览 -->
    <FilePreview
      v-model:visible="filePreviewVisible"
      :url="previewFileUrl"
      :filename="previewFileName"
      :filesize="previewFileSize"
      :title="previewFileName"
      :show-info="true"
    />

    <el-pagination
      v-model:current-page="localRoleCurrentPage"
      v-model:page-size="localRolePageSize"
      :total="roleTotal"
      :page-sizes="[20, 50, 100]"
      layout="total, sizes, prev, pager, next, jumper"
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
      class="pagination-wrapper"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from "vue";
import {
  Edit,
  Delete,
  SortUp,
  SortDown,
  MoreFilled,
  Check,
  Filter,
  CaretTop,
  CaretBottom,
} from "@element-plus/icons-vue";
import { ElMessage, ElImageViewer } from "element-plus";
import FilePreview from "@/components/FilePreview.vue";
import FileIcon from "@/components/FileIcon.vue";

const props = defineProps({
  roleMembers: {
    type: Array,
    default: () => [],
  },
  roleLoading: {
    type: Boolean,
    default: false,
  },
  roleCurrentPage: {
    type: Number,
    default: 1,
  },
  rolePageSize: {
    type: Number,
    default: 20,
  },
  roleTotal: {
    type: Number,
    default: 0,
  },
  visibleFields: {
    type: Array,
    required: true,
    default: () => [],
  },
  fieldConfig: {
    type: Array,
    required: true,
    default: () => [],
  },
  sortRules: {
    type: Array,
    required: true,
    default: () => [],
  },
  // 筛选面板的筛选条件：用于列头菜单回显与列头状态图标
  filterGroups: {
    type: Array,
    default: () => [],
  },
  // 列字段（camelCase）-> 数据库列名（snake）映射
  headerDbFieldMap: {
    type: Object,
    default: () => ({}),
  },
});

const emit = defineEmits([
  "member-selection-change",
  "remove-member",
  "size-change",
  "current-change",
  "headerSort",
  "headerFilter",
]);

const roleTableRef = ref(null);
const showImageViewer = ref(false);
const previewImageList = ref([]);
const previewImageIndex = ref(0);
const filePreviewVisible = ref(false);
const previewFileUrl = ref("");
const previewFileName = ref("");
const previewFileSize = ref(0);

const localRoleCurrentPage = ref(props.roleCurrentPage);
const localRolePageSize = ref(props.rolePageSize);

const sortedVisibleFields = computed(() => {
  return props.fieldConfig.filter((item) =>
    props.visibleFields.includes(item.value),
  );
});

// 打开图片预览
const openImagePreview = (row, index) => {
  if (row.images && row.images.length > 0) {
    previewImageList.value = row.images.map(
      (img) => img.url || img.storagePath
    );
    previewImageIndex.value = index;
    showImageViewer.value = true;
  }
};

// 打开附件预览
const openAttachmentPreview = (file) => {
  previewFileUrl.value = file.url || file.storagePath;
  previewFileName.value = file.filename || "附件";
  previewFileSize.value = file.fileSize || 0;
  filePreviewVisible.value = true;
};

// ==================== 列头菜单 ====================
// 列字段为列表行的 camelCase，排序规则 / 筛选条件存的是数据库列名
const dbFieldOf = (fieldValue) => props.headerDbFieldMap?.[fieldValue] || "";

// 获取排序方向
const getSortDirection = (fieldValue) => {
  const dbField = dbFieldOf(fieldValue);
  if (!dbField) return "";
  const rule = (props.sortRules || []).find((r) => r.field === dbField);
  return rule ? rule.direction : "";
};

// 该列在筛选面板中已有的筛选条件（同一字段只取第一条）
const getFieldCondition = (fieldValue) => {
  const dbField = dbFieldOf(fieldValue);
  if (!dbField) return null;
  for (const group of props.filterGroups || []) {
    const cond = (group.conditions || []).find((item) => item.field === dbField);
    if (cond) return cond;
  }
  return null;
};

// 该列是否存在生效的筛选条件（「为空 / 不为空」无需值，其余必须有值才算生效）
const hasFieldFilter = (fieldValue) => {
  const cond = getFieldCondition(fieldValue);
  if (!cond) return false;
  if (["is_null", "is_not_null"].includes(cond.operator)) return true;
  return String(cond.value ?? "").trim() !== "";
};

// 各列菜单展开状态（按列 key 索引）
const headerMenuVisible = reactive({});
// 列头快捷筛选的草稿：同一时刻只有一个列菜单展开，列间共用
const filterOperator = ref("eq");
const filterValue = ref("");
// 「为空 / 不为空」无需填写筛选值
const isNoValueOperator = computed(() =>
  ["is_null", "is_not_null"].includes(filterOperator.value),
);

// 列头图标状态：无 / 升序 / 降序 / 筛选 / 筛选+升序 / 筛选+降序
const headerStateMap = computed(() => {
  const map = {};
  const columns = Array.isArray(props.fieldConfig) ? props.fieldConfig : [];
  columns.forEach((col) => {
    const direction = getSortDirection(col.value);
    const filtered = hasFieldFilter(col.value);
    if (direction && filtered) map[col.value] = `filter-${direction}`;
    else if (filtered) map[col.value] = "filter";
    else map[col.value] = direction;
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

const onHeaderSort = (fieldValue, direction) => {
  // 再次点击已选中的排序方向 -> 取消该列排序
  const isSame = getSortDirection(fieldValue) === direction;
  emit("headerSort", fieldValue, isSame ? "" : direction);
  closeHeaderMenu(fieldValue);
};

// 列头菜单：应用筛选（同字段覆盖）
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

// 格式化日期
const formatDate = (date) => {
  if (!date) return "-";
  const d = new Date(date);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  const hours = String(d.getHours()).padStart(2, "0");
  const minutes = String(d.getMinutes()).padStart(2, "0");
  return `${year}-${month}-${day} ${hours}:${minutes}`;
};

// 格式化相对时间
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

  if (seconds < 60) return `${seconds}秒前`;
  if (minutes < 60) return `${minutes}分钟前`;
  if (hours < 24) return `${hours}小时前`;
  if (days < 30) return `${days}天前`;
  if (months < 12) return `${months}个月前`;
  return `${years}年前`;
};

// 事件处理
const handleSelectionChange = (selection) => {
  emit("member-selection-change", selection);
};
const handleRemove = (row) => {
  emit("remove-member", row);
};
const handleSizeChange = (size) => {
  emit("size-change", size);
};
const handleCurrentChange = (current) => {
  emit("current-change", current);
};

// 监听 props 变化，同步到本地
watch(
  () => props.roleCurrentPage,
  (newVal) => {
    localRoleCurrentPage.value = newVal;
  }
);
watch(
  () => props.rolePageSize,
  (newVal) => {
    localRolePageSize.value = newVal;
  }
);
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

.pagination-wrapper {
  margin-top: 0;
  justify-content: flex-end;
  display: flex;
}

/* 表头不换行：列宽不足时保持单行展示 */
.admin-user-table :deep(th .cell) {
  white-space: nowrap;
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

.table-images {
  display: flex;
  align-items: center;
  gap: 4px;
}

.table-image-item {
  width: 50px;
  height: 50px;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
  overflow: hidden;
  cursor: pointer;
}

.table-attachments {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}

.attachment-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 6px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background-color: #f5f7fa;
  font-size: 12px;
}

.attachment-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.more-count {
  font-size: 12px;
  color: var(--td-text-color-placeholder);
  background-color: #f0f0f0;
  padding: 2px 6px;
  border-radius: 4px;
}
</style>
