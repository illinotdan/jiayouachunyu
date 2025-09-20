"""
比赛相关数据模型
"""

from config.database import db
from datetime import datetime
import enum
from sqlalchemy.dialects.postgresql import JSONB, ARRAY

class MatchStatus(enum.Enum):
    """比赛状态枚举"""
    UPCOMING = 'upcoming'
    LIVE = 'live'
    FINISHED = 'finished'
    CANCELLED = 'cancelled'

class TeamSide(enum.Enum):
    """队伍方向枚举"""
    RADIANT = 'radiant'
    DIRE = 'dire'

class League(db.Model):
    """联赛模型"""
    __tablename__ = 'leagues'
    
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    short_name = db.Column(db.String(50))
    tier = db.Column(db.Integer, default=3, nullable=False, index=True)
    logo_url = db.Column(db.Text)
    description = db.Column(db.Text)
    prize_pool = db.Column(db.BigInteger)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    region = db.Column(db.String(50), index=True)
    organizer = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    matches = db.relationship('Match', backref='league', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'shortName': self.short_name,
            'tier': self.tier,
            'logo': self.logo_url,
            'description': self.description,
            'prizePool': self.prize_pool,
            'startDate': self.start_date.isoformat() if self.start_date else None,
            'endDate': self.end_date.isoformat() if self.end_date else None,
            'region': self.region,
            'organizer': self.organizer
        }

class Team(db.Model):
    """战队模型"""
    __tablename__ = 'teams'
    
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    tag = db.Column(db.String(10), nullable=False)
    logo_url = db.Column(db.Text)
    region = db.Column(db.String(50), index=True)
    founded_date = db.Column(db.Date)
    description = db.Column(db.Text)
    website_url = db.Column(db.Text)
    social_links = db.Column(JSONB, default=dict)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    radiant_matches = db.relationship('Match', foreign_keys='Match.radiant_team_id', backref='radiant_team')
    dire_matches = db.relationship('Match', foreign_keys='Match.dire_team_id', backref='dire_team')
    players = db.relationship('Player', backref='team', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'tag': self.tag,
            'logo': self.logo_url,
            'region': self.region,
            'foundedDate': self.founded_date.isoformat() if self.founded_date else None,
            'description': self.description,
            'website': self.website_url,
            'socialLinks': self.social_links
        }
    
    def get_recent_matches(self, limit=10):
        """获取最近比赛"""
        from models.match import Match
        return Match.query.filter(
            db.or_(
                Match.radiant_team_id == self.id,
                Match.dire_team_id == self.id
            )
        ).order_by(Match.start_time.desc()).limit(limit).all()

class Player(db.Model):
    """选手模型"""
    __tablename__ = 'players'
    
    id = db.Column(db.BigInteger, primary_key=True)
    steam_id = db.Column(db.String(50), unique=True, index=True)
    name = db.Column(db.String(100), nullable=False)
    nickname = db.Column(db.String(100))
    real_name = db.Column(db.String(100))
    country = db.Column(db.String(3), index=True)
    team_id = db.Column(db.BigInteger, db.ForeignKey('teams.id'))
    position = db.Column(db.Integer)  # 1-5位置
    avatar_url = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'steamId': self.steam_id,
            'name': self.name,
            'nickname': self.nickname,
            'realName': self.real_name,
            'country': self.country,
            'teamId': self.team_id,
            'position': self.position,
            'avatar': self.avatar_url
        }

class Match(db.Model):
    """比赛模型"""
    __tablename__ = 'matches'
    
    id = db.Column(db.BigInteger, primary_key=True)
    match_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    league_id = db.Column(db.BigInteger, db.ForeignKey('leagues.id'))
    radiant_team_id = db.Column(db.BigInteger, db.ForeignKey('teams.id'))
    dire_team_id = db.Column(db.BigInteger, db.ForeignKey('teams.id'))
    radiant_score = db.Column(db.Integer, default=0)
    dire_score = db.Column(db.Integer, default=0)
    radiant_win = db.Column(db.Boolean)
    duration = db.Column(db.Integer)  # 秒数
    start_time = db.Column(db.DateTime, index=True)
    end_time = db.Column(db.DateTime)
    status = db.Column(db.Enum(MatchStatus), default=MatchStatus.UPCOMING, nullable=False, index=True)
    game_mode = db.Column(db.String(50))
    patch_version = db.Column(db.String(20))
    region = db.Column(db.String(50))
    replay_url = db.Column(db.Text)
    
    # 统计数据
    view_count = db.Column(db.Integer, default=0)
    analysis_count = db.Column(db.Integer, default=0)
    expert_review_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    players = db.relationship('MatchPlayer', backref='match', lazy='dynamic', cascade='all, delete-orphan')
    predictions = db.relationship('ExpertPrediction', backref='match', lazy='dynamic')
    analysis = db.relationship('MatchAnalysis', backref='match', uselist=False, cascade='all, delete-orphan')
    
    def to_dict(self, include_details=False):
        data = {
            'id': self.match_id,
            'league': self.league.to_dict() if self.league else None,
            'radiant': {
                **self.radiant_team.to_dict(),
                'score': self.radiant_score
            } if self.radiant_team else None,
            'dire': {
                **self.dire_team.to_dict(), 
                'score': self.dire_score
            } if self.dire_team else None,
            'duration': self.duration,
            'startTime': self.start_time.isoformat() if self.start_time else None,
            'endTime': self.end_time.isoformat() if self.end_time else None,
            'status': self.status.value,
            'radiantWin': self.radiant_win,
            'analysisCount': self.analysis_count,
            'expertReviews': self.expert_review_count,
            'viewCount': self.view_count,
            'commentCount': 0  # TODO: 实现评论统计
        }
        
        if include_details:
            data.update({
                'gameMode': self.game_mode,
                'patchVersion': self.patch_version,
                'region': self.region,
                'replayUrl': self.replay_url,
                'players': {
                    'radiant': [p.to_dict() for p in self.players.filter_by(team_side=TeamSide.RADIANT).all()],
                    'dire': [p.to_dict() for p in self.players.filter_by(team_side=TeamSide.DIRE).all()]
                },
                'analysis': self.analysis.to_dict() if self.analysis else None
            })
        
        return data

