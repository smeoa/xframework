# INSPINIA+ Admin Dashboard UI/UX 规范

> 基于 INSPINIA+ Tailwind 版本 (webapplayers.com/inspinia/tailwind) 分析整理
> 技术栈: Tailwind CSS + Bootstrap 5 混合模式

---

## 1. 色彩体系 (Color System)

### 1.1 语义色 (Semantic Colors)

| 用途 | 色值 | Hover 态 | 说明 |
|------|------|----------|------|
| Primary (主色) | `#1ab394` | `#179f84` | 薄荷绿，用于品牌强调、按钮主色 |
| Secondary (辅助) | `#1c84c6` | `#1977b2` | 蓝色，图表辅助色 |
| Success (成功) | `#0acf97` | `#09ba88` | 绿色，正向状态 |
| Info (信息) | `#23c6c8` | `#20b2b4` | 青色，信息提示 |
| Warning (警告) | `#f8ac59` | `#e19950` | 橙色，注意提醒 |
| Danger (危险) | `#ed5565` | `#d54d5b` | 红色，错误/删除 |
| Dark (深色) | `#313a46` | `#2c3440` | 深灰蓝，深色元素 |
| Light (浅色) | `#eef2f7` | `#d6dbe0` | 浅灰蓝，浅色背景 |

### 1.2 中性色阶 (Neutral Scale)

| Token | 色值 | 用途 |
|-------|------|------|
| `--color-default-50` | `oklch(98.4% 0.003 247.858)` ≈ `#f8f9fc` | 最浅背景 |
| `--color-default-100` | `#f6f7fb` | 卡片悬浮背景 / 交替行 |
| `--color-default-200` | `#eef2f7` | 轻度分隔 / 浅色 Badge 背景 |
| `--color-default-300` | `#e7e9eb` | 边框 / 分割线 |
| `--color-default-400` | `#9ba6b7` | 占位文字 / 次要信息 |
| `--color-default-500` | `#a1a9b1` | 禁用态文字 |
| `--color-default-600` | `#8a969c` | 次要文字 |
| `--color-default-700` | `#6c757d` | 辅助说明文字 |
| `--color-default-800` | `#343a40` | 深色文字 |
| `--color-default-900` | `#313a46` | 标题 / 深色强调 |

### 1.3 图表专用色 (Chart Colors)

| 名称 | 色值 |
|------|------|
| Chart Primary | `#1ab394` |
| Chart Secondary | `#1c84c6` |
| Chart Alpha | `#23c6c8` |
| Chart Beta | `#ed5565` |
| Chart Gamma | `#7b70ef` |
| Chart Delta | `#f8ac59` |
| Chart Zeta | `#ff679b` |
| Chart Gray | `#edeff3` |
| Chart Dark | `#1a57a1` |
| Chart Border | `#ecf4fc` |
| Chart Title | `#bbcae1` |

---

## 2. 字体体系 (Typography)

### 2.1 字体族 (Font Family)

| 用途 | 字体 |
|------|------|
| 主字体 (Body) | `"MiSans", "PingFang SC", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif` |
| 辅助字体 (Secondary) | `"MiSans", "PingFang SC", "Microsoft YaHei", sans-serif` |
| 系统字体 (Sans fallback) | `ui-sans-serif, system-ui, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji"` |
| 等宽字体 (Mono) | `ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace` |

**小米 MiSans 字体加载**（小米官方 CDN，免费商用）:

```html
<link rel="stylesheet" href="https://font.sec.miui.com/font/css?family=MiSans:400,500,600,700:MiSans" />
```

### 2.2 字号层级 (Type Scale)

| 元素 | 字号 | 字重 | 行高 | 颜色 |
|------|------|------|------|------|
| H3 (卡片标题) | `20px` | 600 (Semi-bold) | `30px` (1.5) | `#4c4c5c` |
| H4 (区块标题) | `16px` | 600 (Semi-bold) | `24px` (1.5) | `#4c4c5c` |
| H5 (小标题) | `13px` | 600 (Semi-bold) | `19.5px` (1.5) | `#4c4c5c` |
| Body 正文 | `13px` (`0.8125rem`) | 400 (Normal) | `19.5px` (1.5) | `#4c4c5c` |
| 正文次要 | `13px` | 400 | `19.5px` | `rgba(76,76,92,0.75)` |

### 2.3 字重 (Font Weight)

| 名称 | 值 | 用途 |
|------|-----|------|
| Light | 300 | 大数字展示 |
| Normal | 400 | 正文内容 |
| Medium | 500 | 侧边栏菜单项 |
| Semi-bold | 600 | 标题、H3-H6 |
| Bold | 700 | 侧边栏分类标签 |

### 2.4 文字颜色

