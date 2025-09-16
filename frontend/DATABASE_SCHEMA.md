# 刀塔情书 - 数据库设计文档

## 概述

本文档描述了刀塔情书平台的完整数据库设计，包括所有表结构、字段定义、索引和关系。

### 技术选型建议

- **主数据库**: PostgreSQL 14+
- **缓存**: Redis 6+
- **搜索引擎**: Elasticsearch 8+ (可选)
- **文件存储**: AWS S3 / 阿里云OSS

---

## 1. 用户相关表

### 1.1 users (用户表)

```sql
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    avatar_url TEXT,
    role user_role DEFAULT 'user',
    tier expert_tier DEFAULT 'bronze',
    verified BOOLEAN DEFAULT false,
    reputation INTEGER DEFAULT 0,
    bio TEXT,
    steam_id VARCHAR(50) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true
);

-- 枚举类型
CREATE TYPE user_role AS ENUM ('user', 'expert', 'admin', 'moderator');
CREATE TYPE expert_tier AS ENUM ('bronze', 'silver', 'gold', 'platinum', 'diamond');

-- 索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_steam_id ON users(steam_id);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_tier ON users(tier);
```

### 1.2 user_profiles (用户资料扩展表)

```sql
CREATE TABLE user_profiles (
    user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    display_name VARCHAR(100),
    location VARCHAR(100),
    timezone VARCHAR(50),
    language VARCHAR(10) DEFAULT 'zh-CN',
    notification_settings JSONB DEFAULT '{}',
    privacy_settings JSONB DEFAULT '{}',
    social_links JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 1.3 user_sessions (用户会话表)

```sql
CREATE TABLE user_sessions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_user_sessions_token ON user_sessions(token_hash);
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_expires ON user_sessions(expires_at);
```

---

## 2. 比赛相关表

### 2.1 leagues (联赛表)

```sql
CREATE TABLE leagues (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    short_name VARCHAR(50),
    tier INTEGER DEFAULT 3,
    logo_url TEXT,
    description TEXT,
    prize_pool BIGINT,
    start_date DATE,
    end_date DATE,
    region VARCHAR(50),
    organizer VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_leagues_tier ON leagues(tier);
CREATE INDEX idx_leagues_region ON leagues(region);
CREATE INDEX idx_leagues_active ON leagues(is_active);
```

### 2.2 teams (战队表)

```sql
CREATE TABLE teams (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    tag VARCHAR(10) NOT NULL,
    logo_url TEXT,
    region VARCHAR(50),
    founded_date DATE,
    description TEXT,
    website_url TEXT,
    social_links JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_teams_region ON teams(region);
CREATE INDEX idx_teams_active ON teams(is_active);
CREATE UNIQUE INDEX idx_teams_tag ON teams(tag) WHERE is_active = true;
```

### 2.3 players (选手表)

```sql
CREATE TABLE players (
    id BIGSERIAL PRIMARY KEY,
    steam_id VARCHAR(50) UNIQUE,
    name VARCHAR(100) NOT NULL,
    nickname VARCHAR(100),
    real_name VARCHAR(100),
    country VARCHAR(3),
    team_id BIGINT REFERENCES teams(id),
    position INTEGER, -- 1-5位置
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_players_steam_id ON players(steam_id);
CREATE INDEX idx_players_team_id ON players(team_id);
CREATE INDEX idx_players_country ON players(country);
```

### 2.4 matches (比赛表)

```sql
CREATE TABLE matches (
    id BIGSERIAL PRIMARY KEY,
    match_id VARCHAR(50) UNIQUE NOT NULL, -- OpenDota match ID
    league_id BIGINT REFERENCES leagues(id),
    radiant_team_id BIGINT REFERENCES teams(id),
    dire_team_id BIGINT REFERENCES teams(id),
    radiant_score INTEGER DEFAULT 0,
    dire_score INTEGER DEFAULT 0,
    radiant_win BOOLEAN,
    duration INTEGER, -- 秒数
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    status match_status DEFAULT 'upcoming',
    game_mode VARCHAR(50),
    patch_version VARCHAR(20),
    region VARCHAR(50),
    replay_url TEXT,
    view_count INTEGER DEFAULT 0,
    analysis_count INTEGER DEFAULT 0,
    expert_review_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TYPE match_status AS ENUM ('upcoming', 'live', 'finished', 'cancelled');

-- 索引
CREATE INDEX idx_matches_match_id ON matches(match_id);
CREATE INDEX idx_matches_league_id ON matches(league_id);
CREATE INDEX idx_matches_teams ON matches(radiant_team_id, dire_team_id);
CREATE INDEX idx_matches_start_time ON matches(start_time);
CREATE INDEX idx_matches_status ON matches(status);
```

### 2.5 match_players (比赛选手数据表)

```sql
CREATE TABLE match_players (
    id BIGSERIAL PRIMARY KEY,
    match_id BIGINT NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    player_id BIGINT REFERENCES players(id),
    account_id VARCHAR(50),
    player_name VARCHAR(100),
    team_side team_side NOT NULL,
    hero_id INTEGER NOT NULL,
    kills INTEGER DEFAULT 0,
    deaths INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    last_hits INTEGER DEFAULT 0,
    denies INTEGER DEFAULT 0,
    gpm INTEGER DEFAULT 0,
    xpm INTEGER DEFAULT 0,
    net_worth INTEGER DEFAULT 0,
    hero_damage INTEGER DEFAULT 0,
    tower_damage INTEGER DEFAULT 0,
    hero_healing INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    items JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TYPE team_side AS ENUM ('radiant', 'dire');

CREATE INDEX idx_match_players_match_id ON match_players(match_id);
CREATE INDEX idx_match_players_player_id ON match_players(player_id);
CREATE INDEX idx_match_players_hero_id ON match_players(hero_id);
```

---

## 3. 内容相关表

### 3.1 articles (文章表)

```sql
CREATE TABLE articles (
    id BIGSERIAL PRIMARY KEY,
    author_id BIGINT NOT NULL REFERENCES users(id),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    summary TEXT,
    category article_category DEFAULT 'analysis',
    tags TEXT[] DEFAULT '{}',
    match_id BIGINT REFERENCES matches(id),
    status article_status DEFAULT 'published',
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    featured BOOLEAN DEFAULT false,
    published_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TYPE article_category AS ENUM ('analysis', 'prediction', 'strategy', 'news', 'guide');
CREATE TYPE article_status AS ENUM ('draft', 'published', 'archived', 'deleted');

-- 索引
CREATE INDEX idx_articles_author_id ON articles(author_id);
CREATE INDEX idx_articles_category ON articles(category);
CREATE INDEX idx_articles_status ON articles(status);
CREATE INDEX idx_articles_published_at ON articles(published_at);
CREATE INDEX idx_articles_tags ON articles USING GIN(tags);
```

### 3.2 discussions (讨论表)

```sql
CREATE TABLE discussions (
    id BIGSERIAL PRIMARY KEY,
    author_id BIGINT NOT NULL REFERENCES users(id),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    category discussion_category DEFAULT 'general',
    tags TEXT[] DEFAULT '{}',
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    reply_count INTEGER DEFAULT 0,
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_hot BOOLEAN DEFAULT false,
    is_pinned BOOLEAN DEFAULT false,
    is_locked BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TYPE discussion_category AS ENUM ('analysis', 'prediction', 'strategy', 'news', 'general');

-- 索引
CREATE INDEX idx_discussions_author_id ON discussions(author_id);
CREATE INDEX idx_discussions_category ON discussions(category);
CREATE INDEX idx_discussions_last_activity ON discussions(last_activity_at);
CREATE INDEX idx_discussions_tags ON discussions USING GIN(tags);
```

### 3.3 discussion_replies (讨论回复表)

```sql
CREATE TABLE discussion_replies (
    id BIGSERIAL PRIMARY KEY,
    discussion_id BIGINT NOT NULL REFERENCES discussions(id) ON DELETE CASCADE,
    author_id BIGINT NOT NULL REFERENCES users(id),
    parent_id BIGINT REFERENCES discussion_replies(id),
    content TEXT NOT NULL,
    like_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_discussion_replies_discussion_id ON discussion_replies(discussion_id);
CREATE INDEX idx_discussion_replies_author_id ON discussion_replies(author_id);
CREATE INDEX idx_discussion_replies_parent_id ON discussion_replies(parent_id);
```

---

## 4. 专家系统表

### 4.1 expert_applications (专家申请表)

```sql
CREATE TABLE expert_applications (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    expertise_areas TEXT[] NOT NULL,
    bio TEXT NOT NULL,
    experience_years INTEGER,
    portfolio_links TEXT[],
    social_proof TEXT,
    status application_status DEFAULT 'pending',
    reviewer_id BIGINT REFERENCES users(id),
    review_notes TEXT,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reviewed_at TIMESTAMP WITH TIME ZONE
);

CREATE TYPE application_status AS ENUM ('pending', 'approved', 'rejected', 'under_review');

CREATE INDEX idx_expert_applications_user_id ON expert_applications(user_id);
CREATE INDEX idx_expert_applications_status ON expert_applications(status);
```

### 4.2 expert_predictions (专家预测表)

```sql
CREATE TABLE expert_predictions (
    id BIGSERIAL PRIMARY KEY,
    expert_id BIGINT NOT NULL REFERENCES users(id),
    match_id BIGINT NOT NULL REFERENCES matches(id),
    prediction JSONB NOT NULL, -- 预测内容
    confidence INTEGER CHECK (confidence >= 0 AND confidence <= 100),
    reasoning TEXT,
    result prediction_result,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE
);

CREATE TYPE prediction_result AS ENUM ('correct', 'incorrect', 'pending', 'cancelled');

CREATE INDEX idx_expert_predictions_expert_id ON expert_predictions(expert_id);
CREATE INDEX idx_expert_predictions_match_id ON expert_predictions(match_id);
CREATE INDEX idx_expert_predictions_result ON expert_predictions(result);
```

---

## 5. 交互数据表

### 5.1 user_follows (关注关系表)

```sql
CREATE TABLE user_follows (
    id BIGSERIAL PRIMARY KEY,
    follower_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    following_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(follower_id, following_id)
);

CREATE INDEX idx_user_follows_follower ON user_follows(follower_id);
CREATE INDEX idx_user_follows_following ON user_follows(following_id);
```

### 5.2 content_likes (点赞表)

```sql
CREATE TABLE content_likes (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content_type content_type NOT NULL,
    content_id BIGINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, content_type, content_id)
);

CREATE TYPE content_type AS ENUM ('article', 'discussion', 'reply', 'prediction');

CREATE INDEX idx_content_likes_user_id ON content_likes(user_id);
CREATE INDEX idx_content_likes_content ON content_likes(content_type, content_id);
```

### 5.3 content_views (浏览记录表)

```sql
CREATE TABLE content_views (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    content_type content_type NOT NULL,
    content_id BIGINT NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_content_views_content ON content_views(content_type, content_id);
CREATE INDEX idx_content_views_user_id ON content_views(user_id);
CREATE INDEX idx_content_views_created_at ON content_views(created_at);
```

---

## 6. 游戏数据表

### 6.1 heroes (英雄表)

```sql
CREATE TABLE heroes (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    primary_attribute hero_attribute NOT NULL,
    roles TEXT[] DEFAULT '{}',
    image_url TEXT,
    icon_url TEXT,
    complexity INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TYPE hero_attribute AS ENUM ('strength', 'agility', 'intelligence', 'universal');

CREATE INDEX idx_heroes_attribute ON heroes(primary_attribute);
CREATE INDEX idx_heroes_roles ON heroes USING GIN(roles);
```

### 6.2 hero_stats (英雄统计表)

```sql
CREATE TABLE hero_stats (
    id BIGSERIAL PRIMARY KEY,
    hero_id INTEGER NOT NULL REFERENCES heroes(id),
    period_type stats_period NOT NULL,
    tier_filter stats_tier DEFAULT 'all',
    patch_version VARCHAR(20),
    total_matches INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    picks INTEGER DEFAULT 0,
    bans INTEGER DEFAULT 0,
    win_rate DECIMAL(5,2) DEFAULT 0,
    pick_rate DECIMAL(5,2) DEFAULT 0,
    ban_rate DECIMAL(5,2) DEFAULT 0,
    avg_kda DECIMAL(4,2) DEFAULT 0,
    avg_gpm INTEGER DEFAULT 0,
    avg_xpm INTEGER DEFAULT 0,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TYPE stats_period AS ENUM ('day', 'week', 'month', 'patch', 'all');
CREATE TYPE stats_tier AS ENUM ('herald', 'guardian', 'crusader', 'archon', 'legend', 'ancient', 'divine', 'immortal', 'pro', 'all');

CREATE UNIQUE INDEX idx_hero_stats_unique ON hero_stats(hero_id, period_type, tier_filter, patch_version);
```

---

## 7. 通知系统表

### 7.1 notifications (通知表)

```sql
CREATE TABLE notifications (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type notification_type NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    data JSONB DEFAULT '{}',
    read_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TYPE notification_type AS ENUM ('like', 'reply', 'follow', 'mention', 'system', 'prediction_result');

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_type ON notifications(type);
CREATE INDEX idx_notifications_read ON notifications(user_id, read_at);
```

---

## 8. 系统配置表

### 8.1 site_settings (网站设置表)

```sql
CREATE TABLE site_settings (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    updated_by BIGINT REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 初始化基础设置
INSERT INTO site_settings (key, value, description) VALUES
('site_name', '"刀塔情书"', '网站名称'),
('maintenance_mode', 'false', '维护模式'),
('registration_enabled', 'true', '是否允许注册'),
('expert_application_enabled', 'true', '是否允许专家申请'),
('rate_limits', '{"user": 100, "expert": 500, "admin": 1000}', '频率限制配置');
```

### 8.2 audit_logs (审计日志表)

```sql
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id BIGINT,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
```

---

## 9. 统计和分析表

### 9.1 daily_stats (每日统计表)

```sql
CREATE TABLE daily_stats (
    id BIGSERIAL PRIMARY KEY,
    stat_date DATE NOT NULL,
    total_users INTEGER DEFAULT 0,
    active_users INTEGER DEFAULT 0,
    new_users INTEGER DEFAULT 0,
    total_matches INTEGER DEFAULT 0,
    new_discussions INTEGER DEFAULT 0,
    new_articles INTEGER DEFAULT 0,
    page_views INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_daily_stats_date ON daily_stats(stat_date);
```

### 9.2 user_activity_logs (用户活动日志表)

```sql
CREATE TABLE user_activity_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id BIGINT,
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 分区表 (按月分区)
CREATE TABLE user_activity_logs_y2025m01 PARTITION OF user_activity_logs
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE INDEX idx_user_activity_logs_user_id ON user_activity_logs(user_id);
CREATE INDEX idx_user_activity_logs_action ON user_activity_logs(action);
CREATE INDEX idx_user_activity_logs_created_at ON user_activity_logs(created_at);
```

---

## 10. 触发器和函数

### 10.1 更新时间戳触发器

```sql
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 应用到所有需要的表
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_matches_updated_at
    BEFORE UPDATE ON matches
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ... 其他表类似
```

### 10.2 统计数据更新触发器

```sql
CREATE OR REPLACE FUNCTION update_discussion_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE discussions 
        SET reply_count = reply_count + 1,
            last_activity_at = NOW()
        WHERE id = NEW.discussion_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE discussions 
        SET reply_count = reply_count - 1
        WHERE id = OLD.discussion_id;
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_discussion_reply_stats
    AFTER INSERT OR DELETE ON discussion_replies
    FOR EACH ROW EXECUTE FUNCTION update_discussion_stats();
```

---

## 11. 视图定义

### 11.1 专家统计视图

```sql
CREATE VIEW expert_stats AS
SELECT 
    u.id,
    u.username,
    u.tier,
    COUNT(DISTINCT a.id) as article_count,
    COUNT(DISTINCT p.id) as prediction_count,
    COUNT(DISTINCT p.id) FILTER (WHERE p.result = 'correct') as correct_predictions,
    CASE 
        WHEN COUNT(DISTINCT p.id) > 0 
        THEN ROUND(COUNT(DISTINCT p.id) FILTER (WHERE p.result = 'correct') * 100.0 / COUNT(DISTINCT p.id), 2)
        ELSE 0 
    END as accuracy_rate,
    COUNT(DISTINCT f.follower_id) as follower_count,
    SUM(DISTINCT a.view_count) as total_article_views
FROM users u
LEFT JOIN articles a ON u.id = a.author_id AND a.status = 'published'
LEFT JOIN expert_predictions p ON u.id = p.expert_id
LEFT JOIN user_follows f ON u.id = f.following_id
WHERE u.role IN ('expert', 'admin')
GROUP BY u.id, u.username, u.tier;
```

### 11.2 热门内容视图

```sql
CREATE VIEW trending_content AS
SELECT 
    'discussion' as content_type,
    id as content_id,
    title,
    author_id,
    view_count,
    like_count,
    reply_count as interaction_count,
    created_at,
    last_activity_at as last_updated
FROM discussions
WHERE created_at > NOW() - INTERVAL '7 days'

UNION ALL

SELECT 
    'article' as content_type,
    id as content_id,
    title,
    author_id,
    view_count,
    like_count,
    comment_count as interaction_count,
    created_at,
    updated_at as last_updated
FROM articles
WHERE status = 'published' AND created_at > NOW() - INTERVAL '7 days'

ORDER BY 
    (view_count * 0.3 + like_count * 0.4 + interaction_count * 0.3) DESC,
    last_updated DESC;
```

---

## 12. 数据库优化建议

### 12.1 分区策略
- `user_activity_logs`: 按月分区
- `content_views`: 按月分区
- `audit_logs`: 按月分区

### 12.2 索引优化
- 为所有外键创建索引
- 为经常查询的字段组合创建复合索引
- 为JSON字段的常用查询路径创建表达式索引

### 12.3 缓存策略
- 使用Redis缓存热门内容
- 缓存用户会话信息
- 缓存统计数据

### 12.4 备份策略
- 每日全量备份
- 实时WAL备份
- 定期测试恢复流程

---

## 13. 数据迁移脚本

### 13.1 初始化脚本

```sql
-- 创建数据库
CREATE DATABASE dota_analysis 
WITH 
    ENCODING = 'UTF8'
    LC_COLLATE = 'zh_CN.UTF-8'
    LC_CTYPE = 'zh_CN.UTF-8';

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- 创建默认管理员用户
INSERT INTO users (username, email, password_hash, role, tier, verified) VALUES
('admin', 'admin@dotaanalysis.com', '$2b$12$...', 'admin', 'diamond', true);
```

### 13.2 示例数据脚本

```sql
-- 插入示例联赛数据
INSERT INTO leagues (name, short_name, tier, region) VALUES
('The International 2025', 'TI2025', 1, 'Global'),
('DPC Major 2025', 'DPC Major', 1, 'Global'),
('ESL One Birmingham', 'ESL One', 2, 'Europe'),
('DreamLeague Season 25', 'DreamLeague', 2, 'Europe');

-- 插入示例战队数据
INSERT INTO teams (name, tag, region) VALUES
('Team Liquid', 'TL', 'Europe'),
('Gaimin Gladiators', 'GG', 'Europe'),
('PSG.LGD', 'LGD', 'China'),
('Team Spirit', 'TS', 'CIS');
```

---

*该数据库设计文档会随着需求变化持续更新*
