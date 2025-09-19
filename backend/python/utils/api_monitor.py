"""
API监控中间件
"""

import time
import logging
from functools import wraps
from flask import request, g, current_app
from datetime import datetime
import json
from typing import Dict, Any, Optional
import uuid

logger = logging.getLogger(__name__)

class APIMonitor:
    """API监控中间件"""
    
    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.slow_requests = []
        self.request_times = []
    
    def init_app(self, app):
        """初始化应用"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.teardown_request(self.teardown_request)
        
        # 添加监控端点
        app.add_url_rule('/api/monitor/stats', 'monitor_stats', self.get_stats, methods=['GET'])
        app.add_url_rule('/api/monitor/health', 'monitor_health', self.health_check, methods=['GET'])
    
    def before_request(self):
        """请求前处理"""
        g.request_id = str(uuid.uuid4())
        g.start_time = time.time()
        
        # 记录请求信息
        logger.info(f"[{g.request_id}] {request.method} {request.path} - {request.remote_addr}")
        
        # 增加请求计数
        self.request_count += 1
        
        # 初始化slow_requests属性如果不存在
        if not hasattr(self, 'slow_requests'):
            self.slow_requests = []
        
        # 记录请求详情
        g.request_info = {
            'request_id': g.request_id,
            'method': request.method,
            'path': request.path,
            'remote_addr': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'start_time': datetime.now().isoformat(),
            'data_size': len(request.data) if request.data else 0,
            'form_data_size': len(request.form) if request.form else 0,
            'query_params': dict(request.args)
        }
    
    def after_request(self, response):
        """请求后处理"""
        if not hasattr(g, 'start_time'):
            return response
        
        # 计算请求耗时
        duration = time.time() - g.start_time
        
        # 记录响应时间
        self.request_times.append(duration)
        if len(self.request_times) > 1000:  # 保持最近1000个请求的时间
            self.request_times.pop(0)
        
        # 记录慢请求
        if duration > 1.0:  # 超过1秒的请求
            self.slow_requests.append({
                'request_id': g.request_id,
                'method': request.method,
                'path': request.path,
                'duration': duration,
                'timestamp': datetime.now().isoformat(),
                'status_code': response.status_code
            })
            
            # 限制慢请求记录数量
            if len(self.slow_requests) > 100:
                self.slow_requests.pop(0)
            
            logger.warning(f"[{g.request_id}] 慢请求警告: {request.method} {request.path} - {duration:.2f}s")
        
        # 记录错误
        if response.status_code >= 400:
            self.error_count += 1
            logger.error(f"[{g.request_id}] 错误响应: {request.method} {request.path} - {response.status_code}")
        
        # 记录请求完成
        logger.info(f"[{g.request_id}] 完成: {request.method} {request.path} - {response.status_code} - {duration:.2f}s")
        
        # 添加请求ID到响应头
        response.headers['X-Request-ID'] = g.request_id
        response.headers['X-Response-Time'] = f"{duration:.3f}s"
        
        return response
    
    def teardown_request(self, exception=None):
        """请求清理"""
        if exception:
            logger.error(f"[{g.request_id}] 请求异常: {request.method} {request.path} - {str(exception)}")
            self.error_count += 1
    
    def get_stats(self):
        """获取监控统计"""
        from flask import jsonify
        
        avg_response_time = 0
        if self.request_times:
            avg_response_time = sum(self.request_times) / len(self.request_times)
        
        # 初始化slow_requests属性如果不存在
        if not hasattr(self, 'slow_requests'):
            self.slow_requests = []
        
        stats = {
            'total_requests': self.request_count,
            'error_count': self.error_count,
            'error_rate': self.error_count / max(self.request_count, 1),
            'avg_response_time': avg_response_time,
            'slow_requests_count': len(self.slow_requests),
            'slow_requests': self.slow_requests[-10:],  # 最近10个慢请求
            'uptime': time.time() - getattr(current_app, 'start_time', time.time()),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(stats)
    
    def health_check(self):
        """健康检查"""
        from flask import jsonify
        
        # 检查数据库连接
        db_status = self.check_database_connection()
        
        # 检查Redis连接
        redis_status = self.check_redis_connection()
        
        # 检查外部API
        external_api_status = self.check_external_apis()
        
        overall_status = 'healthy' if all([
            db_status['status'] == 'ok',
            redis_status['status'] == 'ok',
            external_api_status['status'] == 'ok'
        ]) else 'unhealthy'
        
        return jsonify({
            'status': overall_status,
            'timestamp': datetime.now().isoformat(),
            'services': {
                'database': db_status,
                'redis': redis_status,
                'external_api': external_api_status
            }
        })
    
    def check_database_connection(self) -> Dict[str, Any]:
        """检查数据库连接"""
        try:
            from flask_sqlalchemy import SQLAlchemy
            db = current_app.extensions.get('sqlalchemy')
            if db:
                # 执行简单查询测试连接
                db.session.execute('SELECT 1')
                db.session.commit()
                return {'status': 'ok', 'message': '数据库连接正常'}
            else:
                return {'status': 'warning', 'message': '数据库未配置'}
        except Exception as e:
            logger.error(f"数据库连接检查失败: {str(e)}")
            return {'status': 'error', 'message': f'数据库连接失败: {str(e)}'}
    
    def check_redis_connection(self) -> Dict[str, Any]:
        """检查Redis连接"""
        try:
            from flask_caching import Cache
            cache = current_app.extensions.get('cache')
            if cache:
                # 测试Redis连接
                cache.set('health_check', 'ok', timeout=10)
                value = cache.get('health_check')
                if value == 'ok':
                    return {'status': 'ok', 'message': 'Redis连接正常'}
                else:
                    return {'status': 'error', 'message': 'Redis测试失败'}
            else:
                return {'status': 'warning', 'message': 'Redis未配置'}
        except Exception as e:
            logger.error(f"Redis连接检查失败: {str(e)}")
            return {'status': 'error', 'message': f'Redis连接失败: {str(e)}'}
    
    def check_external_apis(self) -> Dict[str, Any]:
        """检查外部API状态"""
        try:
            import requests
            
            # 检查STRATZ API
            stratz_status = self.check_stratz_api()
            
            # 检查OpenDota API
            opendota_status = self.check_opendota_api()
            
            if stratz_status['status'] == 'ok' or opendota_status['status'] == 'ok':
                return {'status': 'ok', 'message': '至少一个外部API可用', 'details': {
                    'stratz': stratz_status,
                    'opendota': opendota_status
                }}
            else:
                return {'status': 'error', 'message': '外部API均不可用', 'details': {
                    'stratz': stratz_status,
                    'opendota': opendota_status
                }}
        except Exception as e:
            logger.error(f"外部API检查失败: {str(e)}")
            return {'status': 'error', 'message': f'外部API检查失败: {str(e)}'}
    
    def check_stratz_api(self) -> Dict[str, Any]:
        """检查STRATZ API"""
        try:
            import requests
            
            # 简单的API调用测试
            response = requests.get('https://api.stratz.com/api/v1/GameVersion', timeout=5)
            if response.status_code == 200:
                return {'status': 'ok', 'message': 'STRATZ API正常'}
            else:
                return {'status': 'error', 'message': f'STRATZ API返回状态码: {response.status_code}'}
        except Exception as e:
            return {'status': 'error', 'message': f'STRATZ API检查失败: {str(e)}'}
    
    def check_opendota_api(self) -> Dict[str, Any]:
        """检查OpenDota API"""
        try:
            import requests
            
            # 简单的API调用测试
            response = requests.get('https://api.opendota.com/api/heroStats', timeout=5)
            if response.status_code == 200:
                return {'status': 'ok', 'message': 'OpenDota API正常'}
            else:
                return {'status': 'error', 'message': f'OpenDota API返回状态码: {response.status_code}'}
        except Exception as e:
            return {'status': 'error', 'message': f'OpenDota API检查失败: {str(e)}'}
    
    def monitor_route(self, func):
        """路由监控装饰器"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                # 记录函数执行时间
                duration = time.time() - start_time
                if duration > 0.5:  # 超过500ms的函数调用
                    logger.warning(f"慢函数调用: {func.__name__} - {duration:.2f}s")
                
                return result
            except Exception as e:
                logger.error(f"函数 {func.__name__} 执行失败: {str(e)}")
                raise
        
        return wrapper

# 全局监控实例
api_monitor = APIMonitor()

def init_monitor(app):
    """初始化监控中间件"""
    api_monitor.init_app(app)
    app.start_time = time.time()
    
    logger.info("API监控中间件已初始化")

def monitor_performance(func):
    """性能监控装饰器"""
    return api_monitor.monitor_route(func)