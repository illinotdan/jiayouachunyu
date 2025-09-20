"""
学习相关API路由
"""
from datetime import datetime

from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError
from sqlalchemy import desc, func, or_

from config.database import db
from models.user import User
from models.learning import (
    LearningContent, LearningContentType, DifficultyLevel,
    LearningComment, UserLearningProgress, AIAnalysisRequest,
    LearningPath, MatchDiscussion
)
from models.content import ContentView, ContentType
from utils.response import ApiResponse
from utils.decorators import limiter, cache
from utils.pagination import paginate

learning_bp = Blueprint('learning', __name__)

class LearningFilterSchema(Schema):
    """学习内容筛选参数"""
    page = fields.Int(load_default=1, validate=lambda x: x > 0)
    page_size = fields.Int(load_default=20, validate=lambda x: 1 <= x <= 100)
    type = fields.Str(validate=lambda x: x in ['guide', 'analysis', 'tips', 'qa'])
    difficulty = fields.Str(validate=lambda x: x in ['beginner', 'intermediate', 'advanced', 'expert'])
    category = fields.Str()
    search = fields.Str()

@learning_bp.route('/content', methods=['GET'])
@limiter.limit("30 per minute")
@cache.cached(timeout=600, key_prefix='learning_content')
def get_learning_content():
    """获取学习内容列表"""
    schema = LearningFilterSchema()
    
    try:
        filters = schema.load(request.args)
    except ValidationError as err:
        return ApiResponse.error('参数验证失败', 'VALIDATION_ERROR', 400, err.messages)
    
    try:
        # 构建查询
        query = LearningContent.query.filter_by(is_verified=True)
        
        # 类型筛选
        if filters.get('type'):
            query = query.filter(LearningContent.content_type == LearningContentType(filters['type']))
        
        # 难度筛选
        if filters.get('difficulty'):
            query = query.filter(LearningContent.difficulty == DifficultyLevel(filters['difficulty']))
        
        # 分类筛选
        if filters.get('category'):
            query = query.filter(LearningContent.category == filters['category'])
        
        # 搜索筛选
        if filters.get('search'):
            search_term = f"%{filters['search']}%"
            query = query.filter(
                or_(
                    LearningContent.title.ilike(search_term),
                    LearningContent.description.ilike(search_term),
                    func.array_to_string(LearningContent.tags, ',').ilike(search_term)
                )
            )
        
        # 排序：精选内容优先，然后按质量评分
        query = query.order_by(
            desc(LearningContent.is_featured),
            desc(LearningContent.quality_score),
            desc(LearningContent.published_at)
        )
        
        # 分页
        page = filters.get('page', 1)
        page_size = filters.get('page_size', 20)
        
        paginated_content = paginate(query, page, page_size)
        
        return ApiResponse.success({
            'content': [content.to_dict() for content in paginated_content.items],
            'pagination': {
                'page': paginated_content.page,
                'pageSize': page_size,
                'total': paginated_content.total,
                'totalPages': paginated_content.pages
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"获取学习内容失败: {e}")
        return ApiResponse.error('获取学习内容失败', 'GET_LEARNING_CONTENT_FAILED', 500)

@learning_bp.route('/content/<int:content_id>', methods=['GET'])
@limiter.limit("60 per minute")
def get_learning_content_detail(content_id):
    """获取学习内容详情"""
    try:
        content = LearningContent.query.get(content_id)
        
        if not content:
            return ApiResponse.error('学习内容不存在', 'CONTENT_NOT_FOUND', 404)
        
        # 记录浏览
        user_id = None
        try:
            user_id = get_jwt_identity()
        except:
            pass
        
        ContentView.record_view(
            ContentType.LEARNING,
            content.id,
            user_id=user_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        # 获取评论
        comments = LearningComment.query.filter_by(
            content_id=content_id,
            parent_id=None  # 只获取顶级评论
        ).order_by(desc(LearningComment.like_count)).limit(10).all()
        
        # 获取用户学习进度（如果已登录）
        progress = None
        if user_id:
            progress = UserLearningProgress.query.filter_by(
                user_id=user_id,
                content_id=content_id
            ).first()
        
        return ApiResponse.success({
            'content': content.to_dict(include_content=True),
            'comments': [comment.to_dict() for comment in comments],
            'userProgress': progress.to_dict() if progress else None
        })
        
    except Exception as e:
        current_app.logger.error(f"获取学习内容详情失败: {e}")
        return ApiResponse.error('获取内容详情失败', 'GET_CONTENT_DETAIL_FAILED', 500)

@learning_bp.route('/ai-analysis', methods=['POST'])
@jwt_required()
@limiter.limit("5 per hour")
def request_ai_analysis():
    """请求AI分析"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return ApiResponse.error('用户不存在', 'USER_NOT_FOUND', 404)
        
        data = request.json
        analysis_type = data.get('analysisType')
        input_data = data.get('inputData', {})
        
        if not analysis_type:
            return ApiResponse.error('分析类型不能为空', 'MISSING_ANALYSIS_TYPE', 400)
        
        # 检查用户是否有待处理的分析请求
        pending_request = AIAnalysisRequest.query.filter_by(
            user_id=user_id,
            status=AIAnalysisRequest.Status.PENDING
        ).first()
        
        if pending_request:
            return ApiResponse.error('您有待处理的分析请求，请等待完成', 'PENDING_REQUEST_EXISTS', 409)
        
        # 创建分析请求
        analysis_request = AIAnalysisRequest(
            user_id=user_id,
            analysis_type=AIAnalysisRequest.AnalysisType(analysis_type),
            input_data=input_data
        )
        
        db.session.add(analysis_request)
        db.session.commit()
        
        # TODO: 触发异步AI分析任务
        # from tasks.ai_analysis import process_analysis_request
        # process_analysis_request.delay(analysis_request.id)
        
        return ApiResponse.success({
            'requestId': analysis_request.id,
            'status': analysis_request.status.value,
            'estimatedTime': '2-5分钟'
        }, 'AI分析请求已提交，请稍等处理结果')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"AI分析请求失败: {e}")
        return ApiResponse.error('分析请求失败', 'AI_ANALYSIS_FAILED', 500)

@learning_bp.route('/ai-analysis/<int:request_id>', methods=['GET'])
@jwt_required()
@limiter.limit("60 per minute")
def get_ai_analysis_result(request_id):
    """获取AI分析结果"""
    try:
        user_id = get_jwt_identity()
        
        analysis_request = AIAnalysisRequest.query.filter_by(
            id=request_id,
            user_id=user_id
        ).first()
        
        if not analysis_request:
            return ApiResponse.error('分析请求不存在', 'REQUEST_NOT_FOUND', 404)
        
        return ApiResponse.success({
            'request': analysis_request.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f"获取AI分析结果失败: {e}")
        return ApiResponse.error('获取分析结果失败', 'GET_AI_RESULT_FAILED', 500)

@learning_bp.route('/progress', methods=['GET'])
@jwt_required()
@limiter.limit("30 per minute")
def get_user_learning_progress():
    """获取用户学习进度"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return ApiResponse.error('用户不存在', 'USER_NOT_FOUND', 404)
        
        # 获取学习进度
        progress_query = UserLearningProgress.query.filter_by(user_id=user_id)
        
        total_content = progress_query.count()
        completed_content = progress_query.filter_by(is_completed=True).count()
        in_progress_content = progress_query.filter(
            UserLearningProgress.completion_percentage > 0,
            UserLearningProgress.is_completed == False
        ).count()
        
        # 获取最近学习的内容
        recent_progress = progress_query.order_by(
            desc(UserLearningProgress.last_accessed_at)
        ).limit(10).all()
        
        # 计算总学习时间
        total_time = db.session.query(
            func.sum(UserLearningProgress.time_spent)
        ).filter_by(user_id=user_id).scalar() or 0
        
        return ApiResponse.success({
            'overview': {
                'totalContent': total_content,
                'completedContent': completed_content,
                'inProgressContent': in_progress_content,
                'completionRate': round((completed_content / total_content * 100) if total_content > 0 else 0, 2),
                'totalTimeSpent': total_time
            },
            'recentProgress': [p.to_dict() for p in recent_progress]
        })
        
    except Exception as e:
        current_app.logger.error(f"获取学习进度失败: {e}")
        return ApiResponse.error('获取学习进度失败', 'GET_PROGRESS_FAILED', 500)

@learning_bp.route('/content/<int:content_id>/progress', methods=['POST'])
@jwt_required()
@limiter.limit("30 per minute")
def update_learning_progress(content_id):
    """更新学习进度"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return ApiResponse.error('用户不存在', 'USER_NOT_FOUND', 404)
        
        content = LearningContent.query.get(content_id)
        if not content:
            return ApiResponse.error('学习内容不存在', 'CONTENT_NOT_FOUND', 404)
        
        data = request.json
        completion_percentage = data.get('completionPercentage', 0)
        time_spent = data.get('timeSpent', 0)
        notes = data.get('notes', '')
        
        # 获取或创建进度记录
        progress = UserLearningProgress.query.filter_by(
            user_id=user_id,
            content_id=content_id
        ).first()
        
        if not progress:
            progress = UserLearningProgress(
                user_id=user_id,
                content_id=content_id
            )
            db.session.add(progress)
        
        # 更新进度
        progress.completion_percentage = min(100, max(0, completion_percentage))
        progress.time_spent += time_spent
        progress.notes = notes
        progress.last_accessed_at = datetime.utcnow()
        
        # 检查是否完成
        if progress.completion_percentage >= 100 and not progress.is_completed:
            progress.is_completed = True
            progress.completed_at = datetime.utcnow()
        
        db.session.commit()
        
        return ApiResponse.success({
            'progress': progress.to_dict()
        }, '学习进度已更新')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新学习进度失败: {e}")
        return ApiResponse.error('更新进度失败', 'UPDATE_PROGRESS_FAILED', 500)

@learning_bp.route('/match-discussions/<string:match_id>', methods=['GET'])
@limiter.limit("30 per minute")
def get_match_discussions(match_id):
    """获取比赛讨论列表"""
    try:
        from models.match import Match
        
        match = Match.query.filter_by(match_id=match_id).first()
        if not match:
            return ApiResponse.error('比赛不存在', 'MATCH_NOT_FOUND', 404)
        
        category_filter = request.args.get('category')
        page = request.args.get('page', 1, type=int)
        page_size = min(request.args.get('page_size', 20, type=int), 50)
        
        # 构建查询
        query = MatchDiscussion.query.filter_by(match_id=match.id)
        
        if category_filter:
            query = query.filter_by(category=MatchDiscussion.Category(category_filter))
        
        # 排序：置顶优先，然后按活跃度
        query = query.order_by(
            desc(MatchDiscussion.is_sticky),
            desc(MatchDiscussion.is_hot),
            desc(MatchDiscussion.last_activity_at)
        )
        
        paginated_discussions = paginate(query, page, page_size)
        
        # 统计信息
        total_discussions = MatchDiscussion.query.filter_by(match_id=match.id).count()
        active_users = db.session.query(
            func.count(func.distinct(MatchDiscussion.author_id))
        ).filter_by(match_id=match.id).scalar()
        
        return ApiResponse.success({
            'discussions': [d.to_dict() for d in paginated_discussions.items],
            'pagination': {
                'page': paginated_discussions.page,
                'pageSize': page_size,
                'total': paginated_discussions.total,
                'totalPages': paginated_discussions.pages
            },
            'stats': {
                'totalDiscussions': total_discussions,
                'activeUsers': active_users
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"获取比赛讨论失败: {e}")
        return ApiResponse.error('获取比赛讨论失败', 'GET_MATCH_DISCUSSIONS_FAILED', 500)

@learning_bp.route('/match-discussions', methods=['POST'])
@jwt_required()
@limiter.limit("10 per hour")
def create_match_discussion():
    """创建比赛讨论"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return ApiResponse.error('用户不存在', 'USER_NOT_FOUND', 404)
        
        data = request.json
        match_id = data.get('matchId')
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        category = data.get('category', 'general')
        tags = data.get('tags', [])
        is_question = data.get('isQuestion', False)
        
        if not match_id or not title or not content:
            return ApiResponse.error('比赛ID、标题和内容不能为空', 'MISSING_REQUIRED_FIELDS', 400)
        
        if len(title) < 5 or len(title) > 200:
            return ApiResponse.error('标题长度应在5-200字符之间', 'INVALID_TITLE_LENGTH', 400)
        
        if len(content) < 20:
            return ApiResponse.error('内容至少需要20个字符', 'CONTENT_TOO_SHORT', 400)
        
        # 验证比赛是否存在
        from models.match import Match
        match = Match.query.get(match_id)
        if not match:
            return ApiResponse.error('比赛不存在', 'MATCH_NOT_FOUND', 404)
        
        # 创建讨论
        discussion = MatchDiscussion(
            match_id=match_id,
            author_id=user_id,
            title=title,
            content=content,
            category=MatchDiscussion.Category(category),
            tags=tags[:5],  # 最多5个标签
            is_question=is_question
        )
        
        db.session.add(discussion)
        db.session.commit()
        
        return ApiResponse.success({
            'discussion': discussion.to_dict(include_content=True)
        }, '讨论发布成功')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"创建比赛讨论失败: {e}")
        return ApiResponse.error('发布讨论失败', 'CREATE_DISCUSSION_FAILED', 500)

@learning_bp.route('/paths', methods=['GET'])
@limiter.limit("30 per minute")
@cache.cached(timeout=900, key_prefix='learning_paths')
def get_learning_paths():
    """获取学习路径列表"""
    try:
        difficulty = request.args.get('difficulty')
        category = request.args.get('category')
        
        query = LearningPath.query.filter_by(is_published=True)
        
        if difficulty:
            query = query.filter_by(difficulty=DifficultyLevel(difficulty))
        
        if category:
            query = query.filter_by(category=category)
        
        # 排序：精选优先，然后按学习人数
        query = query.order_by(
            desc(LearningPath.is_featured),
            desc(LearningPath.enrollment_count)
        )
        
        paths = query.all()
        
        return ApiResponse.success({
            'paths': [path.to_dict() for path in paths]
        })
        
    except Exception as e:
        current_app.logger.error(f"获取学习路径失败: {e}")
        return ApiResponse.error('获取学习路径失败', 'GET_PATHS_FAILED', 500)

@learning_bp.route('/assessment', methods=['POST'])
@jwt_required()
@limiter.limit("3 per day")
def create_skill_assessment():
    """创建技能评估"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return ApiResponse.error('用户不存在', 'USER_NOT_FOUND', 404)
        
        data = request.json
        
        # 验证技能评分
        skills = data.get('skills', {})
        required_skills = ['laning', 'farming', 'teamfight', 'mapAwareness', 'gameSense', 'mechanical']
        
        for skill in required_skills:
            if skill not in skills or not (1 <= skills[skill] <= 10):
                return ApiResponse.error(f'技能评分 {skill} 必须在1-10之间', 'INVALID_SKILL_SCORE', 400)
        
        # 创建或更新技能评估
        from models.learning import UserSkillAssessment
        
        assessment = UserSkillAssessment.query.filter_by(user_id=user_id).first()
        
        if not assessment:
            assessment = UserSkillAssessment(user_id=user_id)
            db.session.add(assessment)
        
        # 更新技能评分
        assessment.laning_skill = skills['laning']
        assessment.farming_skill = skills['farming']
        assessment.teamfight_skill = skills['teamfight']
        assessment.map_awareness = skills['mapAwareness']
        assessment.game_sense = skills['gameSense']
        assessment.mechanical_skill = skills['mechanical']
        
        # 计算总体评分
        assessment.overall_score = UserSkillAssessment.calculate_overall_score(skills)
        
        # 生成AI建议
        assessment.ai_suggestions = generate_skill_suggestions(skills)
        assessment.improvement_areas = identify_improvement_areas(skills)
        assessment.strengths = identify_strengths(skills)
        
        assessment.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return ApiResponse.success({
            'assessment': assessment.to_dict()
        }, '技能评估完成')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"技能评估失败: {e}")
        return ApiResponse.error('技能评估失败', 'SKILL_ASSESSMENT_FAILED', 500)

def generate_skill_suggestions(skills):
    """生成技能改进建议"""
    suggestions = []
    
    if skills['laning'] < 6:
        suggestions.append({
            'area': 'laning',
            'suggestion': '建议多练习补刀和对线，可以观看职业选手的对线视频学习走位技巧'
        })
    
    if skills['farming'] < 6:
        suggestions.append({
            'area': 'farming',
            'suggestion': '提高发育效率，学习野区叠野和拉野技巧，合理分配农兵时间'
        })
    
    if skills['teamfight'] < 6:
        suggestions.append({
            'area': 'teamfight',
            'suggestion': '多观察团战录像，学习站位选择和技能释放时机'
        })
    
    if skills['mapAwareness'] < 6:
        suggestions.append({
            'area': 'mapAwareness',
            'suggestion': '提高地图意识，多看小地图，学习通过信息判断敌方动向'
        })
    
    return suggestions

def identify_improvement_areas(skills):
    """识别需要改进的领域"""
    areas = []
    skill_names = {
        'laning': '对线技能',
        'farming': '发育技能', 
        'teamfight': '团战技能',
        'mapAwareness': '地图意识',
        'gameSense': '游戏理解',
        'mechanical': '操作技巧'
    }
    
    # 找出评分最低的2-3个技能
    sorted_skills = sorted(skills.items(), key=lambda x: x[1])
    
    for skill, score in sorted_skills[:3]:
        if score < 7:  # 评分低于7的技能需要改进
            areas.append(skill_names[skill])
    
    return areas

def identify_strengths(skills):
    """识别优势领域"""
    strengths = []
    skill_names = {
        'laning': '对线技能',
        'farming': '发育技能',
        'teamfight': '团战技能', 
        'mapAwareness': '地图意识',
        'gameSense': '游戏理解',
        'mechanical': '操作技巧'
    }
    
    # 找出评分最高的技能
    for skill, score in skills.items():
        if score >= 8:  # 评分8分以上的为优势
            strengths.append(skill_names[skill])
    
    return strengths
