"""
API缓存管理器
"""

import json
import logging
import hashlib
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta

# 尝试导入redis，如果失败则提供替代方案
try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    redis = None

from flask import request, jsonify, current_app, g
from functools import wraps
import pickle

logger = logging.getLogger(__name__)

class APICacheManager:
    """API缓存管理器"""
    
    def __init__(self, app=None):
        self.redis_client = None
        self.cache_config = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化应用"""
        # 配置Redis连接
        redis_host = app.config.get('REDIS_HOST', 'localhost')
        redis_port = app.config.get('REDIS_PORT', 6379)
        redis_db = app.config.get('REDIS_DB', 1)  # 使用不同的数据库
        redis_password = app.config.get('REDIS_PASSWORD')
        
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
                logger.info("Redis连接成功，用于API缓存")
            except Exception as e:
                logger.error(f"Redis连接失败: {str(e)}")
                self.redis_client = None
        else:
            logger.warning("Redis不可用，API缓存功能将受限")
            self.redis_client = None
        
        # 配置缓存策略
        self.configure_cache_policies()
        
        # 添加缓存管理端点
        app.add_url_rule('/api/cache/stats', 'cache_stats', self.get_cache_stats, methods=['GET'])
        app.add_url_rule('/api/cache/clear', 'cache_clear', self.clear_cache, methods=['POST'])
        
        logger.info("API缓存管理器已初始化")
    
    def configure_cache_policies(self):
        """配置缓存策略"""
        self.cache_config = {
            # 默认缓存策略
            'default': {
                'ttl': 300,  # 5分钟
                'key_prefix': 'api:cache:',
                'compress': True,
                'serialize': 'json'
            },
            
            # 用户相关数据
            'user': {
                'ttl': 1800,  # 30分钟
                'key_prefix': 'api:cache:user:',
                'compress': True,
                'serialize': 'pickle'
            },
            
            # 比赛数据
            'match': {
                'ttl': 600,  # 10分钟
                'key_prefix': 'api:cache:match:',
                'compress': True,
                'serialize': 'json'
            },
            
            # 统计数据
            'stats': {
                'ttl': 3600,  # 1小时
                'key_prefix': 'api:cache:stats:',
                'compress': True,
                'serialize': 'json'
            },
            
            # 静态数据
            'static': {
                'ttl': 86400,  # 24小时
                'key_prefix': 'api:cache:static:',
                'compress': True,
                'serialize': 'json'
            },
            
            # 实时数据
            'realtime': {
                'ttl': 60,  # 1分钟
                'key_prefix': 'api:cache:realtime:',
                'compress': False,
                'serialize': 'json'
            }
        }
    
    def generate_cache_key(self, cache_type: str = 'default', **kwargs) -> str:
        """生成缓存键"""
        # 基础信息
        key_parts = [
            request.method,
            request.path,
            str(hash(frozenset(request.args.items()))),
            str(hash(frozenset(request.form.items())))
        ]
        
        # 添加用户信息
        if hasattr(g, 'user') and g.user:
            key_parts.append(f"user:{g.user.id}")
        
        # 添加额外参数
        for key, value in kwargs.items():
            key_parts.append(f"{key}:{value}")
        
        # 生成哈希
        key_string = '|'.join(key_parts)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        
        # 添加前缀
        config = self.cache_config.get(cache_type, self.cache_config['default'])
        cache_key = f"{config['key_prefix']}{key_hash}"
        
        return cache_key
    
    def get_cache_key_pattern(self, cache_type: str = 'default', user_id: int = None) -> str:
        """获取缓存键模式"""
        config = self.cache_config.get(cache_type, self.cache_config['default'])
        
        if user_id:
            return f"{config['key_prefix']}*user:{user_id}*"
        else:
            return f"{config['key_prefix']}*"
    
    def serialize_data(self, data: Any, serialize_method: str = 'json') -> str:
        """序列化数据"""
        try:
            if serialize_method == 'json':
                return json.dumps(data, ensure_ascii=False, default=str)
            elif serialize_method == 'pickle':
                return pickle.dumps(data).hex()
            else:
                return str(data)
        except Exception as e:
            logger.error(f"数据序列化失败: {str(e)}")
            return json.dumps(data, default=str)
    
    def deserialize_data(self, data: str, serialize_method: str = 'json') -> Any:
        """反序列化数据"""
        try:
            if serialize_method == 'json':
                return json.loads(data)
            elif serialize_method == 'pickle':
                return pickle.loads(bytes.fromhex(data))
            else:
                return data
        except Exception as e:
            logger.error(f"数据反序列化失败: {str(e)}")
            return data
    
    def get(self, key: str, cache_type: str = 'default') -> Optional[Any]:
        """获取缓存数据"""
        if not self.redis_client:
            return None
        
        try:
            data = self.redis_client.get(key)
            if data:
                self.cache_stats['hits'] += 1
                
                config = self.cache_config.get(cache_type, self.cache_config['default'])
                return self.deserialize_data(data, config['serialize'])
            else:
                self.cache_stats['misses'] += 1
                return None
        except Exception as e:
            logger.error(f"获取缓存失败: {key} - {str(e)}")
            return None
    
    def set(self, key: str, data: Any, cache_type: str = 'default', ttl: int = None) -> bool:
        """设置缓存数据"""
        if not self.redis_client:
            return False
        
        try:
            config = self.cache_config.get(cache_type, self.cache_config['default'])
            
            # 序列化数据
            serialized_data = self.serialize_data(data, config['serialize'])
            
            # 设置过期时间
            expire_time = ttl or config['ttl']
            
            # 存储数据
            result = self.redis_client.setex(key, expire_time, serialized_data)
            
            if result:
                self.cache_stats['sets'] += 1
                logger.debug(f"缓存设置成功: {key} (TTL: {expire_time}s)")
            
            return bool(result)
        except Exception as e:
            logger.error(f"设置缓存失败: {key} - {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self.redis_client:
            return False
        
        try:
            result = self.redis_client.delete(key)
            if result:
                self.cache_stats['deletes'] += 1
                logger.debug(f"缓存删除成功: {key}")
            
            return bool(result)
        except Exception as e:
            logger.error(f"删除缓存失败: {key} - {str(e)}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """删除匹配模式的缓存"""
        if not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted_count = self.redis_client.delete(*keys)
                self.cache_stats['deletes'] += deleted_count
                logger.info(f"批量删除缓存成功: {pattern} ({deleted_count} 个)")
                return deleted_count
            return 0
        except Exception as e:
            logger.error(f"批量删除缓存失败: {pattern} - {str(e)}")
            return 0
    
    def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"检查缓存存在失败: {key} - {str(e)}")
            return False
    
    def ttl(self, key: str) -> int:
        """获取缓存剩余时间"""
        if not self.redis_client:
            return -2
        
        try:
            return self.redis_client.ttl(key)
        except Exception as e:
            logger.error(f"获取缓存TTL失败: {key} - {str(e)}")
            return -2
    
    def get_cache_stats(self):
        """获取缓存统计"""
        # 初始化缓存统计属性如果不存在
        if not hasattr(self, 'cache_stats'):
            self.cache_stats = {
                'hits': 0,
                'misses': 0,
                'sets': 0,
                'deletes': 0
            }
        if not hasattr(self, 'cache_type'):
            self.cache_type = 'simple'
        if not hasattr(self, 'enabled'):
            self.enabled = True

        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = self.cache_stats['hits'] / max(total_requests, 1)

        # 获取Redis信息
        redis_info = {}
        if self.redis_client:
            try:
                info = self.redis_client.info()
                redis_info = {
                    'used_memory_human': info.get('used_memory_human', 'N/A'),
                    'connected_clients': info.get('connected_clients', 0),
                    'total_commands_processed': info.get('total_commands_processed', 0)
                }
            except Exception as e:
                logger.error(f"获取Redis信息失败: {str(e)}")

        return jsonify({
            'success': True,
            'data': {
                'stats': self.cache_stats,
                'hit_rate': hit_rate,
                'total_requests': total_requests,
                'redis_info': redis_info,
                'cache_type': self.cache_type,
                'enabled': self.enabled,
                'timestamp': datetime.now().isoformat()
            }
        })
    
    def clear_cache(self):
        """清理缓存"""
        try:
            # 删除所有API缓存
            patterns = [
                'api:cache:*',
                'api:cache:user:*',
                'api:cache:match:*',
                'api:cache:stats:*',
                'api:cache:static:*',
                'api:cache:realtime:*'
            ]
            
            total_deleted = 0
            for pattern in patterns:
                deleted = self.delete_pattern(pattern)
                total_deleted += deleted
            
            # 重置统计
            self.cache_stats = {
                'hits': 0,
                'misses': 0,
                'sets': 0,
                'deletes': 0
            }
            
            logger.info(f"缓存清理完成，共删除 {total_deleted} 个缓存项")
            
            return jsonify({
                'success': True,
                'data': {
                    'deleted_count': total_deleted,
                    'message': '缓存清理完成'
                }
            })
        except Exception as e:
            logger.error(f"缓存清理失败: {str(e)}")
            return jsonify({
                'success': False,
                'error': {
                    'code': 'CACHE_CLEAR_ERROR',
                    'message': f'缓存清理失败: {str(e)}'
                }
            }), 500
    
    def cache_route(self, cache_type: str = 'default', ttl: int = None, key_params: List[str] = None):
        """路由缓存装饰器"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # 生成缓存键
                cache_key_kwargs = {}
                if key_params:
                    for param in key_params:
                        if param in kwargs:
                            cache_key_kwargs[param] = kwargs[param]
                
                cache_key = self.generate_cache_key(cache_type, **cache_key_kwargs)
                
                # 检查缓存
                cached_data = self.get(cache_key, cache_type)
                if cached_data is not None:
                    logger.debug(f"缓存命中: {cache_key}")
                    return cached_data
                
                # 执行函数
                result = func(*args, **kwargs)
                
                # 缓存结果
                if result and hasattr(result, 'status_code') and result.status_code == 200:
                    # 尝试解析响应数据
                    try:
                        if hasattr(result, 'get_json'):
                            data = result.get_json()
                        elif hasattr(result, 'data'):
                            data = json.loads(result.data)
                        else:
                            data = result
                        
                        self.set(cache_key, data, cache_type, ttl)
                        logger.debug(f"缓存设置: {cache_key}")
                    except Exception as e:
                        logger.warning(f"缓存响应数据失败: {str(e)}")
                
                return result
            
            return wrapper
        
        return decorator
    
    def cache_invalidate(self, cache_type: str = 'default', user_id: int = None):
        """缓存失效装饰器"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # 执行函数
                result = func(*args, **kwargs)
                
                # 清理相关缓存
                pattern = self.get_cache_key_pattern(cache_type, user_id)
                deleted_count = self.delete_pattern(pattern)
                
                if deleted_count > 0:
                    logger.info(f"缓存失效: {pattern} ({deleted_count} 个)")
                
                return result
            
            return wrapper
        
        return decorator

# 全局缓存管理器实例
api_cache = APICacheManager()

def init_cache_manager(app):
    """初始化缓存管理器"""
    api_cache.init_app(app)
    logger.info("API缓存管理器已初始化")

# 便捷装饰器
def cache_route(cache_type: str = 'default', ttl: int = None, key_params: List[str] = None):
    """路由缓存装饰器"""
    return api_cache.cache_route(cache_type, ttl, key_params)

def cache_invalidate(cache_type: str = 'default', user_id: int = None):
    """缓存失效装饰器"""
    return api_cache.cache_invalidate(cache_type, user_id)