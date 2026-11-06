---
name: 后台API开发
description: **仅处理3.WBS.json中用户指定WBS编号的单个后台API开发任务**，基于5.DB.md的数据库设计，遵循TDD模式先写测试用例，再按Router→Controller→Model分层实现代码，输出可直接对接前端的标准化FastAPI接口，同步更新3.WBS.json中对应任务的状态。不处理其他任何任务，不修改任何无关文档和代码。
---
# 后台API开发

## 1. 功能描述

**仅处理3.WBS.json中用户指定WBS编号的单个后台API开发任务**，基于5.DB.md的数据库设计，遵循TDD模式先写测试用例，再按Router→Controller→Model分层实现代码，输出可直接对接前端的标准化FastAPI接口，同步更新3.WBS.json中对应任务的状态。不处理其他任何任务，不修改任何无关文档和代码。

## 2. 输入输出规范

- **必选输入参数**：`WBS任务编号`（格式：WBS-BA-X.X-XXX，如WBS-BA-1.1-001）
- **只读输入1**：`3.WBS.json`（仅读取指定WBS编号的任务内容）
- **只读输入2**：`5.DB.md`（仅读取对应表的结构设计）
- **可写输出1**：`admin/{module}/{module}_route.py`（仅追加对应接口路由）
- **可写输出2**：`admin/{module}/{module}_controller.py`（仅追加对应业务方法）
- **可写输出3**：`admin/models/{table}_model.py`（✅ 变更：全局Model目录，表名对应文件名，不存在则创建，存在则追加方法）
- **可写输出4**：`admin/{module}/{module}_test.py`（仅追加对应测试用例）
- **可写输出5**：`3.WBS.json`（仅将指定WBS-BA任务的状态从"未开始"改为"已完成"）
- **绝对禁止**：修改其他模块代码、修改数据库设计文件、修改WBS中其他任务、修改其他表的Model文件、删除任何内容

## 3. 执行步骤（AI严格按顺序执行）

### 步骤1：参数校验与任务解析

1. 确认用户提供的WBS编号格式正确（必须以`WBS-BA-`开头）
2. 读取`3.WBS.json`，**仅提取指定WBS编号的任务内容**
3. 检查任务状态：若为"已完成"则直接返回"任务已完成"；若不是"未开始"则返回"任务状态异常"
4. 从任务描述中提取：接口功能、对应数据库表、业务逻辑要求、验收标准
5. 读取`5.DB.md`，**仅提取对应表的字段结构**，用于生成数据模型
6. 检查目标业务模块目录是否存在，不存在则按标准目录结构创建
7. ✅ 新增：检查`admin/models/`目录是否存在，不存在则创建并初始化`__init__.py`和`base.py`
8. 读取对应表的Model文件（`admin/models/{table}_model.py`），不存在则创建基础结构；存在则读取原有内容，**不修改已有方法**

### 步骤2：编写测试用例（TDD第一步，强制先写）

根据接口功能和验收标准，在`{module}_test.py`中追加测试用例，覆盖：

- 正常场景：参数正确时的预期结果
- 异常场景：参数缺失、参数非法、权限不足、数据不存在
- 边界场景：分页边界、数据量边界、特殊字符输入

### 步骤3：分层实现功能代码

严格按Router→Controller→Model顺序实现，每层职责单一：

1. **Router层**：定义接口路由、参数校验、权限校验，调用Controller方法（无变更）
2. **Controller层**：实现业务逻辑、数据转换、异常处理，调用全局Model方法（仅导入路径变更）
3. **Model层**：✅ 变更：在`admin/models/{table}_model.py`中实现数据库CRUD操作，优先复用基础Model方法，不包含业务逻辑

### 步骤4：测试验证

1. 执行该接口对应的所有测试用例
2. 确保测试通过率100%，符合WBS任务中的验收标准
3. 验证接口文档自动生成正确，参数和响应格式符合规范

### 步骤5：增量更新与状态标记

1. 将生成的Router、Controller代码追加到对应业务模块文件末尾
2. 将生成的Model自定义方法追加到`admin/models/{table}.py`末尾（基础方法无需重复实现）
3. 更新`admin/models/__init__.py`，导出新增的Model类（若为新表）
4. **原子更新WBS**：仅修改3.WBS.json中指定WBS编号任务的`status`字段为"已完成"，其他所有内容完全不变
5. 不修改任何其他文件或内容

