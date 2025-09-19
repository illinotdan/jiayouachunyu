"""
Flask应用配置 - 已迁移到统一配置系统
请使用 utils.config_loader 中的配置类
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入新的配置系统
try:
    from utils.config_loader import Config, DevelopmentConfig, TestingConfig, ProductionConfig
    
    # 配置映射
    config = {
        'development': DevelopmentConfig,
        'testing': TestingConfig,
        'production': ProductionConfig,
        'default': DevelopmentConfig
    }
    
except ImportError:
    # 如果新配置系统不可用，使用旧配置作为后备
    class Config:
        """基础配置类"""
        
        # 应用基础配置
        SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
        VERSION = '1.0.0'
        DEBUG = False
        TESTING = False
        
        # 服务器配置
        HOST = os.environ.get('HOST', '0.0.0.0')
        PORT = int(os.environ.get('PORT', 5000))
        
        # 数据库配置
        DATABASE_URL = os.environ.get('DATABASE_URL') or \
            'postgresql://postgres:password@localhost:5432/dota_analysis'
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': 20,
            'pool_timeout': 30,
            'pool_recycle': 3600,
            'max_overflow': 30
        }
        
        # Redis配置
        REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
        CACHE_TYPE = 'RedisCache'
        CACHE_REDIS_URL = REDIS_URL
        CACHE_DEFAULT_TIMEOUT = 300
        
        # JWT配置
        JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
        JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
        JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
        JWT_BLACKLIST_ENABLED = True
        JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']
        
        # CORS配置
        CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:8000,http://127.0.0.1:8000').split(',')
        
        # 文件上传配置
        UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads')
        MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
        ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg'}
        
        # 邮件配置
        MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
        MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
        MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
        MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
        MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
        MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
        
        # 外部API配置
        OPENDOTA_API_KEY = os.environ.get('OPENDOTA_API_KEY')
        STRATZ_API_KEY = os.environ.get('STRATZ_API_KEY')
        STEAM_API_KEY = os.environ.get('STEAM_API_KEY')
        
        # 阿里云OSS配置
        ALIYUN_ACCESS_KEY_ID = os.environ.get('ALIYUN_ACCESS_KEY_ID')
        ALIYUN_ACCESS_KEY_SECRET = os.environ.get('ALIYUN_ACCESS_KEY_SECRET')
        ALIYUN_OSS_ENDPOINT = os.environ.get('ALIYUN_OSS_ENDPOINT', 'https://oss-cn-hangzhou.aliyuncs.com')
        ALIYUN_OSS_BUCKET = os.environ.get('ALIYUN_OSS_BUCKET', 'dota-analysis')
        
        # 数据同步配置
        DATA_SYNC_BATCH_SIZE = int(os.environ.get('DATA_SYNC_BATCH_SIZE', '100'))
        DATA_SYNC_RATE_LIMIT = int(os.environ.get('DATA_SYNC_RATE_LIMIT', '10'))
        DATA_SYNC_MAX_RETRIES = int(os.environ.get('DATA_SYNC_MAX_RETRIES', '3'))
        DATA_SYNC_TIMEOUT = int(os.environ.get('DATA_SYNC_TIMEOUT', '30'))
        
        # 限流配置
        RATELIMIT_STORAGE_URL = REDIS_URL
        RATELIMIT_STRATEGY = "fixed-window"
        RATELIMIT_DEFAULT = "100 per minute"
        
        # 分页配置
        DEFAULT_PAGE_SIZE = 20
        MAX_PAGE_SIZE = 100
        
        # 缓存配置
        CACHE_CONFIG = {
            'matches_list': 300,
            'match_detail': 60,
            'experts_list': 600,
            'expert_detail': 600,
            'discussions_list': 120,
            'stats': 900,
            'hero_stats': 1800
        }
        
        # Celery配置
        CELERY_BROKER_URL = REDIS_URL
        CELERY_RESULT_BACKEND = REDIS_URL
        CELERY_TASK_SERIALIZER = 'json'
        CELERY_RESULT_SERIALIZER = 'json'
        CELERY_ACCEPT_CONTENT = ['json']
        CELERY_TIMEZONE = 'Asia/Shanghai'
        CELERY_ENABLE_UTC = True
        
        # 监控配置
        SENTRY_DSN = os.environ.get('SENTRY_DSN')
        PROMETHEUS_METRICS = True

    class DevelopmentConfig(Config):
        """开发环境配置"""
        DEBUG = True
        SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
            'postgresql://postgres:password@localhost:5432/dota_analysis_dev'

    class TestingConfig(Config):
        """测试环境配置"""
        TESTING = True
        SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
        JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)
        WTF_CSRF_ENABLED = False

    class ProductionConfig(Config):
        """生产环境配置"""
        DEBUG = False
        
        # 生产环境安全配置
        SESSION_COOKIE_SECURE = True
        SESSION_COOKIE_HTTPONLY = True
        SESSION_COOKIE_SAMESITE = 'Lax'
        
        # 数据库连接池配置
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': 50,
            'pool_timeout': 30,
            'pool_recycle': 3600,
            'max_overflow': 100,
            'pool_pre_ping': True
        }

    # 配置映射
    config = {
        'development': DevelopmentConfig,
        'testing': TestingConfig,
        'production': ProductionConfig,
        'default': DevelopmentConfig
    }
