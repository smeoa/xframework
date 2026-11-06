---
name: 前台前端开发
description: 基于 3.WBS.json 中用户指定的单个 WBS-FF 编号，用 Nuxt4 + @nuxtjs/seo 开发 front-site 前台页面；默认 SSG（prerender）优先，动态页用 ISR，严格遵循《Nuxt4 官网开发 SEO 规范.md》；改动后通过 pnpm generate 与 Playwright 校验，仅同步更新 3.WBS.json 中该任务状态
---

# 前台前端开发规范（Nuxt4 · 官网 SEO 优先）

## 1. 功能描述

仅处理 `3.WBS.json` 中用户指定 WBS 编号的**单个 WBS-FF 前台开发任务**，在 `front-site/` 内用 Nuxt4 实现该页面或组件，全量落地 UX 交互与 SEO 要求，通过构建与 Playwright 验证后，仅把该任务状态改为"已完成"，不修改其他任务与无关文件。

**必读文档（按优先级）**：

| 文档 | 作用 |
|---|---|
| `Nuxt4 官网开发 SEO 规范.md` | SEO / 渲染策略 / CWV 的硬性规则，冲突时以本文为准 |
| `3.WBS.json` | 唯一任务来源，只读指定编号 |
| `2.PRD.md` | 对应章节的需求、字段与验收标准 |
| `UI规范.md` | 视觉基线（颜色、字号、间距、组件尺寸） |

> 技术栈口径：前台统一使用 **Nuxt4 + @nuxtjs/seo v6**；源清单中"Astro 或 Next.js 二选一"的表述不再适用。

## 2. 输入输出规范

- **必选输入参数**：`WBS任务编号`（格式：`WBS-FF-X.X-XXX`，如 `WBS-FF-13.1-001`）
- **只读输入1**：`3.WBS.json`（仅读取指定编号的任务内容与依赖）
- **只读输入2**：`2.PRD.md`（仅读取对应章节）
- **只读输入3**：`Nuxt4 官网开发 SEO 规范.md`、`UI规范.md`
- **可写输出1**：`front-site/app/pages/**`（页面文件）
- **可写输出2**：`front-site/app/components/**`、`app/layouts/**`、`app/composables/**`（组件与复用逻辑）
- **可写输出3**：`front-site/nuxt.config.ts`、`front-site/tests/**`（仅做任务必要改动）
- **可写输出4**：`3.WBS.json`（仅将该任务 `status` 改为"已完成"）
- **绝对禁止**：修改 `admin/`、`front-admin/`、数据库设计文件、其他 WBS 任务、其他页面已有内容

## 3. 技术栈与渲染策略

| 项 | 规定 |
|---|---|
| 框架 | Nuxt4（`app/` 目录结构），TypeScript |
| SEO 模块 | `@nuxtjs/seo`（含 sitemap、robots、schema-org） |
| 包管理 | pnpm；脚本 `dev` / `build` / `generate` / `lint` / `test` |
| 静态内容页 | `prerender: true`（首页、关于、产品、服务、案例、联系、法务页） |
| 详情类动态页 | `isr` 增量静态，默认 6 小时（`3600 * 6`） |
| 后台 / 预览页 | `ssr: false` + `robots: 'noindex,nofollow'` |
| 流式渲染 | 关闭（`experimental.ssrStreaming: false`），保证爬虫抓取完整 |

## 4. 目录结构规范

```text
front-site/
├── app/
│   ├── app.vue                  # 根组件
│   ├── pages/                   # 路由页面（文件即路由）
│   │   ├── index.vue
│   │   ├── about.vue
│   │   ├── contact.vue
│   │   ├── products/
│   │   │   ├── index.vue
│   │   │   └── [slug].vue
│   │   ├── collections/[slug].vue
│   │   ├── blog/
│   │   │   ├── index.vue
│   │   │   └── [slug].vue
│   │   ├── pages/[slug].vue     # 长尾服务落地页
│   │   └── [...slug].vue        # 404 兜底，必须返回 404
│   ├── layouts/
│   │   └── default.vue          # header / topbar / breadcrumb / footer 插槽
│   ├── components/
│   ├── composables/             # useApi、useSeo 等
│   ├── utils/
│   └── assets/
│       ├── css/                 # token、基础样式、组件样式
│       └── images/
├── public/                      # favicon、robots 用静态文件、OG 默认图
├── server/                      # 仅在前台需要同源代理/接口时使用
├── tests/                       # Playwright 用例
├── nuxt.config.ts
├── package.json
└── .env.development / .env.staging / .env.production
```

