-- demo 示例表：新模块开发时复制本表结构作为起点
-- 字段遵循 framework 约定：data_id 对外标识、create_by/update_by、create_time/update_time、is_deleted 软删
CREATE TABLE IF NOT EXISTS x_demo (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    data_id UUID DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    sort INT DEFAULT 0,
    status SMALLINT DEFAULT 1,
    create_by BIGINT DEFAULT 0,
    update_by BIGINT DEFAULT 0,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted SMALLINT DEFAULT 0,
    delete_time TIMESTAMP,
    delete_by BIGINT DEFAULT 0,
    remark TEXT
);

CREATE INDEX IF NOT EXISTS idx_x_demo_status ON x_demo(status);
CREATE INDEX IF NOT EXISTS idx_x_demo_is_deleted ON x_demo(is_deleted);
