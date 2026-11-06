"""控制器基类模块

本模块提供基础控制器类，封装了常用的请求处理、响应生成和数据验证功能。
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any, Type, Optional
from pydantic import BaseModel, ValidationError
from .db import db
from .config import config
from .models import BaseResponse, ErrorResponse, ErrorCategoryEnum
import logging
import datetime
import sys
import uuid
from decimal import Decimal

logger = logging.getLogger(__name__)


class Controller:
    """基础控制器类

    提供控制器常用功能，包括数据CRUD操作
    """

    def __init__(self, request: Request):
        """初始化控制器

        Args:
            request: FastAPI 请求对象
        """
        self.request = request
        self.db = db
        self.config = config
        self.model = None

    def _to_json_compatible(self, data: Any) -> Any:
        """递归转换数据为JSON可序列化格式

        Args:
            data: 要转换的数据

        Returns:
            JSON可序列化的数据
        """
        if isinstance(data, dict):
            return {k: self._to_json_compatible(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._to_json_compatible(item) for item in data]
        elif isinstance(data, (datetime.datetime, datetime.date)):
            return data.isoformat()
        elif isinstance(data, uuid.UUID):
            return str(data)
        elif isinstance(data, Decimal):
            return float(data)
        return data

    def success(self, data: Any = None, message: str = "操作成功") -> JSONResponse:
        """返回成功响应

        Args:
            data: 响应数据
            message: 响应消息

        Returns:
            JSONResponse 对象
        """
        response = BaseResponse(code=200, message=message, data=data)
        compatible_data = self._to_json_compatible(response.model_dump())
        return JSONResponse(compatible_data)

    def error(
        self, code: int = 400, message: str = "操作失败", data: Any = None, category: Optional[ErrorCategoryEnum] = None
    ) -> JSONResponse:
        """返回错误响应

        Args:
            code: 错误码
            message: 错误消息
            data: 附加数据
            category: 错误分类

        Returns:
            JSONResponse 对象
        """
        error_id = str(uuid.uuid4())
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"

        response = ErrorResponse(
            code=code, message=message, detail=data, category=category, error_id=error_id, timestamp=timestamp
        )

        # 记录错误日志（处于 except 上下文时带上堆栈，数据库日志会落进 x_log.exc_info）
        logger.error(
            f"Error {error_id}: {code} - {message}",
            extra={
                "error_id": error_id,
                "category": category.value if category else None,
                "detail": data,
                "timestamp": timestamp,
            },
            exc_info=sys.exc_info()[0] is not None,
        )

        compatible_data = self._to_json_compatible(response.model_dump())
        return JSONResponse(
            status_code=code,
            content=compatible_data,
        )

    def abort(self, code: int = 400, message: str = "请求失败", category: Optional[ErrorCategoryEnum] = None) -> None:
        """中止请求并返回错误

        Args:
            code: 错误码
            message: 错误消息
            category: 错误分类

        Raises:
            HTTPException: 终止请求并返回错误
        """
        error_id = str(uuid.uuid4())
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"

        # 记录错误日志（同上，except 环境下带堆栈）
        logger.warning(
            f"中止请求 {error_id}: {code} - {message}",
            extra={"error_id": error_id, "category": category.value if category else None, "timestamp": timestamp},
            exc_info=sys.exc_info()[0] is not None,
        )

        # 构造结构化的错误详情
        error_detail = {
            "message": message,
            "error_id": error_id,
            "category": category.value if category else None,
            "timestamp": timestamp,
        }

        raise HTTPException(status_code=code, detail=error_detail)

    async def _get_request_data(self) -> Dict[str, Any]:
        """获取请求数据

        Returns:
            请求数据字典
        """
        try:
            return await self.request.json()
        except Exception:
            return {}

    def validate(self, data: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, Any]:
        """验证数据

        Args:
            data: 要验证的数据
            rules: 验证规则

        Returns:
            验证后的数据

        Raises:
            HTTPException: 验证失败时
        """
        errors = {}

        for field, rule in rules.items():
            value = data.get(field)

            # 检查必填
            if rule.get("required") and value is None:
                errors[field] = rule.get("message", f"{field}不能为空")

            # 检查类型
            if value is not None:
                expected_type = rule.get("type")
                if expected_type and not isinstance(value, expected_type):
                    errors[field] = rule.get("message", f"{field}类型错误")

            # 检查长度
            if isinstance(value, str):
                min_length = rule.get("min")
                max_length = rule.get("max")
                if min_length and len(value) < min_length:
                    errors[field] = rule.get("message", f"{field}长度不能小于{min_length}")
                if max_length and len(value) > max_length:
                    errors[field] = rule.get("message", f"{field}长度不能大于{max_length}")

            # 检查自定义验证函数
            if value is not None and "validator" in rule:
                validator = rule["validator"]
                if callable(validator):
                    try:
                        if not validator(value):
                            errors[field] = rule.get("message", f"{field}验证失败")
                    except Exception as e:
                        errors[field] = rule.get("message", f"{field}验证失败: {str(e)}")

        if errors:
            logger.warning(f"数据验证失败: {errors}")
            self.abort(400, str(errors), category=ErrorCategoryEnum.VALIDATION)

        return data  # type: ignore[no-any-return]

    def validate_with_model(self, data: Dict[str, Any], model: Type[BaseModel]) -> BaseModel:
        """使用 Pydantic 模型验证数据

        Args:
            data: 要验证的数据
            model: Pydantic 模型类

        Returns:
            验证后的 Pydantic 模型实例

        Raises:
            HTTPException: 验证失败时
        """
        try:
            return model(**data)
        except ValidationError as e:
            errors = e.errors()
            error_messages = {str(error["loc"][0]): error["msg"] for error in errors}
            logger.warning(f"数据验证失败: {error_messages}")
            self.abort(400, str(error_messages), category=ErrorCategoryEnum.VALIDATION)

        return data  # type: ignore[return-value]