- 页面文件只做数据装配与区块组合，业务区块拆到 `components/`。
- 可复用逻辑（请求、格式化、埋点）放 `composables/`，纯函数放 `utils/`。
- 样式统一走 `assets/css` 中的 token 变量，禁止在页面内写死色值与字号。

## 5. 命名规范

| 类型 | 规范 | 示例 |
|---|---|---|
| 页面文件 | 小写 kebab-case，全英文 | `oem-odm.vue`、`quality-compliance.vue` |
| 动态路由 | 语义化 slug | `products/[slug].vue` |
| 组件 | PascalCase | `ProductCard.vue`、`SiteHeader.vue` |
| composable | camelCase + `use` 前缀 | `useApi.ts`、`useInquiryForm.ts` |
| 工具函数 | camelCase | `formatDate.ts` |
| CSS 类名 | kebab-case，BEM 风格可选 | `.product-card`、`.section-title` |
| 常量 | UPPER_SNAKE_CASE | `MAX_UPLOAD_SIZE` |
| 字段 | 组件/页面 camelCase，接口 snake_case | `productName` / `product_name` |

## 6. nuxt.config.ts 基线

```ts
export default defineNuxtConfig({
  modules: ['@nuxtjs/seo'],

  // 生产域名必须由环境变量注入，禁止写死 localhost 或测试域名
  site: {
    url: process.env.SITE_URL,
    name: '[Brand]',
    description: '925 silver jewelry OEM/ODM manufacturer and wholesale supplier.',
    defaultLocale: 'en'
  },

  routeRules: {
    '/': { prerender: true },
    '/about': { prerender: true },
    '/factory': { prerender: true },
    '/contact': { prerender: true },
    '/faq': { prerender: true },
    '/terms': { prerender: true },
    '/privacy': { prerender: true },
    '/products/**': { prerender: true },
    '/collections/**': { prerender: true },
    '/pages/**': { prerender: true },
    '/blog': { prerender: true },
    '/blog/[slug]': { isr: 3600 * 6 },
    '/admin/**': { ssr: false, robots: 'noindex,nofollow' },
    '/preview/**': { ssr: false, robots: 'noindex,nofollow' }
  },

  nitro: {
    compressPublicAssets: true,
    prerender: {
      crawlLinks: true,   // 自动爬取站内链接并预渲染
      failOnError: true   // 出现 404 / 死链直接构建失败
    }
  },

  experimental: {
    ssrStreaming: false
  },

  robots: {
    allow: ['/'],
    disallow: ['/admin', '/preview', '/api']
  },

  sitemap: {
    autoLastmod: true,
    exclude: ['/admin/**', '/preview/**']
  }
})
```

- `SITE_URL` 只在 `.env.production` / 部署平台注入；缺失时构建应失败而非回退到假域名。

## 7. 路由与 URL 规范

1. 路由文件名小写、英文、短横线分隔，禁止中文、下划线、驼峰。
2. 层级不超过 3 级：`/products/[slug]` 合规，`/category/product/type/detail` 不合规。
3. 动态路由必须语义化 slug，禁止纯 id（`/products/silver-ring-001` 而非 `/products?id=1001`）。
4. 全站 canonical 对齐主域名，统一 `https` 与 `www` / 非 `www`，不产生两套收录入口。
5. 分页 URL 用查询参数（`?page=2`），输出 `rel="prev"` / `rel="next"`，分页页 canonical 指向列表首页。
6. 站内跳转一律 `<NuxtLink to="...">`，最终渲染为 `<a href>`；禁止只用 `@click` 跳转。

## 8. SEO 元信息与结构化数据

### 8.1 页面标准模板

