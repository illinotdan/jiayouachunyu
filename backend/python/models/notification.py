"""
通知相关数据模型
"""
from celery import current_app

from .user import User
from ..config.database import db
from datetime import datetime, timedelta
import enum
from sqlalchemy.dialects.postgresql import JSONB

class NotificationType(enum.Enum):
    """通知类型枚举"""
    LIKE = 'like'
    REPLY = 'reply'
    FOLLOW = 'follow'
    MENTION = 'mention'
    SYSTEM = 'system'
    PREDICTION_RESULT = 'prediction_result'

class Notification(db.Model):
    """通知模型"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False, index=True)
    type = db.Column(db.Enum(NotificationType), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text)
    data = db.Column(JSONB, default=dict)  # 存储相关数据
    read_at = db.Column(db.DateTime, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # 关系
    user = db.relationship('User', backref='notifications')
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type.value,
            'title': self.title,
            'content': self.content,
            'data': self.data,
            'read': self.read_at is not None,
            'readAt': self.read_at.isoformat() if self.read_at else None,
            'createdAt': self.created_at.isoformat()
        }
    
    @classmethod
    def create_like_notification(cls, user_id, liker_id, content_type, content_id, content_title):
        """创建点赞通知"""
        from ..models.user import User
        
        liker = User.query.get(liker_id)
        if not liker:
            return None
        
        notification = cls(
            user_id=user_id,
            type=NotificationType.LIKE,
            title=f'{liker.username} 赞了你的{content_type}',
            content=f'你的{content_type}《{content_title}》收到了新的赞',
            data={
                'likerId': liker_id,
                'likerName': liker.username,
                'contentType': content_type,
                'contentId': content_id,
                'contentTitle': content_title
            }
        )
        
        db.session.add(notification)
        return notification
    
    @classmethod
    def create_reply_notification(cls, user_id, replier_id, discussion_id, discussion_title):
        """创建回复通知"""
        from ..models.user import User
        
        replier = User.query.get(replier_id)
        if not replier:
            return None
        
        notification = cls(
            user_id=user_id,
            type=NotificationType.REPLY,
            title=f'{replier.username} 回复了你的讨论',
            content=f'你的讨论《{discussion_title}》有新的回复',
            data={
                'replierId': replier_id,
                'replierName': replier.username,
                'discussionId': discussion_id,
                'discussionTitle': discussion_title
            }
        )
        
        db.session.add(notification)
        return notification
    
    @classmethod
    def create_follow_notification(cls, user_id, follower_id):
        """创建关注通知"""
        from ..models.user import User
        
        follower = User.query.get(follower_id)
        if not follower:
            return None
        
        notification = cls(
            user_id=user_id,
            type=NotificationType.FOLLOW,
            title=f'{follower.username} 关注了你',
            content=f'{follower.username} 开始关注你，快去看看吧！',
            data={
                'followerId': follower_id,
                'followerName': follower.username,
                'followerAvatar': follower.avatar_url
            }
        )
        
        db.session.add(notification)
        return notification
    
    @classmethod
    def create_mention_notification(cls, user_id, mentioner_id, content_type, content_id, content_title):
        """创建提及通知"""
        from ..models.user import User
        
        mentioner = User.query.get(mentioner_id)
        if not mentioner:
            return None
        
        notification = cls(
            user_id=user_id,
            type=NotificationType.MENTION,
            title=f'{mentioner.username} 在{content_type}中提到了你',
            content=f'你在《{content_title}》中被提及',
            data={
                'mentionerId': mentioner_id,
                'mentionerName': mentioner.username,
                'contentType': content_type,
                'contentId': content_id,
                'contentTitle': content_title
            }
        )
        
        db.session.add(notification)
        return notification
    
    @classmethod
    def create_system_notification(cls, user_id, title, content, data=None):
        """创建系统通知"""
        notification = cls(
            user_id=user_id,
            type=NotificationType.SYSTEM,
            title=title,
            content=content,
            data=data or {}
        )
        
        db.session.add(notification)
        return notification
    
    @classmethod
    def create_prediction_result_notification(cls, user_id, prediction_id, match_title, is_correct):
        """创建预测结果通知"""
        result_text = '正确' if is_correct else '错误'
        emoji = '🎉' if is_correct else '😔'
        
        notification = cls(
            user_id=user_id,
            type=NotificationType.PREDICTION_RESULT,
            title=f'{emoji} 预测结果：{result_text}',
            content=f'你对《{match_title}》的预测结果是{result_text}',
            data={
                'predictionId': prediction_id,
                'matchTitle': match_title,
                'isCorrect': is_correct
            }
        )
        
        db.session.add(notification)
        return notification
    
    @classmethod
    def cleanup_old_notifications(cls, days=30):
        """清理旧通知"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        deleted_count = cls.query.filter(
            cls.created_at < cutoff_date
        ).delete()
        
        db.session.commit()
        return deleted_count
    
    @classmethod
    def get_unread_count(cls, user_id):
        """获取未读通知数量"""
        return cls.query.filter_by(user_id=user_id).filter(
            cls.read_at.is_(None)
        ).count()

