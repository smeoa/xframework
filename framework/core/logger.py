"""日志管理模块

本模块负责配置和管理应用程序的日志系统，提供统一的日志接口。
"""

import logging
from logging.config import dictConfig
from typing import Optional

def setup_logging(log_level: str = "INFO"):
    """配置日志系统
    
    Args:
        log_level: 日志级别，可选值: debug, info, warning, error, critical
    """
    dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": log_level.upper(),
            },
            "detailed_console": {
                "class": "logging.StreamHandler",
                "formatter": "detailed",
                "level": log_level.upper(),
            },
        },
        "loggers": {
            "app": {
                "handlers": ["detailed_console"],
                "level": log_level.upper(),
                "propagate": False,
            },
            "ai": {
                "handlers": ["detailed_console"],
                "level": log_level.upper(),
                "propagate": False,
            },
            "chat": {
                "handlers": ["detailed_console"],
                "level": log_level.upper(),
                "propagate": False,
            },
            "contacts": {
                "handlers": ["detailed_console"],
                "level": log_level.upper(),
                "propagate": False,
            },
            "callback": {
                "handlers": ["detailed_console"],
                "level": log_level.upper(),
                "propagate": False,
            },
        },
        "root": {
            "handlers": ["console"],
            "level": log_level.upper(),
        },
    })

def get_logger(name: str) -> logging.Logger:
    """获取指定名称的 logger 实例
    
    Args:
        name: logger 名称
    
    Returns:
        logging.Logger 实例
    """
    return logging.getLogger(name)