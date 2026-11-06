<template>
  <!-- 编辑弹窗 -->
  <el-dialog
    header="角色编辑"
    v-model="dialogVisible"
    :title="dialogTitle"
    :width="fullscreen ? '100%' : '1000px'"
    :fullscreen="fullscreen"
    :show-close="false"
    class="label-top edit-dialog"
  >
    <template #header>
      <span class="dialog-title">{{ dialogTitle }}</span>
      <div class="dialog-header-actions">
        <el-button @click="toggleFullscreen" title="全屏" text>
          <el-icon>
            <FullScreen />
          </el-icon>
        </el-button>
        <el-button @click="switchDisplayMode('drawer')" title="切换为抽屉" text>
          <i class="iconfont x-youchouti"></i>
        </el-button>
        <el-button @click="handleCancel" title="关闭" text>
          <el-icon>
            <Close />
          </el-icon>
        </el-button>
      </div>
    </template>
    <el-scrollbar class="dialog-content">
      <el-form :model="form" :rules="rules" ref="formRef" class="form-layout">
        <div class="form-row">
          <el-form-item label="角色名称" prop="name" class="form-item w1">
            <el-input v-model="form.name" placeholder="请输入角色名称" />
          </el-form-item>
          <el-form-item label="角色编码" prop="code" class="form-item w1">
            <el-input v-model="form.code" placeholder="请输入角色编码" />
          </el-form-item>
          <el-form-item label="状态" prop="status" class="form-item w1">
            <el-switch
              v-model="form.status"
              :active-value="1"
              :inactive-value="0"
            />
          </el-form-item>
        </div>
        <div class="form-row">
          <el-form-item label="角色描述" class="form-item w2">
            <el-input
              v-model="form.description"
              type="textarea"
              placeholder="请输入角色描述"
              :rows="3"
            />
          </el-form-item>
        </div>
      </el-form>
    </el-scrollbar>
    <template #footer>
      <el-button type="primary" @click="handleSubmit">确定</el-button>
      <el-button @click="handleCancel">取消</el-button>
    </template>
  </el-dialog>

  <!-- 编辑抽屉 -->
  <el-drawer
    v-model="drawerVisible"
    :title="dialogTitle"
    direction="rtl"
    :size="fullscreen ? '100%' : '1000px'"
    :show-close="false"
    class="label-top edit-drawer"
  >
    <template #header>
      <span class="dialog-title">{{ dialogTitle }}</span>
      <div class="dialog-header-actions">
        <el-button @click="toggleFullscreen" title="全屏" text>
          <el-icon>
            <FullScreen />
          </el-icon>
        </el-button>
        <el-button @click="switchDisplayMode('dialog')" title="切换为弹窗" text>
          <i class="iconfont x-tanchuang"></i>
        </el-button>
        <el-button @click="handleCancel" title="关闭" text>
          <el-icon>
            <Close />
          </el-icon>
        </el-button>
      </div>
    </template>
    <el-scrollbar class="drawer-body">
      <el-form
        :model="form"
        label-width="110px"
        :rules="rules"
        ref="formRef"
        class="form-layout"
      >
        <div class="form-row">
          <el-form-item label="角色名称" prop="name" class="form-item w1">
            <el-input v-model="form.name" placeholder="请输入角色名称" />
          </el-form-item>
          <el-form-item label="角色编码" prop="code" class="form-item w1">
            <el-input v-model="form.code" placeholder="请输入角色编码" />
          </el-form-item>
          <el-form-item label="状态" prop="status" class="form-item w1">
            <el-switch
              v-model="form.status"
              :active-value="1"
              :inactive-value="0"
            />
          </el-form-item>
        </div>
        <div class="form-row">
          <el-form-item label="角色描述" class="form-item w2">
            <el-input
              v-model="form.description"
              type="textarea"
              placeholder="请输入角色描述"
              :rows="3"
            />
          </el-form-item>
        </div>
      </el-form>
    </el-scrollbar>
    <template #footer>
      <el-button type="primary" @click="handleSubmit">确定</el-button>
      <el-button @click="handleCancel">取消</el-button>
    </template>
  </el-drawer>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import { FullScreen, Close } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  displayMode: {
    type: String,
    default: "dialog",
    validator: (value) => ["dialog", "drawer"].includes(value),
  },
  role: {
    type: Object,
    default: () => ({
      id: null,
      name: "",
      code: "",
      pid: null,
      description: "",
      status: 1,
    }),
  },
  roleTree: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(["update:visible", "update:displayMode", "submit"]);

const dialogVisible = computed({
  get: () => props.visible && props.displayMode === "dialog",
  set: (value) => {
    if (!value && props.displayMode === "dialog") {
      emit("update:visible", false);
    }
  },
});

const drawerVisible = computed({
  get: () => props.visible && props.displayMode === "drawer",
  set: (value) => {
    if (!value && props.displayMode === "drawer") {
      emit("update:visible", false);
    }
  },
});

const formRef = ref(null);
const form = ref({
  id: null,
  name: "",
  code: "",
  pid: null,
  description: "",
  status: 1,
});

const dialogTitle = computed(() => (form.value.id ? "编辑角色" : "新增角色"));
const fullscreen = ref(false);

const rules = {
  name: [
    { required: true, message: "请输入角色名称", trigger: "blur" },
    { min: 2, max: 50, message: "长度在 2 到 50 个字符", trigger: "blur" },
  ],
  code: [
    { required: true, message: "请输入角色编码", trigger: "blur" },
    { pattern: /^[a-zA-Z0-9_]+$/, message: "只能包含字母、数字和下划线", trigger: "blur" },
  ],
};

watch(
  () => props.role,
  (newRole) => {
    if (newRole) {
      form.value = {
        ...newRole,
      };
    }
  },
  { deep: true, immediate: true }
);

const resetForm = () => {
  form.value = {
    id: null,
    name: "",
    code: "",
    pid: null,
    description: "",
    status: 1,
  };
  if (formRef.value) {
    formRef.value.resetFields();
  }
};

// 切换全屏
const toggleFullscreen = () => {
  fullscreen.value = !fullscreen.value;
};

// 切换显示方式（弹窗/抽屉）
const switchDisplayMode = (mode) => {
  if (!props.visible) {
    emit("update:visible", true);
  }
  emit("update:displayMode", mode);
};

const handleCancel = () => {
  emit("update:visible", false);
};

const handleSubmit = async () => {
  if (!formRef.value) return;
  
  try {
    await formRef.value.validate();
    const submitData = {
      ...form.value,
      status: form.value.status ? 1 : 0,
    };
    emit("submit", submitData);
    emit("update:visible", false);
  } catch (error) {
    if (error !== false) {
      console.error("表单验证失败:", error);
    }
  }
};
</script>

<style scoped>
.dialog-title {
  font-size: 16px;
  line-height: 24px;
}

.dialog-header-actions {
  gap: 8px;
  float: right;
}

.dialog-body {
  height: calc(100vh - 200px);
}

.drawer-body {
  height: 100%;
}

.form-layout {
  padding: 20px 0;
}

.form-row {
  display: flex;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.form-item {
  flex: 1;
  min-width: 200px;
  margin-right: 20px;
}

.form-item.w1 {
  flex: 1;
}

.form-item.w2 {
  flex: 4;
}

.form-item:last-child {
  margin-right: 0;
}

@media (max-width: 768px) {
  .form-row {
    flex-direction: column;
  }
  
  .form-item {
    margin-right: 0;
    margin-bottom: 16px;
  }
  
  .form-item:last-child {
    margin-bottom: 0;
  }
}
</style>
