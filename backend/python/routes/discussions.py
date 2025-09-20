"""
社区讨论相关API路由
"""

from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError
from sqlalchemy import desc, func

from config.database import db
from models.user import User
from models.content import Discussion, DiscussionReply, DiscussionCategory, ContentLike, ContentType, ContentView
from utils.response import ApiResponse
from utils.decorators import limiter, cache
from utils.pagination import paginate
from datetime import datetime, timedelta

discussions_bp = Blueprint('discussions', __name__)

class DiscussionFilterSchema(Schema):
    """讨论筛选参数验证"""
    page = fields.Int(load_default=1, validate=lambda x: x > 0)
    page_size = fields.Int(load_default=20, validate=lambda x: 1 <= x <= 100)
    category = fields.Str(validate=lambda x: x in ['analysis', 'prediction', 'strategy', 'news', 'general'])
    sort = fields.Str(load_default='latest', validate=lambda x: x in ['latest', 'hot', 'top'])
    search = fields.Str()

class CreateDiscussionSchema(Schema):
    """创建讨论验证"""
    title = fields.Str(required=True, validate=lambda x: 5 <= len(x) <= 200)
    content = fields.Str(required=True, validate=lambda x: len(x) >= 50)
    category = fields.Str(required=True, validate=lambda x: x in ['analysis', 'prediction', 'strategy', 'news', 'general'])
    tags = fields.List(fields.Str(), load_default=[], validate=lambda x: len(x) <= 5)

class CreateReplySchema(Schema):
    """创建回复验证"""
    content = fields.Str(required=True, validate=lambda x: len(x) >= 10)
    parent_id = fields.Int()

