"""
灵活的 STRATZ API 服务
支持动态 GraphQL 查询和直接 JSON 处理
"""

import requests
import time
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)

class QueryBuilder:
    """GraphQL 查询构建器"""
    
    @staticmethod
    def build_hero_query(fields: List[str] = None) -> str:
        """构建英雄查询"""
        default_fields = ['id', 'displayName', 'shortName']
        fields = fields or default_fields
        
        fields_str = '\n'.join([f'            {field}' for field in fields])
        
        return f"""
        {{
            constants {{
                heroes {{
{fields_str}
                }}
            }}
        }}
        """
    
    @staticmethod
    def build_match_query(match_id: int, fields: List[str] = None) -> str:
        """构建比赛查询"""
        default_fields = ['id', 'didRadiantWin', 'durationSeconds', 'startDateTime']
        fields = fields or default_fields
        
        fields_str = '\n'.join([f'            {field}' for field in fields])
        
        return f"""
        {{
            match(id: {match_id}) {{
{fields_str}
            }}
        }}
        """
    
    @staticmethod
    def build_player_query(steam_id: int, fields: List[str] = None) -> str:
        """构建玩家查询"""
        default_fields = [
            'steamAccount { id name }',
            'matchCount',
            'winCount'
        ]
        fields = fields or default_fields
        
        fields_str = '\n'.join([f'            {field}' for field in fields])
        
        return f"""
        {{
            player(steamAccountId: {steam_id}) {{
{fields_str}
            }}
        }}
        """

class QueryTemplates:
    """常用查询模板"""
    
    LIVE_MATCHES = """
    {
        live {
            matches {
                matchId
                gameTime
                averageRank
                spectators
                gameMode
                players {
                    heroId
                    steamAccount {
                        name
                    }
                }
            }
        }
    }
    """
    
    HERO_STATS = """
    {
        heroStats {
            winDay(heroIds: [1, 2, 3, 4, 5]) {
                heroId
                matchCount
                winCount
            }
        }
    }
    """
    
    PLAYER_PERFORMANCE = """
    query PlayerPerf($steamId: Long!) {
        player(steamAccountId: $steamId) {
            steamAccount {
                id
                name
                isAnonymous
            }
            matchCount
            winCount
            performance {
                imp
                winRate
                avgKills
                avgDeaths
                avgAssists
            }
            matches(take: 10) {
                id
                heroId
                isVictory
                kills
                deaths
                assists
                startDateTime
            }
        }
    }
    """
    
    MATCH_DETAILS = """
    query MatchDetails($matchId: Long!) {
        match(id: $matchId) {
            id
            didRadiantWin
            durationSeconds
            startDateTime
            gameMode
            lobbyType
            numHumanPlayers
            league {
                id
                displayName
                tier
            }
            players {
                steamAccountId
                heroId
                playerSlot
                isRadiant
                kills
                deaths
                assists
                lastHits
                denies
                goldPerMinute
                experiencePerMinute
                level
                items {
                    itemId
                }
            }
            pickBans {
                heroId
                order
                isPick
                isRadiant
            }
        }
    }
    """

# 字段配置
FIELD_CONFIGS = {
    'hero': {
        'basic': ['id', 'displayName', 'shortName'],
        'detailed': [
            'id', 'displayName', 'shortName', 'language { displayName }'
        ],
        'full': [
            'id', 'displayName', 'shortName', 'language { displayName }',
            'stats { primaryAttribute complexity }'
        ]
    },
    'match': {
        'basic': ['id', 'didRadiantWin', 'durationSeconds', 'startDateTime'],
        'detailed': [
            'id', 'didRadiantWin', 'durationSeconds', 'startDateTime',
            'gameMode', 'lobbyType', 'numHumanPlayers',
            'league { id displayName tier }'
        ],
        'full': [
            'id', 'didRadiantWin', 'durationSeconds', 'startDateTime',
            'gameMode', 'lobbyType', 'numHumanPlayers',
            'league { id displayName tier }',
            'players { steamAccountId heroId kills deaths assists goldPerMinute }',
            'pickBans { heroId isPick isRadiant order }'
        ]
    },
    'player': {
        'basic': ['steamAccount { id name }', 'matchCount', 'winCount'],
        'detailed': [
            'steamAccount { id name isAnonymous }',
            'matchCount', 'winCount',
            'performance { imp winRate avgKills avgDeaths }'
        ],
        'full': [
            'steamAccount { id name isAnonymous avatar countryCode }',
            'matchCount', 'winCount',
            'performance { imp winRate avgKills avgDeaths avgAssists }',
            'ranks { rank seasonRankId }',
            'behaviorScore'
        ]
    }
}

