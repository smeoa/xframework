"""错误处理模块

本模块提供错误日志记录、错误响应数据生成和全局异常处理功能。
支持按错误类型分级处理、统一响应格式。
"""

from typing import Dict, Any, Optional
from enum import Enum
import logging
import datetime
import sys
import uuid

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """错误分类枚举"""

    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    RATE_LIMIT = "rate_limit"
    INTERNAL = "internal"
    EXTERNAL = "external"


class BaseError(Exception):
    """基础自定义异常类"""

    def __init__(
        self,
        message: str,
        code: int = 500,
        category: ErrorCategory = ErrorCategory.INTERNAL,
        detail: Optional[Any] = None,
    ):
        self.message = message
        self.code = code
        self.category = category
        self.detail = detail
        super().__init__(message)


class ValidationError(BaseError):
    """参数验证错误"""

    def __init__(self, message: str = "参数验证失败", detail: Optional[Any] = None):
        super().__init__(message, code=400, category=ErrorCategory.VALIDATION, detail=detail)


class AuthenticationError(BaseError):
    """认证错误"""

    def __init__(self, message: str = "认证失败", detail: Optional[Any] = None):
        super().__init__(message, code=401, category=ErrorCategory.AUTHENTICATION, detail=detail)


class AuthorizationError(BaseError):
    """授权错误"""

    def __init__(self, message: str = "无权访问", detail: Optional[Any] = None):
        super().__init__(message, code=403, category=ErrorCategory.AUTHORIZATION, detail=detail)


class NotFoundError(BaseError):
    """资源不存在错误"""

    def __init__(self, message: str = "资源不存在", detail: Optional[Any] = None):
        super().__init__(message, code=404, category=ErrorCategory.NOT_FOUND, detail=detail)


class ConflictError(BaseError):
    """资源冲突错误"""

    def __init__(self, message: str = "资源冲突", detail: Optional[Any] = None):
        super().__init__(message, code=409, category=ErrorCategory.CONFLICT, detail=detail)


class RateLimitError(BaseError):
    """限流错误"""

    def __init__(self, message: str = "请求过于频繁", detail: Optional[Any] = None):
        super().__init__(message, code=429, category=ErrorCategory.RATE_LIMIT, detail=detail)


def log_error(
    message: str,
    code: int,
    category: Optional[ErrorCategory] = None,
    detail: Optional[Any] = None,
    level: int = logging.ERROR,
    extra: Optional[Dict[str, Any]] = None,
) -> str:
    """记录错误日志

    Args:
        message: 错误消息
        code: 错误码
        category: 错误分类
        detail: 错误详情
        level: 日志级别
        extra: 额外信息

    Returns:
        错误唯一标识
    """
    error_id = str(uuid.uuid4())
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"

    log_extra = {
        "error_id": error_id,
        "code": code,
        "category": category.value if category else None,
        "timestamp": timestamp,
        "detail": detail,
        **(extra or {}),
    }

    # 处于 except 上下文时把堆栈一起记下（x_log.exc_info），否则只记消息
    has_exc = sys.exc_info()[0] is not None

    if category == ErrorCategory.VALIDATION:
        logger.warning(f"{message} (ID: {error_id})", extra=log_extra)
    elif category in [ErrorCategory.AUTHENTICATION, ErrorCategory.AUTHORIZATION, ErrorCategory.RATE_LIMIT]:
        logger.warning(f"{message} (ID: {error_id})", extra=log_extra)
    else:
        logger.log(level, f"{message} (ID: {error_id})", extra=log_extra, exc_info=has_exc)

    return error_id


def get_error_response_data(
    code: int, message: str, detail: Optional[Any] = None, category: Optional[ErrorCategory] = None
) -> Dict[str, Any]:
    """获取错误响应数据

    Args:
        code: 错误码
        message: 错误消息
        detail: 错误详情
        category: 错误分类

    Returns:
        错误响应数据字典
    """
    error_id = str(uuid.uuid4())
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"

    return {
        "code": code,
        "message": message,
        "detail": detail,
        "category": category.value if category else None,
        "error_id": error_id,
        "timestamp": timestamp,
    }