@discussions_bp.route('', methods=['GET'])
@limiter.limit("30 per minute")
@cache.cached(timeout=120, key_prefix='discussions_list')
def get_discussions():
    """获取讨论列表"""
    schema = DiscussionFilterSchema()
    
    try:
        filters = schema.load(request.args)
    except ValidationError as err:
        return ApiResponse.error('参数验证失败', 'VALIDATION_ERROR', 400, err.messages)
    
    try:
        # 构建查询
        query = Discussion.query
        
        # 分类筛选
        if filters.get('category'):
            query = query.filter(Discussion.category == DiscussionCategory(filters['category']))
        
        # 搜索筛选
        if filters.get('search'):
            search_term = f"%{filters['search']}%"
            query = query.filter(
                db.or_(
                    Discussion.title.ilike(search_term),
                    Discussion.content.ilike(search_term)
                )
            )
        
        # 排序
        sort_option = filters.get('sort', 'latest')
        if sort_option == 'latest':
            query = query.order_by(desc(Discussion.last_activity_at))
        elif sort_option == 'hot':
            # 热门排序：综合考虑浏览量、点赞数、回复数和时间
            query = query.order_by(
                desc(Discussion.is_pinned),
                desc(Discussion.is_hot),
                desc(
                    Discussion.view_count * 0.3 + 
                    Discussion.like_count * 0.4 + 
                    Discussion.reply_count * 0.3
                )
            )
        elif sort_option == 'top':
            query = query.order_by(desc(Discussion.like_count))
        
        # 分页
        page = filters.get('page', 1)
        page_size = filters.get('page_size', 20)
        
        paginated_discussions = paginate(query, page, page_size)
        
        return ApiResponse.success({
            'discussions': [discussion.to_dict() for discussion in paginated_discussions.items],
            'pagination': {
                'page': paginated_discussions.page,
                'pageSize': page_size,
                'total': paginated_discussions.total,
                'totalPages': paginated_discussions.pages,
                'hasNext': paginated_discussions.has_next,
                'hasPrev': paginated_discussions.has_prev
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"获取讨论列表失败: {e}")
        return ApiResponse.error('获取讨论列表失败', 'GET_DISCUSSIONS_FAILED', 500)

@discussions_bp.route('/<int:discussion_id>', methods=['GET'])
@limiter.limit("60 per minute")
def get_discussion_detail(discussion_id):
    """获取讨论详情"""
    try:
        discussion = Discussion.query.get(discussion_id)
        
        if not discussion:
            return ApiResponse.error('讨论不存在', 'DISCUSSION_NOT_FOUND', 404)
        
        # 记录浏览
        user_id = None
        try:
            from flask_jwt_extended import get_jwt_identity
            user_id = get_jwt_identity()
        except:
            pass
        
        ContentView.record_view(
            ContentType.DISCUSSION,
            discussion.id,
            user_id=user_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        # 获取回复
        replies = DiscussionReply.query.filter_by(
            discussion_id=discussion_id
        ).order_by(DiscussionReply.created_at).all()
        
        return ApiResponse.success({
            'discussion': discussion.to_dict(include_content=True),
            'replies': [reply.to_dict() for reply in replies]
        })
        
    except Exception as e:
        current_app.logger.error(f"获取讨论详情失败: {e}")
        return ApiResponse.error('获取讨论详情失败', 'GET_DISCUSSION_DETAIL_FAILED', 500)

@discussions_bp.route('', methods=['POST'])
@jwt_required()
@limiter.limit("5 per hour")
def create_discussion():
    """创建讨论"""
    schema = CreateDiscussionSchema()
    
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return ApiResponse.error('参数验证失败', 'VALIDATION_ERROR', 400, err.messages)
    
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return ApiResponse.error('用户不存在', 'USER_NOT_FOUND', 404)
        
        # 创建讨论
        discussion = Discussion(
            author_id=user_id,
            title=data['title'],
            content=data['content'],
            category=DiscussionCategory(data['category']),
            tags=data['tags']
        )
        
        db.session.add(discussion)
        db.session.commit()
        
        return ApiResponse.success({
            'discussion': discussion.to_dict(include_content=True)
        }, '讨论发布成功')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"创建讨论失败: {e}")
        return ApiResponse.error('发布讨论失败', 'CREATE_DISCUSSION_FAILED', 500)

@discussions_bp.route('/<int:discussion_id>/replies', methods=['POST'])
@jwt_required()
@limiter.limit("20 per hour")
def create_reply(discussion_id):
    """回复讨论"""
    schema = CreateReplySchema()
    
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return ApiResponse.error('参数验证失败', 'VALIDATION_ERROR', 400, err.messages)
    
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return ApiResponse.error('用户不存在', 'USER_NOT_FOUND', 404)
        
        discussion = Discussion.query.get(discussion_id)
        if not discussion:
            return ApiResponse.error('讨论不存在', 'DISCUSSION_NOT_FOUND', 404)
        
        if discussion.is_locked:
            return ApiResponse.error('讨论已被锁定', 'DISCUSSION_LOCKED', 403)
        
        # 检查父回复是否存在（如果是回复的回复）
        parent_id = data.get('parent_id')
        if parent_id:
            parent_reply = DiscussionReply.query.filter_by(
                id=parent_id,
                discussion_id=discussion_id
            ).first()
            if not parent_reply:
                return ApiResponse.error('父回复不存在', 'PARENT_REPLY_NOT_FOUND', 404)
        
        # 创建回复
        reply = DiscussionReply(
            discussion_id=discussion_id,
            author_id=user_id,
            parent_id=parent_id,
            content=data['content']
        )
        
        db.session.add(reply)
        
        # 更新讨论统计
        discussion.reply_count += 1
        discussion.update_activity()
        
        db.session.commit()
        
        return ApiResponse.success({
            'reply': reply.to_dict()
        }, '回复发布成功')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"创建回复失败: {e}")
        return ApiResponse.error('发布回复失败', 'CREATE_REPLY_FAILED', 500)

@discussions_bp.route('/<int:discussion_id>/like', methods=['POST'])
@jwt_required()
@limiter.limit("30 per minute")
def toggle_discussion_like(discussion_id):
    """点赞/取消点赞讨论"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return ApiResponse.error('用户不存在', 'USER_NOT_FOUND', 404)
        
        discussion = Discussion.query.get(discussion_id)
        if not discussion:
            return ApiResponse.error('讨论不存在', 'DISCUSSION_NOT_FOUND', 404)
        
        # 切换点赞状态
        is_liked = ContentLike.toggle_like(user_id, ContentType.DISCUSSION, discussion_id)
        
        db.session.commit()
        
        return ApiResponse.success({
            'isLiked': is_liked,
            'likeCount': discussion.like_count
        }, '操作成功')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"点赞操作失败: {e}")
        return ApiResponse.error('操作失败', 'LIKE_FAILED', 500)

@discussions_bp.route('/replies/<int:reply_id>/like', methods=['POST'])
@jwt_required()
@limiter.limit("30 per minute")
def toggle_reply_like(reply_id):
    """点赞/取消点赞回复"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return ApiResponse.error('用户不存在', 'USER_NOT_FOUND', 404)
        
        reply = DiscussionReply.query.get(reply_id)
        if not reply:
            return ApiResponse.error('回复不存在', 'REPLY_NOT_FOUND', 404)
        
        # 切换点赞状态
        is_liked = ContentLike.toggle_like(user_id, ContentType.REPLY, reply_id)
        
        db.session.commit()
        
        return ApiResponse.success({
            'isLiked': is_liked,
            'likeCount': reply.like_count
        }, '操作成功')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"点赞回复失败: {e}")
        return ApiResponse.error('操作失败', 'LIKE_REPLY_FAILED', 500)

