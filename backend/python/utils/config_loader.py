"""
配置加载器 - 统一配置管理工具
从项目根目录的config.yaml文件加载配置
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)

class ConfigLoader:
    """配置加载器类"""
    
    def __init__(self, config_file: str = "config.yaml"):
        """
        初始化配置加载器
        
        Args:
            config_file: 配置文件名，默认为config.yaml
        """
        self.config_file = config_file
        self.config_data = None
        self.project_root = self._find_project_root()
        self.config_path = self.project_root / config_file
        
        # 加载配置
        self._load_config()
    
    def _find_project_root(self) -> Path:
        """查找项目根目录"""
        current_path = Path(__file__).resolve()
        
        # 从当前文件向上查找，直到找到包含config.yaml的目录
        for parent in current_path.parents:
            if (parent / self.config_file).exists():
                return parent
        
        # 如果没找到，默认返回当前文件的上上上级目录
        # backend/python/utils/config_loader.py -> backend/python/utils -> backend/python -> backend -> project_root
        return current_path.parent.parent.parent.parent
    
    def _load_config(self):
        """加载配置文件"""
        try:
            if not self.config_path.exists():
                logger.warning(f"配置文件不存在: {self.config_path}")
                self.config_data = {}
                return
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config_data = yaml.safe_load(f) or {}
            
            logger.info(f"配置文件加载成功: {self.config_path}")
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            self.config_data = {}
    
    def _resolve_env_vars(self, value: Any) -> Any:
        """解析环境变量"""
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            # 格式: ${VAR_NAME:-default_value}
            env_expr = value[2:-1]  # 移除 ${ 和 }
            
            if ":-" in env_expr:
                var_name, default_value = env_expr.split(":-", 1)
                return os.getenv(var_name, default_value)
            else:
                return os.getenv(env_expr, "")
        
        return value
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值，支持点号分隔的路径
        
        Args:
            key_path: 配置键路径，如 'database.postgresql.host'
            default: 默认值
            
        Returns:
            配置值
        """
        if not self.config_data:
            return default
        
        keys = key_path.split('.')
        value = self.config_data
        
        try:
            for key in keys:
                value = value[key]
            
            # 解析环境变量
            value = self._resolve_env_vars(value)
            return value
            
        except (KeyError, TypeError):
            return default
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        获取配置段落
        
        Args:
            section: 段落名称
            
        Returns:
            配置段落字典
        """
        return self.config_data.get(section, {})
    
    def get_database_url(self, db_type: str = "postgresql") -> str:
        """
        构建数据库连接URL
        
        Args:
            db_type: 数据库类型
            
        Returns:
            数据库连接URL
        """
        if db_type == "postgresql":
            host = self.get("database.postgresql.host", "localhost")
            port = self.get("database.postgresql.port", 5432)
            database = self.get("database.postgresql.database", "dota_analysis")
            username = self.get("database.postgresql.username", "postgres")
            password = self.get("database.postgresql.password", "password")
            
            return f"postgresql://{username}:{password}@{host}:{port}/{database}"
        
        elif db_type == "redis":
            host = self.get("database.redis.host", "localhost")
            port = self.get("database.redis.port", 6379)
            password = self.get("database.redis.password", "")
            db_num = self.get("database.redis.databases.cache", 0)
            
            if password:
                return f"redis://:{password}@{host}:{port}/{db_num}"
            else:
                return f"redis://{host}:{port}/{db_num}"
        
        return ""
    
    def get_redis_url(self, purpose: str = "cache") -> str:
        """
        获取Redis连接URL
        
        Args:
            purpose: 用途 (cache, sessions, celery, rate_limit)
            
        Returns:
            Redis连接URL
        """
        host = self.get("database.redis.host", "localhost")
        port = self.get("database.redis.port", 6379)
        password = self.get("database.redis.password", "")
        db_num = self.get(f"database.redis.databases.{purpose}", 0)
        
        if password:
            return f"redis://:{password}@{host}:{port}/{db_num}"
        else:
            return f"redis://{host}:{port}/{db_num}"
    
    def get_oss_config(self) -> Dict[str, Any]:
        """获取OSS配置"""
        return {
            'access_key_id': self.get("oss.access_key_id"),
            'access_key_secret': self.get("oss.access_key_secret"),
            'endpoint': self.get("oss.endpoint"),
            'bucket_name': self.get("oss.bucket_name"),
            'enabled': self.get("oss.enabled", True)
        }
    
    def get_api_config(self, api_name: str) -> Dict[str, Any]:
        """
        获取外部API配置
        
        Args:
            api_name: API名称 (opendota, stratz, steam)
            
        Returns:
            API配置字典
        """
        return self.get_section(f"external_apis.{api_name}")
    
    def get_celery_config(self) -> Dict[str, Any]:
        """获取Celery配置"""
        config = self.get_section("celery")
        
        # 处理broker_url和result_backend
        if "broker_url" in config:
            config["broker_url"] = self._resolve_env_vars(config["broker_url"])
        if "result_backend" in config:
            config["result_backend"] = self._resolve_env_vars(config["result_backend"])
        
        return config
    
    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return self.get_section("logging")
    
    def get_environment_config(self) -> Dict[str, Any]:
        """获取当前环境的特定配置"""
        env = self.get("application.environment", "development")
        return self.get_section(env)
    
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.get("application.environment", "development") == "development"
    
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.get("application.environment", "development") == "production"
    
    def is_testing(self) -> bool:
        """是否为测试环境"""
        return self.get("application.environment", "development") == "testing"
    
    def reload(self):
        """重新加载配置文件"""
        self._load_config()
        logger.info("配置文件已重新加载")

# 全局配置实例
config_loader = ConfigLoader()

class FlaskConfig:
    """Flask配置类，基于统一配置文件"""
    
    def __init__(self, config_loader: ConfigLoader):
        self.config_loader = config_loader
        self._setup_config()
    
    def _setup_config(self):
        """设置配置"""
        # 应用基础配置
        self.SECRET_KEY = self.config_loader.get("application.security.secret_key", "dev-secret-key")
        self.VERSION = self.config_loader.get("application.version", "1.0.0")
        self.DEBUG = self.config_loader.get("application.debug", True)
        self.TESTING = self.config_loader.is_testing()
        
        # 服务器配置
        self.HOST = self.config_loader.get("application.server.host", "0.0.0.0")
        self.PORT = self.config_loader.get("application.server.python_port", 5000)
        
        # 数据库配置
        self.SQLALCHEMY_DATABASE_URI = self.config_loader.get_database_url("postgresql")
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        
        pg_config = self.config_loader.get_section("database.postgresql")
        self.SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': pg_config.get('pool_size', 20),
            'pool_timeout': pg_config.get('pool_timeout', 30),
            'pool_recycle': pg_config.get('pool_recycle', 3600),
            'max_overflow': pg_config.get('max_overflow', 30),
            'pool_pre_ping': pg_config.get('pool_pre_ping', True)
        }
        
        # Redis配置
        self.REDIS_URL = self.config_loader.get_redis_url("cache")
        self.CACHE_TYPE = 'RedisCache'
        self.CACHE_REDIS_URL = self.REDIS_URL
        self.CACHE_DEFAULT_TIMEOUT = self.config_loader.get("database.redis.cache.default_timeout", 300)
        
        # JWT配置
        self.JWT_SECRET_KEY = self.config_loader.get("application.security.jwt_secret_key", self.SECRET_KEY)
        jwt_access_expires = self.config_loader.get("application.security.jwt_access_token_expires", 86400)
        jwt_refresh_expires = self.config_loader.get("application.security.jwt_refresh_token_expires", 2592000)
        self.JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=jwt_access_expires)
        self.JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=jwt_refresh_expires)
        self.JWT_BLACKLIST_ENABLED = True
        self.JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']
        
        # CORS配置
        cors_origins = self.config_loader.get("application.cors.origins", [])
        self.CORS_ORIGINS = cors_origins if isinstance(cors_origins, list) else [cors_origins]
        
        # 文件上传配置
        self.UPLOAD_FOLDER = self.config_loader.project_root / "backend" / "uploads"
        self.MAX_CONTENT_LENGTH = self.config_loader.get("oss.file_settings.max_file_size", 16777216)
        
        # 外部API配置
        self.OPENDOTA_API_KEY = self.config_loader.get("external_apis.opendota.api_key")
        self.STRATZ_API_KEY = self.config_loader.get("external_apis.stratz.api_key")
        self.STEAM_API_KEY = self.config_loader.get("external_apis.steam.api_key")
        
        # 阿里云OSS配置
        oss_config = self.config_loader.get_oss_config()
        self.ALIYUN_ACCESS_KEY_ID = oss_config['access_key_id']
        self.ALIYUN_ACCESS_KEY_SECRET = oss_config['access_key_secret']
        self.ALIYUN_OSS_ENDPOINT = oss_config['endpoint']
        self.ALIYUN_OSS_BUCKET = oss_config['bucket_name']
        
        # 数据同步配置
        sync_config = self.config_loader.get_section("data_sync")
        self.DATA_SYNC_BATCH_SIZE = sync_config.get("batch_sizes", {}).get("matches", 50)
        self.DATA_SYNC_RATE_LIMIT = sync_config.get("rate_limits", {}).get("opendota", 1.0)
        self.DATA_SYNC_MAX_RETRIES = sync_config.get("retry", {}).get("max_attempts", 3)
        self.DATA_SYNC_TIMEOUT = sync_config.get("timeouts", {}).get("api_request", 30)
        
        # Celery配置
        celery_config = self.config_loader.get_celery_config()
        self.CELERY_BROKER_URL = celery_config.get("broker_url", self.config_loader.get_redis_url("celery"))
        self.CELERY_RESULT_BACKEND = celery_config.get("result_backend", self.config_loader.get_redis_url("celery"))
        
        # 限流配置
        self.RATELIMIT_STORAGE_URL = self.config_loader.get_redis_url("rate_limit")
        self.RATELIMIT_STRATEGY = self.config_loader.get("rate_limiting.strategy", "fixed-window")
        
        # 邮件配置
        mail_config = self.config_loader.get_section("mail")
        if mail_config.get("enabled", False):
            self.MAIL_SERVER = mail_config.get("server", "smtp.gmail.com")
            self.MAIL_PORT = mail_config.get("port", 587)
            self.MAIL_USE_TLS = mail_config.get("use_tls", True)
            self.MAIL_USERNAME = mail_config.get("username")
            self.MAIL_PASSWORD = mail_config.get("password")
            self.MAIL_DEFAULT_SENDER = mail_config.get("default_sender")
        
        # 分页配置
        pagination_config = self.config_loader.get_section("pagination")
        self.DEFAULT_PAGE_SIZE = pagination_config.get("default_page_size", 20)
        self.MAX_PAGE_SIZE = pagination_config.get("max_page_size", 100)
        
        # 缓存配置
        cache_timeouts = self.config_loader.get("database.redis.cache.timeouts", {})
        self.CACHE_CONFIG = cache_timeouts
        
        # Celery任务配置
        task_settings = celery_config.get("task_settings", {})
        self.CELERY_TASK_SERIALIZER = task_settings.get("serializer", "json")
        self.CELERY_RESULT_SERIALIZER = task_settings.get("result_serializer", "json")
        self.CELERY_ACCEPT_CONTENT = task_settings.get("accept_content", ["json"])
        self.CELERY_TIMEZONE = task_settings.get("timezone", "Asia/Shanghai")
        self.CELERY_ENABLE_UTC = task_settings.get("enable_utc", True)
        
        # 监控配置
        monitoring_config = self.config_loader.get_section("monitoring")
        self.SENTRY_DSN = monitoring_config.get("sentry", {}).get("dsn")
        self.PROMETHEUS_METRICS = monitoring_config.get("prometheus", {}).get("enabled", True)

class DevelopmentConfig(FlaskConfig):
    """开发环境配置"""
    def __init__(self, config_loader: ConfigLoader):
        super().__init__(config_loader)
        self.DEBUG = True
        dev_config = config_loader.get_section("development")
        self.AUTO_RELOAD = dev_config.get("auto_reload", True)

class TestingConfig(FlaskConfig):
    """测试环境配置"""
    def __init__(self, config_loader: ConfigLoader):
        super().__init__(config_loader)
        self.TESTING = True
        test_config = config_loader.get_section("testing")
        self.SQLALCHEMY_DATABASE_URI = test_config.get("database_url", "sqlite:///:memory:")
        self.JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)
        self.WTF_CSRF_ENABLED = test_config.get("csrf_enabled", False)

class ProductionConfig(FlaskConfig):
    """生产环境配置"""
    def __init__(self, config_loader: ConfigLoader):
        super().__init__(config_loader)
        self.DEBUG = False
        prod_config = config_loader.get_section("production")
        
        # 生产环境安全配置
        self.SESSION_COOKIE_SECURE = prod_config.get("session_cookie_secure", True)
        self.SESSION_COOKIE_HTTPONLY = prod_config.get("session_cookie_httponly", True)
        self.SESSION_COOKIE_SAMESITE = prod_config.get("session_cookie_samesite", "Lax")

# 配置映射
def get_config_class():
    """根据环境返回对应的配置类"""
    env = config_loader.get("application.environment", "development")
    
    config_map = {
        'development': DevelopmentConfig,
        'testing': TestingConfig,
        'production': ProductionConfig,
    }
    
    return config_map.get(env, DevelopmentConfig)(config_loader)

# 导出配置实例
Config = get_config_class()
