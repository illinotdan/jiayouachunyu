"""
DEM解析任务调度模块
使用Celery进行异步任务处理
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from celery import Celery, Task
from flask import current_app

from services.dem_parser_service import DEMParserService
from models.match import Match, MatchAnalysis
from models.audit import AuditLog
from config.database import db
from utils.response import ApiResponse

logger = logging.getLogger(__name__)

# 创建Celery实例
celery_app = Celery('dem_parser_tasks')

class CallbackTask(Task):
    """带回调的任务基类"""
    def on_success(self, retval, task_id, args, kwargs):
        """任务成功完成时的回调"""
        logger.info(f"任务{task_id}成功完成: {retval}")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任务失败时的回调"""
        logger.error(f"任务{task_id}执行失败: {exc}")
        logger.error(f"错误详情: {einfo}")

@celery_app.task(base=CallbackTask, bind=True, max_retries=3)
def parse_single_match_task(self, match_id: int, user_id: int = None):
    """
    解析单场比赛的异步任务
    
    Args:
        match_id: 比赛ID
        user_id: 发起用户ID
    """
    try:
        logger.info(f"开始异步解析比赛{match_id}")
        
        # 创建审计日志
        if user_id:
            audit = AuditLog(
                user_id=user_id,
                action="async_parse_single_match",
                resource_type="dem_parser",
                resource_id=match_id,
                details={"task_id": self.request.id},
                timestamp=datetime.utcnow()
            )
            db.session.add(audit)
            db.session.commit()
        
        # 初始化DEM解析服务
        parser = DEMParserService()
        
        # 使用异步辅助工具运行异步解析
        from utils.async_helper import run_async
        result = run_async(parser.process_single_match, match_id)
        
        if result['success']:
            logger.info(f"比赛{match_id}异步解析成功")
            return {
                "success": True,
                "match_id": match_id,
                "task_id": self.request.id,
                "result": result
            }
        else:
            logger.warning(f"比赛{match_id}异步解析失败: {result.get('errors', [])}")
            # 如果是可重试的错误，进行重试
            if self.request.retries < self.max_retries:
                logger.info(f"重试解析比赛{match_id}，当前重试次数: {self.request.retries + 1}")
                raise self.retry(countdown=60 * (self.request.retries + 1))  # 递增延迟
            
            return {
                "success": False,
                "match_id": match_id,
                "task_id": self.request.id,
                "errors": result.get('errors', [])
            }
            
    except Exception as exc:
        logger.error(f"解析比赛{match_id}时发生异常: {exc}")
        
        # 如果还有重试次数，进行重试
        if self.request.retries < self.max_retries:
            logger.info(f"重试解析比赛{match_id}，当前重试次数: {self.request.retries + 1}")
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
        
        # 超过重试次数，记录失败
        return {
            "success": False,
            "match_id": match_id,
            "task_id": self.request.id,
            "error": str(exc)
        }

@celery_app.task(base=CallbackTask, bind=True)
def batch_parse_matches_task(self, match_ids: List[int], max_concurrent: int = 3, user_id: int = None):
    """
    批量解析比赛的异步任务
    
    Args:
        match_ids: 比赛ID列表
        max_concurrent: 最大并发数
        user_id: 发起用户ID
    """
    try:
        logger.info(f"开始异步批量解析{len(match_ids)}场比赛")
        
        # 创建审计日志
        if user_id:
            audit = AuditLog(
                user_id=user_id,
                action="async_batch_parse_matches",
                resource_type="dem_parser",
                details={
                    "task_id": self.request.id,
                    "match_ids": match_ids,
                    "match_count": len(match_ids),
                    "max_concurrent": max_concurrent
                },
                timestamp=datetime.utcnow()
            )
            db.session.add(audit)
            db.session.commit()
        
        # 初始化DEM解析服务
        parser = DEMParserService()
        
        # 使用异步辅助工具运行批量解析
        from utils.async_helper import run_async
        result = run_async(parser.batch_process_matches, match_ids, max_concurrent)
        
        logger.info(f"批量解析完成: 成功{result['successful']}场，失败{result['failed']}场")
        
        return {
            "success": True,
            "task_id": self.request.id,
            "batch_result": result
        }
        
    except Exception as exc:
        logger.error(f"批量解析比赛时发生异常: {exc}")
        return {
            "success": False,
            "task_id": self.request.id,
            "error": str(exc)
        }

