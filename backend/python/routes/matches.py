"""
比赛相关API路由
"""

from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError
from sqlalchemy import or_, and_, desc, asc
from datetime import datetime, timedelta

from ..config.database import db
from ..models.match import Match, MatchStatus, League, Team, MatchPlayer, MatchAnalysis, ExpertPrediction
from ..models.content import ContentView, ContentType
from ..models.user import User, UserRole
from ..utils.response import ApiResponse
from ..utils.decorators import limiter, cache
from ..utils.pagination import paginate

matches_bp = Blueprint('matches', __name__)

class MatchFilterSchema(Schema):
    """比赛筛选参数验证"""
    page = fields.Int(missing=1, validate=lambda x: x > 0)
    page_size = fields.Int(missing=20, validate=lambda x: 1 <= x <= 100)
    status = fields.Str(validate=lambda x: x in ['live', 'upcoming', 'finished'])
    league = fields.Str()
    team = fields.Str()
    date_from = fields.Date()
    date_to = fields.Date()
    sort = fields.Str(missing='time_desc', validate=lambda x: x in ['time_desc', 'time_asc', 'views_desc'])

@matches_bp.route('', methods=['GET'])
@limiter.limit("30 per minute")
@cache.cached(timeout=300, key_prefix='matches_list')
def get_matches():
    """获取比赛列表"""
    schema = MatchFilterSchema()
    
    try:
        filters = schema.load(request.args)
    except ValidationError as err:
        return ApiResponse.error('参数验证失败', 'VALIDATION_ERROR', 400, err.messages)
    
    try:
        # 构建查询
        query = Match.query
        
        # 状态筛选
        if filters.get('status'):
            query = query.filter(Match.status == MatchStatus(filters['status']))
        
        # 联赛筛选
        if filters.get('league'):
            query = query.join(League).filter(
                League.name.ilike(f"%{filters['league']}%")
            )
        
        # 队伍筛选
        if filters.get('team'):
            query = query.join(Team, or_(
                Match.radiant_team_id == Team.id,
                Match.dire_team_id == Team.id
            )).filter(
                Team.name.ilike(f"%{filters['team']}%")
            )
        
        # 日期筛选
        if filters.get('date_from'):
            query = query.filter(Match.start_time >= filters['date_from'])
        
        if filters.get('date_to'):
            query = query.filter(Match.start_time <= filters['date_to'])
        
        # 排序
        sort_option = filters.get('sort', 'time_desc')
        if sort_option == 'time_desc':
            query = query.order_by(desc(Match.start_time))
        elif sort_option == 'time_asc':
            query = query.order_by(asc(Match.start_time))
        elif sort_option == 'views_desc':
            query = query.order_by(desc(Match.view_count))
        
        # 分页
        page = filters.get('page', 1)
        page_size = filters.get('page_size', 20)
        
        paginated_matches = paginate(query, page, page_size)
        
        return ApiResponse.success({
            'matches': [match.to_dict() for match in paginated_matches.items],
            'pagination': {
                'page': paginated_matches.page,
                'pageSize': page_size,
                'total': paginated_matches.total,
                'totalPages': paginated_matches.pages,
                'hasNext': paginated_matches.has_next,
                'hasPrev': paginated_matches.has_prev
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"获取比赛列表失败: {e}")
        return ApiResponse.error('获取比赛列表失败', 'GET_MATCHES_FAILED', 500)

@matches_bp.route('/<string:match_id>', methods=['GET'])
@limiter.limit("60 per minute")
def get_match_detail(match_id):
    """获取比赛详情"""
    try:
        match = Match.query.filter_by(match_id=match_id).first()
        
        if not match:
            return ApiResponse.error('比赛不存在', 'MATCH_NOT_FOUND', 404)
        
        # 记录浏览
        user_id = None
        try:
            from flask_jwt_extended import get_jwt_identity
            user_id = get_jwt_identity()
        except:
            pass
        
        ContentView.record_view(
            ContentType.MATCH,
            match.id,
            user_id=user_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        # 根据比赛状态设置缓存时间
        cache_timeout = 60 if match.status == MatchStatus.LIVE else 1800
        
        return ApiResponse.success({
            'match': match.to_dict(include_details=True)
        })
        
    except Exception as e:
        current_app.logger.error(f"获取比赛详情失败: {e}")
        return ApiResponse.error('获取比赛详情失败', 'GET_MATCH_DETAIL_FAILED', 500)

@matches_bp.route('/live', methods=['GET'])
@limiter.limit("60 per minute")
@cache.cached(timeout=30, key_prefix='live_matches')
def get_live_matches():
    """获取正在进行的比赛"""
    try:
        live_matches = Match.query.filter_by(status=MatchStatus.LIVE).order_by(
            desc(Match.start_time)
        ).all()
        
        return ApiResponse.success({
            'matches': [match.to_dict() for match in live_matches],
            'count': len(live_matches)
        })
        
    except Exception as e:
        current_app.logger.error(f"获取直播比赛失败: {e}")
        return ApiResponse.error('获取直播比赛失败', 'GET_LIVE_MATCHES_FAILED', 500)

@matches_bp.route('/<string:match_id>/stats', methods=['GET'])
@limiter.limit("30 per minute")
@cache.cached(timeout=600, key_prefix='match_stats')
def get_match_stats(match_id):
    """获取比赛统计数据"""
    try:
        match = Match.query.filter_by(match_id=match_id).first()
        
        if not match:
            return ApiResponse.error('比赛不存在', 'MATCH_NOT_FOUND', 404)
        
        # 获取选手数据
        players = MatchPlayer.query.filter_by(match_id=match.id).all()
        
        # 计算团队统计
        radiant_players = [p for p in players if p.team_side.value == 'radiant']
        dire_players = [p for p in players if p.team_side.value == 'dire']
        
        def calculate_team_stats(team_players):
            if not team_players:
                return {}
            
            return {
                'totalKills': sum(p.kills for p in team_players),
                'totalDeaths': sum(p.deaths for p in team_players),
                'totalAssists': sum(p.assists for p in team_players),
                'totalNetWorth': sum(p.net_worth for p in team_players),
                'avgGPM': sum(p.gpm for p in team_players) // len(team_players),
                'avgXPM': sum(p.xpm for p in team_players) // len(team_players),
                'totalHeroDamage': sum(p.hero_damage for p in team_players),
                'totalTowerDamage': sum(p.tower_damage for p in team_players)
            }
        
        return ApiResponse.success({
            'matchId': match_id,
            'duration': match.duration,
            'radiantStats': calculate_team_stats(radiant_players),
            'direStats': calculate_team_stats(dire_players),
            'players': {
                'radiant': [p.to_dict() for p in radiant_players],
                'dire': [p.to_dict() for p in dire_players]
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"获取比赛统计失败: {e}")
        return ApiResponse.error('获取比赛统计失败', 'GET_MATCH_STATS_FAILED', 500)

@matches_bp.route('/<string:match_id>/predictions', methods=['GET'])
@limiter.limit("30 per minute")
def get_match_predictions(match_id):
    """获取比赛预测"""
    try:
        match = Match.query.filter_by(match_id=match_id).first()
        
        if not match:
            return ApiResponse.error('比赛不存在', 'MATCH_NOT_FOUND', 404)
        
        predictions = ExpertPrediction.query.filter_by(match_id=match.id).all()
        
        return ApiResponse.success({
            'predictions': [pred.to_dict() for pred in predictions],
            'count': len(predictions)
        })
        
    except Exception as e:
        current_app.logger.error(f"获取比赛预测失败: {e}")
        return ApiResponse.error('获取比赛预测失败', 'GET_PREDICTIONS_FAILED', 500)

@matches_bp.route('/<string:match_id>/predict', methods=['POST'])
@jwt_required()
@limiter.limit("5 per minute")
def create_prediction(match_id):
    """创建比赛预测"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return ApiResponse.error('用户不存在', 'USER_NOT_FOUND', 404)
        
        # 检查是否为专家
        if user.role not in [UserRole.EXPERT, UserRole.ADMIN]:
            return ApiResponse.error('只有专家可以发布预测', 'PERMISSION_DENIED', 403)
        
        match = Match.query.filter_by(match_id=match_id).first()
        
        if not match:
            return ApiResponse.error('比赛不存在', 'MATCH_NOT_FOUND', 404)
        
        # 检查比赛是否还可以预测
        if match.status != MatchStatus.UPCOMING:
            return ApiResponse.error('只能预测未开始的比赛', 'MATCH_ALREADY_STARTED', 400)
        
        # 检查是否已经预测过
        existing_prediction = ExpertPrediction.query.filter_by(
            expert_id=user_id,
            match_id=match.id
        ).first()
        
        if existing_prediction:
            return ApiResponse.error('您已经对此比赛进行过预测', 'PREDICTION_EXISTS', 409)
        
        data = request.json
        prediction_data = data.get('prediction')
        confidence = data.get('confidence')
        reasoning = data.get('reasoning')
        
        if not prediction_data or not confidence:
            return ApiResponse.error('预测内容和置信度不能为空', 'MISSING_PREDICTION_DATA', 400)
        
        if not (0 <= confidence <= 100):
            return ApiResponse.error('置信度必须在0-100之间', 'INVALID_CONFIDENCE', 400)
        
        # 创建预测
        prediction = ExpertPrediction(
            expert_id=user_id,
            match_id=match.id,
            prediction=prediction_data,
            confidence=confidence,
            reasoning=reasoning
        )
        
        db.session.add(prediction)
        db.session.commit()
        
        return ApiResponse.success({
            'prediction': prediction.to_dict()
        }, '预测发布成功')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"创建预测失败: {e}")
        return ApiResponse.error('创建预测失败', 'CREATE_PREDICTION_FAILED', 500)