| 用途 | 色值 |
|------|------|
| 主文字 | `#4c4c5c` (`--color-body-color`) |
| 次要文字 (75% 透明度) | `rgba(76, 76, 92, 0.75)` |
| 辅助文字 | `#6c757d` (`--color-default-700`) |
| 占位文字 | `rgba(76, 76, 92, 0.5)` (50% 透明度) |
| 白色文字 | `#ffffff` (深色背景上) |

---

## 3. 间距系统 (Spacing)

基于 Tailwind 的 4px 基准间距 (`--spacing: 0.25rem`)，结合 `--spacing-base: 20px`。

### 3.1 常用间距值

| Tailwind 类 | 实际值 | 典型用途 |
|-------------|--------|----------|
| `p-1.5` | `6px` | 紧凑内间距 |
| `p-2` | `8px` | 表头单元格 |
| `p-2.5` | `10px` | 侧边栏菜单项 |
| `p-3` | `12px` | 表格单元格 |
| `p-5` | `20px` | 卡片内容标准间距 |
| `p-[30px]` | `30px` | 大卡片内容间距 |

### 3.2 布局间距

| 区域 | 间距 |
|------|------|
| 卡片间距 (纵向) | `my-5` = `20px` 上下 |
| 侧边栏菜单项间距 | `7px 10px` (padding) |
| 侧边栏分类标签间距 | `10px` 上下 (padding) |

---

## 4. 圆角系统 (Border Radius)

| Token | 值 | Tailwind 类 | 用途 |
|-------|-----|-------------|------|
| `--radius-sm` | `0.25rem` (4px) | `rounded-sm` | 小型元素 |
| `--radius` | `4px` | `rounded` | 按钮、输入框、卡片 |
| `--radius-md` | `0.375rem` (6px) | `rounded-md` | 中等元素 |
| `--radius-lg` | `0.5rem` (8px) | `rounded-lg` | 较大容器 |
| `--radius-xl` | `0.75rem` (12px) | `rounded-xl` | 大圆角 |
| `--radius-2xl` | `1rem` (16px) | `rounded-2xl` | 特大圆角 |
| `--radius-4xl` | `2rem` (32px) | `rounded-4xl` | 胶囊/圆形 |
| 侧边栏菜单项 | `5px` | - | 活跃/悬浮态 |

---

## 5. 阴影系统 (Shadows)

| Token | 值 | 用途 |
|-------|-----|------|
| `--shadow-sm` | `0 0.0625rem 0.125rem rgba(76,76,92,.15)` | 轻微浮起 (1px 2px) |
| `--shadow` / `--tw-shadow` | `0px 1px 4px 0px rgba(130,143,163,.15)` | 标准阴影 |
| `--jvm-box-shadow` | `0 1px 2px 0 rgba(0,0,0,.05)` | 图表容器阴影 |
| 卡片默认 | `none` (无阴影) | 使用 0.8px 边框代替 |

> 设计特征: INSPINIA 的卡片组件**不使用阴影**，而是通过 `0.8px solid #e7e9eb` 边框来区分层次，风格更偏向扁平简洁。

---

## 6. 布局系统 (Layout)

### 6.1 整体布局

```
┌──────────────────────────────────────────────┐
│  Sidebar (235px)  │  Top Navigation (65px)    │
│                   │──────────────────────────│
│  Background:      │  Content Area            │
│  #23303c          │  Background: #f1f2f7     │
│  (深蓝灰)         │                          │
│                   │  Cards / Widgets         │
│  Text: #8495ab    │                          │
│  Active: #ced6df  │                          │
│  Active BG:       │                          │
│  #1c2f3f          │                          │
└──────────────────────────────────────────────┘
```

### 6.2 布局参数

| 区域 | 参数 | 值 |
|------|------|-----|
| 侧边栏宽度 | `--` | `220px` |
| 顶栏高度 | `--topbar-height` | `65px` |
| 侧边栏背景 | `--` | `rgb(35, 48, 60)` ≈ `#23303c` |
| 顶栏背景 | `--topbar-bg` | `#ffffff` |
| 内容区背景 | `--color-body-bg` | `#f1f2f7` |
| 侧边栏边框色 | `--sidenav-border-color` | `#23303c` |

### 6.3 最小宽度约束

| 属性 | 值 | 说明 |
|------|-----|------|
| 页面最小宽度 | `1440px` | 页面主体内容区域最小宽度，低于此值可能会出现水平滚动 |

---

## 7. 组件规范 (Components)

### 7.1 卡片 (Card)

| 属性 | 值 |
|------|-----|
| 背景色 | `#ffffff` (`--color-card`) |
| 圆角 | `4px` |
| 边框 | `0.8px solid #e7e9eb` |
| 阴影 | `none` |
| 内容区内间距 | `20px` (标准) / `30px` (大卡片) |
| 标题字号 | H5: 13px / H4: 16px |
| 标题字重 | 600 |
| 标题颜色 | `#4c4c5c` |

