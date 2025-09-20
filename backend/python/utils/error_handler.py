"""
世界级错误处理和API响应系统
提供统一的错误处理、日志记录和API响应格式
"""

import logging
import traceback
import uuid
import time
from typing import Any, Dict, Optional, Union, List
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict
from functools import wraps
from flask import request, current_app, g
import sys

logger = logging.getLogger(__name__)

class ErrorCode(Enum):
    """错误代码枚举"""
    # 通用错误
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"

    # 业务错误
    INVALID_MATCH_ID = "INVALID_MATCH_ID"
    USER_ALREADY_EXISTS = "USER_ALREADY_EXISTS"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"

    # 系统错误
    DATABASE_ERROR = "DATABASE_ERROR"
    REDIS_ERROR = "REDIS_ERROR"
    EXTERNAL_API_ERROR = "EXTERNAL_API_ERROR"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"

    # 请求错误
    BAD_REQUEST = "BAD_REQUEST"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_REQUEST_FORMAT = "INVALID_REQUEST_FORMAT"
    PAYLOAD_TOO_LARGE = "PAYLOAD_TOO_LARGE"

@dataclass
class ErrorDetail:
    """错误详情"""
    code: str
    message: str
    field: Optional[str] = None
    value: Optional[Any] = None
    suggestion: Optional[str] = None

@dataclass
class APIError:
    """API错误响应结构"""
    error_id: str
    code: str
    message: str
    timestamp: str
    path: Optional[str] = None
    method: Optional[str] = None
    user_id: Optional[str] = None
    details: Optional[List[ErrorDetail]] = None
    stack_trace: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        # 生产环境不返回堆栈跟踪
        if current_app and not current_app.debug:
            result.pop('stack_trace', None)
        return result

class APIResponse:
    """统一API响应格式"""

    @staticmethod
    def success(data: Any = None,
                message: str = "操作成功",
                meta: Optional[Dict[str, Any]] = None,
                status_code: int = 200) -> tuple:
        """成功响应"""
        response = {
            "success": True,
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }

        if meta:
            response["meta"] = meta

        return response, status_code

    @staticmethod
    def error(error: Union[APIError, str],
              status_code: int = 400,
              details: Optional[List[ErrorDetail]] = None) -> tuple:
        """错误响应"""
        if isinstance(error, str):
            api_error = create_api_error(
                code=ErrorCode.UNKNOWN_ERROR.value,
                message=error,
                details=details
            )
        else:
            api_error = error

        response = {
            "success": False,
            "error": api_error.to_dict(),
            "timestamp": datetime.now().isoformat()
        }

        return response, status_code

    @staticmethod
    def paginated(data: List[Any],
                  page: int,
                  per_page: int,
                  total: int,
                  message: str = "数据获取成功") -> tuple:
        """分页响应"""
        total_pages = (total + per_page - 1) // per_page

        response = {
            "success": True,
            "message": message,
            "data": data,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            },
            "timestamp": datetime.now().isoformat()
        }

        return response, 200

def create_api_error(code: str,
                    message: str,
                    details: Optional[List[ErrorDetail]] = None,
                    context: Optional[Dict[str, Any]] = None,
                    include_stack_trace: bool = False) -> APIError:
    """创建API错误对象"""

    # 生成唯一错误ID
    error_id = str(uuid.uuid4())

    # 获取请求信息
    path = getattr(request, 'path', None) if request else None
    method = getattr(request, 'method', None) if request else None
    user_id = getattr(g, 'user_id', None) if hasattr(g, 'user_id') else None

    # 获取堆栈跟踪
    stack_trace = None
    if include_stack_trace or (current_app and current_app.debug):
        stack_trace = traceback.format_exc()

    return APIError(
        error_id=error_id,
        code=code,
        message=message,
        timestamp=datetime.now().isoformat(),
        path=path,
        method=method,
        user_id=user_id,
        details=details,
        stack_trace=stack_trace,
        context=context
    )

