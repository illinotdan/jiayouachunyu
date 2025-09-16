"""
内容相关数据模型
"""

from config.database import db
from datetime import datetime
import enum
from sqlalchemy.dialects.postgresql import JSONB, ARRAY

class ContentType(enum.Enum):
    """内容类型枚举"""
    ARTICLE = 'article'
    DISCUSSION = 'discussion'
    REPLY = 'reply'
    PREDICTION = 'prediction'

class ArticleCategory(enum.Enum):
    """文章分类枚举"""
    ANALYSIS = 'analysis'
    PREDICTION = 'prediction'
    STRATEGY = 'strategy'
    NEWS = 'news'
    GUIDE = 'guide'

class ArticleStatus(enum.Enum):
    """文章状态枚举"""
    DRAFT = 'draft'
    PUBLISHED = 'published'
    ARCHIVED = 'archived'
    DELETED = 'deleted'

class DiscussionCategory(enum.Enum):
    """讨论分类枚举"""
    ANALYSIS = 'analysis'
    PREDICTION = 'prediction'
    STRATEGY = 'strategy'
    NEWS = 'news'
    GENERAL = 'general'

class Article(db.Model):
    """文章模型"""
    __tablename__ = 'articles'
    
    id = db.Column(db.BigInteger, primary_key=True)
    author_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text)
    category = db.Column(db.Enum(ArticleCategory), default=ArticleCategory.ANALYSIS, index=True)
    tags = db.Column(ARRAY(db.String), default=list)
    match_id = db.Column(db.BigInteger, db.ForeignKey('matches.id'))
    status = db.Column(db.Enum(ArticleStatus), default=ArticleStatus.PUBLISHED, nullable=False, index=True)
    
    # 统计数据
    view_count = db.Column(db.Integer, default=0)
    like_count = db.Column(db.Integer, default=0)
    comment_count = db.Column(db.Integer, default=0)
    featured = db.Column(db.Boolean, default=False)
    
    published_at = db.Column(db.DateTime, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    match = db.relationship('Match', backref='articles')
    
    def to_dict(self, include_content=False):
        data = {
            'id': self.id,
            'title': self.title,
            'summary': self.summary,
            'author': self.author.to_dict(),
            'category': self.category.value,
            'tags': self.tags,
            'status': self.status.value,
            'viewCount': self.view_count,
            'likeCount': self.like_count,
            'commentCount': self.comment_count,
            'featured': self.featured,
            'publishedAt': self.published_at.isoformat() if self.published_at else None,
            'createdAt': self.created_at.isoformat(),
            'updatedAt': self.updated_at.isoformat()
        }
        
        if include_content:
            data['content'] = self.content
        
        if self.match:
            data['match'] = self.match.to_dict()
        
        return data

class Discussion(db.Model):
    """讨论模型"""
    __tablename__ = 'discussions'
    
    id = db.Column(db.BigInteger, primary_key=True)
    author_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.Enum(DiscussionCategory), default=DiscussionCategory.GENERAL, index=True)
    tags = db.Column(ARRAY(db.String), default=list)
    
    # 统计数据
    view_count = db.Column(db.Integer, default=0)
    like_count = db.Column(db.Integer, default=0)
    reply_count = db.Column(db.Integer, default=0)
    
    # 状态标识
    last_activity_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    is_hot = db.Column(db.Boolean, default=False)
    is_pinned = db.Column(db.Boolean, default=False)
    is_locked = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    replies = db.relationship('DiscussionReply', backref='discussion', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self, include_content=False):
        data = {
            'id': self.id,
            'title': self.title,
            'author': self.author.to_dict(),
            'category': self.category.value,
            'tags': self.tags,
            'viewCount': self.view_count,
            'likeCount': self.like_count,
            'replyCount': self.reply_count,
            'lastActivity': self.last_activity_at.isoformat(),
            'isHot': self.is_hot,
            'isPinned': self.is_pinned,
            'isLocked': self.is_locked,
            'createdAt': self.created_at.isoformat(),
            'updatedAt': self.updated_at.isoformat()
        }
        
        if include_content:
            data['content'] = self.content
        
        return data
    
    def update_activity(self):
        """更新最后活动时间"""
        self.last_activity_at = datetime.utcnow()
        db.session.commit()

