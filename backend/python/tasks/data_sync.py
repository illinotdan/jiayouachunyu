"""
数据同步任务
用于从外部API获取和同步比赛数据
支持OpenDota、STRATZ、Liquipedia三个数据源，采用T-1时间策略
"""

import requests
import time
from datetime import datetime, timedelta
from celery import Celery
from flask import current_app
from sqlalchemy import desc

from config.database import db
from models.content import Discussion
from models.match import Match, MatchStatus, League, Team, MatchPlayer, MatchAnalysis, HeroStats
from models.user import User
from utils.response import ApiResponse
from services.opendota_service import OpenDotaService
from services.stratz_service import StratzService
from services.liquipedia_service import LiquipediaService
from services.data_integration_service import DataIntegrationService
from services.unified_data_service import UnifiedDataService

# 创建Celery实例
celery = Celery('dota_analysis')

# 初始化数据服务
def get_data_services():
    """获取数据服务实例"""
    return {
        'opendota': OpenDotaService(api_key=current_app.config.get('OPENDOTA_API_KEY')),
        'stratz': StratzService(api_key=current_app.config.get('STRATZ_API_KEY')),
        'liquipedia': LiquipediaService(),
        'integration': DataIntegrationService(
            opendota_key=current_app.config.get('OPENDOTA_API_KEY'),
            stratz_key=current_app.config.get('STRATZ_API_KEY')
        )
    }

@celery.task
def sync_all_data():
    """完整数据同步流水线 - T-1策略"""
    try:
        current_app.logger.info("开始完整数据同步流水线...")
        
        # 使用统一数据服务进行同步
        unified_service = UnifiedDataService()
        result = unified_service.sync_all_data()
        
        if result['success']:
            current_app.logger.info(f"统一数据服务同步完成: {result}")
            
            # 触发AI分析
            trigger_ai_analysis.delay()
            
            return {
                'matches_synced': result.get('matches_synced', 0),
                'teams_synced': result.get('teams_synced', 0),
                'heroes_synced': result.get('heroes_synced', 0),
                'items_synced': result.get('items_synced', 0),
                'sync_time': datetime.utcnow().isoformat(),
                'source': 'unified_service'
            }
        else:
            current_app.logger.error(f"统一数据服务同步失败: {result.get('error', '未知错误')}")
            return {'error': result.get('error', '统一数据服务同步失败')}
            
    except Exception as e:
        current_app.logger.error(f"完整数据同步失败: {e}")
        return {'error': str(e)}

@celery.task
def sync_match_data():
    """同步比赛数据任务（保持向后兼容）"""
    try:
        current_app.logger.info("开始同步比赛数据...")
        
        # 使用T-1策略
        yesterday = datetime.utcnow() - timedelta(days=1)
        start_time = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        services = get_data_services()
        synced_count = sync_t1_matches(services, start_time, end_time)
        
        current_app.logger.info(f"比赛数据同步完成，同步了 {synced_count} 场比赛")
        return synced_count
        
    except Exception as e:
        current_app.logger.error(f"同步比赛数据失败: {e}")
        return 0

def sync_basic_data(services):
    """同步基础数据（英雄、物品等）"""
    try:
        current_app.logger.info("开始同步基础数据...")
        
        # 同步英雄数据
        sync_heroes_data(services['opendota'], services['stratz'])
        
        # 同步物品数据
        sync_items_data(services['stratz'])
        
        current_app.logger.info("基础数据同步完成")
        
    except Exception as e:
        current_app.logger.error(f"同步基础数据失败: {e}")

