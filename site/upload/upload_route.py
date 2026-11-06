"""附件上传与下载路由（WBS-BA-61.2-001）"""
from fastapi import APIRouter, File, Form, UploadFile
from pydantic import BaseModel, Field

from common import success
from upload.upload_controller import UploadController

router = APIRouter(prefix="/front/upload", tags=["前台-附件"])


class DownloadRequest(BaseModel):
    uuid: str = Field(..., min_length=8, max_length=64, description="附件 uuid")


@router.post("/files", summary="上传附件（multipart）")
async def upload_files(
    form_code: str = Form(..., description="表单编码，如 F03 / F04 / F05 / F06"),
    files: list[UploadFile] = File(..., description="一个或多个文件"),
):
    return success(await UploadController().upload(form_code, files))


@router.post("/download", summary="按 uuid 下载附件")
async def download_file(req: DownloadRequest):
    return await UploadController().download(req.uuid)
