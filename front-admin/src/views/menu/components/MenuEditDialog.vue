<template>
  <el-dialog
    header="菜单编辑"
    v-model="dialogVisible"
    :title="dialogTitle"
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
          <el-icon><DArrowRight /></el-icon>
        </el-button>
        <el-button @click="handleCancel" title="关闭" text>
          <el-icon>
            <Close />
          </el-icon>
        </el-button>
      </div>
    </template>
    <el-scrollbar class="drawer-body">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="110px" class="form-layout">
        <div class="form-row">
          <el-form-item label="菜单名称" prop="name" class="form-item" required>
            <el-input v-model="form.name" placeholder="请输入菜单名称" />
          </el-form-item>
          <el-form-item label="类型" prop="type" class="form-item" required>
            <el-select v-model="form.type" placeholder="请选择菜单类型">
              <el-option label="目录" :value="1" />
              <el-option label="菜单" :value="2" />
            </el-select>
          </el-form-item>
          <el-form-item label="路径" prop="path" class="form-item">
            <el-input v-model="form.path" placeholder="请输入菜单路径" />
          </el-form-item>
          <el-form-item label="图标" prop="icon" class="form-item">
            <el-input v-model="form.icon" placeholder="请输入图标名称" />
          </el-form-item>
        </div>
        <div class="form-row">
          <el-form-item label="上级菜单" prop="pid" class="form-item w1">
            <el-tree-select
              v-model="form.pid"
              :data="menuTree"
              node-key="id"
              check-strictly
              placeholder="请选择上级菜单"
              :props="{ children: 'children', label: 'name' }"
            />
          </el-form-item>
          <el-form-item label="状态" prop="status" class="form-item w1">
            <el-switch
              v-model="form.status"
              :active-value="1"
              :inactive-value="0"
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
      <el-form :model="form" :rules="rules" ref="formRef" label-width="110px" class="form-layout">
        <div class="form-row">
          <el-form-item label="菜单名称" prop="name" class="form-item" required>
            <el-input v-model="form.name" placeholder="请输入菜单名称" />
          </el-form-item>
          <el-form-item label="类型" prop="type" class="form-item" required>
            <el-select v-model="form.type" placeholder="请选择菜单类型">
              <el-option label="目录" :value="1" />
              <el-option label="菜单" :value="2" />
            </el-select>
          </el-form-item>
          <el-form-item label="路径" prop="path" class="form-item">
            <el-input v-model="form.path" placeholder="请输入菜单路径" />
          </el-form-item>
          <el-form-item label="图标" prop="icon" class="form-item">
            <el-input v-model="form.icon" placeholder="请输入图标名称" />
          </el-form-item>
        </div>
        <div class="form-row">
          <el-form-item label="上级菜单" prop="pid" class="form-item w1">
            <el-tree-select
              v-model="form.pid"
              :data="menuTree"
              node-key="id"
              check-strictly
              placeholder="请选择上级菜单"
              :props="{ children: 'children', label: 'name' }"
            />
          </el-form-item>
          <el-form-item label="状态" prop="status" class="form-item w1">
            <el-switch
              v-model="form.status"
              :active-value="1"
              :inactive-value="0"
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
import { ref, computed, watch, onMounted } from "vue";
import { FullScreen, Close, DArrowRight } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import request from "@/utils/request";

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
  menu: {
    type: Object,
    default: () => ({
      id: null,
      name: "",
      path: "",
      icon: "",
      sort: 0,
      type: 1,
      status: 1,
      pid: null,
    }),
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

const dialogTitle = computed(() => (props.menu.id ? "编辑菜单" : "新增菜单"));

const form = ref({ ...props.menu });
const formRef = ref(null);
const fullscreen = ref(false);
const menuTree = ref([]);

watch(
  () => props.menu,
  (newMenu) => {
    form.value = { ...newMenu };
    if (form.value.type === undefined) form.value.type = 1;
    if (form.value.status === undefined) form.value.status = 1;
    if (form.value.sort === undefined) form.value.sort = 0;
  },
  { deep: true },
);

const fetchMenuTree = async () => {
  try {
    const res = await request.post("/admin/menu/get-menu-tree");
    if (res.code === 200) {
      menuTree.value = res.data || [];
    }
  } catch (error) {
    console.error("获取菜单树失败:", error);
  }
};

onMounted(() => {
  fetchMenuTree();
});

const rules = {
  name: [{ required: true, message: "请输入菜单名称", trigger: "blur" }],
  type: [{ required: true, message: "请选择菜单类型", trigger: "change" }],
};

const toggleFullscreen = () => {
  fullscreen.value = !fullscreen.value;
};

const switchDisplayMode = (mode) => {
  emit("update:displayMode", mode);
};

const handleCancel = () => {
  emit("update:visible", false);
};

const handleSubmit = async () => {
  try {
    await formRef.value?.validate();
    const submitData = {
      ...form.value,
      status: form.value.status ? 1 : 0,
    };
    emit("submit", submitData);
    emit("update:visible", false);
  } catch (error) {
    if (error !== false) {
      console.error(error);
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
  padding: 8px;
}

.form-row {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.form-item {
  flex: 1;
}

.w1 {
  width: calc(50% - 8px);
}
</style>