def sync_heroes_data(opendota_service, stratz_service):
    """同步英雄数据"""
    try:
        from models.match import Hero
        
        # 从OpenDota获取英雄列表
        opendota_heroes = opendota_service.get_heroes()
        
        # 从STRATZ获取英雄列表
        stratz_heroes = stratz_service.get_heroes('detailed')
        
        current_app.logger.info(f"OpenDota英雄数: {len(opendota_heroes)}, STRATZ英雄数: {len(stratz_heroes)}")
        
        # 合并和同步英雄数据
        for hero_data in opendota_heroes:
            hero_id = hero_data.get('id')
            if not hero_id:
                continue
                
            # 检查英雄是否已存在
            existing_hero = Hero.query.filter_by(id=hero_id).first()
            
            if not existing_hero:
                hero = Hero(
                    id=hero_id,
                    name=hero_data.get('name', ''),
                    display_name=hero_data.get('localized_name', ''),
                    primary_attribute=Hero.Attribute.STRENGTH,  # 默认值，需要从其他源获取
                    roles=hero_data.get('roles', []),
                    image_url=f"https://api.opendota.com{hero_data.get('img', '')}",
                    icon_url=f"https://api.opendota.com{hero_data.get('icon', '')}",
                    complexity=1,
                    is_active=True
                )
                db.session.add(hero)
        
        db.session.commit()
        current_app.logger.info("英雄数据同步完成")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"同步英雄数据失败: {e}")

def sync_items_data(stratz_service):
    """同步物品数据"""
    try:
        # 从STRATZ获取物品数据
        items = stratz_service.get_items()
        
        current_app.logger.info(f"获取到 {len(items)} 个物品")
        
        # 这里可以添加物品数据模型和同步逻辑
        # 暂时记录日志
        
    except Exception as e:
        current_app.logger.error(f"同步物品数据失败: {e}")

def sync_t1_matches(services, start_time, end_time):
    """同步T-1比赛数据"""
    try:
        current_app.logger.info(f"开始同步T-1比赛数据: {start_time} 到 {end_time}")
        
        synced_count = 0
        
        # 1. 从OpenDota获取职业比赛
        opendota_matches = fetch_matches_from_opendota(services['opendota'], start_time, end_time)
        current_app.logger.info(f"OpenDota获取到 {len(opendota_matches)} 场比赛")
        
        for match_data in opendota_matches:
            if sync_single_match(match_data, services):
                synced_count += 1
        
        # 2. 从STRATZ获取补充数据
        # 这里可以添加STRATZ特有的比赛数据获取逻辑
        
        current_app.logger.info(f"T-1比赛数据同步完成，共同步 {synced_count} 场比赛")
        return synced_count
        
    except Exception as e:
        current_app.logger.error(f"同步T-1比赛数据失败: {e}")
        return 0

def sync_teams_and_players(services):
    """同步战队和选手信息"""
    try:
        current_app.logger.info("开始同步战队和选手信息...")
        
        synced_count = 0
        
        # 1. 从Liquipedia获取热门战队
        popular_teams = [
            'Team Spirit', 'PSG.LGD', 'OG', 'Team Secret', 'Evil Geniuses',
            'Virtus.pro', 'T1', 'Team Liquid', 'Fnatic', 'Alliance'
        ]
        
        for team_name in popular_teams:
            team_info = services['liquipedia'].get_team_info(team_name)
            if team_info and sync_team_info(team_info):
                synced_count += 1
                
            # 避免请求过快
            time.sleep(2)
        
        current_app.logger.info(f"战队和选手信息同步完成，共同步 {synced_count} 个战队")
        return synced_count
        
    except Exception as e:
        current_app.logger.error(f"同步战队和选手信息失败: {e}")
        return 0

def sync_team_info(team_info):
    """同步单个战队信息"""
    try:
        team_name = team_info.get('name')
        if not team_name:
            return False
        
        # 检查战队是否已存在
        existing_team = Team.query.filter_by(name=team_name).first()
        
        if not existing_team:
            team = Team(
                name=team_name,
                tag=team_name[:3].upper(),
                logo_url=team_info.get('logo_url'),
                region=team_info.get('region'),
                description=team_info.get('description'),
                website_url=team_info.get('url'),
                social_links=team_info.get('social_links', {}),
                is_active=True
            )
            db.session.add(team)
        else:
            # 更新现有战队信息
            existing_team.logo_url = team_info.get('logo_url') or existing_team.logo_url
            existing_team.region = team_info.get('region') or existing_team.region
            existing_team.description = team_info.get('description') or existing_team.description
            existing_team.social_links = team_info.get('social_links', existing_team.social_links)
        
        db.session.commit()
        return True
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"同步战队信息失败 {team_info.get('name', 'Unknown')}: {e}")
        return False