class NotificationService:
    """通知服务类"""
    
    @staticmethod
    def send_notification(user_id, notification_type, title, content, data=None, send_email=False, send_push=False):
        """发送通知"""
        try:
            # 检查用户通知设置
            from ..models.user import User
            user = User.query.get(user_id)
            
            if not user:
                return False
            
            # 检查用户是否启用了此类型的通知
            settings = user.profile.notification_settings if user.profile else {}
            
            notification_key = f'{notification_type.value}Notifications'
            if not settings.get(notification_key, True):
                return False  # 用户关闭了此类型通知
            
            # 创建数据库通知
            notification = Notification(
                user_id=user_id,
                type=notification_type,
                title=title,
                content=content,
                data=data or {}
            )
            
            db.session.add(notification)
            db.session.commit()
            
            # 发送邮件通知
            if send_email and settings.get('emailNotifications', True):
                NotificationService.send_email_notification(user, title, content)
            
            # 发送推送通知
            if send_push and settings.get('pushNotifications', True):
                NotificationService.send_push_notification(user, title, content)
            
            return True
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"发送通知失败: {e}")
            return False
    
    @staticmethod
    def send_email_notification(user, title, content):
        """发送邮件通知"""
        try:
            from flask_mail import Message, Mail
            
            mail = Mail(current_app)
            
            msg = Message(
                subject=f'[刀塔解析] {title}',
                recipients=[user.email],
                body=content,
                html=f'''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #4299e1;">{title}</h2>
                    <p>{content}</p>
                    <hr>
                    <p style="color: #666; font-size: 12px;">
                        这是来自刀塔解析的通知邮件。如不想接收邮件通知，请在设置中关闭。
                    </p>
                </div>
                '''
            )
            
            mail.send(msg)
            return True
            
        except Exception as e:
            current_app.logger.error(f"发送邮件通知失败: {e}")
            return False
    
    @staticmethod
    def send_push_notification(user, title, content):
        """发送推送通知"""
        # TODO: 实现推送通知（如使用Firebase、极光推送等）
        pass
    
    @staticmethod
    def broadcast_system_notification(title, content, user_filter=None):
        """广播系统通知"""
        try:
            # 获取目标用户
            query = User.query.filter_by(is_active=True)
            
            if user_filter:
                if user_filter.get('role'):
                    query = query.filter_by(role=user_filter['role'])
                if user_filter.get('tier'):
                    query = query.filter_by(tier=user_filter['tier'])
            
            users = query.all()
            
            # 批量创建通知
            notifications = []
            for user in users:
                notification = Notification(
                    user_id=user.id,
                    type=NotificationType.SYSTEM,
                    title=title,
                    content=content
                )
                notifications.append(notification)
            
            db.session.add_all(notifications)
            db.session.commit()
            
            return len(notifications)
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"广播通知失败: {e}")
            return 0
