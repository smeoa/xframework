"""
七牛云服务模块

提供统一的七牛云存储操作服务，包括：
- 签名URL生成
- 文件上传
- 配置管理
"""

import logging
from urllib.parse import quote, unquote
from typing import Optional
import qiniu

logger = logging.getLogger(__name__)


class QiniuService:
    """七牛云统一服务类"""

    _instance = None
    _initialized = False

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化七牛云服务"""
        if self._initialized:
            return

        self._config = None
        self._auth = None
        self._initialized = True
        logger.info("QiniuService 初始化完成")

    def init_config(self, config: dict):
        """初始化配置 — 非空值才覆盖，避免空配置覆盖已有有效配置"""
        if self._config is None:
            self._config = {}
        for k, v in (config or {}).items():
            if v:
                self._config[k] = v
        access_key = self._get_config("qiniu_access_key")
        secret_key = self._get_config("qiniu_secret_key")

        if access_key and secret_key:
            self._auth = qiniu.Auth(access_key, secret_key)
            logger.info("七牛云认证初始化成功")
        else:
            logger.warning("七牛云配置不完整，access_key 或 secret_key 为空")

    def _get_config(self, key: str, default: str = "") -> str:
        """获取配置项

        Args:
            key: 配置键名
            default: 默认值

        Returns:
            配置值
        """
        if self._config is None:
            return default
        return self._config.get(key, default)


    @property
    def domain(self) -> str:
        """获取七牛云域名"""
        return self._get_config("qiniu_domain", "")

    @property
    def bucket_name(self) -> str:
        """获取存储桶名称"""
        return self._get_config("qiniu_bucket_name", "")

    @property
    def access_key(self) -> str:
        """获取访问密钥"""
        return self._get_config("qiniu_access_key", "")

    @property
    def secret_key(self) -> str:
        """获取密钥"""
        return self._get_config("qiniu_secret_key", "")

    def get_auth(self) -> qiniu.Auth:
        """获取认证对象

        Returns:
            qiniu.Auth 对象
        """
        if self._auth is None:
            self._auth = qiniu.Auth(self.access_key, self.secret_key)
        return self._auth

    def generate_signed_url(self, storage_key: str, expires: int = 3600) -> str:
        """生成带签名的访问URL

        统一处理URL编码，兼容新旧数据格式。

        Args:
            storage_key: 七牛云存储的key（可以是带路径的文件名或完整URL）
            expires: 过期时间（秒），默认3600秒

        Returns:
            带签名的访问URL
        """
        if not storage_key:
            logger.warning("storage_key 为空，无法生成签名URL")
            return ""

        # 如果 storage_key 已经是完整URL，直接生成签名
        if storage_key.startswith("http://") or storage_key.startswith("https://"):
            base_url = storage_key
            logger.debug(f"使用完整URL生成签名: {base_url[:50]}...")
        else:
            # 先解码已有的编码（处理旧数据中的 %2F 等编码）
            storage_key = unquote(storage_key)

            # 分离路径和查询参数（如果有）
            if "?" in storage_key:
                path_part, query_part = storage_key.split("?", 1)
                # 对路径部分进行编码，但保留斜杠
                encoded_key = quote(path_part, safe="/")
                base_url = f"http://{self.domain}/{encoded_key}?{query_part}"
            else:
                # 没有查询参数，只编码文件名部分，保留斜杠
                encoded_key = quote(storage_key, safe="/")
                base_url = f"http://{self.domain}/{encoded_key}"

            logger.debug(f"生成签名URL - key: {storage_key[:50]}..., domain: {self.domain}")

        # 生成带过期时间的签名URL
        try:
            private_url = self.get_auth().private_download_url(base_url, expires=expires)
            logger.debug(f"签名URL生成成功，过期时间: {expires}秒")
            return private_url
        except Exception as e:
            logger.error(f"生成签名URL失败: {str(e)}")
            raise

    def generate_upload_token(self, key: Optional[str] = None) -> tuple:
        """生成上传token

        Args:
            key: 上传的文件key，如果为None则由七牛云自动生成

        Returns:
            (token, key) 元组
        """
        try:
            auth = self.get_auth()
            token = auth.upload_token(self.bucket_name, key)
            return token, key
        except Exception as e:
            logger.error(f"生成上传token失败: {str(e)}")
            raise

    def upload_file(self, key: str, file_path: str, token: str = None) -> tuple:
        """上传文件到七牛云

        Args:
            key: 存储的key
            file_path: 本地文件路径
            token: 上传token，如果为None则自动生成

        Returns:
            (ret, info) 元组
        """
        try:
            if token is None:
                token, _ = self.generate_upload_token(key)

            ret, info = qiniu.put_file(token, key, file_path)

            if ret:
                logger.info(f"文件上传成功: {key}")
            else:
                logger.error(f"文件上传失败: {info}")

            return ret, info
        except Exception as e:
            logger.error(f"上传文件异常: {str(e)}")
            raise


# 全局单例实例
qiniu_service = QiniuService()
