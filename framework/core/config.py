"""配置管理模块

本模块负责加载和管理配置文件，提供统一的配置获取接口。
支持懒加载、环境变量覆盖、类型验证、.env 文件支持等功能。
"""

import yaml
import os
import logging
import time
from typing import Dict, Any, Optional, TypeVar, Type, Literal

T = TypeVar("T")
logger = logging.getLogger(__name__)

CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")


class ConfigManager:
    """配置管理器（单例模式）"""

    _instance: Optional["ConfigManager"] = None
    _initialized: bool = False
    _config: Optional[Dict[str, Any]] = None
    _last_load_time: float = 0
    _cache_ttl: int = 300  # 5分钟缓存

    def __new__(cls) -> "ConfigManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if ConfigManager._initialized:
            return
        ConfigManager._initialized = True

    def _load_env_file(self, env_path: str = None) -> Dict[str, str]:
        """加载 .env 文件

        优先级：显式传入 env_path > 环境变量 XAI_ENV_FILE（前后台独立 env） > 默认 admin/.env。
        """
        result = {}

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if env_path:
            env_file = env_path if os.path.isabs(env_path) else os.path.join(project_root, env_path)
        else:
            env_file = os.environ.get("XAI_ENV_FILE") or os.path.join(project_root, "admin", ".env")

        if not os.path.exists(env_file):
            logger.warning(f".env 文件不存在: {env_file}")
            return result
        
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        result[key] = value
            logger.info(f"加载 .env 文件: {env_file}")
        except Exception as e:
            logger.error(f"读取 .env 文件失败 {env_file}: {e}")
        
        return result

    def _load_yaml_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """加载 YAML 配置文件"""
        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config_data: Optional[Dict[str, Any]] = yaml.safe_load(f)
                if config_data:
                    logger.debug(f"成功加载配置文件: {file_path}")
                    return config_data
                else:
                    logger.warning(f"配置文件为空: {file_path}")
                    return None
        except Exception as e:
            logger.error(f"读取配置文件失败 {file_path}: {e}")
            return None

    def _set_nested_value(self, config: Dict[str, Any], key: str, value: Any) -> None:
        """设置嵌套配置值"""
        if "." not in key:
            config[key] = value
            return

        keys = key.split(".")
        current = config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            elif not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value

    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """应用环境变量覆盖
        
        配置键名与 .env 文件中的参数名完全一致，如 GEWE_API_TOKEN、PG_HOST 等
        """
        env_vars = self._load_env_file()
        env_vars.update(os.environ)

        for key, value in env_vars.items():
            # 直接使用原始环境变量名作为配置键
            self._set_nested_value(config, key, value)
            logger.debug(f"环境变量覆盖配置: {key}")

        return config

    def _load_config(self) -> Dict[str, Any]:
        """加载所有配置文件"""
        logger.info("开始加载配置文件...")
        result: Dict[str, Any] = {}

        if os.path.exists(CONFIG_DIR):
            for filename in os.listdir(CONFIG_DIR):
                if filename.endswith(".yaml") or filename.endswith(".yml"):
                    file_path = os.path.join(CONFIG_DIR, filename)
                    config_data = self._load_yaml_file(file_path)
                    if config_data:
                        result.update(config_data)

        result = self._apply_env_overrides(result)
        logger.info(f"配置加载完成，共 {len(result)} 个配置项")
        return result

    def _ensure_config_loaded(self) -> None:
        """确保配置已加载，支持热重载"""
        current_time = time.time()
        if self._config is None or (current_time - self._last_load_time) > self._cache_ttl:
            self._config = self._load_config()
            self._last_load_time = current_time

    def get(self, key: str, default: Any = None, type_hint: Optional[Type[T]] = None) -> T:
        """获取配置值，支持类型转换

        Args:
            key: 配置键，支持点号分隔的嵌套键
            default: 默认值
            type_hint: 目标类型，支持自动转换

        Returns:
            配置值或默认值
        """
        self._ensure_config_loaded()

        if "." not in key:
            value = self._config.get(key, default) if self._config else default
        else:
            keys = key.split(".")
            value = self._config
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    value = default
                    break

        if default is None and value is None:
            raise Exception(f"配置项缺失: {key}")

        if type_hint is not None and value is not None:
            try:
                if type_hint is bool:
                    return type_hint(str(value).lower() in ["true", "1", "yes", "y"])
                return type_hint(value)
            except (ValueError, TypeError):
                logger.warning(f"配置类型转换失败: {key}={value} -> {type_hint}")

        return value

    def get_int(self, key: str, default: int = 0) -> int:
        """获取整数配置值"""
        return self.get(key, default, int)

    def get_float(self, key: str, default: float = 0.0) -> float:
        """获取浮点数配置值"""
        return self.get(key, default, float)

    def get_bool(self, key: str, default: bool = False) -> bool:
        """获取布尔配置值"""
        return self.get(key, default, bool)

    def get_str(self, key: str, default: str = "") -> str:
        """获取字符串配置值"""
        value = self.get(key, default)
        return str(value) if value is not None else default

    def get_list(self, key: str, default: list = None) -> list:
        """获取列表配置值"""
        value = self.get(key, default or [])
        return list(value) if value else (default or [])

    def get_dict(self, key: str, default: dict = None) -> dict:
        """获取字典配置值"""
        value = self.get(key, default or {})
        return dict(value) if value else (default or {})

    def reload(self) -> None:
        """强制重新加载配置"""
        self._config = None
        self._ensure_config_loaded()
        logger.info("配置已热重载")

    def validate(self, validations: Dict[str, dict]) -> list[str]:
        """验证配置项

        Args:
            validations: 验证规则字典

        Returns:
            错误信息列表
        """
        errors = []
        for key, rules in validations.items():
            value = self.get(key)

            if rules.get("required") and value is None:
                errors.append(f"{key} 是必填项")
                continue

            if value is None:
                continue

            if "type" in rules:
                try:
                    if rules["type"] is bool:
                        if not isinstance(value, bool):
                            str_val = str(value).lower()
                            if str_val not in ["true", "false", "1", "0", "yes", "no"]:
                                errors.append(f"{key} 类型错误，期望 bool")
                    else:
                        rules["type"](value)
                except (ValueError, TypeError):
                    errors.append(f"{key} 类型错误，期望 {rules['type'].__name__}")

            if "min" in rules or "max" in rules:
                try:
                    num_value = float(value)
                    if "min" in rules and num_value < rules["min"]:
                        errors.append(f"{key} 最小值为 {rules['min']}")
                    if "max" in rules and num_value > rules["max"]:
                        errors.append(f"{key} 最大值为 {rules['max']}")
                except (ValueError, TypeError):
                    pass

            if "one_of" in rules and value not in rules["one_of"]:
                errors.append(f"{key} 必须是 {rules['one_of']} 之一")

            if "pattern" in rules and not rules["pattern"].match(str(value)):
                errors.append(f"{key} 格式不正确")

        return errors


_config_manager = ConfigManager()
get = _config_manager.get
get_int = _config_manager.get_int
get_float = _config_manager.get_float
get_bool = _config_manager.get_bool
get_str = _config_manager.get_str
get_list = _config_manager.get_list
get_dict = _config_manager.get_dict
reload = _config_manager.reload
validate = _config_manager.validate
config = _config_manager