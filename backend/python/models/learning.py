"""
学习相关数据模型
"""

from config.database import db
from datetime import datetime
import enum
from sqlalchemy.dialects.postgresql import JSONB, ARRAY

class LearningContentType(enum.Enum):
    """学习内容类型"""
    GUIDE = 'guide'          # 攻略教学
    ANALYSIS = 'analysis'    # 技术分析
    TIPS = 'tips'           # 实用技巧
    QA = 'qa'               # 问答互助

class DifficultyLevel(enum.Enum):
    """难度等级"""
    BEGINNER = 'beginner'    # 新手
    INTERMEDIATE = 'intermediate'  # 中等
    ADVANCED = 'advanced'    # 进阶
    EXPERT = 'expert'       # 困难

class LearningContent(db.Model):
    """学习内容模型"""
    __tablename__ = 'learning_content'
    
    id = db.Column(db.BigInteger, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    content = db.Column(db.Text, nullable=False)
    content_type = db.Column(db.Enum(LearningContentType), nullable=False, index=True)
    difficulty = db.Column(db.Enum(DifficultyLevel), default=DifficultyLevel.INTERMEDIATE, index=True)
    category = db.Column(db.String(50), index=True)  # 'basics', 'heroes', 'tactics', 'advanced'
    tags = db.Column(ARRAY(db.String), default=list)
    
    # 作者信息
    author_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # 关联数据
    hero_id = db.Column(db.Integer, db.ForeignKey('heroes.id'))  # 如果是英雄相关内容
    match_id = db.Column(db.BigInteger, db.ForeignKey('matches.id'))  # 如果基于特定比赛
    
    # 媒体资源
    thumbnail_url = db.Column(db.Text)
    video_url = db.Column(db.Text)
    replay_file_url = db.Column(db.Text)
    
    # 统计数据
    view_count = db.Column(db.Integer, default=0)
    like_count = db.Column(db.Integer, default=0)
    bookmark_count = db.Column(db.Integer, default=0)
    comment_count = db.Column(db.Integer, default=0)
    
    # 质量评分
    quality_score = db.Column(db.Numeric(3, 2), default=0)  # 0-5分
    is_featured = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)  # 官方认证内容
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime, index=True)
    
    # 关系
    author = db.relationship('User', backref='learning_content')
    hero = db.relationship('Hero', backref='learning_content')
    match = db.relationship('Match', backref='learning_content')
    comments = db.relationship('LearningComment', backref='content', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self, include_content=False):
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'type': self.content_type.value,
            'difficulty': self.difficulty.value,
            'category': self.category,
            'tags': self.tags,
            'author': self.author.to_dict(),
            'thumbnail': self.thumbnail_url,
            'videoUrl': self.video_url,
            'viewCount': self.view_count,
            'likeCount': self.like_count,
            'bookmarkCount': self.bookmark_count,
            'commentCount': self.comment_count,
            'qualityScore': float(self.quality_score) if self.quality_score else 0,
            'isFeatured': self.is_featured,
            'isVerified': self.is_verified,
            'createdAt': self.created_at.isoformat(),
            'publishedAt': self.published_at.isoformat() if self.published_at else None
        }
        
        if include_content:
            data['content'] = self.content
        
        if self.hero:
            data['hero'] = self.hero.to_dict()
        
        if self.match:
            data['match'] = self.match.to_dict()
        
        return data

class LearningComment(db.Model):
    """学习内容评论"""
    __tablename__ = 'learning_comments'
    
    id = db.Column(db.BigInteger, primary_key=True)
    content_id = db.Column(db.BigInteger, db.ForeignKey('learning_content.id'), nullable=False, index=True)
    author_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False, index=True)
    parent_id = db.Column(db.BigInteger, db.ForeignKey('learning_comments.id'), index=True)
    
    comment = db.Column(db.Text, nullable=False)
    like_count = db.Column(db.Integer, default=0)
    is_helpful = db.Column(db.Boolean, default=False)  # 是否被标记为有用
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    author = db.relationship('User', backref='learning_comments')
    parent = db.relationship('LearningComment', remote_side=[id], backref='replies')
    
    def to_dict(self):
        return {
            'id': self.id,
            'comment': self.comment,
            'author': self.author.to_dict(),
            'parentId': self.parent_id,
            'likeCount': self.like_count,
            'isHelpful': self.is_helpful,
            'createdAt': self.created_at.isoformat(),
            'updatedAt': self.updated_at.isoformat()
        }

