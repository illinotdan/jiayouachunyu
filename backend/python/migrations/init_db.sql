-- =============================================
-- Dota2 战队分析系统数据库设计
-- =============================================

-- 基础数据表
CREATE TABLE heroes (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    primary_attribute VARCHAR(20) NOT NULL CHECK (primary_attribute IN ('strength', 'agility', 'intelligence', 'universal')),
    roles TEXT[] DEFAULT '{}',
    attack_type VARCHAR(20) DEFAULT 'melee' CHECK (attack_type IN ('melee', 'ranged')),
    image_url TEXT,
    icon_url TEXT,
    complexity INTEGER DEFAULT 1 CHECK (complexity BETWEEN 1 AND 3),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE items (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    cost INTEGER DEFAULT 0,
    category VARCHAR(50),
    components INTEGER[] DEFAULT '{}',
    image_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 团队和选手
CREATE TABLE teams (
    id BIGSERIAL PRIMARY KEY,
    team_id VARCHAR(50) UNIQUE,
    name VARCHAR(255) NOT NULL,
    tag VARCHAR(20) NOT NULL,
    logo_url TEXT,
    region VARCHAR(50),
    founded_date DATE,
    disbanded_date DATE,
    description TEXT,
    website_url TEXT,
    social_links JSONB DEFAULT '{}',
    total_earnings BIGINT DEFAULT 0,
    world_ranking INTEGER,
    regional_ranking INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE players (
    id BIGSERIAL PRIMARY KEY,
    steam_id VARCHAR(50) UNIQUE,
    account_id BIGINT UNIQUE,
    name VARCHAR(100) NOT NULL,
    nickname VARCHAR(100),
    real_name VARCHAR(100),
    country_code VARCHAR(3),
    current_team_id BIGINT REFERENCES teams(id),
    position INTEGER CHECK (position BETWEEN 1 AND 5),
    avatar_url TEXT,
    join_date DATE,
    leave_date DATE,
    total_earnings BIGINT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 联赛和比赛
CREATE TABLE leagues (
    id BIGSERIAL PRIMARY KEY,
    league_id VARCHAR(50) UNIQUE,
    name VARCHAR(255) NOT NULL,
    short_name VARCHAR(100),
    tier INTEGER DEFAULT 3 CHECK (tier BETWEEN 1 AND 4),
    logo_url TEXT,
    description TEXT,
    prize_pool BIGINT DEFAULT 0,
    start_date DATE,
    end_date DATE,
    region VARCHAR(50),
    organizer VARCHAR(255),
    status VARCHAR(20) DEFAULT 'upcoming' CHECK (status IN ('upcoming', 'ongoing', 'finished', 'cancelled')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE matches (
    id BIGSERIAL PRIMARY KEY,
    match_id VARCHAR(50) UNIQUE NOT NULL,
    league_id BIGINT REFERENCES leagues(id),
    series_id VARCHAR(50), -- BO3/BO5系列赛标识
    series_type VARCHAR(10) DEFAULT 'bo1', -- bo1, bo3, bo5
    game_number INTEGER DEFAULT 1, -- 系列赛中的第几局
    
    -- 队伍信息
    radiant_team_id BIGINT REFERENCES teams(id),
    dire_team_id BIGINT REFERENCES teams(id),
    radiant_score INTEGER DEFAULT 0,
    dire_score INTEGER DEFAULT 0,
    radiant_win BOOLEAN,
    
    -- 比赛时间
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration INTEGER, -- 秒数
    
    -- 比赛基本信息
    status VARCHAR(20) DEFAULT 'upcoming' CHECK (status IN ('upcoming', 'live', 'finished', 'cancelled')),
    game_mode VARCHAR(50) DEFAULT 'ranked',
    lobby_type VARCHAR(50),
    patch_version VARCHAR(20),
    region VARCHAR(50),
    
    -- 比赛数据链接
    replay_url TEXT,
    broadcast_url TEXT,
    
    -- 统计数据
    view_count INTEGER DEFAULT 0,
    analysis_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    
    -- 数据来源标记
    data_sources JSONB DEFAULT '{}', -- 记录数据来自哪些源
    data_quality_score INTEGER DEFAULT 0 CHECK (data_quality_score BETWEEN 0 AND 100),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 比赛选手数据（核心分析数据）
CREATE TABLE match_players (
    id BIGSERIAL PRIMARY KEY,
    match_id BIGINT REFERENCES matches(id) ON DELETE CASCADE,
    player_id BIGINT REFERENCES players(id),
    account_id VARCHAR(50),
    player_name VARCHAR(100),
    team_side VARCHAR(10) NOT NULL CHECK (team_side IN ('radiant', 'dire')),
    player_slot INTEGER, -- 0-9，Dota2标准插槽
    hero_id INTEGER REFERENCES heroes(id),
    
    -- 基础数据
    kills INTEGER DEFAULT 0,
    deaths INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    last_hits INTEGER DEFAULT 0,
    denies INTEGER DEFAULT 0,
    
    -- 经济数据
    gold_per_min INTEGER DEFAULT 0,
    exp_per_min INTEGER DEFAULT 0,
    net_worth INTEGER DEFAULT 0,
    
    -- 伤害数据
    hero_damage INTEGER DEFAULT 0,
    tower_damage INTEGER DEFAULT 0,
    hero_healing INTEGER DEFAULT 0,
    
    -- 其他数据
    level INTEGER DEFAULT 1,
    items JSONB DEFAULT '[]', -- 最终装备
    item_timeline JSONB DEFAULT '{}', -- 出装时间线
    
    -- 高级数据（来自不同源）
    ward_placed INTEGER DEFAULT 0,
    ward_destroyed INTEGER DEFAULT 0,
    camps_stacked INTEGER DEFAULT 0,
    rune_pickups INTEGER DEFAULT 0,
    teamfight_participation DECIMAL(5,2) DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Pick/Ban 数据（战术分析核心）
CREATE TABLE match_drafts (
    id BIGSERIAL PRIMARY KEY,
    match_id BIGINT REFERENCES matches(id) ON DELETE CASCADE,
    hero_id INTEGER REFERENCES heroes(id),
    team_side VARCHAR(10) NOT NULL CHECK (team_side IN ('radiant', 'dire')),
    is_pick BOOLEAN NOT NULL, -- TRUE=pick, FALSE=ban
    order_number INTEGER NOT NULL, -- 1-22 (10 bans + 10 picks + 2 bans)
    phase INTEGER NOT NULL CHECK (phase BETWEEN 1 AND 3), -- BP阶段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 比赛分析数据
CREATE TABLE match_analysis (
    id BIGSERIAL PRIMARY KEY,
    match_id BIGINT REFERENCES matches(id) ON DELETE CASCADE,
    
    -- 关键事件
    first_blood_time INTEGER,
    first_blood_player VARCHAR(100),
    first_tower_time INTEGER,
    first_roshan_time INTEGER,
    
    -- 经济分析
    gold_advantage JSONB, -- 每分钟金钱差
    exp_advantage JSONB, -- 每分钟经验差
    net_worth_timeline JSONB, -- 净值时间线
    
    -- 地图控制
    ward_timeline JSONB, -- 视野控制时间线
    tower_timeline JSONB, -- 推塔时间线
    
    -- 团战分析
    teamfights JSONB, -- 团战详情
    key_moments JSONB, -- 关键时刻
    
    -- MVP分析
    mvp_player VARCHAR(100),
    mvp_reasoning TEXT,
    
    -- AI分析结果
    ai_analysis JSONB DEFAULT '{}',
    analysis_confidence INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 统计数据表
CREATE TABLE hero_matchup_stats (
    id BIGSERIAL PRIMARY KEY,
    hero_id INTEGER REFERENCES heroes(id),
    enemy_hero_id INTEGER REFERENCES heroes(id),
    patch_version VARCHAR(20),
    tier_filter VARCHAR(20) DEFAULT 'all',
    
    total_matches INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    win_rate DECIMAL(5,2) DEFAULT 0,
    
    avg_duration INTEGER DEFAULT 0,
    avg_kda DECIMAL(4,2) DEFAULT 0,
    avg_gpm INTEGER DEFAULT 0,
    avg_xpm INTEGER DEFAULT 0,
    
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(hero_id, enemy_hero_id, patch_version, tier_filter)
);

CREATE TABLE team_matchup_stats (
    id BIGSERIAL PRIMARY KEY,
    team_id BIGINT REFERENCES teams(id),
    opponent_id BIGINT REFERENCES teams(id),
    
    total_matches INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    win_rate DECIMAL(5,2) DEFAULT 0,
    
    last_match_date TIMESTAMP,
    avg_duration INTEGER DEFAULT 0,
    
    -- 风格对比
    avg_kills_diff DECIMAL(5,2) DEFAULT 0,
    avg_gpm_diff INTEGER DEFAULT 0,
    early_game_advantage DECIMAL(5,2) DEFAULT 0,
    
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(team_id, opponent_id)
);

-- 选手统计
CREATE TABLE player_stats (
    id BIGSERIAL PRIMARY KEY,
    player_id BIGINT REFERENCES players(id),
    hero_id INTEGER REFERENCES heroes(id),
    position INTEGER,
    patch_version VARCHAR(20),
    time_period VARCHAR(20) DEFAULT 'all', -- week, month, patch, all
    
    total_matches INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    win_rate DECIMAL(5,2) DEFAULT 0,
    
    avg_kills DECIMAL(4,2) DEFAULT 0,
    avg_deaths DECIMAL(4,2) DEFAULT 0,
    avg_assists DECIMAL(4,2) DEFAULT 0,
    avg_kda DECIMAL(4,2) DEFAULT 0,
    
    avg_last_hits DECIMAL(6,2) DEFAULT 0,
    avg_gpm INTEGER DEFAULT 0,
    avg_xpm INTEGER DEFAULT 0,
    
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(player_id, hero_id, position, patch_version, time_period)
);

-- 专家预测和分析
CREATE TABLE expert_predictions (
    id BIGSERIAL PRIMARY KEY,
    expert_id BIGINT REFERENCES players(id), -- 可以是退役选手或分析师
    match_id BIGINT REFERENCES matches(id),
    
    prediction JSONB NOT NULL, -- 预测内容
    confidence INTEGER CHECK (confidence BETWEEN 0 AND 100),
    reasoning TEXT,
    
    result VARCHAR(20) DEFAULT 'pending' CHECK (result IN ('correct', 'incorrect', 'pending', 'cancelled')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    
    UNIQUE(expert_id, match_id)
);

-- 用户评论表（需要添加）
CREATE TABLE match_comments (
    id BIGSERIAL PRIMARY KEY,
    match_id BIGINT REFERENCES matches(id),
    user_id BIGINT REFERENCES users(id),
    content TEXT NOT NULL,
    is_featured BOOLEAN DEFAULT FALSE, -- 精选评论
    like_count INTEGER DEFAULT 0,
    quality_score INTEGER, -- 评论质量评分
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI训练数据表
CREATE TABLE ai_training_samples (
    id BIGSERIAL PRIMARY KEY,
    match_id BIGINT REFERENCES matches(id),
    data_type VARCHAR(50), -- 'match_analysis', 'prediction', 'discussion'
    structured_data JSONB, -- 来自四个数据源的结构化数据
    community_insights JSONB, -- 精选评论和讨论
    training_text TEXT, -- 格式化后的训练文本
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 数据同步日志
CREATE TABLE data_sync_logs (
    id BIGSERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL, -- opendota, stratz, liquipedia, dem
    sync_type VARCHAR(50) NOT NULL, -- full, incremental, specific
    status VARCHAR(20) NOT NULL CHECK (status IN ('running', 'completed', 'failed', 'partial')),
    
    records_processed INTEGER DEFAULT 0,
    records_success INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    error_message TEXT,
    sync_details JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_matches_start_time ON matches(start_time);
CREATE INDEX idx_matches_teams ON matches(radiant_team_id, dire_team_id);
CREATE INDEX idx_matches_league ON matches(league_id);
CREATE INDEX idx_matches_status ON matches(status);

CREATE INDEX idx_match_players_match ON match_players(match_id);
CREATE INDEX idx_match_players_hero ON match_players(hero_id);
CREATE INDEX idx_match_players_player ON match_players(player_id);

CREATE INDEX idx_match_drafts_match ON match_drafts(match_id);
CREATE INDEX idx_match_drafts_hero ON match_drafts(hero_id);

CREATE INDEX idx_hero_matchup_hero ON hero_matchup_stats(hero_id);
CREATE INDEX idx_hero_matchup_enemy ON hero_matchup_stats(enemy_hero_id);

CREATE INDEX idx_team_matchup_team ON team_matchup_stats(team_id);
CREATE INDEX idx_team_matchup_opponent ON team_matchup_stats(opponent_id);

CREATE INDEX idx_player_stats_player ON player_stats(player_id);
CREATE INDEX idx_player_stats_hero ON player_stats(hero_id);

-- 创建触发器来自动更新时间戳
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_teams_updated_at BEFORE UPDATE ON teams FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_players_updated_at BEFORE UPDATE ON players FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_matches_updated_at BEFORE UPDATE ON matches FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_match_analysis_updated_at BEFORE UPDATE ON match_analysis FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();