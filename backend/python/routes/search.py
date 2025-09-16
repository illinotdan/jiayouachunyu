"""
搜索相关API路由
"""

from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError
from sqlalchemy import or_, desc, func

from config.database import db
from models.match import Match, Team, League
from models.user import User, UserRole
from models.content import Discussion, Article
from utils.response import ApiResponse
from utils.decorators import limiter, cache

search_bp = Blueprint('search', __name__)

class SearchSchema(Schema):
    """搜索参数验证"""
    q = fields.Str(required=True, validate=lambda x: len(x.strip()) >= 2)
    type = fields.Str(missing='all', validate=lambda x: x in ['all', 'matches', 'experts', 'discussions', 'articles'])
    page = fields.Int(missing=1, validate=lambda x: x > 0)
    page_size = fields.Int(missing=20, validate=lambda x: 1 <= x <= 100)

@search_bp.route('', methods=['GET'])
@limiter.limit("30 per minute")
@cache.cached(timeout=300, key_prefix='search_results')
def global_search():
    """全局搜索功能"""
    schema = SearchSchema()
    
    try:
        params = schema.load(request.args)
    except ValidationError as err:
        return ApiResponse.error('参数验证失败', 'VALIDATION_ERROR', 400, err.messages)
    
    try:
        query_text = params['q'].strip()
        search_type = params['type']
        page = params['page']
        page_size = params['page_size']
        
        results = {}
        total_results = 0
        search_time_start = time.time()
        
        if search_type in ['all', 'matches']:
            matches_results = search_matches(query_text, page if search_type == 'matches' else 1, 
                                           page_size if search_type == 'matches' else 5)
            results['matches'] = matches_results['items']
            if search_type == 'matches':
                results['pagination'] = matches_results['pagination']
            total_results += matches_results['total']
        
        if search_type in ['all', 'experts']:
            experts_results = search_experts(query_text, page if search_type == 'experts' else 1,
                                           page_size if search_type == 'experts' else 5)
            results['experts'] = experts_results['items']
            if search_type == 'experts':
                results['pagination'] = experts_results['pagination']
            total_results += experts_results['total']
        
        if search_type in ['all', 'discussions']:
            discussions_results = search_discussions(query_text, page if search_type == 'discussions' else 1,
                                                   page_size if search_type == 'discussions' else 5)
            results['discussions'] = discussions_results['items']
            if search_type == 'discussions':
                results['pagination'] = discussions_results['pagination']
            total_results += discussions_results['total']
        
        if search_type in ['all', 'articles']:
            articles_results = search_articles(query_text, page if search_type == 'articles' else 1,
                                             page_size if search_type == 'articles' else 5)
            results['articles'] = articles_results['items']
            if search_type == 'articles':
                results['pagination'] = articles_results['pagination']
            total_results += articles_results['total']
        
        search_time = time.time() - search_time_start
        
        return ApiResponse.success({
            'results': results,
            'total': total_results,
            'searchTime': round(search_time * 1000, 2),  # 毫秒
            'query': query_text,
            'type': search_type
        })
        
    except Exception as e:
        current_app.logger.error(f"搜索失败: {e}")
        return ApiResponse.error('搜索失败', 'SEARCH_FAILED', 500)

def search_matches(query_text, page, page_size):
    """搜索比赛"""
    try:
        # 构建搜索查询
        search_term = f"%{query_text}%"
        
        query = Match.query.join(League, isouter=True).join(
            Team, or_(Match.radiant_team_id == Team.id, Match.dire_team_id == Team.id), isouter=True
        ).filter(
            or_(
                League.name.ilike(search_term),
                Team.name.ilike(search_term),
                Team.tag.ilike(search_term)
            )
        ).distinct()
        
        # 排序
        query = query.order_by(desc(Match.start_time))
        
        # 分页
        from utils.pagination import paginate
        paginated_results = paginate(query, page, page_size)
        
        return {
            'items': [
                {
                    **match.to_dict(),
                    'type': 'match',
                    'relevance': calculate_match_relevance(match, query_text)
                }
                for match in paginated_results.items
            ],
            'total': paginated_results.total,
            'pagination': {
                'page': paginated_results.page,
                'pageSize': page_size,
                'totalPages': paginated_results.pages
            }
        }
        
    except Exception as e:
        current_app.logger.error(f"搜索比赛失败: {e}")
        return {'items': [], 'total': 0}

def search_experts(query_text, page, page_size):
    """搜索专家"""
    try:
        search_term = f"%{query_text}%"
        
        query = User.query.filter(
            User.role.in_([UserRole.EXPERT, UserRole.ADMIN])
        ).filter(
            or_(
                User.username.ilike(search_term),
                User.bio.ilike(search_term)
            )
        )
        
        # 排序：按声望降序
        query = query.order_by(desc(User.reputation))
        
        from utils.pagination import paginate
        paginated_results = paginate(query, page, page_size)
        
        return {
            'items': [
                {
                    **expert.to_dict(),
                    'type': 'expert',
                    'relevance': calculate_expert_relevance(expert, query_text)
                }
                for expert in paginated_results.items
            ],
            'total': paginated_results.total,
            'pagination': {
                'page': paginated_results.page,
                'pageSize': page_size,
                'totalPages': paginated_results.pages
            }
        }
        
    except Exception as e:
        current_app.logger.error(f"搜索专家失败: {e}")
        return {'items': [], 'total': 0}

