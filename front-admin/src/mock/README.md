# Mock 数据模块化控制

## 快速开始

### 1. 配置模块开关

编辑 `src/mock/index.js`：

```javascript
const mockModules = [
  ["user", true], // 使用 MOCK 数据
  ["organization", true], // 使用 MOCK 数据
  ["menu", true], // 使用 MOCK 数据
  ["notification", true], // 使用 MOCK 数据
  ["subform", true], // 使用 MOCK 数据
];
```

### 2. 启动开发服务器

```bash
npm run dev
```

启动时显示模块配置状态：

```
[Mock] 模块配置已加载: user, organization, menu, notification, subform
[Mock] ✓ 已加载 user 模块 (1 个接口)
[Mock] ✓ 已加载 organization 模块 (23 个接口)
[Mock] ✓ 已加载 menu 模块 (11 个接口)
[Mock] 总计注册 48 个接口
[Mock] 中间件已注册（从 src/mock/modules/ 加载）
```

### 3. 测试请求

请求会自动根据配置路由：

- **MOCK 启用**：返回本地 Mock 数据
- **MOCK 禁用**：请求转发到 `http://localhost:8000`

## 配置说明

### 布尔值含义

| 值      | 含义      | 行为                     |
| ------- | --------- | ------------------------ |
| `true`  | 启用 MOCK | 拦截请求，返回 Mock 数据 |
| `false` | 禁用 MOCK | 转发请求到真实后端       |

### 路径匹配规则

中间件通过 URL 路径匹配模块：

```javascript
// 匹配逻辑：path.includes(`/${moduleName}/`)
"/admin/user/list"; // 匹配 user
"/admin/menu/get-menu-tree"; // 匹配 menu
"/admin/organization/get-user-list"; // 匹配 organization
```

### 请求日志

```
[Mock] ✓ POST /admin/organization/get-user-list (0ms) [organization]
[Mock] ✓ POST /admin/menu/get-menu-tree (0ms) [menu]
```

## 添加新的 Mock 数据

### 1. 创建模块文件

在 `src/mock/modules/` 创建新文件：

```javascript
// src/mock/modules/example.js
export default [
  {
    url: "/admin/example/list",
    method: "get",
    response: () => {
      return {
        code: 200,
        message: "success",
        data: {
          list: [{ id: 1, name: "示例数据" }],
          total: 1,
        },
      };
    },
  },
];
```

### 2. 注册模块

在 `src/mock/index.js` 中：

```javascript
// 1. 导入新模块
import exampleMock from "./modules/example";

// 2. 添加到 mockDataMap
const mockDataMap = {
  // ... 现有模块
  example: exampleMock,
};

// 3. 添加到 mockModules 数组
["example", true]; // 启用 MOCK
```

### 3. 重启服务器

配置修改后 Vite 会自动重启。

## Mock 数据格式

### 标准响应格式

```javascript
{
  code: 200,           // 状态码
  message: 'success',  // 消息
  data: { ... }        // 数据
}
```

### 动态响应

支持函数返回动态数据：

```javascript
response: (req) => {
  const { page = 1, limit = 20 } = req.body || {};
  return {
    code: 200,
    data: {
      items: [...],
      total: 100
    }
  };
}
```

## 常见问题

### Q: 配置修改后不生效？

**A**: Vite 会自动检测配置变化并重启服务器。如果未重启，请手动重启。

### Q: 请求返回 404？

**A**: 检查以下几点：

1. 模块是否启用 MOCK
2. URL 路径是否匹配模块名
3. Mock 数据文件是否包含该接口

### Q: 如何调试？

**A**: 打开浏览器开发者工具，查看 Network 面板：

- MOCK 请求：状态码 200，响应来自 `localhost:3000`
- 真实请求：状态码可能不同，响应来自 `localhost:8000`

### Q: 如何临时禁用所有 MOCK？

**A**: 将所有模块设置为 `false`：

```javascript
const mockModules = [
  ["user", false],
  ["organization", false],
  ["menu", false],
  ["notification", false],
  ["subform", false],
];
```

## 架构说明

```
请求流程：
┌──────────────┐
│   前端请求    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Vite 服务器  │
└──────┬───────┘
       │
       ▼
┌──────────────────────────┐
│  Mock 中间件 (vite.config.js) │
│  - 读取 src/mock/index.js 配置   │
│  - 使用 createRequire 加载模块   │
└──────┬───────────────────┘
       │
   ┌───┴───┐
   │       │
   ▼       ▼
┌──────┐ ┌──────────┐
│MOCK │ │真实后端   │
└──────┘ └──────────┘
```

## 文件结构

```
src/mock/
├── index.js           # 模块配置开关
├── README.md          # 本文档
└── modules/           # Mock 数据模块
    ├── user.js
    ├── organization.js
    ├── menu.js
    ├── notification.js
    └── subform.js
```

## 相关文件

- **vite.config.js**: Mock 中间件实现，动态加载 `src/mock/modules/`
- **src/mock/index.js**: 模块开关配置
- **src/utils/request.js**: Axios 请求配置
