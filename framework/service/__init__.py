"""Service 服务模块

提供统一的第三方服务封装，包括七牛云存储、HTTP请求、定时任务调度、头像缓存、WebSocket连接管理等。
"""

from .qiniu_service import QiniuService, qiniu_service
from .http_service import HttpService, http_service
from .avatar_cache_service import (
    FriendAvatarCache,
    GroupAvatarCache,
    AvatarCacheService,
    friend_avatar_cache,
    group_avatar_cache,
    avatar_cache_service,
)
from .websocket_service import WebSocketService, websocket_service
from .converter import (
    SpeechToTextService,
    speech_to_text_service,
    silk_converter_service,
)

from framework.agent.tools.image_understanding import understand_image
from framework.agent.tools.document_summary import summarize_document, analyze_webpage

__all__ = [
    "QiniuService",
    "qiniu_service",
    "HttpService",
    "http_service",
    "FriendAvatarCache",
    "GroupAvatarCache",
    "AvatarCacheService",
    "friend_avatar_cache",
    "group_avatar_cache",
    "avatar_cache_service",
    "WebSocketService",
    "websocket_service",
    "SpeechToTextService",
    "speech_to_text_service",
    "silk_converter_service",
    "understand_image",
    "summarize_document",
    "analyze_webpage",
]
