import { computed, reactive } from 'vue'

// 页面 header 标题后追加的副标题（如当前套用的筛选条件名）
// 由列表页写入，Layout.vue 负责渲染为「标题（副标题）」。
// 按菜单分别保存：页面被 keep-alive 缓存后回到前台时仍显示自己最后一次写入的副标题，
// 不会串用其他页面写入的值（读写均以「当前路由名」为 key，写法对页面保持不变）。
const subtitleMap = reactive({})

// 路由实例由 main.js 注入，避免本模块直接 import router 造成
// router ↔ Layout ↔ pageSubtitle 的循环依赖
let router = null

export const bindRouter = (instance) => {
  router = instance
}

const routeKey = () => {
  const current = router && router.currentRoute && router.currentRoute.value
  return (current && (current.name || current.path)) || ''
}

export const pageSubtitle = computed({
  get: () => subtitleMap[routeKey()] || '',
  set: (text) => {
    subtitleMap[routeKey()] = text || ''
  },
})
