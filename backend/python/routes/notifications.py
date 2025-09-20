"""
通知相关API路由
"""
from datetime import datetime

from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError
from sqlalchemy import desc

from config.database import db
from models.user import User
from models.notification import Notification, NotificationType
from utils.response import ApiResponse
from utils.decorators import limiter
from utils.pagination import paginate

notifications_bp = Blueprint('notifications', __name__)

class NotificationFilterSchema(Schema):
    """通知筛选参数验证"""
    page = fields.Int(load_default=1, validate=lambda x: x > 0)
    page_size = fields.Int(load_default=20, validate=lambda x: 1 <= x <= 100)
    type = fields.Str(validate=lambda x: x in ['like', 'reply', 'follow', 'mention', 'system', 'prediction_result'])
    read = fields.Bool()

@notifications_bp.route('', methods=['GET'])
@jwt_required()
@limiter.limit("60 per minute")
def get_notifications():
    """获取用户通知列表"""
    schema = NotificationFilterSchema()
    
    try:
        filters = schema.load(request.args)
    except ValidationError as err:
        return ApiResponse.error('参数验证失败', 'VALIDATION_ERROR', 400, err.messages)
    
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return ApiResponse.error('用户不存在', 'USER_NOT_FOUND', 404)
        
        # 构建查询
        query = Notification.query.filter_by(user_id=user_id)
        
        # 类型筛选
        if filters.get('type'):
            query = query.filter(Notification.type == NotificationType(filters['type']))
        
        # 已读状态筛选
        if filters.get('read') is not None:
            if filters['read']:
                query = query.filter(Notification.read_at.isnot(None))
            else:
                query = query.filter(Notification.read_at.is_(None))
        
        # 排序
        query = query.order_by(desc(Notification.created_at))
        
        # 分页
        page = filters.get('page', 1)
        page_size = filters.get('page_size', 20)
        
        paginated_notifications = paginate(query, page, page_size)
        
        # 获取未读通知数量
        unread_count = Notification.query.filter_by(
            user_id=user_id
        ).filter(Notification.read_at.is_(None)).count()
        
        return ApiResponse.success({
            'notifications': [notification.to_dict() for notification in paginated_notifications.items],
            'pagination': {
                'page': paginated_notifications.page,
                'pageSize': page_size,
                'total': paginated_notifications.total,
                'totalPages': paginated_notifications.pages,
                'hasNext': paginated_notifications.has_next,
                'hasPrev': paginated_notifications.has_prev
            },
            'unreadCount': unread_count
        })
        
    except Exception as e:
        current_app.logger.error(f"获取通知列表失败: {e}")
        return ApiResponse.error('获取通知列表失败', 'GET_NOTIFICATIONS_FAILED', 500)

@notifications_bp.route('/<int:notification_id>/read', methods=['PUT'])
@jwt_required()
@limiter.limit("60 per minute")
def mark_notification_read(notification_id):
    """标记通知为已读"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return ApiResponse.error('用户不存在', 'USER_NOT_FOUND', 404)
        
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=user_id
        ).first()
        
        if not notification:
            return ApiResponse.error('通知不存在', 'NOTIFICATION_NOT_FOUND', 404)
        
        # 标记为已读
        if not notification.read_at:
            notification.read_at = datetime.utcnow()
            db.session.commit()
        
        return ApiResponse.success({
            'notification': notification.to_dict()
        }, '通知已标记为已读')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"标记通知已读失败: {e}")
        return ApiResponse.error('操作失败', 'MARK_READ_FAILED', 500)

@notifications_bp.route('/read-all', methods=['PUT'])
@jwt_required()
@limiter.limit("10 per minute")
def mark_all_notifications_read():
    """标记所有通知为已读"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return ApiResponse.error('用户不存在', 'USER_NOT_FOUND', 404)
        
        # 更新所有未读通知
        updated_count = Notification.query.filter_by(
            user_id=user_id
        ).filter(Notification.read_at.is_(None)).update({
            'read_at': datetime.utcnow()
        })
        
        db.session.commit()
        
        return ApiResponse.success({
            'updatedCount': updated_count
        }, f'已标记 {updated_count} 条通知为已读')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"批量标记已读失败: {e}")
        return ApiResponse.error('操作失败', 'MARK_ALL_READ_FAILED', 500)

@notifications_bp.route('/<int:notification_id>', methods=['DELETE'])
@jwt_required()
@limiter.limit("30 per minute")
def delete_notification(notification_id):
    """删除通知"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return ApiResponse.error('用户不存在', 'USER_NOT_FOUND', 404)
        
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=user_id
        ).first()
        
        if not notification:
            return ApiResponse.error('通知不存在', 'NOTIFICATION_NOT_FOUND', 404)
        
        db.session.delete(notification)
        db.session.commit()
        
        return ApiResponse.success(None, '通知删除成功')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除通知失败: {e}")
        return ApiResponse.error('删除通知失败', 'DELETE_NOTIFICATION_FAILED', 500)

@notifications_bp.route('/settings', methods=['GET'])
@jwt_required()
def get_notification_settings():
    """获取通知设置"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return ApiResponse.error('用户不存在', 'USER_NOT_FOUND', 404)
        
        # 获取用户的通知设置
        settings = user.profile.notification_settings if user.profile else {}
        
        # 默认设置
        default_settings = {
            'emailNotifications': True,
            'pushNotifications': True,
            'likeNotifications': True,
            'replyNotifications': True,
            'followNotifications': True,
            'mentionNotifications': True,
            'systemNotifications': True,
            'predictionResultNotifications': True
        }
        
        # 合并默认设置和用户设置
        final_settings = {**default_settings, **settings}
        
        return ApiResponse.success({
            'settings': final_settings
        })
        
    except Exception as e:
        current_app.logger.error(f"获取通知设置失败: {e}")
        return ApiResponse.error('获取通知设置失败', 'GET_SETTINGS_FAILED', 500)

@notifications_bp.route('/settings', methods=['PUT'])
@jwt_required()
@limiter.limit("10 per minute")
def update_notification_settings():
    """更新通知设置"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return ApiResponse.error('用户不存在', 'USER_NOT_FOUND', 404)
        
        data = request.json
        
        # 验证设置数据
        valid_settings = [
            'emailNotifications', 'pushNotifications', 'likeNotifications',
            'replyNotifications', 'followNotifications', 'mentionNotifications',
            'systemNotifications', 'predictionResultNotifications'
        ]
        
        settings = {}
        for key, value in data.items():
            if key in valid_settings and isinstance(value, bool):
                settings[key] = value
        
        # 确保用户有profile
        if not user.profile:
            from models.user import UserProfile
            profile = UserProfile(user_id=user_id)
            db.session.add(profile)
            db.session.flush()
        
        # 更新通知设置
        user.profile.notification_settings = settings
        user.profile.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return ApiResponse.success({
            'settings': settings
        }, '通知设置更新成功')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新通知设置失败: {e}")
        return ApiResponse.error('更新设置失败', 'UPDATE_SETTINGS_FAILED', 500)
