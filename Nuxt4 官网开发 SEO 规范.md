# Nuxt4 官网开发 SEO 规范

**适用范围：**企业官网、品牌官网、营销官网、落地页；目标为百度 \+ 谷歌友好、稳定收录、Core Web Vitals 达标、团队可维护。

**基础前提：**Nuxt4 \+ `@nuxtjs/seo v6`；默认推荐 **SSG（prerender）优先**，少量动态页用 ISR；后台/会员页走 CSR \+ noindex。

# 一、项目基础配置规范（nuxt\.config\.ts）

## 1\. 必配 site 信息（@nuxtjs/seo 强依赖）

site 配置是 canonical、sitemap、OG URL 的全局依赖，必须与生产域名一致。

```ts
export default defineNuxtConfig({
  modules: ['@nuxtjs/seo'],
  site: {
    url: 'https://www.company.com', // 带 www，末尾不要斜杠
    name: 'XX科技',
    description: 'XX科技专注于...',
    defaultLocale: 'zh-CN'
  }
  // 国际化官网搭配 @nuxtjs/i18n@10，自动生成 hreflang
})
```

禁止本地、测试环境硬写生产域名；用环境变量 `site: { url: process.env.SITE_URL }` 区分。

## 2\. routeRules 渲染策略（官网标准划分）

Nuxt4 支持混合渲染，同一站点不同页面可采用不同策略。

```ts
routeRules: {
  // 首页、关于、产品列表、解决方案、案例、联系我们：SSG
  '/': { prerender: true },
  '/about': { prerender: true },
  '/solution/**': { prerender: true },
  '/product/**': { prerender: true },
  '/case/**': { prerender: true },
  '/news/**': { prerender: true },

  // 动态新闻详情：ISR，缓存 6 小时
  '/news/[slug]': { isr: 3600 * 6 },

  // 后台、预览、用户相关：纯客户端，禁止收录
  '/admin/**': { ssr: false, robots: 'noindex,nofollow' },
  '/preview/**': { robots: 'noindex,nofollow' },

  // 旧链接 301 永久重定向
  '/old-about': { redirect: { to: '/about', statusCode: 301 } }
}
```

|策略|说明|适用页面|
|---|---|---|
|**prerender**|构建时输出静态 HTML，CDN 部署，SEO 最优|首页、关于、产品、方案、案例等静态营销页|
|**isr**|增量静态，CDN 缓存，到期自动刷新|新闻详情、商品详情等中等更新频率的动态内容|
|**ssr: true**|实时服务端渲染|实时数据、强动态页面（官网少用）|
|**ssr: false**|纯客户端渲染|后台、预览、登录后页面，必须配 noindex|

## 3\. Nitro \& 性能基础配置

```ts
nitro: {
  compressPublicAssets: true, // 开启 brotli/gzip 预压缩
  prerender: {
    crawlLinks: true, // 自动爬取站内链接并预渲染（官网必开）
    failOnError: true // 构建发现 404/死链直接报错，防止上线漏页
  }
},
experimental: {
  ssrStreaming: false // 官网建议关闭流式渲染，避免部分爬虫抓取截断
}
```

## 4\. robots / sitemap 默认规则

```ts
robots: {
  allow: ['/'],
  disallow: ['/admin', '/preview', '/api']
},
sitemap: {
  autoLastmod: true, // 自动带上最后更新时间
  exclude: ['/admin/**', '/preview/**']
}
```

# 二、页面路由 \& URL 命名规范

1. **路由文件名：**小写、英文、短横线 `-` 分隔，禁止中文、驼峰、下划线。

    - ✅ `solution-cloud.vue`

    - ❌ `SolutionCloud.vue`、`解决方案.vue`、`solution_cloud.vue`

2. **路由层级扁平化**，控制在 3 级以内。

    - ✅ `/solution/cloud`

    - ❌ `/category/solution/type/cloud/detail`

3. **动态路由用语义化 slug**，不要纯 id。

    - ✅ `/news/nuxt4-seo-best-practice`

    - ❌ `/news?id=1001`

4. **统一域名：**全站 canonical 对齐主域名，统一 www / 非 www，统一 https，不要同时存在两套收录入口。