class UserLearningProgress(db.Model):
    """用户学习进度"""
    __tablename__ = 'user_learning_progress'
    
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False, index=True)
    content_id = db.Column(db.BigInteger, db.ForeignKey('learning_content.id'), nullable=False, index=True)
    
    # 学习状态
    is_completed = db.Column(db.Boolean, default=False)
    completion_percentage = db.Column(db.Integer, default=0)  # 0-100
    time_spent = db.Column(db.Integer, default=0)  # 学习时间（秒）
    
    # 学习笔记
    notes = db.Column(db.Text)
    bookmarked = db.Column(db.Boolean, default=False)
    
    # 评价
    rating = db.Column(db.Integer)  # 1-5星评价
    feedback = db.Column(db.Text)
    
    # 时间戳
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    last_accessed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    user = db.relationship('User', backref='learning_progress')
    content = db.relationship('LearningContent', backref='user_progress')
    
    # 唯一约束
    __table_args__ = (
        db.UniqueConstraint('user_id', 'content_id', name='unique_user_content_progress'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'contentId': self.content_id,
            'isCompleted': self.is_completed,
            'completionPercentage': self.completion_percentage,
            'timeSpent': self.time_spent,
            'notes': self.notes,
            'bookmarked': self.bookmarked,
            'rating': self.rating,
            'feedback': self.feedback,
            'startedAt': self.started_at.isoformat(),
            'completedAt': self.completed_at.isoformat() if self.completed_at else None,
            'lastAccessedAt': self.last_accessed_at.isoformat()
        }

class MatchDiscussion(db.Model):
    """比赛讨论版"""
    __tablename__ = 'match_discussions'
    
    class Category(enum.Enum):
        GENERAL = 'general'      # 综合讨论
        TACTICS = 'tactics'      # 战术分析
        HIGHLIGHTS = 'highlights' # 精彩时刻
        LEARNING = 'learning'    # 学习要点
        QA = 'qa'               # 问答互助
    
    id = db.Column(db.BigInteger, primary_key=True)
    match_id = db.Column(db.BigInteger, db.ForeignKey('matches.id'), nullable=False, index=True)
    author_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False, index=True)
    
    title = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.Enum(Category), default=Category.GENERAL, index=True)
    tags = db.Column(ARRAY(db.String), default=list)
    
    # 特殊标记
    is_sticky = db.Column(db.Boolean, default=False)  # 置顶
    is_hot = db.Column(db.Boolean, default=False)     # 热门
    is_question = db.Column(db.Boolean, default=False) # 问题求助
    is_solved = db.Column(db.Boolean, default=False)   # 问题已解决
    
    # 统计数据
    view_count = db.Column(db.Integer, default=0)
    like_count = db.Column(db.Integer, default=0)
    reply_count = db.Column(db.Integer, default=0)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # 关系
    match = db.relationship('Match', backref='discussions')
    author = db.relationship('User', backref='match_discussions')
    replies = db.relationship('MatchDiscussionReply', backref='discussion', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self, include_content=False):
        data = {
            'id': self.id,
            'matchId': self.match_id,
            'title': self.title,
            'author': self.author.to_dict(),
            'category': self.category.value,
            'tags': self.tags,
            'isSticky': self.is_sticky,
            'isHot': self.is_hot,
            'isQuestion': self.is_question,
            'isSolved': self.is_solved,
            'viewCount': self.view_count,
            'likeCount': self.like_count,
            'replyCount': self.reply_count,
            'createdAt': self.created_at.isoformat(),
            'lastActivity': self.last_activity_at.isoformat()
        }
        
        if include_content:
            data['content'] = self.content
        
        return data
    
    def update_activity(self):
        """更新最后活动时间"""
        self.last_activity_at = datetime.utcnow()
        db.session.commit()

class MatchDiscussionReply(db.Model):
    """比赛讨论回复"""
    __tablename__ = 'match_discussion_replies'
    
    id = db.Column(db.BigInteger, primary_key=True)
    discussion_id = db.Column(db.BigInteger, db.ForeignKey('match_discussions.id'), nullable=False, index=True)
    author_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False, index=True)
    parent_id = db.Column(db.BigInteger, db.ForeignKey('match_discussion_replies.id'), index=True)
    
    content = db.Column(db.Text, nullable=False)
    like_count = db.Column(db.Integer, default=0)
    is_best_answer = db.Column(db.Boolean, default=False)  # 最佳答案
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    author = db.relationship('User', backref='match_discussion_replies')
    parent = db.relationship('MatchDiscussionReply', remote_side=[id], backref='children')
    
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'author': self.author.to_dict(),
            'parentId': self.parent_id,
            'likeCount': self.like_count,
            'isBestAnswer': self.is_best_answer,
            'createdAt': self.created_at.isoformat(),
            'updatedAt': self.updated_at.isoformat()
        }

