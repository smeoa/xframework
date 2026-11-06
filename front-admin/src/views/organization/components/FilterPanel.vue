<template>
  <el-card class="filter-panel" shadow="never">
    <template #header>
      <!-- 组间逻辑关系 -->
      <div class="groups-logic">
        <span>组间关系：</span>
        <el-select v-model="localGroupsLogic" class="groups-logic-select">
          <el-option label="并且" value="and" />
          <el-option label="或者" value="or" />
        </el-select>
        <el-button type="primary" @click="addFilterGroup">
          <el-icon>
            <Plus />
          </el-icon>
          添加组
        </el-button>
      </div>
    </template>
    <el-scrollbar class="filter-panel-scrollbar">
      <!-- 筛选组 -->
      <div
        v-for="(group, groupIndex) in localFilterGroups"
        :key="groupIndex"
        class="filter-group"
      >
        <el-divider v-if="groupIndex > 0" content-position="center">{{
          group.groupLogic === "and" ? "并且" : "或者"
        }}</el-divider>
        <el-card class="filter-card">
          <template #header>
            <div class="card-header">
              <el-select
                v-model="group.conditionLogic"
                class="condition-logic-select"
              >
                <el-option label="所有" value="and" />
                <el-option label="任意" value="or" />
              </el-select>
              <div class="header-actions">
                <el-button type="primary" @click="addCondToGroup(groupIndex)">
                  <el-icon>
                    <Plus />
                  </el-icon>
                  添加条件
                </el-button>
                <el-button
                  type="danger"
                  @click="removeFilterGroup(groupIndex)"
                  v-if="localFilterGroups.length > 1 && groupIndex > 0"
                >
                  <el-icon>
                    <Delete />
                  </el-icon>
                </el-button>
              </div>
            </div>
          </template>
          <div
            v-for="(cond, condIndex) in group.conditions"
            :key="condIndex"
            class="filter-cond"
          >
            <el-select v-model="cond.field" class="field-select" filterable>
              <el-option label="用户名" value="username" />
              <el-option label="真实姓名" value="name" />
              <el-option label="手机号" value="phone" />
              <el-option label="邮箱" value="email" />
              <el-option label="部门" value="deptId" />
              <el-option label="状态" value="status" />
              <el-option label="创建时间" value="createdTime" />
              <el-option label="更新时间" value="updatedTime" />
              <el-option label="最后登录时间" value="lastLoginTime" />
            </el-select>
            <el-select v-model="cond.operator" class="operator-select">
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
            <!-- 部门字段使用下拉选择；「为空 / 不为空」不需要填写值 -->
            <template v-if="cond.operator !== 'is_null' && cond.operator !== 'is_not_null'">
              <el-select
                v-if="cond.field === 'deptId'"
                v-model="cond.value"
                placeholder="选择部门"
                class="value-select"
                clearable
              >
                <el-option
                  v-for="dept in flatDeptList"
                  :key="dept.id"
                  :label="dept.name"
                  :value="dept.id"
                />
              </el-select>
              <el-input
                v-else
                v-model="cond.value"
                placeholder="请输入值"
                class="value-input"
              />
            </template>
            <el-button
              type="danger"
              @click="removeCondFromGroup(groupIndex, condIndex)"
              class="delete-btn"
            >
              <el-icon>
                <Delete />
              </el-icon>
              删除
            </el-button>
            <el-divider
              v-if="condIndex < group.conditions.length - 1"
              class="cond-divider"
            />
          </div>
        </el-card>
      </div>
      <div class="spacer"></div>
    </el-scrollbar>
    <template #footer>
      <div class="filter-actions">
        <el-button type="primary" @click="applyFilter" class="apply-btn"
          >筛选</el-button
        >
        <el-button @click="resetFilter" class="reset-btn">清空</el-button>
        <el-button @click="handleSaveAs" class="save-as-btn">另存为</el-button>
        <el-button type="primary" @click="handleSave" class="save-btn">保存</el-button>
      </div>
    </template>
  </el-card>
</template>

<script setup>
import { ref, watch, computed } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Plus, Delete } from "@element-plus/icons-vue";

const props = defineProps({
  filterGroups: {
    type: Array,
    default: () => [
      {
        groupLogic: "and",
        conditionLogic: "and",
        conditions: [
          {
            field: "username",
            operator: "eq",
            value: "",
          },
        ],
      },
    ],
  },
  groupsLogic: {
    type: String,
    default: "and",
  },
  deptTree: {
    type: Array,
    default: () => [],
  },
  // 当前生效的已保存方案名，空串表示未选中任何方案（保存按钮据此判断新建还是覆盖更新）
  currentPresetName: { type: String, default: "" },
  // 当前页面已保存的方案名列表，用于新建 / 保存 / 另存为时的前端查重
  presetNames: { type: Array, default: () => [] },
});

