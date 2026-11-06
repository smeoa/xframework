"""数据模型基础定义模块

本模块定义了系统中使用的基础数据模型，包括请求/响应模型、枚举类型等。
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Dict, List, Optional, Any
from enum import Enum


class DirectionEnum(str, Enum):
    """排序方向枚举"""

    ASC = "asc"
    DESC = "desc"


class LogicEnum(str, Enum):
    """逻辑操作枚举"""

    AND = "and"
    OR = "or"


class BaseModelConfig(BaseModel):
    """基础模型配置"""

    model_config = ConfigDict(
        from_attributes=True,  # 支持从 ORM 对象创建
        extra="forbid",  # 禁止额外字段
        strict=True,  # 严格模式
        validate_assignment=True,  # 验证赋值
        use_enum_values=True,  # 使用枚举值
        json_schema_extra={  # AI 工具友好的 schema 元数据
            "description": "基础模型配置，提供统一的模型行为和验证规则",
            "ai_metadata": {"version": "1.0", "purpose": "通用数据模型基础类", "compatibility": "向后兼容"},
        },
    )


class PaginationParams(BaseModelConfig):
    """分页参数模型"""

    page: int = Field(
        default=1,
        ge=1,
        description="页码",
        json_schema_extra={"ai_metadata": {"example": 1, "validation": "必须是大于等于 1 的整数"}},
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="每页条数",
        json_schema_extra={"ai_metadata": {"example": 10, "validation": "必须是 1-100 之间的整数"}},
    )


class SortRule(BaseModelConfig):
    """排序规则模型"""

    field: str = Field(
        ..., description="排序字段", json_schema_extra={"ai_metadata": {"example": "created_at", "validation": "非空字符串"}}
    )
    direction: DirectionEnum = Field(
        default=DirectionEnum.ASC,
        description="排序方向",
        json_schema_extra={"ai_metadata": {"example": "asc", "validation": "必须是 'asc' 或 'desc'"}},
    )


class FilterCondition(BaseModelConfig):
    """过滤条件模型"""

    field: str = Field(
        ..., description="字段名", json_schema_extra={"ai_metadata": {"example": "name", "validation": "非空字符串"}}
    )
    operator: str = Field(
        ..., description="操作符", json_schema_extra={"ai_metadata": {"example": "eq", "validation": "非空字符串"}}
    )
    value: Any = Field(
        ..., description="值", json_schema_extra={"ai_metadata": {"example": "test", "validation": "非空值"}}
    )


class FilterGroup(BaseModelConfig):
    """过滤条件组模型"""

    group_logic: LogicEnum = Field(
        default=LogicEnum.AND,
        description="组逻辑",
        json_schema_extra={"ai_metadata": {"example": "and", "validation": "必须是 'and' 或 'or'"}},
    )
    condition_logic: LogicEnum = Field(
        default=LogicEnum.AND,
        description="条件逻辑",
        json_schema_extra={"ai_metadata": {"example": "and", "validation": "必须是 'and' 或 'or'"}},
    )
    conditions: List[FilterCondition] = Field(
        default_factory=list,
        description="条件列表",
        json_schema_extra={"ai_metadata": {"example": [], "validation": "过滤条件列表"}},
    )


class ListRequest(BaseModelConfig):
    """列表请求模型"""

    filter: List[FilterGroup] = Field(
        default_factory=list,
        description="过滤条件",
        json_schema_extra={"ai_metadata": {"example": [], "validation": "过滤条件组列表"}},
    )
    fields: str = Field(
        default="*",
        description="字段选择",
        json_schema_extra={"ai_metadata": {"example": "id,name", "validation": "字符串，多个字段用逗号分隔"}},
    )
    sort_rules: List[SortRule] = Field(
        default_factory=list,
        description="排序规则",
        json_schema_extra={
            "ai_metadata": {"example": [{"field": "created_at", "direction": "desc"}], "validation": "排序规则列表"}
        },
    )
    page: Optional[int] = Field(
        default=None,
        ge=1,
        description="页码",
        json_schema_extra={"ai_metadata": {"example": 1, "validation": "必须是大于等于 1 的整数"}},
    )
    limit: Optional[int] = Field(
        default=None,
        ge=1,
        le=100,
        description="每页条数",
        json_schema_extra={"ai_metadata": {"example": 10, "validation": "必须是 1-100 之间的整数"}},
    )
    keyword: str = Field(
        default="", description="搜索关键词", json_schema_extra={"ai_metadata": {"example": "test", "validation": "字符串"}}
    )
    search_fields: List[str] = Field(
        default_factory=list,
        description="搜索字段",
        json_schema_extra={"ai_metadata": {"example": ["name", "description"], "validation": "搜索字段列表"}},
    )

    # 为了保持向后兼容性，添加对 searchFields 的支持
    @field_validator("search_fields", mode="before")
    def validate_search_fields(cls, v: Any, info: Any) -> List[str]:
        """验证搜索字段，支持向后兼容

        Args:
            v: 当前字段值
            info: 验证信息

        Returns:
            验证后的搜索字段列表
        """
        if "searchFields" in info.data:
            return info.data["searchFields"]
        return v  # type: ignore[return-value]


class ListResponse(BaseModelConfig):
    """列表响应模型"""

    items: List[Dict[str, Any]] = Field(
        ..., description="数据列表", json_schema_extra={"ai_metadata": {"example": [], "validation": "数据项列表"}}
    )
    total: int = Field(..., description="总记录数", json_schema_extra={"ai_metadata": {"example": 0, "validation": "非负整数"}})


class BaseResponse(BaseModelConfig):
    """基础响应模型"""

    code: int = Field(
        default=200, description="状态码", json_schema_extra={"ai_metadata": {"example": 200, "validation": "整数状态码"}}
    )
    message: str = Field(
        default="success",
        description="消息",
        json_schema_extra={"ai_metadata": {"example": "success", "validation": "字符串消息"}},
    )
    data: Optional[Any] = Field(
        default=None, description="数据", json_schema_extra={"ai_metadata": {"example": None, "validation": "任意类型数据"}}
    )


class ErrorCategoryEnum(str, Enum):
    """错误分类枚举"""

    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATABASE = "database"
    NETWORK = "network"
    INTERNAL = "internal"
    EXTERNAL = "external"
    RESOURCE = "resource"
    BUSINESS = "business"


class ErrorCodeEnum(int, Enum):
    """错误码枚举"""

    # 通用错误
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    TOO_MANY_REQUESTS = 429
    INTERNAL_SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503

    # 业务错误
    VALIDATION_ERROR = 40001
    AUTHENTICATION_ERROR = 40101
    AUTHORIZATION_ERROR = 40301
    DATABASE_ERROR = 50001
    RESOURCE_NOT_FOUND = 40401
    BUSINESS_LOGIC_ERROR = 40002


class ErrorResponse(BaseModelConfig):
    """错误响应模型"""

    code: int = Field(
        ..., description="错误码", json_schema_extra={"ai_metadata": {"example": 400, "validation": "整数错误码"}}
    )
    message: str = Field(
        ..., description="错误消息", json_schema_extra={"ai_metadata": {"example": "Bad Request", "validation": "字符串错误消息"}}
    )
    detail: Optional[Any] = Field(
        default=None, description="错误详情", json_schema_extra={"ai_metadata": {"example": None, "validation": "任意类型错误详情"}}
    )
    category: Optional[ErrorCategoryEnum] = Field(
        default=None,
        description="错误分类",
        json_schema_extra={"ai_metadata": {"example": "validation", "validation": "错误分类枚举值"}},
    )
    error_id: Optional[str] = Field(
        default=None,
        description="错误唯一标识",
        json_schema_extra={"ai_metadata": {"example": "e1234567-89ab-cdef-0123-456789abcdef", "validation": "UUID字符串"}},
    )
    timestamp: Optional[str] = Field(
        default=None,
        description="错误发生时间",
        json_schema_extra={"ai_metadata": {"example": "2023-12-01T12:00:00Z", "validation": "ISO格式时间字符串"}},
    )
