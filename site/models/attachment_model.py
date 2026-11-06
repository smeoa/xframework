"""附件模型（form_attachments）"""
from typing import Any

import db


class AttachmentModel:
    table_name = "form_attachments"

    async def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = await db.fetchrow(
            """
            INSERT INTO form_attachments (
                form_code, original_name, file_ext, mime_type, file_size,
                file_index, storage_key, upload_status, uploaded_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, 'uploaded', CURRENT_TIMESTAMP(3))
            RETURNING id, uuid, form_code, original_name, file_ext, mime_type,
                      file_size, file_index, storage_key, upload_status
            """,
            payload["form_code"],
            payload["original_name"],
            payload["file_ext"],
            payload["mime_type"],
            payload["file_size"],
            payload.get("file_index", 1),
            payload["storage_key"],
        )
        return dict(row)

    async def get_by_ids(self, ids: list[int]) -> list[dict[str, Any]]:
        if not ids:
            return []
        rows = await db.fetch(
            """
            SELECT id, uuid, lead_id, form_code, original_name, file_ext, mime_type,
                   file_size, file_index, storage_key, upload_status
              FROM form_attachments
             WHERE id = ANY($1::bigint[]) AND is_deleted = 0
            """,
            ids,
        )
        return db.to_dicts(rows)

    async def link_to_lead(
        self, ids: list[int], lead_id: int, form_code: str, conn: Any | None = None
    ) -> int:
        if not ids:
            return 0
        sql = """
            UPDATE form_attachments
               SET lead_id = $1
             WHERE id = ANY($2::bigint[]) AND form_code = $3 AND lead_id IS NULL AND is_deleted = 0
            """
        if conn is not None:
            result = await conn.execute(sql, lead_id, ids, form_code)
        else:
            result = await db.execute(sql, lead_id, ids, form_code)
        return int(result.split()[-1]) if result.startswith("UPDATE") else 0

    async def list_by_lead(self, lead_id: int) -> list[dict[str, Any]]:
        rows = await db.fetch(
            """
            SELECT id, uuid, original_name, file_ext, mime_type, file_size, file_index
              FROM form_attachments
             WHERE lead_id = $1 AND is_deleted = 0
             ORDER BY file_index ASC
            """,
            lead_id,
        )
        return db.to_dicts(rows)

    async def get_by_uuid(self, uuid_value: str) -> dict[str, Any] | None:
        row = await db.fetchrow(
            """
            SELECT id, uuid, original_name, file_ext, mime_type, file_size, storage_key, upload_status
              FROM form_attachments
             WHERE uuid = $1::uuid AND is_deleted = 0
             LIMIT 1
            """,
            uuid_value,
        )
        return db.to_dict(row)
