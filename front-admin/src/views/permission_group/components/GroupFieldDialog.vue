<template>
  <el-dialog :model-value="visible" title="字段权限配置" width="720px" class="permission-group-dialog" destroy-on-close
    @update:model-value="handleVisibleChange" @open="handleOpen">
    <div class="dialog-toolbar">
      <el-input v-model="keyword" placeholder="搜索字段名或字段名称" clearable class="search-input">
        <template #prefix>
          <el-icon>
            <Search />
          </el-icon>
        </template>
      </el-input>
      <div class="toolbar-right">
        <el-button @click="handleAllVisible">全部可见</el-button>
        <el-button @click="handleAllHidden">全部隐藏</el-button>
        <span class="dialog-tip">共 {{ rows.length }} 个字段</span>
      </div>
    </div>

    <div class="table-wrap" v-loading="loading">
      <el-table :data="filteredRows" size="small" border stripe max-height="420">
        <el-table-column prop="field" label="字段名" min-width="160" show-overflow-tooltip />
        <el-table-column prop="fieldLabel" label="字段名称" min-width="140" show-overflow-tooltip />
        <el-table-column label="可见" width="90" align="center">
          <template #default="{ row }">
            <el-switch v-model="row.visible" :active-value="1" :inactive-value="0"
              @change="handleRowVisibleChange(row)" />
          </template>
        </el-table-column>
        <el-table-column label="可编辑" width="90" align="center">
          <template #default="{ row }">
            <el-switch v-model="row.editable" :active-value="1" :inactive-value="0" :disabled="row.visible !== 1" />
          </template>
        </el-table-column>
      </el-table>
    </div>

    <template #footer>
      <el-button @click="handleVisibleChange(false)">取消</el-button>
      <el-button type="primary" :loading="saving" @click="handleSubmit">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed } from "vue";
import { Search } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { getFieldCatalog, getGroupDetail, setGroupFields } from "../permissionGroupApi";

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

const keyword = ref("");
const rows = ref([]);
const loading = ref(false);
const saving = ref(false);

const moduleName = computed(() => (props.group && props.group.module) || "");

const filteredRows = computed(() => {
  const key = keyword.value.trim().toLowerCase();
  if (!key) return rows.value;
  return rows.value.filter(
    (row) =>
      String(row.field).toLowerCase().includes(key) ||
      String(row.fieldLabel || "").toLowerCase().includes(key),
  );
});

const handleRowVisibleChange = (row) => {
  if (row.visible !== 1) {
    row.editable = 0;
  }
};

const handleAllVisible = () => {
  rows.value.forEach((row) => {
    row.visible = 1;
  });
};

const handleAllHidden = () => {
  rows.value.forEach((row) => {
    row.visible = 0;
    row.editable = 0;
  });
};

const handleOpen = async () => {
  if (!props.group || !props.group.id || !moduleName.value) return;
  keyword.value = "";
  loading.value = true;
  try {
    const [catalogRes, detailRes] = await Promise.all([
      getFieldCatalog(moduleName.value),
      getGroupDetail(props.group.id),
    ]);

    if (catalogRes.code !== 200) {
      rows.value = [];
      ElMessage.error(catalogRes.message || "获取字段目录失败");
      return;
    }
    const catalog = catalogRes.data || [];
    const existing = detailRes.code === 200 ? detailRes.data?.fields || [] : [];
    const configMap = new Map(
      existing.filter((item) => item.module === moduleName.value).map((item) => [item.field, item]),
    );

    rows.value = catalog.map((item) => {
      const conf = configMap.get(item.field);
      return {
        field: item.field,
        fieldLabel: item.fieldLabel || conf?.fieldLabel || item.field,
        visible: conf ? Number(conf.visible) : 1,
        editable: conf ? Number(conf.editable) : 1,
      };
    });
  } catch (error) {
    ElMessage.error("加载字段权限失败");
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
  const fields = rows.value.map((row) => ({
    field: row.field,
    fieldLabel: row.fieldLabel,
    visible: row.visible,
    editable: row.visible === 1 ? row.editable : 0,
  }));
  saving.value = true;
  try {
    const res = await setGroupFields(props.group.id, moduleName.value, fields);
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
