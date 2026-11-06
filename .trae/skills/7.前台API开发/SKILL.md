---
name: 前台API开发
description: **仅处理 3.WBS.json 中用户指定 WBS 编号的单个前台 API 开发任务**，基于 5.DB.md 的数据库设计，在 site_api/ 内按 Router→Controller→Model 分层实现面向官网前台的公开接口（内容读取、表单、订阅、上传、预约、通知、录入），遵循 TDD 先写用例，输出可直接被 front-site 的 useApi 调用的标准化接口，并同步更新 3.WBS.json 中该任务状态。不处理其他任务，不修改无关文件。
---
# 前台API开发

## 1. 功能描述

**仅处理 `3.WBS.json` 中用户指定编号的单个前台 API 任务（`WBS-BA-*`）**，为官网前台 `front-site/` 提供公开接口。不涉及后台管理接口，不改动 `admin/` 既有模块。

前台 API 的特征：**无登录鉴权、全部 POST、供 SSG/ISR 构建期与浏览器直连**，因此接口必须在无 Cookie、无 Token、公网可达的条件下返回稳定结果。

## 2. 输入输出规范

- **必选输入参数**：`WBS任务编号`（格式：`WBS-BA-X.X-XXX`）
- **只读输入1**：`3.WBS.json`（仅读取指定编号的任务内容与依赖）
- **只读输入2**：`5.DB.md`（仅读取本任务涉及的表的字段、约束、索引）
- **只读输入3**：`2.PRD.md`（对应表单 / 页面 / 数据章节）
- **只读输入4**：`front-site/app/composables/useApi.ts`（请求与命名约定）
- **可写输出1**：`site_api/{module}/{module}_route.py`（追加路由）
- **可写输出2**：`site_api/{module}/{module}_controller.py`（追加业务方法）
- **可写输出3**：`site_api/models/{table}_model.py`（追加 Model，不存在则新建）
- **可写输出4**：`site_api/{module}/{module}_test.py`（追加测试用例）
- **可写输出5**：`3.WBS.json`（仅将该 `wbs_id` 的 `status` 改为"已完成"）
- **绝对禁止**：修改 `admin/` 下既有模块、修改 `5.DB.md` / `6.DB.sql`、修改其他 WBS 任务、修改 `front-site/` 业务页面（联调所需的最小请求适配除外）、删除任何内容

## 3. 执行步骤（严格按顺序）

### 步骤1：任务解析与现状检查

1. 校验编号以 `WBS-BA-` 开头；从 `3.WBS.json` 只取该任务
2. 状态为"已完成"直接返回"任务已完成"；非"未开始"返回"任务状态异常"
3. 从任务描述提取：接口清单、涉及表、字段级校验规则、验收标准
4. 从 `5.DB.md` 只取涉及表的字段与约束，**字段名以 DB 为准**
5. 检查 `site_api/` 是否存在；不存在则按第 4 节初始化（含 `main.py`、`models/__init__.py`、`base_model.py`）

### 步骤2：先写测试用例（TDD 第一步，强制）

在 `site_api/{module}/{module}_test.py` 追加用例，覆盖：

- 正常：合法入参返回 200 且落库字段正确
- 参数异常：必填缺失、格式非法、越界（长度 / 枚举 / 附件大小与类型）返回 400，且错误定位到具体字段
- 业务异常：资源不存在、slug 重复、token 过期或已使用、幂等重复提交
- 边界：空关键词搜索、分页越界、超长文本、大小写不同的邮箱

### 步骤3：分层实现

1. **Route**：`APIRouter(prefix="/front/{kebab-module}")`，Pydantic 请求模型 + `summary`，调用 Controller；**不挂载 `Depends(require_login)`**
2. **Controller**：校验、业务编排、事务、异常捕获（`logger.error(..., exc_info=True)`），统一 `self.success()` / `self.error()`
3. **Model**：只做 SQL/CRUD，继承 `site_api/models/base_model.py` 的 `SiteBaseModel`（`db_prefix = ""`，因 site 表无 `x_` 前缀），禁止在 Model 写业务判断

### 步骤4：测试与联调验证

