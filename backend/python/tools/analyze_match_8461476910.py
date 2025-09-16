#!/usr/bin/env python3
"""
分析比赛ID 8461476910 的数据
从OpenDota API获取的详细数据
"""

import json
import os
from datetime import datetime

def analyze_match_data():
    """分析比赛数据"""
    print("🎯 分析比赛ID: 8461476910")
    print("=" * 60)
    
    # 读取数据文件
    data_file = "test_data/match_8461476910_api2_20250916_141456.json"
    
    if not os.path.exists(data_file):
        print(f"❌ 数据文件不存在: {data_file}")
        return
    
    with open(data_file, 'r', encoding='utf-8') as f:
        match_data = json.load(f)
    
    print(f"✅ 成功加载数据文件")
    print(f"📊 数据大小: {len(str(match_data))} 字符")
    print(f"🔑 主要数据键: {list(match_data.keys())}")
    
    # 基础比赛信息
    print("\n📋 基础比赛信息:")
    print(f"  🆔 比赛ID: {match_data.get('match_id', 'N/A')}")
    print(f"  📊 数据版本: {match_data.get('version', 'N/A')}")
    
    # 解析时间戳
    if 'start_time' in match_data:
        start_time = datetime.fromtimestamp(match_data['start_time'])
        print(f"  ⏰ 开始时间: {start_time}")
    
    # 队伍信息
    if 'radiant_team' in match_data:
        radiant = match_data['radiant_team']
        print(f"  🟢 天辉队伍: {radiant.get('name', 'N/A')}")
    
    if 'dire_team' in match_data:
        dire = match_data['dire_team']
        print(f"  🔴 夜魇队伍: {dire.get('name', 'N/A')}")
    
    # 比赛结果
    if 'radiant_win' in match_data:
        winner = "天辉" if match_data['radiant_win'] else "夜魇"
        print(f"  🏆 获胜方: {winner}")
    
    # 玩家信息
    if 'players' in match_data:
        players = match_data['players']
        print(f"\n👥 玩家信息 (共{len(players)}人):")
        
        # 按队伍分组
        radiant_players = [p for p in players if p.get('player_slot', 0) < 128]
        dire_players = [p for p in players if p.get('player_slot', 0) >= 128]
        
        print(f"  🟢 天辉队伍 ({len(radiant_players)}人):")
        for i, player in enumerate(radiant_players[:5]):
            hero_id = player.get('hero_id', 'N/A')
            kills = player.get('kills', 0)
            deaths = player.get('deaths', 0)
            assists = player.get('assists', 0)
            print(f"    {i+1}. 英雄ID: {hero_id}, KDA: {kills}/{deaths}/{assists}")
        
        print(f"  🔴 夜魇队伍 ({len(dire_players)}人):")
        for i, player in enumerate(dire_players[:5]):
            hero_id = player.get('hero_id', 'N/A')
            kills = player.get('kills', 0)
            deaths = player.get('deaths', 0)
            assists = player.get('assists', 0)
            print(f"    {i+1}. 英雄ID: {hero_id}, KDA: {kills}/{deaths}/{assists}")
    
    # 禁用/挑选阶段
    if 'picks_bans' in match_data:
        picks_bans = match_data['picks_bans']
        print(f"\n🎯 禁用/挑选阶段 (共{len(picks_bans)}个动作):")
        
        picks = [pb for pb in picks_bans if pb.get('is_pick', False)]
        bans = [pb for pb in picks_bans if not pb.get('is_pick', False)]
        
        print(f"  🚫 总禁用: {len(bans)}个")
        print(f"  ✅ 总挑选: {len(picks)}个")
        
        # 显示前几个动作
        print("  📋 前10个动作:")
        for i, action in enumerate(picks_bans[:10]):
            action_type = "挑选" if action.get('is_pick') else "禁用"
            team = "天辉" if action.get('team', 0) == 0 else "夜魇"
            hero_id = action.get('hero_id', 'N/A')
            print(f"    {i+1}. {team} {action_type} 英雄ID: {hero_id}")
    
    # 游戏目标
    if 'objectives' in match_data:
        objectives = match_data['objectives']
        print(f"\n🎯 游戏目标 (共{len(objectives)}个):")
        
        # 按类型分组
        tower_kills = [obj for obj in objectives if obj.get('type') == 'CHAT_MESSAGE_TOWER_KILL']
        barracks_kills = [obj for obj in objectives if obj.get('type') == 'CHAT_MESSAGE_BARRACKS_KILL']
        roshan_kills = [obj for obj in objectives if obj.get('type') == 'CHAT_MESSAGE_ROSHAN_KILL']
        
        print(f"  🏰 防御塔摧毁: {len(tower_kills)}次")
        print(f"  🏛️ 兵营摧毁: {len(barracks_kills)}次")
        print(f"  🐉 Roshan击杀: {len(roshan_kills)}次")
        
        # 显示前5个目标
        if objectives:
            print("  📋 前5个目标:")
            for i, obj in enumerate(objectives[:5]):
                obj_type = obj.get('type', 'N/A')
                team = obj.get('team', 'N/A')
                time = obj.get('time', 'N/A')
                print(f"    {i+1}. 类型: {obj_type}, 队伍: {team}, 时间: {time}")
    
    # 团战数据
    if 'teamfights' in match_data:
        teamfights = match_data['teamfights']
        print(f"\n⚔️ 团战数据 (共{len(teamfights)}次团战):")
        
        if teamfights:
            # 计算平均团战时间
            avg_start = sum(tf.get('start', 0) for tf in teamfights) / len(teamfights)
            avg_end = sum(tf.get('end', 0) for tf in teamfights) / len(teamfights)
            avg_duration = avg_end - avg_start
            
            print(f"  📊 平均开始时间: {avg_start/60:.1f}分钟")
            print(f"  ⏱️ 平均持续时间: {avg_duration:.1f}秒")
            
            # 显示最激烈的团战（死亡人数最多）
            deaths_counts = []
            for fight in teamfights:
                deaths = fight.get('deaths', [])
                if isinstance(deaths, list):
                    deaths_counts.append(len(deaths))
                else:
                    deaths_counts.append(0)
            
            if deaths_counts:
                max_idx = deaths_counts.index(max(deaths_counts))
                max_deaths_fight = teamfights[max_idx]
                max_deaths = deaths_counts[max_idx]
                max_deaths_time = max_deaths_fight.get('start', 0) / 60
            
                print(f"  💀 最激烈团战: {max_deaths_time:.1f}分钟，{max_deaths}人死亡")
            else:
                print("  💀 无法统计团战数据")
    
    # 聊天信息
    if 'chat' in match_data:
        chat = match_data['chat']
        print(f"\n💬 聊天信息 (共{len(chat)}条):")
        
        if chat:
            # 显示前5条聊天
            print("  💭 前5条聊天:")
            for i, msg in enumerate(chat[:5]):
                msg_type = msg.get('type', 'N/A')
                time = msg.get('time', 'N/A')
                unit = msg.get('unit', 'N/A')
                key = msg.get('key', 'N/A')
                print(f"    {i+1}. [{time}] {unit}: {key} ({msg_type})")
    
    print("\n" + "=" * 60)
    print("📊 数据质量评估:")
    print(f"  ✅ 基础数据完整性: {'完整' if match_data.get('match_id') else '不完整'}")
    print(f"  ✅ 玩家数据: {'可用' if 'players' in match_data else '不可用'}")
    print(f"  ✅ 禁用/挑选数据: {'可用' if 'picks_bans' in match_data else '不可用'}")
    print(f"  ✅ 目标数据: {'可用' if 'objectives' in match_data else '不可用'}")
    print(f"  ✅ 团战数据: {'可用' if 'teamfights' in match_data else '不可用'}")
    
    print("\n💡 这份数据可以用于:")
    print("  🎯 AI模型训练: 预测比赛结果、英雄选择策略")
    print("  📈 数据分析: 玩家行为、游戏节奏分析")
    print("  🎮 游戏策略: 团战时机、目标优先级")
    print("  📊 可视化: 比赛时间线、经济经验变化")