5. **分页：**新闻分页 `/news?page=2`，设置 `rel="prev"` / `rel="next"`，分页页 canonical 指向列表首页。

# 三、Meta \& SEO 标签开发规范

统一使用 `useSeoMeta`（Nuxt4 已废弃 `useServerSeoMeta`）。业务数据由 `useAsyncData` 在服务端拉取，**不要在 onMounted 里请求正文数据**。

## 1\. 基础页面模板

```vue
<script setup lang="ts">
const route = useRoute()
// 服务端拿数据，SEO 核心：数据在 HTML 源码输出
const { data: page } = await useAsyncData(
  `page-${route.params.slug}`,
  () => fetchPage(route.params.slug)
)

// 响应式 SEO 配置
useSeoMeta({
  title: () => `${page.value.title} | XX科技`,
  description: () => page.value.summary,
  keywords: () => page.value.keywords,
  canonical: () => `${useSiteUrl()}/${route.params.slug}`,
  ogTitle: () => page.value.title,
  ogDescription: () => page.value.summary,
  ogImage: () => page.value.coverImage,
  ogType: 'website',
  twitterCard: 'summary_large_image',
  robots: 'index, follow'
})

// 结构化数据 JSON-LD
useSchemaOrg([
  defineWebPage({
    name: page.value.title,
    description: page.value.summary,
    image: page.value.coverImage
  })
])
</script>
```

## 2\. 结构化数据选择

- 新闻文章页：`defineArticle()`

- 产品页：`defineProduct()`

- 首页：`defineWebSite()`

## 3\. 硬性字数规范

|字段|要求|
|---|---|
|**title**|20–55 字符，核心关键词前置，后缀统一 `| 品牌名`|
|**description**|80–140 中文，自然描述，不要堆砌关键词|
|**禁止**|全站共用一套固定 title/description|

## 4\. definePageMeta 收录标记

```vue
<script setup>
definePageMeta({
  layout: 'default',
  robots: 'index,follow'
})
// 不需要收录的页面：
// definePageMeta({ robots: 'noindex, nofollow' })
</script>
```

# 四、页面结构、语义 HTML 规范

1. **每页唯一 H1**，放在页面主体头部；H2、H3 层级顺序，禁止跳级（H1 → H3）。

2. **语义标签优先：**`<nav>`、`<main>`、`<section>`、`<article>`、`<footer>`，不要全是 div。

3. **导航与内链统一使用 ****`<NuxtLink>`**，最终渲染 `<a href>`，爬虫可抓取。

    - ✅ `<NuxtLink to="/solution">解决方案</NuxtLink>`

    - ❌ 只用 `@click` 跳转，无 a 标签

4. **外部链接：**出站链接加 `rel="noopener noreferrer"`；不信任外链追加 `rel="nofollow"`。

5. **表单、弹窗、Tab 内容：**核心介绍文字直接渲染在 HTML 里，不要藏在 Tab、折叠面板、弹窗里；营销核心卖点不要只靠前端点击才渲染。

# 五、图片、媒体资源规范（NuxtImg）

1. 全部使用 `<NuxtImg>`，禁止原生 `<img>`。

2. **所有图片必须写 alt**，alt 描述图片内容，不要写 alt="图片"。

3. **首屏大图禁止 ****`loading="lazy"`**；非首屏图片开启懒加载。

4. 固定宽高属性，防止布局偏移 CLS。

5. 图片格式优先 webp/avif；原图提前压缩，不要上传几 MB 大图。

6. OG 分享图统一规格：1200 × 630 px。

```vue
<!-- 首屏大图：不懒加载 -->
<NuxtImg
  src="/images/banner.webp"
  alt="云平台 banner"
  width="1920"
  height="800"
/>

<!-- 非首屏图片：开启懒加载 -->
<NuxtImg
  src="/images/case.webp"
  alt="客户案例截图"
  width="600"
  height="400"
  loading="lazy"
/>
```

# 六、字体、静态资源 \& CWV 规范

- 字体优先系统字体；自定义字体使用 `font-display: swap`，预加载关键字体，避免 FOIT。

