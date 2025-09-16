"""
统计相关API路由
"""

from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError
from sqlalchemy import desc, func, and_
from datetime import datetime, timedelta

from config.database import db
from models.match import Hero, HeroStats, Match, MatchStatus, Team
from models.user import User, UserRole
from models.content import Discussion, Article
from utils.response import ApiResponse
from utils.decorators import limiter, cache

stats_bp = Blueprint('stats', __name__)

class HeroStatsFilterSchema(Schema):
    """英雄统计筛选参数"""
    period = fields.Str(missing='week', validate=lambda x: x in ['week', 'month', 'all'])
    tier = fields.Str(missing='all', validate=lambda x: x in ['pro', 'immortal', 'divine', 'all'])
    patch = fields.Str()

@stats_bp.route('/heroes', methods=['GET'])
@limiter.limit("30 per minute")
@cache.cached(timeout=900, key_prefix='hero_stats')
def get_hero_stats():
    """获取英雄统计数据"""
    schema = HeroStatsFilterSchema()
    
    try:
        filters = schema.load(request.args)
    except ValidationError as err:
        return ApiResponse.error('参数验证失败', 'VALIDATION_ERROR', 400, err.messages)
    
    try:
        # 构建查询
        query = HeroStats.query.join(Hero)
        
        # 时间周期筛选
        period = filters.get('period', 'week')
        if period == 'week':
            query = query.filter(HeroStats.period_type == HeroStats.Period.WEEK)
        elif period == 'month':
            query = query.filter(HeroStats.period_type == HeroStats.Period.MONTH)
        else:
            query = query.filter(HeroStats.period_type == HeroStats.Period.ALL)
        
        # 段位筛选
        tier = filters.get('tier', 'all')
        if tier != 'all':
            query = query.filter(HeroStats.tier_filter == HeroStats.Tier(tier.upper()))
        
        # 版本筛选
        if filters.get('patch'):
            query = query.filter(HeroStats.patch_version == filters['patch'])
        
        # 排序：按胜率降序
        query = query.order_by(desc(HeroStats.win_rate))
        
        hero_stats = query.all()
        
        return ApiResponse.success({
            'heroes': [stat.to_dict() for stat in hero_stats],
            'lastUpdated': hero_stats[0].calculated_at.isoformat() if hero_stats else None,
            'filters': filters
        })
        
    except Exception as e:
        current_app.logger.error(f"获取英雄统计失败: {e}")
        return ApiResponse.error('获取英雄统计失败', 'GET_HERO_STATS_FAILED', 500)