## 4. 目录结构与命名规范（集中式Model版）

### 4.1 标准目录结构（核心变更）

```text
admin/
├── models/                     # ✅ 新增：全局数据模型集中目录
│   ├── __init__.py             # 导出所有Model类，支持批量导入
│   ├── base_model.py                 # 项目基础Model类，封装通用配置
│   ├── org_dept_model.py             # 部门表模型（表名对应文件名：snake_case）
│   ├── sys_user_model.py             # 用户表模型
│   ├── sys_role_model.py             # 角色表模型
│   └── sys_permission_model.py       # 权限表模型
├── org_dept/                   # 业务模块：组织部门（不再包含model文件）
│   ├── org_dept_route.py       # 路由层（不变）
│   ├── org_dept_controller.py  # 控制层（不变）
│   └── org_dept_test.py        # 测试层（不变）
├── sys_user/                   # 业务模块：系统用户（不再包含model文件）
│   ├── sys_user_route.py       # 路由层（不变）
│   ├── sys_user_controller.py  # 控制层（不变）
│   └── sys_user_test.py        # 测试层（不变）
└── ... 其他业务模块            # 所有业务模块不再包含model文件
```

### 4.2 命名规范（仅Model文件名变更）

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块目录 | snake_case | `org_dept`、`sys_user` |
| 文件 | snake_case | `org_dept_route.py`、`org_dept_model.py`|
| 类名 | PascalCase | `OrgDeptController`、`DeptModel`（✅ Model类名：表名大驼峰+Model后缀） |
| 方法名 | snake_case | `get_dept_list`、`create_dept` |
| 路由路径 | kebab-case | `/admin/org-dept/get-dept-list` |
| 接口名 | 动词+名词 | `get_dept_list`、`update_dept_status` |
| 测试用例名 | test_动词_名词_场景 | `test_get_dept_list_success`、`test_create_dept_missing_name` |

## 5. 分层规范（集中式Model适配版）

### 5.1 Router层（无任何变更）

#### 5.1.1 标准结构

```python
from fastapi import APIRouter, Request, Depends
from pydantic import BaseModel, Field
from framework.core.auth import get_current_user
from .{module}_controller import {Module}Controller

router = APIRouter(prefix="/admin/{module-kebab}", tags=["后台-{模块中文名称}"])

# 请求参数模型（Pydantic，强制参数校验）
class Get{Module}ListRequest(BaseModel):
    page: int = Field(1, ge=1, description="页码")
    limit: int = Field(20, ge=1, le=100, description="每页条数")
    keyword: str = Field("", max_length=50, description="搜索关键词")
    status: int | None = Field(None, ge=0, le=1, description="状态：0-禁用，1-正常")
    sort: list[dict] = Field([], description="排序规则")

class Create{Module}Request(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="名称")
    code: str = Field(..., min_length=1, max_length=20, description="编码")
    pid: int = Field(0, ge=0, description="父级ID")
    status: int = Field(1, ge=0, le=1, description="状态")

# 接口定义
@router.post("/get-{module}-list", summary="获取{模块中文名称}列表")
async def get_{module}_list(
    request: Request,
    req: Get{Module}ListRequest,
    current_user: dict = Depends(get_current_user)  # 强制权限校验
):
    controller = {Module}Controller(request, current_user)
    return await controller.get_{module}_list(req)

@router.post("/create-{module}", summary="创建{模块中文名称}")
async def create_{module}(
    request: Request,
    req: Create{Module}Request,
    current_user: dict = Depends(get_current_user)
):
    controller = {Module}Controller(request, current_user)
    return await controller.create_{module}(req)
```

#### 5.1.2 强制规范（无变更）

- 所有接口必须使用`POST`方法
- 所有请求参数必须使用Pydantic模型校验，禁止手动`if not id`式校验
- 所有后台接口必须添加`Depends(get_current_user)`权限校验
- 接口必须添加`summary`描述，用于自动生成接口文档
- 路由前缀使用kebab-case，与模块名对应
- 禁止在Router层写任何业务逻辑，仅负责参数传递和调用Controller