def validate_and_clean_data():
    """数据清洗和验证"""
    try:
        current_app.logger.info("开始数据清洗和验证...")
        
        validation_result = {
            'orphan_matches': 0,
            'missing_logos': 0,
            'data_quality_issues': []
        }
        
        # 检查孤儿比赛（缺少战队信息）
        orphan_matches = Match.query.filter(
            (Match.radiant_team_id.is_(None)) | (Match.dire_team_id.is_(None))
        ).count()
        validation_result['orphan_matches'] = orphan_matches
        
        # 检查缺失Logo的战队
        teams_without_logo = Team.query.filter(
            (Team.logo_url.is_(None)) | (Team.logo_url == '')
        ).count()
        validation_result['missing_logos'] = teams_without_logo
        
        # 记录数据质量问题
        if orphan_matches > 0:
            validation_result['data_quality_issues'].append(f"{orphan_matches} 场比赛缺少战队信息")
        
        if teams_without_logo > 0:
            validation_result['data_quality_issues'].append(f"{teams_without_logo} 个战队缺少Logo")
        
        current_app.logger.info(f"数据验证完成: {validation_result}")
        return validation_result
        
    except Exception as e:
        current_app.logger.error(f"数据验证失败: {e}")
        return {'error': str(e)}

def fetch_matches_from_opendota(opendota_service, start_time, end_time):
    """从OpenDota获取指定时间范围的比赛"""
    try:
        # 获取职业比赛
        pro_matches = opendota_service.get_pro_matches(limit=200)
        
        # 过滤时间范围
        filtered_matches = []
        for match in pro_matches:
            match_time = datetime.utcfromtimestamp(match.get('start_time', 0))
            if start_time <= match_time <= end_time:
                filtered_matches.append(match)
        
        return filtered_matches
        
    except Exception as e:
        current_app.logger.error(f"从OpenDota获取比赛失败: {e}")
        return []

@celery.task
def trigger_ai_analysis():
    """触发AI分析任务"""
    try:
        current_app.logger.info("触发AI分析任务...")
        
        # 这里将调用AI分析服务
        # 暂时记录日志
        current_app.logger.info("AI分析任务已触发")
        
        return {'status': 'triggered', 'time': datetime.utcnow().isoformat()}
        
    except Exception as e:
        current_app.logger.error(f"触发AI分析失败: {e}")
        return {'error': str(e)}

def fetch_recent_matches_from_opendota():
    """从OpenDota API获取最近比赛"""
    try:
        api_key = current_app.config.get('OPENDOTA_API_KEY')
        
        # 获取职业比赛
        url = "https://api.opendota.com/api/proMatches"
        headers = {}
        
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        matches = response.json()
        
        # 只处理最近24小时的比赛
        recent_matches = []
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        for match in matches:
            match_time = datetime.utcfromtimestamp(match['start_time'])
            if match_time >= cutoff_time:
                recent_matches.append(match)
        
        return recent_matches[:50]  # 限制数量
        
    except Exception as e:
        current_app.logger.error(f"获取OpenDota数据失败: {e}")
        return []

