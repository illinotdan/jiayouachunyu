"""
实时数据同步API路由
提供手动触发数据同步的接口
"""

from flask import Blueprint, request, jsonify
from ..services.opendota_service import OpenDotaService
from ..services.stratz_service import STRATZService
from ..services.liquipedia_service import LiquipediaService
from ..services.data_integration_service import DataIntegrationService
from ..tasks.data_sync import sync_heroes_data, sync_items_data
from ..utils.response import success_response, error_response
from ..utils.decorators import require_auth, rate_limit
from ..utils.monitoring import log_api_call
import logging
from datetime import datetime, timedelta
import asyncio
import threading

# 创建蓝图
realtime_sync_bp = Blueprint('realtime_sync', __name__)

# 配置日志
logger = logging.getLogger(__name__)

# 全局同步状态
sync_status = {
    'is_running': False,
    'progress': 0,
    'current_task': '',
    'start_time': None,
    'end_time': None,
    'error': None,
    'last_sync_time': None
}

@realtime_sync_bp.route('/status', methods=['GET'])
@log_api_call
def get_sync_status():
    """获取当前同步状态"""
    try:
        return success_response({
            'is_running': sync_status['is_running'],
            'progress': sync_status['progress'],
            'current_task': sync_status['current_task'],
            'start_time': sync_status['start_time'],
            'end_time': sync_status['end_time'],
            'error': sync_status['error'],
            'last_sync_time': sync_status['last_sync_time']
        })
    except Exception as e:
        logger.error(f"获取同步状态失败: {str(e)}")
        return error_response("获取同步状态失败", 500)

@realtime_sync_bp.route('/trigger', methods=['POST'])
@require_auth
@rate_limit(requests=5, window=300)  # 5分钟内最多5次
@log_api_call
def trigger_realtime_sync():
    """触发实时数据同步"""
    try:
        if sync_status['is_running']:
            return error_response("数据同步正在进行中，请稍后再试", 409)
        
        # 获取请求参数
        data = request.get_json() or {}
        sync_type = data.get('type', 'full')  # full, matches, heroes, items
        hours_back = data.get('hours_back', 24)  # 获取最近几小时的数据
        
        # 启动后台同步任务
        thread = threading.Thread(
            target=run_realtime_sync,
            args=(sync_type, hours_back),
            daemon=True
        )
        thread.start()
        
        return success_response({
            'message': '实时数据同步已启动',
            'sync_type': sync_type,
            'hours_back': hours_back
        })
        
    except Exception as e:
        logger.error(f"触发实时同步失败: {str(e)}")
        return error_response("触发实时同步失败", 500)

@realtime_sync_bp.route('/latest-matches', methods=['POST'])
@require_auth
@rate_limit(requests=10, window=300)
@log_api_call
def sync_latest_matches_api():
    """同步最新比赛数据"""
    try:
        if sync_status['is_running']:
            return error_response("数据同步正在进行中，请稍后再试", 409)
        
        data = request.get_json() or {}
        hours_back = data.get('hours_back', 6)  # 默认获取最近6小时
        
        # 启动比赛数据同步
        thread = threading.Thread(
            target=run_matches_sync,
            args=(hours_back,),
            daemon=True
        )
        thread.start()
        
        return success_response({
            'message': '最新比赛数据同步已启动',
            'hours_back': hours_back
        })
        
    except Exception as e:
        logger.error(f"同步最新比赛数据失败: {str(e)}")
        return error_response("同步最新比赛数据失败", 500)

@realtime_sync_bp.route('/heroes', methods=['POST'])
@require_auth
@rate_limit(requests=3, window=300)
@log_api_call
def sync_heroes_api():
    """同步英雄数据"""
    try:
        if sync_status['is_running']:
            return error_response("数据同步正在进行中，请稍后再试", 409)
        
        # 启动英雄数据同步
        thread = threading.Thread(
            target=run_heroes_sync,
            daemon=True
        )
        thread.start()
        
        return success_response({
            'message': '英雄数据同步已启动'
        })
        
    except Exception as e:
        logger.error(f"同步英雄数据失败: {str(e)}")
        return error_response("同步英雄数据失败", 500)

@realtime_sync_bp.route('/items', methods=['POST'])
@require_auth
@rate_limit(requests=3, window=300)
@log_api_call
def sync_items_api():
    """同步物品数据"""
    try:
        if sync_status['is_running']:
            return error_response("数据同步正在进行中，请稍后再试", 409)
        
        # 启动物品数据同步
        thread = threading.Thread(
            target=run_items_sync,
            daemon=True
        )
        thread.start()
        
        return success_response({
            'message': '物品数据同步已启动'
        })
        
    except Exception as e:
        logger.error(f"同步物品数据失败: {str(e)}")
        return error_response("同步物品数据失败", 500)

def update_sync_status(**kwargs):
    """更新同步状态"""
    global sync_status
    sync_status.update(kwargs)

