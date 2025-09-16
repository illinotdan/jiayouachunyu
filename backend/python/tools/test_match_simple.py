#!/usr/bin/env python3
"""
简化版比赛测试 - 使用基本HTTP请求
测试比赛ID: 8461476910
"""

import requests
import json
import os
from datetime import datetime

def test_match_with_simple_request():
    """使用简单HTTP请求测试比赛数据"""
    print("🎯 测试比赛ID: 8461476910")
    print("=" * 50)
    
    # 尝试不同的端点
    endpoints = [
        # 基本比赛信息
        f"https://api.stratz.com/api/v1/match/{8461476910}",
        # OpenDota API 作为备选
        f"https://api.opendota.com/api/matches/{8461476910}",
        # STRATZ GraphQL 端点（无认证）
        "https://api.stratz.com/graphql"
    ]
    
    # 测试1: 直接API请求
    print("\n1️⃣ 直接API请求测试...")
    for i, endpoint in enumerate(endpoints[:-1]):  # 排除GraphQL端点
        try:
            print(f"尝试端点 {i+1}: {endpoint}")
            response = requests.get(endpoint, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 成功获取数据!")
                print(f"📊 数据键: {list(data.keys())[:10]}...")  # 显示前10个键
                
                # 保存数据
                filename = f"match_8461476910_api{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                filepath = os.path.join("test_data", filename)
                os.makedirs("test_data", exist_ok=True)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                print(f"💾 数据已保存到: {filepath}")
                break
            else:
                print(f"❌ 状态码: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 请求失败: {e}")
    
    # 测试2: GraphQL无认证请求
    print("\n2️⃣ GraphQL无认证请求...")
    try:
        # 简单的GraphQL查询
        query = """
        {
            match(id: 8461476910) {
                id
                startDateTime
                durationSeconds
                gameMode
                didRadiantWin
            }
        }
        """
        
        response = requests.post(
            endpoints[2],
            json={'query': query},
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data'] and data['data']['match']:
                match_data = data['data']['match']
                print(f"✅ GraphQL查询成功!")
                print(f"📊 比赛ID: {match_data.get('id')}")
                print(f"⏰ 开始时间: {match_data.get('startDateTime')}")
                print(f"🕐 持续时间: {match_data.get('durationSeconds')}秒")
                print(f"🎮 游戏模式: {match_data.get('gameMode')}")
                print(f"👑 天辉获胜: {match_data.get('didRadiantWin')}")
                
                # 保存数据
                filename = f"match_8461476910_graphql_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                filepath = os.path.join("test_data", filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                print(f"💾 GraphQL数据已保存到: {filepath}")
            else:
                print(f"❌ GraphQL返回空数据: {data}")
        else:
            print(f"❌ GraphQL状态码: {response.status_code}")
            if response.status_code == 403:
                print("💡 提示: 需要API密钥或权限")
            
    except Exception as e:
        print(f"❌ GraphQL请求失败: {e}")
    
    # 测试3: 尝试获取一些基本信息
    print("\n3️⃣ 获取公开数据...")
    try:
        # 尝试获取英雄列表（通常是公开的）
        heroes_query = """
        {
            constants {
                heroes {
                    id
                    displayName
                }
            }
        }
        """
        
        response = requests.post(
            endpoints[2],
            json={'query': heroes_query},
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']:
                heroes = data['data']['constants']['heroes']
                print(f"✅ 成功获取英雄数据!")
                print(f"👥 英雄数量: {len(heroes)}")
                print(f"🦸 前5个英雄: {[h['displayName'] for h in heroes[:5]]}")
            else:
                print(f"❌ 英雄数据为空: {data}")
        else:
            print(f"❌ 英雄数据状态码: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 英雄数据请求失败: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 测试完成!")
    print("💡 建议:")
    print("   - 如果需要详细比赛数据，可能需要API密钥")
    print("   - 可以尝试使用OpenDota API作为免费备选")
    print("   - 某些基础数据（如英雄列表）可能无需认证")

if __name__ == "__main__":
    test_match_with_simple_request()