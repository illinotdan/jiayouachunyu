"""
统一数据整合服务
协调 OpenDota API、STRATZ API、Liquipedia 爬虫、DEM解析四个数据源
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass
from enum import Enum
import json
import aiohttp
from urllib.parse import urljoin
import time
from flask import current_app
from sqlalchemy import exc

from config.database import db
from services.opendota_service import OpenDotaService
from services.stratz_service import StratzService  
from services.liquipedia_service import LiquipediaService
from models.match import Match, Team, Player, League, MatchPlayer, MatchAnalysis, MatchDraft
from models.user import User
from utils.response import ApiResponse

logger = logging.getLogger(__name__)

class DataSource(Enum):
    """数据源枚举"""
    OPENDOTA = "opendota"
    STRATZ = "stratz"
    LIQUIPEDIA = "liquipedia"
    DEM = "dem"

@dataclass
class DataQuality:
    """数据质量评估"""
    completeness: float  # 0-1
    accuracy: float     # 0-1
    freshness: int      # 小时数
    consistency: bool   # 是否一致
    sources: List[str]  # 数据来源

@dataclass  
class SyncResult:
    """同步结果"""
    source: DataSource
    success: bool
    records_processed: int
    records_success: int
    records_failed: int
    errors: List[str]
    execution_time: float

class UnifiedDataService:
    """统一数据整合服务"""
    
    def __init__(self, 
                 opendota_key: str = None,
                 stratz_key: str = None,
                 liquipedia_config: dict = None,
                 rate_limits: Dict[str, float] = None):
        """
        初始化统一数据服务
        
        Args:
            opendota_key: OpenDota API密钥
            stratz_key: STRATZ API密钥
            liquipedia_config: Liquipedia配置（可选）
            rate_limits: 各数据源的速率限制
        """
        # 使用Flask应用配置或传入的参数
        if opendota_key is None:
            opendota_key = current_app.config.get('OPENDOTA_API_KEY')
        if stratz_key is None:
            stratz_key = current_app.config.get('STRATZ_API_KEY')
            
        self.opendota = OpenDotaService(api_key=opendota_key)
        self.stratz = StratzService(api_key=stratz_key)
        self.liquipedia = LiquipediaService()
        
        # 应用级配置
        self.batch_size = current_app.config.get('DATA_SYNC_BATCH_SIZE', 100)
        self.rate_limit = current_app.config.get('DATA_SYNC_RATE_LIMIT', 10)
        self.max_retries = current_app.config.get('DATA_SYNC_MAX_RETRIES', 3)
        self.timeout = current_app.config.get('DATA_SYNC_TIMEOUT', 30)
        
        # 速率限制设置（合并应用配置与传入参数）
        self.rate_limits = rate_limits or {
            'opendota': 1.0 / self.rate_limit if self.rate_limit > 0 else 1.0,
            'stratz': 0.1,
            'liquipedia': 2.0,
            'dem': 0.5
        }
        
        # 数据源优先级（从高到低）
        self.source_priority = {
            'match_details': [DataSource.STRATZ, DataSource.OPENDOTA, DataSource.DEM],
            'team_info': [DataSource.LIQUIPEDIA, DataSource.STRATZ, DataSource.OPENDOTA],
            'player_info': [DataSource.STRATZ, DataSource.OPENDOTA, DataSource.LIQUIPEDIA],
            'hero_stats': [DataSource.STRATZ, DataSource.OPENDOTA],
            'tournament_info': [DataSource.LIQUIPEDIA, DataSource.STRATZ]
        }
        
    async def sync_all_data(self, start_date: datetime = None, end_date: datetime = None, time_range_hours: int = 24) -> Dict[str, SyncResult]:
        """
        同步所有数据源
        
        Args:
            start_date: 开始日期时间
            end_date: 结束日期时间  
            time_range_hours: 同步时间范围（小时，当日期参数为空时使用）
            
        Returns:
            各数据源的同步结果
        """
        # 确定时间范围
        if start_date and end_date:
            time_range_hours = int((end_date - start_date).total_seconds() / 3600)
            current_app.logger.info(f"开始统一数据同步，时间范围：{start_date} 到 {end_date}")
        else:
            current_app.logger.info(f"开始统一数据同步，时间范围：{time_range_hours}小时")
            if not start_date:
                start_date = datetime.utcnow() - timedelta(hours=time_range_hours)
            if not end_date:
                end_date = datetime.utcnow()
        
        sync_results = {}
        
        # 并发同步各数据源
        tasks = [
            self._sync_opendota_data(time_range_hours),
            self._sync_stratz_data(time_range_hours), 
            self._sync_liquipedia_data(),
            # self._sync_dem_data()  # DEM解析较慢，可选择性执行
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                current_app.logger.error(f"数据源同步失败: {result}")
                continue
            sync_results.update(result)
        
        # 数据质量评估和清理
        await self._assess_and_clean_data()
        
        # 生成同步报告
        sync_report = self._generate_sync_report(sync_results)
        current_app.logger.info(f"数据同步完成: {sync_report}")
        
        return sync_results
    
    def _generate_sync_report(self, sync_results: Dict[str, SyncResult]) -> Dict[str, any]:
        """
        生成同步报告
        
        Args:
            sync_results: 各数据源的同步结果
            
        Returns:
            同步报告摘要
        """
        total_records = sum(r.records_success for r in sync_results.values())
        total_errors = sum(len(r.errors) for r in sync_results.values())
        total_execution_time = sum(r.execution_time for r in sync_results.values())
        
        # 统计各数据源状态
        source_status = {}
        for source, result in sync_results.items():
            source_status[source] = {
                'success': result.success,
                'records_processed': result.records_processed,
                'records_success': result.records_success,
                'records_failed': result.records_failed,
                'error_count': len(result.errors),
                'execution_time': result.execution_time
            }
        
        report = {
            'sync_time': datetime.utcnow().isoformat(),
            'total_sources': len(sync_results),
            'total_records': total_records,
            'total_errors': total_errors,
            'total_execution_time': total_execution_time,
            'success_rate': (total_records / max(sum(r.records_processed for r in sync_results.values()), 1)) * 100,
            'source_status': source_status
        }
        
        return report
    
    async def _assess_and_clean_data(self):
        """
        数据质量评估和清理
        """
        try:
            logger.info("开始数据质量评估和清理...")
            
            # 1. 检查重复数据
            await self._remove_duplicate_matches()
            
            # 2. 修复数据不一致
            await self._fix_data_inconsistencies()
            
            # 3. 清理过期数据
            await self._clean_expired_data()
            
            logger.info("数据质量评估和清理完成")
            
        except Exception as e:
            logger.error(f"数据质量评估和清理异常: {e}")
    
    async def _remove_duplicate_matches(self):
        """移除重复的比赛数据"""
        try:
            # 查询重复的比赛ID
            duplicate_query = """
            SELECT match_id, COUNT(*) as count
            FROM matches 
            GROUP BY match_id 
            HAVING COUNT(*) > 1
            """
            
            # 这里应该执行实际的重复数据清理逻辑
            # 暂时只是记录日志
            logger.info("检查重复比赛数据...")
            
        except Exception as e:
            logger.error(f"移除重复比赛数据异常: {e}")
    
    async def _fix_data_inconsistencies(self):
        """修复数据不一致"""
        try:
            # 修复比赛状态不一致
            logger.info("修复数据不一致...")
            
            # 示例：修复没有联赛信息的比赛
            matches_without_league = Match.query.filter(Match.league_id.is_(None)).limit(100).all()
            for match in matches_without_league:
                # 尝试从其他数据源获取联赛信息
                if match.data_sources and 'opendota' in match.data_sources:
                    # 从OpenDota获取联赛信息
                    pass
            
        except Exception as e:
            logger.error(f"修复数据不一致异常: {e}")
    
    async def _clean_expired_data(self):
        """清理过期数据"""
        try:
            # 清理30天前的临时数据
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            logger.info(f"清理{cutoff_date}前的过期数据...")
            
            # 这里可以添加具体的清理逻辑
            # 例如清理临时文件、缓存数据等
            
        except Exception as e:
            logger.error(f"清理过期数据异常: {e}")
    
    async def _sync_opendota_data(self, time_range_hours: int) -> Dict[str, SyncResult]:
        """同步OpenDota数据"""
        results = {}
        start_time = datetime.now()
        
        try:
            logger.info("开始同步OpenDota数据...")
            
            # 获取职业比赛
            pro_matches = self.opendota.get_pro_matches(limit=100)
            
            processed = 0
            success = 0
            errors = []
            
            # 过滤时间范围内的比赛
            cutoff_time = datetime.utcnow() - timedelta(hours=time_range_hours)
            recent_matches = [
                match for match in pro_matches
                if datetime.utcfromtimestamp(match.get('start_time', 0)) >= cutoff_time
            ]
            
            for match_data in recent_matches:
                try:
                    await self._process_match_from_opendota(match_data)
                    success += 1
                except Exception as e:
                    errors.append(f"Match {match_data.get('match_id')}: {str(e)}")
                processed += 1
                
                # 速率限制
                await asyncio.sleep(self.rate_limits['opendota'])
            
            results['opendota'] = SyncResult(
                source=DataSource.OPENDOTA,
                success=True,
                records_processed=processed,
                records_success=success,
                records_failed=processed - success,
                errors=errors,
                execution_time=(datetime.now() - start_time).total_seconds()
            )
            
        except Exception as e:
            logger.error(f"OpenDota数据同步异常: {e}")
            results['opendota'] = SyncResult(
                source=DataSource.OPENDOTA,
                success=False,
                records_processed=0,
                records_success=0,
                records_failed=0,
                errors=[str(e)],
                execution_time=(datetime.now() - start_time).total_seconds()
            )
        
        return results
    
    async def _sync_stratz_data(self, time_range_hours: int) -> Dict[str, SyncResult]:
        """同步STRATZ数据"""
        results = {}
        start_time = datetime.now()
        
        try:
            logger.info("开始同步STRATZ数据...")
            
            # 获取直播比赛
            live_matches = self.stratz.get_live_matches()
            
            processed = 0
            success = 0
            errors = []
            
            for match_data in live_matches:
                try:
                    await self._process_match_from_stratz(match_data)
                    success += 1
                except Exception as e:
                    errors.append(f"Live match {match_data.get('matchId')}: {str(e)}")
                processed += 1
                
                await asyncio.sleep(self.rate_limits['stratz'])
            
            # 同步英雄数据
            heroes = self.stratz.get_heroes('detailed')
            if heroes:
                await self._sync_heroes_from_stratz(heroes)
            
            results['stratz'] = SyncResult(
                source=DataSource.STRATZ,
                success=True,
                records_processed=processed,
                records_success=success,
                records_failed=processed - success,
                errors=errors,
                execution_time=(datetime.now() - start_time).total_seconds()
            )
            
        except Exception as e:
            logger.error(f"STRATZ数据同步异常: {e}")
            results['stratz'] = SyncResult(
                source=DataSource.STRATZ,
                success=False,
                records_processed=0,
                records_success=0,
                records_failed=0,
                errors=[str(e)],
                execution_time=(datetime.now() - start_time).total_seconds()
            )
        
        return results
    
    async def _sync_liquipedia_data(self) -> Dict[str, SyncResult]:
        """同步Liquipedia数据"""
        results = {}
        start_time = datetime.now()
        
        try:
            logger.info("开始同步Liquipedia数据...")
            
            # 重点战队列表
            priority_teams = [
                'Team Spirit', 'PSG.LGD', 'OG', 'Team Secret', 
                'Evil Geniuses', 'Virtus.pro', 'T1', 'Team Liquid',
                'Fnatic', 'Alliance', 'Tundra Esports', 'BOOM Esports'
            ]
            
            processed = 0
            success = 0
            errors = []
            
            for team_name in priority_teams:
                try:
                    team_info = self.liquipedia.get_team_info(team_name)
                    if team_info:
                        await self._process_team_from_liquipedia(team_info)
                        success += 1
                except Exception as e:
                    errors.append(f"Team {team_name}: {str(e)}")
                processed += 1
                
                await asyncio.sleep(self.rate_limits['liquipedia'])
            
            results['liquipedia'] = SyncResult(
                source=DataSource.LIQUIPEDIA,
                success=True,
                records_processed=processed,
                records_success=success,
                records_failed=processed - success,
                errors=errors,
                execution_time=(datetime.now() - start_time).total_seconds()
            )
            
        except Exception as e:
            logger.error(f"Liquipedia数据同步异常: {e}")
            results['liquipedia'] = SyncResult(
                source=DataSource.LIQUIPEDIA,
                success=False,
                records_processed=0,
                records_success=0,
                records_failed=0,
                errors=[str(e)],
                execution_time=(datetime.now() - start_time).total_seconds()
            )
        
        return results
    
    async def _sync_dem_data(self, match_ids: List[str] = None) -> Dict[str, SyncResult]:
        """
        同步DEM数据到阿里云OSS
        
        Args:
            match_ids: 指定要处理的比赛ID列表，为空则处理最近的比赛
        """
        results = {}
        start_time = datetime.now()
        
        try:
            logger.info("开始DEM数据处理流程...")
            
            # 获取需要处理的比赛ID
            if not match_ids:
                match_ids = await self._get_recent_match_ids_for_dem()
            
            processed = 0
            success = 0
            errors = []
            
            for match_id in match_ids:
                try:
                    # 1. 下载DEM文件
                    dem_path = await self._download_dem_file(match_id)
                    if not dem_path:
                        errors.append(f"Match {match_id}: DEM文件下载失败")
                        continue
                    
                    # 2. 解析DEM为JSON
                    json_data = await self._parse_dem_to_json(dem_path, match_id)
                    if not json_data:
                        errors.append(f"Match {match_id}: DEM解析失败")
                        continue
                    
                    # 3. 上传到阿里云OSS
                    oss_url = await self._upload_json_to_oss(json_data, match_id)
                    if oss_url:
                        # 4. 保存OSS链接到数据库
                        await self._save_dem_analysis_link(match_id, oss_url)
                        success += 1
                    else:
                        errors.append(f"Match {match_id}: OSS上传失败")
                        
                except Exception as e:
                    errors.append(f"Match {match_id}: {str(e)}")
                
                processed += 1
                await asyncio.sleep(self.rate_limits['dem'])
            
            results['dem'] = SyncResult(
                source=DataSource.DEM,
                success=True,
                records_processed=processed,
                records_success=success,
                records_failed=processed - success,
                errors=errors,
                execution_time=(datetime.now() - start_time).total_seconds()
            )
            
        except Exception as e:
            logger.error(f"DEM数据处理异常: {e}")
            results['dem'] = SyncResult(
                source=DataSource.DEM,
                success=False,
                records_processed=0,
                records_success=0,
                records_failed=0,
                errors=[str(e)],
                execution_time=(datetime.now() - start_time).total_seconds()
            )
        
        return results
    
    async def _download_dem_file(self, match_id: str) -> Optional[str]:
        """
        下载DEM文件
        
        Args:
            match_id: 比赛ID
            
        Returns:
            本地DEM文件路径，失败返回None
        """
        import os
        import aiohttp
        
        try:
            # 构建DEM文件URL（OpenDota提供）
            dem_url = f"https://api.opendota.com/api/replays?match_id={match_id}"
            
            # 创建本地存储目录
            dem_dir = "data/dem_files"
            os.makedirs(dem_dir, exist_ok=True)
            
            local_path = os.path.join(dem_dir, f"{match_id}.dem")
            
            async with aiohttp.ClientSession() as session:
                # 获取DEM下载链接
                async with session.get(dem_url) as resp:
                    if resp.status != 200:
                        logger.error(f"获取DEM链接失败: {match_id}, status: {resp.status}")
                        return None
                    
                    replay_data = await resp.json()
                    if not replay_data or not replay_data[0].get('url'):
                        logger.error(f"DEM链接为空: {match_id}")
                        return None
                    
                    download_url = replay_data[0]['url']
                
                # 下载DEM文件
                async with session.get(download_url) as resp:
                    if resp.status != 200:
                        logger.error(f"DEM文件下载失败: {match_id}, status: {resp.status}")
                        return None
                    
                    with open(local_path, 'wb') as f:
                        async for chunk in resp.content.iter_chunked(8192):
                            f.write(chunk)
                    
                    logger.info(f"DEM文件下载成功: {local_path}")
                    return local_path
        
        except Exception as e:
            logger.error(f"下载DEM文件异常 {match_id}: {e}")
            return None
    
    async def _parse_dem_to_json(self, dem_path: str, match_id: str) -> Optional[Dict]:
        """
        解析DEM文件为JSON数据
        
        Args:
            dem_path: DEM文件路径
            match_id: 比赛ID
            
        Returns:
            解析后的JSON数据，失败返回None
        """
        import subprocess
        import tempfile
        import os
        
        try:
            # 使用clarity或其他DEM解析工具
            # 这里假设你有一个DEM解析工具（如clarity、dotaconstants等）
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                output_path = temp_file.name
            
            # 调用DEM解析工具（需要你根据实际工具调整）
            cmd = [
                'clarity',  # 或者你使用的其他解析工具
                '--match-id', match_id,
                '--input', dem_path,
                '--output', output_path,
                '--format', 'json'
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"DEM解析失败 {match_id}: {stderr.decode()}")
                return None
            
            # 读取解析结果
            if os.path.exists(output_path):
                with open(output_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                # 清理临时文件
                os.unlink(output_path)
                os.unlink(dem_path)  # 删除原DEM文件节省空间
                
                logger.info(f"DEM解析成功: {match_id}")
                return json_data
            else:
                logger.error(f"DEM解析输出文件不存在: {match_id}")
                return None
                
        except Exception as e:
            logger.error(f"解析DEM文件异常 {match_id}: {e}")
            return None
    
    async def _upload_json_to_oss(self, json_data: Dict, match_id: str) -> Optional[str]:
        """
        上传JSON数据到阿里云OSS
        
        Args:
            json_data: JSON数据
            match_id: 比赛ID
            
        Returns:
            OSS文件URL，失败返回None
        """
        try:
            import oss2
            from config.settings import OSS_CONFIG
            
            # 初始化OSS客户端
            auth = oss2.Auth(OSS_CONFIG['access_key_id'], OSS_CONFIG['access_key_secret'])
            bucket = oss2.Bucket(auth, OSS_CONFIG['endpoint'], OSS_CONFIG['bucket_name'])
            
            # 构建OSS文件路径
            oss_key = f"dota2/dem_analysis/{datetime.now().year}/{match_id}.json"
            
            # 上传JSON数据
            json_str = json.dumps(json_data, ensure_ascii=False, separators=(',', ':'))
            result = bucket.put_object(oss_key, json_str.encode('utf-8'))
            
            if result.status == 200:
                oss_url = f"https://{OSS_CONFIG['bucket_name']}.{OSS_CONFIG['endpoint']}/{oss_key}"
                logger.info(f"JSON数据上传OSS成功: {oss_url}")
                return oss_url
            else:
                logger.error(f"OSS上传失败 {match_id}: status {result.status}")
                return None
                
        except Exception as e:
            logger.error(f"上传JSON到OSS异常 {match_id}: {e}")
            return None
    
    async def _save_dem_analysis_link(self, match_id: str, oss_url: str):
        """保存DEM分析链接到数据库"""
        try:
            match = Match.query.filter_by(match_id=match_id).first()
            if match:
                if not match.analysis:
                    from models.match import MatchAnalysis
                    match.analysis = MatchAnalysis(match_id=match.id)
                
                # 保存OSS链接
                if not match.analysis.ai_analysis:
                    match.analysis.ai_analysis = {}
                
                match.analysis.ai_analysis['dem_json_url'] = oss_url
                match.analysis.ai_analysis['dem_processed_at'] = datetime.utcnow().isoformat()
                
                # 更新数据源标记
                if not match.data_sources:
                    match.data_sources = {}
                match.data_sources['dem'] = True
                
                db.session.commit()
                logger.info(f"DEM分析链接已保存: {match_id}")
                
        except Exception as e:
            logger.error(f"保存DEM分析链接异常 {match_id}: {e}")
            db.session.rollback()
    
    async def _get_recent_match_ids_for_dem(self, days: int = 1) -> List[str]:
        """获取需要DEM处理的最近比赛ID"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days)
            
            # 查询没有DEM数据的最近比赛
            matches = db.session.query(Match.match_id).filter(
                Match.start_time >= cutoff_time,
                Match.status == 'finished',
                ~Match.data_sources.has_key('dem')  # 没有DEM数据
            ).limit(10).all()  # 限制数量避免过载
            
            return [match.match_id for match in matches]
            
        except Exception as e:
            logger.error(f"获取比赛ID列表异常: {e}")
            return []
    
    async def sync_latest_data_on_demand(self) -> Dict[str, any]:
        """
        按需同步最新数据（手动触发按钮）
        
        Returns:
            同步结果摘要
        """
        logger.info("开始按需同步最新数据...")
        
        try:
            # 1. 快速同步最近2小时的数据
            sync_results = await self.sync_all_data(time_range_hours=2)
            
            # 2. 检查是否有新的DEM需要处理
            recent_match_ids = await self._get_recent_match_ids_for_dem()
            if recent_match_ids:
                dem_results = await self._sync_dem_data(recent_match_ids[:3])  # 只处理最近3场
                sync_results.update(dem_results)
            
            # 3. 生成摘要报告
            summary = {
                'sync_time': datetime.utcnow().isoformat(),
                'sources_synced': len(sync_results),
                'total_records': sum(r.records_success for r in sync_results.values()),
                'total_errors': sum(len(r.errors) for r in sync_results.values()),
                'execution_time': sum(r.execution_time for r in sync_results.values()),
                'details': {
                    source: {
                        'success': result.records_success,
                        'failed': result.records_failed,
                        'errors': len(result.errors)
                    }
                    for source, result in sync_results.items()
                }
            }
            
            logger.info(f"按需同步完成: {summary}")
            return summary
            
        except Exception as e:
            logger.error(f"按需同步异常: {e}")
            return {
                'error': str(e),
                'sync_time': datetime.utcnow().isoformat()
            }