### 5.2 Controller层（仅导入路径变更，逻辑完全不变）

#### 5.2.1 标准结构（仅导入语句变更）

```python
from fastapi import Request
from framework.core.controller import Controller
from admin.models import {Module}Model
import logging

logger = logging.getLogger(__name__)

class {Module}Controller(Controller):
    def __init__(self, request: Request, current_user: dict):
        super().__init__(request)
        self.current_user = current_user
        self.{module}_model = {Module}Model()  

    async def get_{module}_list(self, req):
        """获取{模块中文名称}列表"""
        try:
            # 业务逻辑：构建筛选条件
            filter_conditions = self._build_filter_conditions(req)
            
            # 调用Model层获取数据（使用方式完全不变）
            result = await self.{module}_model.get_list(
                filter=filter_conditions,
                sort=req.sort,
                page=req.page,
                limit=req.limit
            )
            
            return self.success(result)
        except Exception as e:
            logger.error(f"获取{模块中文名称}列表失败: {str(e)}", exc_info=True)
            return self.error(code=500, message="系统内部错误")

    async def create_{module}(self, req):
        """创建{模块中文名称}"""
        try:
            # 业务逻辑：唯一性校验
            exists = await self.{module}_model.exists({"code": req.code})
            if exists:
                return self.error(code=400, message=f"编码{req.code}已存在")
            
            # 业务逻辑：补充创建人信息
            data = req.dict()
            data["create_by"] = self.current_user["id"]
            data["update_by"] = self.current_user["id"]
            
            # 调用Model层创建数据（使用方式完全不变）
            id = await self.{module}_model.create(data)
            
            return self.success({"id": id})
        except Exception as e:
            logger.error(f"创建{模块中文名称}失败: {str(e)}", exc_info=True)
            return self.error(code=500, message="系统内部错误")

    def _build_filter_conditions(self, req):
        """构建筛选条件（私有方法，业务逻辑）"""
        conditions = []
        if req.keyword:
            conditions.append({"field": "name", "operator": "contains", "value": req.keyword})
        if req.status is not None:
            conditions.append({"field": "status", "operator": "eq", "value": req.status})
        
        return [
            {
                "group_logic": "and",
                "condition_logic": "and",
                "conditions": conditions
            }
        ]
```

#### 5.2.2 强制规范（无变更）

- 所有业务逻辑必须在Controller层实现，禁止在Router或Model层写业务逻辑
- 所有数据库操作必须通过调用Model层方法实现，禁止直接写SQL
- 必须捕获所有异常，记录详细日志（包含`exc_info=True`），返回统一错误格式
- 敏感错误信息（如数据库错误）不返回给前端，统一返回"系统内部错误"
- 私有方法以下划线开头，用于封装可复用的业务逻辑
- 必须使用`current_user`获取当前用户信息，禁止从其他地方获取

### 5.3 Model层（✅ 集中式重构，核心变更）

#### 5.3.1 基础Model类（`admin/models/base_model.py`，全局唯一）

```python
from framework.core.model import Model

class BaseModel(Model):
    """项目基础Model类，所有业务Model继承自此类
    封装全局通用配置，避免每个Model重复定义
    """
    # 全局软删除配置
    soft_delete = True
    soft_delete_field = "is_deleted"
    soft_delete_value = 1
    
    # 全局通用外键关联（所有表自动关联创建人/更新人）
    foreign_key_fields = [
        {
            "field": "create_by",
            "ref_table": "sys_user",
            "ref_field": "id",
            "alias_field": "create_user_name",
            "display_field": "name",
        },
        {
            "field": "update_by",
            "ref_table": "sys_user",
            "ref_field": "id",
            "alias_field": "update_user_name",
            "display_field": "name",
        }
    ]
```

#### 5.3.2 业务Model标准结构（`admin/models/{table}_model.py`）

