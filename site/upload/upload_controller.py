"""附件上传与下载业务（WBS-BA-61.2-001）

- 三重校验：扩展名白名单 / 单文件大小 / 数量上限
- 服务端重命名存储，storage_key 只允许相对路径
- 下载按 uuid 取真实存储路径，拒绝越权路径
"""
import logging
import uuid as uuid_lib
from datetime import datetime, timezone
from pathlib import Path

from fastapi import UploadFile
from fastapi.responses import FileResponse

from common import ApiProblem, text
from models import AttachmentModel
from settings import settings
from upload.rules import ATTACHMENT_RULES

logger = logging.getLogger(__name__)


class UploadController:
    def __init__(self) -> None:
        self.attachment_model = AttachmentModel()

    async def upload(self, form_code: str, files: list[UploadFile]) -> list[dict]:
        code = text(form_code).upper()
        rule = ATTACHMENT_RULES.get(code)
        if not rule:
            raise ApiProblem(400, "This form does not accept attachments.", {"form_code": "Unsupported form."})
        if not files:
            raise ApiProblem(400, "No file received.", {"files": "Please choose at least one file."})
        if len(files) > min(rule["max_count"], settings.upload_max_count):
            raise ApiProblem(
                400,
                f"You can upload up to {rule['max_count']} files.",
                {"files": f"You can upload up to {rule['max_count']} files."},
            )

        max_bytes = min(rule["max_mb"], settings.upload_max_mb) * 1024 * 1024
        target_dir = (settings.storage_dir / code).resolve()
        target_dir.mkdir(parents=True, exist_ok=True)

        saved: list[dict] = []
        for index, upload in enumerate(files, start=1):
            original_name = Path(upload.filename or "").name
            if not original_name or "." not in original_name:
                raise ApiProblem(400, "Invalid file name.", {"files": "Invalid file name."})
            file_ext = original_name.rsplit(".", 1)[1].lower()
            if file_ext not in rule["extensions"]:
                raise ApiProblem(
                    400,
                    f"Unsupported file type. Allowed: {', '.join(sorted(rule['extensions']))}.",
                    {"files": f"Unsupported file type. Allowed: {', '.join(sorted(rule['extensions']))}."},
                )

            content = await upload.read()
            if not content:
                raise ApiProblem(400, "Empty file.", {"files": "Empty file."})
            if len(content) > max_bytes:
                raise ApiProblem(
                    400,
                    f"Each file must be {rule['max_mb']} MB or smaller.",
                    {"files": f"Each file must be {rule['max_mb']} MB or smaller."},
                )

            storage_key = f"{code}/{datetime.now(timezone.utc).strftime('%Y%m%d')}/{uuid_lib.uuid4().hex}.{file_ext}"
            target = (settings.storage_dir / storage_key).resolve()
            if not str(target).startswith(str(settings.storage_dir.resolve())):
                raise ApiProblem(400, "Invalid storage path.")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)

            row = await self.attachment_model.create(
                {
                    "form_code": code,
                    "original_name": original_name,
                    "file_ext": file_ext,
                    "mime_type": upload.content_type or "application/octet-stream",
                    "file_size": len(content),
                    "file_index": index,
                    "storage_key": storage_key,
                }
            )
            saved.append(
                {
                    "id": row["id"],
                    "uuid": str(row["uuid"]),
                    "original_name": row["original_name"],
                    "file_ext": row["file_ext"],
                    "file_size": row["file_size"],
                    "mime_type": row["mime_type"],
                }
            )

        logger.info("uploaded %s files for %s", len(saved), code)
        return saved

    async def download(self, file_uuid: str) -> FileResponse:
        try:
            parsed_uuid = str(uuid_lib.UUID(text(file_uuid)))
        except (ValueError, AttributeError, TypeError):
            raise ApiProblem(404, "File not found.")
        row = await self.attachment_model.get_by_uuid(parsed_uuid)
        if not row:
            raise ApiProblem(404, "File not found.")
        storage_key = row["storage_key"] or ""
        if not storage_key or storage_key.startswith(("/", "\\")) or ".." in storage_key:
            raise ApiProblem(400, "Invalid storage path.")
        path = (settings.storage_dir / storage_key).resolve()
        if not str(path).startswith(str(settings.storage_dir.resolve())) or not path.is_file():
            raise ApiProblem(404, "File not found.")
        return FileResponse(
            path,
            media_type=row["mime_type"] or "application/octet-stream",
            filename=row["original_name"],
        )
