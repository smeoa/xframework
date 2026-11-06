<template>
  <!-- 编辑弹窗 -->
  <el-dialog
    header="用户编辑"
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
          <el-form-item label="用户名" prop="username" class="form-item w1">
            <el-input
              v-model="form.username"
              placeholder="请输入用户名"
              :disabled="!!form.id"
            />
          </el-form-item>
          <el-form-item
            label="密码"
            prop="password"
            v-if="!form.id"
            class="form-item w1"
          >
            <el-input
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              show-password
            />
          </el-form-item>
          <el-form-item label="真实姓名" prop="name" class="form-item w1">
            <el-input v-model="form.name" placeholder="请输入真实姓名" />
          </el-form-item>
          <el-form-item label="手机号" prop="phone" class="form-item w1">
            <el-input v-model="form.phone" placeholder="请输入手机号" />
          </el-form-item>
        </div>
        <div class="form-row">
          <el-form-item label="邮箱" prop="email" class="form-item w1">
            <el-input v-model="form.email" placeholder="请输入邮箱" />
          </el-form-item>
          <el-form-item label="部门" prop="deptId" class="form-item w1">
            <el-tree-select
              v-model="form.deptId"
              :data="deptTree"
              node-key="id"
              check-strictly
              placeholder="请选择部门"
              :props="{
                children: 'children',
                label: 'name',
              }"
            />
          </el-form-item>
          <el-form-item label="头像" prop="avatar" class="form-item w1">
            <el-input v-model="form.avatar" placeholder="请输入头像URL" />
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
          <el-form-item label="图片" prop="images" class="form-item w2">
            <ImageUploader
              v-model="form.images"
              :sortable="false"
              :selectable="false"
              :show-title="false"
              :paste-enabled="true"
              upload-api="/admin/attachment/upload-attachment"
              module="admin_user"
              tip="支持拖拽或粘贴上传图片"
              @change="handleImageChange"
            />
          </el-form-item>
          <el-form-item label="附件" prop="attachments" class="form-item w2">
            <FileUploader
              v-model="form.attachments"
              :max-count="20"
              :max-size="50"
              module="admin_user"
              @change="handleAttachmentChange"
            />
          </el-form-item>
        </div>
        <div class="form-row" v-if="form.id">
          <el-form-item
            label="最后登录时间"
            prop="lastLoginTime"
            class="form-item"
          >
            <el-input
              v-model="form.lastLoginTime"
              placeholder="最后登录时间"
              disabled
            />
          </el-form-item>
          <el-form-item label="最后登录IP" prop="lastLoginIp" class="form-item">
            <el-input
              v-model="form.lastLoginIp"
              placeholder="最后登录IP"
              disabled
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
          <el-form-item label="用户名" prop="username" class="form-item w1">
            <el-input
              v-model="form.username"
              placeholder="请输入用户名"
              :disabled="!!form.id"
            />
          </el-form-item>
          <el-form-item
            label="密码"
            prop="password"
            v-if="!form.id"
            class="form-item w1"
          >
            <el-input
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              show-password
            />
          </el-form-item>
          <el-form-item label="真实姓名" prop="name" class="form-item w1">
            <el-input v-model="form.name" placeholder="请输入真实姓名" />
          </el-form-item>
          <el-form-item label="手机号" prop="phone" class="form-item w1">
            <el-input v-model="form.phone" placeholder="请输入手机号" />
          </el-form-item>
        </div>
        <div class="form-row">
          <el-form-item label="邮箱" prop="email" class="form-item w1">
            <el-input v-model="form.email" placeholder="请输入邮箱" />
          </el-form-item>
          <el-form-item label="部门" prop="deptId" class="form-item w1">
            <el-tree-select
              v-model="form.deptId"
              :data="deptTree"
              node-key="id"
              placeholder="请选择部门"
              :props="{
                children: 'children',
                label: 'name',
              }"
            />
          </el-form-item>
          <el-form-item label="头像" prop="avatar" class="form-item w1">
            <el-input v-model="form.avatar" placeholder="请输入头像URL" />
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
          <el-form-item label="图片" prop="images" class="form-item w2">
            <ImageUploader
              v-model="form.images"
              :max-count="9"
              :selectable="false"
              :show-title="false"
              :paste-enabled="true"
              upload-api="/admin/attachment/upload-attachment"
              module="admin_user"
              tip=""
              @change="handleImageChange"
            />
          </el-form-item>
          <el-form-item label="附件" prop="attachments" class="form-item w2">
            <FileUploader
              v-model="form.attachments"
              :max-count="20"
              :max-size="50"
              module="admin_user"
              @change="handleAttachmentChange"
            />
          </el-form-item>
        </div>
        <div class="form-row" v-if="form.id">
          <el-form-item
            label="最后登录时间"
            prop="lastLoginTime"
            class="form-item"
          >
            <el-input
              v-model="form.lastLoginTime"
              placeholder="最后登录时间"
              disabled
            />
          </el-form-item>
          <el-form-item label="最后登录IP" prop="lastLoginIp" class="form-item">
            <el-input
              v-model="form.lastLoginIp"
              placeholder="最后登录IP"
              disabled
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

  <!-- 通用文件预览组件 -->
  <FilePreview
    v-model:visible="filePreviewVisible"
    :url="previewFileUrl"
    :filename="previewFileName"
    :filesize="previewFileSize"
    :title="previewFileName"
    :show-info="true"
  />
