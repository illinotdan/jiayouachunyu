"""
装饰器工具
"""
import datetime
from functools import wraps
from flask import request, current_app, g
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    HAS_LIMITER = True
except ImportError:
    HAS_LIMITER = False
    Limiter = None
    get_remote_address = None

try:
    from flask_caching import Cache
    HAS_CACHE = True
except ImportError:
    HAS_CACHE = False
    Cache = None
try:
    from flask_jwt_extended import get_jwt_identity
    HAS_JWT = True
except ImportError:
    HAS_JWT = False
    get_jwt_identity = None

import hashlib
import json

# 初始化限流器
if HAS_LIMITER:
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["100 per minute"]
    )
else:
    limiter = None

# 初始化缓存
if HAS_CACHE:
    cache = Cache()
else:
    cache = None

def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            from flask_jwt_extended import jwt_required, get_jwt_identity
            from ..models.user import User, UserRole
            
            # 首先检查JWT
            jwt_required()(lambda: None)()
            
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            if not user or user.role != UserRole.ADMIN:
                from ..utils.response import ApiResponse
                return ApiResponse.error('需要管理员权限', 'ADMIN_REQUIRED', 403)
            
            g.current_user = user
            return f(*args, **kwargs)
            
        except Exception as e:
            from ..utils.response import ApiResponse
            return ApiResponse.error('权限验证失败', 'AUTH_FAILED', 401)
    
    return decorated_function

def expert_required(f):
    """专家权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            from flask_jwt_extended import jwt_required, get_jwt_identity
            from ..models.user import User, UserRole
            
            # 首先检查JWT
            jwt_required()(lambda: None)()
            
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            if not user or user.role not in [UserRole.EXPERT, UserRole.ADMIN]:
                from ..utils.response import ApiResponse
                return ApiResponse.error('需要专家权限', 'EXPERT_REQUIRED', 403)
            
            g.current_user = user
            return f(*args, **kwargs)
            
        except Exception as e:
            from ..utils.response import ApiResponse
            return ApiResponse.error('权限验证失败', 'AUTH_FAILED', 401)
    
    return decorated_function

def cache_key_with_user(*args, **kwargs):
    """为缓存生成包含用户信息的键"""
    try:
        user_id = get_jwt_identity() if HAS_JWT and get_jwt_identity else 'anonymous'
    except:
        user_id = 'anonymous'
    
    # 包含请求参数的缓存键
    cache_data = {
        'user_id': user_id,
        'args': request.args.to_dict(),
        'path': request.path
    }
    
    cache_string = json.dumps(cache_data, sort_keys=True)
    return hashlib.md5(cache_string.encode()).hexdigest()

def user_cache(timeout=300):
    """用户相关的缓存装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not HAS_CACHE or not cache:
                # 如果没有缓存，直接执行函数
                return f(*args, **kwargs)
                
            # 生成缓存键
            cache_key = f"user_cache:{cache_key_with_user()}"
            
            # 尝试从缓存获取
            cached_result = cache.get(cache_key)
            if cached_result:
                return cached_result
            
            # 执行函数并缓存结果
            result = f(*args, **kwargs)
            cache.set(cache_key, result, timeout=timeout)
            
            return result
        
        return decorated_function
    return decorator

def log_api_call(f):
    """API调用日志装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = datetime.utcnow()
        
        try:
            # 记录请求信息
            current_app.logger.info(
                f"API调用: {request.method} {request.path} - "
                f"IP: {request.remote_addr} - "
                f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}"
            )
            
            # 执行函数
            result = f(*args, **kwargs)
            
            # 记录响应时间
            duration = (datetime.utcnow() - start_time).total_seconds()
            current_app.logger.info(f"API响应: {request.path} - 耗时: {duration:.3f}s")
            
            return result
            
        except Exception as e:
            # 记录错误
            duration = (datetime.utcnow() - start_time).total_seconds()
            current_app.logger.error(
                f"API错误: {request.path} - 耗时: {duration:.3f}s - 错误: {str(e)}"
            )
            raise
    
    return decorated_function

def validate_json(required_fields=None):
    """JSON数据验证装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                from ..utils.response import ApiResponse
                return ApiResponse.error('请求必须是JSON格式', 'INVALID_JSON', 400)
            
            if required_fields:
                missing_fields = []
                for field in required_fields:
                    if field not in request.json:
                        missing_fields.append(field)
                
                if missing_fields:
                    from ..utils.response import ApiResponse
                    return ApiResponse.error(
                        f'缺少必需字段: {", ".join(missing_fields)}',
                        'MISSING_FIELDS',
                        400
                    )
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def rate_limit_by_user(limit_string):
    """基于用户的限流装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not HAS_LIMITER or not limiter:
                # 如果没有限流器，直接执行函数
                return f(*args, **kwargs)
                
            try:
                user_id = get_jwt_identity() if HAS_JWT and get_jwt_identity else None
                if user_id:
                    # 为认证用户使用更宽松的限制
                    return limiter.limit(limit_string, key_func=lambda: str(user_id))(f)(*args, **kwargs)
                else:
                    # 匿名用户使用更严格的限制
                    return limiter.limit("10 per minute")(f)(*args, **kwargs)
            except:
                # 如果JWT验证失败，使用IP限流
                return limiter.limit("10 per minute")(f)(*args, **kwargs)
        
        return decorated_function
    return decorator

def require_auth(f):
    """需要认证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            from flask_jwt_extended import jwt_required, get_jwt_identity
            from ..models.user import User
            
            # 首先检查JWT
            jwt_required()(lambda: None)()
            
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            if not user:
                from ..utils.response import ApiResponse
                return ApiResponse.error('用户不存在', 'USER_NOT_FOUND', 404)
            
            g.current_user = user
            return f(*args, **kwargs)
            
        except Exception as e:
            from ..utils.response import ApiResponse
            return ApiResponse.error('认证失败', 'AUTH_FAILED', 401)
    
    return decorated_function

def rate_limit(limit_string="100 per minute"):
    """通用限流装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not HAS_LIMITER or not limiter:
                # 如果没有限流器，直接执行函数
                return f(*args, **kwargs)
            return limiter.limit(limit_string)(f)(*args, **kwargs)
        return decorated_function
    return decorator

def cache_result(timeout=300):
    """缓存结果装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not HAS_CACHE or not cache:
                # 如果没有缓存，直接执行函数
                return f(*args, **kwargs)
                
            # 生成缓存键
            cache_key = f"cache_result:{f.__name__}:{str(args)}:{str(kwargs)}"
            
            # 尝试从缓存获取
            cached_result = cache.get(cache_key)
            if cached_result:
                return cached_result
            
            # 执行函数并缓存结果
            result = f(*args, **kwargs)
            cache.set(cache_key, result, timeout=timeout)
            
            return result
        
        return decorated_function
    return decorator

def monitor_performance(f):
    """性能监控装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        import time
        start_time = time.time()
        
        try:
            result = f(*args, **kwargs)
            duration = time.time() - start_time
            
            # 记录性能信息
            if current_app:
                current_app.logger.info(f"性能监控: {f.__name__} - 耗时: {duration:.3f}s")
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            if current_app:
                current_app.logger.error(f"性能监控错误: {f.__name__} - 耗时: {duration:.3f}s - 错误: {str(e)}")
            raise
    
    return decorated_function