@discussions_bp.route('/stats', methods=['GET'])
@limiter.limit("30 per minute")
@cache.cached(timeout=600, key_prefix='discussion_stats')
def get_discussion_stats():
    """获取社区统计数据"""
    try:
        # 计算各种统计数据
        total_discussions = Discussion.query.count()
        
        # 活跃用户数（最近7天有活动的用户）
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        active_users = db.session.query(func.count(func.distinct(Discussion.author_id))).filter(
            Discussion.created_at >= seven_days_ago
        ).scalar()
        
        # 今日发帖数
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_posts = Discussion.query.filter(Discussion.created_at >= today_start).count()
        
        # 总回复数
        total_replies = DiscussionReply.query.count()
        
        # 各分类统计
        category_stats = db.session.query(
            Discussion.category,
            func.count(Discussion.id)
        ).group_by(Discussion.category).all()
        
        return ApiResponse.success({
            'totalDiscussions': total_discussions,
            'activeUsers': active_users,
            'todayPosts': today_posts,
            'totalReplies': total_replies,
            'categoryStats': {
                category.value: count for category, count in category_stats
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"获取社区统计失败: {e}")
        return ApiResponse.error('获取统计数据失败', 'GET_STATS_FAILED', 500)

@discussions_bp.route('/hot', methods=['GET'])
@limiter.limit("30 per minute")
@cache.cached(timeout=300, key_prefix='hot_discussions')
def get_hot_discussions():
    """获取热门讨论"""
    try:
        # 获取最近7天的热门讨论
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        hot_discussions = Discussion.query.filter(
            Discussion.created_at >= seven_days_ago
        ).order_by(
            desc(Discussion.is_pinned),
            desc(Discussion.is_hot),
            desc(
                Discussion.view_count * 0.3 + 
                Discussion.like_count * 0.4 + 
                Discussion.reply_count * 0.3
            )
        ).limit(10).all()
        
        return ApiResponse.success({
            'discussions': [discussion.to_dict() for discussion in hot_discussions]
        })
        
    except Exception as e:
        current_app.logger.error(f"获取热门讨论失败: {e}")
        return ApiResponse.error('获取热门讨论失败', 'GET_HOT_DISCUSSIONS_FAILED', 500)

@discussions_bp.route('/<int:discussion_id>', methods=['PUT'])
@jwt_required()
def update_discussion(discussion_id):
    """更新讨论（作者或管理员）"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return ApiResponse.error('用户不存在', 'USER_NOT_FOUND', 404)
        
        discussion = Discussion.query.get(discussion_id)
        if not discussion:
            return ApiResponse.error('讨论不存在', 'DISCUSSION_NOT_FOUND', 404)
        
        # 权限检查
        if discussion.author_id != user_id and user.role.value != 'admin':
            return ApiResponse.error('无权修改此讨论', 'PERMISSION_DENIED', 403)
        
        data = request.json
        
        # 更新允许的字段
        if 'title' in data and 5 <= len(data['title']) <= 200:
            discussion.title = data['title']
        
        if 'content' in data and len(data['content']) >= 50:
            discussion.content = data['content']
        
        if 'tags' in data and len(data['tags']) <= 5:
            discussion.tags = data['tags']
        
        discussion.updated_at = datetime.utcnow()
        db.session.commit()
        
        return ApiResponse.success({
            'discussion': discussion.to_dict(include_content=True)
        }, '讨论更新成功')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新讨论失败: {e}")
        return ApiResponse.error('更新讨论失败', 'UPDATE_DISCUSSION_FAILED', 500)

@discussions_bp.route('/<int:discussion_id>', methods=['DELETE'])
@jwt_required()
def delete_discussion(discussion_id):
    """删除讨论（作者或管理员）"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return ApiResponse.error('用户不存在', 'USER_NOT_FOUND', 404)
        
        discussion = Discussion.query.get(discussion_id)
        if not discussion:
            return ApiResponse.error('讨论不存在', 'DISCUSSION_NOT_FOUND', 404)
        
        # 权限检查
        if discussion.author_id != user_id and user.role.value != 'admin':
            return ApiResponse.error('无权删除此讨论', 'PERMISSION_DENIED', 403)
        
        # 删除讨论（级联删除回复）
        db.session.delete(discussion)
        db.session.commit()
        
        return ApiResponse.success(None, '讨论删除成功')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除讨论失败: {e}")
        return ApiResponse.error('删除讨论失败', 'DELETE_DISCUSSION_FAILED', 500)

@discussions_bp.route('/<int:discussion_id>/pin', methods=['POST'])
@jwt_required()
def toggle_pin_discussion(discussion_id):
    """置顶/取消置顶讨论（管理员）"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.role.value != 'admin':
            return ApiResponse.error('权限不足', 'PERMISSION_DENIED', 403)
        
        discussion = Discussion.query.get(discussion_id)
        if not discussion:
            return ApiResponse.error('讨论不存在', 'DISCUSSION_NOT_FOUND', 404)
        
        # 切换置顶状态
        discussion.is_pinned = not discussion.is_pinned
        discussion.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        action = '置顶' if discussion.is_pinned else '取消置顶'
        
        return ApiResponse.success({
            'isPinned': discussion.is_pinned
        }, f'讨论{action}成功')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"置顶操作失败: {e}")
        return ApiResponse.error('操作失败', 'PIN_FAILED', 500)

@discussions_bp.route('/<int:discussion_id>/lock', methods=['POST'])
@jwt_required()
def toggle_lock_discussion(discussion_id):
    """锁定/解锁讨论（管理员）"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.role.value != 'admin':
            return ApiResponse.error('权限不足', 'PERMISSION_DENIED', 403)
        
        discussion = Discussion.query.get(discussion_id)
        if not discussion:
            return ApiResponse.error('讨论不存在', 'DISCUSSION_NOT_FOUND', 404)
        
        # 切换锁定状态
        discussion.is_locked = not discussion.is_locked
        discussion.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        action = '锁定' if discussion.is_locked else '解锁'
        
        return ApiResponse.success({
            'isLocked': discussion.is_locked
        }, f'讨论{action}成功')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"锁定操作失败: {e}")
        return ApiResponse.error('操作失败', 'LOCK_FAILED', 500)
