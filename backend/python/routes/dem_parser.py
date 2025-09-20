"""
DEM解析API路由
提供DEM解析服务的HTTP接口
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from services.dem_parser_service import DEMParserService
from models.audit import AuditLog
from utils.response import ApiResponse
from utils.decorators import admin_required  # 使用admin_required替代require_role
from config.database import db

import logging
logger = logging.getLogger(__name__)

# 创建蓝图
dem_parser_bp = Blueprint('dem_parser', __name__, url_prefix='/api/dem')

def create_audit_log(user_id: int, action: str, resource_type: str, 
                    resource_id: int = None, details: dict = None):
    """创建审计日志"""
    try:
        audit = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            timestamp=datetime.utcnow()
        )
        db.session.add(audit)
        db.session.commit()
    except Exception as e:
        logger.error(f"创建审计日志失败: {e}")
        db.session.rollback()

@dem_parser_bp.route('/start-workflow', methods=['POST'])
@jwt_required()
@admin_required
def start_dem_parsing_workflow():
    """
    启动DEM解析工作流程
    
    POST /api/dem/start-workflow
    {
        "days_back": 7,
        "limit": 50,
        "max_concurrent": 3
    }
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        
        # 参数验证
        days_back = data.get('days_back', 7)
        limit = data.get('limit', 50)
        max_concurrent = data.get('max_concurrent', 3)
        
        # 参数范围检查
        if not 1 <= days_back <= 30:
            return ApiResponse.error("days_back参数必须在1-30之间", code=400)
        
        if not 1 <= limit <= 200:
            return ApiResponse.error("limit参数必须在1-200之间", code=400)
        
        if not 1 <= max_concurrent <= 10:
            return ApiResponse.error("max_concurrent参数必须在1-10之间", code=400)
        
        # 创建审计日志
        create_audit_log(
            user_id=user_id,
            action="start_dem_workflow",
            resource_type="dem_parser",
            details={
                "days_back": days_back,
                "limit": limit,
                "max_concurrent": max_concurrent
            }
        )
        
        # 初始化DEM解析服务
        parser = DEMParserService()
        
        # 使用异步辅助工具运行异步任务
        from utils.async_helper import run_async
        result = run_async(parser.start_dem_parsing_workflow, days_back, limit, max_concurrent)
        
        if result['success']:
            return ApiResponse.success(
                data=result,
                message="DEM解析工作流程启动成功"
            )
        else:
            return ApiResponse.error(
                message="DEM解析工作流程执行失败",
                data=result,
                code=500
            )
            
    except Exception as e:
        logger.error(f"启动DEM解析工作流程失败: {e}")
        return ApiResponse.error(f"启动工作流程失败: {str(e)}", code=500)

@dem_parser_bp.route('/process-match/<int:match_id>', methods=['POST'])
@jwt_required()
@admin_required
def process_single_match(match_id: int):
    """
    处理单场比赛的DEM解析
    
    POST /api/dem/process-match/123456
    """
    try:
        user_id = get_jwt_identity()
        
        # 验证match_id
        if match_id <= 0:
            return ApiResponse.error("无效的比赛ID", code=400)
        
        # 创建审计日志
        create_audit_log(
            user_id=user_id,
            action="process_single_match",
            resource_type="dem_parser",
            resource_id=match_id
        )
        
        # 初始化DEM解析服务
        parser = DEMParserService()
        
        # 使用异步辅助工具运行异步任务
        from utils.async_helper import run_async
        result = run_async(parser.process_single_match, match_id)
        
        if result['success']:
            return ApiResponse.success(
                data=result,
                message=f"比赛{match_id}的DEM解析完成"
            )
        else:
            return ApiResponse.error(
                message=f"比赛{match_id}的DEM解析失败",
                data=result,
                code=500
            )
            
    except Exception as e:
        logger.error(f"处理单场比赛DEM解析失败: {e}")
        return ApiResponse.error(f"处理失败: {str(e)}", code=500)

