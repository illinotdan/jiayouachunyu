# -*- coding: utf-8 -*-
"""
工具模块初始化文件
"""

# 基础工具
from .response import ApiResponse, error_response, success_response
from .validators import validate_email, validate_password, validate_username
from .decorators import require_auth, rate_limit, cache_result, monitor_performance
from .async_helper import run_async, async_context
from .config_loader import Config, DevelopmentConfig, TestingConfig, ProductionConfig
from .errors import register_error_handlers, APIException, ErrorLogger

# API增强工具
from .api_monitor import APIMonitor, api_monitor, init_monitor
from .api_cache import APICacheManager, api_cache as cache_manager, cache_route, init_cache_manager
from .rate_limiter import APIRateLimiter, rate_limiter, rate_limit_by_user_role, init_rate_limiter
from .api_version import APIVersionManager, api_version_manager, init_version_manager
from .monitoring import init_performance_monitoring
from .swagger_config import init_swagger, init_swagger_config
from .api_docs import APIDocumentationGenerator, init_swagger as init_swagger_docs

__all__ = [
    'ApiResponse',
    'error_response',
    'success_response',
    'validate_email',
    'validate_password',
    'validate_username',
    'require_auth',
    'rate_limit',
    'cache_result',
    'monitor_performance',
    'run_async',
    'async_context',
    'Config',
    'DevelopmentConfig',
    'TestingConfig',
    'ProductionConfig',
    'register_error_handlers',
    'APIException',
    'ErrorLogger',
    'APIMonitor',
    'api_monitor',
    'init_monitor',
    'APICacheManager',
    'cache_manager',
    'cache_route',
    'init_cache_manager',
    'APIRateLimiter',
    'rate_limiter',
    'rate_limit_by_user_role',
    'init_rate_limiter',
    'APIVersionManager',
    'api_version_manager',
    'init_version_manager',
    'init_performance_monitoring',
    'init_swagger',
    'init_swagger_config',
    'APIDocumentationGenerator',
    'init_swagger_docs'
]