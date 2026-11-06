"""WebSocket 路由模块

提供 WebSocket 连接管理、消息广播、文件导出清理等功能。
支持连接数限制、心跳保活、自动清理过期文件。
"""

import asyncio
import os
import tempfile
import time
from typing import Dict, Set

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, JSONResponse

from framework.core.auth import get_current_user
from framework.core.function import build_content_disposition

router = APIRouter(prefix="/ws")

# 临时目录配置
TEMP_DIR = tempfile.gettempdir()
EXPORT_DIR = os.path.join(TEMP_DIR, "xai_exports")
os.makedirs(EXPORT_DIR, exist_ok=True)

# WebSocket 配置
MAX_CONNECTIONS = 1000
HEARTBEAT_INTERVAL = 30
EXPIRE_TIME = 24 * 60 * 60

# 导出文件存储: {task_id: {"file_path": str, "filename": str, "created_at": float}}
export_files: Dict[str, Dict[str, object]] = {}


def restore_export_files() -> None:
    """从磁盘恢复导出文件注册表

    注册表是进程内存字典，后端重启后会丢失，导致已生成的下载链接返回
    「文件不存在或已过期」；而导出文件本身仍保存在 EXPORT_DIR 中。
    故此处按磁盘实际文件重建注册表，顺带清理已过期文件。
    文件名无从还原，统一回退为通用名（前端另有时效与默认名兜底）。
    """
    current_time = time.time()
    try:
        names = os.listdir(EXPORT_DIR)
    except OSError:
        return

    for name in names:
        if not name.endswith(".xlsx"):
            continue
        file_path = os.path.join(EXPORT_DIR, name)
        try:
            created_at = os.path.getmtime(file_path)
        except OSError:
            continue

        if current_time - created_at > EXPIRE_TIME:
            try:
                os.remove(file_path)
            except OSError:
                pass
            continue

        export_files[name[: -len(".xlsx")]] = {
            "file_path": file_path,
            "filename": "导出文件.xlsx",
            "created_at": created_at,
        }


restore_export_files()


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        # 用户ID到客户端ID集合的映射（同一用户可多页签/多端同时在线，需向全部连接推送）
        self.user_connections: Dict[str, Set[str]] = {}
        self._cleanup_task: asyncio.Task | None = None

    @property
    def connection_count(self) -> int:
        """当前连接数"""
        return len(self.active_connections)

    async def connect(self, client_id: str, websocket: WebSocket) -> bool:
        """接受新连接

        Returns:
            bool: 是否成功连接，False 表示达到连接上限
        """
        if self.connection_count >= MAX_CONNECTIONS:
            return False

        await websocket.accept()
        self.active_connections[client_id] = websocket
        return True

    def disconnect(self, client_id: str) -> None:
        """断开连接"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        # 同步清理该连接对应的用户映射（同一连接可能注册过多个用户ID）
        for user_id, conn_ids in list(self.user_connections.items()):
            conn_ids.discard(client_id)
            if not conn_ids:
                del self.user_connections[user_id]

    def register_user(self, user_id: str, client_id: str) -> None:
        """建立用户ID到客户端ID的映射（同一用户允许多个连接同时在线）"""
        self.user_connections.setdefault(str(user_id), set()).add(client_id)

    def get_client_ids_by_user_id(self, user_id: str) -> Set[str]:
        """根据用户ID获取其全部在线客户端ID"""
        return set(self.user_connections.get(str(user_id)) or ())

    async def send_personal_message(self, message: Dict, client_id: str) -> None:
        """发送个人消息"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except RuntimeError:
                self.disconnect(client_id)

    async def broadcast(self, message: Dict, exclude: Set[str] | None = None) -> None:
        """广播消息"""
        disconnected = []
        for client_id, connection in self.active_connections.items():
            if exclude and client_id in exclude:
                continue
            try:
                await connection.send_json(message)
            except RuntimeError:
                disconnected.append(client_id)

        for client_id in disconnected:
            self.disconnect(client_id)

    def get_all_clients(self) -> Set[str]:
        """获取所有已连接的客户端ID"""
        return set(self.active_connections.keys())


