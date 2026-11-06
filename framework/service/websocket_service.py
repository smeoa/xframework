"""WebSocket服务

提供统一的WebSocket连接管理服务，包括：
1. 稳定的连接保持和心跳检测
2. 消息队列和批量发送
3. 连接状态管理
4. 广播消息支持
"""

from fastapi import WebSocket
from typing import Set, Dict, List, Optional
import json
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSocketService:
    """WebSocket服务类"""
    
    def __init__(self):
        self._callbacks: Set[WebSocket] = set()
        self._connection_info: Dict[WebSocket, dict] = {}
        self._message_queue: List[dict] = []
        self._queue_lock = asyncio.Lock()
        self._is_processing = False
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._process_task: Optional[asyncio.Task] = None
        
        self.HEARTBEAT_INTERVAL = 60  # 心跳间隔（秒）
        self.MESSAGE_QUEUE_MAX_SIZE = 1000  # 消息队列最大容量
        self.MESSAGE_BATCH_SIZE = 10  # 批量发送大小
        self.MESSAGE_FLUSH_INTERVAL = 0.1  # 队列刷新间隔（秒）
    
    async def _heartbeat(self):
        """定期发送心跳检测 - 优化版本，不主动断开连接"""
        while True:
            await asyncio.sleep(self.HEARTBEAT_INTERVAL)
            # 只记录，不主动断开
            for ws in list(self._callbacks):
                try:
                    await ws.send_json({"type": "heartbeat", "timestamp": datetime.now().isoformat()})
                    self._connection_info[ws]["last_heartbeat"] = datetime.now()
                except Exception as e:
                    logger.debug(f"发送心跳失败: {e}")
    
    async def _process_message_queue(self):
        """处理消息队列，批量发送"""
        while True:
            await asyncio.sleep(self.MESSAGE_FLUSH_INTERVAL)
            
            if not self._message_queue or self._is_processing:
                continue
            
            async with self._queue_lock:
                if not self._message_queue:
                    continue
                self._is_processing = True
                batch = self._message_queue[:self.MESSAGE_BATCH_SIZE]
                self._message_queue[:] = self._message_queue[self.MESSAGE_BATCH_SIZE:]
                self._is_processing = False
            
            await self._broadcast_batch(batch)
    
    async def _broadcast_batch(self, messages: List[dict]):
        """批量广播消息"""
        if not self._callbacks:
            return
        
        dead: list[WebSocket] = []
        for ws in self._callbacks:
            try:
                for msg in messages:
                    await ws.send_json(msg)
            except Exception as e:
                dead.append(ws)
                logger.debug(f"发送消息失败，移除连接: {e}")
        
        for ws in dead:
            self._callbacks.discard(ws)
            self._connection_info.pop(ws, None)
    
    async def handle_connection(self, ws: WebSocket):
        """处理WebSocket连接"""
        await ws.accept()
        
        client_info = {
            "connected_at": datetime.now(),
            "last_heartbeat": datetime.now(),
            "message_count": 0,
        }
        self._callbacks.add(ws)
        self._connection_info[ws] = client_info
        
        logger.info(f"新连接建立，当前连接数: {len(self._callbacks)}")
        
        try:
            while True:
                try:
                    # 等待消息，不设置超时，让连接自然保持
                    data = await ws.receive_text()
                    if data:
                        try:
                            message = json.loads(data)
                            if message.get("type") == "ping":
                                await ws.send_json({"type": "pong"})
                                self._connection_info[ws]["last_heartbeat"] = datetime.now()
                        except json.JSONDecodeError:
                            pass
                except Exception as e:
                    # 只有真正的异常才断开
                    logger.debug(f"连接异常: {e}")
                    break
        except Exception as e:
            logger.debug(f"连接异常关闭: {e}")
        finally:
            self._callbacks.discard(ws)
            self._connection_info.pop(ws, None)
            logger.info(f"连接关闭，当前连接数: {len(self._callbacks)}")
    
    async def broadcast(self, data: dict):
        """广播消息到所有客户端
        
        优化点：
        1. 使用消息队列异步发送，不阻塞主线程
        2. 支持批量发送，减少网络开销
        3. 队列满时丢弃最老消息，防止内存溢出
        """
        async with self._queue_lock:
            if len(self._message_queue) >= self.MESSAGE_QUEUE_MAX_SIZE:
                self._message_queue.pop(0)
            self._message_queue.append(data)
    
    async def broadcast_to_conversation(self, conversation_id: int, data: dict):
        """向指定会话的客户端广播消息（预留扩展）"""
        data["conversation_id"] = conversation_id
        await self.broadcast(data)
    
    def get_connection_count(self) -> int:
        """获取当前连接数"""
        return len(self._callbacks)
    
    def get_connection_stats(self) -> dict:
        """获取连接统计信息"""
        now = datetime.now()
        stats = {
            "total_connections": len(self._callbacks),
            "active_connections": sum(
                1 for info in self._connection_info.values()
                if (now - info["last_heartbeat"]).seconds < self.HEARTBEAT_INTERVAL * 2
            ),
            "queue_size": len(self._message_queue),
        }
        return stats
    
    async def init(self):
        """初始化WebSocket服务"""
        self._heartbeat_task = asyncio.create_task(self._heartbeat())
        self._process_task = asyncio.create_task(self._process_message_queue())
        logger.info("WebSocket服务初始化完成")


# 单例实例
websocket_service = WebSocketService()