class ErrorLogger:
    """错误日志记录器"""

    @staticmethod
    def log_error(error: APIError, severity: str = "ERROR"):
        """记录错误日志"""
        log_data = {
            "error_id": error.error_id,
            "code": error.code,
            "message": error.message,
            "path": error.path,
            "method": error.method,
            "user_id": error.user_id,
            "timestamp": error.timestamp
        }

        if severity == "CRITICAL":
            logger.critical(f"Critical error: {log_data}")
        elif severity == "ERROR":
            logger.error(f"Error: {log_data}")
        elif severity == "WARNING":
            logger.warning(f"Warning: {log_data}")
        else:
            logger.info(f"Info: {log_data}")

        # 在生产环境中，这里可以发送到监控系统
        # 比如Sentry, DataDog等

def handle_validation_error(e):
    """处理验证错误"""
    details = []
    if hasattr(e, 'messages'):
        for field, messages in e.messages.items():
            for message in messages:
                details.append(ErrorDetail(
                    code="FIELD_VALIDATION_ERROR",
                    message=message,
                    field=field,
                    suggestion="请检查字段格式是否正确"
                ))

    error = create_api_error(
        code=ErrorCode.VALIDATION_ERROR.value,
        message="请求数据验证失败",
        details=details
    )

    ErrorLogger.log_error(error, "WARNING")
    return APIResponse.error(error, 400)

def handle_authentication_error(e):
    """处理认证错误"""
    error = create_api_error(
        code=ErrorCode.AUTHENTICATION_ERROR.value,
        message="认证失败，请检查您的登录凭据",
        details=[ErrorDetail(
            code="INVALID_TOKEN",
            message=str(e),
            suggestion="请重新登录获取有效的认证令牌"
        )]
    )

    ErrorLogger.log_error(error, "WARNING")
    return APIResponse.error(error, 401)

def handle_authorization_error(e):
    """处理授权错误"""
    error = create_api_error(
        code=ErrorCode.AUTHORIZATION_ERROR.value,
        message="权限不足，无法执行此操作",
        details=[ErrorDetail(
            code="INSUFFICIENT_PERMISSIONS",
            message=str(e),
            suggestion="请联系管理员获取相应权限"
        )]
    )

    ErrorLogger.log_error(error, "WARNING")
    return APIResponse.error(error, 403)

def handle_not_found_error(e):
    """处理404错误"""
    error = create_api_error(
        code=ErrorCode.NOT_FOUND.value,
        message="请求的资源不存在",
        details=[ErrorDetail(
            code="RESOURCE_NOT_FOUND",
            message=str(e),
            suggestion="请检查URL是否正确"
        )]
    )

    ErrorLogger.log_error(error, "INFO")
    return APIResponse.error(error, 404)

def handle_rate_limit_error(e):
    """处理限流错误"""
    error = create_api_error(
        code=ErrorCode.RATE_LIMIT_EXCEEDED.value,
        message="请求频率过高，请稍后再试",
        details=[ErrorDetail(
            code="TOO_MANY_REQUESTS",
            message=str(e),
            suggestion="请降低请求频率或稍后重试"
        )]
    )

    ErrorLogger.log_error(error, "WARNING")
    return APIResponse.error(error, 429)

def handle_database_error(e):
    """处理数据库错误"""
    error = create_api_error(
        code=ErrorCode.DATABASE_ERROR.value,
        message="数据库操作失败",
        details=[ErrorDetail(
            code="DB_OPERATION_FAILED",
            message="数据库暂时不可用",
            suggestion="请稍后重试"
        )],
        context={"original_error": str(e)},
        include_stack_trace=True
    )

    ErrorLogger.log_error(error, "ERROR")
    return APIResponse.error(error, 503)

def handle_external_api_error(e):
    """处理外部API错误"""
    error = create_api_error(
        code=ErrorCode.EXTERNAL_API_ERROR.value,
        message="外部服务暂时不可用",
        details=[ErrorDetail(
            code="EXTERNAL_SERVICE_ERROR",
            message=str(e),
            suggestion="系统正在使用缓存数据，部分功能可能受限"
        )]
    )

    ErrorLogger.log_error(error, "WARNING")
    return APIResponse.error(error, 503)

def handle_internal_server_error(e):
    """处理内部服务器错误"""
    error = create_api_error(
        code=ErrorCode.INTERNAL_SERVER_ERROR.value,
        message="服务器内部错误",
        details=[ErrorDetail(
            code="INTERNAL_ERROR",
            message="服务器遇到了一个意外的错误",
            suggestion="请联系技术支持或稍后重试"
        )],
        context={"original_error": str(e)},
        include_stack_trace=True
    )

    ErrorLogger.log_error(error, "CRITICAL")
    return APIResponse.error(error, 500)

