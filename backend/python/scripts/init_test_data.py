#!/usr/bin/env python3
"""
测试数据生成和数据库初始化脚本
用于生成Dota2战队分析系统的测试数据
"""

import asyncio
import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import sys
import os

# 添加项目路径到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db
from config.settings import Config
from models.match import Match, MatchDraft, League, Team, Player
from models.user import User
from models.content import Hero, Item
from models.audit import AuditLog
from models.learning import LearningProgress
from models.notification import Notification


class TestDataGenerator:
    """测试数据生成器"""
    
    def __init__(self, session):
        self.session = session
        self.heroes = []
        self.items = []
        self.teams = []
        self.players = []
        self.leagues = []
        self.matches = []
        
        # Dota2相关数据
        self.hero_names = [
            'Anti-Mage', 'Axe', 'Bane', 'Bloodseeker', 'Crystal Maiden',
            'Drow Ranger', 'Earthshaker', 'Juggernaut', 'Mirana', 'Shadow Fiend',
            'Morphling', 'Phantom Lancer', 'Puck', 'Pudge', 'Razor',
            'Sand King', 'Storm Spirit', 'Sven', 'Tiny', 'Vengeful Spirit',
            'Windranger', 'Zeus', 'Kunkka', 'Lina', 'Lion',
            'Shadow Shaman', 'Slardar', 'Tidehunter', 'Witch Doctor', 'Riki'
        ]
        
        self.item_names = [
            'Abyssal Blade', 'Aghanim\'s Scepter', 'Assault Cuirass', 'Black King Bar',
            'Blink Dagger', 'Bloodthorn', 'Butterfly', 'Crimson Guard',
            'Daedalus', 'Desolator', 'Diffusal Blade', 'Divine Rapier',
            'Dragon Lance', 'Drum of Endurance', 'Eul\'s Scepter', 'Force Staff',
            'Guardian Greaves', 'Heart of Tarrasque', 'Heaven\'s Halberd', 'Helm of the Dominator',
            'Hood of Defiance', 'Hurricane Pike', 'Linken\'s Sphere', 'Lotus Orb',
            'Maelstrom', 'Manta Style', 'Mask of Madness', 'Medallion of Courage',
            'Mekansm', 'Mjollnir', 'Monkey King Bar', 'Necronomicon',
            'Nullifier', 'Octarine Core', 'Orchid Malevolence', 'Pipe of Insight',
            'Radiance', 'Refresher Orb', 'Rod of Atos', 'Scythe of Vyse',
            'Shiva\'s Guard', 'Silver Edge', 'Skull Basher', 'Solar Crest'
        ]
        
        self.team_names = [
            'Team Secret', 'OG', 'Virtus.pro', 'Evil Geniuses', 'PSG.LGD',
            'Vici Gaming', 'Team Liquid', 'Alliance', 'Natus Vincere', 'Fnatic',
            'Cloud9', 'Digital Chaos', 'Newbee', 'Wings Gaming', 'Invictus Gaming',
            'LGD Gaming', 'EHOME', 'CDEC Gaming', 'Complexity Gaming', 'Mousesports'
        ]
        
        self.league_names = [
            'The International', 'ESL One', 'DreamLeague', 'MDL', 'Summit',
            'StarLadder', 'PGL', 'Epicenter', 'Manila Masters', 'Boston Major',
            'Kiev Major', 'Anaheim Major', 'Chongqing Major', 'Stockholm Major', 'Birmingham Major',
            'Chengdu Major', 'Leipzig Major', 'Los Angeles Major', 'Singapore Major', 'Kyiv Major'
        ]
        
        self.player_names = [
            'Miracle-', 'N0tail', 'Puppey', 'Arteezy', 'SumaiL',
            'S4', 'Fly', 'Crit-', 'Universe', 'Fear',
            'Dendi', 'XBOCT', 'Pasha', 'LightOfHeaven', 'ARS-ART',
            'Ferrari_430', 'YYF', 'Chuan', 'Faith', 'Zhou',
            'xiao8', 'Sylar', 'Maybe', 'Somnus', 'fy',
            'rOtk', 'LaNm', 'Mushi', 'Ohaiyo', 'Net'
        ]
        
        # 位置映射
        self.positions = ['position_1', 'position_2', 'position_3', 'position_4', 'position_5']
        
        # 比赛状态
        self.match_statuses = ['upcoming', 'live', 'finished', 'cancelled']
        
        # 战队排名
        self.team_rankings = list(range(1, 21))

    def generate_heroes(self, count: int = 30):
        """生成英雄数据"""
        print(f"生成 {count} 个英雄数据...")
        
        for i in range(count):
            hero = Hero(
                hero_id=i + 1,
                name=self.hero_names[i % len(self.hero_names)],
                display_name=self.hero_names[i % len(self.hero_names)],
                primary_attr=random.choice(['strength', 'agility', 'intelligence']),
                attack_type=random.choice(['melee', 'ranged']),
                roles=random.sample(['carry', 'support', 'nuker', 'disabler', 'jungler', 'durable', 'escape', 'pusher', 'initiator'], random.randint(2, 4)),
                base_health=random.randint(500, 800),
                base_health_regen=random.uniform(0.5, 3.0),
                base_mana=random.randint(200, 400),
                base_mana_regen=random.uniform(0.5, 2.0),
                base_armor=random.uniform(-2, 5),
                base_mr=random.uniform(15, 35),
                base_attack_min=random.randint(20, 60),
                base_attack_max=random.randint(40, 80),
                base_strength=random.randint(15, 30),
                base_agility=random.randint(15, 30),
                base_intelligence=random.randint(15, 30),
                strength_gain=random.uniform(1.0, 4.0),
                agility_gain=random.uniform(1.0, 4.0),
                intelligence_gain=random.uniform(1.0, 4.0),
                attack_range=random.randint(150, 700),
                projectile_speed=random.randint(600, 1200) if random.choice([True, False]) else None,
                attack_rate=random.uniform(1.4, 2.0),
                move_speed=random.randint(280, 330),
                turn_rate=random.uniform(0.4, 1.0),
                cm_enabled=random.choice([True, False]),
                legs=random.randint(0, 4),
                image_url=f"https://cdn.dota2.com/apps/dota2/images/heroes/{self.hero_names[i % len(self.hero_names)].lower().replace(' ', '_')}_full.png",
                icon_url=f"https://cdn.dota2.com/apps/dota2/images/heroes/{self.hero_names[i % len(self.hero_names)].lower().replace(' ', '_')}_icon.png",
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 365))
            )
            self.session.add(hero)
            self.heroes.append(hero)
        
        self.session.commit()
        print(f"成功生成 {len(self.heroes)} 个英雄数据")

    def generate_items(self, count: int = 40):
        """生成物品数据"""
        print(f"生成 {count} 个物品数据...")
        
        for i in range(count):
            item = Item(
                item_id=i + 1,
                name=self.item_names[i % len(self.item_names)],
                display_name=self.item_names[i % len(self.item_names)],
                description=f"{self.item_names[i % len(self.item_names)]} 是一件强大的物品",
                cost=random.randint(500, 8000),
                secret_shop=random.choice([True, False]),
                side_shop=random.choice([True, False]),
                recipe=random.choice([True, False]),
                localized_name=self.item_names[i % len(self.item_names)],
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 365))
            )
            self.session.add(item)
            self.items.append(item)
        
        self.session.commit()
        print(f"成功生成 {len(self.items)} 个物品数据")

    def generate_teams(self, count: int = 10):
        """生成战队数据"""
        print(f"生成 {count} 个战队数据...")
        
        for i in range(count):
            team = Team(
                team_id=i + 1,
                name=self.team_names[i % len(self.team_names)],
                tag=self.team_names[i % len(self.team_names)].replace(' ', '').replace('.', ''),
                logo_url=f"https://cdn.dota2.com/teams/{i + 1}.png",
                country=random.choice(['China', 'USA', 'Russia', 'Sweden', 'Germany', 'Philippines', 'Malaysia', 'Ukraine', 'Canada', 'Australia']),
                ranking=self.team_rankings[i % len(self.team_rankings)],
                rating=random.uniform(1000, 2000),
                wins=random.randint(50, 200),
                losses=random.randint(20, 150),
                is_professional=random.choice([True, False]),
                created_at=datetime.utcnow() - timedelta(days=random.randint(30, 365))
            )
            self.session.add(team)
            self.teams.append(team)
        
        self.session.commit()
        print(f"成功生成 {len(self.teams)} 个战队数据")

    def generate_players(self, count: int = 50):
        """生成选手数据"""
        print(f"生成 {count} 个选手数据...")
        
        for i in range(count):
            # 随机分配到战队
            team = random.choice(self.teams) if self.teams else None
            
            player = Player(
                player_id=i + 1,
                name=self.player_names[i % len(self.player_names)],
                steam_id=f"76561198{random.randint(10000000, 99999999)}",
                avatar_url=f"https://cdn.dota2.com/players/{i + 1}.jpg",
                country=random.choice(['China', 'USA', 'Russia', 'Sweden', 'Germany', 'Philippines', 'Malaysia', 'Ukraine', 'Canada', 'Australia']),
                team_id=team.team_id if team else None,
                position=random.choice(self.positions),
                mmr=random.randint(6000, 11000),
                rank=random.choice(['Immortal', 'Divine', 'Ancient', 'Legend', 'Archon', 'Crusader', 'Guardian', 'Herald']),
                wins=random.randint(100, 1000),
                losses=random.randint(50, 500),
                is_professional=random.choice([True, False]),
                created_at=datetime.utcnow() - timedelta(days=random.randint(30, 365))
            )
            self.session.add(player)
            self.players.append(player)
        
        self.session.commit()
        print(f"成功生成 {len(self.players)} 个选手数据")

    def generate_leagues(self, count: int = 10):
        """生成联赛数据"""
        print(f"生成 {count} 个联赛数据...")
        
        for i in range(count):
            league = League(
                league_id=i + 1,
                name=self.league_names[i % len(self.league_names)],
                description=f"{self.league_names[i % len(self.league_names)]} 是一项顶级Dota2赛事",
                prize_pool=random.randint(100000, 40000000),
                tier=random.choice(['premium', 'professional', 'major', 'minor']),
                region=random.choice(['global', 'china', 'europe', 'americas', 'se_asia']),
                status=random.choice(['upcoming', 'ongoing', 'completed']),
                start_date=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
                end_date=datetime.utcnow() + timedelta(days=random.randint(1, 60)),
                logo_url=f"https://cdn.dota2.com/leagues/{i + 1}.png",
                created_at=datetime.utcnow() - timedelta(days=random.randint(30, 365))
            )
            self.session.add(league)
            self.leagues.append(league)
        
        self.session.commit()
        print(f"成功生成 {len(self.leagues)} 个联赛数据")

    def generate_matches(self, count: int = 20):
        """生成比赛数据"""
        print(f"生成 {count} 个比赛数据...")
        
        for i in range(count):
            # 随机选择两个不同的战队
            team1 = random.choice(self.teams)
            team2 = random.choice([t for t in self.teams if t.team_id != team1.team_id])
            
            # 随机选择联赛
            league = random.choice(self.leagues) if self.leagues else None
            
            # 随机比赛状态
            status = random.choice(self.match_statuses)
            
            # 生成比赛时间
            start_time = datetime.utcnow() - timedelta(days=random.randint(0, 30))
            
            if status == 'finished':
                duration = random.randint(1800, 3600)  # 30-60分钟
                end_time = start_time + timedelta(seconds=duration)
                radiant_win = random.choice([True, False])
            elif status == 'live':
                duration = random.randint(300, 1800)  # 5-30分钟
                end_time = None
                radiant_win = None
            else:
                duration = None
                end_time = None
                radiant_win = None
            
            match = Match(
                match_id=i + 1,
                league_id=league.league_id if league else None,
                radiant_team_id=team1.team_id,
                dire_team_id=team2.team_id,
                radiant_win=radiant_win,
                duration=duration,
                start_time=start_time,
                end_time=end_time,
                status=status,
                game_mode=random.choice(['all_pick', 'captains_mode', 'random_draft', 'single_draft']),
                lobby_type=random.choice(['ranked', 'casual', 'tournament']),
                cluster=random.randint(100, 200),
                radiant_score=random.randint(0, 50) if status == 'finished' else None,
                dire_score=random.randint(0, 50) if status == 'finished' else None,
                data_sources=random.sample(['opendota', 'stratz', 'dem'], random.randint(1, 3)),
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30))
            )
            self.session.add(match)
            self.matches.append(match)
        
        self.session.commit()
        print(f"成功生成 {len(self.matches)} 个比赛数据")

    def generate_match_players(self):
        """生成比赛选手数据"""
        print("生成比赛选手数据...")
        
        for match in self.matches:
            # 为每个位置生成选手数据
            for position in range(1, 11):  # 1-5: 天辉, 6-10: 夜魇
                is_radiant = position <= 5
                team_id = match.radiant_team_id if is_radiant else match.dire_team_id
                
                # 随机选择英雄
                hero = random.choice(self.heroes) if self.heroes else None
                
                # 根据位置设置不同的数据范围
                if position in [1, 6]:  # 核心位置
                    kills = random.randint(5, 20)
                    deaths = random.randint(2, 10)
                    assists = random.randint(5, 15)
                    gold_per_min = random.randint(400, 700)
                    xp_per_min = random.randint(400, 600)
                    hero_damage = random.randint(15000, 30000)
                    tower_damage = random.randint(2000, 8000)
                    hero_healing = random.randint(0, 1000)
                elif position in [2, 7]:  # 中单
                    kills = random.randint(8, 18)
                    deaths = random.randint(3, 12)
                    assists = random.randint(8, 18)
                    gold_per_min = random.randint(350, 650)
                    xp_per_min = random.randint(450, 650)
                    hero_damage = random.randint(18000, 35000)
                    tower_damage = random.randint(1000, 5000)
                    hero_healing = random.randint(0, 500)
                elif position in [3, 8]:  # 劣势路
                    kills = random.randint(3, 15)
                    deaths = random.randint(5, 15)
                    assists = random.randint(10, 25)
                    gold_per_min = random.randint(250, 500)
                    xp_per_min = random.randint(300, 500)
                    hero_damage = random.randint(10000, 25000)
                    tower_damage = random.randint(500, 3000)
                    hero_healing = random.randint(0, 2000)
                elif position in [4, 9]:  # 辅助
                    kills = random.randint(2, 12)
                    deaths = random.randint(6, 18)
                    assists = random.randint(15, 30)
                    gold_per_min = random.randint(150, 350)
                    xp_per_min = random.randint(200, 400)
                    hero_damage = random.randint(5000, 15000)
                    tower_damage = random.randint(100, 1000)
                    hero_healing = random.randint(1000, 5000)
                else:  # 5号位
                    kills = random.randint(1, 10)
                    deaths = random.randint(8, 20)
                    assists = random.randint(18, 35)
                    gold_per_min = random.randint(100, 300)
                    xp_per_min = random.randint(150, 350)
                    hero_damage = random.randint(3000, 12000)
                    tower_damage = random.randint(50, 500)
                    hero_healing = random.randint(2000, 8000)
                
                match_player = MatchDraft(
                    match_id=match.match_id,
                    player_slot=position - 1 if is_radiant else position - 6 + 128,
                    account_id=random.randint(100000000, 999999999),
                    hero_id=hero.hero_id if hero else random.randint(1, 30),
                    kills=kills,
                    deaths=deaths,
                    assists=assists,
                    gold_per_min=gold_per_min,
                    xp_per_min=xp_per_min,
                    level=random.randint(1, 25),
                    gold=random.randint(1000, 30000),
                    gold_spent=random.randint(1000, 25000),
                    hero_damage=hero_damage,
                    tower_damage=tower_damage,
                    hero_healing=hero_healing,
                    last_hits=random.randint(50, 400),
                    denies=random.randint(0, 100),
                    items=random.sample([item.item_id for item in self.items[:6]] if self.items else list(range(1, 7)), 6),
                    backpack=random.sample([item.item_id for item in self.items[:3]] if self.items else list(range(1, 4)), 3),
                    is_radiant=is_radiant,
                    team_id=team_id,
                    position=self.positions[(position - 1) % 5] if is_radiant else self.positions[(position - 6) % 5],
                    created_at=datetime.utcnow()
                )
                self.session.add(match_player)
        
        self.session.commit()
        print("成功生成比赛选手数据")

    def generate_match_drafts(self):
        """生成比赛Pick/Ban数据"""
        print("生成比赛Pick/Ban数据...")
        
        for match in self.matches:
            if match.status != 'finished':
                continue
                
            # 生成Ban阶段数据
            banned_heroes = random.sample(self.heroes, 20) if len(self.heroes) >= 20 else self.heroes
            
            for i, hero in enumerate(banned_heroes[:20]):
                draft = MatchDraft(
                    match_id=match.match_id,
                    pick=False,  # Ban
                    team='radiant' if i % 2 == 0 else 'dire',
                    hero_id=hero.hero_id,
                    order=i + 1,
                    created_at=datetime.utcnow()
                )
                self.session.add(draft)
            
            # 生成Pick阶段数据
            picked_heroes = random.sample([h for h in self.heroes if h not in banned_heroes[:20]], 20) if len([h for h in self.heroes if h not in banned_heroes[:20]]) >= 20 else [h for h in self.heroes if h not in banned_heroes[:20]]
            
            for i, hero in enumerate(picked_heroes[:20]):
                draft = MatchDraft(
                    match_id=match.match_id,
                    pick=True,  # Pick
                    team='radiant' if i % 2 == 0 else 'dire',
                    hero_id=hero.hero_id,
                    order=i + 21,  # Pick阶段从21开始
                    created_at=datetime.utcnow()
                )
                self.session.add(draft)
        
        self.session.commit()
        print("成功生成比赛Pick/Ban数据")

    def generate_match_analyses(self):
        """生成比赛分析数据"""
        print("生成比赛分析数据...")
        
        for match in self.matches:
            if match.status != 'finished':
                continue
                
            # 生成简单的比赛分析
            analysis = {
                'match_id': match.match_id,
                'analysis_type': 'post_match',
                'content': f"比赛 {match.match_id} 分析：",
                'data': {
                    'key_moments': [
                        {'time': 600, 'description': 'First blood'},
                        {'time': 1200, 'description': 'Team fight at Roshan'},
                        {'time': 1800, 'description': 'Final push'}
                    ],
                    'performance': {
                        'radiant': {'score': random.randint(60, 95), 'highlights': ['Good early game', 'Strong team coordination']},
                        'dire': {'score': random.randint(60, 95), 'highlights': ['Good late game', 'Individual skill']}
                    }
                },
                'created_at': datetime.utcnow()
            }
            
            # 这里可以保存到专门的分析表或作为JSON存储
            print(f"生成比赛 {match.match_id} 的分析数据")
        
        print("成功生成比赛分析数据")

    def generate_users(self, count: int = 10):
        """生成用户数据"""
        print(f"生成 {count} 个用户数据...")
        
        for i in range(count):
            user = User(
                username=f"user_{i + 1}",
                email=f"user{i + 1}@example.com",
                password_hash="pbkdf2:sha256:260000$random$salt",  # 模拟密码哈希
                steam_id=f"76561198{random.randint(10000000, 99999999)}",
                is_active=random.choice([True, False]),
                is_admin=random.choice([True, False]),
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 365))
            )
            self.session.add(user)
        
        self.session.commit()
        print(f"成功生成 {count} 个用户数据")

    def generate_audit_logs(self, count: int = 50):
        """生成审计日志"""
        print(f"生成 {count} 条审计日志...")
        
        actions = ['login', 'logout', 'create_match', 'update_match', 'delete_match', 'sync_data', 'export_data']
        
        for i in range(count):
            audit_log = AuditLog(
                user_id=random.randint(1, 10),
                action=random.choice(actions),
                resource_type=random.choice(['match', 'player', 'team', 'league']),
                resource_id=random.randint(1, 20),
                details={'ip': f"192.168.1.{random.randint(1, 255)}", 'user_agent': 'Mozilla/5.0'},
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30))
            )
            self.session.add(audit_log)
        
        self.session.commit()
        print(f"成功生成 {count} 条审计日志")

    def generate_learning_progress(self, count: int = 30):
        """生成学习进度数据"""
        print(f"生成 {count} 个学习进度...")
        
        for i in range(count):
            progress = LearningProgress(
                user_id=random.randint(1, 10),
                content_type=random.choice(['hero', 'item', 'strategy']),
                content_id=random.randint(1, 30),
                progress=random.uniform(0, 100),
                completed=random.choice([True, False]),
                score=random.randint(0, 100),
                time_spent=random.randint(300, 3600),
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
                updated_at=datetime.utcnow() - timedelta(days=random.randint(0, 7))
            )
            self.session.add(progress)
        
        self.session.commit()
        print(f"成功生成 {count} 个学习进度")

    def generate_notifications(self, count: int = 20):
        """生成通知数据"""
        print(f"生成 {count} 个通知...")
        
        notification_types = ['match_update', 'system', 'learning', 'social']
        
        for i in range(count):
            notification = Notification(
                user_id=random.randint(1, 10),
                type=random.choice(notification_types),
                title=f"通知标题 {i + 1}",
                message=f"这是通知消息内容 {i + 1}",
                is_read=random.choice([True, False]),
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30))
            )
            self.session.add(notification)
        
        self.session.commit()
        print(f"成功生成 {count} 个通知")

    def generate_all_test_data(self):
        """生成所有测试数据"""
        print("开始生成所有测试数据...")
        
        try:
            # 按依赖顺序生成数据
            self.generate_heroes()
            self.generate_items()
            self.generate_teams()
            self.generate_players()
            self.generate_leagues()
            self.generate_matches()
            self.generate_match_players()
            self.generate_match_drafts()
            self.generate_match_analyses()
            self.generate_users()
            self.generate_audit_logs()
            self.generate_learning_progress()
            self.generate_notifications()
            
            print("所有测试数据生成完成！")
            
        except Exception as e:
            print(f"生成测试数据时出错: {e}")
            self.session.rollback()
            raise


def init_test_database():
    """初始化测试数据库"""
    print("开始初始化测试数据库...")
    
    try:
        # 创建数据库引擎
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        
        # 创建会话
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # 检查数据库连接
        session.execute(text('SELECT 1'))
        print("数据库连接成功")
        
        # 创建所有表
        print("创建数据库表...")
        db.create_all()
        print("数据库表创建完成")
        
        # 生成测试数据
        generator = TestDataGenerator(session)
        generator.generate_all_test_data()
        
        # 验证数据
        print("\n验证生成的数据:")
        print(f"英雄数量: {session.query(Hero).count()}")
        print(f"物品数量: {session.query(Item).count()}")
        print(f"战队数量: {session.query(Team).count()}")
        print(f"选手数量: {session.query(Player).count()}")
        print(f"联赛数量: {session.query(League).count()}")
        print(f"比赛数量: {session.query(Match).count()}")
        print(f"用户数量: {session.query(User).count()}")
        
        session.close()
        print("\n测试数据库初始化完成！")
        
    except SQLAlchemyError as e:
        print(f"数据库错误: {e}")
        raise
    except Exception as e:
        print(f"初始化失败: {e}")
        raise


if __name__ == '__main__':
    init_test_database()