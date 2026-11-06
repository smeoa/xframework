<script setup lang="ts">
/** 全局布局壳：页头 → 主内容 → 页脚，页面可覆盖 header / footer 插槽 */
import { siteConfig } from '~/utils/siteConfig'
</script>

<template>
  <div class="site-shell">
    <header class="site-header">
      <slot name="header">
        <NuxtLink to="/" class="site-logo">{{ siteConfig.name }}</NuxtLink>
      </slot>
    </header>

    <main id="main-content" class="site-main">
      <slot />
    </main>

    <footer class="site-footer">
      <slot name="footer">
        <p>© {{ new Date().getFullYear() }} {{ siteConfig.name }}</p>
      </slot>
    </footer>
  </div>
</template>

<style scoped>
.site-shell {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.site-header {
  padding: 16px 24px;
  border-bottom: 1px solid #e5e7eb;
}

.site-logo {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  text-decoration: none;
}

.site-main {
  flex: 1;
  padding: 24px;
}

.site-footer {
  padding: 16px 24px;
  border-top: 1px solid #e5e7eb;
  color: #6b7280;
  font-size: 13px;
}
</style>
