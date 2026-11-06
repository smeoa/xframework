# front-site · 925 银饰 B2B 独立站前台

Nuxt4 + `@nuxtjs/seo` 官网前台，默认 SSG（prerender）优先，动态详情页使用 ISR。

## 环境要求

| 项      | 版本                               |
| ------- | ---------------------------------- |
| Node.js | >= 22.22.3（当前开发机为 22.23.4） |
| pnpm    | 9.x                                |

前台使用 `nuxt 4.6.x` + `@nuxtjs/seo 6.x`，两者均要求 Node `>= 22.22.3`。

## 常用命令

```bash
pnpm install          # 安装依赖（自动执行 nuxt prepare 与 git hooks 安装）
pnpm dev              # 开发服务器，读取 .env.development
pnpm build            # 生产构建，读取 .env.production
pnpm generate         # 全站预渲染，产物在 .output/public
pnpm preview          # 预览生产产物
pnpm lint             # ESLint 检查
pnpm lint:fix         # ESLint 自动修复
pnpm typecheck        # 类型检查
pnpm format           # Prettier 格式化
pnpm format:check     # 格式化校验
pnpm test             # Playwright 冒烟测试（自动拉起 dev server）
```

首次运行 `pnpm test` 前需安装浏览器：`npx playwright install chromium`。

未全局安装 pnpm 时，用 `npx -y pnpm@9 <命令>` 替代。

## 环境变量

| 文件               | 用途         | 提交入库               |
| ------------------ | ------------ | ---------------------- |
| `.env.development` | 本地开发     | 是（无密钥）           |
| `.env.staging`     | 预发布       | 是（无密钥）           |
| `.env.production`  | 生产         | 是（仅键名与占位域名） |
| `.env.example`     | 变量模板     | 是                     |
| `.env.local`       | 本地私有覆盖 | 否                     |

- `SITE_URL` 缺失时生产构建会直接失败，禁止回退到 localhost。
- `.env.production` 中 `SITE_URL` 为占位域名，上线前由部署平台注入真实域名。
- 表单 webhook、邮件、Calendly、埋点等键值统一由部署平台注入，仓库内不存放任何真实密钥。

## 目录结构

```text
front-site/
├── app/
│   ├── app.vue              # 根组件
│   ├── pages/               # 路由页面（文件即路由）
│   ├── layouts/             # 布局（全局骨架由 ENG-003 落地）
│   ├── components/          # 业务区块组件
│   ├── composables/         # 请求、表单、埋点等复用逻辑
│   ├── utils/               # 纯函数
│   └── assets/css/          # 全局样式（token 由 ENG-002 落地）
├── public/                  # favicon、OG 默认图等静态文件
├── tests/                   # Playwright 用例
├── nuxt.config.ts
└── .env.*
```

## 渲染策略

| 路由                       | 策略                                                         |
| -------------------------- | ------------------------------------------------------------ |
| `/`                        | `prerender: true`                                            |
| `/admin/**`、`/preview/**` | `ssr: false` + `noindex,nofollow`                            |
| 其余未匹配路由             | `app/pages/[...slug].vue` 返回 HTTP 404 + `noindex,nofollow` |

业务页面路由由 ENG-004 统一注册，本阶段仅登记已存在路由，避免 `prerender.failOnError` 因未建页面而构建失败。

## 部署

1. 部署平台注入 `SITE_URL` 及所需键值。
2. 执行 `pnpm generate`，上传 `.output/public` 至静态 CDN。
3. 静态托管需配置未匹配路径回退到 `404.html` 并返回 404 状态码（`npx serve .output/public` 已按此行为验证）。
4. 强制 HTTPS，`sitemap.xml` / `robots.txt` 由 `@nuxtjs/seo` 自动生成。

## 提交规范

`pre-commit` 钩子（simple-git-hooks + lint-staged）会执行 ESLint 自动修复、Prettier 格式化与 `nuxt typecheck`；任一失败即阻止提交，不提供绕过脚本。