@celery_app.task(base=CallbackTask, bind=True)
def dem_parsing_workflow_task(self, days_back: int = 7, limit: int = 50, max_concurrent: int = 3, user_id: int = None):
    """
    完整DEM解析工作流程的异步任务
    
    Args:
        days_back: 获取多少天前的比赛
        limit: 最大处理数量
        max_concurrent: 最大并发数
        user_id: 发起用户ID
    """
    try:
        logger.info(f"开始异步DEM解析工作流程")
        
        # 创建审计日志
        if user_id:
            audit = AuditLog(
                user_id=user_id,
                action="async_dem_workflow",
                resource_type="dem_parser",
                details={
                    "task_id": self.request.id,
                    "days_back": days_back,
                    "limit": limit,
                    "max_concurrent": max_concurrent
                },
                timestamp=datetime.utcnow()
            )
            db.session.add(audit)
            db.session.commit()
        
        # 初始化DEM解析服务
        parser = DEMParserService()
        
        # 使用异步辅助工具运行完整工作流
        from utils.async_helper import run_async
        result = run_async(parser.start_dem_parsing_workflow, days_back, max_matches)
        
        if result['success']:
            logger.info("DEM解析工作流程异步执行成功")
        else:
            logger.warning(f"DEM解析工作流程异步执行失败: {result.get('error', 'Unknown error')}")
        
        return {
            "success": result['success'],
            "task_id": self.request.id,
            "workflow_result": result
        }
        
    except Exception as exc:
        logger.error(f"DEM解析工作流程异步执行时发生异常: {exc}")
        return {
            "success": False,
            "task_id": self.request.id,
            "error": str(exc)
        }

@celery_app.task(base=CallbackTask)
def scheduled_dem_parsing_task():
    """
    定时DEM解析任务
    每天自动执行一次，解析最近的职业比赛
    """
    try:
        logger.info("开始定时DEM解析任务")
        
        # 创建审计日志
        audit = AuditLog(
            user_id=None,  # 系统任务
            action="scheduled_dem_parsing",
            resource_type="dem_parser",
            details={"scheduled": True},
            timestamp=datetime.utcnow()
        )
        db.session.add(audit)
        db.session.commit()
        
        # 初始化DEM解析服务
        parser = DEMParserService()
        
        # 使用异步辅助工具运行清理任务
        from utils.async_helper import run_async
        result = run_async(parser.cleanup_old_dem_files, days_old)
        
        logger.info(f"定时DEM解析任务完成: 成功{result.get('batch_result', {}).get('successful', 0)}场")
        
        return {
            "success": result['success'],
            "scheduled": True,
            "workflow_result": result
        }
        
    except Exception as exc:
        logger.error(f"定时DEM解析任务执行失败: {exc}")
        return {
            "success": False,
            "scheduled": True,
            "error": str(exc)
        }