manager = ConnectionManager()


async def cleanup_expired_files():
    """定期清理过期的导出文件"""
    while True:
        current_time = time.time()
        expired_tasks = []

        for task_id, file_info in export_files.items():
            created_at = file_info.get("created_at", 0)
            if current_time - created_at > EXPIRE_TIME:
                expired_tasks.append(task_id)

        for task_id in expired_tasks:
            file_info = export_files[task_id]
            file_path = file_info.get("file_path")
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass
            del export_files[task_id]

        await asyncio.sleep(3600)


def start_cleanup_task():
    """启动清理任务"""
    if manager._cleanup_task is None:
        manager._cleanup_task = asyncio.create_task(cleanup_expired_files())


def stop_cleanup_task():
    """停止清理任务"""
    if manager._cleanup_task:
        manager._cleanup_task.cancel()
        manager._cleanup_task = None


@router.websocket("/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket 端点

    Args:
        websocket: WebSocket 连接
        client_id: 客户端唯一标识
    """
    connected = await manager.connect(client_id, websocket)
    if not connected:
        await websocket.close(code=4000, reason="连接数已达上限")
        return

    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=HEARTBEAT_INTERVAL)
                await handle_websocket_message(client_id, data)
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping", "timestamp": time.time()})
            except RuntimeError:
                break
            except ValueError:
                try:
                    await websocket.send_json({"type": "error", "message": "无效的JSON格式"})
                except RuntimeError:
                    break
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        await manager.broadcast({"type": "user_left", "client_id": client_id})


async def handle_websocket_message(client_id: str, data: Dict):
    """处理 WebSocket 消息

    Args:
        client_id: 客户端ID
        data: 消息数据
    """
    msg_type = data.get("type")

    if msg_type == "register":
        user_id = data.get("user_id")
        if user_id is not None and str(user_id).strip() != "":
            manager.register_user(str(user_id), client_id)
            await manager.send_personal_message(
                {"type": "register_success", "message": "用户注册成功"}, client_id
            )
        else:
            await manager.send_personal_message(
                {"type": "error", "message": "注册失败：缺少 user_id"}, client_id
            )
        return

    if msg_type == "pong":
        return

    if msg_type == "broadcast":
        message = data.get("message", {})
        await manager.broadcast({"type": "broadcast", "from": client_id, "data": message}, exclude={client_id})
        return

    if msg_type == "private":
        target_id = data.get("target_id")
        message = data.get("message", {})
        if target_id in manager.get_all_clients():
            await manager.send_personal_message({"type": "private", "from": client_id, "data": message}, target_id)
        else:
            await manager.send_personal_message({"type": "error", "message": "目标客户端不在线"}, client_id)
        return

    await manager.send_personal_message({"type": "echo", "data": data}, client_id)


# 显式要求登录：/ws/* 在全局白名单内且本路由跳过了全局登录依赖，
# 故此处直接依赖 get_current_user（不判定白名单），避免导出文件被匿名下载
@router.get("/download/{task_id}", dependencies=[Depends(get_current_user)])
async def download_export_file(task_id: str):
    """下载导出的文件

    Args:
        task_id: 导出任务ID

    Returns:
        文件流或错误响应
    """
    if task_id in export_files:
        file_info = export_files[task_id]
        filename = file_info.get("filename", "export.xlsx")
        file_path = file_info.get("file_path")

        if file_path and os.path.exists(file_path):

            def file_generator():
                with open(file_path, "rb") as f:
                    yield from f

            return StreamingResponse(
                file_generator(),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": build_content_disposition(filename)},
            )

    return JSONResponse(status_code=404, content={"code": 404, "message": "文件不存在或已过期"})
