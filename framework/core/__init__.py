"""Core 核心模块

提供应用框架的核心功能：
- 配置管理
- 数据库操作
- 模型与控制器基类
- 错误处理
- 日志记录
"""

from .config import config
from .db import db
from .model import Model
from .controller import Controller
from . import models
from .error_handler import log_error, get_error_response_data, handle_exception
from .error_codes import get_error_info, format_error_message, ERROR_MESSAGES

__all__ = [
    "config",
    "db",
    "Model",
    "Controller",
    "models",
    "log_error",
    "get_error_response_data",
    "handle_exception",
    "get_error_info",
    "format_error_message",
    "ERROR_MESSAGES",
]
