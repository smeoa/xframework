<template>
  <el-dialog
    v-model="visible"
    title="导入菜单"
    width="600px"
    :close-on-click-modal="false"
  >
    <el-scrollbar class="dialog-content">
      <el-form :model="form" :rules="rules" ref="formRef" class="form-layout">
        <el-form-item label="导入文件" prop="file" required>
          <el-upload
            class="upload-demo"
            drag
            :auto-upload="false"
            :on-change="handleFileChange"
            :file-list="fileList"
            accept=".xlsx,.xls,.csv"
          >
            <el-icon class="el-icon--upload">
              <Upload />
            </el-icon>
            <div class="el-upload__text">
              将文件拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                只能上传 xlsx/xls/csv 文件
              </div>
            </template>
          </el-upload>
        </el-form-item>
        <el-form-item label="导入模式">
          <el-radio-group v-model="form.importMode">
            <el-radio label="insert">新增</el-radio>
            <el-radio label="update">更新</el-radio>
            <el-radio label="insert_update">新增或更新</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="字段映射">
          <el-alert
            title="字段映射说明：请将Excel列号与菜单字段进行对应"
            type="info"
            :closable="false"
            show-icon
          />
          <el-table :data="fieldMapping" border style="width: 100%; margin-top: 8px">
            <el-table-column prop="field" label="字段名" width="120" />
            <el-table-column prop="label" label="字段说明" width="120" />
            <el-table-column prop="column" label="Excel列号" width="120">
              <template #default="{ row }">
                <el-select v-model="row.column" placeholder="请选择">
                  <el-option v-for="col in columnOptions" :key="col.value" :label="col.label" :value="col.value" />
                </el-select>
              </template>
            </el-table-column>
          </el-table>
        </el-form-item>
      </el-form>
    </el-scrollbar>
    <template #footer>
      <el-button @click="handleCancel">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="loading">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Upload } from "@element-plus/icons-vue";
import request from "@/utils/request";

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["update:visible", "import-success"]);

const visible = ref(props.visible);
const loading = ref(false);
const formRef = ref(null);
const fileList = ref([]);

const form = reactive({
  importMode: "insert",
});

const columnOptions = [
  { value: "column1", label: "第1列" },
  { value: "column2", label: "第2列" },
  { value: "column3", label: "第3列" },
  { value: "column4", label: "第4列" },
  { value: "column5", label: "第5列" },
  { value: "column6", label: "第6列" },
  { value: "column7", label: "第7列" },
  { value: "column8", label: "第8列" },
  { value: "column9", label: "第9列" },
  { value: "column10", label: "第10列" },
];

const fieldMapping = reactive([
  { field: "name", label: "菜单名称", column: "column1" },
  { field: "path", label: "路径", column: "column2" },
  { field: "component", label: "组件", column: "column3" },
  { field: "icon", label: "图标", column: "column4" },
  { field: "type", label: "类型", column: "column5" },
  { field: "permission", label: "权限标识", column: "column6" },
  { field: "status", label: "状态", column: "column7" },
  { field: "pid", label: "上级菜单ID", column: "column8" },
]);

const rules = {
  file: [{ required: true, message: "请选择要导入的文件", trigger: "change" }],
};

const handleFileChange = (file) => {
  fileList.value = [file];
};

const handleCancel = () => {
  visible.value = false;
  fileList.value = [];
  form.importMode = "insert";
  emit("update:visible", false);
};

const handleSubmit = async () => {
  if (!fileList.value.length) {
    ElMessage.warning("请选择要导入的文件");
    return;
  }

  try {
    loading.value = true;
    const formData = new FormData();
    formData.append("file", fileList.value[0].raw);
    formData.append("import_mode", form.importMode);
    formData.append("field_mapping", JSON.stringify(fieldMapping));

    const res = await request.post("/admin/menu/import-menu", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });

    if (res.code === 200) {
      const result = res.data;
      const message = `导入完成：成功${result.success}条，失败${result.failure}条，共${result.total}条`;
      if (result.errors && result.errors.length > 0) {
        ElMessageBox.alert(
          `${message}\n\n失败详情：\n${result.errors.map((e, i) => `${i + 1}. 第${e.row}行: ${e.message}`).join("\n")}`,
          "导入结果",
          { type: "info" }
        );
      } else {
        ElMessage.success(message);
      }
      emit("import-success");
    }
  } catch (error) {
    ElMessage.error("导入失败");
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.dialog-content {
  max-height: 400px;
}

.form-layout {
  padding: 8px;
}
</style>