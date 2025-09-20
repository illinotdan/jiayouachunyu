"""
审计日志数据模型
"""

from ..config.database import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB, INET

class AuditLog(db.Model):
    """审计日志模型"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), index=True)
    action = db.Column(db.String(100), nullable=False, index=True)
    resource_type = db.Column(db.String(50), index=True)
    resource_id = db.Column(db.BigInteger, index=True)
    old_values = db.Column(JSONB)
    new_values = db.Column(JSONB)
    details = db.Column(JSONB, default=dict)
    ip_address = db.Column(INET)
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # 关系
    user = db.relationship('User', backref='audit_logs')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user': self.user.to_dict() if self.user else None,
            'action': self.action,
            'resourceType': self.resource_type,
            'resourceId': self.resource_id,
            'oldValues': self.old_values,
            'newValues': self.new_values,
            'details': self.details,
            'ipAddress': str(self.ip_address) if self.ip_address else None,
            'userAgent': self.user_agent,
            'createdAt': self.created_at.isoformat()
        }
    
    @classmethod
    def log_action(cls, user_id, action, resource_type=None, resource_id=None, 
                   old_values=None, new_values=None, details=None, request=None):
        """记录操作日志"""
        try:
            log = cls(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                old_values=old_values,
                new_values=new_values,
                details=details or {}
            )
            
            if request:
                log.ip_address = request.remote_addr
                log.user_agent = request.headers.get('User-Agent')
            
            db.session.add(log)
            return log
            
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"记录审计日志失败: {e}")
            return None

class DailyStats(db.Model):
    """每日统计模型"""
    __tablename__ = 'daily_stats'
    
    id = db.Column(db.BigInteger, primary_key=True)
    stat_date = db.Column(db.Date, nullable=False, unique=True, index=True)
    total_users = db.Column(db.Integer, default=0)
    active_users = db.Column(db.Integer, default=0)
    new_users = db.Column(db.Integer, default=0)
    total_matches = db.Column(db.Integer, default=0)
    new_discussions = db.Column(db.Integer, default=0)
    new_articles = db.Column(db.Integer, default=0)
    page_views = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'date': self.stat_date.isoformat(),
            'totalUsers': self.total_users,
            'activeUsers': self.active_users,
            'newUsers': self.new_users,
            'totalMatches': self.total_matches,
            'newDiscussions': self.new_discussions,
            'newArticles': self.new_articles,
            'pageViews': self.page_views
        }
    
    @classmethod
    def calculate_daily_stats(cls, target_date=None):
        """计算指定日期的统计数据"""
        if target_date is None:
            target_date = datetime.utcnow().date()
        
        try:
            # 检查是否已存在该日期的统计
            existing_stat = cls.query.filter_by(stat_date=target_date).first()
            if existing_stat:
                return existing_stat
            
            # 计算统计数据
            day_start = datetime.combine(target_date, datetime.min.time())
            day_end = datetime.combine(target_date, datetime.max.time())
            
            # 用户统计
            total_users = User.query.filter(User.created_at <= day_end).count()
            new_users = User.query.filter(
                User.created_at >= day_start,
                User.created_at <= day_end
            ).count()
            
            # 活跃用户（当天有活动的用户）
            from models.content import ContentView
            active_users = db.session.query(
                func.count(func.distinct(ContentView.user_id))
            ).filter(
                ContentView.created_at >= day_start,
                ContentView.created_at <= day_end,
                ContentView.user_id.isnot(None)
            ).scalar()
            
            # 内容统计
            from models.content import Discussion, Article
            new_discussions = Discussion.query.filter(
                Discussion.created_at >= day_start,
                Discussion.created_at <= day_end
            ).count()
            
            new_articles = Article.query.filter(
                Article.created_at >= day_start,
                Article.created_at <= day_end,
                Article.status == 'published'
            ).count()
            
            # 比赛统计
            from models.match import Match
            total_matches = Match.query.filter(Match.created_at <= day_end).count()
            
            # 页面浏览统计
            page_views = ContentView.query.filter(
                ContentView.created_at >= day_start,
                ContentView.created_at <= day_end
            ).count()
            
            # 创建统计记录
            daily_stat = cls(
                stat_date=target_date,
                total_users=total_users,
                active_users=active_users,
                new_users=new_users,
                total_matches=total_matches,
                new_discussions=new_discussions,
                new_articles=new_articles,
                page_views=page_views
            )
            
            db.session.add(daily_stat)
            db.session.commit()
            
            return daily_stat
            
        except Exception as e:
            db.session.rollback()
            from flask import current_app
            current_app.logger.error(f"计算每日统计失败: {e}")
            return None