1. `pytest site_api/{module}/{module}_test.py` 全绿
2. 启动 `site_api`（默认 8100），用真实 `site` 库跑通每个接口
3. 前台侧验证：`front-site` 指向该服务完成构建或页面请求，表单 / 列表 / 详情能取到真实数据
4. 写库类接口必须复查数据库落库结果，测试数据随后清理

### 步骤5：原子更新 WBS

仅把该编号的 `status` 改为"已完成"，其余字段与任务一字不改；改完二次 `JSON.parse` 校验。

## 4. 目录结构规范

```text
site_api/
├── main.py                      # 独立 FastAPI 应用（与 admin/main.py 分离）
├── models/
│   ├── __init__.py              # 导出全部 Model
│   ├── base_model.py            # SiteBaseModel：db_prefix = ""
│   ├── product_model.py         # 表名对应文件（snake_case）
│   ├── post_model.py
│   └── lead_model.py
├── content/                     # 内容读取：类目 / 产品 / 文章 / 案例 / FAQ / 搜索
│   ├── content_route.py
│   ├── content_controller.py
│   └── content_test.py
├── form/                        # F01–F09 表单提交
├── newsletter/                  # 双确认订阅与退订
├── upload/                      # 附件上传与下载
├── appointment/                 # 预约配置与回执
├── notify/                      # 邮件模板渲染与 webhook 分流
└── seo/                         # 文案与 SEO 清单、内容录入
```

- `main.py` 只注册 `site_api` 路由、CORS、异常处理与 `/health`，**不得复用 admin 的登录依赖**
- 端口读 `SITE_API_PORT`（默认 8100），CORS 白名单读 `SITE_CORS_ORIGINS`
- 启动方式：`uvicorn site_api.main:app --port 8100`

## 5. 命名规范

| 类型 | 规范 | 示例 |
|---|---|---|
| 模块目录 | snake_case | `content`、`newsletter` |
| 文件 | `{module}_route.py` / `_controller.py` / `_test.py` | `form_route.py` |
| Model 文件 | `{table}_model.py` | `blog_posts` → `blog_post_model.py` |
| 类名 | PascalCase | `FormController`、`LeadModel` |
| 方法名 | snake_case | `submit_inquiry`、`get_product_list` |
| 路由路径 | `/front/{kebab-module}/{动词-名词}` | `/front/form/submit-inquiry` |
| 测试用例 | `test_动词_名词_场景` | `test_submit_inquiry_missing_email` |
| 请求/响应字段 | snake_case（前端自动转 camelCase） | `work_email` ↔ `workEmail` |

## 6. 分层规范

### 6.1 Route 层

```python
router = APIRouter(prefix="/front/form", tags=["前台-表单"])

class SubmitInquiryRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120, description="姓名")
    work_email: EmailStr = Field(..., description="工作邮箱")
    message: str = Field(..., min_length=20, max_length=5000, description="需求描述")
    consent: bool = Field(..., description="隐私政策同意")

@router.post("/submit-inquiry", summary="提交 F01 询盘")
async def submit_inquiry(request: Request, req: SubmitInquiryRequest):
    return await FormController(request).submit_inquiry(req)
```

强制项：

- 所有业务接口必须 `POST`；`/health` 可用 GET
- 参数校验一律 Pydantic，禁止手写 `if not x` 式校验
- 前台接口不得添加 `Depends(get_current_user)` / `require_login`
- 每个接口必须有 `summary`，每个 `Field` 必须有 `description`

### 6.2 Controller 层

- 业务逻辑与事务在此层；跨表写操作必须使用事务
- 异常必须捕获并 `logger.error(..., exc_info=True)`，对外只返回可读文案，禁止暴露 SQL / 堆栈
- 字段级校验失败返回 `400` 且 `data` 为 `{字段名: 提示}`，前端据此高亮
- 私有方法以下划线开头

### 6.3 Model 层

```python
class SiteBaseModel(Model):
    """前台站点表模型基类：site 库新表无 x_ 前缀"""
    def __init__(self, table_name: str):
        super().__init__(table_name)
        self.db_prefix = ""
```

- 只写 CRUD 与查询构造，禁止业务判断
- 一律逻辑删除（`is_deleted = 0`），禁止物理删除
- 列表查询避免 N+1，关联字段用 JOIN 或批量 `IN`
- `jsonb_fields`、`default_sort` 必须在 Model 中声明

