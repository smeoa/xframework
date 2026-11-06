<template>
  <div class="dashboard">
    <el-card class="welcome-card">
      <h1 class="welcome-title">欢迎使用 xf 管理后台</h1>
      <p class="welcome-subtitle">
        这是一个基于框架 + Demo 模块的快速开发模板。从左侧菜单进入「Demo 示例」查看完整增删改查样板。
      </p>
      <el-button type="primary" @click="$router.push('/demo')">进入 Demo 示例</el-button>
    </el-card>
  </div>
</template>

<script setup>
</script>

<style scoped>
.dashboard {
  padding: 16px;
}

.welcome-card {
  max-width: 720px;
}

.welcome-title {
  margin: 0 0 8px;
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
}

.welcome-subtitle {
  margin: 0 0 16px;
  font-size: 13px;
  color: #6b7280;
}
</style>
