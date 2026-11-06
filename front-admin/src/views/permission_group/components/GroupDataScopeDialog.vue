<template>
  <el-dialog :model-value="visible" title="数据权限配置" width="600px" class="permission-group-dialog" destroy-on-close
    @update:model-value="handleVisibleChange" @open="handleOpen">
    <div class="dialog-tip tip-block">
      配置业务模块 {{ moduleLabel }} 的数据可见范围，由后端在查询 SQL 中注入生效；未配置时默认仅本人数据。
    </div>

    <el-radio-group v-model="scope" class="scope-group" v-loading="loading">
      <el-radio v-for="option in DATA_SCOPE_OPTIONS" :key="option.value" :value="option.value" class="scope-radio">
        {{ option.label }}
      </el-radio>
    </el-radio-group>

    <div v-if="scope === 'custom'" class="custom-dept">
      <div class="dialog-tip tip-block">
        自定义部门按所选部门精确匹配（不含下级部门）；如需包含下级部门请一并勾选。
      </div>
      <div class="tree-wrap">
        <el-tree ref="deptTreeRef" :data="deptTree" node-key="id" show-checkbox check-strictly default-expand-all
          :expand-on-click-node="false" :props="deptTreeProps">
          <template #empty>
            <div class="empty-node">暂无部门数据</div>
          </template>
        </el-tree>
      </div>
    </div>

    <template #footer>
      <el-button @click="handleVisibleChange(false)">取消</el-button>
      <el-button type="primary" :loading="saving" @click="handleSubmit">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, nextTick } from "vue";
import { ElMessage } from "element-plus";
import {
  DATA_SCOPE_OPTIONS,
  buildDeptTree,
  getBindableSubjects,
  getGroupDetail,
  setGroupDataScope,
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

const deptTreeProps = {
  label: "label",
  children: "children",
};

const deptTreeRef = ref(null);
const deptTree = ref([]);
const scope = ref("dept");
const loading = ref(false);
const saving = ref(false);

const moduleName = computed(() => (props.group && props.group.module) || "");
const moduleLabel = computed(() => moduleName.value || "未指定");

const handleOpen = async () => {
  if (!props.group || !props.group.id) return;
  loading.value = true;
  try {
    const [detailRes, subjectRes] = await Promise.all([
      getGroupDetail(props.group.id),
      getBindableSubjects(),
    ]);

    if (subjectRes.code === 200) {
      deptTree.value = buildDeptTree(subjectRes.data?.depts || []);
    } else {
      deptTree.value = [];
      ElMessage.error(subjectRes.message || "获取部门选项失败");
    }

    const scopes = detailRes.code === 200 ? detailRes.data?.dataScopes || [] : [];
    const current = scopes.find((item) => item.module === moduleName.value);
    scope.value = current?.scope || "dept";
    const checkedDeptIds = Array.isArray(current?.customDeptIds) ? current.customDeptIds : [];

    await nextTick();
    if (deptTreeRef.value) {
      deptTreeRef.value.setCheckedKeys(checkedDeptIds);
    }
  } catch (error) {
    ElMessage.error("加载数据权限失败");
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
  const customDeptIds =
    scope.value === "custom" && deptTreeRef.value ? deptTreeRef.value.getCheckedKeys() : [];
  if (scope.value === "custom" && !customDeptIds.length) {
    ElMessage.warning("自定义数据范围必须选择至少一个部门");
    return;
  }
  saving.value = true;
  try {
    const res = await setGroupDataScope(props.group.id, moduleName.value, scope.value, customDeptIds);
    if (res.code === 200) {
      ElMessage.success("保存成功");
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