def api_error_handler(f):
    """API错误处理装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            return handle_validation_error(e)
        except PermissionError as e:
            return handle_authorization_error(e)
        except FileNotFoundError as e:
            return handle_not_found_error(e)
        except ConnectionError as e:
            return handle_external_api_error(e)
        except Exception as e:
            return handle_internal_server_error(e)

    return decorated_function

def setup_error_handlers(app):
    """设置Flask应用的错误处理器"""

    @app.errorhandler(400)
    def handle_bad_request(e):
        return handle_validation_error(e)

    @app.errorhandler(401)
    def handle_unauthorized(e):
        return handle_authentication_error(e)

    @app.errorhandler(403)
    def handle_forbidden(e):
        return handle_authorization_error(e)

    @app.errorhandler(404)
    def handle_not_found(e):
        return handle_not_found_error(e)

    @app.errorhandler(429)
    def handle_too_many_requests(e):
        return handle_rate_limit_error(e)

    @app.errorhandler(500)
    def handle_internal_error(e):
        return handle_internal_server_error(e)

    @app.errorhandler(503)
    def handle_service_unavailable(e):
        return handle_external_api_error(e)

class BusinessException(Exception):
    """业务异常基类"""

    def __init__(self, code: str, message: str, details: Optional[List[ErrorDetail]] = None):
        self.code = code
        self.message = message
        self.details = details or []
        super().__init__(message)

class ValidationException(BusinessException):
    """验证异常"""

    def __init__(self, message: str, field: str = None, value: Any = None):
        details = [ErrorDetail(
            code="VALIDATION_FAILED",
            message=message,
            field=field,
            value=value,
            suggestion="请检查输入数据格式"
        )]
        super().__init__(ErrorCode.VALIDATION_ERROR.value, message, details)

class AuthenticationException(BusinessException):
    """认证异常"""

    def __init__(self, message: str = "认证失败"):
        super().__init__(ErrorCode.AUTHENTICATION_ERROR.value, message)

class AuthorizationException(BusinessException):
    """授权异常"""

    def __init__(self, message: str = "权限不足"):
        super().__init__(ErrorCode.AUTHORIZATION_ERROR.value, message)

class ResourceNotFoundException(BusinessException):
    """资源未找到异常"""

    def __init__(self, resource_type: str, resource_id: Any):
        message = f"{resource_type} (ID: {resource_id}) 不存在"
        super().__init__(ErrorCode.NOT_FOUND.value, message)

class ExternalServiceException(BusinessException):
    """外部服务异常"""

    def __init__(self, service_name: str, message: str = None):
        message = message or f"{service_name} 服务暂时不可用"
        super().__init__(ErrorCode.EXTERNAL_API_ERROR.value, message)

# 业务异常处理装饰器
def handle_business_exceptions(f):
    """业务异常处理装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except BusinessException as e:
            error = create_api_error(
                code=e.code,
                message=e.message,
                details=e.details
            )

            if e.code == ErrorCode.AUTHENTICATION_ERROR.value:
                status_code = 401
            elif e.code == ErrorCode.AUTHORIZATION_ERROR.value:
                status_code = 403
            elif e.code == ErrorCode.NOT_FOUND.value:
                status_code = 404
            elif e.code == ErrorCode.VALIDATION_ERROR.value:
                status_code = 400
            else:
                status_code = 500

            ErrorLogger.log_error(error, "WARNING")
            return APIResponse.error(error, status_code)

    return decorated_function

# 请求ID跟踪中间件
def setup_request_tracking(app):
    """设置请求跟踪"""

    @app.before_request
    def before_request():
        # 只在没有设置的情况下设置，避免覆盖其他监控系统的设置
        if not hasattr(g, 'request_id'):
            g.request_id = str(uuid.uuid4())
        if not hasattr(g, 'start_time'):
            g.start_time = time.time()  # 使用时间戳，与api_monitor保持一致

    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time  # 使用时间戳计算
        else:
            duration = 0

        # 记录请求日志
        logger.info(f"Request {g.request_id}: {request.method} {request.path} - "
                   f"{response.status_code} - {duration:.3f}s")

        # 添加请求ID到响应头
        response.headers['X-Request-ID'] = g.request_id

        return response