def sync_single_match(match_data, services=None):
    """同步单场比赛数据"""
    try:
        match_id = str(match_data['match_id'])
        
        # 检查比赛是否已存在
        existing_match = Match.query.filter_by(match_id=match_id).first()
        if existing_match:
            return False
        
        # 获取或创建战队
        radiant_team = get_or_create_team(match_data.get('radiant_team'))
        dire_team = get_or_create_team(match_data.get('dire_team'))
        
        # 获取或创建联赛
        league = get_or_create_league(match_data.get('league'))
        
        # 创建比赛记录
        match = Match(
            match_id=match_id,
            league_id=league.id if league else None,
            radiant_team_id=radiant_team.id if radiant_team else None,
            dire_team_id=dire_team.id if dire_team else None,
            radiant_score=match_data.get('radiant_score', 0),
            dire_score=match_data.get('dire_score', 0),
            radiant_win=match_data.get('radiant_win'),
            duration=match_data.get('duration'),
            start_time=datetime.utcfromtimestamp(match_data['start_time']),
            status=MatchStatus.FINISHED,
            patch_version=match_data.get('patch'),
            region=match_data.get('region')
        )
        
        db.session.add(match)
        db.session.flush()  # 获取match.id
        
        # 获取详细比赛数据
        if services and 'integration' in services:
            # 使用数据整合服务获取增强数据
            enhanced_data = services['integration'].get_enhanced_match_data(int(match_id))
            if enhanced_data:
                sync_enhanced_match_data(match.id, enhanced_data)
        else:
            # 使用原有方式获取详细数据
            detailed_data = fetch_match_details(match_id)
            if detailed_data:
                sync_match_players(match.id, detailed_data)
                sync_match_analysis(match.id, detailed_data)
        
        db.session.commit()
        return True
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"同步比赛 {match_data.get('match_id')} 失败: {e}")
        return False

def sync_enhanced_match_data(match_id, enhanced_data):
    """同步增强版比赛数据"""
    try:
        # 处理OpenDota数据
        opendota_data = enhanced_data.get('opendota_data', {})
        if opendota_data:
            sync_match_players(match_id, opendota_data)
            sync_match_analysis(match_id, opendota_data)
        
        # 处理STRATZ数据
        stratz_data = enhanced_data.get('stratz_data', {})
        if stratz_data:
            # 这里可以添加STRATZ特有的数据处理逻辑
            current_app.logger.info(f"处理STRATZ数据: {match_id}")
        
        # 保存数据质量评估
        data_quality = enhanced_data.get('data_quality', {})
        current_app.logger.info(f"比赛 {match_id} 数据质量: {data_quality}")
        
    except Exception as e:
        current_app.logger.error(f"同步增强版比赛数据失败 {match_id}: {e}")

def get_or_create_team(team_data):
    """获取或创建战队"""
    if not team_data or not team_data.get('name'):
        return None
    
    team = Team.query.filter_by(name=team_data['name']).first()
    
    if not team:
        team = Team(
            name=team_data['name'],
            tag=team_data.get('tag', team_data['name'][:3].upper()),
            logo_url=team_data.get('logo_url')
        )
        db.session.add(team)
        db.session.flush()
    
    return team

def get_or_create_league(league_data):
    """获取或创建联赛"""
    if not league_data or not league_data.get('name'):
        return None
    
    league = League.query.filter_by(name=league_data['name']).first()
    
    if not league:
        league = League(
            name=league_data['name'],
            tier=league_data.get('tier', 3)
        )
        db.session.add(league)
        db.session.flush()
    
    return league

def fetch_match_details(match_id):
    """获取比赛详细数据"""
    try:
        api_key = current_app.config.get('OPENDOTA_API_KEY')
        
        url = f"https://api.opendota.com/api/matches/{match_id}"
        headers = {}
        
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        return response.json()
        
    except Exception as e:
        current_app.logger.error(f"获取比赛详情失败 {match_id}: {e}")
        return None

