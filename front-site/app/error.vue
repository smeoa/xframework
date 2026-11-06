<script setup lang="ts">
/** 全局错误页：404 与运行时异常的统一出口 */
import type { NuxtError } from '#app'

const props = defineProps<{ error: NuxtError }>()

const isNotFound = computed(() => props.error?.statusCode === 404)

function retry() {
  clearError({ redirect: useRoute().fullPath })
}
</script>

<template>
  <NuxtLayout>
    <div class="error-page">
      <h1 class="error-page__title">
        {{ isNotFound ? 'Page not found' : 'Something went wrong' }}
      </h1>
      <p class="error-page__lead">
        {{ isNotFound ? 'The page you requested does not exist.' : 'Please try again.' }}
      </p>
      <div class="error-page__actions">
        <button type="button" class="btn" @click="retry">Try again</button>
        <NuxtLink to="/" class="btn">Back to homepage</NuxtLink>
      </div>
    </div>
  </NuxtLayout>
</template>

<style scoped>
.error-page {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-block: 48px;
}

.error-page__actions {
  display: flex;
  gap: 8px;
}

.btn {
  padding: 8px 16px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #fff;
  color: #1f2937;
  text-decoration: none;
  cursor: pointer;
}
</style>
