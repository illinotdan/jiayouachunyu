"""
API响应工具类
"""

from flask import jsonify
from datetime import datetime

class ApiResponse:
    """统一的API响应格式"""
    
    @staticmethod
    def success(data=None, message="操作成功", status_code=200):
        """成功响应"""
        response_data = {
            'success': True,
            'data': data,
            'message': message,
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        }
        
        return jsonify(response_data), status_code
    
    @staticmethod
    def error(message="操作失败", error_code="UNKNOWN_ERROR", status_code=400, details=None):
        """错误响应"""
        response_data = {
            'success': False,
            'error': {
                'code': error_code,
                'message': message,
                'details': details
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(response_data), status_code

# 兼容旧代码的函数
def error_response(message="操作失败", error_code="UNKNOWN_ERROR", status_code=400, details=None):
    """错误响应函数（兼容旧代码）"""
    return ApiResponse.error(message, error_code, status_code, details)

def success_response(data=None, message="操作成功", status_code=200):
    """成功响应函数（兼容旧代码）"""
    return ApiResponse.success(data, message, status_code)
    
    @staticmethod
    def paginated(items, pagination, message="获取成功"):
        """分页响应"""
        return ApiResponse.success({
            'items': items,
            'pagination': {
                'page': pagination.page,
                'pageSize': pagination.per_page,
                'total': pagination.total,
                'totalPages': pagination.pages,
                'hasNext': pagination.has_next,
                'hasPrev': pagination.has_prev
            }
        }, message)

class ErrorCodes:
    """错误代码常量"""
    
    # 通用错误
    UNKNOWN_ERROR = 'UNKNOWN_ERROR'
    VALIDATION_ERROR = 'VALIDATION_ERROR'
    PERMISSION_DENIED = 'PERMISSION_DENIED'
    NOT_FOUND = 'NOT_FOUND'
    
    # 认证错误
    INVALID_CREDENTIALS = 'INVALID_CREDENTIALS'
    TOKEN_EXPIRED = 'TOKEN_EXPIRED'
    TOKEN_INVALID = 'INVALID_TOKEN'
    TOKEN_MISSING = 'MISSING_TOKEN'
    TOKEN_REVOKED = 'TOKEN_REVOKED'
    
    # 用户错误
    USER_NOT_FOUND = 'USER_NOT_FOUND'
    USERNAME_EXISTS = 'USERNAME_EXISTS'
    EMAIL_EXISTS = 'EMAIL_EXISTS'
    WEAK_PASSWORD = 'WEAK_PASSWORD'
    PASSWORD_MISMATCH = 'PASSWORD_MISMATCH'
    ACCOUNT_DISABLED = 'ACCOUNT_DISABLED'
    
    # 内容错误
    CONTENT_NOT_FOUND = 'CONTENT_NOT_FOUND'
    CONTENT_LOCKED = 'CONTENT_LOCKED'
    DUPLICATE_CONTENT = 'DUPLICATE_CONTENT'
    
    # 业务逻辑错误
    MATCH_NOT_FOUND = 'MATCH_NOT_FOUND'
    EXPERT_NOT_FOUND = 'EXPERT_NOT_FOUND'
    DISCUSSION_NOT_FOUND = 'DISCUSSION_NOT_FOUND'
    PREDICTION_EXISTS = 'PREDICTION_EXISTS'
    APPLICATION_EXISTS = 'APPLICATION_EXISTS'
    
    # 系统错误
    DATABASE_ERROR = 'DATABASE_ERROR'
    EXTERNAL_API_ERROR = 'EXTERNAL_API_ERROR'
    FILE_UPLOAD_ERROR = 'FILE_UPLOAD_ERROR'
    RATE_LIMITED = 'RATE_LIMITED'