## 7. 前台接口硬性约定

| 项 | 规定 |
|---|---|
| 请求方法 | 全部 `POST`；非 POST 返回 `405` |
| 响应信封 | `{ "code": 200, "message": "success", "data": {...} }`；错误时 HTTP 状态码 = `code` |
| 数据解包 | 前台 `useApi` 读取 `data` 作为业务数据；`data` 内字段一律 snake_case |
| 公开可读 | 仅返回已发布数据：`is_published = 1`（类目 / 产品）、`status = 'published'`（文章）、`is_deleted = 0` |
| 不编造 | 未知业务事实返回空串 / `null` / `[placeholder: ...]`，禁止虚构品牌名、年限、认证、客户名 |
| 图片占位 | 所有占位图必须使用 trae 生图链接：`https://trae-api-cn.mchost.guru/api/ide/v1/tool_text_to_image?prompt={URL编码提示词}&image_size={尺寸}`；`image_size` 仅取 `square_hd` / `square` / `portrait_4_3` / `portrait_16_9` / `landscape_4_3` / `landscape_16_9`。禁止输出空 src、`/images/placeholder.svg` 或本地占位图 |
| 图片字段 | 返回 `{src, width, height, alt}` 四要素，`alt` 必须描述画面内容，禁止空 alt |
| 分页 | 入参 `page`（≥1）/ `page_size`（1–60）；出参 `{items, total, page, page_size, total_pages}` |
| 搜索 | 关键词为空直接返回空列表，不查库；结果项含 `type` / `title` / `url` / `excerpt` |
| 幂等 | 创建类接口用 `idempotency_key`（表单编码 + 邮箱 + `client_ts` + 载荷摘要），唯一索引兜底，重复提交返回首次结果 |
| 频率限制 | 公开表单按 IP + 表单编码限流（默认 20 次/10 分钟），超限返回 `429` |
| 附件 | 扩展名白名单 + 单文件大小 + 数量上限三重校验；存储 key 只允许相对路径，拒绝绝对路径、盘符、协议头与 `..` |
| 订阅 | 双确认：未确认不入正式订阅名单；`confirm_token` 一次性，`token_expires_at` 过期即失效；退订走 token |
| 密钥 | SMTP / CRM / 邮件平台密钥只从环境变量读取，禁止写库、禁止写日志、禁止返回前端 |
| 邮件 | 模板合并字段缺失时替换为空串或占位符，禁止把 `None` / `undefined` 渲染进正文 |
| 安全 | 错误响应不含 SQL、堆栈、内网地址；上传文件名不参与路径拼接（服务端重命名） |

## 8. TDD 测试规范

- 使用 `pytest` + `fastapi.testclient.TestClient`，测试文件与模块同目录
- 每个接口至少 3 类场景：正常、参数异常、业务异常；写库接口额外覆盖幂等与约束冲突
- 用例相互独立，不依赖执行顺序；测试数据用固定前缀并在 `finally` 中清理
- 断言必须具体到状态码、`code`、字段值与数据库落库结果，禁止 `assert True`
- 测试结束校验表内无残留（例如 `leads` 计数回到基线）

## 9. 联调验收清单

- [ ] `pytest site_api/` 全部通过
- [ ] 每个接口实测返回 `code=200` 与预期 `data` 结构
- [ ] 只返回已发布 / 未删除数据
- [ ] 表单落库字段完整，埋点 7 项（`form_code` / `source_page` / `utm_*` / `referrer` / `client_ts`）可追溯
- [ ] 附件越界（类型、大小、数量）被服务端拒绝，路径穿越被拒绝
- [ ] 订阅 token 一次性、过期失效、退订可用
- [ ] 占位图均为 trae 生图链接且带 `alt` / `width` / `height`
- [ ] 前台 `front-site` 能取到真实数据并成功渲染（构建或页面实测）
- [ ] 无控制台报错、无 4xx/5xx 未处理路径
- [ ] `3.WBS.json` 仅该任务状态变更，JSON 可解析
- [ ] 临时脚本、测试数据已清理，仓库无多余文件
