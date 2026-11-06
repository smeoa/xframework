"""前台 API 服务配置

优先读取环境变量；本地开发回退到 admin/.env 的 PG_* 配置。
禁止在代码中硬编码生产域名与密钥。
"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BASE_DIR = Path(__file__).resolve().parent
STORAGE_DIR = Path(os.getenv("SITE_UPLOAD_DIR") or (BASE_DIR / "storage")).resolve()


def _load_env_file(path: Path) -> None:
    """极简 .env 解析：仅补齐缺失的键，不覆盖已有环境变量"""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_env_file(PROJECT_ROOT / "admin" / ".env")
_load_env_file(BASE_DIR / ".env")


def get_str(key: str, default: str = "") -> str:
    return os.getenv(key, default) or default


def get_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, "") or default)
    except (TypeError, ValueError):
        return default


def get_bool(key: str, default: bool = False) -> bool:
    value = os.getenv(key, "")
    if not value:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    app_title = "Site Front API"
    app_version = "1.0.0"
    port = get_int("SITE_API_PORT", 8100)
    host = get_str("SITE_API_HOST", "0.0.0.0")

    # PostgreSQL
    pg_host = get_str("PG_HOST", "127.0.0.1")
    pg_port = get_int("PG_PORT", 5432)
    pg_database = get_str("PG_DBNAME", "xf")
    pg_user = get_str("PG_USER", "postgres")
    pg_password = get_str("PG_PASSWORD", "")
    pg_pool_min = get_int("PG_POOL_MIN", 2)
    pg_pool_max = get_int("PG_POOL_MAX", 10)

    # 跨域：前台 dev / 预览 / 静态站
    cors_origins = [
        item.strip()
        for item in get_str(
            "SITE_CORS_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3010,"
            "http://127.0.0.1:3010,http://localhost:3011,http://127.0.0.1:3011,"
            "http://127.0.0.1:3020",
        ).split(",")
        if item.strip()
    ]

    site_url = get_str("SITE_URL", "http://localhost:3000")

    # 上传
    storage_dir = STORAGE_DIR
    upload_max_mb = get_int("SITE_UPLOAD_MAX_MB", 10)
    upload_max_count = get_int("SITE_UPLOAD_MAX_COUNT", 5)

    # 表单限流：次数 / 窗口秒（common.check_rate_limit 使用）
    rate_limit_count = get_int("SITE_RATE_LIMIT_COUNT", 20)
    rate_limit_window = get_int("SITE_RATE_LIMIT_WINDOW", 600)

    # 内容写接口保护：为空时仅允许本机访问（开发态）
    admin_token = get_str("SITE_ADMIN_TOKEN", "")


settings = Settings()
