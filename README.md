# xf 开发模板

基于 XAI Framework 的干净开发模板：框架 + 基础模块 + 完整 demo CRUD 样板，用于快速开发新业务功能。

## 项目结构

```
admin/        FastAPI 后台 API（端口 8000）
  demo/       demo CRUD 样板模块（新模块复制改表名即可）
site/         FastAPI 前台 API（端口 8100，含通用上传示例）
framework/    核心框架（Model / Controller / 认证 / 权限 / 日志）
front-admin/  Vue3 + Element Plus 后台前端（vite，端口 3000）
front-site/   Nuxt4 前台站点（含 useApi 调用示例）
INIT.SQL      PostgreSQL 初始化脚本（仅框架骨架数据）
```

## 快速开始

### 1. 初始化数据库

```powershell
$env:PGPASSWORD='admin'
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h 127.0.0.1 -U postgres -c "CREATE DATABASE xf"
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h 127.0.0.1 -U postgres -d xf -f INIT.SQL
```

默认账号：`admin / admin123`

### 2. 启动后台 API

```powershell
cd admin
python main.py          # http://localhost:8000，接口文档 /docs
```

配置在 `admin/.env`（数据库连接、JWT_SECRET、七牛云等，密钥一律不入库）。

### 3. 启动后台前端

```powershell
cd front-admin
npm install
npm run dev             # http://localhost:3000
```

### 4. 启动前台 API 与站点（可选）

```powershell
cd site
python -m uvicorn main:app --port 8100     # 前台 API

cd front-site
pnpm install
pnpm dev              # http://localhost:3000（如占用用 PORT 指定）
```

## 开发新模块

### 后端（admin）

复制 `admin/demo/` 四件套，改表名与字段：

```
demo.sql              建表语句（标准列：id / data_id / create_by / update_by / create_time / update_time / is_deleted / delete_time / delete_by / remark）
demo_model.py         Model 层（分页、筛选、软删）
demo_controller.py    Controller 层（success / error 统一响应）
demo_route.py         路由（前缀 /admin/<模块>/，自动注册，目录名须与文件名一致）
```

约定：
- **所有接口 POST**，kebab-case 路径（如 `get-demo-list`）
- 权限通过 `Depends(require_permission("demo:list"))` 声明，权限码入库 `x_permission`
- 软删除：`is_deleted = 1`；`destroy-*` 为物理删除

### 前端（front-admin）

复制 `src/views/demo/Demo.vue` 改 API 路径；在 `src/router/index.js` 加路由（`meta.permission` 对应权限码）。
- API 一律走 `@/utils/request`（自动处理 camelCase ↔ snake_case，勿直接用 fetch）
- 按钮级权限：`v-permission="'demo:create'"`

菜单与权限配置写入 `x_menu` / `x_permission` 表后生效。

### 前台站点（front-site）

Nuxt4 + SSG（prerender），页面放 `app/pages/`，接口调用用 `app/composables/useApi.ts`。

## 规范文档

- `Nuxt4 官网开发 SEO 规范.md` — 前台开发规范
- `UI规范.md` — UI 规范
- `.trae/rules/project_rules.md` — 项目规则（编码约定）
