#!/usr/bin/env python3
"""
测试特定比赛ID的数据收集
使用用户提供的比赛ID: 8461476910
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.stratz_service import StratzService
from tools.simple_match_collector import SimpleMatchCollector

def test_specific_match():
    """测试特定比赛ID"""
    print("🎯 测试特定比赛ID: 8461476910")
    print("=" * 50)
    
    # 初始化服务
    service = StratzService()  # 不需要API密钥
    collector = None  # 不使用简化收集器
    
    # 测试1: 获取比赛详情
    print("\n1️⃣ 获取比赛详情...")
    try:
        match_details = service.get_match(8461476910)
        if match_details:
            print(f"✅ 比赛详情获取成功!")
            print(f"📊 比赛ID: {match_details.get('id', 'N/A')}")
            print(f"🏆 游戏模式: {match_details.get('gameMode', 'N/A')}")
            print(f"⏰ 开始时间: {match_details.get('startDateTime', 'N/A')}")
            print(f"👥 玩家人数: {len(match_details.get('players', []))}")
            
            # 显示一些玩家信息
            players = match_details.get('players', [])
            if players:
                print(f"\n👤 玩家信息示例:")
                for i, player in enumerate(players[:3]):  # 显示前3个玩家
                    hero = player.get('hero', {})
                    print(f"  玩家{i+1}: 英雄={hero.get('displayName', 'N/A')}, "
                          f"击杀={player.get('kills', 'N/A')}, "
                          f"死亡={player.get('deaths', 'N/A')}, "
                          f"助攻={player.get('assists', 'N/A')}")
        else:
            print("❌ 比赛详情为空")
    except Exception as e:
        print(f"❌ 获取比赛详情失败: {e}")
    
    # 测试2: 获取详细比赛数据
    print("\n2️⃣ 获取详细比赛数据...")
    try:
        detailed_match = service.get_match_detailed(8461476910)
        if detailed_match:
            print(f"✅ 详细比赛数据获取成功!")
            print(f"📋 数据键: {list(detailed_match.keys())}")
            
            # 显示更多详细信息
            if 'match' in detailed_match:
                match_data = detailed_match['match']
                print(f"\n📊 比赛统计:")
                print(f"  持续时间: {match_data.get('duration', 'N/A')}")
                print(f"  服务器区域: {match_data.get('region', 'N/A')}")
                print(f"  联赛ID: {match_data.get('leagueId', 'N/A')}")
        else:
            print("❌ 详细比赛数据为空")
    except Exception as e:
        print(f"❌ 获取详细比赛数据失败: {e}")
    
    # 测试3: 保存获取的数据
    print("\n3️⃣ 保存比赛数据...")
    try:
        # 获取基本比赛数据
        match_data = service.get_match(8461476910, fields='detailed')
        if match_data:
            print(f"✅ 比赛数据获取成功!")
            print(f"💾 数据大小: {len(str(match_data))} 字符")
            
            # 保存数据到文件
            import json
            from datetime import datetime
            
            filename = f"match_8461476910_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join("test_data", filename)
            
            # 确保目录存在
            os.makedirs("test_data", exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(match_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 数据已保存到: {filepath}")
        else:
            print("❌ 比赛数据为空")
    except Exception as e:
        print(f"❌ 保存数据失败: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 测试完成!")

if __name__ == "__main__":
    test_specific_match()