"""
统计数据API路由 - 完整版
基于Dota 2数据分析图表推荐文档实现
支持多维度数据分析和可视化数据API
"""

from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError
from datetime import datetime, timedelta

from utils.response import ApiResponse
from utils.decorators import limiter, cache
from services.statistics_service import StatisticsService

stats_bp = Blueprint('stats', __name__)

# 初始化统计服务
stats_service = StatisticsService()

class TimeRangeSchema(Schema):
    """时间范围参数验证"""
    time_range = fields.Int(load_default=30, validate=lambda x: 1 <= x <= 365)
    patch_version = fields.Str()
    tier_filter = fields.Str(load_default='all', validate=lambda x: x in [
        'herald', 'guardian', 'crusader', 'archon', 'legend',
        'ancient', 'divine', 'immortal', 'pro', 'all'
    ])

class HeroAnalysisSchema(Schema):
    """英雄分析参数验证"""
    hero_id = fields.Int()
    limit = fields.Int(load_default=20, validate=lambda x: 1 <= x <= 100)
    time_range = fields.Int(load_default=30, validate=lambda x: 1 <= x <= 365)

class PlayerAnalysisSchema(Schema):
    """选手分析参数验证"""
    player_ids = fields.List(fields.Int())
    position = fields.Str(validate=lambda x: x in ['1', '2', '3', '4', '5', 'all'])

# ========== 1. 英雄Meta分析 API ==========

@stats_bp.route('/hero/winrate-ranking', methods=['GET'])
@limiter.limit("20 per minute")
@cache.cached(timeout=1800, key_prefix='hero_winrate_ranking')
def get_hero_winrate_ranking():
    """
    英雄胜率排行榜API
    支持按段位分层显示
    """
    schema = TimeRangeSchema()
    
    try:
        filters = schema.load(request.args)
    except ValidationError as err:
        return ApiResponse.error('参数验证失败', 'VALIDATION_ERROR', 400, err.messages)
    
    try:
        result = stats_service.get_hero_winrate_ranking(
            tier_filter=filters.get('tier_filter', 'all'),
            patch_version=filters.get('patch_version'),
            time_range=filters.get('time_range', 30)
        )
        
        if 'error' in result:
            return ApiResponse.error('获取英雄胜率排行榜失败', 'STATS_ERROR', 500, result['error'])
        
        return ApiResponse.success(result)
        
    except Exception as e:
        current_app.logger.error(f"英雄胜率排行榜API失败: {e}")
        return ApiResponse.error('服务器内部错误', 'INTERNAL_ERROR', 500)

@stats_bp.route('/hero/pickrate-heatmap', methods=['GET'])
@limiter.limit("10 per minute")
@cache.cached(timeout=3600, key_prefix='hero_pickrate_heatmap')
def get_hero_pickrate_heatmap():
    """
    英雄选取率热力图API
    时间序列展示meta变化
    """
    days = request.args.get('days', 30, type=int)
    
    if not (1 <= days <= 90):
        return ApiResponse.error('时间范围必须在1-90天之间', 'INVALID_RANGE', 400)
    
    try:
        result = stats_service.get_hero_pickrate_heatmap(days=days)
        
        if 'error' in result:
            return ApiResponse.error('生成英雄选取率热力图失败', 'STATS_ERROR', 500, result['error'])
        
        return ApiResponse.success(result)
        
    except Exception as e:
        current_app.logger.error(f"英雄选取率热力图API失败: {e}")
        return ApiResponse.error('服务器内部错误', 'INTERNAL_ERROR', 500)

@stats_bp.route('/hero/role-distribution', methods=['GET'])
@limiter.limit("30 per minute")
@cache.cached(timeout=1800, key_prefix='hero_role_distribution')
def get_hero_role_distribution():
    """
    英雄角色分布饼图API
    显示核心/辅助/工具人占比
    """
    time_range = request.args.get('time_range', 30, type=int)
    
    if not (1 <= time_range <= 365):
        return ApiResponse.error('时间范围必须在1-365天之间', 'INVALID_RANGE', 400)
    
    try:
        result = stats_service.get_hero_role_distribution(time_range=time_range)
        
        if 'error' in result:
            return ApiResponse.error('获取英雄角色分布失败', 'STATS_ERROR', 500, result['error'])
        
        return ApiResponse.success(result)
        
    except Exception as e:
        current_app.logger.error(f"英雄角色分布API失败: {e}")
        return ApiResponse.error('服务器内部错误', 'INTERNAL_ERROR', 500)

