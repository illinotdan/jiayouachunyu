#!/usr/bin/env python3
"""
比赛数据收集工具 - 用于AI训练数据准备
专门用于获取所有比赛ID和多条件搜索比赛
"""

import sys
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.append('..')
from ..services.stratz_service import StratzService


class MatchDataCollector:
    """比赛数据收集器 - 专门用于AI训练数据准备"""
    
    def __init__(self, api_key: str):
        """初始化收集器"""
        self.service = StratzService(api_key=api_key)
        self.collected_match_ids: Set[int] = set()
        self.batch_size = 100
        self.max_workers = 5
        
    def get_all_match_ids(self, start_date: str = None, end_date: str = None, 
                         max_matches: int = 10000) -> List[int]:
        """
        获取指定时间范围内的所有比赛ID
        
        Args:
            start_date: 开始日期 (YYYY-MM-DD格式)
            end_date: 结束日期 (YYYY-MM-DD格式)
            max_matches: 最大比赛数量限制
            
        Returns:
            比赛ID列表
        """
        print(f"🎯 开始收集比赛ID...")
        print(f"时间范围: {start_date} 到 {end_date}")
        print(f"最大数量限制: {max_matches}")
        
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        match_ids = []
        offset = 0
        
        while len(match_ids) < max_matches:
            print(f"📊 正在获取第 {offset//self.batch_size + 1} 批比赛...")
            
            # 使用GraphQL查询获取比赛ID
            query = f"""
            {{
                matches(
                    request: {{
                        startDateTime: "{start_date}T00:00:00Z"
                        endDateTime: "{end_date}T23:59:59Z"
                        take: {self.batch_size}
                        skip: {offset}
                        orderBy: {{field: START_DATE_TIME, direction: DESC}}
                    }}
                ) {{
                    id
                    startDateTime
                    duration
                    gameMode
                    lobbyType
                }}
            }}
            """
            
            result = self.service.raw_query(query)
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
            
            # 避免API限流
            time.sleep(0.5)
            
            # 检查是否达到限制
            if len(match_ids) >= max_matches:
                match_ids = match_ids[:max_matches]
                break
        
        print(f"🎉 比赛ID收集完成！总计: {len(match_ids)} 场比赛")
        return match_ids
    
    def search_matches_by_team(self, team_name: str, limit: int = 100) -> List[Dict]:
        """
        搜索指定战队的比赛
        
        Args:
            team_name: 战队名称
            limit: 返回结果数量限制
            
        Returns:
            比赛信息列表
        """
        print(f"🔍 搜索战队: {team_name}")
        
        query = f"""
        {{
            teams(request: {{search: "{team_name}", take: 50}}) {{
                id
                name
                matches(take: {limit}) {{
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
                }}
            }}
        }}
        """
        
        result = self.service.raw_query(query)
        if not result or 'data' not in result:
            return []
            
        matches = []
        for team in result['data']['teams']:
            team_matches = team.get('matches', [])
            for match in team_matches:
                match['team_name'] = team['name']
                match['team_id'] = team['id']
                matches.append(match)
        
        print(f"✅ 找到 {len(matches)} 场战队比赛")
        return matches
    
    def search_matches_by_player(self, player_name: str, limit: int = 100) -> List[Dict]:
        """
        搜索指定选手的比赛
        
        Args:
            player_name: 选手名称或Steam ID
            limit: 返回结果数量限制
            
        Returns:
            比赛信息列表
        """
        print(f"🔍 搜索选手: {player_name}")
        
        # 如果是数字，可能是Steam ID
        if player_name.isdigit():
            steam_id = int(player_name)
            return self._get_player_matches_by_id(steam_id, limit)
        else:
            return self._search_player_by_name(player_name, limit)
    
    def _search_player_by_name(self, player_name: str, limit: int) -> List[Dict]:
        """通过选手名称搜索"""
        query = f"""
        {{
            players(request: {{search: "{player_name}", take: 10}}) {{
                steamAccountId
                proName
                name
                matches(take: {limit}) {{
                    id
                    startDateTime
                    duration
                    gameMode
                    lobbyType
                    players {{
                        heroId
                        isVictory
                        kills
                        deaths
                        assists
                    }}
                }}
            }}
        }}
        """
        
        result = self.service.raw_query(query)
        if not result or 'data' not in result:
            return []
            
        matches = []
        for player in result['data']['players']:
            player_matches = player.get('matches', [])
            for match in player_matches:
                match['player_name'] = player.get('proName') or player.get('name')
                match['player_id'] = player['steamAccountId']
                matches.append(match)
        
        print(f"✅ 找到 {len(matches)} 场选手比赛")
        return matches
    
    def _get_player_matches_by_id(self, steam_id: int, limit: int) -> List[Dict]:
        """通过Steam ID获取选手比赛"""
        return self.service.get_player_matches(steam_id, limit=limit)
    
    def search_matches_by_hero(self, hero_name: str, limit: int = 100) -> List[Dict]:
        """
        搜索指定英雄的比赛
        
        Args:
            hero_name: 英雄名称
            limit: 返回结果数量限制
            
        Returns:
            比赛信息列表
        """
        print(f"🔍 搜索英雄: {hero_name}")
        
        # 先获取英雄ID
        heroes = self.service.get_heroes(['id', 'displayName'])
        hero_id = None
        
        for hero in heroes:
            if hero_name.lower() in hero['displayName'].lower():
                hero_id = hero['id']
                break
        
        if not hero_id:
            print(f"❌ 未找到英雄: {hero_name}")
            return []
        
        print(f"✅ 找到英雄ID: {hero_id}")
        
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
                lobbyType
                players {{
                    heroId
                    steamAccountId
                    isVictory
                    kills
                    deaths
                    assists
                }}
            }}
        }}
        """
        
        result = self.service.raw_query(query)
        if not result or 'data' not in result:
            return []
            
        matches = result['data']['matches']
        for match in matches:
            match['hero_id'] = hero_id
            match['hero_name'] = hero_name
        
        print(f"✅ 找到 {len(matches)} 场英雄比赛")
        return matches
    
    def search_matches_by_league(self, league_name: str, limit: int = 100) -> List[Dict]:
        """
        搜索指定联赛的比赛
        
        Args:
            league_name: 联赛名称
            limit: 返回结果数量限制
            
        Returns:
            比赛信息列表
        """
        print(f"🔍 搜索联赛: {league_name}")
        
        query = f"""
        {{
            leagues(request: {{search: "{league_name}", take: 20}}) {{
                id
                name
                displayName
                matches(take: {limit}) {{
                    id
                    startDateTime
                    duration
                    gameMode
                    lobbyType
                    league {{
                        id
                        name
                        displayName
                        prizePool
                    }}
                }}
            }}
        }}
        """
        
        result = self.service.raw_query(query)
        if not result or 'data' not in result:
            return []
            
        matches = []
        for league in result['data']['leagues']:
            league_matches = league.get('matches', [])
            for match in league_matches:
                match['league_name'] = league['name']
                match['league_id'] = league['id']
                matches.append(match)
        
        print(f"✅ 找到 {len(matches)} 场联赛比赛")
        return matches
    
    def complex_search(self, **conditions) -> List[Dict]:
        """
        多条件复合搜索
        
        Args:
            team: 战队名称
            player: 选手名称/Steam ID
            hero: 英雄名称
            league: 联赛名称
            start_date: 开始日期
            end_date: 结束日期
            game_mode: 游戏模式
            min_duration: 最小比赛时长(秒)
            max_duration: 最大比赛时长(秒)
            limit: 返回结果数量限制
            
        Returns:
            比赛信息列表
        """
        print(f"🔍 执行复合搜索...")
        print(f"搜索条件: {conditions}")
        
        # 分别搜索各个条件，然后取交集
        all_results = []
        
        if conditions.get('team'):
            team_matches = self.search_matches_by_team(
                conditions['team'], 
                limit=conditions.get('limit', 200)
            )
            all_results.append(set(match['id'] for match in team_matches))
        
        if conditions.get('player'):
            player_matches = self.search_matches_by_player(
                conditions['player'], 
                limit=conditions.get('limit', 200)
            )
            all_results.append(set(match['id'] for match in player_matches))
        
        if conditions.get('hero'):
            hero_matches = self.search_matches_by_hero(
                conditions['hero'], 
                limit=conditions.get('limit', 200)
            )
            all_results.append(set(match['id'] for match in hero_matches))
        
        if conditions.get('league'):
            league_matches = self.search_matches_by_league(
                conditions['league'], 
                limit=conditions.get('limit', 200)
            )
            all_results.append(set(match['id'] for match in league_matches))
        
        # 如果没有搜索条件，获取时间范围内的比赛
        if not all_results:
            match_ids = self.get_all_match_ids(
                start_date=conditions.get('start_date'),
                end_date=conditions.get('end_date'),
                max_matches=conditions.get('limit', 100)
            )
            return [{'id': match_id} for match_id in match_ids]
        
        # 取交集
        if len(all_results) == 1:
            common_ids = all_results[0]
        else:
            common_ids = set.intersection(*all_results)
        
        print(f"✅ 复合搜索完成，找到 {len(common_ids)} 场符合条件的比赛")
        return [{'id': match_id} for match_id in common_ids]
    
    def get_match_details_batch(self, match_ids: List[int]) -> List[Dict]:
        """
        批量获取比赛详细信息
        
        Args:
            match_ids: 比赛ID列表
            
        Returns:
            比赛详细信息列表
        """
        print(f"📋 批量获取 {len(match_ids)} 场比赛详情...")
        
        all_details = []
        
        # 分批处理以避免API限流
        for i in range(0, len(match_ids), self.batch_size):
            batch_ids = match_ids[i:i + self.batch_size]
            print(f"   处理第 {i//self.batch_size + 1} 批 ({len(batch_ids)} 场比赛)")
            
            # 使用多线程加速
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_id = {
                    executor.submit(self.service.get_match, match_id): match_id 
                    for match_id in batch_ids
                }
                
                for future in as_completed(future_to_id):
                    match_id = future_to_id[future]
                    try:
                        match_detail = future.result()
                        if match_detail:
                            all_details.append(match_detail)
                    except Exception as e:
                        print(f"⚠️  获取比赛 {match_id} 详情失败: {e}")
            
            # 避免API限流
            if i + self.batch_size < len(match_ids):
                time.sleep(1)
        
        print(f"✅ 成功获取 {len(all_details)} 场比赛详情")
        return all_details
    
    def save_match_data(self, matches: List[Dict], filename_prefix: str = "matches") -> str:
        """
        保存比赛数据到文件
        
        Args:
            matches: 比赛数据列表
            filename_prefix: 文件名前缀
            
        Returns:
            保存的文件路径
        """
        return self.service.save_data(matches, filename_prefix, "match_data")
    
    def collect_training_data(self, **conditions) -> Dict:
        """
        收集AI训练数据的完整流程
        
        Returns:
            包含统计信息和文件路径的字典
        """
        print("🚀 开始收集AI训练数据...")
        start_time = time.time()
        
        # 1. 搜索符合条件的比赛
        match_results = self.complex_search(**conditions)
        match_ids = [match['id'] for match in match_results]
        
        if not match_ids:
            print("❌ 未找到符合条件的比赛")
            return {'success': False, 'message': '未找到符合条件的比赛'}
        
        print(f"📊 找到 {len(match_ids)} 场符合条件的比赛")
        
        # 2. 获取比赛详情
        match_details = self.get_match_details_batch(match_ids)
        
        if not match_details:
            print("❌ 未能获取比赛详情")
            return {'success': False, 'message': '未能获取比赛详情'}
        
        # 3. 保存数据
        filepath = self.save_match_data(match_details, "training_matches")
        
        # 4. 生成统计信息
        end_time = time.time()
        stats = {
            'total_matches': len(match_details),
            'collection_time': round(end_time - start_time, 2),
            'average_match_duration': sum(m.get('duration', 0) for m in match_details) / len(match_details) if match_details else 0,
            'game_modes': {},
            'date_range': {
                'earliest': min(m.get('startDateTime', '') for m in match_details) if match_details else None,
                'latest': max(m.get('startDateTime', '') for m in match_details) if match_details else None
            }
        }
        
        # 统计游戏模式
        for match in match_details:
            game_mode = match.get('gameMode', 'Unknown')
            stats['game_modes'][game_mode] = stats['game_modes'].get(game_mode, 0) + 1
        
        result = {
            'success': True,
            'filepath': filepath,
            'stats': stats,
            'search_conditions': conditions
        }
        
        print("🎉 AI训练数据收集完成！")
        print(f"📁 数据文件: {filepath}")
        print(f"📊 统计信息: {stats}")
        
        return result


def main():
    """测试和使用示例"""
    # API密钥
    api_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJTdWJqZWN0IjoiYzM1OGY4N2YtYjI3Ny00MTZiLTliOTQtNjQxNDUyZmVhZTdlIiwiU3RlYW1JZCI6IjE2NDgzNDU1NyIsIkFQSVVzZXIiOiJ0cnVlIiwibmJmIjoxNzU3OTk4MjE0LCJleHAiOjE3ODk1MzQyMTQsImlhdCI6MTc1Nzk5ODIxNCwiaXNzIjoiaHR0cHM6Ly9hcGkuc3RyYXR6LmNvbSJ9.r_3s8lSC3uXd7v0LhnP2cvYRByQf56EtUONikFS_x_4'
    
    # 创建收集器
    collector = MatchDataCollector(api_key)
    
    print("🎯 比赛数据收集工具")
    print("=" * 50)
    
    # 示例1: 获取最近的比赛ID
    print("\n1️⃣ 获取最近的比赛ID:")
    recent_match_ids = collector.get_all_match_ids(
        start_date='2024-09-01',
        end_date='2024-09-16',
        max_matches=50
    )
    print(f"获取到 {len(recent_match_ids)} 场比赛ID")
    
    # 示例2: 搜索特定英雄的比赛
    print("\n2️⃣ 搜索特定英雄的比赛:")
    hero_matches = collector.search_matches_by_hero('Pudge', limit=20)
    print(f"找到 {len(hero_matches)} 场Pudge比赛")
    
    # 示例3: 复合搜索
    print("\n3️⃣ 复合搜索:")
    complex_results = collector.complex_search(
        hero='Invoker',
        start_date='2024-09-01',
        end_date='2024-09-16',
        limit=30
    )
    print(f"复合搜索找到 {len(complex_results)} 场比赛")
    
    # 示例4: 收集AI训练数据
    print("\n4️⃣ 收集AI训练数据:")
    training_data = collector.collect_training_data(
        hero='Anti-Mage',
        start_date='2024-08-01',
        end_date='2024-09-16',
        limit=25
    )
    
    if training_data['success']:
        print(f"训练数据已保存到: {training_data['filepath']}")
        print(f"数据统计: {training_data['stats']}")


if __name__ == '__main__':
    main()