class AIAnalysisRequest(db.Model):
    """AI分析请求"""
    __tablename__ = 'ai_analysis_requests'
    
    class Status(enum.Enum):
        PENDING = 'pending'
        PROCESSING = 'processing'
        COMPLETED = 'completed'
        FAILED = 'failed'
    
    class AnalysisType(enum.Enum):
        REPLAY_ANALYSIS = 'replay_analysis'      # replay文件分析
        MATCH_ANALYSIS = 'match_analysis'        # 比赛分析
        SKILL_ASSESSMENT = 'skill_assessment'    # 技能评估
        LEARNING_SUGGESTION = 'learning_suggestion'  # 学习建议
    
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False, index=True)
    analysis_type = db.Column(db.Enum(AnalysisType), nullable=False)
    status = db.Column(db.Enum(Status), default=Status.PENDING, index=True)
    
    # 输入数据
    input_data = db.Column(JSONB, nullable=False)  # 存储输入参数
    file_url = db.Column(db.Text)  # 上传的文件URL
    
    # 分析结果
    result_data = db.Column(JSONB)  # 存储分析结果
    suggestions = db.Column(JSONB)  # AI建议
    
    # 处理信息
    error_message = db.Column(db.Text)
    processing_time = db.Column(db.Integer)  # 处理时间（秒）
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # 关系
    user = db.relationship('User', backref='ai_requests')
    
    def to_dict(self):
        return {
            'id': self.id,
            'userId': self.user_id,
            'analysisType': self.analysis_type.value,
            'status': self.status.value,
            'inputData': self.input_data,
            'fileUrl': self.file_url,
            'resultData': self.result_data,
            'suggestions': self.suggestions,
            'errorMessage': self.error_message,
            'processingTime': self.processing_time,
            'createdAt': self.created_at.isoformat(),
            'startedAt': self.started_at.isoformat() if self.started_at else None,
            'completedAt': self.completed_at.isoformat() if self.completed_at else None
        }

class UserSkillAssessment(db.Model):
    """用户技能评估"""
    __tablename__ = 'user_skill_assessments'
    
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # 技能评分（1-10分）
    laning_skill = db.Column(db.Integer, default=5)      # 对线技能
    farming_skill = db.Column(db.Integer, default=5)     # 发育技能
    teamfight_skill = db.Column(db.Integer, default=5)   # 团战技能
    map_awareness = db.Column(db.Integer, default=5)     # 地图意识
    game_sense = db.Column(db.Integer, default=5)        # 游戏理解
    mechanical_skill = db.Column(db.Integer, default=5)  # 操作技巧
    
    # 总体评分
    overall_score = db.Column(db.Numeric(3, 1), default=5.0)
    
    # 评估基础数据
    assessment_data = db.Column(JSONB)  # 评估的详细数据
    improvement_areas = db.Column(ARRAY(db.String))  # 需要改进的领域
    strengths = db.Column(ARRAY(db.String))  # 优势领域
    
    # AI建议
    ai_suggestions = db.Column(JSONB)
    recommended_content = db.Column(ARRAY(db.BigInteger))  # 推荐的学习内容ID
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = db.relationship('User', backref='skill_assessments')
    
    def to_dict(self):
        return {
            'id': self.id,
            'userId': self.user_id,
            'skills': {
                'laning': self.laning_skill,
                'farming': self.farming_skill,
                'teamfight': self.teamfight_skill,
                'mapAwareness': self.map_awareness,
                'gameSense': self.game_sense,
                'mechanical': self.mechanical_skill
            },
            'overallScore': float(self.overall_score),
            'improvementAreas': self.improvement_areas,
            'strengths': self.strengths,
            'aiSuggestions': self.ai_suggestions,
            'recommendedContent': self.recommended_content,
            'createdAt': self.created_at.isoformat(),
            'updatedAt': self.updated_at.isoformat()
        }
    
    @classmethod
    def calculate_overall_score(cls, skills):
        """计算总体评分"""
        total = sum(skills.values())
        return round(total / len(skills), 1)

class LearningPath(db.Model):
    """学习路径"""
    __tablename__ = 'learning_paths'
    
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    difficulty = db.Column(db.Enum(DifficultyLevel), nullable=False)
    
    # 路径内容
    content_ids = db.Column(ARRAY(db.BigInteger), nullable=False)  # 学习内容ID列表
    estimated_hours = db.Column(db.Integer)  # 预估学习时长
    
    # 路径标签
    tags = db.Column(ARRAY(db.String), default=list)
    category = db.Column(db.String(50))
    
    # 创建者
    creator_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    
    # 统计
    enrollment_count = db.Column(db.Integer, default=0)  # 学习人数
    completion_rate = db.Column(db.Numeric(5, 2), default=0)  # 完成率
    
    # 状态
    is_published = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    creator = db.relationship('User', backref='created_learning_paths')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'difficulty': self.difficulty.value,
            'contentIds': self.content_ids,
            'estimatedHours': self.estimated_hours,
            'tags': self.tags,
            'category': self.category,
            'creator': self.creator.to_dict(),
            'enrollmentCount': self.enrollment_count,
            'completionRate': float(self.completion_rate),
            'isFeatured': self.is_featured,
            'createdAt': self.created_at.isoformat()
        }