@stats_bp.route('/hero/counter-network', methods=['GET'])
@limiter.limit("5 per minute")  # 复杂计算，限制更严格
@cache.cached(timeout=7200, key_prefix='hero_counter_network')
def get_hero_counter_network():
    """
    英雄克制关系网络图API
    基于对战数据生成克制关系
    """
    schema = HeroAnalysisSchema()
    
    try:
        filters = schema.load(request.args)
    except ValidationError as err:
        return ApiResponse.error('参数验证失败', 'VALIDATION_ERROR', 400, err.messages)
    
    try:
        result = stats_service.get_hero_counter_network(
            hero_id=filters.get('hero_id'),
            limit=filters.get('limit', 50)
        )
        
        if 'error' in result:
            return ApiResponse.error('生成英雄克制关系网络失败', 'STATS_ERROR', 500, result['error'])
        
        return ApiResponse.success(result)
        
    except Exception as e:
        current_app.logger.error(f"英雄克制关系网络API失败: {e}")
        return ApiResponse.error('服务器内部错误', 'INTERNAL_ERROR', 500)

# ========== 2. 物品经济分析 API ==========

@stats_bp.route('/item/purchase-trends', methods=['GET'])
@limiter.limit("20 per minute")
@cache.cached(timeout=3600, key_prefix='item_purchase_trends')
def get_item_purchase_trends():
    """
    物品购买趋势API
    显示不同时期物品流行度变化
    """
    time_range = request.args.get('time_range', 90, type=int)
    
    if not (7 <= time_range <= 365):
        return ApiResponse.error('时间范围必须在7-365天之间', 'INVALID_RANGE', 400)
    
    try:
        result = stats_service.get_item_purchase_trends(time_range=time_range)
        
        if 'error' in result:
            return ApiResponse.error('获取物品购买趋势失败', 'STATS_ERROR', 500, result['error'])
        
        return ApiResponse.success(result)
        
    except Exception as e:
        current_app.logger.error(f"物品购买趋势API失败: {e}")
        return ApiResponse.error('服务器内部错误', 'INTERNAL_ERROR', 500)

# ========== 3. 比赛数据概览 API ==========

@stats_bp.route('/match/duration-distribution', methods=['GET'])
@limiter.limit("30 per minute")
@cache.cached(timeout=1800, key_prefix='match_duration_distribution')
def get_match_duration_distribution():
    """
    比赛时长分布直方图API
    展示游戏节奏变化
    """
    time_range = request.args.get('time_range', 30, type=int)
    
    if not (1 <= time_range <= 365):
        return ApiResponse.error('时间范围必须在1-365天之间', 'INVALID_RANGE', 400)
    
    try:
        result = stats_service.get_match_duration_distribution(time_range=time_range)
        
        if 'error' in result:
            return ApiResponse.error('获取比赛时长分布失败', 'STATS_ERROR', 500, result['error'])
        
        return ApiResponse.success(result)
        
    except Exception as e:
        current_app.logger.error(f"比赛时长分布API失败: {e}")
        return ApiResponse.error('服务器内部错误', 'INTERNAL_ERROR', 500)

@stats_bp.route('/match/first-blood-timing', methods=['GET'])
@limiter.limit("30 per minute")
@cache.cached(timeout=1800, key_prefix='first_blood_timing')
def get_first_blood_timing_trend():
    """
    首杀时间趋势API
    显示游戏pace变化
    """
    time_range = request.args.get('time_range', 30, type=int)
    
    if not (1 <= time_range <= 365):
        return ApiResponse.error('时间范围必须在1-365天之间', 'INVALID_RANGE', 400)
    
    try:
        result = stats_service.get_first_blood_timing_trend(time_range=time_range)
        
        if 'error' in result:
            return ApiResponse.error('获取首杀时间趋势失败', 'STATS_ERROR', 500, result['error'])
        
        return ApiResponse.success(result)
        
    except Exception as e:
        current_app.logger.error(f"首杀时间趋势API失败: {e}")
        return ApiResponse.error('服务器内部错误', 'INTERNAL_ERROR', 500)