def handle_exception(
    exception: Exception,
    code: int = 500,
    message: str = "内部服务器错误",
    category: ErrorCategory = ErrorCategory.INTERNAL,
) -> Dict[str, Any]:
    """处理异常

    Args:
        exception: 异常对象
        code: 错误码
        message: 错误消息
        category: 错误分类

    Returns:
        错误响应数据字典
    """
    if isinstance(exception, BaseError):
        error_id = log_error(
            message=exception.message,
            code=exception.code,
            category=exception.category,
            detail=exception.detail,
        )
        return get_error_response_data(
            code=exception.code,
            message=exception.message,
            detail=exception.detail,
            category=exception.category,
        )

    error_id = log_error(
        message=f"{message}: {str(exception)}",
        code=code,
        category=category,
        detail=str(exception),
        extra={"exception_type": type(exception).__name__},
    )

    return get_error_response_data(
        code=code,
        message=message,
        detail={"error": str(exception), "exception_type": type(exception).__name__},
        category=category,
    )


def register_error_handlers(app):
    """注册全局异常处理器到 FastAPI 应用

    Args:
        app: FastAPI 应用实例
    """
    from fastapi import Request
    from fastapi.responses import JSONResponse
    from pydantic import ValidationError as PydanticValidationError

    @app.exception_handler(PydanticValidationError)
    async def pydantic_validation_error_handler(request: Request, exc: PydanticValidationError):
        """Pydantic 参数验证错误处理"""
        errors = [
            {"field": ".".join(str(loc) for loc in err["loc"]), "message": err["msg"]} for err in exc.errors()
        ]
        error_id = log_error("参数验证失败", code=400, category=ErrorCategory.VALIDATION, detail=errors)
        return JSONResponse(
            status_code=400,
            content=get_error_response_data(400, "参数验证失败", errors, ErrorCategory.VALIDATION),
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        """自定义参数验证错误处理"""
        error_id = log_error(exc.message, code=exc.code, category=exc.category, detail=exc.detail)
        return JSONResponse(
            status_code=exc.code,
            content=get_error_response_data(exc.code, exc.message, exc.detail, exc.category),
        )

    @app.exception_handler(AuthenticationError)
    async def authentication_error_handler(request: Request, exc: AuthenticationError):
        """认证错误处理"""
        error_id = log_error(exc.message, code=exc.code, category=exc.category, detail=exc.detail)
        return JSONResponse(
            status_code=exc.code,
            content=get_error_response_data(exc.code, exc.message, exc.detail, exc.category),
        )

    @app.exception_handler(AuthorizationError)
    async def authorization_error_handler(request: Request, exc: AuthorizationError):
        """授权错误处理"""
        error_id = log_error(exc.message, code=exc.code, category=exc.category, detail=exc.detail)
        return JSONResponse(
            status_code=exc.code,
            content=get_error_response_data(exc.code, exc.message, exc.detail, exc.category),
        )

    @app.exception_handler(NotFoundError)
    async def not_found_error_handler(request: Request, exc: NotFoundError):
        """资源不存在错误处理"""
        error_id = log_error(exc.message, code=exc.code, category=exc.category, detail=exc.detail)
        return JSONResponse(
            status_code=exc.code,
            content=get_error_response_data(exc.code, exc.message, exc.detail, exc.category),
        )

    @app.exception_handler(ConflictError)
    async def conflict_error_handler(request: Request, exc: ConflictError):
        """资源冲突错误处理"""
        error_id = log_error(exc.message, code=exc.code, category=exc.category, detail=exc.detail)
        return JSONResponse(
            status_code=exc.code,
            content=get_error_response_data(exc.code, exc.message, exc.detail, exc.category),
        )

    @app.exception_handler(RateLimitError)
    async def rate_limit_error_handler(request: Request, exc: RateLimitError):
        """限流错误处理"""
        error_id = log_error(exc.message, code=exc.code, category=exc.category, detail=exc.detail)
        return JSONResponse(
            status_code=exc.code,
            content=get_error_response_data(exc.code, exc.message, exc.detail, exc.category),
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """全局异常处理器"""
        import traceback
        error_detail = str(exc) + "\n" + traceback.format_exc()
        error_id = log_error(f"未处理的异常: {str(exc)}", code=500, category=ErrorCategory.INTERNAL)
        return JSONResponse(
            status_code=500,
            content=get_error_response_data(500, "服务器内部错误", error_detail, ErrorCategory.INTERNAL),
        )