const flatDeptList = computed(() => {
  const result = [];
  const flatten = (nodes, prefix = "") => {
    for (const node of nodes) {
      result.push({
        id: node.id,
        name: prefix ? `${prefix} / ${node.name}` : node.name,
      });
      if (node.children?.length) {
        flatten(node.children, prefix ? `${prefix} / ${node.name}` : node.name);
      }
    }
  };
  flatten(props.deptTree);
  return result;
});

const emit = defineEmits([
  "update:filterGroups",
  "update:groupsLogic",
  "apply",
  "reset",
  "save",
  "save-as",
]);

const localFilterGroups = ref([...props.filterGroups]);
const localGroupsLogic = ref(props.groupsLogic);

watch(
  () => props.filterGroups,
  (newGroups) => {
    localFilterGroups.value = [...newGroups];
  },
  { deep: true }
);

watch(
  () => props.groupsLogic,
  (newLogic) => {
    localGroupsLogic.value = newLogic;
  }
);

watch(
  localFilterGroups,
  (newGroups) => {
    const deepCopiedGroups = JSON.parse(JSON.stringify(newGroups));
    const currentPropsJson = JSON.stringify(props.filterGroups);
    const newGroupsJson = JSON.stringify(deepCopiedGroups);
    if (currentPropsJson !== newGroupsJson) {
      emit("update:filterGroups", deepCopiedGroups);
    }
  },
  { deep: true }
);

watch(localGroupsLogic, (newLogic) => {
  if (newLogic !== props.groupsLogic) {
    emit("update:groupsLogic", newLogic);
  }
});

const addFilterGroup = () => {
  localFilterGroups.value.push({
    groupLogic: localGroupsLogic.value,
    conditionLogic: localGroupsLogic.value,
    conditions: [],
  });
};

const removeFilterGroup = (groupIndex) => {
  if (localFilterGroups.value.length > 1) {
    localFilterGroups.value.splice(groupIndex, 1);
  }
};

const addCondToGroup = (groupIndex) => {
  if (!localFilterGroups.value[groupIndex].conditions) {
    localFilterGroups.value[groupIndex].conditions = [];
  }
  localFilterGroups.value[groupIndex].conditions.push({
    field: "username",
    operator: "eq",
    value: "",
  });
};

const removeCondFromGroup = (groupIndex, condIndex) => {
  if (localFilterGroups.value[groupIndex].conditions) {
    localFilterGroups.value[groupIndex].conditions.splice(condIndex, 1);
  }
};

const applyFilter = () => {
  emit("apply");
};

const resetFilter = () => {
  localFilterGroups.value = [
    {
      groupLogic: "and",
      conditionLogic: "and",
      conditions: [],
    },
  ];
  localGroupsLogic.value = "and";
  emit("reset");
};

// 是否存在有效筛选条件（任一条件已选择字段即视为非空）
const hasCondition = computed(() =>
  localFilterGroups.value.some((group) =>
    (group.conditions || []).some((cond) => cond.field),
  ),
);

// 方案名称最大长度，与后端 MAX_NAME_LENGTH / 数据库列定义保持一致
const MAX_PRESET_NAME_LENGTH = 64;

/**
 * 弹出名称输入框收集方案名称
 *
 * @param {string} title 弹框标题
 * @param {string} excludeName 查重时排除的名称（保存已有方案时传原名称，允许名称不变）
 * @returns {Promise<string>} 确认返回名称；取消或校验失败返回空串
 */
const promptPresetName = async (title, excludeName = "") => {
  try {
    const { value } = await ElMessageBox.prompt("请输入筛选条件名称", title, {
      confirmButtonText: "保存",
      cancelButtonText: "取消",
      // 保存已有方案时预填原名称，直接确认即名称不变
      inputValue: excludeName,
      inputValidator: (text) => {
        const name = (text || "").trim();
        if (!name) return "名称不能为空";
        if (name.length > MAX_PRESET_NAME_LENGTH) {
          return `名称长度不能超过 ${MAX_PRESET_NAME_LENGTH} 字符`;
        }
        if (name !== excludeName && props.presetNames.includes(name)) {
          return "方案名称已存在";
        }
        return true;
      },
    });
    return value.trim();
  } catch (error) {
    // 取消输入不做处理
    return "";
  }
};

// 保存条件：已选中方案时预填原名称（可改名，改名即重命名并覆盖更新条件）；未选中方案时新建
const handleSave = async () => {
  if (!hasCondition.value) {
    ElMessage.warning("请先添加筛选条件");
    return;
  }
  const name = await promptPresetName(
    props.currentPresetName ? "保存筛选条件（修改名称即重命名）" : "保存筛选条件",
    props.currentPresetName,
  );
  if (name) emit("save", name);
};

