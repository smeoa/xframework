---
name: 后台前端开发
description: 基于 3.WBS.json 和现有代码，用 Vue3+JS+Element Plus 开发后台前端，全量实现 UX 交互，代码修改后更新并通过 Playwright 测试，输出规范代码且同步更新 3.WBS.json
---

# 后台前端开发规范

## 一、项目结构规范

### 1.1 目录结构

``` text
front-admin/
├── src/
│   ├── components/           # 通用组件
│   │   ├── layouts/         # 布局组件
│   │   │   └── Layout.vue
│   │   ├── FileIcon.vue     # 文件图标组件
│   │   ├── FilePreview.vue  # 文件预览组件
│   │   ├── FileUploader.vue # 文件上传组件
│   │   ├── ImageUploader.vue # 图片上传组件
│   │   └── MessageNotification.vue # 消息通知组件
│   ├── views/              # 页面组件
│   │   ├── {module}/       # 模块目录
│   │   │   ├── {Module}.vue # 主页面
│   │   │   ├── components/  #  
│   │   │   │   ├── *Dialog.vue
│   │   │   │   ├── *Panel.vue
│   │   │   │   ├── *Table.vue
│   │   │   │   ├── *Tree.vue
│   │   │   │   └── ...
│   │   │   └── style/       # 模块样式
│   ├── router/             # 路由配置
│   ├── utils/              # 工具函数
│   ├── App.vue
│   └── main.js
├── tests/                  # Playwright 测试
├── vite.config.js          # Vite 配置
└── package.json
```

### 1.2 模块目录结构

每个业务模块应包含：

``` text
views/{module}/
├── {Module}.vue              # 主页面组件
├── components/               # 子组件
│   ├── *EditDialog.vue      # 编辑对话框
│   ├── *DetailView.vue      # 详情视图
│   ├── *FilterPanel.vue     # 筛选面板
│   ├── *SortDialog.vue      # 排序设置
│   ├── *FieldSettings.vue   # 字段设置
│   ├── *ImportDialog.vue    # 导入对话框
│   ├── *Table.vue           # 表格组件
│   ├── *Tree.vue            # 树形组件
│   └── ...
└── style/
    └── {module}.css          # 模块样式
```

## 二、命名规范

### 2.1 文件命名

| 类型 | 规范 | 示例 |
|------|------|------|
| Vue 组件 | PascalCase | `UserEditDialog.vue` |
| 工具文件 | kebab-case | `file-utils.js` |
| 样式文件 | kebab-case | `admin-user.css` |

### 2.2 变量与函数

| 类型 | 规范 | 示例 |
|------|------|------|
| 响应式数据 | camelCase | `tableData`, `loading` |
| Props | camelCase | `visible`, `userId` |
| 方法名 | camelCase | `handleAdd`, `onNodeClick` |
| 计算属性 | camelCase | `dialogVisible`, `isDisabled` |
| 常量 | UPPER_SNAKE_CASE | `MAX_FILE_SIZE` |
| CSS 类名 | kebab-case | `.form-row`, `.cell-actions` |

### 2.3 API 路径

### 接口命名及设计规范

- 格式：`/{模块名}/{方法名}`
- 命名：kebab-case，动词在前
- 所有接口都要以动词开头，如get、post、put、delete等
- 每个模块下的接口命名都要以模块名开头，如user/get-list、user/create、user/update、user/delete等
- **所有的请求都用 POST 方法**
- 示例：`/admin/organization/get-user-list`

### 2.4 字段命名

| 场景 | 规范 | 示例 |
|------|------|------|
| 前端变量 | camelCase | `userName`, `createTime` |
| 后端字段 | snake_case | `user_name`, `create_time` |
| API 请求 | snake_case | `{ user_name: "xxx" }` |
| API 响应 | snake_case | `{ user_name: "xxx" }` |

> **注意**：`request.js` 已自动处理 camelCase ↔ snake_case 转换

## 四、Playwright 测试规范

### 4.1 测试文件结构

每次测试前，根据最新代码更新测试用例。

``` text
tests/
├── {module}.spec.js       # 模块测试
```

## 五、最佳实践

### 5.1 性能优化

1. 使用 `v-show` 代替 `v-if` 频繁切换
2. 使用 `computed` 缓存复杂计算
3. 合理使用 `watch` 和 `watchEffect`
4. 列表使用 `row-key` 提升渲染性能

### 5.2 验收规范

1. 代码要通过eslint测试，符合vue3规范
2. 代码要通过playwright测试，符合功能需求
