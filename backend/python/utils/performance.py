"""
API性能监控工具
"""

import time
import functools
from flask import request, current_app, g
from prometheus_flask_exporter import PrometheusMetrics
import logging

# 全局指标实例
metrics = None

def init_metrics(app):
    """初始化Prometheus指标监控"""
    global metrics
    
    metrics = PrometheusMetrics(app, defaults_prefix='dota_api')
    
    # 自定义指标
    metrics.register_default(
        metrics.counter(
            'api_requests_total',
            'Total API requests',
            labels={'endpoint': lambda: request.endpoint, 'method': lambda: request.method}
        )
    )
    
    metrics.register_default(
        metrics.histogram(
            'api_request_duration_seconds',
            'API request duration in seconds',
            labels={'endpoint': lambda: request.endpoint, 'method': lambda: request.method}
        )
    )
    
    metrics.register_default(
        metrics.counter(
            'api_errors_total',
            'Total API errors',
            labels={'endpoint': lambda: request.endpoint, 'error_type': lambda: g.get('error_type', 'unknown')}
        )
    )
    
    # 用户相关指标
    metrics.register_default(
        metrics.counter(
            'user_actions_total',
            'Total user actions',
            labels={'action': lambda: g.get('user_action', 'unknown'), 'user_id': lambda: g.get('user_id', 'anonymous')}
        )
    )
    
    return metrics

def track_performance(f):
    """API性能跟踪装饰器"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = f(*args, **kwargs)
            
            # 记录成功响应时间
            duration = time.time() - start_time
            if metrics:
                metrics.histogram('api_success_duration_seconds').observe(duration)
            
            current_app.logger.info(f"API性能: {request.endpoint} - 耗时: {duration:.3f}s")
            
            return result
            
        except Exception as e:
            # 记录错误和响应时间
            duration = time.time() - start_time
            g.error_type = type(e).__name__
            
            if metrics:
                metrics.counter('api_errors_total').inc()
                metrics.histogram('api_error_duration_seconds').observe(duration)
            
            current_app.logger.error(f"API错误性能: {request.endpoint} - 耗时: {duration:.3f}s - 错误: {str(e)}")
            
            raise
    
    return decorated_function

def track_user_action(action_name):
    """用户行为跟踪装饰器"""
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            g.user_action = action_name
            
            try:
                from flask_jwt_extended import get_jwt_identity
                user_id = get_jwt_identity()
                g.user_id = user_id or 'anonymous'
            except:
                g.user_id = 'anonymous'
            
            if metrics:
                metrics.counter('user_actions_total').inc()
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics_data = {}
    
    def start_timer(self, name):
        """开始计时"""
        self.metrics_data[f"{name}_start"] = time.time()
    
    def end_timer(self, name):
        """结束计时并返回耗时"""
        start_key = f"{name}_start"
        if start_key in self.metrics_data:
            duration = time.time() - self.metrics_data[start_key]
            del self.metrics_data[start_key]
            
            current_app.logger.info(f"性能指标: {name} - 耗时: {duration:.3f}s")
            return duration
        
        return None
    
    def record_metric(self, name, value):
        """记录指标值"""
        current_app.logger.info(f"性能指标: {name} = {value}")
        
        if metrics:
            metrics.gauge(name).set(value)
    
    def increment_counter(self, name, value=1):
        """增加计数器"""
        if metrics:
            metrics.counter(name).inc(value)

# 全局性能监控器实例
performance_monitor = PerformanceMonitor()

def log_slow_requests(threshold=1.0):
    """记录慢请求"""
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            result = f(*args, **kwargs)
            duration = time.time() - start_time
            
            if duration > threshold:
                current_app.logger.warning(
                    f"慢请求警告: {request.endpoint} - 耗时: {duration:.3f}s "
                    f"(阈值: {threshold}s) - IP: {request.remote_addr}"
                )
            
            return result
        
        return decorated_function
    return decorator