class MatchPlayer(db.Model):
    """比赛选手数据"""
    __tablename__ = 'match_players'
    
    id = db.Column(db.BigInteger, primary_key=True)
    match_id = db.Column(db.BigInteger, db.ForeignKey('matches.id'), nullable=False, index=True)
    player_id = db.Column(db.BigInteger, db.ForeignKey('players.id'))
    account_id = db.Column(db.String(50))
    player_name = db.Column(db.String(100))
    team_side = db.Column(db.Enum(TeamSide), nullable=False)
    hero_id = db.Column(db.Integer, nullable=False, index=True)
    
    # 比赛数据
    kills = db.Column(db.Integer, default=0)
    deaths = db.Column(db.Integer, default=0)
    assists = db.Column(db.Integer, default=0)
    last_hits = db.Column(db.Integer, default=0)
    denies = db.Column(db.Integer, default=0)
    gpm = db.Column(db.Integer, default=0)
    xpm = db.Column(db.Integer, default=0)
    net_worth = db.Column(db.Integer, default=0)
    hero_damage = db.Column(db.Integer, default=0)
    tower_damage = db.Column(db.Integer, default=0)
    hero_healing = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    items = db.Column(JSONB, default=list)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    player = db.relationship('Player', backref='match_performances')
    
    def to_dict(self):
        return {
            'accountId': self.account_id,
            'name': self.player_name,
            'teamSide': self.team_side.value,
            'heroId': self.hero_id,
            'kills': self.kills,
            'deaths': self.deaths,
            'assists': self.assists,
            'lastHits': self.last_hits,
            'denies': self.denies,
            'gpm': self.gpm,
            'xpm': self.xpm,
            'netWorth': self.net_worth,
            'heroDamage': self.hero_damage,
            'towerDamage': self.tower_damage,
            'heroHealing': self.hero_healing,
            'level': self.level,
            'items': self.items
        }

class MatchAnalysis(db.Model):
    """比赛分析"""
    __tablename__ = 'match_analysis'
    
    id = db.Column(db.BigInteger, primary_key=True)
    match_id = db.Column(db.BigInteger, db.ForeignKey('matches.id'), nullable=False, unique=True)
    key_moments = db.Column(JSONB, default=list)
    mvp_player = db.Column(db.String(100))
    turning_point = db.Column(db.Text)
    prediction_confidence = db.Column(db.Integer)
    prediction_reasoning = db.Column(db.Text)
    
    # AI分析结果
    ai_analysis = db.Column(JSONB, default=dict)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'keyMoments': self.key_moments,
            'mvp': self.mvp_player,
            'turningPoint': self.turning_point,
            'prediction': {
                'confidence': self.prediction_confidence,
                'reasoning': self.prediction_reasoning
            },
            'aiAnalysis': self.ai_analysis
        }

