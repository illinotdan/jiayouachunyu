"""
用户相关数据模型
"""

from config.database import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import enum
from sqlalchemy.dialects.postgresql import JSONB, ARRAY

class UserRole(enum.Enum):
    """用户角色枚举"""
    USER = 'user'
    EXPERT = 'expert'
    ADMIN = 'admin'
    MODERATOR = 'moderator'

class ExpertTier(enum.Enum):
    """专家等级枚举"""
    BRONZE = 'bronze'
    SILVER = 'silver'
    GOLD = 'gold'
    PLATINUM = 'platinum'
    DIAMOND = 'diamond'

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.BigInteger, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    avatar_url = db.Column(db.Text)
    role = db.Column(db.Enum(UserRole), default=UserRole.USER, nullable=False, index=True)
    tier = db.Column(db.Enum(ExpertTier), default=ExpertTier.BRONZE, index=True)
    verified = db.Column(db.Boolean, default=False, nullable=False)
    reputation = db.Column(db.Integer, default=0, nullable=False)
    bio = db.Column(db.Text)
    steam_id = db.Column(db.String(50), unique=True, index=True)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = db.Column(db.DateTime)
    
    # 状态
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # 关系
    articles = db.relationship('Article', backref='author', lazy='dynamic')
    discussions = db.relationship('Discussion', backref='author', lazy='dynamic')
    predictions = db.relationship('ExpertPrediction', backref='expert', lazy='dynamic')
    
    # 关注关系
    following = db.relationship(
        'UserFollow', 
        foreign_keys='UserFollow.follower_id',
        backref='follower', 
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    followers = db.relationship(
        'UserFollow',
        foreign_keys='UserFollow.following_id', 
        backref='following_user',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def follow(self, user):
        """关注用户"""
        if not self.is_following(user):
            follow = UserFollow(follower_id=self.id, following_id=user.id)
            db.session.add(follow)
            return True
        return False
    
    def unfollow(self, user):
        """取消关注"""
        follow = self.following.filter_by(following_id=user.id).first()
        if follow:
            db.session.delete(follow)
            return True
        return False
    
    def is_following(self, user):
        """检查是否已关注"""
        return self.following.filter_by(following_id=user.id).first() is not None
    
    def get_follower_count(self):
        """获取关注者数量"""
        return self.followers.count()
    
    def get_following_count(self):
        """获取关注数量"""
        return self.following.count()
    
    def get_article_count(self):
        """获取文章数量"""
        return self.articles.filter_by(status='published').count()
    
    def get_prediction_accuracy(self):
        """获取预测准确率"""
        total_predictions = self.predictions.filter(
            ExpertPrediction.result.in_(['correct', 'incorrect'])
        ).count()
        
        if total_predictions == 0:
            return 0.0
        
        correct_predictions = self.predictions.filter_by(result='correct').count()
        return round((correct_predictions / total_predictions) * 100, 2)
    
    def to_dict(self, include_sensitive=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'username': self.username,
            'avatar': self.avatar_url,
            'role': self.role.value,
            'tier': self.tier.value if self.tier else None,
            'verified': self.verified,
            'reputation': self.reputation,
            'bio': self.bio,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'lastLoginAt': self.last_login_at.isoformat() if self.last_login_at else None,
            'stats': {
                'followers': self.get_follower_count(),
                'following': self.get_following_count(),
                'articles': self.get_article_count(),
                'accuracy': self.get_prediction_accuracy()
            }
        }
        
        if include_sensitive:
            data['email'] = self.email
            data['steamId'] = self.steam_id
        
        return data
    
    def __repr__(self):
        return f'<User {self.username}>'

class UserProfile(db.Model):
    """用户资料扩展"""
    __tablename__ = 'user_profiles'
    
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), primary_key=True)
    display_name = db.Column(db.String(100))
    location = db.Column(db.String(100))
    timezone = db.Column(db.String(50))
    language = db.Column(db.String(10), default='zh-CN')
    notification_settings = db.Column(JSONB, default=dict)
    privacy_settings = db.Column(JSONB, default=dict)
    social_links = db.Column(JSONB, default=dict)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = db.relationship('User', backref=db.backref('profile', uselist=False))

class UserSession(db.Model):
    """用户会话"""
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False, index=True)
    token_hash = db.Column(db.String(255), nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    user = db.relationship('User', backref='sessions')
    
    @classmethod
    def cleanup_expired(cls):
        """清理过期会话"""
        expired_sessions = cls.query.filter(cls.expires_at < datetime.utcnow()).all()
        for session in expired_sessions:
            db.session.delete(session)
        db.session.commit()
        return len(expired_sessions)

class UserFollow(db.Model):
    """用户关注关系"""
    __tablename__ = 'user_follows'
    
    id = db.Column(db.BigInteger, primary_key=True)
    follower_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    following_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 唯一约束
    __table_args__ = (
        db.UniqueConstraint('follower_id', 'following_id', name='unique_follow'),
    )
    
    # 索引
    __table_args__ = (
        db.Index('idx_user_follows_follower', 'follower_id'),
        db.Index('idx_user_follows_following', 'following_id'),
    )

class ExpertApplication(db.Model):
    """专家申请"""
    __tablename__ = 'expert_applications'
    
    class Status(enum.Enum):
        PENDING = 'pending'
        APPROVED = 'approved'
        REJECTED = 'rejected'
        UNDER_REVIEW = 'under_review'
    
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    expertise_areas = db.Column(ARRAY(db.String), nullable=False)
    bio = db.Column(db.Text, nullable=False)
    experience_years = db.Column(db.Integer)
    portfolio_links = db.Column(ARRAY(db.String))
    social_proof = db.Column(db.Text)
    status = db.Column(db.Enum(Status), default=Status.PENDING, nullable=False)
    reviewer_id = db.Column(db.BigInteger, db.ForeignKey('users.id'))
    review_notes = db.Column(db.Text)
    
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    
    # 关系
    user = db.relationship('User', foreign_keys=[user_id], backref='expert_application')
    reviewer = db.relationship('User', foreign_keys=[reviewer_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'user': self.user.to_dict(),
            'expertiseAreas': self.expertise_areas,
            'bio': self.bio,
            'experienceYears': self.experience_years,
            'portfolioLinks': self.portfolio_links,
            'socialProof': self.social_proof,
            'status': self.status.value,
            'reviewNotes': self.review_notes,
            'appliedAt': self.applied_at.isoformat(),
            'reviewedAt': self.reviewed_at.isoformat() if self.reviewed_at else None
        }
