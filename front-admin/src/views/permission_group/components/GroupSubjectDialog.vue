<template>
  <el-dialog :model-value="visible" title="绑定主体" width="680px" class="permission-group-dialog" destroy-on-close
    @update:model-value="handleVisibleChange" @open="handleOpen">
    <div class="dialog-tip tip-block">
      权限组按「部门 / 角色 / 人员」三类主体合并解析，任一主体命中即对该用户生效；人员或角色匹配优先级高于部门。
    </div>

    <el-tabs v-model="activeTab" class="subject-tabs" v-loading="loading">
      <el-tab-pane :label="`部门 (${deptCount})`" name="dept">
        <div class="tip-inline">部门按所选部门精确匹配（不含下级部门）。</div>
        <div class="tree-wrap">
          <el-tree ref="deptTreeRef" :data="deptTree" node-key="id" show-checkbox check-strictly default-expand-all
            :expand-on-click-node="false" :props="deptTreeProps" @check="syncDeptIds">
            <template #empty>
              <div class="empty-node">暂无部门数据</div>
            </template>
          </el-tree>
        </div>
      </el-tab-pane>

      <el-tab-pane :label="`角色 (${selectedRoleIds.length})`" name="role">
        <div class="table-wrap">
          <el-checkbox-group v-model="selectedRoleIds" class="subject-checkbox-group">
            <el-checkbox v-for="role in roles" :key="role.id" :value="role.id">
              {{ role.name || role.title }}（{{ role.code }}）
            </el-checkbox>
          </el-checkbox-group>
          <div v-if="!roles.length" class="empty-node">暂无角色数据</div>
        </div>
      </el-tab-pane>

      <el-tab-pane :label="`人员 (${selectedUserIds.length})`" name="user">
        <el-select v-model="selectedUserIds" multiple filterable collapse-tags collapse-tags-tooltip
          placeholder="搜索并选择人员" class="full-width">
          <el-option v-for="user in users" :key="user.id" :label="`${user.name || user.username}（${user.username}）`"
            :value="user.id" />
        </el-select>
      </el-tab-pane>
    </el-tabs>

    <template #footer>
      <el-button @click="handleVisibleChange(false)">取消</el-button>
      <el-button type="primary" :loading="saving" @click="handleSubmit">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, nextTick } from "vue";
import { ElMessage } from "element-plus";
import { bindGroupSubjects, buildDeptTree, getBindableSubjects, getGroupDetail } from "../permissionGroupApi";

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

const activeTab = ref("dept");
const deptTreeRef = ref(null);
const deptTree = ref([]);
const roles = ref([]);
const users = ref([]);
const selectedRoleIds = ref([]);
const selectedUserIds = ref([]);
const checkedDeptIds = ref([]);
const loading = ref(false);
const saving = ref(false);

const deptCount = computed(() => checkedDeptIds.value.length);

const syncDeptIds = () => {
  const tree = deptTreeRef.value;
  checkedDeptIds.value = tree ? tree.getCheckedKeys() : [];
};

const handleOpen = async () => {
  if (!props.group || !props.group.id) return;
  activeTab.value = "dept";
  checkedDeptIds.value = [];
  loading.value = true;
  try {
    const [detailRes, subjectRes] = await Promise.all([
      getGroupDetail(props.group.id),
      getBindableSubjects(),
    ]);

    if (subjectRes.code === 200) {
      const data = subjectRes.data || {};
      deptTree.value = buildDeptTree(data.depts || []);
      roles.value = data.roles || [];
      users.value = data.users || [];
    } else {
      ElMessage.error(subjectRes.message || "获取可绑定主体失败");
    }

    const subjects = detailRes.code === 200 ? detailRes.data?.subjects || [] : [];
    const deptIds = subjects.filter((s) => s.subjectType === "dept").map((s) => s.subjectId);
    selectedRoleIds.value = subjects.filter((s) => s.subjectType === "role").map((s) => s.subjectId);
    selectedUserIds.value = subjects.filter((s) => s.subjectType === "user").map((s) => s.subjectId);

    await nextTick();
    if (deptTreeRef.value) {
      deptTreeRef.value.setCheckedKeys(deptIds);
    }
    checkedDeptIds.value = deptIds;
  } catch (error) {
    ElMessage.error("加载主体绑定失败");
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
  const deptIds = checkedDeptIds.value;
  const subjects = [
    ...deptIds.map((id) => ({ subjectType: "dept", subjectId: id })),
    ...selectedRoleIds.value.map((id) => ({ subjectType: "role", subjectId: id })),
    ...selectedUserIds.value.map((id) => ({ subjectType: "user", subjectId: id })),
  ];
  saving.value = true;
  try {
    const res = await bindGroupSubjects(props.group.id, subjects);
    if (res.code === 200) {
      ElMessage.success(`绑定成功，共 ${subjects.length} 个主体`);
      emit("update:visible", false);
    } else {
      ElMessage.error(res.message || "绑定失败");
    }
  } catch (error) {
    ElMessage.error("绑定失败，请稍后重试");
  } finally {
    saving.value = false;
  }
};
</script>
