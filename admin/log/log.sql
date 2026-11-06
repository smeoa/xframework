-- ============================================================
-- 系统日志表 x_log
-- 本文件为唯一事实来源，全部语句均可重复执行（幂等）
-- 执行方式：asyncpg conn.execute(整个文件内容)
-- 写入方：framework/core/log_db.py（按 .env 的 LOG_LEVEL 过滤后异步批量落库）
-- ============================================================

-- ------------------------------------------------------------
-- 1. 主表 x_log
--    风格与既有表保持一致：id 自增 bigint + data_id uuid + 审计列 + 软删除列
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS x_log (
    id             BIGSERIAL PRIMARY KEY,
    data_id        UUID DEFAULT gen_random_uuid(),

    level          VARCHAR(16)  NOT NULL,     -- DEBUG/INFO/WARNING/ERROR/CRITICAL
    logger         VARCHAR(128),              -- logger 名称
    module         VARCHAR(128),              -- 模块名
    func           VARCHAR(128),              -- 函数名
    line           INTEGER,                   -- 行号
    message        TEXT,                      -- 日志正文
    exc_info       TEXT,                      -- 异常堆栈（有则落）

    request_id     VARCHAR(64),               -- 一次请求的串联ID（中间件生成）
    request_path   VARCHAR(255),
    request_method VARCHAR(16),
    client_ip      VARCHAR(64),
    user_id        BIGINT,                    -- 产生日志的用户（能取到才填）

    remark         TEXT,                      -- 备注

    create_time    TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    create_by      BIGINT DEFAULT 0,
    update_by      BIGINT DEFAULT 0,
    update_time    TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_deleted     SMALLINT DEFAULT 0,
    delete_time    TIMESTAMP WITHOUT TIME ZONE,
    delete_by      BIGINT DEFAULT 0
);

-- ------------------------------------------------------------
-- 2. 索引：按级别/时间/logger/请求ID 查都是常见诉求
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_x_log_level       ON x_log (level);
CREATE INDEX IF NOT EXISTS idx_x_log_create_time ON x_log (create_time);
CREATE INDEX IF NOT EXISTS idx_x_log_logger      ON x_log (logger);
CREATE INDEX IF NOT EXISTS idx_x_log_request_id  ON x_log (request_id);

-- ------------------------------------------------------------
-- 3. 兼容既有库：补齐后续新增列（重复执行安全）
-- ------------------------------------------------------------
ALTER TABLE x_log ADD COLUMN IF NOT EXISTS exc_info TEXT;
ALTER TABLE x_log ADD COLUMN IF NOT EXISTS request_id VARCHAR(64);

-- 审计列（框架 Model.update 会写 update_by/update_time，缺了会导致删除/批量删除报错）
ALTER TABLE x_log ADD COLUMN IF NOT EXISTS create_by BIGINT DEFAULT 0;
ALTER TABLE x_log ADD COLUMN IF NOT EXISTS update_by BIGINT DEFAULT 0;
ALTER TABLE x_log ADD COLUMN IF NOT EXISTS update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE x_log ADD COLUMN IF NOT EXISTS remark TEXT;
COMMENT ON COLUMN x_log.remark IS '备注';
