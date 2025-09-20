"""
管理员相关API路由
"""
import os

from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError
from sqlalchemy import desc, func
from datetime import datetime, timedelta

from ..config.database import db
from ..models.user import User, UserRole, ExpertApplication, ExpertTier
from ..models.content import Discussion, Article, ContentView
from ..models.match import Match
from ..models.notification import NotificationService, NotificationType
from ..utils.response import ApiResponse
from ..utils.decorators import limiter, admin_required
from ..utils.pagination import paginate

admin_bp = Blueprint('admin', __name__)

class UserManagementSchema(Schema):
    """用户管理参数验证"""
    action = fields.Str(required=True, validate=lambda x: x in ['activate', 'deactivate', 'verify', 'unverify', 'promote', 'demote'])
    reason = fields.Str()

class ContentModerationSchema(Schema):
    """内容审核参数验证"""
    action = fields.Str(required=True, validate=lambda x: x in ['approve', 'reject', 'delete', 'pin', 'unpin', 'lock', 'unlock'])
    reason = fields.Str()

@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
@limiter.limit("30 per minute")
def get_admin_dashboard():
    """获取管理员仪表板数据"""
    try:
        # 获取基础统计
        total_users = User.query.count()
        total_experts = User.query.filter(User.role.in_([UserRole.EXPERT, UserRole.ADMIN])).count()
        total_discussions = Discussion.query.count()
        total_articles = Article.query.filter_by(status='published').count()
        total_matches = Match.query.count()
        
        # 待处理事项
        pending_applications = ExpertApplication.query.filter_by(
            status=ExpertApplication.Status.PENDING
        ).count()
        
        # 最近24小时活动
        yesterday = datetime.utcnow() - timedelta(hours=24)
        
        recent_registrations = User.query.filter(User.created_at >= yesterday).count()
        recent_discussions = Discussion.query.filter(Discussion.created_at >= yesterday).count()
        recent_articles = Article.query.filter(
            Article.created_at >= yesterday,
            Article.status == 'published'
        ).count()
        
        # 最近7天的用户活跃度
        week_ago = datetime.utcnow() - timedelta(days=7)
        active_users = db.session.query(
            func.count(func.distinct(ContentView.user_id))
        ).filter(
            ContentView.created_at >= week_ago,
            ContentView.user_id.isnot(None)
        ).scalar()
        
        # 热门内容
        hot_discussions = Discussion.query.filter(
            Discussion.created_at >= week_ago
        ).order_by(
            desc(Discussion.view_count + Discussion.like_count * 2 + Discussion.reply_count * 3)
        ).limit(5).all()
        
        # 系统健康状态
        system_health = {
            'database': 'healthy',  # TODO: 实际健康检查
            'redis': 'healthy',
            'storage': 'healthy'
        }
        
        return ApiResponse.success({
            'overview': {
                'totalUsers': total_users,
                'totalExperts': total_experts,
                'totalDiscussions': total_discussions,
                'totalArticles': total_articles,
                'totalMatches': total_matches
            },
            'pending': {
                'expertApplications': pending_applications
            },
            'recentActivity': {
                'registrations': recent_registrations,
                'discussions': recent_discussions,
                'articles': recent_articles,
                'activeUsers': active_users
            },
            'hotContent': {
                'discussions': [d.to_dict() for d in hot_discussions]
            },
            'systemHealth': system_health,
            'lastUpdated': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"获取管理员仪表板失败: {e}")
        return ApiResponse.error('获取仪表板数据失败', 'GET_DASHBOARD_FAILED', 500)

@admin_bp.route('/users', methods=['GET'])
@admin_required
@limiter.limit("30 per minute")
def get_users_management():
    """获取用户管理列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = min(request.args.get('page_size', 20, type=int), 100)
        role_filter = request.args.get('role')
        search = request.args.get('search')
        
        # 构建查询
        query = User.query
        
        if role_filter:
            query = query.filter_by(role=UserRole(role_filter))
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    User.username.ilike(search_term),
                    User.email.ilike(search_term)
                )
            )
        
        query = query.order_by(desc(User.created_at))
        
        paginated_users = paginate(query, page, page_size)
        
        return ApiResponse.success({
            'users': [user.to_dict(include_sensitive=True) for user in paginated_users.items],
            'pagination': {
                'page': paginated_users.page,
                'pageSize': page_size,
                'total': paginated_users.total,
                'totalPages': paginated_users.pages
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"获取用户管理列表失败: {e}")
        return ApiResponse.error('获取用户列表失败', 'GET_USERS_FAILED', 500)

@admin_bp.route('/users/<int:user_id>/manage', methods=['PUT'])
@admin_required
@limiter.limit("20 per minute")
def manage_user(user_id):
    """管理用户（激活/禁用/验证等）"""
    schema = UserManagementSchema()
    
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return ApiResponse.error('参数验证失败', 'VALIDATION_ERROR', 400, err.messages)
    
    try:
        admin_id = get_jwt_identity()
        admin = User.query.get(admin_id)
        
        target_user = User.query.get(user_id)
        if not target_user:
            return ApiResponse.error('用户不存在', 'USER_NOT_FOUND', 404)
        
        action = data['action']
        reason = data.get('reason', '')
        
        # 执行管理操作
        if action == 'activate':
            target_user.is_active = True
            message = '用户已激活'
        elif action == 'deactivate':
            target_user.is_active = False
            message = '用户已禁用'
        elif action == 'verify':
            target_user.verified = True
            message = '用户已验证'
        elif action == 'unverify':
            target_user.verified = False
            message = '用户验证已取消'
        elif action == 'promote':
            if target_user.role == UserRole.USER:
                target_user.role = UserRole.EXPERT
                target_user.tier = ExpertTier.SILVER
                message = '用户已提升为专家'
            else:
                return ApiResponse.error('用户已经是专家或管理员', 'INVALID_PROMOTION', 400)
        elif action == 'demote':
            if target_user.role == UserRole.EXPERT:
                target_user.role = UserRole.USER
                message = '专家已降级为普通用户'
            else:
                return ApiResponse.error('只能降级专家用户', 'INVALID_DEMOTION', 400)
        
        target_user.updated_at = datetime.utcnow()
        
        # 记录管理操作日志
        from ..models.audit import AuditLog
        audit_log = AuditLog(
            user_id=admin_id,
            action=f'user_{action}',
            resource_type='user',
            resource_id=user_id,
            details={
                'action': action,
                'reason': reason,
                'target_user': target_user.username
            }
        )
        db.session.add(audit_log)
        
        # 发送通知给目标用户
        NotificationService.send_notification(
            user_id=user_id,
            notification_type=NotificationType.SYSTEM,
            title=f'账号状态更新',
            content=f'您的账号状态已更新：{message}' + (f'。原因：{reason}' if reason else ''),
            data={'action': action, 'reason': reason}
        )
        
        db.session.commit()
        
        return ApiResponse.success({
            'user': target_user.to_dict(),
            'action': action
        }, message)
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"用户管理操作失败: {e}")
        return ApiResponse.error('管理操作失败', 'USER_MANAGEMENT_FAILED', 500)

@admin_bp.route('/expert-applications', methods=['GET'])
@admin_required
@limiter.limit("30 per minute")
def get_expert_applications():
    """获取专家申请列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = min(request.args.get('page_size', 20, type=int), 100)
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
        current_app.logger.error(f"获取专家申请列表失败: {e}")
        return ApiResponse.error('获取申请列表失败', 'GET_APPLICATIONS_FAILED', 500)

@admin_bp.route('/expert-applications/<int:application_id>', methods=['PUT'])
@admin_required
@limiter.limit("20 per minute")
def review_expert_application(application_id):
    """审核专家申请"""
    try:
        admin_id = get_jwt_identity()
        
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
                applicant.tier = ExpertTier.SILVER
                applicant.verified = True
                
                # 发送批准通知
                NotificationService.send_notification(
                    user_id=applicant.id,
                    notification_type=NotificationType.SYSTEM,
                    title='🎉 专家申请已通过',
                    content='恭喜！您的专家申请已通过审核，现在您可以发布专业分析和预测了。',
                    data={'applicationId': application_id},
                    send_email=True
                )
        else:
            application.status = ExpertApplication.Status.REJECTED
            
            # 发送拒绝通知
            applicant = User.query.get(application.user_id)
            if applicant:
                NotificationService.send_notification(
                    user_id=applicant.id,
                    notification_type=NotificationType.SYSTEM,
                    title='专家申请未通过',
                    content=f'很抱歉，您的专家申请未通过审核。{review_notes}',
                    data={'applicationId': application_id, 'reason': review_notes}
                )
        
        application.reviewer_id = admin_id
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

@admin_bp.route('/content/reports', methods=['GET'])
@admin_required
@limiter.limit("30 per minute")
def get_content_reports():
    """获取内容举报列表"""
    try:
        # TODO: 实现内容举报系统
        return ApiResponse.success({
            'reports': [],
            'message': '内容举报系统开发中'
        })
        
    except Exception as e:
        current_app.logger.error(f"获取内容举报失败: {e}")
        return ApiResponse.error('获取举报列表失败', 'GET_REPORTS_FAILED', 500)

@admin_bp.route('/content/<string:content_type>/<int:content_id>/moderate', methods=['PUT'])
@admin_required
@limiter.limit("20 per minute")
def moderate_content(content_type, content_id):
    """内容审核"""
    schema = ContentModerationSchema()
    
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return ApiResponse.error('参数验证失败', 'VALIDATION_ERROR', 400, err.messages)
    
    try:
        admin_id = get_jwt_identity()
        action = data['action']
        reason = data.get('reason', '')
        
        # 根据内容类型执行操作
        if content_type == 'discussion':
            content = Discussion.query.get(content_id)
            if not content:
                return ApiResponse.error('讨论不存在', 'DISCUSSION_NOT_FOUND', 404)
            
            if action == 'delete':
                db.session.delete(content)
                message = '讨论已删除'
            elif action == 'pin':
                content.is_pinned = True
                message = '讨论已置顶'
            elif action == 'unpin':
                content.is_pinned = False
                message = '讨论已取消置顶'
            elif action == 'lock':
                content.is_locked = True
                message = '讨论已锁定'
            elif action == 'unlock':
                content.is_locked = False
                message = '讨论已解锁'
            
        elif content_type == 'article':
            content = Article.query.get(content_id)
            if not content:
                return ApiResponse.error('文章不存在', 'ARTICLE_NOT_FOUND', 404)
            
            if action == 'delete':
                content.status = 'deleted'
                message = '文章已删除'
            elif action == 'approve':
                content.status = 'published'
                message = '文章已发布'
            elif action == 'reject':
                content.status = 'archived'
                message = '文章已归档'
        
        else:
            return ApiResponse.error('不支持的内容类型', 'INVALID_CONTENT_TYPE', 400)
        
        # 记录审核日志
        from ..models.audit import AuditLog
        audit_log = AuditLog(
            user_id=admin_id,
            action=f'moderate_{content_type}',
            resource_type=content_type,
            resource_id=content_id,
            details={
                'action': action,
                'reason': reason
            }
        )
        db.session.add(audit_log)
        
        # 如果是删除操作，通知内容作者
        if action == 'delete' and hasattr(content, 'author_id'):
            NotificationService.send_notification(
                user_id=content.author_id,
                notification_type=NotificationType.SYSTEM,
                title='内容被删除',
                content=f'您的{content_type}因违反社区规则被删除。' + (f'原因：{reason}' if reason else ''),
                data={
                    'contentType': content_type,
                    'contentId': content_id,
                    'action': action,
                    'reason': reason
                }
            )
        
        db.session.commit()
        
        return ApiResponse.success({
            'contentType': content_type,
            'contentId': content_id,
            'action': action
        }, message)
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"内容审核失败: {e}")
        return ApiResponse.error('审核失败', 'MODERATION_FAILED', 500)

