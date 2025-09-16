#!/usr/bin/env python3
"""
简化版比赛数据收集工具 - 无代理版本
专门用于获取所有比赛ID和多条件搜索比赛
"""

import sys
import json
import time
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class SimpleMatchCollector:
    """简化版比赛数据收集器"""
    
    def __init__(self, api_key: str):
        """初始化收集器"""
        self.api_key = api_key
        self.base_url = 'https://api.stratz.com/graphql'
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'STRATZ-Python-Client'
        }
        self.collected_match_ids: Set[int] = set()
        self.batch_size = 50  # 减小批量大小
        self.max_workers = 3  # 减少并发数
        
    def _make_request(self, query: str) -> Optional[Dict]:
        """发送GraphQL请求"""
        try:
            response = requests.post(
                self.base_url,
                json={'query': query},
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ 请求失败: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            return None
    
    def get_recent_match_ids(self, days_back: int = 7, max_matches: int = 100) -> List[int]:
        """
        获取最近的比赛ID（简化版）
        
        Args:
            days_back: 回溯天数
            max_matches: 最大比赛数量
            
        Returns:
            比赛ID列表
        """
        print(f"🎯 获取最近 {days_back} 天的比赛ID...")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        match_ids = []
        offset = 0
        
        while len(match_ids) < max_matches:
            print(f"📊 正在获取第 {offset//self.batch_size + 1} 批比赛...")
            
            # 简化查询，只获取基本信息
            query = f"""
            {{
                matches(
                    request: {{
                        take: {self.batch_size}
                        skip: {offset}
                        orderBy: {{field: START_DATE_TIME, direction: DESC}}
                    }}
                ) {{
                    id
                    startDateTime
                }}
            }}
            """
            
            result = self._make_request(query)
            if not result or 'data' not in result:
                print("❌ 查询失败，跳过...")
                break
                
            matches = result['data']['matches']
            if not matches:
                print("✅ 所有比赛已获取完成")
                break
                
            batch_ids = [match['id'] for match in matches]
            match_ids.extend(batch_ids)
            
            print(f"   本批获取: {len(batch_ids)} 场比赛")
            print(f"   总计: {len(match_ids)} 场比赛")
            
            offset += self.batch_size
            
            # 更长的延迟避免限流
            time.sleep(2)
            
            # 检查是否达到限制
            if len(match_ids) >= max_matches:
                match_ids = match_ids[:max_matches]
                break
        
        print(f"🎉 比赛ID收集完成！总计: {len(match_ids)} 场比赛")
        return match_ids
    
    def search_by_hero_simple(self, hero_name: str, limit: int = 20) -> List[Dict]:
        """
        简化版英雄搜索
        
        Args:
            hero_name: 英雄名称
            limit: 返回结果数量
            
        Returns:
            比赛信息列表
        """
        print(f"🔍 搜索英雄: {hero_name}")
        
        # 先获取英雄列表
        heroes_query = """
        {
            heroes {
                id
                displayName
            }
        }
        """
        
        heroes_result = self._make_request(heroes_query)
        if not heroes_result or 'data' not in heroes_result:
            return []
        
        # 查找英雄ID
        hero_id = None
        for hero in heroes_result['data']['heroes']:
            if hero_name.lower() in hero['displayName'].lower():
                hero_id = hero['id']
                print(f"✅ 找到英雄: {hero['displayName']} (ID: {hero_id})")
                break
        
        if not hero_id:
            print(f"❌ 未找到英雄: {hero_name}")
            return []
        
        # 搜索包含该英雄的比赛
        query = f"""
        {{
            matches(
                request: {{
                    take: {limit}
                    heroes: [{hero_id}]
                }}
            ) {{
                id
                startDateTime
                duration
                gameMode
                players {{
                    heroId
                    isVictory
                    kills
                    deaths
                    assists
                }}
            }}
        }}
        """
        
        result = self._make_request(query)
        if not result or 'data' not in result:
            return []
            
        matches = result['data']['matches']
        print(f"✅ 找到 {len(matches)} 场英雄比赛")
        return matches
    
    def get_match_details_simple(self, match_ids: List[int]) -> List[Dict]:
        """
        简化版比赛详情获取
        
        Args:
            match_ids: 比赛ID列表
            
        Returns:
            比赛详情列表
        """
        print(f"📋 获取 {len(match_ids)} 场比赛详情...")
        
        all_details = []
        
        for i, match_id in enumerate(match_ids):
            print(f"   处理比赛 {i+1}/{len(match_ids)}: {match_id}")
            
            query = f"""
            {{
                match(id: {match_id}) {{
                    id
                    startDateTime
                    duration
                    gameMode
                    lobbyType
                    league {{
                        id
                        name
                        displayName
                    }}
                    players {{
                        heroId
                        steamAccountId
                        isVictory
                        kills
                        deaths
                        assists
                        goldPerMinute
                        experiencePerMinute
                        heroDamage
                        towerDamage
                        healing
                    }}
                }}
            }}
            """
            
            result = self._make_request(query)
            if result and 'data' in result and result['data']['match']:
                all_details.append(result['data']['match'])
            
            # 较长的延迟避免限流
            time.sleep(3)
        
        print(f"✅ 成功获取 {len(all_details)} 场比赛详情")
        return all_details
    
    def save_data(self, data: List[Dict], filename: str) -> str:
        """保存数据到文件"""
        # 创建数据目录
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'match_data')
        os.makedirs(data_dir, exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{filename}_{timestamp}.json"
        filepath = os.path.join(data_dir, filename)
        
        # 保存数据
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 数据已保存到: {filepath}")
        return filepath
    
    def collect_sample_data(self, hero_name: str = 'Pudge', limit: int = 10) -> Dict:
        """
        收集示例数据 - 专为AI训练优化
        
        Args:
            hero_name: 英雄名称
            limit: 比赛数量限制
            
        Returns:
            包含数据和统计信息的字典
        """
        print(f"🚀 开始收集 {hero_name} 的AI训练数据...")
        start_time = time.time()
        
        # 1. 搜索英雄相关比赛
        matches = self.search_by_hero_simple(hero_name, limit)
        
        if not matches:
            return {'success': False, 'message': '未找到相关比赛'}
        
        # 2. 获取比赛详情
        match_ids = [match['id'] for match in matches]
        match_details = self.get_match_details_simple(match_ids[:5])  # 限制数量避免超时
        
        if not match_details:
            return {'success': False, 'message': '未能获取比赛详情'}
        
        # 3. 保存数据
        filepath = self.save_data(match_details, f"ai_training_{hero_name.lower()}")
        
        # 4. 生成统计信息
        end_time = time.time()
        stats = {
            'total_matches': len(match_details),
            'collection_time': round(end_time - start_time, 2),
            'average_duration': sum(m.get('duration', 0) for m in match_details) / len(match_details) if match_details else 0,
            'game_modes': {}
        }
        
        # 统计游戏模式
        for match in match_details:
            game_mode = match.get('gameMode', 'Unknown')
            stats['game_modes'][game_mode] = stats['game_modes'].get(game_mode, 0) + 1
        
        result = {
            'success': True,
            'filepath': filepath,
            'stats': stats,
            'hero': hero_name
        }
        
        print("🎉 AI训练数据收集完成！")
        print(f"📁 数据文件: {filepath}")
        print(f"📊 统计信息: {stats}")
        
        return result


def main():
    """主函数 - 示例使用"""
    
    # API密钥
    api_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJTdWJqZWN0IjoiYzM1OGY4N2YtYjI3Ny00MTZiLTliOTQtNjQxNDUyZmVhZTdlIiwiU3RlYW1JZCI6IjE2NDgzNDU1NyIsIkFQSVVzZXIiOiJ0cnVlIiwibmJmIjoxNzU3OTk4MjE0LCJleHAiOjE3ODk1MzQyMTQsImlhdCI6MTc1Nzk5ODIxNCwiaXNzIjoiaHR0cHM6Ly9hcGkuc3RyYXR6LmNvbSJ9.r_3s8lSC3uXd7v0LhnP2cvYRByQf56EtUONikFS_x_4'
    
    # 创建简化版收集器
    collector = SimpleMatchCollector(api_key)
    
    print("🎯 简化版比赛数据收集工具")
    print("=" * 50)
    
    # 示例1: 获取最近的比赛ID
    print("\n1️⃣ 获取最近的比赛ID:")
    match_ids = collector.get_recent_match_ids(days_back=3, max_matches=10)
    print(f"✅ 获取到 {len(match_ids)} 个比赛ID")
    
    # 示例2: 搜索特定英雄的比赛
    print("\n2️⃣ 搜索特定英雄的比赛:")
    hero_matches = collector.search_by_hero_simple('Pudge', limit=5)
    print(f"✅ 找到 {len(hero_matches)} 场Pudge比赛")
    
    # 示例3: 收集AI训练数据
    print("\n3️⃣ 收集AI训练数据:")
    training_data = collector.collect_sample_data('Invoker', limit=5)
    
    if training_data['success']:
        print(f"✅ AI训练数据收集完成")
        print(f"📁 文件: {training_data['filepath']}")
        print(f"📈 比赛数量: {training_data['stats']['total_matches']}")
        print(f"⏱️  用时: {training_data['stats']['collection_time']}秒")
    else:
        print(f"❌ 数据收集失败: {training_data['message']}")
    
    print("\n🎉 所有测试完成！")
    print("💡 你可以使用这个工具来收集AI训练数据")
    print("📋 支持的英雄搜索、比赛详情获取等功能")


if __name__ == '__main__':
    main()