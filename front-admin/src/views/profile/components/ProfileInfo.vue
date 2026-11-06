<template>
  <el-card shadow="hover" class="info-card" :class="{ 'is-editing': editMode }">
    <template #header>
      <div class="card-header">
        <span>基本信息</span>
        <el-button type="primary" @click="editMode = true">
          <el-icon>
            <Edit />
          </el-icon>
          编辑
        </el-button>
      </div>
    </template>
    <el-scrollbar class="card-scrollbar">
      <div v-if="!editMode" class="info-content">
        <div class="info-item">
          <span class="label">姓名：</span>
          <span class="value">{{ userInfo.name }}</span>
        </div>
        <div class="info-item">
          <span class="label">手机号：</span>
          <span class="value">{{ userInfo.phone }}</span>
        </div>
        <div class="info-item">
          <span class="label">邮箱：</span>
          <span class="value">{{ userInfo.email }}</span>
        </div>
        <div class="info-item">
          <span class="label">职位：</span>
          <span class="value">{{ userInfo.position || "未设置" }}</span>
        </div>
        <div class="info-item">
          <span class="label">所属部门：</span>
          <span class="value">{{ userInfo.department || "未设置" }}</span>
        </div>
        <div class="info-item">
          <span class="label">入职时间：</span>
          <span class="value">{{ userInfo.joinDate || "未设置" }}</span>
        </div>
      </div>

      <el-form v-else :model="form" label-width="100px" class="edit-form">
        <el-form-item label="姓名" required>
          <el-input v-model="form.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="手机号" required>
          <el-input v-model="form.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="邮箱" required>
          <el-input v-model="form.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="职位">
          <el-input v-model="form.position" placeholder="请输入职位" />
        </el-form-item>
        <el-form-item label="头像">
          <el-upload
            class="avatar-uploader"
            action="#"
            :show-file-list="false"
            :auto-upload="false"
            :on-change="handleAvatarChange"
          >
            <img v-if="form.avatar" :src="form.avatar" class="avatar" />
            <el-icon v-else class="avatar-uploader-icon">
              <Plus />
            </el-icon>
          </el-upload>
        </el-form-item>
      </el-form>
    </el-scrollbar>

    <template #footer>
      <div class="card-footer">
        <el-button type="primary" @click="handleSave">保存</el-button>
        <el-button @click="handleCancel">取消</el-button>
      </div>
    </template>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { Edit, Plus } from "@element-plus/icons-vue";
import request from "@/utils/request";

const editMode = ref(false);
const userInfo = ref({
  name: "张三",
  phone: "13800138000",
  email: "zhangsan@example.com",
  position: "产品经理",
  department: "产品部",
  joinDate: "2026-01-01",
  avatar: "",
});

const form = ref({});

onMounted(() => {
  loadUserInfo();
});

const loadUserInfo = async () => {
  try {
    const response = await request.post("/admin/profile/get-profile");
    if (response.code === 200) {
      userInfo.value = response.data;
      form.value = { ...response.data };
    }
  } catch (error) {
    console.error("获取个人资料失败:", error);
  }
};

const handleAvatarChange = (file) => {
  // 处理头像上传
  form.value.avatar = URL.createObjectURL(file.raw);
};

const handleSave = async () => {
  try {
    const response = await request.post("/admin/profile/update-profile", {
      data: form.value,
    });
    if (response.code === 200) {
      userInfo.value = { ...form.value };
      editMode.value = false;
      ElMessage.success("保存成功");
    }
  } catch (error) {
    console.error("保存个人资料失败:", error);
    ElMessage.error("保存失败，请重试");
  }
};

const handleCancel = () => {
  form.value = { ...userInfo.value };
  editMode.value = false;
};
</script>

<style scoped>
.profile-info {
  padding: 20px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 20px;
  color: var(--td-text-color-primary);
}

/* 卡片高度自适应父容器：纵向 flex 撑满，头部固定、主体滚动 */
.info-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  margin-bottom: 0;
}

/* body 作为滚动区域外壳：占满剩余高度，内边距下移到滚动内容上，
   避免滚动条宽度占用内容盒（滚动条由 el-scrollbar 自绘） */
.info-card :deep(.el-card__body) {
  flex: 1;
  min-height: 0;
  padding: 0;
  overflow: hidden;
}

/* 滚动容器铺满 body，滚动条贴卡片右缘 */
.card-scrollbar {
  height: 100%;
}

.card-scrollbar :deep(.el-scrollbar__view) {
  padding: var(--td-comp-paddingTB-l) 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 保存/取消仅在编辑态显示，非编辑态隐藏 footer，避免出现空操作栏 */
.info-card:not(.is-editing) :deep(.el-card__footer) {
  display: none;
}

.card-footer {
  display: flex;
  gap: 8px;
}

.info-content {
  padding: 20px;
}

.info-item {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
}

.label {
  width: 100px;
  font-weight: 500;
  color: var(--td-text-color-secondary);
}

.value {
  flex: 1;
  color: var(--td-text-color-primary);
}

.edit-form {
  padding: 20px;
}

.avatar-uploader {
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  width: 100px;
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-uploader:hover {
  border-color: var(--brand-color);
}

.avatar-uploader-icon {
  font-size: 28px;
  color: var(--td-text-color-secondary);
}

.avatar {
  width: 100%;
  height: 100%;
  display: block;
}
</style>
