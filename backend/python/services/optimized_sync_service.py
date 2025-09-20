"""
数据同步优化服务
包含智能同步策略、错误处理、性能优化等功能
"""
import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import redis
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from config.database import DatabaseManager
from models.sync import SyncTask, SyncStatus, SyncType
from utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class SyncConfig:
    """同步配置"""
    batch_size: int = 100
    max_workers: int = 4
    retry_attempts: int = 3
    retry_delay: int = 5
    rate_limit_delay: float = 0.1
    cache_ttl: int = 3600
    enable_compression: bool = True
    enable_batch_processing: bool = True

class OptimizedSyncService:
    """优化的数据同步服务"""
    
    def __init__(self, config: SyncConfig = None):
        self.config = config or SyncConfig()
        self.db_manager = DatabaseManager()
        self.redis_client = redis.Redis(
            host='localhost', port=6379, db=0, decode_responses=True
        )
        self.engine = create_engine(self.db_manager.get_database_url())
        self.Session = sessionmaker(bind=self.engine)
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
        
    async def sync_with_optimization(self, sync_type: SyncType, **kwargs) -> Dict[str, Any]:
        """执行优化的数据同步"""
        start_time = time.time()
        task_id = f"{sync_type.value}_{int(start_time)}"
        
        try:
            # 创建同步任务记录
            task = self._create_sync_task(task_id, sync_type)
            
            # 检查缓存
            cache_key = f"sync:{sync_type.value}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data and not kwargs.get('force_refresh'):
                logger.info(f"使用缓存数据: {sync_type.value}")
                return cached_data
            
            # 执行同步
            result = await self._execute_sync(task, sync_type, **kwargs)
            
            # 更新缓存
            if result['success']:
                self._set_cache(cache_key, result, self.config.cache_ttl)
            
            # 更新任务状态
            self._update_task_status(task, SyncStatus.COMPLETED, result)
            
            execution_time = time.time() - start_time
            logger.info(f"同步完成: {sync_type.value}, 耗时: {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"同步失败: {sync_type.value}, 错误: {str(e)}")
            self._update_task_status(task, SyncStatus.FAILED, {'error': str(e)})
            raise
    
    async def _execute_sync(self, task: SyncTask, sync_type: SyncType, **kwargs) -> Dict[str, Any]:
        """执行具体的同步逻辑"""
        
        if sync_type == SyncType.MATCHES:
            return await self._sync_matches(**kwargs)
        elif sync_type == SyncType.HERO_STATS:
            return await self._sync_hero_stats(**kwargs)
        elif sync_type == SyncType.TEAM_INFO:
            return await self._sync_team_info(**kwargs)
        elif sync_type == SyncType.PREDICTIONS:
            return await self._sync_predictions(**kwargs)
        else:
            raise ValueError(f"不支持的同步类型: {sync_type}")
    
    async def _sync_matches(self, **kwargs) -> Dict[str, Any]:
        """同步比赛数据"""
        from services.opendota_service import OpenDotaService
        from services.stratz_service import StratzService
        
        opendota_service = OpenDotaService()
        stratz_service = StratzService()
        
        # 获取时间范围
        start_time = kwargs.get('start_time', datetime.utcnow() - timedelta(days=7))
        end_time = kwargs.get('end_time', datetime.utcnow())
        
        # 并行获取数据
        tasks = [
            self._fetch_with_retry(opendota_service.get_matches, start_time, end_time),
            self._fetch_with_retry(stratz_service.get_matches, start_time, end_time)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 合并和去重
        all_matches = []
        seen_match_ids = set()
        
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"数据源获取失败: {result}")
                continue
                
            for match in result:
                if match['match_id'] not in seen_match_ids:
                    all_matches.append(match)
                    seen_match_ids.add(match['match_id'])
        
        # 批量插入数据库
        inserted_count = await self._batch_insert_matches(all_matches)
        
        return {
            'success': True,
            'data': {
                'total_matches': len(all_matches),
                'inserted_matches': inserted_count,
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                }
            }
        }
    
    async def _sync_hero_stats(self, **kwargs) -> Dict[str, Any]:
        """同步英雄统计数据"""
        # 实现英雄统计同步逻辑
        pass
    
    async def _sync_team_info(self, **kwargs) -> Dict[str, Any]:
        """同步战队信息"""
        # 实现战队信息同步逻辑
        pass
    
    async def _sync_predictions(self, **kwargs) -> Dict[str, Any]:
        """同步预测数据"""
        # 实现预测数据同步逻辑
        pass
    
    async def _fetch_with_retry(self, fetch_func, *args, **kwargs):
        """带重试机制的数据获取"""
        for attempt in range(self.config.retry_attempts):
            try:
                # 速率限制
                await asyncio.sleep(self.config.rate_limit_delay)
                
                # 执行获取
                if asyncio.iscoroutinefunction(fetch_func):
                    result = await fetch_func(*args, **kwargs)
                else:
                    result = fetch_func(*args, **kwargs)
                
                return result
                
            except Exception as e:
                logger.warning(f"获取失败 (尝试 {attempt + 1}): {e}")
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
                else:
                    raise
    
    async def _batch_insert_matches(self, matches: List[Dict]) -> int:
        """批量插入比赛数据"""
        if not matches:
            return 0
        
        session = self.Session()
        try:
            inserted_count = 0
            
            # 分批处理
            for i in range(0, len(matches), self.config.batch_size):
                batch = matches[i:i + self.config.batch_size]
                
                # 构建批量插入SQL
                values = []
                for match in batch:
                    values.append({
                        'match_id': match['match_id'],
                        'start_time': datetime.fromtimestamp(match['start_time']),
                        'duration': match.get('duration', 0),
                        'radiant_team_id': match.get('radiant_team_id'),
                        'dire_team_id': match.get('dire_team_id'),
                        'radiant_win': match.get('radiant_win'),
                        'game_mode': match.get('game_mode'),
                        'lobby_type': match.get('lobby_type'),
                        'data': json.dumps(match) if self.config.enable_compression else match
                    })
                
                # 执行批量插入
                if values:
                    session.execute(
                        text("""
                            INSERT INTO matches (match_id, start_time, duration, 
                                              radiant_team_id, dire_team_id, radiant_win,
                                              game_mode, lobby_type, raw_data)
                            VALUES (:match_id, :start_time, :duration,
                                   :radiant_team_id, :dire_team_id, :radiant_win,
                                   :game_mode, :lobby_type, :data)
                            ON CONFLICT (match_id) DO UPDATE SET
                                raw_data = EXCLUDED.raw_data,
                                updated_at = NOW()
                        """),
                        values
                    )
                    inserted_count += len(values)
            
            session.commit()
            return inserted_count
            
        except Exception as e:
            session.rollback()
            logger.error(f"批量插入失败: {e}")
            raise
        finally:
            session.close()
    
    def _create_sync_task(self, task_id: str, sync_type: SyncType) -> SyncTask:
        """创建同步任务"""
        session = self.Session()
        try:
            task = SyncTask(
                task_id=task_id,
                sync_type=sync_type,
                status=SyncStatus.RUNNING,
                started_at=datetime.utcnow()
            )
            session.add(task)
            session.commit()
            return task
        finally:
            session.close()
    
    def _update_task_status(self, task: SyncTask, status: SyncStatus, result: Dict):
        """更新任务状态"""
        session = self.Session()
        try:
            task.status = status
            task.completed_at = datetime.utcnow()
            task.result_data = result
            session.merge(task)
            session.commit()
        finally:
            session.close()
    
    def _get_from_cache(self, key: str) -> Optional[Dict]:
        """从缓存获取数据"""
        try:
            data = self.redis_client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.warning(f"缓存获取失败: {e}")
            return None
    
    def _set_cache(self, key: str, data: Dict, ttl: int = 3600):
        """设置缓存数据"""
        try:
            self.redis_client.setex(key, ttl, json.dumps(data))
        except Exception as e:
            logger.warning(f"缓存设置失败: {e}")
    
    async def cleanup_old_data(self, days_to_keep: int = 90):
        """清理旧数据"""
        session = self.Session()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # 清理旧的比赛数据
            result = session.execute(
                text("DELETE FROM matches WHERE start_time < :cutoff_date"),
                {'cutoff_date': cutoff_date}
            )
            
            # 清理旧的同步任务
            session.execute(
                text("DELETE FROM sync_tasks WHERE created_at < :cutoff_date"),
                {'cutoff_date': cutoff_date}
            )
            
            session.commit()
            logger.info(f"清理完成，删除 {result.rowcount} 条旧数据")
            
        finally:
            session.close()
    
    def get_sync_statistics(self, days: int = 7) -> Dict[str, Any]:
        """获取同步统计信息"""
        session = self.Session()
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # 获取任务统计
            result = session.execute(
                text("""
                    SELECT 
                        sync_type,
                        COUNT(*) as total_tasks,
                        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful_tasks,
                        AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_duration
                    FROM sync_tasks
                    WHERE created_at >= :start_date
                    GROUP BY sync_type
                """),
                {'start_date': start_date}
            )
            
            statistics = {}
            for row in result:
                statistics[row.sync_type] = {
                    'total_tasks': row.total_tasks,
                    'successful_tasks': row.successful_tasks,
                    'success_rate': row.successful_tasks / row.total_tasks if row.total_tasks > 0 else 0,
                    'avg_duration_seconds': float(row.avg_duration) if row.avg_duration else 0
                }
            
            return statistics
            
        finally:
            session.close()