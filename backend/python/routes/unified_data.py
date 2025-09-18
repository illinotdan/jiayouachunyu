#!/usr/bin/env python3
"""
统一数据服务API路由
提供数据同步、状态查询等功能
"""

from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import asyncio
import random
from typing import Dict, Any

from services.unified_data_service import UnifiedDataService
from config.database import db
from models.audit import AuditLog
from utils.response import ApiResponse
from utils.validators import validate_date_range

# 创建蓝图
unified_data_bp = Blueprint('unified_data', __name__)


def create_audit_log(user_id: int, action: str, resource_type: str, 
                    resource_id: int = None, details: Dict[str, Any] = None):
    """创建审计日志"""
    try:
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            created_at=datetime.utcnow()
        )
        db.session.add(audit_log)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f"创建审计日志失败: {e}")
        db.session.rollback()


@unified_data_bp.route('/sync', methods=['POST'])
@jwt_required()
def sync_data():
    """
    同步数据
    
    请求参数:
        - start_date: 开始日期 (ISO格式, 可选)
        - end_date: 结束日期 (ISO格式, 可选)
        - data_sources: 数据源列表 (可选, 默认全部)
        - sync_type: 同步类型 (可选: 'full', 'incremental', 't1')
    
    返回:
        - 同步结果和状态
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        
        # 解析日期参数
        start_date = None
        end_date = None
        
        if 'start_date' in data:
            try:
                start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
            except ValueError:
                return ApiResponse.error('无效的start_date格式'), 400
        
        if 'end_date' in data:
            try:
                end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
            except ValueError:
                return ApiResponse.error('无效的end_date格式'), 400
        
        # 验证日期范围
        if start_date and end_date and start_date > end_date:
            return ApiResponse.error('开始日期不能晚于结束日期'), 400
        
        # 默认同步最近24小时的数据（T-1策略）
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=1)
        if not end_date:
            end_date = datetime.utcnow()
        
        # 获取同步类型
        sync_type = data.get('sync_type', 't1')
        
        current_app.logger.info(f"用户 {user_id} 请求数据同步: {start_date} 到 {end_date}, 类型: {sync_type}")
        
        # 创建统一数据服务实例
        unified_service = UnifiedDataService()
        
        # 执行同步（使用异步运行器）
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            sync_results = loop.run_until_complete(
                unified_service.sync_all_data(start_date, end_date)
            )
        finally:
            loop.close()
        
        # 构建响应结果
        result = {
            'status': 'success',
            'sync_time': datetime.utcnow().isoformat(),
            'sources_synced': len(sync_results),
            'total_records': sum(r.records_success for r in sync_results.values()),
            'total_errors': sum(len(r.errors) for r in sync_results.values()),
            'execution_time': sum(r.execution_time for r in sync_results.values()),
            'details': {
                source: {
                    'success': result.success,
                    'records_processed': result.records_processed,
                    'records_success': result.records_success,
                    'records_failed': result.records_failed,
                    'errors': result.errors,
                    'execution_time': result.execution_time
                }
                for source, result in sync_results.items()
            }
        }
        
        # 创建审计日志
        create_audit_log(
            user_id=user_id,
            action='sync_data',
            resource_type='data_sync',
            details={
                'sync_type': sync_type,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'result_summary': {
                    'status': result['status'],
                    'sources_synced': result['sources_synced'],
                    'total_records': result['total_records'],
                    'total_errors': result['total_errors']
                }
            }
        )
        
        if result['status'] == 'success':
            current_app.logger.info(f"数据同步成功: {result}")
            return ApiResponse.success(result, '数据同步成功')
        else:
            current_app.logger.error(f"数据同步失败: {result}")
            return ApiResponse.error(f"数据同步失败: {result.get('error', '未知错误')}"), 500
            
    except Exception as e:
        current_app.logger.error(f"数据同步请求处理失败: {e}")
        db.session.rollback()
        return ApiResponse.error(f"数据同步失败: {str(e)}"), 500


@unified_data_bp.route('/sync/status/<sync_id>', methods=['GET'])
@jwt_required()
def get_sync_status(sync_id: str):
    """
    获取同步状态
    
    参数:
        - sync_id: 同步任务ID
    
    返回:
        - 同步状态信息
    """
    try:
        user_id = get_jwt_identity()
        
        # 这里应该查询实际的同步任务状态
        # 暂时返回模拟数据
        status_info = {
            'sync_id': sync_id,
            'status': 'completed',  # pending, running, completed, failed
            'progress': 100,
            'start_time': datetime.utcnow().isoformat(),
            'end_time': datetime.utcnow().isoformat(),
            'results': {
                'matches_synced': random.randint(10, 100),
                'players_synced': random.randint(50, 500),
                'teams_synced': random.randint(5, 20)
            }
        }
        
        return ApiResponse.success(status_info)
        
    except Exception as e:
        current_app.logger.error(f"获取同步状态失败: {e}")
        return ApiResponse.error(f"获取同步状态失败: {str(e)}"), 500


@unified_data_bp.route('/sync/history', methods=['GET'])
@jwt_required()
def get_sync_history():
    """
    获取同步历史
    
    查询参数:
        - page: 页码 (默认: 1)
        - per_page: 每页数量 (默认: 20)
        - start_date: 开始日期
        - end_date: 结束日期
    
    返回:
        - 同步历史记录
    """
    try:
        user_id = get_jwt_identity()
        
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 查询审计日志中的同步记录
        query = AuditLog.query.filter_by(action='sync_data')
        
        # 日期过滤
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.filter(AuditLog.created_at >= start_dt)
            except ValueError:
                return ApiResponse.error('无效的start_date格式'), 400
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.filter(AuditLog.created_at <= end_dt)
            except ValueError:
                return ApiResponse.error('无效的end_date格式'), 400
        
        # 分页
        pagination = query.order_by(AuditLog.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        history = []
        for log in pagination.items:
            history.append({
                'id': log.id,
                'user_id': log.user_id,
                'action': log.action,
                'resource_type': log.resource_type,
                'details': log.details,
                'created_at': log.created_at.isoformat()
            })
        
        return ApiResponse.success({
            'history': history,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"获取同步历史失败: {e}")
        return ApiResponse.error(f"获取同步历史失败: {str(e)}"), 500


@unified_data_bp.route('/data-quality', methods=['GET'])
@jwt_required()
def get_data_quality():
    """
    获取数据质量报告
    
    查询参数:
        - data_source: 数据源 (可选)
        - date_range: 日期范围 (可选: '1d', '7d', '30d')
    
    返回:
        - 数据质量报告
    """
    try:
        user_id = get_jwt_identity()
        
        data_source = request.args.get('data_source')
        date_range = request.args.get('date_range', '7d')
        
        # 计算日期范围
        end_date = datetime.utcnow()
        if date_range == '1d':
            start_date = end_date - timedelta(days=1)
        elif date_range == '7d':
            start_date = end_date - timedelta(days=7)
        elif date_range == '30d':
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=7)
        
        # 这里应该查询实际的数据质量指标
        # 暂时返回模拟数据
        quality_report = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'overall_score': random.uniform(0.7, 0.95),
            'data_sources': {
                'opendota': {
                    'score': random.uniform(0.8, 0.95),
                    'completeness': random.uniform(0.85, 0.98),
                    'accuracy': random.uniform(0.9, 0.99),
                    'timeliness': random.uniform(0.7, 0.9),
                    'consistency': random.uniform(0.8, 0.95)
                },
                'stratz': {
                    'score': random.uniform(0.75, 0.92),
                    'completeness': random.uniform(0.8, 0.95),
                    'accuracy': random.uniform(0.85, 0.98),
                    'timeliness': random.uniform(0.8, 0.95),
                    'consistency': random.uniform(0.75, 0.9)
                },
                'liquipedia': {
                    'score': random.uniform(0.8, 0.93),
                    'completeness': random.uniform(0.75, 0.9),
                    'accuracy': random.uniform(0.95, 0.99),
                    'timeliness': random.uniform(0.6, 0.85),
                    'consistency': random.uniform(0.85, 0.98)
                }
            },
            'issues': [
                {
                    'type': 'missing_data',
                    'severity': 'medium',
                    'description': '部分比赛缺少选手详细数据',
                    'affected_records': random.randint(10, 50),
                    'suggestion': '建议从多个数据源获取数据以提高完整性'
                },
                {
                    'type': 'data_delay',
                    'severity': 'low',
                    'description': 'STRATZ数据源更新延迟',
                    'affected_records': random.randint(5, 20),
                    'suggestion': '考虑增加数据源或调整同步频率'
                }
            ]
        }
        
        return ApiResponse.success(quality_report)
        
    except Exception as e:
        current_app.logger.error(f"获取数据质量报告失败: {e}")
        return ApiResponse.error(f"获取数据质量报告失败: {str(e)}"), 500


@unified_data_bp.route('/data-sources', methods=['GET'])
@jwt_required()
def get_data_sources():
    """
    获取数据源状态
    
    返回:
        - 数据源状态和配置信息
    """
    try:
        user_id = get_jwt_identity()
        
        # 数据源状态信息
        data_sources = {
            'opendota': {
                'name': 'OpenDota',
                'status': 'active',
                'last_sync': datetime.utcnow().isoformat(),
                'api_key_configured': bool(current_app.config.get('OPENDOTA_API_KEY')),
                'rate_limit': current_app.config.get('DATA_SYNC_RATE_LIMIT', 10),
                'priority': 1,
                'description': '提供详细的比赛数据和选手统计信息'
            },
            'stratz': {
                'name': 'STRATZ',
                'status': 'active',
                'last_sync': datetime.utcnow().isoformat(),
                'api_key_configured': bool(current_app.config.get('STRATZ_API_KEY')),
                'rate_limit': current_app.config.get('DATA_SYNC_RATE_LIMIT', 10),
                'priority': 2,
                'description': '提供高质量的比赛分析和选手数据'
            },
            'liquipedia': {
                'name': 'Liquipedia',
                'status': 'active',
                'last_sync': datetime.utcnow().isoformat(),
                'api_key_configured': True,  # Liquipedia通常不需要API密钥
                'rate_limit': current_app.config.get('DATA_SYNC_RATE_LIMIT', 10),
                'priority': 3,
                'description': '提供赛事信息和战队数据'
            }
        }
        
        return ApiResponse.success(data_sources)
        
    except Exception as e:
        current_app.logger.error(f"获取数据源状态失败: {e}")
        return ApiResponse.error(f"获取数据源状态失败: {str(e)}"), 500


@unified_data_bp.route('/sync/t1', methods=['POST'])
@jwt_required()
def sync_t1_data():
    """
    执行T-1数据同步（同步最近24小时的数据）
    
    这是专门为T-1策略设计的快捷同步接口
    
    返回:
        - T-1同步结果
    """
    try:
        user_id = get_jwt_identity()
        
        current_app.logger.info(f"用户 {user_id} 请求T-1数据同步")
        
        # 设置T-1时间范围
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=1)
        
        # 创建统一数据服务实例
        unified_service = UnifiedDataService()
        
        # 执行同步
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                unified_service.sync_all_data(start_date, end_date)
            )
        finally:
            loop.close()
        
        # 创建审计日志
        create_audit_log(
            user_id=user_id,
            action='sync_t1_data',
            resource_type='data_sync',
            details={
                'sync_type': 't1',
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'result': result
            }
        )
        
        if result['status'] == 'success':
            current_app.logger.info(f"T-1数据同步成功")
            return ApiResponse.success(result, 'T-1数据同步成功')
        else:
            current_app.logger.error(f"T-1数据同步失败: {result}")
            return ApiResponse.error(f"T-1数据同步失败: {result.get('error', '未知错误')}"), 500
            
    except Exception as e:
        current_app.logger.error(f"T-1数据同步请求处理失败: {e}")
        return ApiResponse.error(f"T-1数据同步失败: {str(e)}"), 500


@unified_data_bp.route('/liquipedia/team/<team_name>', methods=['GET'])
@jwt_required()
def get_liquipedia_team(team_name: str):
    """
    获取Liquipedia战队信息
    
    参数:
        - team_name: 战队名称
    
    查询参数:
        - sync_to_db: 是否同步到数据库 (可选, 默认: false)
    
    返回:
        - Liquipedia战队数据
    """
    try:
        user_id = get_jwt_identity()
        sync_to_db = request.args.get('sync_to_db', 'false').lower() == 'true'
        
        current_app.logger.info(f"用户 {user_id} 请求Liquipedia战队信息: {team_name}, 同步到DB: {sync_to_db}")
        
        # 创建统一数据服务实例
        unified_service = UnifiedDataService()
        
        # 获取战队信息
        team_data = unified_service.liquipedia.get_team_info(team_name)
        
        if not team_data:
            return ApiResponse.error(f'未找到战队 "{team_name}" 的信息'), 404
        
        # 如果需要同步到数据库
        if sync_to_db:
            try:
                unified_service._process_team_from_liquipedia(team_data)
                current_app.logger.info(f"战队 {team_name} 信息已同步到数据库")
            except Exception as e:
                current_app.logger.error(f"同步战队 {team_name} 到数据库失败: {e}")
                # 不返回错误，继续返回数据
        
        # 创建审计日志
        create_audit_log(
            user_id=user_id,
            action='get_liquipedia_team',
            resource_type='liquipedia_data',
            details={
                'team_name': team_name,
                'sync_to_db': sync_to_db,
                'data_found': True
            }
        )
        
        return ApiResponse.success(team_data, f'成功获取战队 "{team_name}" 的信息')
        
    except Exception as e:
        current_app.logger.error(f"获取Liquipedia战队信息失败: {e}")
        return ApiResponse.error(f"获取战队信息失败: {str(e)}"), 500


@unified_data_bp.route('/liquipedia/search', methods=['GET'])
@jwt_required()
def search_liquipedia_teams():
    """
    搜索Liquipedia战队
    
    查询参数:
        - q: 搜索关键词 (必需)
        - limit: 返回数量限制 (可选, 默认: 10)
    
    返回:
        - 搜索结果列表
    """
    try:
        user_id = get_jwt_identity()
        
        # 获取查询参数
        query = request.args.get('q', '').strip()
        limit = request.args.get('limit', 10, type=int)
        
        if not query:
            return ApiResponse.error('搜索关键词不能为空'), 400
        
        if limit < 1 or limit > 50:
            return ApiResponse.error('limit参数必须在1-50之间'), 400
        
        current_app.logger.info(f"用户 {user_id} 搜索Liquipedia战队: {query}, limit: {limit}")
        
        # 创建统一数据服务实例
        unified_service = UnifiedDataService()
        
        # 搜索战队
        search_results = unified_service.liquipedia.search_teams(query, limit)
        
        # 创建审计日志
        create_audit_log(
            user_id=user_id,
            action='search_liquipedia_teams',
            resource_type='liquipedia_data',
            details={
                'query': query,
                'limit': limit,
                'results_count': len(search_results)
            }
        )
        
        return ApiResponse.success({
            'query': query,
            'results': search_results,
            'count': len(search_results)
        }, f'搜索完成，找到 {len(search_results)} 个结果')
        
    except Exception as e:
        current_app.logger.error(f"搜索Liquipedia战队失败: {e}")
        return ApiResponse.error(f"搜索失败: {str(e)}"), 500