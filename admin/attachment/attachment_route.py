from fastapi import APIRouter, Request, UploadFile, File, Form, Depends
from typing import Optional
from framework.core.auth import require_permission
from .attachment_controller import AttachmentController


# 初始化附件表
async def init_attachment_tables(db):
    """初始化附件相关表"""
    try:
        # 创建附件表
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS x_attachment (
            id BIGSERIAL PRIMARY KEY,
            data_id UUID DEFAULT gen_random_uuid(),
            filename VARCHAR(255) NOT NULL,
            title VARCHAR(255),
            storage_path VARCHAR(500) NOT NULL,
            file_size BIGINT DEFAULT 0,
            file_type VARCHAR(100),
            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            upload_user_id BIGINT,
            module VARCHAR(50),
            description TEXT,
            access_permission VARCHAR(20) DEFAULT 'private',
            status VARCHAR(20) DEFAULT 'normal',
            remark TEXT,
            create_by BIGINT DEFAULT 0,
            update_by BIGINT DEFAULT 0,
            delete_by BIGINT DEFAULT 0,
            create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            delete_time TIMESTAMP WITHOUT TIME ZONE,
            is_deleted SMALLINT DEFAULT 0
        )
        """
        )

        # 增量列（对已建表的库补通用字段，幂等）
        for ddl in (
            "ALTER TABLE x_attachment ADD COLUMN IF NOT EXISTS data_id UUID DEFAULT gen_random_uuid()",
            "ALTER TABLE x_attachment ADD COLUMN IF NOT EXISTS title VARCHAR(255)",
            "ALTER TABLE x_attachment ADD COLUMN IF NOT EXISTS remark TEXT",
            "ALTER TABLE x_attachment ADD COLUMN IF NOT EXISTS create_by BIGINT DEFAULT 0",
            "ALTER TABLE x_attachment ADD COLUMN IF NOT EXISTS update_by BIGINT DEFAULT 0",
            "ALTER TABLE x_attachment ADD COLUMN IF NOT EXISTS delete_by BIGINT DEFAULT 0",
            "ALTER TABLE x_attachment ADD COLUMN IF NOT EXISTS create_time TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE x_attachment ADD COLUMN IF NOT EXISTS update_time TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE x_attachment ADD COLUMN IF NOT EXISTS delete_time TIMESTAMP WITHOUT TIME ZONE",
            "ALTER TABLE x_attachment ADD COLUMN IF NOT EXISTS is_deleted SMALLINT DEFAULT 0",
        ):
            await db.execute(ddl)
        await db.execute("UPDATE x_attachment SET data_id = gen_random_uuid() WHERE data_id IS NULL")

        # 添加索引
        await db.execute("CREATE INDEX IF NOT EXISTS idx_attachment_data_id ON x_attachment(data_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_attachment_module ON x_attachment(module)")

        print("附件表初始化成功")
    except Exception as e:
        print(f"初始化附件表失败: {str(e)}")


router = APIRouter(prefix="/admin/attachment", tags=["附件管理"])


# 附件相关接口
@router.post("/get-attachment", dependencies=[Depends(require_permission("attachment:list"))])
async def get_attachment(request: Request):
    """获取单个附件

    Returns:
        附件信息
    """
    controller = AttachmentController(request)
    return await controller.get_attachment()


@router.post("/get-attachment-list", dependencies=[Depends(require_permission("attachment:list"))])
async def get_attachment_list(request: Request):
    """获取附件列表

    Returns:
        附件列表
    """
    controller = AttachmentController(request)
    return await controller.get_attachment_list()


@router.post("/create-attachment", dependencies=[Depends(require_permission("attachment:create"))])
async def create_attachment(request: Request):
    """创建附件

    Returns:
        创建结果
    """
    controller = AttachmentController(request)
    return await controller.create_attachment()


@router.post("/update-attachment", dependencies=[Depends(require_permission("attachment:update"))])
async def update_attachment(request: Request):
    """更新附件

    Returns:
        更新结果
    """
    controller = AttachmentController(request)
    return await controller.update_attachment()


@router.post("/delete-attachment", dependencies=[Depends(require_permission("attachment:delete"))])
async def delete_attachment(request: Request):
    """删除附件

    Returns:
        删除结果
    """
    controller = AttachmentController(request)
    return await controller.delete_attachment()


@router.post("/destroy-attachment", dependencies=[Depends(require_permission("attachment:delete"))])
async def destroy_attachment(request: Request):
    """物理删除附件

    Returns:
        删除结果
    """
    controller = AttachmentController(request)
    return await controller.destroy_attachment()


@router.post("/batch-all-attachment", dependencies=[Depends(require_permission("attachment:delete"))])
async def batch_all_attachment(request: Request):
    """删除所有符合筛选条件的附件

    Returns:
        删除结果
    """
    controller = AttachmentController(request)
    return await controller.batch_all_attachment()


@router.post("/batch-attachment", dependencies=[Depends(require_permission("attachment:delete"))])
async def batch_attachment(request: Request):
    """批量删除指定ID的附件

    Returns:
        删除结果
    """
    controller = AttachmentController(request)
    return await controller.batch_attachment()


@router.post("/upload-attachment", dependencies=[Depends(require_permission("attachment:upload"))])
async def upload_attachment(request: Request):
    """上传附件

    Returns:
        上传结果
    """
    controller = AttachmentController(request)
    result = await controller.upload_attachment()
    return result


# 其他接口
@router.get("/download/{attachment_id}", dependencies=[Depends(require_permission("attachment:download"))])
async def download_attachment(request: Request, attachment_id: int):
    """下载附件

    Returns:
        下载链接
    """
    controller = AttachmentController(request)
    return await controller.download_attachment(attachment_id)


@router.get("/preview/{attachment_id}", dependencies=[Depends(require_permission("attachment:download"))])
async def preview_attachment(request: Request, attachment_id: int):
    """预览附件

    Returns:
        预览链接
    """
    controller = AttachmentController(request)
    return await controller.preview_attachment(attachment_id)


@router.post("/update-by-data-id", dependencies=[Depends(require_permission("attachment:update"))])
async def update_attachment_by_data_id(request: Request):
    """根据data_id更新附件

    Returns:
        更新结果
    """
    controller = AttachmentController(request)
    return await controller.update_attachment_by_data_id()
