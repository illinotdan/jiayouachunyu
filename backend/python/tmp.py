"""
配置文件和测试数据生成器
"""

# config/settings.py
import os
from datetime import datetime

class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dota2-analysis-secret-key'
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://username:password@localhost:5432/dota2_analysis'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Redis配置（缓存）
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # API密钥
    OPENDOTA_API_KEY = os.environ.get('OPENDOTA_API_KEY')
    STRATZ_API_KEY = os.environ.get('STRATZ_API_KEY')
    
    # 阿里云OSS配置
    OSS_CONFIG = {
        'access_key_id': os.environ.get('OSS_ACCESS_KEY_ID'),
        'access_key_secret': os.environ.get('OSS_ACCESS_KEY_SECRET'),
        'endpoint': os.environ.get('OSS_ENDPOINT') or 'oss-cn-hangzhou.aliyuncs.com',
        'bucket_name': os.environ.get('OSS_BUCKET_NAME') or 'dota2-analysis'
    }
    
    # Celery配置
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/1'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/1'
    
    # 数据同步配置
    DATA_SYNC_CONFIG = {
        'rate_limits': {
            'opendota': 1.0,
            'stratz': 0.1,
            'liquipedia': 2.0,
            'dem': 0.5
        },
        'batch_sizes': {
            'matches': 50,
            'teams': 20,
            'players': 100
        },
        'retry_attempts': 3,
        'timeout_seconds': 30
    }