```vue
<script setup lang="ts">
const route = useRoute()
const { data: page } = await useAsyncData(
  `page-${route.params.slug}`,
  () => fetchPage(route.params.slug as string)
)

useSeoMeta({
  title: () => `${page.value?.title} | [Brand]`,
  description: () => page.value?.summary,
  ogTitle: () => page.value?.title,
  ogDescription: () => page.value?.summary,
  ogImage: () => page.value?.coverImage,
  ogType: 'website',
  twitterCard: 'summary_large_image',
  robots: 'index, follow'
})

useSchemaOrg([
  defineWebPage({
    name: page.value?.title,
    description: page.value?.summary,
    image: page.value?.coverImage
  })
])
</script>
```

### 8.2 硬性要求

| 项 | 要求 |
|---|---|
| API | 必须使用 `useSeoMeta`（Nuxt4 已废弃 `useServerSeoMeta`） |
| title | 20–55 字符，核心关键词前置，后缀统一 `\| [Brand]`；每页独立，禁止全站复用 |
| description | 80–140 字符，自然描述，禁止堆词 |
| H1 | 每页唯一，位于主体头部 |
| 结构化数据 | 首页 `defineWebSite`、产品页 `defineProduct`、文章页 `defineArticle`、其余 `defineWebPage`；产品页不输出公开价格，`offers` 用 Inquiry Required 口径 |
| 收录控制 | 需收录页 `robots: 'index,follow'`；后台/预览/404 页 `noindex,nofollow` |
| sitemap / robots | 由 `@nuxtjs/seo` 自动生成，不在页面内手写 |

## 9. 页面结构与语义 HTML

1. 语义标签优先：`<header>`、`<nav>`、`<main>`、`<section>`、`<article>`、`<footer>`，禁止全 `div`。
2. 标题层级严格 H1 → H2 → H3，不跳级，每页一个 H1。
3. 正文、卖点、产品参数等核心内容必须直接渲染进 HTML，不得藏在 Tab、折叠面板、弹窗或 `onMounted` 之后。
4. 外链加 `rel="noopener noreferrer"`；不信任来源追加 `rel="nofollow"`。
5. 表单控件必须绑定 `<label>`，图标按钮补 `aria-label`，焦点样式可见。

## 10. 数据请求规范

```ts
// ✅ setup 顶层 await，数据由服务端渲染进 HTML
const { data: products } = await useAsyncData('products', () =>
  useApi('/products/get-product-list', { page: 1, limit: 24 })
)
```

- 统一走 `app/composables/useApi.ts`：仅 `POST`、统一错误结构、自动 snake_case ↔ camelCase 转换（与 `admin` 侧 `request.js` 约定保持一致）。
- 禁止在 `onMounted` 拉取页面标题、正文、产品介绍等核心内容；禁止先请求再用 `v-if` 渲染整页主体。
- 预渲染阶段会真实发起请求：接口必须公网可达、无需登录鉴权，且能在构建环境正常返回。
- 请求失败必须有失败态与重试入口，禁止白屏。

## 11. 图片与媒体规范

1. 一律使用 `<NuxtImg>`，禁止原生 `<img>`。
2. 所有图片必须写 `alt`，描述画面内容，禁止 `alt="image"` 或空 `alt`。
3. 首屏大图（LCP 元素）禁止 `loading="lazy"`；非首屏图片必须懒加载。
4. 必须声明 `width` / `height`，避免 CLS；格式优先 webp / avif。
5. OG 分享图统一 1200 × 630 px，放在 `public/` 或走 CDN。

```vue
<!-- 首屏大图 -->
<NuxtImg src="/images/hero.webp" alt="Silver jewelry production line" width="1920" height="800" />

<!-- 非首屏 -->
<NuxtImg src="/images/case.webp" alt="Custom silver ring sample" width="600" height="400" loading="lazy" />
```

## 12. 样式与 CWV 规范