class DiscussionReply(db.Model):
    """讨论回复模型"""
    __tablename__ = 'discussion_replies'
    
    id = db.Column(db.BigInteger, primary_key=True)
    discussion_id = db.Column(db.BigInteger, db.ForeignKey('discussions.id'), nullable=False, index=True)
    author_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False, index=True)
    parent_id = db.Column(db.BigInteger, db.ForeignKey('discussion_replies.id'), index=True)
    content = db.Column(db.Text, nullable=False)
    like_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    parent = db.relationship('DiscussionReply', remote_side=[id], backref='children')
    
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'author': self.author.to_dict(),
            'parentId': self.parent_id,
            'likeCount': self.like_count,
            'createdAt': self.created_at.isoformat(),
            'updatedAt': self.updated_at.isoformat()
        }

class ContentLike(db.Model):
    """内容点赞模型"""
    __tablename__ = 'content_likes'
    
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False, index=True)
    content_type = db.Column(db.Enum(ContentType), nullable=False)
    content_id = db.Column(db.BigInteger, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 唯一约束
    __table_args__ = (
        db.UniqueConstraint('user_id', 'content_type', 'content_id', name='unique_content_like'),
        db.Index('idx_content_likes_content', 'content_type', 'content_id'),
    )
    
    @classmethod
    def toggle_like(cls, user_id, content_type, content_id):
        """切换点赞状态"""
        existing_like = cls.query.filter_by(
            user_id=user_id,
            content_type=content_type,
            content_id=content_id
        ).first()
        
        if existing_like:
            # 取消点赞
            db.session.delete(existing_like)
            cls._update_like_count(content_type, content_id, -1)
            return False
        else:
            # 添加点赞
            new_like = cls(
                user_id=user_id,
                content_type=content_type,
                content_id=content_id
            )
            db.session.add(new_like)
            cls._update_like_count(content_type, content_id, 1)
            return True
    
    @staticmethod
    def _update_like_count(content_type, content_id, delta):
        """更新内容的点赞数"""
        if content_type == ContentType.ARTICLE:
            article = Article.query.get(content_id)
            if article:
                article.like_count = max(0, article.like_count + delta)
        elif content_type == ContentType.DISCUSSION:
            discussion = Discussion.query.get(content_id)
            if discussion:
                discussion.like_count = max(0, discussion.like_count + delta)
        elif content_type == ContentType.REPLY:
            reply = DiscussionReply.query.get(content_id)
            if reply:
                reply.like_count = max(0, reply.like_count + delta)

class ContentView(db.Model):
    """内容浏览记录"""
    __tablename__ = 'content_views'
    
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), index=True)
    content_type = db.Column(db.Enum(ContentType), nullable=False)
    content_id = db.Column(db.BigInteger, nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # 索引
    __table_args__ = (
        db.Index('idx_content_views_content', 'content_type', 'content_id'),
    )
    
    @classmethod
    def record_view(cls, content_type, content_id, user_id=None, ip_address=None, user_agent=None):
        """记录浏览"""
        # 检查是否在短时间内重复浏览（防刷）
        if user_id:
            recent_view = cls.query.filter_by(
                user_id=user_id,
                content_type=content_type,
                content_id=content_id
            ).filter(
                cls.created_at > datetime.utcnow() - timedelta(minutes=5)
            ).first()
            
            if recent_view:
                return False
        
        # 记录浏览
        view = cls(
            user_id=user_id,
            content_type=content_type,
            content_id=content_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(view)
        
        # 更新浏览计数
        cls._update_view_count(content_type, content_id, 1)
        
        return True
    
    @staticmethod
    def _update_view_count(content_type, content_id, delta):
        """更新内容的浏览数"""
        if content_type == ContentType.ARTICLE:
            article = Article.query.get(content_id)
            if article:
                article.view_count += delta
        elif content_type == ContentType.DISCUSSION:
            discussion = Discussion.query.get(content_id)
            if discussion:
                discussion.view_count += delta
        elif content_type == ContentType.MATCH:
            from models.match import Match
            match = Match.query.get(content_id)
            if match:
                match.view_count += delta