@dem_parser_bp.route('/batch-process', methods=['POST'])
@jwt_required()
@admin_required
def batch_process_matches():
    """
    批量处理多场比赛的DEM解析
    
    POST /api/dem/batch-process
    {
        "match_ids": [123456, 123457, 123458],
        "max_concurrent": 3
    }
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'match_ids' not in data:
            return ApiResponse.error("缺少match_ids参数", code=400)
        
        match_ids = data['match_ids']
        max_concurrent = data.get('max_concurrent', 3)
        
        # 参数验证
        if not isinstance(match_ids, list) or not match_ids:
            return ApiResponse.error("match_ids必须是非空数组", code=400)
        
        if len(match_ids) > 100:
            return ApiResponse.error("单次批量处理最多支持100场比赛", code=400)
        
        if not 1 <= max_concurrent <= 10:
            return ApiResponse.error("max_concurrent参数必须在1-10之间", code=400)
        
        # 验证所有match_id都是正整数
        for match_id in match_ids:
            if not isinstance(match_id, int) or match_id <= 0:
                return ApiResponse.error(f"无效的比赛ID: {match_id}", code=400)
        
        # 创建审计日志
        create_audit_log(
            user_id=user_id,
            action="batch_process_matches",
            resource_type="dem_parser",
            details={
                "match_ids": match_ids,
                "match_count": len(match_ids),
                "max_concurrent": max_concurrent
            }
        )
        
        # 初始化DEM解析服务
        parser = DEMParserService()
        
        # 使用异步辅助工具运行异步任务
        from utils.async_helper import run_async
        result = run_async(parser.batch_process_matches, match_ids, max_concurrent)
        
        return ApiResponse.success(
            data=result,
            message=f"批量处理完成，成功{result['successful']}场，失败{result['failed']}场"
        )
        
    except Exception as e:
        logger.error(f"批量处理DEM解析失败: {e}")
        return ApiResponse.error(f"批量处理失败: {str(e)}", code=500)

@dem_parser_bp.route('/get-pro-matches', methods=['GET'])
@jwt_required()
def get_professional_matches():
    """
    获取职业比赛ID列表
    
    GET /api/dem/get-pro-matches?days_back=7&limit=100
    """
    try:
        user_id = get_jwt_identity()
        
        # 获取查询参数
        days_back = request.args.get('days_back', 7, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        # 参数验证
        if not 1 <= days_back <= 30:
            return ApiResponse.error("days_back参数必须在1-30之间", code=400)
        
        if not 1 <= limit <= 500:
            return ApiResponse.error("limit参数必须在1-500之间", code=400)
        
        # 创建审计日志
        create_audit_log(
            user_id=user_id,
            action="get_professional_matches",
            resource_type="dem_parser",
            details={
                "days_back": days_back,
                "limit": limit
            }
        )
        
        # 初始化DEM解析服务
        parser = DEMParserService()
        
        # 使用异步辅助工具运行异步任务
        from utils.async_helper import run_async
        match_ids = run_async(parser.get_professional_match_ids, days_back, limit)
        
        return ApiResponse.success(
            data={
                "match_ids": match_ids,
                "count": len(match_ids),
                "days_back": days_back,
                "limit": limit
            },
            message=f"获取到{len(match_ids)}场职业比赛"
        )
        
    except Exception as e:
        logger.error(f"获取职业比赛ID失败: {e}")
        return ApiResponse.error(f"获取失败: {str(e)}", code=500)

@dem_parser_bp.route('/status', methods=['GET'])
@jwt_required()
def get_parser_status():
    """
    获取DEM解析服务状态
    
    GET /api/dem/status
    """
    try:
        user_id = get_jwt_identity()
        
        # 创建审计日志
        create_audit_log(
            user_id=user_id,
            action="get_parser_status",
            resource_type="dem_parser"
        )
        
        # 初始化DEM解析服务并检查状态
        parser = DEMParserService()
        
        status = {
            "service_available": True,
            "java_tool_available": parser.clarity_jar_path.exists(),
            "java_tool_path": str(parser.clarity_jar_path),
            "oss_configured": parser.oss_bucket is not None,
            "work_directory": str(parser.work_dir),
            "work_directory_writable": parser.work_dir.exists() and os.access(parser.work_dir, os.W_OK),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # 检查Java环境
        try:
            import subprocess
            java_version = subprocess.run(
                ["java", "-version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            status["java_available"] = java_version.returncode == 0
            if java_version.returncode == 0:
                # 从stderr获取版本信息（Java版本信息通常在stderr中）
                version_info = java_version.stderr.split('\n')[0] if java_version.stderr else "Unknown"
                status["java_version"] = version_info
        except Exception as e:
            status["java_available"] = False
            status["java_error"] = str(e)
        
        return ApiResponse.success(
            data=status,
            message="DEM解析服务状态获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取DEM解析服务状态失败: {e}")
        return ApiResponse.error(f"获取状态失败: {str(e)}", code=500)

@dem_parser_bp.route('/config', methods=['GET'])
@jwt_required()
@admin_required
def get_parser_config():
    """
    获取DEM解析服务配置（仅管理员）
    
    GET /api/dem/config
    """
    try:
        user_id = get_jwt_identity()
        
        # 创建审计日志
        create_audit_log(
            user_id=user_id,
            action="get_parser_config",
            resource_type="dem_parser"
        )
        
        config = {
            "opendota_api_configured": bool(current_app.config.get('OPENDOTA_API_KEY')),
            "oss_configured": {
                "access_key_id": bool(current_app.config.get('ALIYUN_ACCESS_KEY_ID')),
                "access_key_secret": bool(current_app.config.get('ALIYUN_ACCESS_KEY_SECRET')),
                "endpoint": current_app.config.get('ALIYUN_OSS_ENDPOINT'),
                "bucket": current_app.config.get('ALIYUN_OSS_BUCKET')
            },
            "java_tool_path": str(Path(__file__).parent.parent.parent / "dem2json" / "java" / "clarity_dem2json.jar"),
            "work_directory": current_app.config.get('UPLOAD_FOLDER', '/tmp') + "/dem_parser",
            "data_sync_config": {
                "batch_size": current_app.config.get('DATA_SYNC_BATCH_SIZE', 100),
                "rate_limit": current_app.config.get('DATA_SYNC_RATE_LIMIT', 10),
                "max_retries": current_app.config.get('DATA_SYNC_MAX_RETRIES', 3),
                "timeout": current_app.config.get('DATA_SYNC_TIMEOUT', 30)
            }
        }
        
        return ApiResponse.success(
            data=config,
            message="DEM解析服务配置获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取DEM解析服务配置失败: {e}")
        return ApiResponse.error(f"获取配置失败: {str(e)}", code=500)

# 错误处理
@dem_parser_bp.errorhandler(404)
def not_found(error):
    return ApiResponse.error("API端点不存在", code=404)

@dem_parser_bp.errorhandler(405)
def method_not_allowed(error):
    return ApiResponse.error("HTTP方法不允许", code=405)

@dem_parser_bp.errorhandler(500)
def internal_error(error):
    logger.error(f"内部服务器错误: {error}")
    return ApiResponse.error("内部服务器错误", code=500)