@celery_app.task(base=CallbackTask)
def cleanup_old_dem_files_task(days_old: int = 7):
    """
    清理旧的DEM文件任务
    
    Args:
        days_old: 清理多少天前的文件
    """
    try:
        logger.info(f"开始清理{days_old}天前的DEM文件")
        
        # 初始化DEM解析服务
        parser = DEMParserService()
        
        if not parser.work_dir.exists():
            logger.info("工作目录不存在，无需清理")
            return {"success": True, "cleaned_files": 0}
        
        # 计算清理时间
        cutoff_time = datetime.now() - timedelta(days=days_old)
        cutoff_timestamp = cutoff_time.timestamp()
        
        cleaned_files = 0
        
        # 清理DEM文件
        for file_path in parser.work_dir.glob("*.dem"):
            try:
                file_stat = file_path.stat()
                if file_stat.st_mtime < cutoff_timestamp:
                    file_path.unlink()
                    cleaned_files += 1
                    logger.info(f"清理旧DEM文件: {file_path}")
            except Exception as e:
                logger.warning(f"清理文件{file_path}失败: {e}")
        
        # 清理临时JSON文件
        for file_path in parser.work_dir.glob("*.json"):
            try:
                file_stat = file_path.stat()
                if file_stat.st_mtime < cutoff_timestamp:
                    file_path.unlink()
                    cleaned_files += 1
                    logger.info(f"清理旧JSON文件: {file_path}")
            except Exception as e:
                logger.warning(f"清理文件{file_path}失败: {e}")
        
        logger.info(f"清理完成，共清理{cleaned_files}个文件")
        
        return {
            "success": True,
            "cleaned_files": cleaned_files,
            "days_old": days_old
        }
        
    except Exception as exc:
        logger.error(f"清理旧DEM文件任务失败: {exc}")
        return {
            "success": False,
            "error": str(exc)
        }

# 任务状态查询函数
def get_task_status(task_id: str) -> Dict:
    """
    获取任务状态
    
    Args:
        task_id: 任务ID
        
    Returns:
        Dict: 任务状态信息
    """
    try:
        task = celery_app.AsyncResult(task_id)
        
        return {
            "task_id": task_id,
            "status": task.status,
            "result": task.result if task.ready() else None,
            "info": task.info,
            "successful": task.successful(),
            "failed": task.failed(),
            "ready": task.ready(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取任务{task_id}状态失败: {e}")
        return {
            "task_id": task_id,
            "status": "UNKNOWN",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

def cancel_task(task_id: str) -> Dict:
    """
    取消任务
    
    Args:
        task_id: 任务ID
        
    Returns:
        Dict: 取消结果
    """
    try:
        celery_app.control.revoke(task_id, terminate=True)
        
        return {
            "success": True,
            "task_id": task_id,
            "message": "任务已取消",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"取消任务{task_id}失败: {e}")
        return {
            "success": False,
            "task_id": task_id,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

def get_active_tasks() -> List[Dict]:
    """
    获取活跃任务列表
    
    Returns:
        List[Dict]: 活跃任务列表
    """
    try:
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()
        
        if not active_tasks:
            return []
        
        all_tasks = []
        for worker, tasks in active_tasks.items():
            for task in tasks:
                all_tasks.append({
                    "task_id": task.get("id"),
                    "name": task.get("name"),
                    "args": task.get("args", []),
                    "kwargs": task.get("kwargs", {}),
                    "worker": worker,
                    "time_start": task.get("time_start"),
                    "acknowledged": task.get("acknowledged", False)
                })
        
        return all_tasks
        
    except Exception as e:
        logger.error(f"获取活跃任务列表失败: {e}")
        return []

# Celery配置
celery_app.conf.update(
    broker_url=current_app.config.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    result_backend=current_app.config.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1小时任务超时
    task_soft_time_limit=3300,  # 55分钟软超时
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    task_default_retry_delay=60,  # 默认重试延迟60秒
    task_max_retries=3,  # 默认最大重试3次
)

# 定时任务配置
celery_app.conf.beat_schedule = {
    'scheduled-dem-parsing': {
        'task': 'tasks.dem_parsing_tasks.scheduled_dem_parsing_task',
        'schedule': 3600.0,  # 每小时执行一次
    },
    'cleanup-old-dem-files': {
        'task': 'tasks.dem_parsing_tasks.cleanup_old_dem_files_task',
        'schedule': 24 * 3600.0,  # 每天执行一次
        'kwargs': {'days_old': 7}
    },
}

if __name__ == "__main__":
    # 启动Celery worker
    celery_app.start()