```python
from .base_model import BaseModel

class {Module}Model(BaseModel):
    """{模块中文名称}表模型"""
    # 表名（与数据库完全一致，snake_case）
    table_name = "{module_name}"
    
    # 模块特有外键关联（全局通用的已在BaseModel中定义）
    foreign_key_fields = [
        {
            "field": "pid",
            "ref_table": "org_dept",
            "ref_field": "id",
            "alias_field": "parent_name",
            "display_field": "name",
        },
        {
            "field": "leader_id",
            "ref_table": "sys_user",
            "ref_field": "id",
            "alias_field": "leader_name",
            "display_field": "name",
        }
    ]
    
    # 模块特有配置
    jsonb_fields = ["ext_info"]
    default_sort = [
        {"field": "sort", "direction": "asc"},
        {"field": "id", "direction": "desc"}
    ]

    # 自定义数据库操作方法（仅包含SQL逻辑，无业务逻辑）
    # 基础方法已在BaseModel和framework中实现，无需重复编写
    async def get_children_by_pid(self, pid: int):
        """根据父ID获取所有子节点"""
        return await self.get_list(filter=[
            {"field": "pid", "operator": "eq", "value": pid}
        ])
```

#### 5.3.3 全局导出文件（`admin/models/__init__.py`）

```python
# 导出所有业务Model类，支持批量导入
from .org_dept import DeptModel
from .sys_user import UserModel
from .sys_role import RoleModel
from .sys_permission import PermissionModel

__all__ = [
    "DeptModel",
    "UserModel",
    "RoleModel",
    "PermissionModel"
]
```

#### 5.3.4 基础方法（自动继承，无需重复实现，无变更）

| 方法名 | 功能 | 参数 | 返回值 |
|--------|------|------|--------|
| `get_by_id(id)` | 根据ID查询单条数据 | id: 主键ID | 数据字典或None |
| `get_list(filter, sort, page, limit)` | 分页查询列表 | filter: 筛选条件<br>sort: 排序规则<br>page: 页码<br>limit: 每页条数 | {"items": [...], "total": 总条数, "page": 页码, "limit": 每页条数} |
| `create(data)` | 创建单条数据 | data: 数据字典 | 新数据ID |
| `update_by_id(id, data)` | 根据ID更新数据 | id: 主键ID<br>data: 更新数据字典 | 受影响行数 |
| `delete_by_id(id)` | 软删除单条数据 | id: 主键ID | 受影响行数 |
| `exists(condition)` | 判断数据是否存在 | condition: 条件字典 | bool |
| `batch_create(data_list)` | 批量创建数据 | data_list: 数据字典列表 | 新增数据ID列表 |
| `batch_delete(ids)` | 批量软删除数据 | ids: 主键ID列表 | 受影响行数 |

#### 5.3.5 强制规范（仅新增集中式相关要求）

- Model层仅负责数据库CRUD操作，禁止包含任何业务逻辑
- 所有业务Model必须继承自`BaseModel`，复用全局配置
- 优先使用基础Model提供的方法，无需重复实现
- 若基础方法无法满足，可在对应表的Model文件中添加自定义方法，但必须仅包含数据库操作
- 所有数据库操作必须使用框架提供的ORM，禁止直接写原生SQL（特殊情况需标注）
- 必须配置`soft_delete=True`，使用逻辑删除，禁止物理删除
- 外键关联必须在`foreign_key_fields`中配置，自动关联查询
- ✅ 新增：新表创建时，必须在`admin/models/__init__.py`中导出对应的Model类

## 6. TDD测试规范（无任何变更）

### 6.1 测试文件结构

```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# 测试用例分组
class Test{Module}API:
    # 测试前置：登录获取token
    @pytest.fixture(autouse=True)
    def setup(self):
        # 登录获取管理员token
        response = client.post("/admin/auth/login", json={"username": "admin", "password": "123456"})
        self.token = response.json()["data"]["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    # 正常场景测试
    def test_get_{module}_list_success(self):
        """测试获取{模块中文名称}列表成功"""
        response = client.post(
            "/admin/{module}/get-{module}-list",
            json={"page": 1, "limit": 20},
            headers=self.headers
        )
        assert response.status_code == 200
        assert response.json()["code"] == 200
        assert "items" in response.json()["data"]
        assert "total" in response.json()["data"]

    # 异常场景测试
    def test_create_{module}_missing_name(self):
        """测试创建{模块中文名称}缺少名称参数"""
        response = client.post(
            "/admin/{module}/create-{module}",
            json={"code": "test001"},  # 缺少name字段
            headers=self.headers
        )
        assert response.status_code == 422  # Pydantic校验失败返回422
        assert response.json()["code"] == 422

    def test_create_{module}_duplicate_code(self):
        """测试创建{模块中文名称}编码重复"""
        # 先创建一个测试数据
        client.post(
            "/admin/{module}/create-{module}",
            json={"name": "测试部门", "code": "test001"},
            headers=self.headers
        )
        
        # 再次创建相同编码
        response = client.post(
            "/admin/{module}/create-{module}",
            json={"name": "测试部门2", "code": "test001"},
            headers=self.headers
        )
        assert response.status_code == 200
        assert response.json()["code"] == 400
        assert "已存在" in response.json()["message"]
```

