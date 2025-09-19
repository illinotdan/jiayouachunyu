# -*- coding: utf-8 -*-
"""
监控相关API蓝图
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.response import ApiResponse
from utils.performance import api_request_count, api_request_duration, api_errors_count
from utils.rate_limiter import rate_limiter
from utils.api_monitor import api_monitor
from utils.decorators import admin_required
import time

monitor_bp = Blueprint('monitor', __name__)

@monitor_bp.route('/api/monitor/stats', methods=['GET'])
@admin_required
def get_monitor_stats():
    """获取API监控统计信息"""
    try:
        stats = {
            'requests': {
                'total': api_request_count._value.get(),
                'rate_per_minute': api_request_count._value.get() / 60,
                'rate_per_hour': api_request_count._value.get() / 3600
            },
            'performance': {
                'average_response_time': api_request_duration._value.get() / max(api_request_count._value.get(), 1),
                'error_rate': api_errors_count._value.get() / max(api_request_count._value.get(), 1),
                'total_errors': api_errors_count._value.get()
            },
            'system': {
                'timestamp': time.time(),
                'uptime': time.time() - getattr(api_monitor, 'start_time', time.time()) if hasattr(api_monitor, 'start_time') else 0
            }
        }
        return ApiResponse.success(stats)
    except Exception as e:
        return ApiResponse.error(f"获取监控统计失败: {str(e)}")

@monitor_bp.route('/api/rate-limit/status', methods=['GET'])
@jwt_required(optional=True)
def get_rate_limit_status():
    """获取当前用户的限流状态"""
    try:
        user_id = get_jwt_identity()
        client_id = user_id if user_id else request.remote_addr
        
        # 获取限流状态
        status = rate_limiter.get_rate_limit_stats()
        
        return ApiResponse.success({
            'client_id': client_id,
            'user_authenticated': bool(user_id),
            'rate_limit_info': status
        })
    except Exception as e:
        return ApiResponse.error(f"获取限流状态失败: {str(e)}")

@monitor_bp.route('/api/cache/stats', methods=['GET'])
@admin_required
def get_cache_stats():
    """获取缓存统计信息"""
    try:
        from utils.api_cache import cache_manager
        stats = cache_manager.get_cache_stats()
        return ApiResponse.success(stats)
    except Exception as e:
        return ApiResponse.error(f"获取缓存统计失败: {str(e)}")

@monitor_bp.route('/api/performance/slow-requests', methods=['GET'])
@admin_required
def get_slow_requests():
    """获取慢请求列表"""
    try:
        slow_requests = api_monitor.get_slow_requests()
        return ApiResponse.success({
            'slow_requests': slow_requests,
            'count': len(slow_requests)
        })
    except Exception as e:
        return ApiResponse.error(f"获取慢请求列表失败: {str(e)}")

@monitor_bp.route('/api/performance/reset-stats', methods=['POST'])
@admin_required
def reset_performance_stats():
    """重置性能统计"""
    try:
        api_request_count._value.set(0)
        api_request_duration._value.set(0)
        api_errors_count._value.set(0)
        
        return ApiResponse.success({'message': '性能统计已重置'})
    except Exception as e:
        return ApiResponse.error(f"重置性能统计失败: {str(e)}")