### 7.2 按钮 (Button)

| 属性 | 值 |
|------|-----|
| 圆角 | `4px` |
| 字号 | `13px` |
| 字重 | 500 (Medium) |
| 内间距 | 根据 Tailwind 默认 |
| Primary 背景 | `#1ab394` |
| Primary 文字 | `#ffffff` |
| Primary Hover | `#179f84` |

### 7.3 输入框 (Input)

| 属性 | 值 |
|------|-----|
| 高度 | `37px` |
| 圆角 | `4px` |
| 边框 | `0.8px solid #e7e9eb` |
| 字号 | `13px` |
| 背景 | `transparent` (搜索框) |
| 占位符透明度 | `50%` |

### 7.4 表格 (Table)

| 属性 | 值 |
|------|-----|
| 单元格下边框 (行) | `0.8px solid #eef2f7` (on `el-table__row`) |
| 表头背景 | `#f6f7fb` (`--color-default-100`)，非透明 |
| 表头文字 | `13px`, 400 (Normal), `#4c4c5c` |
| 表头内间距 | `12px 0` (仅保留上下内边距) |
| 单元格内间距 | `12px 0` (仅保留上下内边距) |
| 单元格颜色 | `#4c4c5c` |
| 最后一行 | 无下边框 |

**表格宽度规范：**

- 表格自动填满父容器宽度（继承 `el-table` 默认 `width: 100%`）
- 列宽自适应内容（`min-width: 0`，不设固定宽度）
- 固定列仅限：选择框列 `40px`、操作列 `120px`
- 表格区域 `.table-area` 的 `min-width: 0`（不限制最小宽度）
- 禁止使用 `min-width: 400px` 等硬编码约束

**单元格内容展示策略：**

| 条件 | 行为 | CSS |
|------|------|-----|
| 默认 | 允许自然换行 | `white-space: normal; word-break: break-word; overflow: hidden` |
| 超过 2 行（`field.wrap = true`） | 省略号截断 + hover 悬浮显示全文 | `-webkit-line-clamp: 2; overflow: hidden` + `el-popover` |

> 默认 `.cell` 为自然换行模式。如需限制 2 行并 hover 查看全文，在 `fieldConfig` 中设置 `wrap: true`。

### 7.5 分页 (Pagination)

| 属性 | 值 |
|------|-----|
| 页码字号 | `13px` |
| 页码字重 | `400` (Normal)，不加粗 |
| 对齐方式 | 居右 (`justify-content: flex-end`) |
| 上边距 | `20px` |

### 7.6 Badge / 标签

| 类型 | 背景色 | 文字色 |
|------|--------|--------|
| Success | `#0acf97` | `#ffffff` |
| Warning | `#f8ac59` | `#ffffff` |
| Danger | `#ed5565` | `#ffffff` |
| Light | `#eef2f7` | `#313a46` |
| Success (Soft) | `rgba(10, 207, 151, 0.15)` | `#0acf97` |

> 圆角: Badge 使用 `rounded-full` (完全圆角) 或 `rounded` (4px)

### 7.6 侧边栏导航 (Sidebar Navigation)

| 属性 | 值 |
|------|-----|
| 宽度 | `235px` |
| 背景色 | `#23303c` (深蓝灰) |
| 分类标签字号 | `9.8px` (约 10px) |
| 分类标签字重 | 700 (Bold) |
| 分类标签颜色 | `#8495ab` |
| 分类标签字间距 | `0.98px` |
| 分类标签文字变换 | `uppercase` |
| 菜单项字号 | `13.2px` |
| 菜单项字重 | 500 (Medium) |
| 菜单项颜色 | `#8495ab` |
| 菜单项悬浮颜色 | `#ced6df` |
| 菜单项活跃颜色 | `#ced6df` |
| 菜单项活跃背景 | `#1c2f3f` |
| 菜单项内间距 | `7px 10px` |
| 菜单项高度 | `31.5px` |
| 菜单项圆角 | `5px` |

### 7.7 顶栏 (Topbar)

| 属性 | 值 |
|------|-----|
| 高度 | `65px` |
| 背景 | `#ffffff` |
| 项目文字颜色 | `#6c757d` |
| 项目悬浮颜色 | `#1ab394` (Primary) |
| 搜索框边框 | `#e7e9eb` |
| 搜索框背景 | `transparent` |

---

## 8. 图标系统 (Icons)

使用 **Iconify** 图标库，图标类名格式: `iconify tabler--{icon-name}`

示例:

- `iconify tabler--credit-card` (信用卡图标)
- 图标对齐: 使用 `me-1.5 text-base align-middle` 与文字对齐

