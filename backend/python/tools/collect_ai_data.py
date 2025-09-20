#!/usr/bin/env python3
"""
AI训练数据收集配置和使用示例
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.match_data_collector import MatchDataCollector


def collect_data_for_ai_training():
    """为AI训练收集数据的完整示例"""
    
    # API密钥
    api_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJTdWJqZWN0IjoiYzM1OGY4N2YtYjI3Ny00MTZiLTliOTQtNjQxNDUyZmVhZTdlIiwiU3RlYW1JZCI6IjE2NDgzNDU1NyIsIkFQSVVzZXIiOiJ0cnVlIiwibmJmIjoxNzU3OTk4MjE0LCJleHAiOjE3ODk1MzQyMTQsImlhdCI6MTc1Nzk5ODIxNCwiaXNzIjoiaHR0cHM6Ly9hcGkuc3RyYXR6LmNvbSJ9.r_3s8lSC3uXd7v0LhnP2cvYRByQf56EtUONikFS_x_4'
    
    # 创建收集器
    collector = MatchDataCollector(api_key)
    
    print("🤖 AI训练数据收集开始")
    print("=" * 60)
    
    # 场景1: 收集热门英雄的比赛数据
    print("\n🎯 场景1: 收集热门英雄数据")
    popular_heroes = ['Pudge', 'Invoker', 'Anti-Mage', 'Shadow Fiend', 'Phantom Assassin']
    
    for hero in popular_heroes:
        print(f"\n📊 收集 {hero} 的比赛数据...")
        result = collector.collect_training_data(
            hero=hero,
            start_date='2024-08-01',
            end_date='2024-09-16',
            limit=100  # 每个英雄100场比赛
        )
        
        if result['success']:
            print(f"✅ {hero} 数据收集完成")
            print(f"   📁 文件: {result['filepath']}")
            print(f"   📈 比赛数量: {result['stats']['total_matches']}")
        else:
            print(f"❌ {hero} 数据收集失败")
    
    # 场景2: 收集职业比赛数据
    print("\n🎯 场景2: 收集职业比赛数据")
    professional_leagues = ['The International', 'DPC', 'ESL', 'PGL', 'BetBoom']
    
    for league in professional_leagues:
        print(f"\n📊 收集 {league} 的比赛数据...")
        result = collector.collect_training_data(
            league=league,
            start_date='2024-01-01',
            end_date='2024-09-16',
            limit=200  # 每个联赛200场比赛
        )
        
        if result['success']:
            print(f"✅ {league} 数据收集完成")
            print(f"   📁 文件: {result['filepath']}")
            print(f"   📈 比赛数量: {result['stats']['total_matches']}")
    
    # 场景3: 收集特定游戏模式数据
    print("\n🎯 场景3: 收集特定游戏模式数据")
    game_modes = ['Ranked', 'Captains Mode', 'All Pick', 'Turbo']
    
    for mode in game_modes:
        print(f"\n📊 收集 {mode} 模式的比赛数据...")
        # 这里需要获取所有比赛然后按游戏模式过滤
        match_ids = collector.get_all_match_ids(
            start_date='2024-08-01',
            end_date='2024-09-16',
            max_matches=150
        )
        
        # 获取详细数据
        match_details = collector.get_match_details_batch(match_ids[:100])
        
        # 过滤指定游戏模式
        filtered_matches = [
            match for match in match_details 
            if mode.lower() in str(match.get('gameMode', '')).lower()
        ]
        
        # 保存过滤后的数据
        filepath = collector.save_match_data(
            filtered_matches,
            f"{mode.replace(' ', '_')}_matches"
        )
        
        print(f"✅ {mode} 模式数据收集完成")
        print(f"   📁 文件: {filepath}")
        print(f"   📈 比赛数量: {len(filtered_matches)}")
    
    # 场景4: 复合条件搜索
    print("\n🎯 场景4: 复合条件搜索示例")
    complex_conditions = [
        {
            'name': '高端局_Pudge',
            'conditions': {
                'hero': 'Pudge',
                'start_date': '2024-08-01',
                'end_date': '2024-09-16',
                'limit': 50
            }
        },
        {
            'name': '职业比赛_Invoker',
            'conditions': {
                'hero': 'Invoker',
                'league': 'DPC',
                'start_date': '2024-06-01',
                'end_date': '2024-09-16',
                'limit': 30
            }
        }
    ]
    
    for search_config in complex_conditions:
        print(f"\n📊 执行复合搜索: {search_config['name']}")
        result = collector.collect_training_data(**search_config['conditions'])
        
        if result['success']:
            print(f"✅ {search_config['name']} 数据收集完成")
            print(f"   📁 文件: {result['filepath']}")
            print(f"   📈 比赛数量: {result['stats']['total_matches']}")
    
    print("\n🎉 AI训练数据收集全部完成！")
    print("📋 数据文件已保存到 backend/python/data/match_data/ 目录")
    print("🚀 现在可以使用这些数据进行AI模型训练了")


def quick_data_collection():
    """快速数据收集 - 用于测试或小规模数据需求"""
    
    api_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJTdWJqZWN0IjoiYzM1OGY4N2YtYjI3Ny00MTZiLTliOTQtNjQxNDUyZmVhZTdlIiwiU3RlYW1JZCI6IjE2NDgzNDU1NyIsIkFQSVVzZXIiOiJ0cnVlIiwibmJmIjoxNzU3OTk4MjE0LCJleHAiOjE3ODk1MzQyMTQsImlhdCI6MTc1Nzk5ODIxNCwiaXNzIjoiaHR0cHM6Ly9hcGkuc3RyYXR6LmNvbSJ9.r_3s8lSC3uXd7v0LhnP2cvYRByQf56EtUONikFS_x_4'
    collector = MatchDataCollector(api_key)
    
    print("⚡ 快速数据收集模式")
    print("=" * 40)
    
    # 快速收集最近的比赛
    print("\n📊 收集最近的比赛数据...")
    result = collector.collect_training_data(
        start_date='2024-09-10',
        end_date='2024-09-16',
        limit=20
    )
    
    if result['success']:
        print(f"✅ 快速数据收集完成")
        print(f"📁 文件: {result['filepath']}")
        print(f"📈 比赛数量: {result['stats']['total_matches']}")
        print(f"⏱️  用时: {result['stats']['collection_time']}秒")


if __name__ == '__main__':
    # 选择收集模式
    print("请选择数据收集模式:")
    print("1. 完整AI训练数据收集")
    print("2. 快速数据收集")
    
    choice = input("\n请输入选择 (1或2): ").strip()
    
    if choice == '1':
        collect_data_for_ai_training()
    elif choice == '2':
        quick_data_collection()
    else:
        print("❌ 无效选择，默认使用快速模式")
        quick_data_collection()