def sync_match_players(match_id, match_data):
    """同步比赛选手数据"""
    try:
        players_data = match_data.get('players', [])
        
        for i, player_data in enumerate(players_data):
            team_side = 'radiant' if i < 5 else 'dire'
            
            match_player = MatchPlayer(
                match_id=match_id,
                account_id=str(player_data.get('account_id', 0)),
                player_name=player_data.get('personaname', f'Player {i+1}'),
                team_side=team_side,
                hero_id=player_data.get('hero_id', 1),
                kills=player_data.get('kills', 0),
                deaths=player_data.get('deaths', 0),
                assists=player_data.get('assists', 0),
                last_hits=player_data.get('last_hits', 0),
                denies=player_data.get('denies', 0),
                gpm=player_data.get('gold_per_min', 0),
                xpm=player_data.get('xp_per_min', 0),
                net_worth=player_data.get('net_worth', 0),
                hero_damage=player_data.get('hero_damage', 0),
                tower_damage=player_data.get('tower_damage', 0),
                hero_healing=player_data.get('hero_healing', 0),
                level=player_data.get('level', 1),
                items=player_data.get('item_0', [])  # 简化处理
            )
            
            db.session.add(match_player)
        
    except Exception as e:
        current_app.logger.error(f"同步选手数据失败: {e}")

def sync_match_analysis(match_id, match_data):
    """同步比赛分析数据"""
    try:
        # 提取关键时刻
        key_moments = []
        objectives = match_data.get('objectives', [])
        
        for obj in objectives[:10]:  # 限制数量
            if obj.get('type') in ['CHAT_MESSAGE_FIRSTBLOOD', 'CHAT_MESSAGE_AEGIS']:
                key_moments.append({
                    'time': f"{obj.get('time', 0) // 60}:{obj.get('time', 0) % 60:02d}",
                    'event': obj.get('type', 'Unknown'),
                    'description': f"第{obj.get('time', 0) // 60}分钟重要事件"
                })
        
        # 找出MVP（最高KDA的选手）
        mvp_player = None
        best_kda = 0
        
        for player in match_data.get('players', []):
            kills = player.get('kills', 0)
            deaths = max(player.get('deaths', 1), 1)  # 避免除零
            assists = player.get('assists', 0)
            kda = (kills + assists) / deaths
            
            if kda > best_kda:
                best_kda = kda
                mvp_player = player.get('personaname', 'Unknown')
        
        # 创建分析记录
        analysis = MatchAnalysis(
            match_id=match_id,
            key_moments=key_moments,
            mvp_player=mvp_player,
            turning_point="比赛关键转折点分析",
            prediction_confidence=85,
            prediction_reasoning="基于数据分析的预测"
        )
        
        db.session.add(analysis)
        
    except Exception as e:
        current_app.logger.error(f"同步分析数据失败: {e}")

@celery.task
def update_hero_statistics():
    """更新英雄统计数据任务"""
    try:
        current_app.logger.info("开始更新英雄统计...")
        
        from models.match import HeroStats, Hero
        
        # 获取所有英雄
        heroes = Hero.query.filter_by(is_active=True).all()
        
        for hero in heroes:
            # 计算不同时间周期的统计
            for period in ['week', 'month', 'all']:
                calculate_hero_stats_for_period(hero.id, period)
        
        current_app.logger.info("英雄统计更新完成")
        return True
        
    except Exception as e:
        current_app.logger.error(f"更新英雄统计失败: {e}")
        return False

