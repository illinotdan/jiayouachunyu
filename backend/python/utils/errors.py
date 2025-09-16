"""
错误处理工具
"""

from flask import current_app, request
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import IntegrityError, OperationalError
from marshmallow import ValidationError
from utils.response import ApiResponse, ErrorCodes
import logging

def register_error_handlers(app):
    """注册全局错误处理器"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return ApiResponse.error(
            '请求参数错误',
            ErrorCodes.VALIDATION_ERROR,
            400
        )
    
    @app.errorhandler(401)
    def unauthorized(error):
        return ApiResponse.error(
            '未授权访问',
            ErrorCodes.TOKEN_MISSING,
            401
        )
    
    @app.errorhandler(403)
    def forbidden(error):
        return ApiResponse.error(
            '权限不足',
            ErrorCodes.PERMISSION_DENIED,
            403
        )
    
    @app.errorhandler(404)
    def not_found(error):
        return ApiResponse.error(
            '资源不存在',
            ErrorCodes.NOT_FOUND,
            404
        )
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return ApiResponse.error(
            '请求方法不允许',
            'METHOD_NOT_ALLOWED',
            405
        )
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return ApiResponse.error(
            '请求频率过高，请稍后再试',
            ErrorCodes.RATE_LIMITED,
            429
        )
    
    @app.errorhandler(500)
    def internal_error(error):
        current_app.logger.error(f'服务器内部错误: {error}')
        return ApiResponse.error(
            '服务器内部错误',
            'INTERNAL_SERVER_ERROR',
            500
        )
    
    @app.errorhandler(ValidationError)
    def validation_error(error):
        return ApiResponse.error(
            '数据验证失败',
            ErrorCodes.VALIDATION_ERROR,
            400,
            error.messages
        )
    
    @app.errorhandler(IntegrityError)
    def integrity_error(error):
        current_app.logger.error(f'数据库完整性错误: {error}')
        
        # 解析常见的完整性错误
        error_message = str(error.orig)
        
        if 'unique constraint' in error_message.lower():
            if 'username' in error_message:
                return ApiResponse.error('用户名已存在', ErrorCodes.USERNAME_EXISTS, 409)
            elif 'email' in error_message:
                return ApiResponse.error('邮箱已被注册', ErrorCodes.EMAIL_EXISTS, 409)
            else:
                return ApiResponse.error('数据已存在', 'DUPLICATE_DATA', 409)
        
        return ApiResponse.error(
            '数据库操作失败',
            ErrorCodes.DATABASE_ERROR,
            500
        )
    
    @app.errorhandler(OperationalError)
    def operational_error(error):
        current_app.logger.error(f'数据库操作错误: {error}')
        return ApiResponse.error(
            '数据库连接失败',
            ErrorCodes.DATABASE_ERROR,
            503
        )
    
    @app.errorhandler(Exception)
    def general_exception(error):
        current_app.logger.error(f'未处理的异常: {error}', exc_info=True)
        
        # 在开发环境显示详细错误信息
        if current_app.debug:
            return ApiResponse.error(
                f'服务器错误: {str(error)}',
                'DEBUG_ERROR',
                500,
                {'traceback': str(error)}
            )
        
        return ApiResponse.error(
            '服务器内部错误',
            'INTERNAL_SERVER_ERROR',
            500
        )

class APIException(Exception):
    """自定义API异常"""
    
    def __init__(self, message, error_code=None, status_code=400, details=None):
        self.message = message
        self.error_code = error_code or ErrorCodes.UNKNOWN_ERROR
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)

def handle_api_exception(app):
    """处理自定义API异常"""
    
    @app.errorhandler(APIException)
    def api_exception_handler(error):
        return ApiResponse.error(
            error.message,
            error.error_code,
            error.status_code,
            error.details
        )

class ErrorLogger:
    """错误日志记录器"""
    
    @staticmethod
    def log_error(error, context=None):
        """记录错误日志"""
        error_info = {
            'error': str(error),
            'type': type(error).__name__,
            'url': request.url if request else None,
            'method': request.method if request else None,
            'ip': request.remote_addr if request else None,
            'user_agent': request.headers.get('User-Agent') if request else None,
            'context': context
        }
        
        current_app.logger.error(f'API错误: {error_info}')
        
        # 发送到外部监控服务（如Sentry）
        try:
            import sentry_sdk
            sentry_sdk.capture_exception(error)
        except:
            pass
    
    @staticmethod
    def log_warning(message, context=None):
        """记录警告日志"""
        warning_info = {
            'message': message,
            'url': request.url if request else None,
            'method': request.method if request else None,
            'ip': request.remote_addr if request else None,
            'context': context
        }
        
        current_app.logger.warning(f'API警告: {warning_info}')
    
    @staticmethod
    def log_info(message, context=None):
        """记录信息日志"""
        info = {
            'message': message,
            'url': request.url if request else None,
            'context': context
        }
        
        current_app.logger.info(f'API信息: {info}')

def safe_execute(func, *args, **kwargs):
    """安全执行函数，捕获异常"""
    try:
        return func(*args, **kwargs), None
    except Exception as e:
        ErrorLogger.log_error(e)
        return None, str(e)

def validate_request_size(max_size=16*1024*1024):  # 16MB
    """验证请求大小"""
    def decorator(f):
        def decorated_function(*args, **kwargs):
            if request.content_length and request.content_length > max_size:
                return ApiResponse.error(
                    '请求体过大',
                    'REQUEST_TOO_LARGE',
                    413
                )
            return f(*args, **kwargs)
        return decorated_function
    return decorator