class StratzService:
    """灵活的 STRATZ API 服务"""
    
    def __init__(self, api_key: str = None, rate_limit_delay: float = 0.05):
        """
        初始化 STRATZ API 服务
        
        Args:
            api_key: API 密钥
            rate_limit_delay: 速率限制延迟（秒）
        """
        self.api_key = api_key or os.getenv('STRATZ_API_KEY')
        self.rate_limit_delay = rate_limit_delay
        self.base_url = "https://api.stratz.com/graphql"
        
        # 基于成功测试的请求头
        self.headers = {
            'User-Agent': 'STRATZ_API',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if self.api_key:
            self.headers['Authorization'] = f'Bearer {self.api_key}'
        
        self.builder = QueryBuilder()
    
    def query(self, query_string: str, variables: Dict = None) -> Optional[Dict]:
        """
        通用 GraphQL 查询方法
        
        Args:
            query_string: GraphQL 查询字符串
            variables: 查询变量
            
        Returns:
            查询结果 JSON 或 None
        """
        payload = {
            'query': query_string,
            'variables': variables or {}
        }
        
        # 基于成功测试的网络配置
        session_configs = [
            {"proxies": {}, "verify": True},
            {"verify": False},
            {"proxies": {}, "verify": False}
        ]
        
        for i, config in enumerate(session_configs, 1):
            try:
                response = requests.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload,
                    timeout=30,
                    **config
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if 'errors' in result:
                        logger.error(f"GraphQL 错误: {result['errors']}")
                        return None
                    
                    # 控制请求频率
                    time.sleep(self.rate_limit_delay)
                    return result
                    
                elif response.status_code == 403:
                    logger.error("403 Forbidden - 检查 API 密钥和权限")
                    return None
                    
                elif response.status_code == 429:
                    logger.warning("速率限制触发，等待...")
                    time.sleep(self.rate_limit_delay * 3)
                    continue
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"网络配置 {i} 失败: {e}")
                continue
        
        logger.error("所有网络配置都失败了")
        return None
    
    def test_connection(self) -> bool:
        """测试连接"""
        test_query = """
        {
            __schema {
                queryType {
                    name
                }
            }
        }
        """
        
        result = self.query(test_query)
        return result is not None
    
    # === 基础数据方法 ===
    
    def get_heroes(self, fields: Union[List[str], str] = 'basic') -> List[Dict]:
        """
        获取英雄数据
        
        Args:
            fields: 字段列表或预设配置名称 ('basic', 'detailed', 'full')
        """
        if isinstance(fields, str):
            fields = FIELD_CONFIGS['hero'].get(fields, FIELD_CONFIGS['hero']['basic'])
        
        query = self.builder.build_hero_query(fields)
        result = self.query(query)
        
        if result and 'data' in result:
            return result['data']['constants']['heroes']
        return []
    
    def get_items(self, fields: List[str] = None) -> List[Dict]:
        """获取物品数据"""
        default_fields = ['id', 'displayName', 'shortName']
        fields = fields or default_fields
        
        fields_str = '\n'.join([f'            {field}' for field in fields])
        
        query = f"""
        {{
            constants {{
                items {{
{fields_str}
                }}
            }}
        }}
        """
        
        result = self.query(query)
        if result and 'data' in result:
            return result['data']['constants']['items']
        return []
    
    def get_live_matches(self) -> List[Dict]:
        """获取直播比赛"""
        result = self.query(QueryTemplates.LIVE_MATCHES)
        if result and 'data' in result:
            return result['data']['live']['matches']
        return []
    
    # === 比赛相关方法 ===
    
    def get_match(self, match_id: int, fields: Union[List[str], str] = 'basic') -> Optional[Dict]:
        """
        获取比赛数据
        
        Args:
            match_id: 比赛 ID
            fields: 字段列表或预设配置名称
        """
        if isinstance(fields, str):
            fields = FIELD_CONFIGS['match'].get(fields, FIELD_CONFIGS['match']['basic'])
        
        query = self.builder.build_match_query(match_id, fields)
        result = self.query(query)
        
        if result and 'data' in result:
            return result['data']['match']
        return None
    
    def get_match_detailed(self, match_id: int) -> Optional[Dict]:
        """获取比赛详细信息（使用模板）"""
        result = self.query(QueryTemplates.MATCH_DETAILS, {"matchId": match_id})
        if result and 'data' in result:
            return result['data']['match']
        return None
    
    # === 玩家相关方法 ===
    
    def get_player(self, steam_id: int, fields: Union[List[str], str] = 'basic') -> Optional[Dict]:
        """
        获取玩家数据
        
        Args:
            steam_id: Steam ID
            fields: 字段列表或预设配置名称
        """
        if isinstance(fields, str):
            fields = FIELD_CONFIGS['player'].get(fields, FIELD_CONFIGS['player']['basic'])
        
        query = self.builder.build_player_query(steam_id, fields)
        result = self.query(query)
        
        if result and 'data' in result:
            return result['data']['player']
        return None
    
    def get_player_performance(self, steam_id: int) -> Optional[Dict]:
        """获取玩家表现数据（使用模板）"""
        result = self.query(QueryTemplates.PLAYER_PERFORMANCE, {"steamId": steam_id})
        if result and 'data' in result:
            return result['data']['player']
        return None
    
    def get_player_matches(self, steam_id: int, limit: int = 20, fields: List[str] = None) -> List[Dict]:
        """获取玩家比赛记录"""
        default_fields = ['id', 'heroId', 'startDateTime']
        fields = fields or default_fields
        
        fields_str = '\n'.join([f'                {field}' for field in fields])
        
        query = f"""
        {{
            player(steamAccountId: {steam_id}) {{
                matches(request: {{take: {limit}}}) {{
{fields_str}
                }}
            }}
        }}
        """
        
        result = self.query(query)
        if result and 'data' in result:
            player_data = result['data']['player']
            return player_data['matches'] if player_data else []
        return []
    
    # === 统计相关方法 ===
    
    def get_hero_stats(self, hero_ids: List[int] = None) -> Dict:
        """获取英雄统计数据"""
        result = self.query(QueryTemplates.HERO_STATS)
        if result and 'data' in result and 'heroStats' in result['data']:
            return result['data']['heroStats']
        return {}
    
    # === 原始查询方法 ===
    
    def raw_query(self, query_string: str, variables: Dict = None) -> Optional[Dict]:
        """直接执行原始 GraphQL 查询"""
        return self.query(query_string, variables)
    
    # === 便捷方法 ===
    
    def search_data(self, data_type: str, **kwargs) -> Union[List[Dict], Dict, None]:
        """
        通用搜索方法
        
        Args:
            data_type: 数据类型 ('heroes', 'matches', 'players', 'items')
            **kwargs: 搜索参数
        """
        if data_type == 'heroes':
            return self.get_heroes(kwargs.get('fields', 'basic'))
        elif data_type == 'items':
            return self.get_items(kwargs.get('fields'))
        elif data_type == 'live_matches':
            return self.get_live_matches()
        elif data_type == 'match' and 'match_id' in kwargs:
            return self.get_match(kwargs['match_id'], kwargs.get('fields', 'basic'))
        elif data_type == 'player' and 'steam_id' in kwargs:
            return self.get_player(kwargs['steam_id'], kwargs.get('fields', 'basic'))
        else:
            logger.error(f"不支持的数据类型: {data_type}")
            return None
    
    def explore_api(self, entity: str = 'heroes', sample_size: int = 3) -> Dict:
        """
        探索 API 结构
        
        Args:
            entity: 要探索的实体类型
            sample_size: 样本数量
        """
        results = {}
        
        if entity == 'heroes':
            # 先获取基础数据
            basic_heroes = self.get_heroes('basic')
            if basic_heroes:
                results['basic'] = basic_heroes[:sample_size]
                
                # 再获取详细数据
                detailed_heroes = self.get_heroes('detailed')
                if detailed_heroes:
                    results['detailed'] = detailed_heroes[:sample_size]
        
        elif entity == 'live_matches':
            live_matches = self.get_live_matches()
            if live_matches:
                results['live_matches'] = live_matches[:sample_size]
        
        return results
    
    # === 数据保存方法 ===
    
    def save_data(self, data: Union[Dict, List], filename: str, data_dir: str = "data") -> Optional[str]:
        """保存数据到文件"""
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_filename = f"{filename}_{timestamp}.json"
        filepath = os.path.join(data_dir, full_filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"数据已保存: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"保存数据失败: {e}")
            return None
    
    def batch_collect(self, tasks: List[Dict]) -> Dict:
        """
        批量收集数据
        
        Args:
            tasks: 任务列表，每个任务包含 {'type': 'heroes', 'params': {...}}
        """
        results = {}
        
        for i, task in enumerate(tasks):
            task_type = task.get('type')
            params = task.get('params', {})
            
            logger.info(f"执行任务 {i+1}/{len(tasks)}: {task_type}")
            
            try:
                if task_type == 'heroes':
                    data = self.get_heroes(params.get('fields', 'basic'))
                elif task_type == 'items':
                    data = self.get_items(params.get('fields'))
                elif task_type == 'live_matches':
                    data = self.get_live_matches()
                elif task_type == 'match':
                    data = self.get_match(params['match_id'], params.get('fields', 'basic'))
                elif task_type == 'player':
                    data = self.get_player(params['steam_id'], params.get('fields', 'basic'))
                elif task_type == 'raw_query':
                    data = self.raw_query(params['query'], params.get('variables'))
                else:
                    logger.warning(f"未知任务类型: {task_type}")
                    continue
                
                results[f"{task_type}_{i}"] = data
                
                # 保存数据（如果指定）
                if task.get('save'):
                    self.save_data(data, f"{task_type}_{i}")
                
                # 避免速率限制
                time.sleep(self.rate_limit_delay)
                
            except Exception as e:
                logger.error(f"任务 {task_type} 执行失败: {e}")
                results[f"{task_type}_{i}"] = None
        
        return results

# 使用示例
if __name__ == "__main__":
    # 初始化服务
    api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJTdWJqZWN0IjoiYzM1OGY4N2YtYjI3Ny00MTZiLTliOTQtNjQxNDUyZmVhZTdlIiwiU3RlYW1JZCI6IjE2NDgzNDU1NyIsIkFQSVVzZXIiOiJ0cnVlIiwibmJmIjoxNzU3OTk4MjE0LCJleHAiOjE3ODk1MzQyMTQsImlhdCI6MTc1Nzk5ODIxNCwiaXNzIjoiaHR0cHM6Ly9hcGkuc3RyYXR6LmNvbSJ9.r_3s8lSC3uXd7v0LhnP2cvYRByQf56EtUONikFS_x_4"
    service = StratzService(api_key=api_key)
    
    # 测试连接
    print("测试连接...")
    if service.test_connection():
        print("✅ 连接成功")
    else:
        print("❌ 连接失败")
        exit()
    
    # 基础使用
    print("\n=== 基础使用 ===")
    
    # 获取英雄数据
    heroes = service.get_heroes('basic')
    print(f"获取到 {len(heroes)} 个英雄")
    
    # 获取详细英雄数据
    detailed_heroes = service.get_heroes('detailed')
    print(f"详细英雄数据: {len(detailed_heroes)} 个")
    
    # 获取直播比赛
    live_matches = service.get_live_matches()
    print(f"当前直播比赛: {len(live_matches)} 场")
    
    # 高级使用
    print("\n=== 高级使用 ===")
    
    # 自定义字段查询
    custom_heroes = service.get_heroes(['id', 'displayName', 'complexity'])
    if custom_heroes:
        print(f"自定义字段英雄: {custom_heroes[0]}")
    
    # 原始查询
    raw_result = service.raw_query("""
    {
        heroStats {
            winDay(heroIds: [1, 2, 3]) {
                heroId
                matchCount
                winCount
            }
        }
    }
    """)
    
    if raw_result:
        print(f"原始查询结果: {raw_result['data']['heroStats']['winDay'][:2]}")
    
    # 批量任务
    print("\n=== 批量任务 ===")
    
    tasks = [
        {'type': 'heroes', 'params': {'fields': 'basic'}, 'save': True},
        {'type': 'live_matches', 'save': True},
        {'type': 'player', 'params': {'steam_id': 164834557, 'fields': 'detailed'}, 'save': True}
    ]
    
    batch_results = service.batch_collect(tasks)
    print(f"批量任务完成，获取到 {len(batch_results)} 个结果")
    
    # 探索 API
    print("\n=== 探索 API ===")
    exploration = service.explore_api('heroes', sample_size=2)
    print(f"API 探索结果: {list(exploration.keys())}")