# 测试数据生成器
class TestDataGenerator:
    """测试数据生成器"""
    
    def __init__(self, db_session):
        self.db = db_session
        
    def generate_all_test_data(self):
        """生成所有测试数据"""
        print("开始生成测试数据...")
        
        # 1. 生成英雄数据
        heroes = self.generate_heroes()
        print(f"生成 {len(heroes)} 个英雄")
        
        # 2. 生成物品数据
        items = self.generate_items()
        print(f"生成 {len(items)} 个物品")
        
        # 3. 生成联赛数据
        leagues = self.generate_leagues()
        print(f"生成 {len(leagues)} 个联赛")
        
        # 4. 生成战队数据
        teams = self.generate_teams()
        print(f"生成 {len(teams)} 个战队")
        
        # 5. 生成选手数据
        players = self.generate_players(teams)
        print(f"生成 {len(players)} 个选手")
        
        # 6. 生成比赛数据
        matches = self.generate_matches(leagues, teams)
        print(f"生成 {len(matches)} 场比赛")
        
        # 7. 生成比赛选手数据
        match_players = self.generate_match_players(matches, players, heroes)
        print(f"生成 {len(match_players)} 条比赛选手记录")
        
        # 8. 生成Pick/Ban数据
        drafts = self.generate_match_drafts(matches, heroes)
        print(f"生成 {len(drafts)} 条Pick/Ban记录")
        
        # 9. 生成比赛分析数据
        analyses = self.generate_match_analyses(matches)
        print(f"生成 {len(analyses)} 条比赛分析")
        
        self.db.commit()
        print("测试数据生成完成！")
        
        return {
            'heroes': len(heroes),
            'items': len(items),
            'leagues': len(leagues),
            'teams': len(teams),
            'players': len(players),
            'matches': len(matches),
            'match_players': len(match_players),
            'drafts': len(drafts),
            'analyses': len(analyses)
        }
    
    def generate_heroes(self):
        """生成英雄测试数据"""
        from models.match import Hero
        
        sample_heroes = [
            {'id': 1, 'name': 'antimage', 'display_name': '敌法师', 'primary_attribute': 'agility', 'roles': ['Carry', 'Escape'], 'complexity': 1},
            {'id': 2, 'name': 'axe', 'display_name': '斧王', 'primary_attribute': 'strength', 'roles': ['Initiator', 'Durable'], 'complexity': 1},
            {'id': 3, 'name': 'bane', 'display_name': '祸乱之源', 'primary_attribute': 'intelligence', 'roles': ['Support', 'Disabler'], 'complexity': 2},
            {'id': 4, 'name': 'crystal_maiden', 'display_name': '水晶室女', 'primary_attribute': 'intelligence', 'roles': ['Support', 'Nuker'], 'complexity': 1},
            {'id': 5, 'name': 'pudge', 'display_name': '屠夫', 'primary_attribute': 'strength', 'roles': ['Disabler', 'Durable'], 'complexity': 2},
            {'id': 6, 'name': 'invoker', 'display_name': '祈求者', 'primary_attribute': 'intelligence', 'roles': ['Nuker', 'Escape'], 'complexity': 3},
            {'id': 7, 'name': 'shadow_fiend', 'display_name': '影魔', 'primary_attribute': 'agility', 'roles': ['Carry', 'Nuker'], 'complexity': 2},
            {'id': 8, 'name': 'drow_ranger', 'display_name': '卓尔游侠', 'primary_attribute': 'agility', 'roles': ['Carry', 'Pusher'], 'complexity': 1},
            {'id': 9, 'name': 'zeus', 'display_name': '宙斯', 'primary_attribute': 'intelligence', 'roles': ['Nuker'], 'complexity': 1},
            {'id': 10, 'name': 'lina', 'display_name': '莉娜', 'primary_attribute': 'intelligence', 'roles': ['Support', 'Nuker'], 'complexity': 1}
        ]
        
        heroes = []
        for hero_data in sample_heroes:
            existing = Hero.query.filter_by(id=hero_data['id']).first()
            if not existing:
                hero = Hero(
                    id=hero_data['id'],
                    name=hero_data['name'],
                    display_name=hero_data['display_name'],
                    primary_attribute=Hero.Attribute(hero_data['primary_attribute']),
                    roles=hero_data['roles'],
                    complexity=hero_data['complexity'],
                    is_active=True
                )
                self.db.add(hero)
                heroes.append(hero)
        
        return heroes
    
    def generate_items(self):
        """生成物品测试数据"""
        sample_items = [
            {'id': 1, 'name': 'blink', 'display_name': '闪烁匕首', 'cost': 2250, 'category': 'consumables'},
            {'id': 2, 'name': 'black_king_bar', 'display_name': '黑皇杖', 'cost': 4050, 'category': 'armaments'},
            {'id': 3, 'name': 'divine_rapier', 'display_name': '圣剑', 'cost': 6000, 'category': 'artifacts'},
            {'id': 4, 'name': 'boots_of_travel', 'display_name': '远行鞋', 'cost': 2400, 'category': 'upgrades'},
            {'id': 5, 'name': 'aghanims_scepter', 'display_name': '阿哈利姆神杖', 'cost': 4200, 'category': 'upgrades'},
        ]
        
        items = []
        for item_data in sample_items:
            # 这里假设你有Item模型，需要根据实际模型调整
            pass  # 暂时跳过，专注于核心比赛数据
        
        return items
    
    def generate_leagues(self):
        """生成联赛测试数据"""
        from models.match import League
        
        sample_leagues = [
            {'name': 'The International 2024', 'short_name': 'TI12', 'tier': 1, 'prize_pool': 15000000, 'region': 'Global'},
            {'name': 'Dota Pro Circuit 2024', 'short_name': 'DPC', 'tier': 1, 'prize_pool': 5000000, 'region': 'Global'},
            {'name': 'ESL One Stockholm', 'short_name': 'ESL', 'tier': 2, 'prize_pool': 1000000, 'region': 'Europe'},
            {'name': '完美世界联赛', 'short_name': 'PWL', 'tier': 2, 'prize_pool': 800000, 'region': 'China'},
            {'name': 'BLAST Premier', 'short_name': 'BLAST', 'tier': 2, 'prize_pool': 600000, 'region': 'Europe'}
        ]
        
        leagues = []
        for league_data in sample_leagues:
            league = League(
                name=league_data['name'],
                short_name=league_data['short_name'],
                tier=league_data['tier'],
                prize_pool=league_data['prize_pool'],
                region=league_data['region'],
                start_date=datetime.now().date(),
                is_active=True
            )
            self.db.add(league)
            leagues.append(league)
        
        return leagues
    
    def generate_teams(self):
        """生成战队测试数据"""
        from models.match import Team
        
        sample_teams = [
            {'name': 'Team Spirit', 'tag': 'SPIRIT', 'region': 'Europe', 'logo_url': 'https://example.com/spirit.png'},
            {'name': 'PSG.LGD', 'tag': 'LGD', 'region': 'China', 'logo_url': 'https://example.com/lgd.png'},
            {'name': 'OG', 'tag': 'OG', 'region': 'Europe', 'logo_url': 'https://example.com/og.png'},
            {'name': 'Team Secret', 'tag': 'SECRET', 'region': 'Europe', 'logo_url': 'https://example.com/secret.png'},
            {'name': 'Evil Geniuses', 'tag': 'EG', 'region': 'North America', 'logo_url': 'https://example.com/eg.png'},
            {'name': 'Virtus.pro', 'tag': 'VP', 'region': 'Europe', 'logo_url': 'https://example.com/vp.png'},
            {'name': 'T1', 'tag': 'T1', 'region': 'Southeast Asia', 'logo_url': 'https://example.com/t1.png'},
            {'name': 'Team Liquid', 'tag': 'LIQUID', 'region': 'Europe', 'logo_url': 'https://example.com/liquid.png'},
            {'name': 'Fnatic', 'tag': 'FNATIC', 'region': 'Southeast Asia', 'logo_url': 'https://example.com/fnatic.png'},
            {'name': 'Alliance', 'tag': 'ALLIANCE', 'region': 'Europe', 'logo_url': 'https://example.com/alliance.png'}
        ]
        
        teams = []
        for team_data in sample_teams:
            team = Team(
                name=team_data['name'],
                tag=team_data['tag'],
                region=team_data['region'],
                logo_url=team_data['logo_url'],
                is_active=True
            )
            self.db.add(team)
            teams.append(team)
        
        return teams
    
    def generate_players(self, teams):
        """生成选手测试数据"""
        from models.match import Player
        import random
        
        sample_players = [
            {'name': 'TORONTOTOKYO', 'real_name': 'Alexander Khertek', 'position': 1, 'country': 'RU'},
            {'name': 'Collapse', 'real_name': 'Magomed Khalilov', 'position': 3, 'country': 'RU'},
            {'name': 'Mira', 'real_name': 'Miroslav Kolpakov', 'position': 4, 'country': 'RU'},
            {'name': 'Miposhka', 'real_name': 'Yaroslav Naidenov', 'position': 5, 'country': 'RU'},
            {'name': 'Yatoro', 'real_name': 'Illya Mulyarchuk', 'position': 2, 'country': 'UA'},
            {'name': 'Ame', 'real_name': 'Wang Chunyu', 'position': 1, 'country': 'CN'},
            {'name': 'NothingToSay', 'real_name': 'Cheng Jin Xiang', 'position': 2, 'country': 'MY'},
            {'name': 'faith_bian', 'real_name': 'Zhang Ruida', 'position': 3, 'country': 'CN'},
            {'name': 'XinQ', 'real_name': 'Zhao Zixing', 'position': 4, 'country': 'CN'},
            {'name': 'y`', 'real_name': 'Zhang Yiping', 'position': 5, 'country': 'CN'}
        ]
        
        players = []
        for i, player_data in enumerate(sample_players):
            team = teams[i // 5] if i < len(teams) * 5 else random.choice(teams)
            
            player = Player(
                steam_id=f"7656119{80000000 + i:08d}",
                account_id=80000000 + i,
                name=player_data['name'],
                real_name=player_data['real_name'],
                position=player_data['position'],
                country=player_data['country'],
                current_team_id=team.id,
                is_active=True
            )
            self.db.add(player)
            players.append(player)
        
        return players
    
    def generate_matches(self, leagues, teams):
        """生成比赛测试数据"""
        from models.match import Match, MatchStatus
        import random
        from datetime import datetime, timedelta
        
        matches = []
        for i in range(10):  # 生成10场比赛
            radiant_team = random.choice(teams)
            dire_team = random.choice([t for t in teams if t.id != radiant_team.id])
            league = random.choice(leagues)
            
            # 随机生成比赛时间（最近7天内）
            start_time = datetime.utcnow() - timedelta(
                hours=random.randint(1, 168)  # 1-168小时前
            )
            
            # 随机比赛结果
            radiant_win = random.choice([True, False])
            duration = random.randint(1800, 4200)  # 30-70分钟
            
            match = Match(
                match_id=f"match_{7000000000 + i}",
                league_id=league.id,
                radiant_team_id=radiant_team.id,
                dire_team_id=dire_team.id,
                radiant_score=1 if radiant_win else 0,
                dire_score=0 if radiant_win else 1,
                radiant_win=radiant_win,
                duration=duration,
                start_time=start_time,
                end_time=start_time + timedelta(seconds=duration),
                status=MatchStatus.FINISHED,
                game_mode='ranked',
                patch_version='7.34d',
                region=radiant_team.region,
                data_sources={'opendota': True, 'stratz': True},
                data_quality_score=85
            )
            self.db.add(match)
            matches.append(match)
        
        return matches
    
    def generate_match_players(self, matches, players, heroes):
        """生成比赛选手数据"""
        from models.match import MatchPlayer, TeamSide
        import random
        
        match_players = []
        
        for match in matches:
            # 获取两队选手
            radiant_players = [p for p in players if p.current_team_id == match.radiant_team_id][:5]
            dire_players = [p for p in players if p.current_team_id == match.dire_team_id][:5]
            
            # 随机选择英雄
            used_heroes = set()
            
            # Radiant队选手
            for i, player in enumerate(radiant_players):
                available_heroes = [h for h in heroes if h.id not in used_heroes]
                if available_heroes:
                    hero = random.choice(available_heroes)
                    used_heroes.add(hero.id)
                    
                    # 根据位置生成不同的数据范围
                    position = i + 1
                    if position == 1:  # 大哥
                        kills = random.randint(5, 15)
                        deaths = random.randint(2, 8)
                        assists = random.randint(3, 12)
                        gpm = random.randint(600, 800)
                        xpm = random.randint(600, 750)
                        last_hits = random.randint(250, 400)
                    elif position in [2, 3]:  # 中单/三号位
                        kills = random.randint(3, 12)
                        deaths = random.randint(3, 10)
                        assists = random.randint(5, 15)
                        gpm = random.randint(400, 650)
                        xpm = random.randint(500, 650)
                        last_hits = random.randint(150, 300)
                    else:  # 四五号位
                        kills = random.randint(1, 8)
                        deaths = random.randint(4, 12)
                        assists = random.randint(8, 20)
                        gpm = random.randint(250, 450)
                        xpm = random.randint(350, 500)
                        last_hits = random.randint(20, 100)
                    
                    match_player = MatchPlayer(
                        match_id=match.id,
                        player_id=player.id,
                        account_id=player.account_id,
                        player_name=player.name,
                        team_side=TeamSide.RADIANT,
                        player_slot=i,
                        hero_id=hero.id,
                        kills=kills,
                        deaths=deaths,
                        assists=assists,
                        last_hits=last_hits,
                        denies=random.randint(5, 30),
                        gold_per_min=gpm,
                        exp_per_min=xpm,
                        net_worth=gpm * (match.duration // 60),
                        hero_damage=random.randint(15000, 50000),
                        tower_damage=random.randint(1000, 8000),
                        hero_healing=random.randint(500, 5000),
                        level=random.randint(20, 25),
                        items=[1, 2, 3, 4, 5, 6]  # 简化的装备ID
                    )
                    self.db.add(match_player)
                    match_players.append(match_player)
            
            # Dire队选手（类似逻辑）
            for i, player in enumerate(dire_players):
                available_heroes = [h for h in heroes if h.id not in used_heroes]
                if available_heroes:
                    hero = random.choice(available_heroes)
                    used_heroes.add(hero.id)
                    
                    position = i + 1
                    if position == 1:
                        kills = random.randint(5, 15)
                        deaths = random.randint(2, 8)
                        assists = random.randint(3, 12)
                        gpm = random.randint(600, 800)
                        xpm = random.randint(600, 750)
                        last_hits = random.randint(250, 400)
                    elif position in [2, 3]:
                        kills = random.randint(3, 12)
                        deaths = random.randint(3, 10)
                        assists = random.randint(5, 15)
                        gpm = random.randint(400, 650)
                        xpm = random.randint(500, 650)
                        last_hits = random.randint(150, 300)
                    else:
                        kills = random.randint(1, 8)
                        deaths = random.randint(4, 12)
                        assists = random.randint(8, 20)
                        gpm = random.randint(250, 450)
                        xpm = random.randint(350, 500)
                        last_hits = random.randint(20, 100)
                    
                    match_player = MatchPlayer(
                        match_id=match.id,
                        player_id=player.id,
                        account_id=player.account_id,
                        player_name=player.name,
                        team_side=TeamSide.DIRE,
                        player_slot=i + 128,  # Dire队的slot是128+
                        hero_id=hero.id,
                        kills=kills,
                        deaths=deaths,
                        assists=assists,
                        last_hits=last_hits,
                        denies=random.randint(5, 30),
                        gold_per_min=gpm,
                        exp_per_min=xpm,
                        net_worth=gpm * (match.duration // 60),
                        hero_damage=random.randint(15000, 50000),
                        tower_damage=random.randint(1000, 8000),
                        hero_healing=random.randint(500, 5000),
                        level=random.randint(20, 25),
                        items=[1, 2, 3, 4, 5, 6]
                    )
                    self.db.add(match_player)
                    match_players.append(match_player)
        
        return match_players
    
    def generate_match_drafts(self, matches, heroes):
        """生成Pick/Ban数据"""
        import random
        
        drafts = []
        
        for match in matches:
            used_heroes = set()
            order = 1
            
            # 标准BP顺序：Ban-Ban-Ban-Ban-Pick-Pick-Pick-Pick-Ban-Ban-Pick-Pick-Pick-Pick-Ban-Ban-Pick-Pick-Pick-Pick
            bp_sequence = [
                ('ban', 'radiant'), ('ban', 'dire'), ('ban', 'radiant'), ('ban', 'dire'),
                ('pick', 'radiant'), ('pick', 'dire'), ('pick', 'dire'), ('pick', 'radiant'),
                ('ban', 'dire'), ('ban', 'radiant'), ('pick', 'dire'), ('pick', 'radiant'),
                ('pick', 'radiant'), ('pick', 'dire'), ('ban', 'radiant'), ('ban', 'dire'),
                ('pick', 'radiant'), ('pick', 'dire'), ('pick', 'dire'), ('pick', 'radiant')
            ]
            
            for action, team_side in bp_sequence:
                available_heroes = [h for h in heroes if h.id not in used_heroes]
                if available_heroes:
                    hero = random.choice(available_heroes)
                    used_heroes.add(hero.id)
                    
                    from models.match import MatchDraft
                    draft = MatchDraft(
                        match_id=match.id,
                        hero_id=hero.id,
                        team_side=team_side,
                        is_pick=(action == 'pick'),
                        order_number=order,
                        phase=1 if order <= 8 else (2 if order <= 14 else 3)
                    )
                    self.db.add(draft)
                    drafts.append(draft)
                    order += 1
        
        return drafts
    
    def generate_match_analyses(self, matches):
        """生成比赛分析数据"""
        from models.match import MatchAnalysis
        import random
        
        analyses = []
        
        for match in matches:
            # 随机生成分析数据
            key_moments = [
                {"time": "02:30", "event": "first_blood", "description": "Radiant获得一血"},
                {"time": "12:45", "event": "first_tower", "description": "Dire推倒第一座塔"},
                {"time": "25:20", "event": "roshan", "description": "Radiant击杀肉山"},
                {"time": "38:15", "event": "teamfight", "description": "关键团战，Dire团灭Radiant"}
            ]
            
            analysis = MatchAnalysis(
                match_id=match.id,
                first_blood_time=random.randint(60, 300),  # 1-5分钟
                first_blood_player=f"Player_{random.randint(1, 10)}",
                first_tower_time=random.randint(600, 1200),  # 10-20分钟
                key_moments=key_moments,
                mvp_player=f"Player_{random.randint(1, 10)}",
                analysis_confidence=random.randint(75, 95),
                ai_analysis={
                    "game_pace": random.choice(["slow", "medium", "fast"]),
                    "winning_factor": random.choice(["early_game", "mid_game", "late_game", "teamfight"]),
                    "draft_advantage": random.choice(["radiant", "dire", "balanced"])
                }
            )
            self.db.add(analysis)
            analyses.append(analysis)
        
        return analyses

# 使用示例脚本
def init_test_database():
    """初始化测试数据库"""
    from config.database import db
    from models.match import Hero, Team, Player, League, Match, MatchPlayer, MatchAnalysis
    
    print("初始化测试数据库...")
    
    # 创建所有表
    db.create_all()
    
    # 生成测试数据
    generator = TestDataGenerator(db.session)
    results = generator.generate_all_test_data()
    
    print("数据库初始化完成！")
    print(f"生成的数据统计: {results}")
    
    return results

if __name__ == "__main__":
    # 运行测试数据生成
    results = init_test_database()
    
    # 验证数据
    from models.match import Match, Team, Player
    
    match_count = Match.query.count()
    team_count = Team.query.count() 
    player_count = Player.query.count()
    
    print(f"\n数据验证:")
    print(f"比赛数量: {match_count}")
    print(f"战队数量: {team_count}")
    print(f"选手数量: {player_count}")
    
    # 显示一场比赛的详细信息
    sample_match = Match.query.first()
    if sample_match:
        print(f"\n示例比赛:")
        print(f"比赛ID: {sample_match.match_id}")
        print(f"对阵: {sample_match.radiant_team.name} vs {sample_match.dire_team.name}")
        print(f"结果: {'Radiant' if sample_match.radiant_win else 'Dire'} 获胜")
        print(f"时长: {sample_match.duration // 60}:{sample_match.duration % 60:02d}")
        print(f"选手数据: {sample_match.players.count()} 条记录")