---

## 9. 交互规范 (Interaction Patterns)

### 9.1 悬浮态 (Hover States)

| 元素 | Hover 效果 |
|------|------------|
| 按钮 | 背景色变深 10-15% (各语义色均有对应 hover 值) |
| 侧边栏菜单 | 文字颜色变为 `#ced6df` |
| 顶栏项目 | 文字颜色变为 Primary `#1ab394` |
| 表格行 | 隐含 `table-hover` 类 |

### 9.2 活跃态 (Active States)

| 元素 | Active 效果 |
|------|-------------|
| 侧边栏菜单 | 背景 `#1c2f3f` + 文字 `#ced6df` |

### 9.3 通知/红点

- 圆形 Badge: `size-4` (16px), `rounded-full`, 绝对定位 `-end-px -top-[13px]`
- 数字标签: 同上，白色文字居中

---

## 10. 设计特征总结

### 风格定位

- **类型**: 企业级后台管理面板 (Admin Dashboard)
- **风格**: 扁平化 + 轻微深度，偏向简洁专业
- **视觉密度**: 中高密度信息展示，适合数据驱动的管理场景

### 核心设计决策

1. **无边框阴影策略**: 卡片不使用 box-shadow，改用 0.8px 细边框 (`#e7e9eb`) 区分层级，保持界面干净
2. **薄荷绿主色调**: `#1ab394` 贯穿整个品牌，区别于常见的蓝色系后台
3. **深色侧边栏 + 白色内容区**: 经典的对比布局，深蓝灰 `#23303c` 侧边栏搭配白色顶栏和浅灰内容区
4. **紧凑字号**: 基础字号 13px，表头仅 11px，适合在有限空间内展示更多数据
5. **MiSans 字体**: 小米自有字体（mi.com 同款），优秀的中英文屏幕可读性，来自 font.sec.miui.com CDN，免费商用
6. **统一的圆角体系**: 全局使用 4px 基准圆角，菜单项 5px，保持一致性
7. **语义色完整**: Primary / Secondary / Success / Info / Warning / Danger / Dark / Light 八色体系，均有对应 hover 态

### 响应式断点

基于 Tailwind CSS 默认断点:

- `sm`: 640px
- `md`: 768px
- `lg`: 1024px
- `xl`: 1280px
- `2xl`: 1536px

---

## 附录: CSS 变量速查

```css
:root {
  /* 语义色 */
  --color-primary: #1ab394;
  --color-primary-hover: #179f84;
  --color-secondary: #1c84c6;
  --color-secondary-hover: #1977b2;
  --color-success: #0acf97;
  --color-success-hover: #09ba88;
  --color-info: #23c6c8;
  --color-info-hover: #20b2b4;
  --color-warning: #f8ac59;
  --color-warning-hover: #e19950;
  --color-danger: #ed5565;
  --color-danger-hover: #d54d5b;
  --color-dark: #313a46;
  --color-dark-hover: #2c3440;
  --color-light: #eef2f7;
  --color-light-hover: #d6dbe0;

  /* 基础色 */
  --color-body-bg: #f1f2f7;
  --color-body-color: #4c4c5c;
  --color-card: #ffffff;

  /* 布局 */
  --topbar-bg: #ffffff;
  --topbar-height: 65px;
  --topbar-item-color: #6c757d;
  --topbar-item-hover-color: #1ab394;
  --topbar-search-border: #e7e9eb;
  --topbar-search-bg: transparent;

  /* 侧边栏 */
  --sidenav-item-color: #8495ab;
  --sidenav-item-hover-color: #ced6df;
  --sidenav-item-active-color: #ced6df;
  --sidenav-item-font-size: 0.875rem;
  --sidenav-item-font-weight: 500;
  --sidenav-sub-item-font-size: 0.825rem;
  --sidenav-sub-item-font-weight: 500;
  --sidenav-border-color: #23303c;

  /* 字体 */
  --font-body: "MiSans", "PingFang SC", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
  --font-secondary: "MiSans", "PingFang SC", "Microsoft YaHei", sans-serif;
  --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  --text-body: 0.8125rem; /* 13px */

  /* 间距 */
  --spacing: 0.25rem;
  --spacing-base: 20px;

  /* 圆角 */
  --radius: 4px;
  --radius-sm: 0.25rem;
  --radius-md: 0.375rem;
  --radius-lg: 0.5rem;
  --radius-xl: 0.75rem;
  --radius-2xl: 1rem;
  --radius-4xl: 2rem;

  /* 阴影 */
  --shadow: 0px 1px 4px 0px rgba(130,143,163,.15);
  --shadow-sm: 0 0.0625rem 0.125rem rgba(76,76,92,.15);
}
```
