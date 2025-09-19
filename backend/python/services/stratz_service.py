"""
灵活的 STRATZ API 服务 - 更新版
支持动态 GraphQL 查询和直接 JSON 处理
优化接口一致性，确保能正确集成到数据整合服务
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
    """灵活的 STRATZ API 服务 - 优化版"""
    
    def __init__(self, api_key: str = None, rate_limit_delay: float = 0.05):
        """
        初始化 STRATZ API 服务
        
        Args:
            api_key: API 密钥
            rate_limit_delay: 速率限制延迟（秒）
        """
        self.api_key = api_key or os.getenv('STRATZ_API_KEY')
        self.rate_limit_delay = rate_limit_delay
        
        # 从配置文件获取API URL
        try:
            from utils.config_loader import config_loader
            api_config = config_loader.get_api_config('stratz')
            self.base_url = api_config.get('graphql_url', "https://api.stratz.com/graphql")
        except ImportError:
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
        
        # 连接状态跟踪
        self._last_successful_request = None
        self._connection_status = 'unknown'
    
    def query(self, query_string: str, variables: Dict = None, retries: int = 3) -> Optional[Dict]:
        """
        通用 GraphQL 查询方法 - 优化版
        
        Args:
            query_string: GraphQL 查询字符串
            variables: 查询变量
            retries: 重试次数
            
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
        
        for attempt in range(retries):
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
                            continue  # 尝试下一个配置
                        
                        # 更新连接状态
                        self._last_successful_request = datetime.now()
                        self._connection_status = 'healthy'
                        
                        # 控制请求频率
                        time.sleep(self.rate_limit_delay)
                        return result
                        
                    elif response.status_code == 403:
                        logger.error("403 Forbidden - 检查 API 密钥和权限")
                        self._connection_status = 'auth_failed'
                        continue
                        
                    elif response.status_code == 429:
                        logger.warning("速率限制触发，等待...")
                        time.sleep(self.rate_limit_delay * (3 + attempt))
                        continue
                        
                except requests.exceptions.RequestException as e:
                    logger.debug(f"网络配置 {i} 失败 (尝试 {attempt+1}): {e}")
                    continue
            
            # 所有配置都失败，等待后重试
            if attempt < retries - 1:
                wait_time = (attempt + 1) * 2
                logger.debug(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
        
        # 所有重试都失败
        logger.error("所有网络配置和重试都失败了")
        self._connection_status = 'failed'
        return None
    
    def test_connection(self) -> bool:
        """测试连接 - 优化版"""
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
        is_connected = result is not None
        
        if is_connected:
            self._connection_status = 'healthy'
            logger.info("STRATZ API 连接测试成功")
        else:
            self._connection_status = 'failed'
            logger.warning("STRATZ API 连接测试失败")
        
        return is_connected
    
    def get_service_status(self) -> Dict:
        """获取服务状态 - 统一接口"""
        return {
            'service_name': 'STRATZ',
            'available': self._connection_status == 'healthy',
            'connection_status': self._connection_status,
            'api_key_provided': bool(self.api_key),
            'last_successful_request': self._last_successful_request.isoformat() if self._last_successful_request else None,
            'rate_limit_delay': self.rate_limit_delay,
            'base_url': self.base_url,
            'timestamp': datetime.utcnow().isoformat()
        }
    
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
        
        if result and 'data' in result and result['data']:
            constants = result['data'].get('constants', {})
            heroes = constants.get('heroes', [])
            logger.info(f"获取到 {len(heroes)} 个英雄数据")
            return heroes
        
        logger.warning("未获取到英雄数据")
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
        if result and 'data' in result and result['data']:
            constants = result['data'].get('constants', {})
            items = constants.get('items', [])
            return items
        return []
    
    def get_live_matches(self) -> List[Dict]:
        """获取直播比赛"""
        result = self.query(QueryTemplates.LIVE_MATCHES)
        if result and 'data' in result and result['data']:
            live_data = result['data'].get('live', {})
            matches = live_data.get('matches', [])
            logger.info(f"获取到 {len(matches)} 场直播比赛")
            return matches
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
        
        if result and 'data' in result and result['data']:
            match_data = result['data'].get('match')
            if match_data:
                logger.info(f"获取到比赛数据: {match_id}")
            else:
                logger.warning(f"未找到比赛: {match_id}")
            return match_data
        return None
    
    def get_match_detailed(self, match_id: int) -> Optional[Dict]:
        """获取比赛详细信息（使用模板）"""
        result = self.query(QueryTemplates.MATCH_DETAILS, {"matchId": match_id})
        if result and 'data' in result and result['data']:
            return result['data'].get('match')
        return None
    
    def get_detailed_match_analysis(self, match_id: int) -> Optional[Dict]:
        """获取详细比赛分析 - 别名方法，保持兼容性"""
        return self.get_match_detailed(match_id)
    
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
        
        if result and 'data' in result and result['data']:
            player_data = result['data'].get('player')
            if player_data:
                logger.info(f"获取到玩家数据: {steam_id}")
            else:
                logger.warning(f"未找到玩家: {steam_id}")
            return player_data
        return None
    
    def get_player_performance(self, steam_id: int) -> Optional[Dict]:
        """获取玩家表现数据（使用模板）"""
        result = self.query(QueryTemplates.PLAYER_PERFORMANCE, {"steamId": steam_id})
        if result and 'data' in result and result['data']:
            return result['data'].get('player')
        return None
    
    def get_player_matches(self, steam_id: int, limit: int = 20, fields: List[str] = None) -> List[Dict]:
        """获取玩家比赛记录"""
        default_fields = ['id', 'heroId', 'startDateTime', 'isVictory']
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
        if result and 'data' in result and result['data']:
            player_data = result['data'].get('player')
            matches = player_data.get('matches', []) if player_data else []
            logger.info(f"获取到玩家 {steam_id} 的 {len(matches)} 场比赛记录")
            return matches
        return []
    
    def get_player_heroes(self, steam_id: int, limit: int = None) -> List[Dict]:
        """获取玩家英雄统计"""
        query_limit = f", take: {limit}" if limit else ""
        
        query = f"""
        {{
            player(steamAccountId: {steam_id}) {{
                heroPerformance(request: {{orderBy: MATCH_COUNT{query_limit}}}) {{
                    heroId
                    matchCount
                    winCount
                    avgKills
                    avgDeaths
                    avgAssists
                }}
            }}
        }}
        """
        
        result = self.query(query)
        if result and 'data' in result and result['data']:
            player_data = result['data'].get('player')
            heroes = player_data.get('heroPerformance', []) if player_data else []
            return heroes
        return []
    
    # === 统计相关方法 ===
    
    def get_hero_stats(self, hero_ids: List[int] = None) -> Dict:
        """获取英雄统计数据"""
        if hero_ids:
            # 限制查询的英雄数量以避免请求过大
            limited_ids = hero_ids[:10]
            hero_ids_str = str(limited_ids).replace("'", "")
            
            query = f"""
            {{
                heroStats {{
                    winDay(heroIds: {hero_ids_str}) {{
                        heroId
                        matchCount
                        winCount
                    }}
                }}
            }}
            """
        else:
            query = QueryTemplates.HERO_STATS
        
        result = self.query(query)
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
        try:
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
        except Exception as e:
            logger.error(f"搜索数据失败 {data_type}: {e}")
            return None
    
    def explore_api(self, entity: str = 'heroes', sample_size: int = 3) -> Dict:
        """
        探索 API 结构
        
        Args:
            entity: 要探索的实体类型
            sample_size: 样本数量
        """
        results = {
            'entity': entity,
            'timestamp': datetime.now().isoformat(),
            'connection_status': self._connection_status
        }
        
        try:
            if entity == 'heroes':
                # 先获取基础数据
                basic_heroes = self.get_heroes('basic')
                if basic_heroes:
                    results['basic'] = basic_heroes[:sample_size]
                    
                    # 再获取详细数据
                    detailed_heroes = self.get_heroes('detailed')
                    if detailed_heroes:
                        results['detailed'] = detailed_heroes[:sample_size]
                else:
                    results['error'] = '无法获取英雄数据'
            
            elif entity == 'live_matches':
                live_matches = self.get_live_matches()
                if live_matches:
                    results['live_matches'] = live_matches[:sample_size]
                else:
                    results['live_matches'] = []
                    results['note'] = '当前没有直播比赛'
            
            elif entity == 'connection_test':
                results['connection_test'] = {
                    'success': self.test_connection(),
                    'api_key_provided': bool(self.api_key),
                    'service_status': self.get_service_status()
                }
        
        except Exception as e:
            results['error'] = str(e)
            logger.error(f"探索API失败 {entity}: {e}")
        
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
    
    def batch_collect(self, tasks: List[Dict], save_results: bool = False) -> Dict:
        """
        批量收集数据
        
        Args:
            tasks: 任务列表，每个任务包含 {'type': 'heroes', 'params': {...}}
            save_results: 是否自动保存结果
        """
        results = {
            'batch_id': datetime.now().strftime("%Y%m%d_%H%M%S"),
            'total_tasks': len(tasks),
            'completed_tasks': 0,
            'failed_tasks': 0,
            'results': {},
            'errors': []
        }
        
        for i, task in enumerate(tasks):
            task_type = task.get('type')
            params = task.get('params', {})
            task_id = f"{task_type}_{i}"
            
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
                    results['failed_tasks'] += 1
                    results['errors'].append(f"Task {task_id}: 未知任务类型")
                    continue
                
                results['results'][task_id] = {
                    'type': task_type,
                    'success': data is not None,
                    'data': data,
                    'data_count': len(data) if isinstance(data, list) else 1 if data else 0
                }
                
                # 保存数据（如果指定）
                if save_results and data:
                    filepath = self.save_data(data, task_id)
                    results['results'][task_id]['saved_to'] = filepath
                
                results['completed_tasks'] += 1
                
                # 避免速率限制
                time.sleep(self.rate_limit_delay)
                
            except Exception as e:
                logger.error(f"任务 {task_type} 执行失败: {e}")
                results['failed_tasks'] += 1
                results['errors'].append(f"Task {task_id}: {str(e)}")
        
        # 生成批量处理报告
        results['success_rate'] = results['completed_tasks'] / results['total_tasks'] if results['total_tasks'] > 0 else 0
        results['summary'] = f"完成 {results['completed_tasks']}/{results['total_tasks']} 个任务"
        
        logger.info(f"批量收集完成: {results['summary']}")
        return results
    
    # === 数据质量验证 ===
    
    def validate_data_quality(self, data: Dict, data_type: str) -> Dict:
        """验证数据质量"""
        quality_report = {
            'data_type': data_type,
            'is_valid': True,
            'completeness_score': 0.0,
            'issues': [],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if not data:
            quality_report['is_valid'] = False
            quality_report['issues'].append('数据为空')
            return quality_report
        
        # 根据数据类型验证必要字段
        required_fields = {
            'match': ['id', 'didRadiantWin'],
            'player': ['steamAccount'],
            'hero': ['id', 'displayName']
        }
        
        if data_type in required_fields:
            missing_fields = []
            for field in required_fields[data_type]:
                if field not in data or data[field] is None:
                    missing_fields.append(field)
            
            if missing_fields:
                quality_report['issues'].append(f'缺少必要字段: {missing_fields}')
                quality_report['completeness_score'] = (len(required_fields[data_type]) - len(missing_fields)) / len(required_fields[data_type])
            else:
                quality_report['completeness_score'] = 1.0
        
        quality_report['is_valid'] = len(quality_report['issues']) == 0
        
        return quality_report

# 使用示例
if __name__ == "__main__":
    # 初始化服务
    api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJTdWJqZWN0IjoiYzM1OGY4N2YtYjI3Ny00MTZiLTliOTQtNjQxNDUyZmVhZTdlIiwiU3RlYW1JZCI6IjE2NDgzNDU1NyIsIkFQSVVzZXIiOiJ0cnVlIiwibmJmIjoxNzU3OTk4MjE0LCJleHAiOjE3ODk1MzQyMTQsImlhdCI6MTc1Nzk5ODIxNCwiaXNzIjoiaHR0cHM6Ly9hcGkuc3RyYXR6LmNvbSJ9.r_3s8lSC3uXd7v0LhnP2cvYRByQf56EtUONikFS_x_4"
    service = StratzService(api_key=api_key)
    
    # 测试连接
    logger.info("测试STRATZ API连接...")
    connection_test = service.explore_api('connection_test')
    logger.info(f"连接测试结果: {connection_test}")
    
    if connection_test.get('connection_test', {}).get('success'):
        logger.info("✅ STRATZ API 连接成功")
        
        # 基础使用示例
        logger.info("\n=== 基础使用示例 ===")
        
        # 获取英雄数据
        heroes = service.get_heroes('basic')
        logger.info(f"获取到 {len(heroes)} 个英雄")
        
        # 获取详细英雄数据
        detailed_heroes = service.get_heroes('detailed')
        logger.info(f"详细英雄数据: {len(detailed_heroes)} 个")
        
        # 获取直播比赛
        live_matches = service.get_live_matches()
        logger.info(f"当前直播比赛: {len(live_matches)} 场")
        
        # 批量任务示例
        logger.info("\n=== 批量任务示例 ===")
        tasks = [
            {'type': 'heroes', 'params': {'fields': 'basic'}},
            {'type': 'live_matches'},
            {'type': 'player', 'params': {'steam_id': 164834557, 'fields': 'detailed'}}
        ]
        
        batch_results = service.batch_collect(tasks, save_results=True)
        logger.info(f"批量任务完成: {batch_results['summary']}")
        
    else:
        logger.error("❌ STRATZ API 连接失败")