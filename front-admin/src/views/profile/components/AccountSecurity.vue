<template>
  <!-- 修改密码 -->
  <el-card shadow="hover" class="security-card">
    <template #header>
      <div class="card-header">
        <span>修改密码</span>
      </div>
    </template>

    <el-form :model="passwordForm" label-width="100px" class="password-form">
      <el-form-item label="原密码" required>
        <el-input
          v-model="passwordForm.oldPassword"
          type="password"
          placeholder="请输入原密码"
        />
      </el-form-item>
      <el-form-item label="新密码" required>
        <el-input
          v-model="passwordForm.newPassword"
          type="password"
          placeholder="请输入新密码"
        />
        <div class="password-tip">密码长度至少8位，包含字母和数字</div>
      </el-form-item>
      <el-form-item label="确认新密码" required>
        <el-input
          v-model="passwordForm.confirmPassword"
          type="password"
          placeholder="请确认新密码"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="card-footer">
        <el-button type="primary" @click="handleChangePassword"
          >修改密码</el-button
        >
      </div>
    </template>
  </el-card>
</template>

<script setup>
import { ref } from "vue";
import request from "@/utils/request";

const passwordForm = ref({
  oldPassword: "",
  newPassword: "",
  confirmPassword: "",
});

const handleChangePassword = async () => {
  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    ElMessage.error("两次输入的密码不一致");
    return;
  }

  if (passwordForm.value.newPassword.length < 8) {
    ElMessage.error("密码长度至少8位");
    return;
  }

  try {
    const response = await request.post("/admin/profile/change-password", {
      data: passwordForm.value,
    });
    if (response.code === 200) {
      ElMessage.success("密码修改成功，请重新登录");
      // 清空表单
      passwordForm.value = {
        oldPassword: "",
        newPassword: "",
        confirmPassword: "",
      };
    }
  } catch (error) {
    console.error("修改密码失败:", error);
    ElMessage.error("修改密码失败，请重试");
  }
};
</script>

<style scoped>
.account-security {
  padding: 20px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 20px;
  color: var(--td-text-color-primary);
}

/* 仅剩「修改密码」一张卡片，按内容高度展示，不参与压缩 */
.security-card {
  flex: 0 0 auto;
  margin-bottom: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-footer {
  display: flex;
  gap: 8px;
}

.password-form {
  padding: 20px;
}

.password-tip {
  font-size: 12px;
  color: var(--td-text-color-placeholder);
  margin-top: 5px;
}
</style>
