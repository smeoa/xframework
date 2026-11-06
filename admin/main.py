"""Admin 应用主入口

提供 FastAPI 应用初始化、路由注册、生命周期管理等功能。
"""

import os
import sys
import time
import asyncio
import importlib
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.routing import APIWebSocketRoute
from fastapi.staticfiles import StaticFiles

# Windows 平台下 asyncpg 需要 SelectorEventLoop 而非默认的 ProactorEventLoop
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from framework import config
from framework.core import log_db
from framework.core.auth import require_login
from framework.core.db import init_db, db
from framework.core.error_handler import register_error_handlers
from framework.core.logger import setup_logging
from admin.ws.ws_route import start_cleanup_task, stop_cleanup_task

# 前端构建产物目录（vite build 输出）：同源部署时由后端托管；目录不存在时仅提供 API。
# 可用 .env 的 WEB_DIST_DIR 覆盖（支持相对项目根或绝对路径）。
_web_dist = config.get("WEB_DIST_DIR", "") or os.path.join(project_root, "front-admin", "dist")
WEB_DIST_DIR = os.path.normpath(
    _web_dist if os.path.isabs(_web_dist) else os.path.join(project_root, _web_dist)
)

# 属于后端自身的路径前缀，不做 SPA 回退（未命中时返回 404，避免 API 客户端收到 HTML）
_BACKEND_PATH_PREFIXES = ("admin/", "ws/", "docs", "redoc", "openapi.json", "health")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理

    Args:
        app: FastAPI 应用实例
    """
    start_time = time.time()

    # 日志系统：先按 .env 的 LOG_LEVEL 配好控制台输出，再把数据库日志挂上
    log_level = config.get("LOG_LEVEL", "INFO")
    try:
        setup_logging(log_level)
        log_db.install(log_level)
        print(f"[OK] 日志系统初始化完成 (级别={log_level}, 数据库日志见 {log_db.LOG_TABLE} 表)")
    except Exception as e:
        print(f"[WARNING] 日志系统初始化失败: {str(e)}")

    try:
        await init_db()
        print(f"[OK] 数据库连接池初始化完成 ({time.time() - start_time:.2f}s)")
    except Exception as e:
        print(f"[WARNING] 数据库初始化失败: {str(e)}")

    try:
        await log_db.start()
        print("[OK] 数据库日志落库协程已启动")
    except Exception as e:
        print(f"[WARNING] 数据库日志启动失败: {str(e)}")

    try:
        start_cleanup_task()
        print(f"[OK] WebSocket 清理任务启动完成")
    except Exception as e:
        print(f"[WARNING] WebSocket 清理任务启动失败: {str(e)}")

    print(f"\n=== 应用启动完成，耗时: {time.time() - start_time:.2f}s ===")

    yield

    print("\n=== 正在关闭应用... ===")

    try:
        stop_cleanup_task()
        print("[OK] WebSocket 清理任务已停止")
    except Exception as e:
        print(f"[WARNING] 停止清理任务失败: {str(e)}")

    try:
        await log_db.stop()
        print("[OK] 数据库日志已收尾停止")
    except Exception as e:
        print(f"[WARNING] 停止数据库日志失败: {str(e)}")

    try:
        await db.close_pool()
        print("[OK] 数据库连接池已关闭")
    except Exception as e:
        print(f"[WARNING] 关闭数据库连接池失败: {str(e)}")

    print("=== 应用已优雅关闭 ===")


app = FastAPI(
    title=config.get("APP_TITLE", "XAI Admin API"),
    description=config.get("APP_DESCRIPTION", "XAI Framework Admin API"),
    version=config.get("APP_VERSION", "1.0.0"),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.get("APP_CORS_ORIGINS", ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # 导出下载改为前端携带 token 请求 + Blob 保存后，需暴露该响应头，
    # 否则浏览器脚本读不到 Content-Disposition，无法解析后端返回的真实文件名
    expose_headers=["Content-Disposition"],
)


@app.middleware("http")
async def request_logger(request: Request, call_next):
    """请求日志中间件

    Args:
        request: 请求对象
        call_next: 下一个处理函数

    Returns:
        响应对象
    """
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}"

    if process_time > 1:
        print(f"[SLOW] {request.method} {request.url.path} - {process_time:.4f}s - Status: {response.status_code}")

    return response


def auto_register_routers():
    """自动注册所有路由（仅 admin 后台，前台 site_api 独立运行）"""
    print("\n=== 开始自动注册路由 ===")

    admin_dir = os.path.dirname(os.path.abspath(__file__))
    local_count = 0
    for item in os.listdir(admin_dir):
        item_path = os.path.join(admin_dir, item)

        if not os.path.isdir(item_path):
            continue

        if item.startswith("_"):
            continue

        route_file = os.path.join(item_path, f"{item}_route.py")
        if not os.path.exists(route_file):
            continue

        try:
            module_name = f"admin.{item}.{item}_route"
            module = importlib.import_module(module_name)

            if hasattr(module, "router"):
                router = getattr(module, "router")
                # WebSocket 路由无法注入 Request 依赖，单独注册（其消息鉴权在连接内自行处理）
                if any(isinstance(r, APIWebSocketRoute) for r in router.routes):
                    app.include_router(router)
                    print(f"  [OK] 已注册: admin.{item}（含 WebSocket，跳过全局登录依赖）")
                else:
                    app.include_router(router, dependencies=[Depends(require_login)])
                    print(f"  [OK] 已注册: admin.{item}")
                local_count += 1
            else:
                print(f"  [SKIP] admin.{item}: 未找到 router")
        except Exception as e:
            print(f"  [ERROR] admin.{item}: {str(e)}")

    print(f"=== 路由注册完成: admin {local_count} 个 ===\n")


auto_register_routers()
register_error_handlers(app)

# 请求上下文中间件：给每条日志带上 request_id / path / ip / user_id，便于按请求串联排查
app.middleware("http")(log_db.log_context_middleware)


@app.get("/")
async def root():
    """根路径：同源部署时返回前端首页，否则返回欢迎信息"""
    index_file = os.path.join(WEB_DIST_DIR, "index.html")
    if os.path.isfile(index_file):
        return FileResponse(index_file)
    return {
        "message": "Welcome to XAI Admin API",
        "version": config.get("APP_VERSION", "1.0.0"),
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": config.get("APP_TITLE", "XAI Admin API"),
        "timestamp": time.time(),
    }



@app.get("/health/detail")
async def health_detail():
    """详细健康检查"""
    db_health = "ok" if db._pool is not None else "error"

    return {
        "status": "healthy",
        "service": config.get("APP_TITLE", "XAI Admin API"),
        "timestamp": time.time(),
        "database": db_health,
        "ws_connections": len(app.state.__dict__.get("_ws_connections", {})),
    }


# ==================== 前端静态资源与 SPA 回退（同源部署）====================
# 仅在构建产物存在时启用；开发时前端由 vite dev server 提供，不受影响
if os.path.isdir(WEB_DIST_DIR):
    _dist_assets = os.path.join(WEB_DIST_DIR, "assets")
    if os.path.isdir(_dist_assets):
        app.mount("/assets", StaticFiles(directory=_dist_assets), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        """SPA 前端路由回退：命中构建产物中的静态文件则原样返回，否则回退 index.html

        该路由最后注册，故 /admin、/ws、/docs、/health 等后端路由优先命中；
        未命中的后端路径返回 404，避免 API 客户端拿到 HTML。
        """
        if full_path.startswith(_BACKEND_PATH_PREFIXES):
            raise HTTPException(status_code=404, detail="Not Found")

        candidate = os.path.normpath(os.path.join(WEB_DIST_DIR, full_path))
        # 防目录穿越：解析后的路径必须仍位于 dist 目录内
        if candidate.startswith(WEB_DIST_DIR) and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(WEB_DIST_DIR, "index.html"))


if __name__ == "__main__":
    import uvicorn

    reload_enabled = config.get_bool("APP_RELOAD", True)
    # 热重载监听目录：admin（业务代码）与 framework（框架代码）
    # 默认只监听工作目录（admin），framework 改动不会触发重载，故显式加入
    reload_dirs = (
        [os.path.dirname(os.path.abspath(__file__)), os.path.join(project_root, "framework")]
        if reload_enabled
        else None
    )

    uvicorn.run(
        "main:app",
        host=config.get("APP_HOST", "0.0.0.0"),
        port=config.get_int("APP_PORT", 8000),
        reload=reload_enabled,
        reload_dirs=reload_dirs,
    )