@stats_bp.route('/teams', methods=['GET'])
@limiter.limit("30 per minute")
@cache.cached(timeout=900, key_prefix='team_stats')
def get_team_stats():
    """获取战队统计数据"""
    try:
        # 计算战队统计
        team_stats = db.session.query(
            Team.id,
            Team.name,
            Team.tag,
            Team.logo_url,
            Team.region,
            func.count(Match.id).label('total_matches'),
            func.sum(
                func.case(
                    (and_(Match.radiant_team_id == Team.id, Match.radiant_win == True), 1),
                    (and_(Match.dire_team_id == Team.id, Match.radiant_win == False), 1),
                    else_=0
                )
            ).label('wins'),
            func.sum(
                func.case(
                    (and_(Match.radiant_team_id == Team.id, Match.radiant_win == False), 1),
                    (and_(Match.dire_team_id == Team.id, Match.radiant_win == True), 1),
                    else_=0
                )
            ).label('losses')
        ).outerjoin(
            Match, 
            db.or_(
                Match.radiant_team_id == Team.id,
                Match.dire_team_id == Team.id
            )
        ).filter(
            Match.status == MatchStatus.FINISHED
        ).group_by(Team.id).all()
        
        # 计算胜率和排名
        teams_data = []
        for stat in team_stats:
            total_matches = stat.total_matches or 0
            wins = stat.wins or 0
            losses = stat.losses or 0
            win_rate = (wins / total_matches * 100) if total_matches > 0 else 0
            points = wins * 3 + losses * 1  # 简单的积分系统
            
            teams_data.append({
                'id': stat.id,
                'name': stat.name,
                'tag': stat.tag,
                'logo': stat.logo_url,
                'region': stat.region,
                'stats': {
                    'wins': wins,
                    'losses': losses,
                    'totalMatches': total_matches,
                    'winRate': round(win_rate, 2),
                    'points': points
                }
            })
        
        # 按积分排序
        teams_data.sort(key=lambda x: x['stats']['points'], reverse=True)
        
        # 添加排名
        for i, team in enumerate(teams_data):
            team['ranking'] = i + 1
            # 简单的趋势计算（实际应该基于最近比赛）
            team['trend'] = 'stable'  # TODO: 实现真实的趋势计算
        
        return ApiResponse.success({
            'teams': teams_data[:20],  # 返回前20名
            'lastUpdated': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"获取战队统计失败: {e}")
        return ApiResponse.error('获取战队统计失败', 'GET_TEAM_STATS_FAILED', 500)

@stats_bp.route('/trends', methods=['GET'])
@limiter.limit("30 per minute")
@cache.cached(timeout=1800, key_prefix='meta_trends')
def get_meta_trends():
    """获取Meta趋势分析"""
    try:
        # 获取最近两个版本的英雄胜率变化
        current_patch = "7.37c"  # TODO: 从配置或数据库获取当前版本
        previous_patch = "7.37b"
        
        current_stats = HeroStats.query.filter_by(
            patch_version=current_patch,
            period_type=HeroStats.Period.PATCH,
            tier_filter=HeroStats.Tier.PRO
        ).all()
        
        previous_stats = HeroStats.query.filter_by(
            patch_version=previous_patch,
            period_type=HeroStats.Period.PATCH,
            tier_filter=HeroStats.Tier.PRO
        ).all()
        
        # 创建英雄变化字典
        current_dict = {stat.hero_id: stat for stat in current_stats}
        previous_dict = {stat.hero_id: stat for stat in previous_stats}
        
        hero_changes = []
        for hero_id, current_stat in current_dict.items():
            previous_stat = previous_dict.get(hero_id)
            if previous_stat:
                win_rate_change = float(current_stat.win_rate) - float(previous_stat.win_rate)
                pick_rate_change = float(current_stat.pick_rate) - float(previous_stat.pick_rate)
                
                if abs(win_rate_change) > 2 or abs(pick_rate_change) > 3:  # 显著变化
                    hero_changes.append({
                        'hero': current_stat.hero.to_dict(),
                        'winRateChange': round(win_rate_change, 2),
                        'pickRateChange': round(pick_rate_change, 2),
                        'currentWinRate': float(current_stat.win_rate),
                        'currentPickRate': float(current_stat.pick_rate),
                        'type': 'buff' if win_rate_change > 0 else 'nerf'
                    })
        
        # 按变化幅度排序
        hero_changes.sort(key=lambda x: abs(x['winRateChange']), reverse=True)
        
        # Meta趋势分析
        meta_analysis = {
            'strongStrategies': [
                '推进流阵容胜率上升',
                '团控英雄受到重视', 
                '早期节奏型打法流行'
            ],
            'weakStrategies': [
                '后期carry流胜率下降',
                '分推战术效果减弱',
                '纯输出阵容不再流行'
            ],
            'emergingPicks': [
                hero['hero']['displayName'] for hero in hero_changes[:5] 
                if hero['type'] == 'buff'
            ],
            'decliningPicks': [
                hero['hero']['displayName'] for hero in hero_changes[:5]
                if hero['type'] == 'nerf'
            ]
        }
        
        return ApiResponse.success({
            'currentPatch': current_patch,
            'heroChanges': hero_changes[:20],
            'metaAnalysis': meta_analysis,
            'lastUpdated': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"获取Meta趋势失败: {e}")
        return ApiResponse.error('获取趋势分析失败', 'GET_TRENDS_FAILED', 500)

@stats_bp.route('/predictions', methods=['GET'])
@limiter.limit("30 per minute")
@cache.cached(timeout=900, key_prefix='prediction_stats')
def get_prediction_stats():
    """获取预测统计数据"""
    try:
        from models.match import ExpertPrediction
        
        # 总预测统计
        total_predictions = ExpertPrediction.query.count()
        
        # 已解析的预测
        resolved_predictions = ExpertPrediction.query.filter(
            ExpertPrediction.result.in_(['correct', 'incorrect'])
        ).count()
        
        # 正确预测
        correct_predictions = ExpertPrediction.query.filter_by(
            result='correct'
        ).count()
        
        # 计算总体准确率
        overall_accuracy = (correct_predictions / resolved_predictions * 100) if resolved_predictions > 0 else 0
        
        # 专家参与统计
        expert_count = db.session.query(
            func.count(func.distinct(ExpertPrediction.expert_id))
        ).scalar()
        
        # 最近7天的预测数量
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_predictions = ExpertPrediction.query.filter(
            ExpertPrediction.created_at >= seven_days_ago
        ).count()
        
        # 本月新增预测
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_predictions = ExpertPrediction.query.filter(
            ExpertPrediction.created_at >= month_start
        ).count()
        
        # 专家准确率排行
        expert_ranking = db.session.query(
            User.id,
            User.username,
            User.avatar_url,
            User.tier,
            func.count(ExpertPrediction.id).label('total_predictions'),
            func.round(
                func.avg(
                    func.case(
                        (ExpertPrediction.result == 'correct', 100.0),
                        (ExpertPrediction.result == 'incorrect', 0.0),
                        else_=None
                    )
                ), 2
            ).label('accuracy')
        ).join(ExpertPrediction).filter(
            User.role.in_([UserRole.EXPERT, UserRole.ADMIN])
        ).group_by(User.id).having(
            func.count(ExpertPrediction.id) >= 5
        ).order_by(desc('accuracy')).limit(10).all()
        
        return ApiResponse.success({
            'totalPredictions': total_predictions,
            'resolvedPredictions': resolved_predictions,
            'correctPredictions': correct_predictions,
            'overallAccuracy': round(overall_accuracy, 2),
            'expertCount': expert_count,
            'recentPredictions': recent_predictions,
            'monthlyPredictions': monthly_predictions,
            'expertRanking': [
                {
                    'id': row.id,
                    'username': row.username,
                    'avatar': row.avatar_url,
                    'tier': row.tier.value if row.tier else 'bronze',
                    'totalPredictions': row.total_predictions,
                    'accuracy': float(row.accuracy) if row.accuracy else 0
                }
                for row in expert_ranking
            ]
        })
        
    except Exception as e:
        current_app.logger.error(f"获取预测统计失败: {e}")
        return ApiResponse.error('获取预测统计失败', 'GET_PREDICTION_STATS_FAILED', 500)

@stats_bp.route('/general', methods=['GET'])
@limiter.limit("30 per minute")
@cache.cached(timeout=600, key_prefix='general_stats')
def get_general_stats():
    """获取平台总体统计"""
    try:
        # 用户统计
        total_users = User.query.count()
        expert_users = User.query.filter(User.role.in_([UserRole.EXPERT, UserRole.ADMIN])).count()
        
        # 内容统计
        total_discussions = Discussion.query.count()
        total_articles = Article.query.filter_by(status='published').count()
        
        # 比赛统计
        total_matches = Match.query.count()
        analyzed_matches = Match.query.filter(Match.analysis_count > 0).count()
        
        # 活跃度统计（最近7天）
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        active_users = db.session.query(
            func.count(func.distinct(Discussion.author_id))
        ).filter(Discussion.created_at >= seven_days_ago).scalar()
        
        new_discussions = Discussion.query.filter(
            Discussion.created_at >= seven_days_ago
        ).count()
        
        # 今日统计
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        today_discussions = Discussion.query.filter(
            Discussion.created_at >= today_start
        ).count()
        
        today_articles = Article.query.filter(
            Article.created_at >= today_start,
            Article.status == 'published'
        ).count()
        
        return ApiResponse.success({
            'users': {
                'total': total_users,
                'experts': expert_users,
                'activeWeekly': active_users
            },
            'content': {
                'totalDiscussions': total_discussions,
                'totalArticles': total_articles,
                'weeklyDiscussions': new_discussions,
                'todayDiscussions': today_discussions,
                'todayArticles': today_articles
            },
            'matches': {
                'total': total_matches,
                'analyzed': analyzed_matches,
                'analysisRate': round((analyzed_matches / total_matches * 100) if total_matches > 0 else 0, 2)
            },
            'lastUpdated': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"获取总体统计失败: {e}")
        return ApiResponse.error('获取统计数据失败', 'GET_GENERAL_STATS_FAILED', 500)

@stats_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """获取仪表板统计（管理员）"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.role != UserRole.ADMIN:
            return ApiResponse.error('权限不足', 'PERMISSION_DENIED', 403)
        
        # 获取各种管理统计数据
        from models.user import ExpertApplication
        
        # 待处理的专家申请
        pending_applications = ExpertApplication.query.filter_by(
            status=ExpertApplication.Status.PENDING
        ).count()
        
        # 最近24小时的活动
        yesterday = datetime.utcnow() - timedelta(hours=24)
        
        recent_registrations = User.query.filter(User.created_at >= yesterday).count()
        recent_discussions = Discussion.query.filter(Discussion.created_at >= yesterday).count()
        recent_articles = Article.query.filter(
            Article.created_at >= yesterday,
            Article.status == 'published'
        ).count()
        
        # 系统性能指标
        from utils.monitoring import get_system_metrics
        system_metrics = get_system_metrics()
        
        return ApiResponse.success({
            'pendingApplications': pending_applications,
            'recentActivity': {
                'registrations': recent_registrations,
                'discussions': recent_discussions,
                'articles': recent_articles
            },
            'systemMetrics': system_metrics,
            'lastUpdated': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"获取仪表板统计失败: {e}")
        return ApiResponse.error('获取仪表板数据失败', 'GET_DASHBOARD_FAILED', 500)

@stats_bp.route('/export', methods=['GET'])
@jwt_required()
def export_stats():
    """导出统计数据（管理员）"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.role != UserRole.ADMIN:
            return ApiResponse.error('权限不足', 'PERMISSION_DENIED', 403)
        
        export_type = request.args.get('type', 'general')
        
        if export_type == 'users':
            # 导出用户统计
            data = export_user_stats()
        elif export_type == 'matches':
            # 导出比赛统计
            data = export_match_stats()
        elif export_type == 'content':
            # 导出内容统计
            data = export_content_stats()
        else:
            # 导出综合统计
            data = export_general_stats()
        
        return ApiResponse.success({
            'exportType': export_type,
            'data': data,
            'exportedAt': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"导出统计数据失败: {e}")
        return ApiResponse.error('导出数据失败', 'EXPORT_FAILED', 500)

def export_user_stats():
    """导出用户统计数据"""
    return {
        'totalUsers': User.query.count(),
        'usersByRole': dict(
            db.session.query(User.role, func.count(User.id)).group_by(User.role).all()
        ),
        'usersByTier': dict(
            db.session.query(User.tier, func.count(User.id)).group_by(User.tier).all()
        ),
        'verifiedUsers': User.query.filter_by(verified=True).count()
    }

def export_match_stats():
    """导出比赛统计数据"""
    return {
        'totalMatches': Match.query.count(),
        'matchesByStatus': dict(
            db.session.query(Match.status, func.count(Match.id)).group_by(Match.status).all()
        ),
        'matchesByLeague': dict(
            db.session.query(Match.league_id, func.count(Match.id)).group_by(Match.league_id).all()
        )
    }

def export_content_stats():
    """导出内容统计数据"""
    return {
        'totalDiscussions': Discussion.query.count(),
        'discussionsByCategory': dict(
            db.session.query(Discussion.category, func.count(Discussion.id)).group_by(Discussion.category).all()
        ),
        'totalArticles': Article.query.count(),
        'articlesByCategory': dict(
            db.session.query(Article.category, func.count(Article.id)).group_by(Article.category).all()
        )
    }

def export_general_stats():
    """导出综合统计数据"""
    return {
        'users': export_user_stats(),
        'matches': export_match_stats(),
        'content': export_content_stats()
    }