class ExpertPrediction(db.Model):
    """专家预测"""
    __tablename__ = 'expert_predictions'
    
    class Result(enum.Enum):
        CORRECT = 'correct'
        INCORRECT = 'incorrect'
        PENDING = 'pending'
        CANCELLED = 'cancelled'
    
    id = db.Column(db.BigInteger, primary_key=True)
    expert_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False, index=True)
    match_id = db.Column(db.BigInteger, db.ForeignKey('matches.id'), nullable=False, index=True)
    prediction = db.Column(JSONB, nullable=False)
    confidence = db.Column(db.Integer, nullable=False)  # 0-100
    reasoning = db.Column(db.Text)
    result = db.Column(db.Enum(Result), default=Result.PENDING, index=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    
    # 约束
    __table_args__ = (
        db.CheckConstraint('confidence >= 0 AND confidence <= 100', name='check_confidence_range'),
        db.UniqueConstraint('expert_id', 'match_id', name='unique_expert_match_prediction'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'expert': self.expert.to_dict(),
            'match': self.match.to_dict(),
            'prediction': self.prediction,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'result': self.result.value,
            'createdAt': self.created_at.isoformat(),
            'resolvedAt': self.resolved_at.isoformat() if self.resolved_at else None
        }
    
    @classmethod
    def resolve_predictions_for_match(cls, match_id):
        """为已结束的比赛解析预测结果"""
        from models.match import Match
        
        match = Match.query.get(match_id)
        if not match or match.status != MatchStatus.FINISHED:
            return
        
        predictions = cls.query.filter_by(
            match_id=match_id, 
            result=cls.Result.PENDING
        ).all()
        
        for prediction in predictions:
            # 根据预测内容和实际结果判断正确性
            predicted_winner = prediction.prediction.get('winner')
            actual_winner = 'radiant' if match.radiant_win else 'dire'
            
            if predicted_winner == actual_winner:
                prediction.result = cls.Result.CORRECT
            else:
                prediction.result = cls.Result.INCORRECT
            
            prediction.resolved_at = datetime.utcnow()
        
        db.session.commit()

class Hero(db.Model):
    """英雄模型"""
    __tablename__ = 'heroes'
    
    class Attribute(enum.Enum):
        STRENGTH = 'strength'
        AGILITY = 'agility'
        INTELLIGENCE = 'intelligence'
        UNIVERSAL = 'universal'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    primary_attribute = db.Column(db.Enum(Attribute), nullable=False, index=True)
    roles = db.Column(ARRAY(db.String), default=list)
    image_url = db.Column(db.Text)
    icon_url = db.Column(db.Text)
    complexity = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'displayName': self.display_name,
            'primaryAttribute': self.primary_attribute.value,
            'roles': self.roles,
            'image': self.image_url,
            'icon': self.icon_url,
            'complexity': self.complexity
        }

class HeroStats(db.Model):
    """英雄统计"""
    __tablename__ = 'hero_stats'
    
    class Period(enum.Enum):
        DAY = 'day'
        WEEK = 'week'
        MONTH = 'month'
        PATCH = 'patch'
        ALL = 'all'
    
    class Tier(enum.Enum):
        HERALD = 'herald'
        GUARDIAN = 'guardian'
        CRUSADER = 'crusader'
        ARCHON = 'archon'
        LEGEND = 'legend'
        ANCIENT = 'ancient'
        DIVINE = 'divine'
        IMMORTAL = 'immortal'
        PRO = 'pro'
        ALL = 'all'
    
    id = db.Column(db.BigInteger, primary_key=True)
    hero_id = db.Column(db.Integer, db.ForeignKey('heroes.id'), nullable=False)
    period_type = db.Column(db.Enum(Period), nullable=False)
    tier_filter = db.Column(db.Enum(Tier), default=Tier.ALL)
    patch_version = db.Column(db.String(20))
    
    # 统计数据
    total_matches = db.Column(db.Integer, default=0)
    wins = db.Column(db.Integer, default=0)
    picks = db.Column(db.Integer, default=0)
    bans = db.Column(db.Integer, default=0)
    win_rate = db.Column(db.Numeric(5, 2), default=0)
    pick_rate = db.Column(db.Numeric(5, 2), default=0)
    ban_rate = db.Column(db.Numeric(5, 2), default=0)
    avg_kda = db.Column(db.Numeric(4, 2), default=0)
    avg_gpm = db.Column(db.Integer, default=0)
    avg_xpm = db.Column(db.Integer, default=0)
    
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    hero = db.relationship('Hero', backref='stats')
    
    # 唯一约束
    __table_args__ = (
        db.UniqueConstraint('hero_id', 'period_type', 'tier_filter', 'patch_version', 
                          name='unique_hero_stats'),
    )
    
    def to_dict(self):
        return {
            'heroId': self.hero_id,
            'hero': self.hero.to_dict() if self.hero else None,
            'periodType': self.period_type.value,
            'tierFilter': self.tier_filter.value,
            'patchVersion': self.patch_version,
            'stats': {
                'totalMatches': self.total_matches,
                'wins': self.wins,
                'picks': self.picks,
                'bans': self.bans,
                'winRate': float(self.win_rate),
                'pickRate': float(self.pick_rate),
                'banRate': float(self.ban_rate),
                'avgKDA': float(self.avg_kda),
                'avgGPM': self.avg_gpm,
                'avgXPM': self.avg_xpm
            },
            'calculatedAt': self.calculated_at.isoformat()
        }