def extract_training_data():
    """提取AI训练数据"""
    print("\n🤖 提取AI训练数据...")
    
    data_file = "test_data/match_8461476910_api2_20250916_141456.json"
    
    if not os.path.exists(data_file):
        print(f"❌ 数据文件不存在: {data_file}")
        return
    
    with open(data_file, 'r', encoding='utf-8') as f:
        match_data = json.load(f)
    
    # 构建训练数据
    training_data = {
        'match_id': match_data.get('match_id'),
        'radiant_win': match_data.get('radiant_win'),
        'duration': match_data.get('duration'),
        'start_time': match_data.get('start_time'),
        'game_mode': match_data.get('game_mode'),
        'lobby_type': match_data.get('lobby_type'),
        'human_players': match_data.get('human_players'),
        'leagueid': match_data.get('leagueid'),
        'cluster': match_data.get('cluster'),
        'radiant_score': match_data.get('radiant_score'),
        'dire_score': match_data.get('dire_score'),
        'players': [],
        'picks_bans': match_data.get('picks_bans', []),
        'objectives': match_data.get('objectives', []),
        'teamfights': []
    }
    
    # 处理玩家数据
    if 'players' in match_data:
        for player in match_data['players']:
            player_data = {
                'player_slot': player.get('player_slot'),
                'hero_id': player.get('hero_id'),
                'kills': player.get('kills'),
                'deaths': player.get('deaths'),
                'assists': player.get('assists'),
                'last_hits': player.get('last_hits'),
                'denies': player.get('denies'),
                'gold_per_min': player.get('gold_per_min'),
                'xp_per_min': player.get('xp_per_min'),
                'level': player.get('level'),
                'hero_damage': player.get('hero_damage'),
                'tower_damage': player.get('tower_damage'),
                'hero_healing': player.get('hero_healing'),
                'gold': player.get('gold'),
                'gold_spent': player.get('gold_spent'),
                'scaled_hero_damage': player.get('scaled_hero_damage'),
                'scaled_tower_damage': player.get('scaled_tower_damage'),
                'scaled_hero_healing': player.get('scaled_hero_healing'),
            }
            training_data['players'].append(player_data)
    
    # 处理团战数据（简化版）
    if 'teamfights' in match_data:
        for fight in match_data['teamfights']:
            deaths = fight.get('deaths', [])
            if isinstance(deaths, list):
                deaths_count = len(deaths)
            else:
                deaths_count = 0
            
            players = fight.get('players', [])
            if isinstance(players, list):
                players_count = len(players)
            else:
                players_count = 0
            
            fight_data = {
                'start': fight.get('start'),
                'end': fight.get('end'),
                'last_death': fight.get('last_death'),
                'deaths': deaths_count,
                'players': players_count
            }
            training_data['teamfights'].append(fight_data)
    
    # 保存训练数据
    training_file = "test_data/training_data_8461476910.json"
    with open(training_file, 'w', encoding='utf-8') as f:
        json.dump(training_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 训练数据提取完成!")
    print(f"📊 玩家数据: {len(training_data['players'])}条")
    print(f"📊 禁用/挑选: {len(training_data['picks_bans'])}条")
    print(f"📊 目标数据: {len(training_data['objectives'])}条")
    print(f"📊 团战数据: {len(training_data['teamfights'])}条")
    print(f"💾 训练数据已保存到: {training_file}")

if __name__ == "__main__":
    analyze_match_data()
    extract_training_data()