def search_discussions(query_text, page, page_size):
    """搜索讨论"""
    try:
        search_term = f"%{query_text}%"
        
        query = Discussion.query.filter(
            or_(
                Discussion.title.ilike(search_term),
                Discussion.content.ilike(search_term),
                func.array_to_string(Discussion.tags, ',').ilike(search_term)
            )
        )
        
        # 排序：按最后活动时间降序
        query = query.order_by(desc(Discussion.last_activity_at))
        
        from utils.pagination import paginate
        paginated_results = paginate(query, page, page_size)
        
        return {
            'items': [
                {
                    **discussion.to_dict(),
                    'type': 'discussion',
                    'relevance': calculate_discussion_relevance(discussion, query_text)
                }
                for discussion in paginated_results.items
            ],
            'total': paginated_results.total,
            'pagination': {
                'page': paginated_results.page,
                'pageSize': page_size,
                'totalPages': paginated_results.pages
            }
        }
        
    except Exception as e:
        current_app.logger.error(f"搜索讨论失败: {e}")
        return {'items': [], 'total': 0}

def search_articles(query_text, page, page_size):
    """搜索文章"""
    try:
        search_term = f"%{query_text}%"
        
        query = Article.query.filter(
            Article.status == 'published'
        ).filter(
            or_(
                Article.title.ilike(search_term),
                Article.content.ilike(search_term),
                Article.summary.ilike(search_term),
                func.array_to_string(Article.tags, ',').ilike(search_term)
            )
        )
        
        # 排序：按发布时间降序
        query = query.order_by(desc(Article.published_at))
        
        from utils.pagination import paginate
        paginated_results = paginate(query, page, page_size)
        
        return {
            'items': [
                {
                    **article.to_dict(),
                    'type': 'article',
                    'relevance': calculate_article_relevance(article, query_text)
                }
                for article in paginated_results.items
            ],
            'total': paginated_results.total,
            'pagination': {
                'page': paginated_results.page,
                'pageSize': page_size,
                'totalPages': paginated_results.pages
            }
        }
        
    except Exception as e:
        current_app.logger.error(f"搜索文章失败: {e}")
        return {'items': [], 'total': 0}

def calculate_match_relevance(match, query_text):
    """计算比赛搜索相关性"""
    relevance = 0
    query_lower = query_text.lower()
    
    # 联赛名称匹配
    if match.league and query_lower in match.league.name.lower():
        relevance += 50
    
    # 战队名称匹配
    if match.radiant_team and query_lower in match.radiant_team.name.lower():
        relevance += 40
    if match.dire_team and query_lower in match.dire_team.name.lower():
        relevance += 40
    
    # 战队标签匹配
    if match.radiant_team and query_lower in match.radiant_team.tag.lower():
        relevance += 30
    if match.dire_team and query_lower in match.dire_team.tag.lower():
        relevance += 30
    
    # 根据比赛热度调整
    relevance += min(match.view_count / 100, 20)
    
    return min(relevance, 100)

def calculate_expert_relevance(expert, query_text):
    """计算专家搜索相关性"""
    relevance = 0
    query_lower = query_text.lower()
    
    # 用户名匹配
    if query_lower in expert.username.lower():
        relevance += 60
    
    # 简介匹配
    if expert.bio and query_lower in expert.bio.lower():
        relevance += 40
    
    # 根据专家等级调整
    tier_bonus = {
        'diamond': 20,
        'platinum': 15,
        'gold': 10,
        'silver': 5,
        'bronze': 0
    }
    relevance += tier_bonus.get(expert.tier.value if expert.tier else 'bronze', 0)
    
    # 根据声望调整
    relevance += min(expert.reputation / 1000, 20)
    
    return min(relevance, 100)

def calculate_discussion_relevance(discussion, query_text):
    """计算讨论搜索相关性"""
    relevance = 0
    query_lower = query_text.lower()
    
    # 标题匹配
    if query_lower in discussion.title.lower():
        relevance += 60
    
    # 内容匹配
    if query_lower in discussion.content.lower():
        relevance += 30
    
    # 标签匹配
    for tag in discussion.tags:
        if query_lower in tag.lower():
            relevance += 20
            break
    
    # 根据热度调整
    if discussion.is_hot:
        relevance += 15
    if discussion.is_pinned:
        relevance += 10
    
    # 根据互动数调整
    interaction_score = discussion.view_count * 0.1 + discussion.like_count * 0.5 + discussion.reply_count * 0.3
    relevance += min(interaction_score / 100, 15)
    
    return min(relevance, 100)

def calculate_article_relevance(article, query_text):
    """计算文章搜索相关性"""
    relevance = 0
    query_lower = query_text.lower()
    
    # 标题匹配
    if query_lower in article.title.lower():
        relevance += 60
    
    # 摘要匹配
    if article.summary and query_lower in article.summary.lower():
        relevance += 40
    
    # 内容匹配
    if query_lower in article.content.lower():
        relevance += 20
    
    # 标签匹配
    for tag in article.tags:
        if query_lower in tag.lower():
            relevance += 15
            break
    
    # 根据文章质量调整
    if article.featured:
        relevance += 20
    
    # 根据互动数调整
    interaction_score = article.view_count * 0.1 + article.like_count * 0.5
    relevance += min(interaction_score / 100, 15)
    
    return min(relevance, 100)
