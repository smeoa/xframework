<template>
  <el-dialog :model-value="visible" :title="isEdit ? '编辑权限组' : '新建权限组'" width="560px" class="permission-group-dialog"
    destroy-on-close @update:model-value="handleVisibleChange" @open="handleOpen">
    <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
      <el-form-item label="权限组名称" prop="title">
        <el-input v-model="form.title" placeholder="如：运营-店铺查看" maxlength="50" show-word-limit />
      </el-form-item>
      <el-form-item v-if="!menuBound" label="权限组编码" prop="code">
        <el-input v-model="form.code" :disabled="isEdit" placeholder="留空则自动生成" maxlength="50" />
      </el-form-item>
      <el-form-item v-if="!menuBound" label="所属菜单" prop="menuId">
        <el-select v-model="form.menuId" placeholder="请选择菜单（权限组归属的业务场景）" filterable class="full-width"
          @change="handleMenuChange">
          <el-option v-for="menu in menuOptions" :key="menu.id" :label="menu.title" :value="menu.id">
            <span>{{ menu.title }}</span>
            <span class="option-code">{{ menu.code }}</span>
          </el-option>
        </el-select>
      </el-form-item>
      <el-form-item v-if="!menuBound" label="业务模块" prop="module">
        <el-input v-model="form.module" readonly placeholder="由所属菜单自动推导" />
      </el-form-item>
      <el-form-item label="排序">
        <el-input-number v-model="form.sort" :min="0" :max="9999" />
      </el-form-item>
      <el-form-item label="状态">
        <el-radio-group v-model="form.status">
          <el-radio :value="1">启用</el-radio>
          <el-radio :value="0">禁用</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item label="描述">
        <el-input v-model="form.description" type="textarea" :rows="3" placeholder="该权限组允许的业务权限场景说明"
          maxlength="200" show-word-limit />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="handleVisibleChange(false)">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, ref, reactive } from "vue";

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  group: {
    type: Object,
    default: null,
  },
  menuOptions: {
    type: Array,
    default: () => [],
  },
  // 由当前菜单上下文自动绑定所属菜单与业务模块（抽屉入口），此时不展示这两项与编码
  menuBound: {
    type: Boolean,
    default: false,
  },
  loading: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["update:visible", "submit"]);

const formRef = ref(null);
const isEdit = computed(() => Boolean(props.group && props.group.id));

const form = reactive({
  id: null,
  code: "",
  title: "",
  menuId: null,
  module: "",
  sort: 0,
  status: 1,
  description: "",
});

const rules = {
  title: [{ required: true, message: "请输入权限组名称", trigger: "blur" }],
  code: [{ required: true, message: "请输入权限组编码", trigger: "blur" }],
  menuId: [{ required: true, message: "请选择所属菜单", trigger: "change" }],
  module: [{ required: true, message: "业务模块不能为空", trigger: "change" }],
};

const handleOpen = () => {
  const group = props.group || {};
  form.id = group.id || null;
  form.code = group.code || "";
  form.title = group.title || "";
  form.menuId = group.menuId || null;
  form.module = group.module || "";
  form.sort = group.sort || 0;
  form.status = group.status === 0 ? 0 : 1;
  form.description = group.description || "";
};

const handleMenuChange = (menuId) => {
  const menu = props.menuOptions.find((item) => item.id === menuId);
  form.module = (menu && menu.businessModule) || "";
};

const handleVisibleChange = (value) => {
  emit("update:visible", value);
};

const handleSubmit = async () => {
  if (!formRef.value) {
    return;
  }
  const valid = await formRef.value.validate().catch(() => false);
  if (!valid) {
    return;
  }
  emit("submit", {
    id: form.id,
    code: form.code.trim(),
    title: form.title.trim(),
    menuId: form.menuId,
    module: form.module,
    sort: form.sort,
    status: form.status,
    description: form.description,
  });
};
</script>

<style scoped>
.full-width {
  width: 100%;
}

.option-code {
  float: right;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}
</style>