// 另存为：无论当前是否选中方案，均按新名称保存成新方案
const handleSaveAs = async () => {
  if (!hasCondition.value) {
    ElMessage.warning("请先添加筛选条件");
    return;
  }
  const name = await promptPresetName("另存为新的筛选条件");
  if (name) emit("save-as", name);
};
</script>

<style scoped>
.filter-panel {
  width: 320px;
  background-color: #fff;
  height: 100%;
  /* 描边由外层容器（aside）统一承担，卡片自身不重复描边；仅右侧两角随容器圆角 */
  border: 0 !important;
  border-radius: 0 var(--radius-card) var(--radius-card) 0;
}

/* body 只作为滚动区域的外壳，内边距下移到滚动内容上，
   避免滚动条宽度占用内容盒后触发横向滚动 */
.filter-panel > :deep(.el-card__body) {
  padding: 0;
}

/* 滚动容器铺满 body，内部内容用 8px 垂直 / 12px 水平内边距与 header 对齐 */
.filter-panel-scrollbar {
  height: 100%;
}

.filter-panel-scrollbar :deep(.el-scrollbar__view) {
  display: block;
  padding: 8px 12px;
}

/* header 垂直内边距与主卡片 header 一致，使两者高度与底部分隔线对齐；
   水平内边距 25px，使顶部内容与下方筛选组左右对齐 */
.filter-panel > :deep(.el-card__header) {
  padding: var(--td-comp-paddingTB-l) 25px;
}

/* 顶部区域已由 el-card header 承载，内边距由 header 提供 */
.groups-logic {
  display: flex;
  align-items: center;
  border-radius: 4px;
}

/* 标签固定宽度，避免被压缩导致右侧下拉框位置漂移 */
.groups-logic > span {
  width: 75px;
}

/* 添加组按钮靠右对齐 */
.groups-logic .el-button {
  margin-left: auto;
}

.groups-logic-select {
  width: 90px;
  margin-left: 8px;
  margin-right: 8px;
}

.groups-logic-select :deep(.el-select__wrapper) {
  width: 90px;
}

.filter-group {
}

.filter-card {
  max-width: 480px;
  width: 295px;
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  /* 占满 header 内容盒，使「添加条件」等操作按钮靠右贴齐卡片内边缘 */
  width: 100%;
}

.filter-card :deep(.el-card__header) {
  width: 295px;
  padding-left: 12px;
  padding-right: 12px;
}

.filter-card :deep(.el-card__body) {
  padding-left: 0;
  padding-right: 0;
  padding-bottom: 8px;
}

.condition-logic-select {
  width: 148px;
  margin-left: 0px;
}

.condition-logic-select :deep(.el-select__wrapper) {
  width: 85px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.header-actions :deep(.el-button--primary) {
  margin-left: 20px;
  padding-left: 12px;
}

.filter-cond {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  width: 271px;
  margin: 0 auto;
}

.field-select {
  width: 148px;
  margin-bottom: 8px;
}

.field-select :deep(.el-select__wrapper) {
  width: 148px;
}

.value-input :deep(.el-input__wrapper) {
  width: 148px;
}

.operator-select {
  width: 97px;
  margin-bottom: 8px;
}

.operator-select :deep(.el-select__wrapper) {
  width: 96px;
}

.operator-select {
  margin-left: auto;
}

.value-select {
  width: 168px;
  margin-bottom: 8px;
}

.value-input {
  width: 148px;
  margin-bottom: 8px;
}

.delete-btn {
  width: 96px;
  line-height: 24px;
  margin-bottom: 8px;
  margin-left: auto;
}

.cond-divider {
  margin-bottom: 16px;
  margin-top: 8px;
}

.spacer {
  margin-bottom: 120px;
}

/* 操作栏已由 el-card 的 footer 承载：去掉原先 fixed 定位与自带内边距/描边，
   内边距与外框统一交给 footer，避免与 footer 的顶边框和圆角叠加 */
.filter-actions {
  width: 100%;
  display: flex;
  flex-direction: row;
  /* 全局 .filter-actions 带 align-items: center，会令子行收缩为内容宽度，此处显式拉伸 */
  align-items: stretch;
  padding: 0;
  border: 0;
  border-radius: 0;
  background-color: transparent;
  gap: 8px;
}

/* 四个按钮单行平分宽度：去掉 Element Plus 相邻按钮外边距，压缩内边距避免「保存条件」换行 */
.filter-actions .el-button {
  flex: 1;
  margin-left: 0;
  padding-left: 8px;
  padding-right: 8px;
}
</style>
