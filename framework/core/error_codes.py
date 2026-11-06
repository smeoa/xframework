"""错误码管理模块

本模块定义了系统中使用的错误码和错误消息模板，提供错误信息获取和格式化功能。
"""

from typing import Dict, Any
from .models import ErrorCategoryEnum, ErrorCodeEnum

# 错误消息模板
ERROR_MESSAGES: Dict[int, Dict[str, Any]] = {
    # 通用错误
    ErrorCodeEnum.BAD_REQUEST: {"message": "请求参数错误", "category": ErrorCategoryEnum.VALIDATION},
    ErrorCodeEnum.UNAUTHORIZED: {"message": "未授权访问", "category": ErrorCategoryEnum.AUTHENTICATION},
    ErrorCodeEnum.FORBIDDEN: {"message": "禁止访问", "category": ErrorCategoryEnum.AUTHORIZATION},
    ErrorCodeEnum.NOT_FOUND: {"message": "资源不存在", "category": ErrorCategoryEnum.RESOURCE},
    ErrorCodeEnum.METHOD_NOT_ALLOWED: {"message": "请求方法不允许", "category": ErrorCategoryEnum.VALIDATION},
    ErrorCodeEnum.CONFLICT: {"message": "请求冲突", "category": ErrorCategoryEnum.BUSINESS},
    ErrorCodeEnum.UNPROCESSABLE_ENTITY: {"message": "请求数据无法处理", "category": ErrorCategoryEnum.VALIDATION},
    ErrorCodeEnum.TOO_MANY_REQUESTS: {"message": "请求过于频繁", "category": ErrorCategoryEnum.RESOURCE},
    ErrorCodeEnum.INTERNAL_SERVER_ERROR: {"message": "内部服务器错误", "category": ErrorCategoryEnum.INTERNAL},
    ErrorCodeEnum.SERVICE_UNAVAILABLE: {"message": "服务不可用", "category": ErrorCategoryEnum.INTERNAL},
    # 业务错误
    ErrorCodeEnum.VALIDATION_ERROR: {"message": "数据验证失败", "category": ErrorCategoryEnum.VALIDATION},
    ErrorCodeEnum.AUTHENTICATION_ERROR: {"message": "认证失败", "category": ErrorCategoryEnum.AUTHENTICATION},
    ErrorCodeEnum.AUTHORIZATION_ERROR: {"message": "权限不足", "category": ErrorCategoryEnum.AUTHORIZATION},
    ErrorCodeEnum.DATABASE_ERROR: {"message": "数据库操作失败", "category": ErrorCategoryEnum.DATABASE},
    ErrorCodeEnum.RESOURCE_NOT_FOUND: {"message": "请求的资源不存在", "category": ErrorCategoryEnum.RESOURCE},
    ErrorCodeEnum.BUSINESS_LOGIC_ERROR: {"message": "业务逻辑错误", "category": ErrorCategoryEnum.BUSINESS},
}


def get_error_info(code: int) -> Dict[str, Any]:
    """获取错误信息

    Args:
        code: 错误码

    Returns:
        错误信息字典，包含消息和分类
    """
    return ERROR_MESSAGES.get(code, {"message": "未知错误", "category": ErrorCategoryEnum.INTERNAL})


def format_error_message(code: int, **kwargs: Any) -> str:
    """格式化错误消息

    Args:
        code: 错误码
        **kwargs: 消息模板参数

    Returns:
        格式化后的错误消息
    """
    error_info = get_error_info(code)
    message = error_info["message"]
    if kwargs:
        return message.format(**kwargs)
    return message  # type: ignore[no-any-return]