def calculate_hero_stats_for_period(hero_id, period):
    """计算指定英雄在指定时期的统计数据"""
    try:
        # 计算时间范围
        if period == 'week':
            start_date = datetime.utcnow() - timedelta(days=7)
            period_enum = HeroStats.Period.WEEK
        elif period == 'month':
            start_date = datetime.utcnow() - timedelta(days=30)
            period_enum = HeroStats.Period.MONTH
        else:
            start_date = None
            period_enum = HeroStats.Period.ALL
        
        # 构建查询
        from models.match import MatchPlayer, Match
        
        query = db.session.query(MatchPlayer).join(Match).filter(
            MatchPlayer.hero_id == hero_id,
            Match.status == MatchStatus.FINISHED
        )
        
        if start_date:
            query = query.filter(Match.start_time >= start_date)
        
        player_performances = query.all()
        
        if not player_performances:
            return
        
        # 计算统计数据
        total_matches = len(player_performances)
        wins = sum(1 for p in player_performances if 
                  (p.team_side.value == 'radiant' and p.match.radiant_win) or
                  (p.team_side.value == 'dire' and not p.match.radiant_win))
        
        win_rate = (wins / total_matches * 100) if total_matches > 0 else 0
        
        # 计算平均数据
        avg_kda = sum((p.kills + p.assists) / max(p.deaths, 1) for p in player_performances) / total_matches
        avg_gpm = sum(p.gpm for p in player_performances) / total_matches
        avg_xpm = sum(p.xpm for p in player_performances) / total_matches
        
        # 更新或创建统计记录
        hero_stat = HeroStats.query.filter_by(
            hero_id=hero_id,
            period_type=period_enum,
            tier_filter=HeroStats.Tier.ALL
        ).first()
        
        if not hero_stat:
            hero_stat = HeroStats(
                hero_id=hero_id,
                period_type=period_enum,
                tier_filter=HeroStats.Tier.ALL
            )
            db.session.add(hero_stat)
        
        # 更新数据
        hero_stat.total_matches = total_matches
        hero_stat.wins = wins
        hero_stat.win_rate = round(win_rate, 2)
        hero_stat.avg_kda = round(avg_kda, 2)
        hero_stat.avg_gpm = int(avg_gpm)
        hero_stat.avg_xpm = int(avg_xpm)
        hero_stat.calculated_at = datetime.utcnow()
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"计算英雄 {hero_id} 统计失败: {e}")

@celery.task
def resolve_match_predictions():
    """解析比赛预测结果任务"""
    try:
        current_app.logger.info("开始解析预测结果...")
        
        from models.match import ExpertPrediction
        
        # 获取已结束但预测未解析的比赛
        finished_matches = Match.query.filter(
            Match.status == MatchStatus.FINISHED,
            Match.end_time.isnot(None)
        ).join(ExpertPrediction).filter(
            ExpertPrediction.result == 'pending'
        ).distinct().all()
        
        resolved_count = 0
        for match in finished_matches:
            ExpertPrediction.resolve_predictions_for_match(match.id)
            resolved_count += 1
        
        current_app.logger.info(f"预测结果解析完成，处理了 {resolved_count} 场比赛")
        return resolved_count
        
    except Exception as e:
        current_app.logger.error(f"解析预测结果失败: {e}")
        return 0

@celery.task
def calculate_daily_statistics():
    """计算每日统计数据任务"""
    try:
        from models.audit import DailyStats
        from datetime import date
        
        yesterday = date.today() - timedelta(days=1)
        
        # 计算昨天的统计数据
        daily_stat = DailyStats.calculate_daily_stats(yesterday)
        
        if daily_stat:
            current_app.logger.info(f"每日统计计算完成: {yesterday}")
            return True
        else:
            current_app.logger.error(f"每日统计计算失败: {yesterday}")
            return False
            
    except Exception as e:
        current_app.logger.error(f"计算每日统计失败: {e}")
        return False

@celery.task
def cleanup_expired_data():
    """清理过期数据任务"""
    try:
        from models.user import UserSession
        from models.notification import Notification
        from models.content import ContentView
        
        # 清理过期会话
        expired_sessions = UserSession.cleanup_expired()
        
        # 清理旧通知
        deleted_notifications = Notification.cleanup_old_notifications(days=30)
        
        # 清理旧浏览记录
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        deleted_views = ContentView.query.filter(
            ContentView.created_at < thirty_days_ago
        ).delete()
        
        db.session.commit()
        
        current_app.logger.info(
            f"数据清理完成 - 会话: {expired_sessions}, "
            f"通知: {deleted_notifications}, 浏览记录: {deleted_views}"
        )
        
        return {
            'sessions': expired_sessions,
            'notifications': deleted_notifications,
            'views': deleted_views
        }
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"清理过期数据失败: {e}")
        return None