</template>

<script setup>
import { ref, computed, watch } from "vue";
import { FullScreen, Close } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import FilePreview from "@/components/FilePreview.vue";
import ImageUploader from "@/components/ImageUploader.vue";
import FileUploader from "@/components/FileUploader.vue";

const { visible, displayMode, user, deptTree } = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  displayMode: {
    type: String,
    default: "dialog",
    validator: (value) => ["dialog", "drawer"].includes(value),
  },
  user: {
    type: Object,
    default: () => ({
      id: null,
      username: "",
      password: "",
      name: "",
      phone: "",
      email: "",
      deptId: null,
      deptName: "",
      avatar: "",
      images: [],
      attachments: [],
      status: 1,
      lastLoginTime: null,
      lastLoginIp: null,
      createdTime: null,
      updatedTime: null,
    }),
  },
  deptTree: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(["update:visible", "update:displayMode", "submit"]);

const dialogVisible = computed({
  get: () => visible && displayMode === "dialog",
  set: (value) => {
    if (!value && displayMode === "dialog") {
      emit("update:visible", false);
    }
  },
});

const drawerVisible = computed({
  get: () => visible && displayMode === "drawer",
  set: (value) => {
    if (!value && displayMode === "drawer") {
      emit("update:visible", false);
    }
  },
});

const dialogTitle = computed(() => (user.id ? "编辑用户" : "新增用户"));

const form = ref({
  ...user,
  images: user.images || [],
  attachments: user.attachments || [],
});
const formRef = ref(null);
const fullscreen = ref(false);
const filePreviewVisible = ref(false);
const previewFileUrl = ref("");
const previewFileName = ref("");
const previewFileSize = ref(0);

watch(
  () => user,
  (newUser) => {
    form.value = { ...newUser };
    if (newUser.images) {
      form.value.images = Array.isArray(newUser.images)
        ? [...newUser.images]
        : [];
    } else {
      form.value.images = [];
    }
    if (newUser.attachments) {
      form.value.attachments = Array.isArray(newUser.attachments)
        ? [...newUser.attachments]
        : [];
    } else {
      form.value.attachments = [];
    }
  },
  { deep: true },
);

// 处理图片变化
const handleImageChange = (images) => {
  form.value.images = images || [];
};

// 处理附件变化
const handleAttachmentChange = (files) => {
  form.value.attachments = files || [];
};

const rules = {
  username: [
    { required: true, message: "请输入用户名", trigger: "blur" },
    { min: 3, max: 50, message: "长度在 3 到 50 个字符", trigger: "blur" },
  ],
  password: [
    { required: true, message: "请输入密码", trigger: "blur" },
    { min: 6, message: "密码长度不能少于 6 个字符", trigger: "blur" },
  ],
  name: [{ required: true, message: "请输入真实姓名", trigger: "blur" }],
  email: [{ type: "email", message: "请输入正确的邮箱地址", trigger: "blur" }],
  deptId: [{ required: true, message: "请选择部门", trigger: "change" }],
};

// 切换全屏
const toggleFullscreen = () => {
  fullscreen.value = !fullscreen.value;
};

// 切换显示方式（弹窗/抽屉）
const switchDisplayMode = (mode) => {
  if (!visible) {
    emit("update:visible", true);
  }
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
</style>
