"""公共工具：统一响应、参数校验、限流、幂等键、占位图

响应信封：{code, message, data}
- 成功 code=200
- 校验失败 code=400，data 为 {字段名: 提示}
- 其他错误 code 同 HTTP 状态码
"""
import hashlib
import json
import re
import time
from collections import defaultdict, deque
from typing import Any
from urllib.parse import quote

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from settings import settings

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[A-Za-z]{2,}$")
URL_RE = re.compile(r"^https?://[^\s]+\.[^\s]+$", re.I)
PHONE_RE = re.compile(r"^\+?[0-9][0-9\s\-()]{5,19}$")

TRAE_IMAGE_BASE = "https://trae-api-cn.mchost.guru/api/ide/v1/tool_text_to_image"
TRAE_IMAGE_SIZES = {
    "square_hd",
    "square",
    "portrait_4_3",
    "portrait_16_9",
    "landscape_4_3",
    "landscape_16_9",
}


class ApiProblem(Exception):
    """业务异常：由全局异常处理器转成统一错误响应"""

    def __init__(self, code: int = 400, message: str = "Request failed.", data: Any = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data


def success(data: Any = None, message: str = "success") -> JSONResponse:
    return JSONResponse({"code": 200, "message": message, "data": jsonable_encoder(data)})


def error_response(code: int, message: str, data: Any = None) -> JSONResponse:
    return JSONResponse(
        {"code": code, "message": message, "data": jsonable_encoder(data)}, status_code=code
    )


def fail(message: str, errors: dict[str, str] | None = None) -> None:
    """字段级校验失败：统一抛出 400，data 为字段错误映射"""
    raise ApiProblem(400, message, errors or {})


# ---------------- 参数读取与校验 ----------------

def text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value)
    return str(value).strip()


def to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return text(value).lower() in {"1", "true", "yes", "on"}


def to_list(value: Any) -> list[str]:
    if isinstance(value, (list, tuple)):
        return [text(item) for item in value if text(item)]
    raw = text(value)
    return [item.strip() for item in raw.split(",") if item.strip()] if raw else []


def to_int(value: Any, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def snake_key(name: str) -> str:
    """camelCase → snake_case（前端 useApi 可能已转换，做兼容）"""
    output = []
    for index, char in enumerate(name):
        if char.isupper() and index > 0:
            output.append("_")
        output.append(char.lower())
    return "".join(output)


def normalize_keys(data: Any) -> Any:
    """递归把字典键统一为 snake_case"""
    if isinstance(data, dict):
        return {snake_key(str(key)): normalize_keys(value) for key, value in data.items()}
    if isinstance(data, list):
        return [normalize_keys(item) for item in data]
    return data


def page_params(body: dict[str, Any], default_size: int = 12) -> tuple[int, int, int]:
    page = max(1, to_int(body.get("page"), 1))
    size = to_int(body.get("page_size") or body.get("pageSize"), default_size)
    size = min(60, max(1, size))
    return page, size, (page - 1) * size


def paginated(items: list[Any], total: int, page: int, size: int) -> dict[str, Any]:
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": size,
        "total_pages": max(1, (total + size - 1) // size),
    }


def require(errors: dict[str, str], field: str, value: Any, message: str) -> None:
    if not text(value):
        errors[field] = message


def min_length(errors: dict[str, str], field: str, value: Any, length: int, message: str) -> None:
    raw = text(value)
    if not raw:
        errors[field] = message
    elif len(raw) < length:
        errors[field] = message


def check_email(errors: dict[str, str], field: str, value: Any) -> None:
    raw = text(value)
    if not raw:
        errors[field] = "Work email is required."
    elif not EMAIL_RE.match(raw):
        errors[field] = "Please enter a valid email address."


def check_phone(errors: dict[str, str], field: str, value: Any) -> None:
    raw = text(value)
    if not raw:
        errors[field] = "Phone number is required."
        return
    digits = re.sub(r"\D", "", raw)
    if not PHONE_RE.match(raw) or not 7 <= len(digits) <= 15:
        errors[field] = "Please enter a valid international phone number."


def check_url(errors: dict[str, str], field: str, value: Any) -> None:
    raw = text(value)
    if raw and not URL_RE.match(raw):
        errors[field] = "Please enter a valid URL starting with http:// or https://."


def check_consent(errors: dict[str, str], field: str, value: Any, message: str) -> None:
    if not to_bool(value):
        errors[field] = message


def check_enum(errors: dict[str, str], field: str, value: Any, allowed: set[str], message: str) -> None:
    raw = text(value)
    if not raw:
        errors[field] = message
    elif raw not in allowed:
        errors[field] = message


# ---------------- 限流 ----------------

_rate_buckets: dict[str, deque[float]] = defaultdict(deque)


def check_rate_limit(request: Request, scope: str) -> None:
    """按 IP + 业务域限流，超限返回 429"""
    ip = get_client_ip(request)
    key = f"{scope}:{ip}"
    now = time.time()
    window = settings.rate_limit_window
    bucket = _rate_buckets[key]
    while bucket and now - bucket[0] > window:
        bucket.popleft()
    if len(bucket) >= settings.rate_limit_count:
        raise ApiProblem(429, "Too many submissions. Please try again later.")
    bucket.append(now)


def reset_rate_limit() -> None:
    _rate_buckets.clear()


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def require_admin(request: Request) -> None:
    """内容写接口保护：配置了 token 则校验；未配置时只允许本机调用"""
    token = settings.admin_token
    if token:
        if request.headers.get("x-admin-token", "") != token:
            raise ApiProblem(401, "Unauthorized.")
        return
    ip = get_client_ip(request)
    if ip not in {"127.0.0.1", "::1", "localhost"}:
        raise ApiProblem(403, "Content write APIs are restricted.")


# ---------------- 幂等与追踪 ----------------

def build_idempotency_key(form_code: str, email: str, client_ts: str, payload: dict[str, Any]) -> str:
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    ).hexdigest()[:32]
    seed = f"{form_code}|{text(email).lower()}|{text(client_ts)}|{digest}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:64]


def tracking_fields(body: dict[str, Any]) -> dict[str, str]:
    """7 项埋点字段：缺失时留空，不编造来源"""
    return {
        "form_code": text(body.get("form_code")),
        "source_page": text(body.get("source_page"))[:500],
        "utm_source": text(body.get("utm_source"))[:200],
        "utm_medium": text(body.get("utm_medium"))[:200],
        "utm_campaign": text(body.get("utm_campaign"))[:200],
        "referrer": text(body.get("referrer"))[:1000],
        "client_ts": text(body.get("client_ts")),
    }


# ---------------- 占位图 ----------------

def json_value(value: Any, default: Any) -> Any:
    """asyncpg 的 json/jsonb 默认返回字符串，统一解析为对象"""
    if value is None:
        return default
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def trae_image(prompt: str, size: str = "square_hd") -> str:
    """统一占位图：trae 生图链接（禁止本地占位图与空 src）"""
    if size not in TRAE_IMAGE_SIZES:
        size = "square_hd"
    clean = " ".join(text(prompt).split()) or "silver jewelry product photo"
    return f"{TRAE_IMAGE_BASE}?prompt={quote(clean)}&image_size={size}"
