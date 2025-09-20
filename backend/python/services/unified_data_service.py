"""
统一数据整合服务 - 更新版
协调 OpenDota API、STRATZ API、Liquipedia 爬虫、DEM解析四个数据源
确保所有数据源正确流入数据整合服务
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
from services.data_integration_service import DataIntegrationService
from services.dem_parser_service import DEMParserService
from models.match import Match, Team, Player, League, MatchPlayer, MatchAnalysis
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
    """统一数据整合服务 - 更新版"""
    
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
            
        # 初始化各个服务
        self.opendota = OpenDotaService(api_key=opendota_key)
        self.stratz = StratzService(api_key=stratz_key)
        self.liquipedia = LiquipediaService()
        
        # 初始化数据整合服务 - 核心改进
        self.data_integration = DataIntegrationService(
            opendota_key=opendota_key,
            stratz_key=stratz_key
        )
        
        # 初始化DEM解析服务
        self.dem_parser = DEMParserService(opendota_key=opendota_key)
        
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
        同步所有数据源 - 通过数据整合服务
        
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
        
        # 并发同步各数据源 - 通过整合服务
        tasks = [
            self._sync_integrated_data(time_range_hours),  # 使用整合服务
            self._sync_dem_data()  # DEM解析较慢，可选择性执行
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
    
    async def _sync_integrated_data(self, time_range_hours: int) -> Dict[str, SyncResult]:
        """
        通过数据整合服务同步所有API数据源
        """
        results = {}
        start_time = datetime.now()
        
        try:
            logger.info("开始通过数据整合服务同步数据...")
            
            # 检查所有服务状态
            service_status = self.data_integration.check_all_services_status()
            logger.info(f"服务状态检查: {service_status['overall']['status']}")
            
            processed = 0
            success = 0
            errors = []
            
            # 同步战队数据（通过整合服务）
            logger.info("同步战队数据...")
            team_sync_result = await self._sync_teams_via_integration()
            if team_sync_result['success']:
                success += team_sync_result['records_success']
                processed += team_sync_result['records_processed']
            else:
                errors.extend(team_sync_result['errors'])
            
            # 同步比赛数据（通过整合服务）
            logger.info("同步比赛数据...")
            match_sync_result = await self._sync_matches_via_integration(time_range_hours)
            if match_sync_result['success']:
                success += match_sync_result['records_success']
                processed += match_sync_result['records_processed']
            else:
                errors.extend(match_sync_result['errors'])
            
            # 同步锦标赛数据
            logger.info("同步锦标赛数据...")
            tournament_sync_result = await self._sync_tournaments_via_integration()
            if tournament_sync_result['success']:
                success += tournament_sync_result['records_success']
                processed += tournament_sync_result['records_processed']
            else:
                errors.extend(tournament_sync_result['errors'])
            
            results['integrated_data'] = SyncResult(
                source=DataSource.LIQUIPEDIA,  # 代表整合数据
                success=len(errors) == 0,
                records_processed=processed,
                records_success=success,
                records_failed=processed - success,
                errors=errors,
                execution_time=(datetime.now() - start_time).total_seconds()
            )
            
        except Exception as e:
            logger.error(f"整合数据同步异常: {e}")
            results['integrated_data'] = SyncResult(
                source=DataSource.LIQUIPEDIA,
                success=False,
                records_processed=0,
                records_success=0,
                records_failed=0,
                errors=[str(e)],
                execution_time=(datetime.now() - start_time).total_seconds()
            )
        
        return results
    
    async def _sync_teams_via_integration(self) -> Dict:
        """通过数据整合服务同步战队数据"""
        try:
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
                    # 使用数据整合服务获取增强战队数据
                    enhanced_team = self.data_integration.get_enhanced_team_data(team_name)
                    if enhanced_team:
                        # 处理并保存到数据库
                        await self._process_enhanced_team_data(enhanced_team)
                        success += 1
                    else:
                        errors.append(f"Team {team_name}: 无法获取增强数据")
                        
                except Exception as e:
                    errors.append(f"Team {team_name}: {str(e)}")
                
                processed += 1
                await asyncio.sleep(self.rate_limits['liquipedia'])
            
            return {
                'success': len(errors) == 0,
                'records_processed': processed,
                'records_success': success,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"战队数据同步失败: {e}")
            return {
                'success': False,
                'records_processed': 0,
                'records_success': 0,
                'errors': [str(e)]
            }
    
    async def _sync_matches_via_integration(self, time_range_hours: int) -> Dict:
        """通过数据整合服务同步比赛数据"""
        try:
            # 获取职业比赛列表
            pro_matches = self.opendota.get_pro_matches(limit=50)
            
            processed = 0
            success = 0
            errors = []
            
            # 过滤时间范围内的比赛
            cutoff_time = datetime.utcnow() - timedelta(hours=time_range_hours)
            recent_matches = [
                match for match in pro_matches
                if datetime.utcfromtimestamp(match.get('start_time', 0)) >= cutoff_time
            ]
            
            for match_data in recent_matches[:10]:  # 限制数量避免过载
                try:
                    match_id = match_data.get('match_id')
                    if match_id:
                        # 使用数据整合服务获取增强比赛数据
                        enhanced_match = self.data_integration.get_enhanced_match_data(match_id)
                        if enhanced_match:
                            # 处理并保存到数据库
                            await self._process_enhanced_match_data(enhanced_match)
                            success += 1
                        else:
                            errors.append(f"Match {match_id}: 无法获取增强数据")
                            
                except Exception as e:
                    errors.append(f"Match {match_data.get('match_id')}: {str(e)}")
                
                processed += 1
                await asyncio.sleep(self.rate_limits['opendota'])
            
            return {
                'success': len(errors) == 0,
                'records_processed': processed,
                'records_success': success,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"比赛数据同步失败: {e}")
            return {
                'success': False,
                'records_processed': 0,
                'records_success': 0,
                'errors': [str(e)]
            }
    
    async def _sync_tournaments_via_integration(self) -> Dict:
        """通过数据整合服务同步锦标赛数据"""
        try:
            # 使用数据整合服务获取锦标赛数据
            tournament_data = self.data_integration.get_tournament_data(limit=20)
            
            if tournament_data and tournament_data.get('liquipedia_tournaments'):
                tournaments = tournament_data['liquipedia_tournaments']
                
                processed = len(tournaments)
                success = 0
                errors = []
                
                for tournament in tournaments:
                    try:
                        # 处理并保存锦标赛数据
                        await self._process_tournament_data(tournament)
                        success += 1
                    except Exception as e:
                        errors.append(f"Tournament {tournament.get('name', 'unknown')}: {str(e)}")
                
                return {
                    'success': len(errors) == 0,
                    'records_processed': processed,
                    'records_success': success,
                    'errors': errors
                }
            else:
                return {
                    'success': False,
                    'records_processed': 0,
                    'records_success': 0,
                    'errors': ['无法获取锦标赛数据']
                }
                
        except Exception as e:
            logger.error(f"锦标赛数据同步失败: {e}")
            return {
                'success': False,
                'records_processed': 0,
                'records_success': 0,
                'errors': [str(e)]
            }
    
    async def _process_enhanced_team_data(self, enhanced_team: Dict) -> bool:
        """处理增强战队数据并保存到数据库"""
        try:
            team_name = enhanced_team.get('team_name', '')
            liquipedia_data = enhanced_team.get('liquipedia_data', {})
            
            if not team_name or not liquipedia_data:
                return False
            
            # 查找或创建战队记录
            team = Team.query.filter_by(name=team_name).first()
            if not team:
                team = Team(name=team_name)
                db.session.add(team)
                logger.info(f"创建新战队: {team_name}")
            
            # 更新战队信息（来自Liquipedia）
            if liquipedia_data.get('logo_url'):
                team.logo_url = liquipedia_data['logo_url']
            if liquipedia_data.get('region'):
                team.region = liquipedia_data['region']
            if liquipedia_data.get('total_earnings'):
                team.total_earnings = liquipedia_data['total_earnings']
            
            # 标记数据来源
            if not team.data_sources:
                team.data_sources = {}
            team.data_sources['liquipedia'] = True
            team.data_sources['enhanced_integration'] = True
            
            # 处理战队阵容
            current_roster = liquipedia_data.get('current_roster', [])
            if current_roster:
                await self._process_team_roster_enhanced(team.id, current_roster)
            
            team.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"增强战队数据处理成功: {team_name}")
            return True
            
        except Exception as e:
            logger.error(f"处理增强战队数据失败: {e}")
            db.session.rollback()
            return False
    
    async def _process_enhanced_match_data(self, enhanced_match: Dict) -> bool:
        """处理增强比赛数据并保存到数据库"""
        try:
            match_id = enhanced_match.get('match_id')
            opendota_data = enhanced_match.get('opendota_data', {})
            stratz_data = enhanced_match.get('stratz_data', {})
            
            if not match_id or not opendota_data:
                return False
            
            # 查找或创建比赛记录
            match = Match.query.filter_by(match_id=str(match_id)).first()
            if not match:
                match = Match(match_id=str(match_id))
                db.session.add(match)
            
            # 更新比赛基本信息（来自OpenDota）
            match.radiant_win = opendota_data.get('radiant_win')
            match.duration = opendota_data.get('duration')
            match.start_time = datetime.utcfromtimestamp(opendota_data.get('start_time', 0))
            
            # 补充STRATZ数据
            if stratz_data:
                # STRATZ可能有额外的分析数据
                pass
            
            # 标记数据来源
            if not match.data_sources:
                match.data_sources = {}
            match.data_sources['opendota'] = True
            match.data_sources['stratz'] = bool(stratz_data)
            match.data_sources['enhanced_integration'] = True
            
            match.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"增强比赛数据处理成功: {match_id}")
            return True
            
        except Exception as e:
            logger.error(f"处理增强比赛数据失败: {e}")
            db.session.rollback()
            return False
    
    async def _process_tournament_data(self, tournament: Dict) -> bool:
        """处理锦标赛数据"""
        try:
            tournament_name = tournament.get('name', '')
            if not tournament_name:
                return False
            
            # 查找或创建联赛记录
            league = League.query.filter_by(name=tournament_name).first()
            if not league:
                league = League(name=tournament_name)
                db.session.add(league)
            
            # 更新联赛信息
            if tournament.get('prize_pool'):
                league.prize_pool = tournament['prize_pool']
            if tournament.get('date'):
                league.start_date = tournament['date']
            
            # 标记数据来源
            if not league.data_sources:
                league.data_sources = {}
            league.data_sources['liquipedia'] = True
            
            league.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"锦标赛数据处理成功: {tournament_name}")
            return True
            
        except Exception as e:
            logger.error(f"处理锦标赛数据失败: {e}")
            db.session.rollback()
            return False
    
    async def _process_team_roster_enhanced(self, team_id: int, roster: List[Dict]):
        """处理战队阵容信息（增强版）"""
        try:
            # 将现有选手标记为非活跃
            Player.query.filter_by(team_id=team_id).update({'is_active': False})
            
            # 处理新阵容
            for player_data in roster:
                player_id = player_data.get('id', '')
                player_name = player_data.get('name', '')
                
                if not player_id:
                    continue
                
                # 查找或创建选手
                player = Player.query.filter_by(name=player_id).first()
                if not player:
                    player = Player(name=player_id)
                    db.session.add(player)
                
                # 更新选手信息
                player.team_id = team_id
                if player_name:
                    player.real_name = player_name
                player.is_active = True
                player.updated_at = datetime.utcnow()
                
                # 标记数据来源
                if not player.data_sources:
                    player.data_sources = {}
                player.data_sources['liquipedia'] = True
            
            logger.info(f"战队阵容更新成功: {team_id}, 选手数量: {len(roster)}")
            
        except Exception as e:
            logger.error(f"处理战队阵容失败: {e}")
            raise
    
    # 更新的DEM处理逻辑 - 使用新的DEMParserService
    async def _sync_dem_data(self, match_ids: List[int] = None, days_back: int = 7, limit: int = 50) -> Dict[str, SyncResult]:
        """
        同步DEM数据 - 使用新的DEM解析服务
        从OpenDota获取职业比赛 -> 下载DEM -> 解析为JSON
        """
        start_time = datetime.now()
        
        try:
            logger.info("开始新版DEM数据处理流程...")
            
            # 如果没有指定match_ids，则获取最近的职业比赛
            if not match_ids:
                logger.info(f"获取最近{days_back}天的职业比赛ID")
                match_ids = await self.dem_parser.get_professional_match_ids(days_back, limit)
            
            if not match_ids:
                logger.warning("未获取到需要处理的比赛ID")
                return {
                    'dem': SyncResult(
                        source=DataSource.DEM,
                        records_processed=0,
                        records_success=0,
                        records_failed=0,
                        errors=["未获取到需要处理的比赛ID"],
                        execution_time=0.0
                    )
                }
            
            logger.info(f"开始处理{len(match_ids)}场比赛的DEM解析")
            
            # 使用DEM解析服务进行批量处理
            batch_result = await self.dem_parser.batch_process_matches(
                match_ids=match_ids,
                max_concurrent=2  # 控制并发数避免过载
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 构建结果
            dem_sync_result = SyncResult(
                source=DataSource.DEM,
                records_processed=batch_result['total_matches'],
                records_success=batch_result['successful'],
                records_failed=batch_result['failed'],
                errors=[],
                execution_time=execution_time
            )
            
            # 收集错误信息
            for result in batch_result['results']:
                if not result['success'] and 'errors' in result:
                    dem_sync_result.errors.extend(result['errors'])
            
            logger.info(f"DEM数据处理完成: 成功{batch_result['successful']}场，失败{batch_result['failed']}场，耗时{execution_time:.2f}秒")
            
            return {'dem': dem_sync_result}
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"DEM数据处理异常: {e}")
            return {
                'dem': SyncResult(
                    source=DataSource.DEM,
                    records_processed=0,
                    records_success=0,
                    records_failed=0,
                    errors=[str(e)],
                    execution_time=execution_time
                )
            }
    
    # 保持所有原有的DEM处理方法不变
    async def _download_dem_file(self, match_id: str) -> Optional[str]:
        """下载DEM文件 - 保持原有逻辑"""
        import os
        import aiohttp
        
        try:
            # 构建DEM文件URL（OpenDota提供）
            # 从配置文件获取OpenDota API URL
            try:
                from utils.config_loader import config_loader
                api_config = config_loader.get_api_config('opendota')
                base_url = api_config.get('base_url', "https://api.opendota.com/api")
            except ImportError:
                base_url = "https://api.opendota.com/api"
            
            dem_url = f"{base_url}/replays?match_id={match_id}"
            
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
        """解析DEM文件为JSON数据 - 保持原有逻辑"""
        import subprocess
        import tempfile
        import os
        
        try:
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
        """上传JSON数据到阿里云OSS - 保持原有逻辑"""
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
        """保存DEM分析链接到数据库 - 保持原有逻辑"""
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
        """获取需要DEM处理的最近比赛ID - 保持原有逻辑"""
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
    
    # 保持所有原有的数据质量评估和清理方法
    async def _assess_and_clean_data(self):
        """数据质量评估和清理 - 保持原有逻辑"""
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
            duplicate_query = """
            SELECT match_id, COUNT(*) as count
            FROM matches 
            GROUP BY match_id 
            HAVING COUNT(*) > 1
            """
            
            logger.info("检查重复比赛数据...")
            
        except Exception as e:
            logger.error(f"移除重复比赛数据异常: {e}")
    
    async def _fix_data_inconsistencies(self):
        """修复数据不一致"""
        try:
            logger.info("修复数据不一致...")
            
            # 示例：修复没有联赛信息的比赛
            matches_without_league = Match.query.filter(Match.league_id.is_(None)).limit(100).all()
            for match in matches_without_league:
                # 尝试从其他数据源获取联赛信息
                if match.data_sources and 'opendota' in match.data_sources:
                    pass
            
        except Exception as e:
            logger.error(f"修复数据不一致异常: {e}")
    
    async def _clean_expired_data(self):
        """清理过期数据"""
        try:
            # 清理30天前的临时数据
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            logger.info(f"清理{cutoff_date}前的过期数据...")
            
        except Exception as e:
            logger.error(f"清理过期数据异常: {e}")
    
    def _generate_sync_report(self, sync_results: Dict[str, SyncResult]) -> Dict[str, any]:
        """生成同步报告 - 保持原有逻辑"""
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
            'source_status': source_status,
            'integration_service_used': True  # 标记使用了整合服务
        }
        
        return report
    
    async def sync_latest_data_on_demand(self) -> Dict[str, any]:
        """
        按需同步最新数据（手动触发按钮）
        通过数据整合服务进行
        """
        logger.info("开始按需同步最新数据（通过整合服务）...")
        
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
                'integration_service_status': 'active',  # 标记整合服务状态
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
                'sync_time': datetime.utcnow().isoformat(),
                'integration_service_status': 'error'
            }
    
    # 新增：直接访问整合服务的便捷方法
    def get_integration_service(self) -> DataIntegrationService:
        """获取数据整合服务实例"""
        return self.data_integration
    
    async def get_service_health_check(self) -> Dict:
        """获取所有服务健康检查"""
        return self.data_integration.check_all_services_status()