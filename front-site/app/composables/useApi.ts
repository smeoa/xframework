/**
 * 前台统一请求入口（POST only）
 * - 接口基址由 NUXT_PUBLIC_API_BASE 注入，不暴露后端密钥
 * - 自动完成 camelCase ↔ snake_case 转换，与后台 request.js 约定一致
 */
export function toSnakeCase(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(toSnakeCase)
  if (value instanceof Date) return value.toISOString()
  if (value && typeof value === 'object' && value.constructor === Object) {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>).map(([key, child]) => [
        key.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`),
        toSnakeCase(child)
      ])
    )
  }
  return value
}

export function toCamelCase(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(toCamelCase)
  if (value && typeof value === 'object' && value.constructor === Object) {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>).map(([key, child]) => [
        key.replace(/_([a-z0-9])/g, (_, letter: string) => letter.toUpperCase()),
        toCamelCase(child)
      ])
    )
  }
  return value
}

/** 统一错误结构：调用方只需读取 message，不直接暴露后端细节 */
export interface ApiError {
  message: string
  statusCode: number
  code?: string
}

export function normalizeApiError(error: unknown): ApiError {
  const candidate = error as {
    data?: { message?: string; code?: string }
    statusCode?: number
    status?: number
    message?: string
  }
  return {
    message: candidate?.data?.message || candidate?.message || 'Request failed. Please retry.',
    statusCode: candidate?.statusCode ?? candidate?.status ?? 0,
    code: candidate?.data?.code
  }
}

export function useApi<T>(path: string, body: Record<string, unknown> = {}): Promise<T> {
  const config = useRuntimeConfig()
  const base = config.public.apiBase as string

  if (!base) {
    throw new Error('[useApi] 缺少 NUXT_PUBLIC_API_BASE：未配置接口基址，禁止回退到假数据请求。')
  }

  return $fetch<T>(path, {
    baseURL: base,
    method: 'POST',
    body: toSnakeCase(body) as Record<string, unknown>
  }).then((response) => toCamelCase(response) as T)
}
