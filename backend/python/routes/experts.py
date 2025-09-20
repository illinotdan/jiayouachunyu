"""
专家相关API路由
"""

from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError
from sqlalchemy import desc, func

from config.database import db
from models.user import User, UserRole, ExpertTier, UserFollow, ExpertApplication
from models.content import Article, ContentView, ContentType
from models.match import ExpertPrediction
from utils.response import ApiResponse
from utils.decorators import limiter, cache
from utils.pagination import paginate

experts_bp = Blueprint('experts', __name__)

class ExpertFilterSchema(Schema):
    """专家筛选参数验证"""
    page = fields.Int(load_default=1, validate=lambda x: x > 0)
    page_size = fields.Int(load_default=20, validate=lambda x: 1 <= x <= 100)
    tier = fields.Str(validate=lambda x: x in ['diamond', 'platinum', 'gold', 'silver', 'bronze'])
    expertise = fields.Str()
    sort = fields.Str(load_default='accuracy_desc', validate=lambda x: x in [
        'accuracy_desc', 'followers_desc', 'articles_desc', 'reputation_desc'
    ])
    search = fields.Str()

@experts_bp.route('', methods=['GET'])
@limiter.limit("30 per minute")
@cache.cached(timeout=600, key_prefix='experts_list')
def get_experts():
    """获取专家列表"""
    schema = ExpertFilterSchema()
    
    try:
        filters = schema.load(request.args)
    except ValidationError as err:
        return ApiResponse.error('参数验证失败', 'VALIDATION_ERROR', 400, err.messages)
    
    try:
        # 构建查询 - 只查询专家和管理员
        query = User.query.filter(User.role.in_([UserRole.EXPERT, UserRole.ADMIN]))
        
        # 等级筛选
        if filters.get('tier'):
            query = query.filter(User.tier == ExpertTier(filters['tier']))
        
        # 搜索筛选
        if filters.get('search'):
            search_term = f"%{filters['search']}%"
            query = query.filter(
                db.or_(
                    User.username.ilike(search_term),
                    User.bio.ilike(search_term)
                )
            )
        
        # 排序
        sort_option = filters.get('sort', 'accuracy_desc')
        if sort_option == 'accuracy_desc':
            # 按预测准确率排序（需要子查询）
            query = query.outerjoin(ExpertPrediction).group_by(User.id).order_by(
                desc(func.avg(
                    func.case(
                        (ExpertPrediction.result == 'correct', 100),
                        (ExpertPrediction.result == 'incorrect', 0),
                        else_=None
                    )
                ))
            )
        elif sort_option == 'followers_desc':
            # 按关注者数量排序
            query = query.outerjoin(UserFollow, User.id == UserFollow.following_id).group_by(User.id).order_by(
                desc(func.count(UserFollow.follower_id))
            )
        elif sort_option == 'articles_desc':
            # 按文章数量排序
            query = query.outerjoin(Article).group_by(User.id).order_by(
                desc(func.count(Article.id))
            )
        elif sort_option == 'reputation_desc':
            query = query.order_by(desc(User.reputation))
        
        # 分页
        page = filters.get('page', 1)
        page_size = filters.get('page_size', 20)
        
        paginated_experts = paginate(query, page, page_size)
        
        return ApiResponse.success({
            'experts': [expert.to_dict() for expert in paginated_experts.items],
            'pagination': {
                'page': paginated_experts.page,
                'pageSize': page_size,
                'total': paginated_experts.total,
                'totalPages': paginated_experts.pages,
                'hasNext': paginated_experts.has_next,
                'hasPrev': paginated_experts.has_prev
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"获取专家列表失败: {e}")
        return ApiResponse.error('获取专家列表失败', 'GET_EXPERTS_FAILED', 500)

@experts_bp.route('/<int:expert_id>', methods=['GET'])
@limiter.limit("60 per minute")
@cache.cached(timeout=600, key_prefix='expert_detail')
def get_expert_detail(expert_id):
    """获取专家详情"""
    try:
        expert = User.query.filter_by(id=expert_id).filter(
            User.role.in_([UserRole.EXPERT, UserRole.ADMIN])
        ).first()
        
        if not expert:
            return ApiResponse.error('专家不存在', 'EXPERT_NOT_FOUND', 404)
        
        # 记录浏览
        user_id = None
        try:
            from flask_jwt_extended import get_jwt_identity
            user_id = get_jwt_identity()
        except:
            pass
        
        ContentView.record_view(
            ContentType.EXPERT,
            expert.id,
            user_id=user_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        # 获取专家的详细统计
        expert_data = expert.to_dict()
        
        # 获取最近的文章
        recent_articles = Article.query.filter_by(
            author_id=expert.id,
            status='published'
        ).order_by(desc(Article.published_at)).limit(5).all()
        
        # 获取最近的预测
        recent_predictions = ExpertPrediction.query.filter_by(
            expert_id=expert.id
        ).order_by(desc(ExpertPrediction.created_at)).limit(10).all()
        
        expert_data.update({
            'recentArticles': [article.to_dict() for article in recent_articles],
            'recentPredictions': [pred.to_dict() for pred in recent_predictions],
            'achievements': []  # TODO: 实现成就系统
        })
        
        return ApiResponse.success({
            'expert': expert_data
        })
        
    except Exception as e:
        current_app.logger.error(f"获取专家详情失败: {e}")
        return ApiResponse.error('获取专家详情失败', 'GET_EXPERT_DETAIL_FAILED', 500)

@experts_bp.route('/<int:expert_id>/articles', methods=['GET'])
@limiter.limit("30 per minute")
def get_expert_articles(expert_id):
    """获取专家文章列表"""
    try:
        expert = User.query.get(expert_id)
        if not expert or expert.role not in [UserRole.EXPERT, UserRole.ADMIN]:
            return ApiResponse.error('专家不存在', 'EXPERT_NOT_FOUND', 404)
        
        page = request.args.get('page', 1, type=int)
        page_size = min(request.args.get('page_size', 20, type=int), 50)
        
        articles_query = Article.query.filter_by(
            author_id=expert_id,
            status='published'
        ).order_by(desc(Article.published_at))
        
        paginated_articles = paginate(articles_query, page, page_size)
        
        return ApiResponse.success({
            'articles': [article.to_dict() for article in paginated_articles.items],
            'pagination': {
                'page': paginated_articles.page,
                'pageSize': page_size,
                'total': paginated_articles.total,
                'totalPages': paginated_articles.pages
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"获取专家文章失败: {e}")
        return ApiResponse.error('获取专家文章失败', 'GET_EXPERT_ARTICLES_FAILED', 500)

@experts_bp.route('/<int:expert_id>/predictions', methods=['GET'])
@limiter.limit("30 per minute")
def get_expert_predictions(expert_id):
    """获取专家预测记录"""
    try:
        expert = User.query.get(expert_id)
        if not expert or expert.role not in [UserRole.EXPERT, UserRole.ADMIN]:
            return ApiResponse.error('专家不存在', 'EXPERT_NOT_FOUND', 404)
        
        page = request.args.get('page', 1, type=int)
        page_size = min(request.args.get('page_size', 20, type=int), 50)
        
        predictions_query = ExpertPrediction.query.filter_by(
            expert_id=expert_id
        ).order_by(desc(ExpertPrediction.created_at))
        
        paginated_predictions = paginate(predictions_query, page, page_size)
        
        return ApiResponse.success({
            'predictions': [pred.to_dict() for pred in paginated_predictions.items],
            'pagination': {
                'page': paginated_predictions.page,
                'pageSize': page_size,
                'total': paginated_predictions.total,
                'totalPages': paginated_predictions.pages
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"获取专家预测失败: {e}")
        return ApiResponse.error('获取专家预测失败', 'GET_EXPERT_PREDICTIONS_FAILED', 500)

@experts_bp.route('/<int:expert_id>/follow', methods=['POST'])
@jwt_required()
@limiter.limit("10 per minute")
def toggle_follow_expert(expert_id):
    """关注/取消关注专家"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return ApiResponse.error('用户不存在', 'USER_NOT_FOUND', 404)
        
        expert = User.query.get(expert_id)
        if not expert or expert.role not in [UserRole.EXPERT, UserRole.ADMIN]:
            return ApiResponse.error('专家不存在', 'EXPERT_NOT_FOUND', 404)
        
        if user_id == expert_id:
            return ApiResponse.error('不能关注自己', 'CANNOT_FOLLOW_SELF', 400)
        
        # 切换关注状态
        if user.is_following(expert):
            user.unfollow(expert)
            action = 'unfollowed'
            message = '取消关注成功'
        else:
            user.follow(expert)
            action = 'followed'
            message = '关注成功'
        
        db.session.commit()
        
        return ApiResponse.success({
            'action': action,
            'expertId': expert_id,
            'followerCount': expert.get_follower_count()
        }, message)
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"关注操作失败: {e}")
        return ApiResponse.error('操作失败，请稍后重试', 'FOLLOW_FAILED', 500)

@experts_bp.route('/apply', methods=['POST'])
@jwt_required()
@limiter.limit("3 per hour")
def apply_for_expert():
    """申请成为专家"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return ApiResponse.error('用户不存在', 'USER_NOT_FOUND', 404)
        
        if user.role in [UserRole.EXPERT, UserRole.ADMIN]:
            return ApiResponse.error('您已经是专家用户', 'ALREADY_EXPERT', 400)
        
        # 检查是否已有待处理的申请
        existing_application = ExpertApplication.query.filter_by(
            user_id=user_id,
            status=ExpertApplication.Status.PENDING
        ).first()
        
        if existing_application:
            return ApiResponse.error('您已有待处理的专家申请', 'APPLICATION_EXISTS', 409)
        
        data = request.json
        expertise_areas = data.get('expertiseAreas', [])
        bio = data.get('bio', '')
        experience_years = data.get('experienceYears')
        portfolio_links = data.get('portfolioLinks', [])
        social_proof = data.get('socialProof', '')
        
        if not expertise_areas or not bio:
            return ApiResponse.error('专业领域和个人简介不能为空', 'MISSING_REQUIRED_FIELDS', 400)
        
        if len(bio) < 50:
            return ApiResponse.error('个人简介至少需要50个字符', 'BIO_TOO_SHORT', 400)
        
        # 创建专家申请
        application = ExpertApplication(
            user_id=user_id,
            expertise_areas=expertise_areas,
            bio=bio,
            experience_years=experience_years,
            portfolio_links=portfolio_links,
            social_proof=social_proof
        )
        
        db.session.add(application)
        db.session.commit()
        
        return ApiResponse.success({
            'application': application.to_dict()
        }, '专家申请提交成功，我们会在3-5个工作日内审核')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"专家申请失败: {e}")
        return ApiResponse.error('申请提交失败', 'APPLICATION_FAILED', 500)

@experts_bp.route('/applications', methods=['GET'])
@jwt_required()
def get_expert_applications():
    """获取专家申请列表（管理员）"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.role != UserRole.ADMIN:
            return ApiResponse.error('权限不足', 'PERMISSION_DENIED', 403)
        
        page = request.args.get('page', 1, type=int)
        page_size = min(request.args.get('page_size', 20, type=int), 50)
        status_filter = request.args.get('status')
        
        query = ExpertApplication.query
        
        if status_filter:
            query = query.filter_by(status=ExpertApplication.Status(status_filter))
        
        query = query.order_by(desc(ExpertApplication.applied_at))
        
        paginated_applications = paginate(query, page, page_size)
        
        return ApiResponse.success({
            'applications': [app.to_dict() for app in paginated_applications.items],
            'pagination': {
                'page': paginated_applications.page,
                'pageSize': page_size,
                'total': paginated_applications.total,
                'totalPages': paginated_applications.pages
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"获取专家申请失败: {e}")
        return ApiResponse.error('获取申请列表失败', 'GET_APPLICATIONS_FAILED', 500)

@experts_bp.route('/applications/<int:application_id>', methods=['PUT'])
@jwt_required()
def review_expert_application(application_id):
    """审核专家申请（管理员）"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.role != UserRole.ADMIN:
            return ApiResponse.error('权限不足', 'PERMISSION_DENIED', 403)
        
        application = ExpertApplication.query.get(application_id)
        if not application:
            return ApiResponse.error('申请不存在', 'APPLICATION_NOT_FOUND', 404)
        
        data = request.json
        action = data.get('action')  # 'approve' or 'reject'
        review_notes = data.get('reviewNotes', '')
        
        if action not in ['approve', 'reject']:
            return ApiResponse.error('无效的审核操作', 'INVALID_ACTION', 400)
        
        # 更新申请状态
        if action == 'approve':
            application.status = ExpertApplication.Status.APPROVED
            
            # 提升用户为专家
            applicant = User.query.get(application.user_id)
            if applicant:
                applicant.role = UserRole.EXPERT
                applicant.tier = ExpertTier.SILVER  # 默认银级专家
                applicant.verified = True
        else:
            application.status = ExpertApplication.Status.REJECTED
        
        application.reviewer_id = user_id
        application.review_notes = review_notes
        application.reviewed_at = datetime.utcnow()
        
        db.session.commit()
        
        return ApiResponse.success({
            'application': application.to_dict()
        }, f'申请{action}成功')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"审核专家申请失败: {e}")
        return ApiResponse.error('审核失败', 'REVIEW_FAILED', 500)

@experts_bp.route('/ranking', methods=['GET'])
@limiter.limit("30 per minute")
@cache.cached(timeout=900, key_prefix='expert_ranking')
def get_expert_ranking():
    """获取专家排行榜"""
    try:
        # 按预测准确率排序的专家排行
        accuracy_ranking = db.session.query(
            User.id,
            User.username,
            User.avatar_url,
            User.tier,
            func.count(ExpertPrediction.id).label('total_predictions'),
            func.count(
                func.case(
                    (ExpertPrediction.result == 'correct', 1),
                    else_=None
                )
            ).label('correct_predictions'),
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
            func.count(ExpertPrediction.id) >= 5  # 至少5次预测
        ).order_by(desc('accuracy')).limit(20).all()
        
        # 按关注者数量排序
        followers_ranking = db.session.query(
            User.id,
            User.username,
            User.avatar_url,
            User.tier,
            func.count(UserFollow.follower_id).label('follower_count')
        ).outerjoin(UserFollow, User.id == UserFollow.following_id).filter(
            User.role.in_([UserRole.EXPERT, UserRole.ADMIN])
        ).group_by(User.id).order_by(desc('follower_count')).limit(20).all()
        
        return ApiResponse.success({
            'accuracyRanking': [
                {
                    'id': row.id,
                    'username': row.username,
                    'avatar': row.avatar_url,
                    'tier': row.tier.value if row.tier else 'bronze',
                    'totalPredictions': row.total_predictions,
                    'correctPredictions': row.correct_predictions,
                    'accuracy': float(row.accuracy) if row.accuracy else 0
                }
                for row in accuracy_ranking
            ],
            'followersRanking': [
                {
                    'id': row.id,
                    'username': row.username,
                    'avatar': row.avatar_url,
                    'tier': row.tier.value if row.tier else 'bronze',
                    'followerCount': row.follower_count
                }
                for row in followers_ranking
            ]
        })
        
    except Exception as e:
        current_app.logger.error(f"获取专家排行失败: {e}")
        return ApiResponse.error('获取排行榜失败', 'GET_RANKING_FAILED', 500)
