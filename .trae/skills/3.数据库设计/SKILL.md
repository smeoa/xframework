---
name: 数据库设计
description: 基于 3.WBS.json 和现有代码，用 PostgreSQL 设计数据库表结构，全量实现数据库设计规范，输出规范代码且同步更新 3.WBS.json
---

# 技能：数据库设计

## 1. 功能描述

**仅处理3.WBS.json中用户指定WBS编号的单个数据库设计任务**，生成对应的表结构并追加到5.DB.md和6.DB.sql中。不处理其他任何任务，不修改任何其他文档内容。

## 2. 输入输出

- **必选输入参数**：`WBS任务编号`（如：WBS-DB-1-001）
- **只读输入**：`3.WBS.json`（仅读取指定WBS编号的任务内容）
- **可写输出1**：`3.WBS.json`（仅将指定DB任务的状态从"未开始"改为"已完成"）
- **可写输出2**：`5.DB.md`（仅追加指定表的设计内容，原有表结构完全保留）
- **可写输出3**：`6.DB.sql`（仅追加指定表的SQL脚本，原有SQL完全保留）
- **绝对禁止**：修改DB中已存在的其他表结构、修改前端/API相关任务、删除任何内容

## 3. 执行步骤（AI严格按顺序执行）

### 步骤1：参数校验与文件读取

1. 确认用户提供了有效的WBS任务编号（格式：WBS-DB-X-XXX）
2. 读取`3.WBS.json`文件，**仅提取指定WBS编号的任务内容**
3. 检查该任务状态是否为"未开始"，如果已是"已完成"则直接返回"任务已完成"
4. 检查`5.DB.md`和`6.DB.sql`是否存在，不存在则创建初始结构；存在则读取原有内容，**不做任何修改**

### 步骤2：单表设计（仅处理指定DB任务）

对提取的单个数据库设计任务，生成以下内容：

- 表结构定义（含通用字段+业务字段）
- 约束与索引设计
- 对应的PostgreSQL SQL脚本
- 实体关系图片段（仅涉及该表）

严格遵循PostgreSQL V3.0设计规范，通用字段顺序固定。

### 步骤3：增量更新文件

1. **原子更新WBS**：仅修改`3.WBS.json`中指定WBS编号任务的`status`字段为"已完成"，其他所有任务完全不变
2. **追加模式写入DB.md**：将生成的指定表设计内容添加到`5.DB.md`文件末尾，原有表结构完全保留
3. **追加模式写入DB.sql**：将生成的指定表SQL脚本添加到`6.DB.sql`文件末尾，原有SQL完全保留
4. 不修改任何其他文件或内容

## 4. 标准输出模板（单表追加）

### 4.1 5.DB.md追加内容

```markdown
---
## X. [表名]（[表说明]）
### X.1 表结构
| 字段名 | 数据类型 | 约束条件 | 说明 |
|--------|----------|----------|------|
| id | BIGINT GENERATED ALWAYS AS IDENTITY | PRIMARY KEY | 内部主键 |
| uuid | UUID | NOT NULL DEFAULT gen_random_uuid() | 外部唯一标识 |
| [业务字段1] | [类型] | [约束] | [说明] |
| [业务字段2] | [类型] | [约束] | [说明] |
| create_by | BIGINT | NOT NULL DEFAULT 0 | 创建人ID |
| update_by | BIGINT | NOT NULL DEFAULT 0 | 更新人ID |
| delete_by | BIGINT | DEFAULT NULL | 删除人ID |
| create_time | TIMESTAMP(3) WITH TIME ZONE | NOT NULL DEFAULT CURRENT_TIMESTAMP(3) | 创建时间 |
| update_time | TIMESTAMP(3) WITH TIME ZONE | NOT NULL DEFAULT CURRENT_TIMESTAMP(3) | 更新时间 |
| delete_time | TIMESTAMP(3) WITH TIME ZONE | DEFAULT NULL | 删除时间 |
| is_deleted | SMALLINT | NOT NULL DEFAULT 0 CHECK (is_deleted IN (0, 1)) | 逻辑删除标志 |
| remark | VARCHAR(500) | DEFAULT NULL | 备注 |

### X.2 索引设计
| 索引名称 | 索引类型 | 包含字段 | 说明 |
|----------|----------|----------|------|
| idx_[表名]_[字段1] | B树 | [字段1] | [说明] |
| idx_[表名]_[字段1]_[字段2] | B树 | [字段1,字段2] | [说明] |
```

### 4.2 6.DB.sql追加内容

```sql
-- =============================================
-- WBS-DB-X-001: [任务名称]
-- 创建时间: [YYYY-MM-DD]
-- =============================================

-- 创建表
CREATE TABLE IF NOT EXISTS [表名] (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    uuid UUID NOT NULL DEFAULT gen_random_uuid(),
    [业务字段1] [类型] [约束] COMMENT '[说明]',
    [业务字段2] [类型] [约束] COMMENT '[说明]',
    create_by BIGINT NOT NULL DEFAULT 0 COMMENT '创建人ID',
    update_by BIGINT NOT NULL DEFAULT 0 COMMENT '更新人ID',
    delete_by BIGINT DEFAULT NULL COMMENT '删除人ID',
    create_time TIMESTAMP(3) WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
    update_time TIMESTAMP(3) WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '更新时间',
    delete_time TIMESTAMP(3) WITH TIME ZONE DEFAULT NULL COMMENT '删除时间',
    is_deleted SMALLINT NOT NULL DEFAULT 0 CHECK (is_deleted IN (0, 1)) COMMENT '逻辑删除标志',
    remark VARCHAR(500) DEFAULT NULL COMMENT '备注'
) COMMENT '[表说明]';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_[表名]_[字段1] ON [表名] ([字段1]);
CREATE INDEX IF NOT EXISTS idx_[表名]_[字段1]_[字段2] ON [表名] ([字段1], [字段2]);

-- 创建更新时间触发器
CREATE TRIGGER trigger_[表名]_update_time
BEFORE UPDATE ON [表名]
FOR EACH ROW EXECUTE FUNCTION update_update_time();
```

## 5. AI执行铁律（违反视为错误）

1. **仅处理指定WBS编号**：绝对不处理其他任何编号的任务
2. **仅追加不覆盖**：DB文件只能在末尾追加内容，原有表结构和SQL一字不改
3. **仅修改指定任务状态**：WBS文件只能修改指定DB任务的`status`字段，其他所有内容完全不变
4. **不碰其他文件**：绝对不创建、修改、删除TODO、PRD、前端/API相关的任何文件
5. **通用字段严格一致**：所有表的通用字段顺序和定义必须完全相同，不得修改

---
