"""前台 API 应用入口

启动（在项目根目录执行）：
    uvicorn main:app --app-dir site --host 0.0.0.0 --port 8100

说明：目录名 site 与 Python 标准库同名，因此以「应用根目录」方式加载（--app-dir），
不作为包导入，避免与标准库 site 冲突。
"""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

import db
from common import ApiProblem, error_response, success
from settings import settings
from upload.upload_route import router as upload_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("site_api")


async def _startup() -> None:
    await db.init_pool()
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    logger.info("数据库连接池已初始化，存储目录 %s", settings.storage_dir)


async def _shutdown() -> None:
    await db.close_pool()


app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    docs_url="/docs",
    openapi_url="/openapi.json",
    on_startup=[_startup],
    on_shutdown=[_shutdown],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Content-Type", "X-Admin-Token"],
)


@app.exception_handler(ApiProblem)
async def handle_api_problem(request: Request, exc: ApiProblem):
    return error_response(exc.code, exc.message, exc.data)


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError):
    errors = {}
    for item in exc.errors():
        location = [str(part) for part in item.get("loc", []) if part not in ("body", "query", "path")]
        field = ".".join(location) or "request"
        errors[field] = item.get("msg", "Invalid value.")
    return error_response(400, "Please fix the highlighted fields and try again.", errors)


@app.exception_handler(Exception)
async def handle_unexpected(request: Request, exc: Exception):
    logger.error("未处理异常 %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    return error_response(500, "System error. Please try again later.")


@app.get("/health", tags=["运维"])
async def health():
    try:
        await db.fetchval("SELECT 1")
        database = True
    except Exception:  # noqa: BLE001 - 健康检查需要返回真实状态
        database = False
    return success({"status": "ok" if database else "degraded", "database": database, "version": settings.app_version})


for router in (
    upload_router,
):
    app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=False)