- 视觉 token 与组件尺寸以 `UI规范.md` 为准，全部落成 CSS 变量，页面内禁止自造色值。
- 字体优先系统字体；自定义字体必须 `font-display: swap` 并预加载关键字体。
- 埋点、客服、订阅弹窗等非首屏组件延迟加载，不阻塞 LCP。
- 禁止用大体积 base64 内联图片。
- 目标：LCP ≤ 2.5s、CLS ≤ 0.1、INP ≤ 200ms（以 PageSpeed Insights 实测为准）。

## 13. 404 与状态码规范

1. `app/pages/[...slug].vue` 兜底，必须返回 HTTP 404 状态码，禁止软 404（返回 200）。
2. 临时下线页返回 503；永久迁移页用 301 跳转到相关页，不留死链。
3. 404 页设置 `robots: 'noindex,nofollow'`，并提供返回首页、产品目录、联系我们的出口。

```vue
<script setup lang="ts">
definePageMeta({ robots: 'noindex, nofollow' })
const event = useRequestEvent()
if (event) setResponseStatus(event, 404)
</script>
```

## 14. 本站（925 银饰 B2B）硬性约束

- 询盘制站点：不实现购物车、结账、在线支付、公开注册登录、公开价格。
- 界面文案与页面内容为英文；代码注释中文。
- 未知业务事实（品牌名、年限、产能、认证、客户名）一律保留 `【待我方确认】` 或 `[placeholder:...]`，禁止编造。
- 主 CTA 统一指向询盘表单或 Contact 页，并带来源参数。
- 表单提交必须有三态（提交中 / 成功 / 失败），失败保留已填内容。

## 15. 执行步骤（严格按顺序）

1. **解析任务**：确认编号以 `WBS-FF-` 开头；读取 `3.WBS.json` 该任务；状态非"未开始"则终止并说明。
2. **读取依据**：`2.PRD.md` 对应章节、`Nuxt4 官网开发 SEO 规范.md`、`UI规范.md`；确认该页渲染策略（prerender / isr / ssr:false）。
3. **检查现状**：若 `front-site/` 不存在，按第 4 节结构初始化并配置 `nuxt.config.ts`；已存在则沿用现有目录与样式 token。
4. **实现页面**：先路由与布局插槽，再区块组件，最后交互；同步写入 `useSeoMeta` 与 JSON-LD。
5. **补充样式**：只改任务相关样式，复用 token，验证 390 / 768 / 1440 三档无横向溢出。
6. **构建验证**：`pnpm generate` 必须零报错、零死链；检查 `.output/public` 内每页独立 html，源码含 title、description、H1、OG。
7. **Playwright 验证**：更新/新增 `tests/{page}.spec.js`，覆盖渲染、导航、表单三态、404、无控制台报错。
8. **更新 WBS**：仅将 `3.WBS.json` 中该 `wbs_id` 的 `status` 改为"已完成"，其余字段与任务不动。
9. **清理**：删除临时脚本与调试文件，不留在仓库中。

## 16. 验收清单

- [ ] `pnpm lint` 无错误，符合 Vue3 / TypeScript 规范
- [ ] `pnpm generate` 成功，`prerender.failOnError` 未触发
- [ ] 查看网页源代码可见 title、description、H1、OG、canonical
- [ ] 每页唯一 H1，标题层级不跳级，图片 alt 齐全
- [ ] 站内链接均为 `<a href>`，无 `@click` 跳转式假链接
- [ ] 390 / 768 / 1440 三档布局稳定，无横向滚动
- [ ] 首屏大图未懒加载，其余图片懒加载，无布局偏移
- [ ] 404 返回 404 状态码与 `noindex`
- [ ] Playwright 用例全部通过，无控制台错误
- [ ] `3.WBS.json` 仅该任务状态变更

## 17. 禁止清单（红线）

| 禁止项 |
|---|
| 核心内容在 `onMounted` 请求后渲染 |
| 多个页面共用一套固定 title / description |
| URL 含中文、特殊符号、下划线、驼峰 |
| 首屏大图加 `loading="lazy"` |
| 404 返回 200 |
| 营销页面设置 `ssr: false` |
| 外链不加 `nofollow` / `noopener` |
| 开启 `ssrStreaming` |
| 生产环境 `site.url` 写 localhost 或测试域名 |
| 页面内写死色值、字号，绕过 `UI规范.md` token |