def run_realtime_sync(sync_type, hours_back):
    """运行实时数据同步"""
    try:
        update_sync_status(
            is_running=True,
            progress=0,
            current_task='初始化同步任务',
            start_time=datetime.now().isoformat(),
            end_time=None,
            error=None
        )
        
        # 初始化服务
        opendota_service = OpenDotaService()
        stratz_service = STRATZService()
        liquipedia_service = LiquipediaService()
        data_integration_service = DataIntegrationService()
        
        total_tasks = 0
        completed_tasks = 0
        
        if sync_type in ['full', 'matches']:
            total_tasks += 1
        if sync_type in ['full', 'heroes']:
            total_tasks += 1
        if sync_type in ['full', 'items']:
            total_tasks += 1
        if sync_type == 'full':
            total_tasks += 1  # 团队数据
        
        # 同步比赛数据
        if sync_type in ['full', 'matches']:
            update_sync_status(current_task=f'同步最近{hours_back}小时的比赛数据')
            sync_latest_matches_data(hours_back)
            completed_tasks += 1
            update_sync_status(progress=int((completed_tasks / total_tasks) * 100))
        
        # 同步英雄数据
        if sync_type in ['full', 'heroes']:
            update_sync_status(current_task='同步英雄数据')
            sync_heroes_data()
            completed_tasks += 1
            update_sync_status(progress=int((completed_tasks / total_tasks) * 100))
        
        # 同步物品数据
        if sync_type in ['full', 'items']:
            update_sync_status(current_task='同步物品数据')
            sync_items_data()
            completed_tasks += 1
            update_sync_status(progress=int((completed_tasks / total_tasks) * 100))
        
        # 同步团队数据
        if sync_type == 'full':
            update_sync_status(current_task='同步团队和联赛数据')
            sync_teams_data()
            completed_tasks += 1
            update_sync_status(progress=int((completed_tasks / total_tasks) * 100))
        
        # 完成同步
        update_sync_status(
            is_running=False,
            progress=100,
            current_task='同步完成',
            end_time=datetime.now().isoformat(),
            last_sync_time=datetime.now().isoformat()
        )
        
        logger.info(f"实时数据同步完成: {sync_type}, 耗时: {hours_back}小时")
        
    except Exception as e:
        logger.error(f"实时数据同步失败: {str(e)}")
        update_sync_status(
            is_running=False,
            error=str(e),
            end_time=datetime.now().isoformat()
        )

def run_matches_sync(hours_back):
    """运行比赛数据同步"""
    try:
        update_sync_status(
            is_running=True,
            progress=0,
            current_task=f'同步最近{hours_back}小时的比赛数据',
            start_time=datetime.now().isoformat(),
            error=None
        )
        
        sync_latest_matches_data(hours_back)
        
        update_sync_status(
            is_running=False,
            progress=100,
            current_task='比赛数据同步完成',
            end_time=datetime.now().isoformat(),
            last_sync_time=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"比赛数据同步失败: {str(e)}")
        update_sync_status(
            is_running=False,
            error=str(e),
            end_time=datetime.now().isoformat()
        )

def run_heroes_sync():
    """运行英雄数据同步"""
    try:
        update_sync_status(
            is_running=True,
            progress=0,
            current_task='同步英雄数据',
            start_time=datetime.now().isoformat(),
            error=None
        )
        
        sync_heroes_data()
        
        update_sync_status(
            is_running=False,
            progress=100,
            current_task='英雄数据同步完成',
            end_time=datetime.now().isoformat(),
            last_sync_time=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"英雄数据同步失败: {str(e)}")
        update_sync_status(
            is_running=False,
            error=str(e),
            end_time=datetime.now().isoformat()
        )

def run_items_sync():
    """运行物品数据同步"""
    try:
        update_sync_status(
            is_running=True,
            progress=0,
            current_task='同步物品数据',
            start_time=datetime.now().isoformat(),
            error=None
        )
        
        sync_items_data()
        
        update_sync_status(
            is_running=False,
            progress=100,
            current_task='物品数据同步完成',
            end_time=datetime.now().isoformat(),
            last_sync_time=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"物品数据同步失败: {str(e)}")
        update_sync_status(
            is_running=False,
            error=str(e),
            end_time=datetime.now().isoformat()
        )

def sync_latest_matches_data(hours_back):
    """同步最新比赛数据"""
    try:
        opendota_service = OpenDotaService()
        data_integration_service = DataIntegrationService()
        
        # 计算时间范围
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        
        logger.info(f"开始同步比赛数据: {start_time} 到 {end_time}")
        
        # 获取比赛列表
        matches = opendota_service.get_matches_by_date_range(
            start_time=start_time,
            end_time=end_time,
            limit=1000  # 限制数量避免超时
        )
        
        if not matches:
            logger.warning("未找到新的比赛数据")
            return
        
        logger.info(f"找到 {len(matches)} 场新比赛")
        
        # 处理每场比赛
        for i, match in enumerate(matches):
            try:
                # 使用数据集成服务处理比赛
                data_integration_service.process_match(match['match_id'])
                
                # 更新进度
                progress = int((i + 1) / len(matches) * 100)
                update_sync_status(progress=progress)
                
            except Exception as e:
                logger.error(f"处理比赛 {match['match_id']} 失败: {str(e)}")
                continue
        
        logger.info(f"比赛数据同步完成，处理了 {len(matches)} 场比赛")
        
    except Exception as e:
        logger.error(f"同步最新比赛数据失败: {str(e)}")
        raise

def sync_teams_data():
    """同步团队数据"""
    try:
        liquipedia_service = LiquipediaService()
        
        # 获取热门团队信息
        teams = liquipedia_service.get_popular_teams()
        
        if teams:
            logger.info(f"同步了 {len(teams)} 个团队的数据")
        else:
            logger.warning("未获取到团队数据")
            
    except Exception as e:
        logger.error(f"同步团队数据失败: {str(e)}")
        raise
