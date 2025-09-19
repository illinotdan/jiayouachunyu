"""
API限流器
"""

from flask import request, jsonify, g

# 尝试导入flask_limiter，如果失败则提供替代方案
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    HAS_LIMITER = True
except ImportError:
    HAS_LIMITER = False
    Limiter = None
    get_remote_address = None

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

# 尝试导入redis，如果失败则提供替代方案
try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    redis = None

import json
from functools import wraps

logger = logging.getLogger(__name__)

class APIRateLimiter:
    """API限流器"""
    
    def __init__(self, app=None):
        self.limiter = None
        self.redis_client = None
        self.custom_limits = {}
        self.user_limits = {}
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化应用"""
        # 配置Redis连接
        redis_host = app.config.get('REDIS_HOST', 'localhost')
        redis_port = app.config.get('REDIS_PORT', 6379)
        redis_db = app.config.get('REDIS_DB', 0)
        redis_password = app.config.get('REDIS_PASSWORD')
        
        # 检查Redis是否可用
        if HAS_REDIS:
            try:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    password=redis_password,
                    decode_responses=True
                )
                # 测试连接
                self.redis_client.ping()
                logger.info("Redis连接成功，用于限流存储")
            except Exception as e:
                logger.error(f"Redis连接失败: {str(e)}")
                self.redis_client = None
        else:
            logger.warning("Redis不可用，限流功能将降级为内存模式")
            self.redis_client = None
        
        # 初始化Flask-Limiter
        if HAS_LIMITER:
            try:
                self.limiter = Limiter(
                    app,
                    key_func=self.get_rate_limit_key,
                    storage_uri=f"redis://{redis_host}:{redis_port}/{redis_db}" if redis_password is None else f"redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}",
                    default_limits=["200 per day", "50 per hour"],
                    strategy="fixed-window"
                )
                logger.info("Flask-Limiter初始化成功")
            except Exception as e:
                logger.error(f"Flask-Limiter初始化失败: {str(e)}")
                self.limiter = None
        else:
            logger.warning("Flask-Limiter不可用，使用自定义限流逻辑")
            self.limiter = None
        
        # 配置限流规则
        self.configure_rate_limits()
        
        logger.info("API限流器已初始化")
    
    def get_rate_limit_key(self):
        """获取限流键"""
        # 优先使用用户ID
        if hasattr(g, 'user') and g.user:
            return f"user:{g.user.id}"
        
        # 使用IP地址
        if get_remote_address:
            return f"ip:{get_remote_address()}"
        else:
            # 如果没有get_remote_address，使用request.remote_addr
            return f"ip:{request.remote_addr or 'unknown'}"
    
    def configure_rate_limits(self):
        """配置限流规则"""
        # 用户级别限流
        self.user_limits = {
            'default': ["200 per day", "50 per hour", "10 per minute"],
            'authenticated': ["1000 per day", "200 per hour", "30 per minute"],
            'premium': ["5000 per day", "500 per hour", "100 per minute"],
            'admin': ["unlimited"]
        }
        
        # 端点级别限流
        self.custom_limits = {
            '/api/auth/login': ["5 per minute"],  # 登录接口严格限流
            '/api/auth/register': ["3 per minute"],  # 注册接口严格限流
            '/api/password/reset': ["5 per hour"],  # 密码重置限流
            '/api/upload': ["10 per hour"],  # 文件上传限流
            '/api/matches/sync': ["10 per minute"],  # 数据同步限流
            '/api/ai/analyze': ["20 per hour"],  # AI分析限流
            '/api/learning/train': ["5 per day"],  # 模型训练限流
        }
    
    def get_user_rate_limit(self, user_role: str = 'default') -> List[str]:
        """获取用户级别的限流规则"""
        return self.user_limits.get(user_role, self.user_limits['default'])
    
    def get_endpoint_rate_limit(self, endpoint: str) -> Optional[List[str]]:
        """获取端点级别的限流规则"""
        for pattern, limits in self.custom_limits.items():
            if pattern in endpoint:
                return limits
        return None
    
    def check_rate_limit(self, user_role: str = 'default', endpoint: str = None) -> Dict[str, Any]:
        """检查限流状态"""
        key = self.get_rate_limit_key()
        
        # 获取适用的限流规则
        endpoint_limits = self.get_endpoint_rate_limit(endpoint) if endpoint else None
        user_limits = self.get_user_rate_limit(user_role)
        
        limits = endpoint_limits or user_limits
        
        # 检查是否超限
        current_counts = self.get_current_counts(key, limits)
        
        return {
            'allowed': all(count['remaining'] > 0 for count in current_counts),
            'limits': current_counts,
            'reset_time': self.get_reset_time(limits)
        }
    
    def get_current_counts(self, key: str, limits: List[str]) -> List[Dict[str, Any]]:
        """获取当前计数"""
        counts = []
        
        for limit in limits:
            if limit == "unlimited":
                counts.append({
                    'limit': limit,
                    'remaining': -1,
                    'reset_time': None
                })
                continue
            
            try:
                # 解析限流规则 (例如: "50 per hour")
                parts = limit.split(' per ')
                if len(parts) != 2:
                    continue
                
                max_requests = int(parts[0])
                period = parts[1]
                
                # 计算时间窗口
                current_count = self.get_request_count(key, period)
                remaining = max(0, max_requests - current_count)
                
                counts.append({
                    'limit': limit,
                    'current': current_count,
                    'remaining': remaining,
                    'max': max_requests,
                    'reset_time': self.get_reset_time_for_period(period)
                })
            except Exception as e:
                logger.error(f"解析限流规则失败: {limit} - {str(e)}")
                continue
        
        return counts
    
    def get_request_count(self, key: str, period: str) -> int:
        """获取请求计数"""
        if not self.redis_client:
            return 0
        
        try:
            # 构建Redis键
            period_seconds = self.parse_period(period)
            current_window = int(datetime.now().timestamp() / period_seconds)
            redis_key = f"rate_limit:{key}:{period}:{current_window}"
            
            # 获取计数
            count = self.redis_client.get(redis_key)
            return int(count) if count else 0
        except Exception as e:
            logger.error(f"获取请求计数失败: {key} - {str(e)}")
            return 0
    
    def increment_request_count(self, key: str, period: str):
        """增加请求计数"""
        if not self.redis_client:
            return
        
        try:
            period_seconds = self.parse_period(period)
            current_window = int(datetime.now().timestamp() / period_seconds)
            redis_key = f"rate_limit:{key}:{period}:{current_window}"
            
            # 增加计数并设置过期时间
            pipe = self.redis_client.pipeline()
            pipe.incr(redis_key)
            pipe.expire(redis_key, period_seconds + 1)
            pipe.execute()
        except Exception as e:
            logger.error(f"增加请求计数失败: {key} - {str(e)}")
    
    def parse_period(self, period: str) -> int:
        """解析时间周期"""
        period_map = {
            'second': 1,
            'minute': 60,
            'hour': 3600,
            'day': 86400,
            'week': 604800,
            'month': 2592000
        }
        
        for unit, seconds in period_map.items():
            if unit in period:
                return seconds
        
        return 3600  # 默认1小时
    
    def get_reset_time_for_period(self, period: str) -> datetime:
        """获取重置时间"""
        period_seconds = self.parse_period(period)
        current_window = int(datetime.now().timestamp() / period_seconds)
        next_window_start = (current_window + 1) * period_seconds
        
        return datetime.fromtimestamp(next_window_start)
    
    def get_reset_time(self, limits: List[str]) -> Optional[datetime]:
        """获取最早的重置时间"""
        reset_times = []
        
        for limit in limits:
            if limit != "unlimited" and " per " in limit:
                _, period = limit.split(' per ')
                reset_times.append(self.get_reset_time_for_period(period))
        
        return min(reset_times) if reset_times else None
    
    def rate_limit_by_user_role(self, func):
        """基于用户角色的限流装饰器"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 获取用户角色
            user_role = getattr(g, 'user_role', 'default')
            if hasattr(g, 'user') and g.user:
                user_role = g.user.role or 'authenticated'
            
            # 检查限流
            endpoint = request.path
            status = self.check_rate_limit(user_role, endpoint)
            
            if not status['allowed']:
                # 记录超限日志
                logger.warning(f"用户 {self.get_rate_limit_key()} 触发限流: {endpoint}")
                
                # 返回限流响应
                reset_time = status['limits'][0]['reset_time'] if status['limits'] else None
                
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'RATE_LIMIT_EXCEEDED',
                        'message': '请求过于频繁，请稍后再试',
                        'retry_after': reset_time.isoformat() if reset_time else None
                    }
                }), 429
            
            # 增加计数
            limits = self.get_endpoint_rate_limit(endpoint) or self.get_user_rate_limit(user_role)
            key = self.get_rate_limit_key()
            
            for limit in limits:
                if limit != "unlimited":
                    self.increment_request_count(key, limit.split(' per ')[1])
            
            return func(*args, **kwargs)
        
        return wrapper
    
    def dynamic_rate_limit(self, limits_func):
        """动态限流装饰器"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # 获取动态限流规则
                dynamic_limits = limits_func()
                
                if dynamic_limits:
                    # 临时设置限流规则
                    original_limits = self.custom_limits.get(request.path)
                    self.custom_limits[request.path] = dynamic_limits
                    
                    try:
                        # 检查限流
                        status = self.check_rate_limit()
                        
                        if not status['allowed']:
                            return jsonify({
                                'success': False,
                                'error': {
                                    'code': 'RATE_LIMIT_EXCEEDED',
                                    'message': '请求过于频繁，请稍后再试'
                                }
                            }), 429
                    finally:
                        # 恢复原始限流规则
                        if original_limits:
                            self.custom_limits[request.path] = original_limits
                        else:
                            self.custom_limits.pop(request.path, None)
                
                return func(*args, **kwargs)
            
            return wrapper
        
        return decorator
    
    def get_rate_limit_stats(self) -> Dict[str, Any]:
        """获取限流统计"""
        key = self.get_rate_limit_key()
        user_role = getattr(g, 'user_role', 'default')
        endpoint = request.path
        
        # 检查Redis是否可用
        if not HAS_REDIS or not hasattr(self, 'redis_client') or not self.redis_client:
            return {
                'key': key,
                'user_role': user_role,
                'endpoint': endpoint,
                'rate_limit_status': {
                    'allowed': True,
                    'limits': [],
                    'reset_time': None
                },
                'timestamp': datetime.now().isoformat(),
                'status': 'disabled',
                'note': 'Redis不可用，限流功能已禁用'
            }
        
        try:
            status = self.check_rate_limit(user_role, endpoint)
            
            return {
                'key': key,
                'user_role': user_role,
                'endpoint': endpoint,
                'rate_limit_status': status,
                'timestamp': datetime.now().isoformat(),
                'status': 'active'
            }
        except Exception as e:
            logger.error(f"获取限流统计失败: {str(e)}")
            return {
                'key': key,
                'user_role': user_role,
                'endpoint': endpoint,
                'rate_limit_status': {
                    'allowed': True,
                    'limits': [],
                    'reset_time': None
                },
                'timestamp': datetime.now().isoformat(),
                'status': 'error',
                'error': str(e)
            }

# 全局限流器实例
rate_limiter = APIRateLimiter()

def init_rate_limiter(app):
    """初始化限流器"""
    rate_limiter.init_app(app)
    
    # 添加限流状态端点
    @app.route('/api/rate-limit/status', methods=['GET'])
    def get_rate_limit_status():
        """获取当前限流状态"""
        return jsonify({
            'success': True,
            'data': rate_limiter.get_rate_limit_stats()
        })
    
    logger.info("API限流器已初始化")

# 便捷装饰器
def rate_limit_by_user_role(func):
    """基于用户角色的限流装饰器"""
    return rate_limiter.rate_limit_by_user_role(func)

def dynamic_rate_limit(limits_func):
    """动态限流装饰器"""
    return rate_limiter.dynamic_rate_limit(limits_func)