@celery.task
def send_digest_emails():
    """发送每日摘要邮件任务"""
    try:
        from models.user import User
        from flask_mail import Message, Mail
        
        # 获取订阅了邮件摘要的用户
        users = User.query.filter_by(is_active=True).all()
        
        # 获取昨天的热门内容
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        hot_discussions = Discussion.query.filter(
            Discussion.created_at >= yesterday
        ).order_by(desc(Discussion.view_count)).limit(5).all()
        
        sent_count = 0
        
        for user in users:
            # 检查用户是否启用了邮件通知
            if user.profile and not user.profile.notification_settings.get('emailNotifications', True):
                continue
            
            try:
                send_daily_digest(user, hot_discussions)
                sent_count += 1
                
                # 避免发送过快
                time.sleep(0.1)
                
            except Exception as e:
                current_app.logger.error(f"发送摘要邮件给 {user.email} 失败: {e}")
        
        current_app.logger.info(f"每日摘要邮件发送完成，发送了 {sent_count} 封邮件")
        return sent_count
        
    except Exception as e:
        current_app.logger.error(f"发送摘要邮件任务失败: {e}")
        return 0

def send_daily_digest(user, hot_discussions):
    """发送单个用户的每日摘要"""
    from flask_mail import Message, Mail
    
    mail = Mail(current_app)
    
    # 构建邮件内容
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #1a1f2e; color: #e2e8f0; padding: 20px;">
        <h1 style="color: #4299e1; text-align: center;">🎮 刀塔解析每日摘要</h1>
        
        <p>Hi {user.username},</p>
        
        <p>以下是昨日的热门讨论：</p>
        
        <div style="margin: 20px 0;">
            {''.join([
                f'''
                <div style="background: #2d3748; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #4299e1;">
                    <h3 style="margin: 0 0 10px 0; color: #ffffff;">{discussion.title}</h3>
                    <p style="margin: 0; color: #a0aec0; font-size: 14px;">
                        👁️ {discussion.view_count} 浏览 | 👍 {discussion.like_count} 点赞 | 💬 {discussion.reply_count} 回复
                    </p>
                </div>
                '''
                for discussion in hot_discussions
            ])}
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="http://dotaanalysis.com" style="background: #4299e1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">
                访问刀塔解析
            </a>
        </div>
        
        <hr style="border: none; border-top: 1px solid #2d3748; margin: 20px 0;">
        
        <p style="color: #718096; font-size: 12px; text-align: center;">
            不想接收每日摘要？<a href="http://dotaanalysis.com/settings" style="color: #4299e1;">点击这里</a>修改设置
        </p>
    </div>
    """
    
    msg = Message(
        subject='[刀塔解析] 每日热门摘要',
        recipients=[user.email],
        html=html_content
    )
    
    mail.send(msg)

# Celery定时任务配置
@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """设置定时任务 - 采用T-1策略"""
    from celery.schedules import crontab
    
    # 每天凌晨1点执行完整数据同步（T-1策略）
    sender.add_periodic_task(
        crontab(hour=1, minute=0),
        sync_all_data.s(),
        name='daily T-1 data sync'
    )
    
    # 每天凌晨2点计算统计数据
    sender.add_periodic_task(
        crontab(hour=2, minute=0),
        calculate_daily_statistics.s(),
        name='calculate daily stats'
    )
    
    # 每天凌晨3点更新英雄统计
    sender.add_periodic_task(
        crontab(hour=3, minute=0),
        update_hero_statistics.s(),
        name='update hero stats'
    )
    
    # 每天凌晨4点清理过期数据
    sender.add_periodic_task(
        crontab(hour=4, minute=0),
        cleanup_expired_data.s(),
        name='cleanup expired data'
    )
    
    # 每30分钟解析预测结果（保持实时性）
    sender.add_periodic_task(
        1800.0,  # 30分钟
        resolve_match_predictions.s(),
        name='resolve predictions'
    )
    
    # 每天早上8点发送摘要邮件
    sender.add_periodic_task(
        crontab(hour=8, minute=0),
        send_digest_emails.s(),
        name='send daily digest'
    )
    
    # 备用：每4小时执行一次增量同步（仅比赛数据）
    sender.add_periodic_task(
        14400.0,  # 4小时
        sync_match_data.s(),
        name='incremental match sync'
    )
