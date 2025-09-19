# -*- coding: utf-8 -*-
"""
API版本管理蓝图
"""
from flask import Blueprint, jsonify, request
from utils.response import ApiResponse
from utils.api_version import api_version_manager
from utils.decorators import rate_limit_by_user
from utils.api_cache import cache_route

version_bp = Blueprint('version', __name__)

@version_bp.route('/api/version', methods=['GET'])
@cache_route(cache_type='static', ttl=3600)  # 缓存1小时
@rate_limit_by_user(limit=60, per=60)  # 每分钟60次
def get_api_versions():
    """获取所有API版本信息"""
    try:
        versions = api_version_manager.get_all_versions()
        current_version = api_version_manager.get_current_version()
        
        return ApiResponse.success({
            'current_version': current_version,
            'available_versions': versions,
            'versioning_enabled': True,
            'deprecation_policy': {
                'support_duration_months': 12,
                'notice_period_months': 3
            }
        })
    except Exception as e:
        return ApiResponse.error(f"获取版本信息失败: {str(e)}")

@version_bp.route('/api/version/<version>/info', methods=['GET'])
@cache_route(cache_type='static', ttl=3600)  # 缓存1小时
@rate_limit_by_user(limit=60, per=60)  # 每分钟60次
def get_version_info(version):
    """获取指定版本的详细信息"""
    try:
        version_info = api_version_manager.get_version_info(version)
        
        if not version_info:
            return ApiResponse.error("版本不存在", code=404)
        
        return ApiResponse.success({
            'version': version,
            'status': version_info.get('status', 'unknown'),
            'release_date': version_info.get('release_date'),
            'deprecation_date': version_info.get('deprecation_date'),
            'changes': version_info.get('changes', []),
            'endpoints': version_info.get('endpoints', [])
        })
    except Exception as e:
        return ApiResponse.error(f"获取版本信息失败: {str(e)}")

@version_bp.route('/api/version/<version>/migrate', methods=['POST'])
@rate_limit_by_user(limit=10, per=60)  # 每分钟10次
def migrate_to_version(version):
    """迁移到指定版本"""
    try:
        # 获取迁移信息
        migration_guide = api_version_manager.get_migration_guide(version)
        
        if not migration_guide:
            return ApiResponse.error("版本不存在或无迁移指南", code=404)
        
        return ApiResponse.success({
            'version': version,
            'migration_steps': migration_guide.get('steps', []),
            'breaking_changes': migration_guide.get('breaking_changes', []),
            'deprecated_features': migration_guide.get('deprecated_features', [])
        })
    except Exception as e:
        return ApiResponse.error(f"获取迁移指南失败: {str(e)}")

@version_bp.route('/api/version/changelog', methods=['GET'])
@cache_route(cache_type='static', ttl=1800)  # 缓存30分钟
@rate_limit_by_user(limit=60, per=60)  # 每分钟60次
def get_changelog():
    """获取版本变更日志"""
    try:
        changelog = [
            {
                'version': '1.0.0',
                'date': '2024-01-01',
                'changes': [
                    '初始版本发布',
                    '基础API端点实现',
                    '用户认证系统',
                    '比赛数据分析'
                ]
            },
            {
                'version': '1.1.0', 
                'date': '2024-02-01',
                'changes': [
                    '添加专家分析功能',
                    '社区讨论系统',
                    '实时数据同步',
                    'WebSocket支持'
                ]
            },
            {
                'version': '1.2.0',
                'date': '2024-03-01', 
                'changes': [
                    'API版本管理系统',
                    '性能监控和限流',
                    '缓存优化',
                    '文档自动生成'
                ]
            }
        ]
        
        return ApiResponse.success({
            'changelog': changelog,
            'latest_version': '1.2.0'
        })
    except Exception as e:
        return ApiResponse.error(f"获取变更日志失败: {str(e)}")