@stats_bp.route('/match/economy-winrate', methods=['GET'])
@limiter.limit("20 per minute")
@cache.cached(timeout=1800, key_prefix='economy_winrate')
def get_economy_advantage_winrate():
    """
    经济领先胜率曲线API
    显示经济优势与胜率关系
    """
    time_range = request.args.get('time_range', 30, type=int)
    
    if not (1 <= time_range <= 365):
        return ApiResponse.error('时间范围必须在1-365天之间', 'INVALID_RANGE', 400)
    
    try:
        result = stats_service.get_economy_advantage_winrate(time_range=time_range)
        
        if 'error' in result:
            return ApiResponse.error('获取经济优势胜率关系失败', 'STATS_ERROR', 500, result['error'])
        
        return ApiResponse.success(result)
        
    except Exception as e:
        current_app.logger.error(f"经济优势胜率API失败: {e}")
        return ApiResponse.error('服务器内部错误', 'INTERNAL_ERROR', 500)

# ========== 4. 选手表现分析 API ==========

@stats_bp.route('/player/kda-distribution', methods=['GET'])
@limiter.limit("20 per minute")
@cache.cached(timeout=1800, key_prefix='player_kda_distribution')
def get_player_kda_distribution():
    """
    选手KDA分布箱线图API
    不同位置选手表现对比
    """
    schema = PlayerAnalysisSchema()
    
    try:
        filters = schema.load(request.args)
    except ValidationError as err:
        return ApiResponse.error('参数验证失败', 'VALIDATION_ERROR', 400, err.messages)
    
    try:
        result = stats_service.get_player_kda_distribution(
            position=filters.get('position')
        )
        
        if 'error' in result:
            return ApiResponse.error('获取选手KDA分布失败', 'STATS_ERROR', 500, result['error'])
        
        return ApiResponse.success(result)
        
    except Exception as e:
        current_app.logger.error(f"选手KDA分布API失败: {e}")
        return ApiResponse.error('服务器内部错误', 'INTERNAL_ERROR', 500)

@stats_bp.route('/player/farm-efficiency', methods=['GET'])
@limiter.limit("20 per minute")
@cache.cached(timeout=1800, key_prefix='farm_efficiency')
def get_farm_efficiency_comparison():
    """
    Farm效率对比雷达图API
    比较补刀/分钟等指标
    """
    schema = PlayerAnalysisSchema()
    
    try:
        filters = schema.load(request.args)
    except ValidationError as err:
        return ApiResponse.error('参数验证失败', 'VALIDATION_ERROR', 400, err.messages)
    
    try:
        result = stats_service.get_farm_efficiency_comparison(
            player_ids=filters.get('player_ids')
        )
        
        if 'error' in result:
            return ApiResponse.error('获取Farm效率对比失败', 'STATS_ERROR', 500, result['error'])
        
        return ApiResponse.success(result)
        
    except Exception as e:
        current_app.logger.error(f"Farm效率对比API失败: {e}")
        return ApiResponse.error('服务器内部错误', 'INTERNAL_ERROR', 500)

# ========== 5. 综合分析 API ==========

@stats_bp.route('/dashboard', methods=['GET'])
@limiter.limit("10 per minute")
@cache.cached(timeout=900, key_prefix='comprehensive_dashboard')
def get_comprehensive_dashboard():
    """
    综合仪表盘API
    包含多个核心统计指标
    """
    time_range = request.args.get('time_range', 7, type=int)
    
    if not (1 <= time_range <= 90):
        return ApiResponse.error('时间范围必须在1-90天之间', 'INVALID_RANGE', 400)
    
    try:
        result = stats_service.get_comprehensive_dashboard_data(time_range=time_range)
        
        if 'error' in result:
            return ApiResponse.error('生成综合仪表盘失败', 'STATS_ERROR', 500, result['error'])
        
        return ApiResponse.success(result)
        
    except Exception as e:
        current_app.logger.error(f"综合仪表盘API失败: {e}")
        return ApiResponse.error('服务器内部错误', 'INTERNAL_ERROR', 500)

