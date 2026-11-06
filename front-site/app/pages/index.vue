<script setup lang="ts">
/**
 * 首页：模板欢迎页 + 前台 API 健康检查调用示例（useApi）
 */
import { siteConfig } from '~/utils/siteConfig'

interface HealthResponse {
  code: number
  data?: { status?: string; database?: boolean; version?: string }
}

const apiStatus = ref<string>('未请求')

async function checkHealth() {
  try {
    const res = await useApi<HealthResponse>('/health')
    apiStatus.value = res.data?.status ?? 'unknown'
  } catch (e) {
    apiStatus.value = `请求失败：${normalizeApiError(e).message}`
  }
}

useSeoMeta({
  title: siteConfig.name,
  description: `${siteConfig.name} front site`
})
</script>

<template>
  <section class="home">
    <h1 class="home__title">欢迎使用 {{ siteConfig.name }}</h1>
    <p class="home__lead">
      这是基于 Nuxt4 + @nuxtjs/seo 的前台模板。下方按钮演示通过 useApi 调用前台 API（POST
      /health）。
    </p>
    <button type="button" class="home__btn" @click="checkHealth">检查前台 API</button>
    <p class="home__status">API 状态：{{ apiStatus }}</p>
  </section>
</template>

<style scoped>
.home {
  max-width: 720px;
}

.home__title {
  margin: 0 0 8px;
  font-size: 24px;
}

.home__lead {
  margin: 0 0 16px;
  color: #6b7280;
}

.home__btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  background: #4f46e5;
  color: #fff;
  cursor: pointer;
}

.home__status {
  margin-top: 12px;
  font-size: 13px;
  color: #374151;
}
</style>