@admin_bp.route('/system/broadcast', methods=['POST'])
@admin_required
@limiter.limit("5 per hour")
def broadcast_notification():
    """广播系统通知"""
    try:
        data = request.json
        title = data.get('title')
        content = data.get('content')
        target_filter = data.get('targetFilter', {})
        
        if not title or not content:
            return ApiResponse.error('标题和内容不能为空', 'MISSING_REQUIRED_FIELDS', 400)
        
        # 广播通知
        sent_count = NotificationService.broadcast_system_notification(
            title=title,
            content=content,
            user_filter=target_filter
        )
        
        return ApiResponse.success({
            'sentCount': sent_count
        }, f'系统通知已发送给 {sent_count} 个用户')
        
    except Exception as e:
        current_app.logger.error(f"广播通知失败: {e}")
        return ApiResponse.error('广播失败', 'BROADCAST_FAILED', 500)

@admin_bp.route('/system/stats', methods=['GET'])
@admin_required
@limiter.limit("10 per minute")
def get_system_stats():
    """获取系统统计信息"""
    try:
        # 数据库统计
        from ..config.database import DatabaseManager
        db_stats = DatabaseManager.get_database_stats()
        
        # 缓存统计
        from flask import current_app
        cache_stats = {
            'hits': 0,  # TODO: 实现缓存统计
            'misses': 0,
            'size': 0
        }
        
        # 文件存储统计
        upload_folder = current_app.config['UPLOAD_FOLDER']
        storage_stats = {
            'totalFiles': 0,
            'totalSize': 0
        }
        
        if os.path.exists(upload_folder):
            for root, dirs, files in os.walk(upload_folder):
                storage_stats['totalFiles'] += len(files)
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        storage_stats['totalSize'] += os.path.getsize(file_path)
                    except:
                        pass
        
        return ApiResponse.success({
            'database': db_stats,
            'cache': cache_stats,
            'storage': storage_stats,
            'lastUpdated': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"获取系统统计失败: {e}")
        return ApiResponse.error('获取系统统计失败', 'GET_SYSTEM_STATS_FAILED', 500)