@stats_bp.route('/summary', methods=['GET'])
@limiter.limit("30 per minute")
@cache.cached(timeout=3600, key_prefix='stats_summary')
def get_statistics_summary():
    """
    统计分析摘要API
    返回平台统计能力和数据概览
    """
    try:
        result = stats_service.get_advanced_statistics_summary()
        
        if 'error' in result:
            return ApiResponse.error('获取统计摘要失败', 'STATS_ERROR', 500, result['error'])
        
        return ApiResponse.success(result)
        
    except Exception as e:
        current_app.logger.error(f"统计摘要API失败: {e}")
        return ApiResponse.error('服务器内部错误', 'INTERNAL_ERROR', 500)

# ========== 6. 数据导出 API ==========

@stats_bp.route('/export/<chart_type>', methods=['GET'])
@jwt_required()
@limiter.limit("5 per minute")
def export_chart_data(chart_type):
    """
    导出图表数据API
    支持导出各种统计图表的原始数据
    """
    user_id = get_jwt_identity()
    
    if not user_id:
        return ApiResponse.error('需要登录', 'AUTH_REQUIRED', 401)
    
    # 支持的图表类型
    supported_charts = [
        'hero-winrate', 'hero-pickrate', 'hero-roles', 
        'match-duration', 'economy-winrate', 'player-kda'
    ]
    
    if chart_type not in supported_charts:
        return ApiResponse.error(
            f'不支持的图表类型: {chart_type}', 
            'UNSUPPORTED_CHART', 
            400,
            {'supported_types': supported_charts}
        )
    
    try:
        # 根据图表类型调用相应的统计方法
        if chart_type == 'hero-winrate':
            result = stats_service.get_hero_winrate_ranking()
        elif chart_type == 'hero-pickrate':
            result = stats_service.get_hero_pickrate_heatmap()
        elif chart_type == 'hero-roles':
            result = stats_service.get_hero_role_distribution()
        elif chart_type == 'match-duration':
            result = stats_service.get_match_duration_distribution()
        elif chart_type == 'economy-winrate':
            result = stats_service.get_economy_advantage_winrate()
        elif chart_type == 'player-kda':
            result = stats_service.get_player_kda_distribution()
        else:
            return ApiResponse.error('图表类型处理错误', 'CHART_ERROR', 500)
        
        if 'error' in result:
            return ApiResponse.error('导出数据失败', 'EXPORT_ERROR', 500, result['error'])
        
        # 添加导出元数据
        export_data = {
            'chart_type': chart_type,
            'exported_by': user_id,
            'exported_at': datetime.utcnow().isoformat(),
            'data': result
        }
        
        return ApiResponse.success(export_data, '数据导出成功')
        
    except Exception as e:
        current_app.logger.error(f"导出图表数据失败 {chart_type}: {e}")
        return ApiResponse.error('导出失败', 'EXPORT_ERROR', 500)

# ========== 7. 健康检查和状态 API ==========

@stats_bp.route('/health', methods=['GET'])
@limiter.limit("60 per minute")
def stats_health_check():
    """
    统计服务健康检查API
    """
    try:
        # 简单的数据库连接测试
        from models.match import Match
        recent_matches = Match.query.limit(1).first()
        
        health_status = {
            'service': 'statistics',
            'status': 'healthy',
            'database': 'connected' if recent_matches else 'no_data',
            'features': {
                'hero_analysis': True,
                'match_analysis': True,
                'player_analysis': True,
                'export_function': True
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return ApiResponse.success(health_status)
        
    except Exception as e:
        current_app.logger.error(f"统计服务健康检查失败: {e}")
        return ApiResponse.error('服务不可用', 'SERVICE_UNAVAILABLE', 503)

# 错误处理
@stats_bp.errorhandler(429)
def ratelimit_handler(e):
    return ApiResponse.error('请求过于频繁，请稍后再试', 'RATE_LIMIT_EXCEEDED', 429)

@stats_bp.errorhandler(500)
def internal_error_handler(e):
    current_app.logger.error(f"统计API内部错误: {e}")
    return ApiResponse.error('统计服务内部错误', 'STATS_INTERNAL_ERROR', 500)