### 6.2 强制测试覆盖要求（无变更）

- 每个接口至少覆盖3类场景：正常场景、参数异常场景、业务异常场景
- 测试用例必须独立，不依赖其他用例的执行结果
- 所有断言必须明确，禁止使用`assert True`等无效断言
- 测试数据必须在测试结束后清理，避免污染数据库
- 测试用例命名必须清晰表达测试场景

## 7. 统一响应与错误码规范（无任何变更）

### 7.1 统一响应格式（强制）

```json
{
  "code": 200,
  "message": "success",
  "data": {
    // 业务数据
  }
}
```

### 7.2 标准错误码体系

| 错误码 | 含义 | 示例 |
|--------|------|------|
| 200 | 成功 | 操作成功 |
| 400 | 请求参数错误 | 参数缺失、参数格式错误 |
| 401 | 未授权 | 未登录、token过期 |
| 403 | 权限不足 | 无操作权限 |
| 404 | 资源不存在 | 数据不存在、接口不存在 |
| 409 | 资源冲突 | 编码重复、名称重复 |
| 500 | 系统内部错误 | 数据库错误、第三方服务错误 |

### 7.3 响应方法（Controller基类提供）

```python
# 成功响应
return self.success(data={"id": 1})

# 错误响应
return self.error(code=400, message="编码已存在")
return self.error(code=404, message="部门不存在")
```

## 8. 接口文档规范（无任何变更）

- 所有接口自动生成OpenAPI文档，访问地址：`http://localhost:8000/docs`
- 接口`summary`必须简洁明了，说明接口功能
- Pydantic模型的`Field`必须添加`description`，说明参数含义
- 复杂响应格式需在接口注释中说明
- 接口文档必须包含请求示例和响应示例

## 9. 最佳实践与避坑指南（新增集中式Model相关）

1. **分层严格分离**：Router只做路由和参数校验，Controller只做业务逻辑，Model只做数据库操作
2. **参数校验必须使用Pydantic**：禁止手动校验参数，避免遗漏和不一致
3. **异常必须捕获并记录**：所有可能抛出异常的地方都要捕获，记录详细日志
4. **敏感信息不返回**：密码、身份证号等敏感字段禁止返回给前端
5. **批量操作限制**：批量删除、批量导入等操作必须限制单次操作数量（如最多100条）
6. **避免N+1查询**：使用外键关联配置自动关联查询，禁止循环查询
7. **事务管理**：涉及多表操作的业务必须使用事务，保证数据一致性
8. **代码复用**：可复用的业务逻辑封装为Controller的私有方法，可复用的数据库操作封装为对应Model的方法
9. **禁止硬编码**：状态码、枚举值等禁止硬编码，使用常量或配置文件
10. **幂等性设计**：创建、更新等操作必须保证幂等性，避免重复提交
11. ✅ 新增：**避免循环导入**：不要在Model中导入Controller或其他业务代码；互相依赖的Model使用方法内部延迟导入

    ```python
    # 错误：顶部导入导致循环依赖
    from .user import UserModel
    
    class DeptModel(BaseModel):
        async def get_leader(self, dept_id):
            user_model = UserModel()
            # ...
    
    # 正确：方法内部延迟导入
    class DeptModel(BaseModel):
        async def get_leader(self, dept_id):
            from .user import UserModel
            user_model = UserModel()
            # ...
    ```