- 首页 banner、首屏 JS 尽量轻量化；第三方统计（百度统计、友盟）延迟加载，不要阻塞渲染。

- 禁止大量内联大体积 base64 图片。

- 埋点、聊天客服组件用 `useLazyComponent` 延迟引入，不阻塞 LCP。

```ts
const ChatWidget = useLazyComponent(() => import('@/components/ChatWidget.vue'))
```

# 七、数据请求 \& 接口规范（SEO 高频翻车点）

**规范写法：**`useAsyncData` / `useFetch`，在 setup 顶层 await，服务端获取数据并渲染进 HTML 源码。

**禁止：**在 `onMounted` 里面拉取页面核心标题、正文、产品介绍；禁止接口返回后再 v\-if 渲染全部主体内容（源码空白）。

预渲染模式下，`prerender` 构建阶段就会执行接口请求，接口必须支持公网访问、无登录鉴权；动态接口需要做构建环境兼容。

```ts
// ✅ 正确：服务端拿到数据渲染进 HTML
const { data: list } = await useAsyncData('posts', () => $fetch('/api/posts'))
```

# 八、404、状态码、错误页规范

1. 404 页面使用 `pages/[...catchall].vue`，必须返回 HTTP 404 状态码。

2. 不要让 404 返回 200（软 404，SEO 大忌）。

3. 临时下线页面返回 503；永久删除页面 301 跳转到相关页面，不要留死链。

```vue
<script setup>
definePageMeta({
  robots: 'noindex, nofollow'
})
const error = useError()
if (error.value?.statusCode !== 404) {
  error.value = { statusCode: 404, message: '页面不存在' }
}
</script>
```

# 九、构建、上线、验收检查清单

## 开发阶段自检

- 右键【查看网页源代码】，检查 title、description、正文文本、h1、og 标签是否存在。

- 检查图片 alt 是否齐全。

- 检查链接是否为 `<a href>`，不是只有 js 跳转。

- 页面内没有重复 H1。

## 构建 \& 打包检查

- `pnpm generate` 构建无报错，无未捕获死链（依赖 `prerender.failOnError: true`）。

- 输出 `.output/public` 内每个页面独立 html。

## 上线验收

- 提交 sitemap\.xml 到百度资源平台、Google Search Console。

- 抓取诊断：百度抓取工具查看快照源码。

- 检测 Core Web Vitals：PageSpeed Insights。

- 结构化数据校验：Google 富媒体测试工具。

- 检查 canonical、lastmod、hreflang（多语言）。

# 十、禁止清单（红线）

|❌ 以下行为禁止出现在官网项目中|
|---|
|核心内容只在 onMounted 请求渲染|
|多个页面共用一套固定 title / description|
|URL 带中文、特殊符号、驼峰命名|
|首屏大图加 lazy|
|404 返回 200|
|营销官网主页面设置 ssr: false|
|外链不区分 nofollow，全部 follow|
|开启流式渲染（官网稳定优先）|
|生产环境 site\.url 写 localhost、测试域名|

# 十一、官网项目目录推荐

```text
pages/
├── index.vue                # 首页
├── about.vue                # 关于我们
├── solution/
│   ├── index.vue            # 方案列表
│   └── [slug].vue           # 方案详情
├── product/
│   ├── index.vue
│   └── [slug].vue
├── news/
│   ├── index.vue
│   └── [slug].vue
├── case/
│   ├── index.vue
│   └── [slug].vue
├── contact.vue
└── [...catchall].vue        # 404
```

# 附：最简可直接跑的 nuxt\.config\.ts SEO 模板

```ts
export default defineNuxtConfig({
  modules: ['@nuxtjs/seo'],
  site: {
    url: 'https://example.com',
    name: 'Demo Site'
  },
  routeRules: {
    '/blog/**': { prerender: true },
    '/admin/**': { ssr: false, robots: 'noindex,nofollow' }
  },
  nitro: {
    compressPublicAssets: true,
    prerender: {
      crawlLinks: true,
      failOnError: true
    }
  }
})
```

> （注：部分内容由豆包工作 AI 生成）
