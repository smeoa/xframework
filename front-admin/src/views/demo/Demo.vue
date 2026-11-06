<template>
  <div class="demo-page">
    <el-card>
      <template #header>
        <div class="page-header">
          <span class="page-title">Demo 示例</span>
          <div class="page-actions">
            <el-input
              v-model="query.keyword"
              placeholder="搜索名称/描述"
              clearable
              style="width: 220px"
              @keyup.enter="loadList"
              @clear="loadList"
            />
            <el-button :icon="Search" @click="loadList">搜索</el-button>
            <el-button v-if="canCreate" type="primary" :icon="Plus" @click="openEdit()">新增</el-button>
            <el-button
              v-if="canDelete"
              type="danger"
              plain
              :disabled="!selected.length"
              @click="onBatchDelete"
            >批量删除</el-button>
          </div>
        </div>
      </template>

      <el-table v-loading="loading" :data="rows" border stripe @selection-change="(v) => (selected = v)">
        <el-table-column type="selection" width="45" />
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="sort" label="排序" width="80" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'">
              {{ row.status === 1 ? "启用" : "停用" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="170">
          <template #default="{ row }">{{ formatTime(row.createTime) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button v-if="canUpdate" link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button v-if="canDelete" link type="danger" @click="onDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="page-footer">
        <el-pagination
          v-model:current-page="query.page"
          v-model:page-size="query.limit"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @size-change="loadList"
          @current-change="loadList"
        />
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑' : '新增'" width="520px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" maxlength="100" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" maxlength="500" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort" :min="0" :max="9999" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.status" :active-value="1" :inactive-value="0" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" maxlength="200" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="onSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Plus, Search } from "@element-plus/icons-vue";
import request from "@/utils/request";
import { hasPermission } from "@/utils/permission";

const API = {
  LIST: "/admin/demo/get-demo-list",
  CREATE: "/admin/demo/create-demo",
  UPDATE: "/admin/demo/update-demo",
  DELETE: "/admin/demo/delete-demo",
  BATCH: "/admin/demo/batch-demo",
};

const loading = ref(false);
const saving = ref(false);
const rows = ref([]);
const total = ref(0);
const selected = ref([]);
const dialogVisible = ref(false);
const formRef = ref(null);

const query = reactive({ page: 1, limit: 20, keyword: "" });
const form = reactive({ id: null, name: "", description: "", sort: 0, status: 1, remark: "" });
const rules = { name: [{ required: true, message: "请输入名称", trigger: "blur" }] };

const canCreate = computed(() => hasPermission("demo:create"));
const canUpdate = computed(() => hasPermission("demo:update"));
const canDelete = computed(() => hasPermission("demo:delete"));

async function loadList() {
  loading.value = true;
  try {
    const res = await request.post(API.LIST, { ...query });
    if (res.code === 200) {
      rows.value = res.data?.items ?? [];
      total.value = res.data?.total ?? 0;
    } else {
      ElMessage.error(res.message || "查询失败");
    }
  } finally {
    loading.value = false;
  }
}

function openEdit(row) {
  Object.assign(form, row
    ? { id: row.id, name: row.name, description: row.description, sort: row.sort, status: row.status, remark: row.remark }
    : { id: null, name: "", description: "", sort: 0, status: 1, remark: "" });
  dialogVisible.value = true;
}

async function onSave() {
  await formRef.value.validate();
  saving.value = true;
  try {
    const url = form.id ? API.UPDATE : API.CREATE;
    const res = await request.post(url, { data: { ...form } });
    if (res.code === 200) {
      ElMessage.success("保存成功");
      dialogVisible.value = false;
      loadList();
    } else {
      ElMessage.error(res.message || "保存失败");
    }
  } finally {
    saving.value = false;
  }
}

async function onDelete(row) {
  await ElMessageBox.confirm(`确认删除「${row.name}」？`, "提示", { type: "warning" });
  const res = await request.post(API.DELETE, { data: { id: row.id } });
  if (res.code === 200) {
    ElMessage.success("删除成功");
    loadList();
  } else {
    ElMessage.error(res.message || "删除失败");
  }
}

async function onBatchDelete() {
  await ElMessageBox.confirm(`确认删除选中的 ${selected.value.length} 条数据？`, "提示", { type: "warning" });
  const res = await request.post(API.BATCH, { ids: selected.value.map((r) => r.id) });
  if (res.code === 200) {
    ElMessage.success("删除成功");
    loadList();
  } else {
    ElMessage.error(res.message || "删除失败");
  }
}

function formatTime(value) {
  return value ? String(value).replace("T", " ").slice(0, 19) : "-";
}

onMounted(loadList);
</script>

<style scoped>
.demo-page {
  padding: 16px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.page-title {
  font-size: 16px;
  font-weight: 600;
}

.page-actions {
  display: flex;
  gap: 8px;
}

.page-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
