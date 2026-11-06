<template>
  <div class="login-container">
    <div class="login-bg" aria-hidden="true">
      <span class="login-bg__glow"></span>
      <span class="login-bg__grid"></span>
    </div>

    <section class="login-card">
      <header class="login-header">
        <div class="login-brand">
          <span class="login-brand__mark">
            <svg
              class="login-brand__logo"
              viewBox="0 0 48 48"
              role="img"
              aria-label="xf"
            >
              <path
                d="M24 8 C25.2 10.6 25.6 12.4 25.4 14.2 C34 14.4 41.4 16.6 47 20 C41 20.6 33.6 20.6 26.2 18.6 C26 22 25.6 25.4 25 28.6 C27.2 33.6 29.2 39.4 30.6 45.6 C28.6 40.6 26.4 36.4 24 32.8 C21.6 36.4 19.4 40.6 17.4 45.6 C18.8 39.4 20.8 33.6 23 28.6 C22.4 25.4 22 22 21.8 18.6 C14.4 20.6 7 20.6 1 20 C6.6 16.6 14 14.4 22.6 14.2 C22.4 12.4 22.8 10.6 24 8 Z"
                fill="currentColor"
              />
            </svg>
          </span>
        </div>
        <h1 class="login-title">xf</h1>
        <p class="login-subtitle">官网内容 · 客户线索 · 图片素材管理后台</p>
      </header>

      <el-form class="login-form" :model="form" @submit.prevent="handleLogin">
        <el-input
          v-model="form.username"
          class="login-input"
          size="large"
          placeholder="请输入用户名"
          :prefix-icon="User"
          clearable
          @keyup.enter="handleLogin"
        />
        <el-input
          v-model="form.password"
          class="login-input"
          size="large"
          type="password"
          placeholder="请输入密码"
          :prefix-icon="Lock"
          show-password
          @keyup.enter="handleLogin"
        />
        <el-button
          class="login-submit"
          type="primary"
          size="large"
          :loading="loading"
          @click="handleLogin"
          >登录</el-button
        >
      </el-form>

      <p class="login-tip">默认账号：<b>admin</b> / <b>admin123</b></p>
    </section>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { User, Lock } from "@element-plus/icons-vue";
import request from "@/utils/request";
import { setLoginData } from "@/utils/permission";
import { resolveHomePath } from "@/utils/homePath";

const router = useRouter();
const loading = ref(false);
const form = ref({
  username: "",
  password: "",
});

const handleLogin = async () => {
  if (!form.value.username || !form.value.password) {
    ElMessage.warning("请输入用户名和密码");
    return;
  }
  loading.value = true;
  try {
    const res = await request.post("/admin/auth/login", {
      username: form.value.username,
      password: form.value.password,
    });
    if (res && res.code === 200) {
      setLoginData(res.data);
      ElMessage.success("登录成功");
      // 登录后进入当前账号第一个可访问菜单，而非固定的 /dashboard
      const home = await resolveHomePath(router);
      router.push(home || "/dashboard");
    } else {
      ElMessage.error((res && res.message) || "用户名或密码错误");
    }
  } catch (error) {
    ElMessage.error(error.message || "用户名或密码错误");
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-container {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100vh;
  overflow: hidden;
  padding: 24px;
  background: #f7f8fa;
  font-family: var(--td-font-family);
}

/* ---------- 背景层 ---------- */
.login-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.login-bg__glow {
  position: absolute;
  top: -22%;
  left: 50%;
  width: 720px;
  height: 720px;
  transform: translateX(-50%);
  background: radial-gradient(
    circle,
    rgba(var(--brand-color-rgb), 0.16) 0%,
    rgba(var(--brand-color-rgb), 0) 62%
  );
}

.login-bg__grid {
  position: absolute;
  inset: 0;
  background-image: linear-gradient(
      to right,
      rgba(15, 23, 42, 0.035) 1px,
      transparent 1px
    ),
    linear-gradient(to bottom, rgba(15, 23, 42, 0.035) 1px, transparent 1px);
  background-size: 56px 56px;
  -webkit-mask-image: radial-gradient(
    circle at 50% 42%,
    #000 0%,
    transparent 72%
  );
  mask-image: radial-gradient(circle at 50% 42%, #000 0%, transparent 72%);
}

/* ---------- 卡片 ---------- */
.login-card {
  position: relative;
  z-index: 1;
  width: 380px;
  max-width: 100%;
  padding: 40px 36px 30px;
  background: rgba(255, 255, 255, 0.86);
  -webkit-backdrop-filter: saturate(180%) blur(12px);
  backdrop-filter: saturate(180%) blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.7);
  border-radius: 16px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04),
    0 16px 36px -18px rgba(15, 23, 42, 0.22);
}

/* ---------- 头部 ---------- */
.login-header {
  margin-bottom: 28px;
  text-align: center;
}

.login-brand {
  display: flex;
  justify-content: center;
  margin-bottom: 16px;
}

.login-brand__mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  color: #fff;
  background: linear-gradient(
    140deg,
    var(--brand-color-hover),
    var(--brand-color-active)
  );
  box-shadow: 0 8px 18px -8px rgba(var(--brand-color-rgb), 0.7);
}

.login-brand__logo {
  display: block;
  width: 30px;
  height: 30px;
}

.login-title {
  margin: 0;
  font-size: var(--td-font-size-title-large);
  font-weight: 600;
  color: var(--td-text-color-primary);
  letter-spacing: 0.5px;
}

.login-subtitle {
  margin: 6px 0 0;
  font-size: var(--td-font-size-body-small);
  color: var(--td-text-color-placeholder);
  letter-spacing: 0.5px;
}

/* ---------- 表单 ---------- */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.login-form :deep(.el-input__wrapper) {
  height: 44px;
  border-radius: var(--td-radius-medium);
  background: #fff;
  box-shadow: 0 0 0 1px var(--td-border-level-1-color) inset;
  transition: box-shadow 0.2s ease;
}

.login-form :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--td-border-level-2-color) inset;
}

.login-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--brand-color) inset;
}

.login-form :deep(.el-input__prefix) {
  color: var(--td-text-color-placeholder);
}

.login-submit {
  width: 100%;
  height: 44px;
  margin-top: 6px;
  border-radius: var(--td-radius-medium);
  font-weight: 500;
  letter-spacing: 2px;
  box-shadow: 0 10px 20px -12px rgba(var(--brand-color-rgb), 0.9);
  transition: transform 0.15s ease, box-shadow 0.2s ease;
}

.login-submit:hover {
  transform: translateY(-1px);
  box-shadow: 0 12px 24px -12px rgba(var(--brand-color-rgb), 1);
}

.login-submit:active {
  transform: translateY(0);
}

/* ---------- 底部提示 ---------- */
.login-tip {
  margin: 22px 0 0;
  text-align: center;
  font-size: var(--td-font-size-body-small);
  color: var(--td-text-color-placeholder);
  letter-spacing: 0.5px;
}

.login-tip b {
  color: var(--td-text-color-secondary);
  font-weight: 600;
}

@media (max-width: 480px) {
  .login-card {
    padding: 32px 24px 26px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .login-submit,
  .login-form :deep(.el-input__wrapper) {
    transition: none;
  }

  .login-submit:hover {
    transform: none;
  }
}
</style>
