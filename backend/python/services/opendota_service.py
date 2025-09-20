"""
OpenDota API 服务模块 - 更新版
用于获取Dota2比赛和选手数据（完全免费）
优化接口一致性，确保能正确集成到数据整合服务
"""

import requests
import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class OpenDotaService:
    """OpenDota API服务类 - 优化版"""
    
    def __init__(self, api_key: str = None, rate_limit_delay: float = 1.0):
        """
        初始化OpenDota API服务
        
        Args:
            api_key: API密钥（可选，提供后可以提高请求限制）
            rate_limit_delay: 速率限制延迟（秒），免费用户建议1秒
        """
        self.api_key = api_key or os.getenv('OPENDOTA_API_KEY')
        self.rate_limit_delay = rate_limit_delay
        self.base_url = "https://api.opendota.com/api"
        self.session = requests.Session()
        
        # 配置SOCKS5代理
        self.proxies = {
            "http": "socks5h://127.0.0.1:10808",
            "https": "socks5h://127.0.0.1:10808",
        }
        self.session.proxies.update(self.proxies)
        
        # 设置请求头
        self.session.headers.update({
            'User-Agent': 'DotaAnalysis/1.0 (contact@dotaanalysis.com)',
            'Accept': 'application/json'
        })
        
        # API密钥可以通过查询参数传递
        self.default_params = {}
        if self.api_key:
            self.default_params['api_key'] = self.api_key
    
    def _make_request(self, endpoint: str, params: Dict = None, debug: bool = False) -> Optional[Dict]:
        """发送API请求"""
        url = f"{self.base_url}/{endpoint}"
        
        # 合并默认参数
        final_params = {**self.default_params, **(params or {})}
        
        if debug:
            logger.debug(f"OpenDota API 调试:")
            logger.debug(f"  URL: {url}")
            logger.debug(f"  Params: {final_params}")
        
        try:
            response = self.session.get(url, params=final_params, timeout=30)
            
            if debug:
                logger.debug(f"  状态码: {response.status_code}")
                logger.debug(f"  响应头: {dict(response.headers)}")
            
            # 速率限制处理
            if response.status_code == 429:
                logger.warning("OpenDota API速率限制触发，等待...")
                time.sleep(self.rate_limit_delay * 2)
                return self._make_request(endpoint, params, debug)
            
            response.raise_for_status()
            
            # 控制请求频率
            time.sleep(self.rate_limit_delay)
            
            result = response.json()
            
            if debug and result:
                logger.debug(f"  数据类型: {type(result)}")
                if isinstance(result, list):
                    logger.debug(f"  数组长度: {len(result)}")
                elif isinstance(result, dict):
                    logger.debug(f"  字典键: {list(result.keys())}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenDota API请求失败: {e}")
            if debug:
                logger.debug(f"  请求异常: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            if debug:
                logger.debug(f"  JSON解析异常: {e}")
            return None
    
    def test_connection(self) -> bool:
        """测试API连接"""
        try:
            heroes = self.get_heroes()
            return heroes is not None and len(heroes) > 0
        except Exception as e:
            logger.error(f"测试OpenDota连接失败: {e}")
            return False
    
    def get_service_status(self) -> Dict:
        """获取服务状态 - 统一接口"""
        return {
            'service_name': 'OpenDota',
            'available': self.test_connection(),
            'api_key_provided': bool(self.api_key),
            'rate_limit_delay': self.rate_limit_delay,
            'base_url': self.base_url,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    # ========== 核心API方法 ==========
    
    def get_pro_matches(self, limit: int = 100) -> List[Dict]:
        """获取职业比赛列表"""
        params = {'limit': limit} if limit != 100 else None
        result = self._make_request("proMatches", params)
        return result or []
    
    def get_public_matches(self, limit: int = 100) -> List[Dict]:
        """获取公开比赛列表"""
        params = {}
        if limit != 100:
            params['limit'] = limit
        result = self._make_request("publicMatches", params)
        return result or []
    
    def get_match_details(self, match_id: int) -> Optional[Dict]:
        """获取比赛详情"""
        return self._make_request(f"matches/{match_id}")
    
    def get_match_detail(self, match_id: int) -> Optional[Dict]:
        """获取比赛详情 - 别名方法，保持兼容性"""
        return self.get_match_details(match_id)
    
    def get_heroes(self) -> List[Dict]:
        """获取英雄列表"""
        result = self._make_request("heroes")
        return result or []
    
    def get_teams(self) -> List[Dict]:
        """获取战队列表"""
        result = self._make_request("teams")
        return result or []
    
    def get_leagues(self) -> List[Dict]:
        """获取联赛列表"""
        result = self._make_request("leagues")
        return result or []
    
    def get_player(self, account_id: int) -> Optional[Dict]:
        """获取选手信息"""
        return self._make_request(f"players/{account_id}")
    
    def get_player_matches(self, account_id: int, limit: int = 20) -> List[Dict]:
        """获取选手比赛历史"""
        params = {'limit': limit}
        result = self._make_request(f"players/{account_id}/matches", params)
        return result or []
    
    def get_player_recent_matches(self, account_id: int, limit: int = 20) -> List[Dict]:
        """获取选手最近比赛 - 别名方法"""
        return self.get_player_matches(account_id, limit)
    
    def get_hero_stats(self) -> List[Dict]:
        """获取英雄统计数据"""
        result = self._make_request("heroStats")
        return result or []
    
    def search_players(self, query: str) -> List[Dict]:
        """搜索选手"""
        params = {'q': query}
        result = self._make_request("search", params)
        return result or []
    
    def get_live_matches(self) -> List[Dict]:
        """获取正在进行的比赛"""
        result = self._make_request("live")
        return result or []
    
    # ========== 扩展API方法 ==========
    
    def get_player_wl(self, account_id: int, limit: int = None) -> Optional[Dict]:
        """获取选手胜负记录"""
        params = {'limit': limit} if limit else None
        return self._make_request(f"players/{account_id}/wl", params)
    
    def get_player_heroes(self, account_id: int, limit: int = None) -> List[Dict]:
        """获取选手英雄统计"""
        params = {'limit': limit} if limit else None
        result = self._make_request(f"players/{account_id}/heroes", params)
        return result or []
    
    def get_player_peers(self, account_id: int, limit: int = None) -> List[Dict]:
        """获取选手队友统计"""
        params = {'limit': limit} if limit else None
        result = self._make_request(f"players/{account_id}/peers", params)
        return result or []
    
    def get_team_matches(self, team_id: int, limit: int = None) -> List[Dict]:
        """获取战队比赛历史"""
        params = {'limit': limit} if limit else None
        result = self._make_request(f"teams/{team_id}/matches", params)
        return result or []
    
    def get_team_players(self, team_id: int) -> List[Dict]:
        """获取战队选手列表"""
        result = self._make_request(f"teams/{team_id}/players")
        return result or []
    
    def get_team_heroes(self, team_id: int) -> List[Dict]:
        """获取战队英雄统计"""
        result = self._make_request(f"teams/{team_id}/heroes")
        return result or []
    
    def get_league_matches(self, league_id: int) -> List[Dict]:
        """获取联赛比赛列表"""
        result = self._make_request(f"leagues/{league_id}/matches")
        return result or []
    
    def get_league_teams(self, league_id: int) -> List[Dict]:
        """获取联赛参赛队伍"""
        result = self._make_request(f"leagues/{league_id}/teams")
        return result or []
    
    # ========== 批量操作方法 ==========
    
    def get_matches_batch(self, match_ids: List[int], max_concurrent: int = 5) -> List[Optional[Dict]]:
        """批量获取比赛详情"""
        results = []
        
        for i in range(0, len(match_ids), max_concurrent):
            batch = match_ids[i:i + max_concurrent]
            batch_results = []
            
            for match_id in batch:
                try:
                    match_data = self.get_match_details(match_id)
                    batch_results.append(match_data)
                except Exception as e:
                    logger.error(f"获取比赛详情失败 {match_id}: {e}")
                    batch_results.append(None)
                
                # 批量请求间的延迟
                time.sleep(self.rate_limit_delay)
            
            results.extend(batch_results)
            
            # 批次间的额外延迟
            if i + max_concurrent < len(match_ids):
                time.sleep(self.rate_limit_delay * 2)
        
        return results
    
    def get_players_batch(self, account_ids: List[int], max_concurrent: int = 5) -> List[Optional[Dict]]:
        """批量获取选手信息"""
        results = []
        
        for i in range(0, len(account_ids), max_concurrent):
            batch = account_ids[i:i + max_concurrent]
            batch_results = []
            
            for account_id in batch:
                try:
                    player_data = self.get_player(account_id)
                    batch_results.append(player_data)
                except Exception as e:
                    logger.error(f"获取选手信息失败 {account_id}: {e}")
                    batch_results.append(None)
                
                time.sleep(self.rate_limit_delay)
            
            results.extend(batch_results)
            
            if i + max_concurrent < len(account_ids):
                time.sleep(self.rate_limit_delay * 2)
        
        return results
    
    # ========== 测试和样本数据方法 ==========
    
    def test_api_access(self, debug: bool = True) -> Dict:
        """测试OpenDota API访问"""
        test_results = {
            'api_key_provided': bool(self.api_key),
            'endpoints_tested': {},
            'data_samples': {},
            'service_status': 'unknown'
        }
        
        logger.info("OpenDota API 访问测试...")
        
        # 测试各个端点
        endpoints_to_test = [
            ('heroes', '英雄数据'),
            ('proMatches', '职业比赛'),
            ('teams', '战队数据'),
            ('leagues', '联赛数据')
        ]
        
        successful_tests = 0
        
        for endpoint, description in endpoints_to_test:
            logger.info(f"测试 {description} ({endpoint})...")
            
            try:
                data = self._make_request(endpoint, debug=debug)
                success = data is not None
                test_results['endpoints_tested'][endpoint] = success
                
                if success:
                    logger.info(f"✅ {description}: 成功")
                    successful_tests += 1
                    
                    # 保存样本数据
                    if isinstance(data, list) and len(data) > 0:
                        test_results['data_samples'][endpoint] = {
                            'count': len(data),
                            'sample': data[0] if data else None
                        }
                        logger.info(f"   数据量: {len(data)} 条")
                    elif isinstance(data, dict):
                        test_results['data_samples'][endpoint] = {
                            'type': 'object',
                            'keys': list(data.keys()),
                            'sample': data
                        }
                        logger.info(f"   数据键: {list(data.keys())}")
                else:
                    logger.warning(f"❌ {description}: 失败")
                    
            except Exception as e:
                test_results['endpoints_tested'][endpoint] = False
                logger.error(f"❌ {description}: 异常 - {e}")
        
        # 测试特定比赛数据
        logger.info("测试特定比赛数据...")
        test_match_id = 8464041509
        match_data = self._make_request(f"matches/{test_match_id}", debug=debug)
        test_results['endpoints_tested']['match_detail'] = match_data is not None
        
        if match_data:
            logger.info("✅ 比赛详情: 成功")
            successful_tests += 1
            test_results['data_samples']['match_detail'] = {
                'match_id': match_data.get('match_id'),
                'duration': match_data.get('duration'),
                'radiant_win': match_data.get('radiant_win'),
                'start_time': match_data.get('start_time')
            }
        else:
            logger.warning("❌ 比赛详情: 失败")
        
        # 设置服务状态
        total_tests = len(endpoints_to_test) + 1  # +1 for match_detail
        if successful_tests == total_tests:
            test_results['service_status'] = 'healthy'
        elif successful_tests > 0:
            test_results['service_status'] = 'partial'
        else:
            test_results['service_status'] = 'down'
        
        test_results['success_rate'] = successful_tests / total_tests
        
        return test_results
    
    def fetch_and_save_samples(self, sample_dir: str = "data/samples") -> Dict:
        """获取并保存OpenDota样本数据"""
        if not os.path.exists(sample_dir):
            os.makedirs(sample_dir)
        
        samples = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        logger.info("开始获取OpenDota样本数据...")
        
        # 1. 英雄数据
        logger.info("1. 获取英雄数据...")
        heroes = self.get_heroes()
        if heroes:
            filepath = os.path.join(sample_dir, f"opendota_heroes_{timestamp}.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(heroes, f, ensure_ascii=False, indent=2)
            
            samples['heroes'] = {
                'count': len(heroes),
                'filepath': filepath,
                'sample': heroes[:3] if len(heroes) > 3 else heroes
            }
            logger.info(f"   ✅ 获取到 {len(heroes)} 个英雄")
        
        # 2. 职业比赛数据
        logger.info("2. 获取职业比赛数据...")
        pro_matches = self.get_pro_matches(limit=50)
        if pro_matches:
            filepath = os.path.join(sample_dir, f"opendota_pro_matches_{timestamp}.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(pro_matches, f, ensure_ascii=False, indent=2)
            
            samples['pro_matches'] = {
                'count': len(pro_matches),
                'filepath': filepath,
                'sample': pro_matches[:2] if len(pro_matches) > 2 else pro_matches
            }
            logger.info(f"   ✅ 获取到 {len(pro_matches)} 场比赛")
        
        # 3. 战队数据
        logger.info("3. 获取战队数据...")
        teams = self.get_teams()
        if teams:
            # 只保存前100个战队
            limited_teams = teams[:100]
            filepath = os.path.join(sample_dir, f"opendota_teams_{timestamp}.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(limited_teams, f, ensure_ascii=False, indent=2)
            
            samples['teams'] = {
                'count': len(limited_teams),
                'filepath': filepath,
                'sample': limited_teams[:3] if len(limited_teams) > 3 else limited_teams
            }
            logger.info(f"   ✅ 获取到 {len(limited_teams)} 个战队")
        
        # 4. 联赛数据
        logger.info("4. 获取联赛数据...")
        leagues = self.get_leagues()
        if leagues:
            filepath = os.path.join(sample_dir, f"opendota_leagues_{timestamp}.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(leagues, f, ensure_ascii=False, indent=2)
            
            samples['leagues'] = {
                'count': len(leagues),
                'filepath': filepath,
                'sample': leagues[:3] if len(leagues) > 3 else leagues
            }
            logger.info(f"   ✅ 获取到 {len(leagues)} 个联赛")
        
        # 5. 获取1-2场比赛的详细数据
        logger.info("5. 获取比赛详细数据...")
        if pro_matches:
            detailed_matches = []
            for match in pro_matches[:2]:  # 只获取前2场的详细数据
                match_id = match.get('match_id')
                if match_id:
                    logger.info(f"   获取比赛 {match_id} 详情...")
                    details = self.get_match_details(match_id)
                    if details:
                        detailed_matches.append(details)
                    time.sleep(2)  # 避免速率限制
            
            if detailed_matches:
                filepath = os.path.join(sample_dir, f"opendota_match_details_{timestamp}.json")
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(detailed_matches, f, ensure_ascii=False, indent=2)
                
                samples['match_details'] = {
                    'count': len(detailed_matches),
                    'filepath': filepath,
                    'sample': detailed_matches[0] if detailed_matches else None
                }
                logger.info(f"   ✅ 获取到 {len(detailed_matches)} 场详细比赛数据")
        
        logger.info("OpenDota样本数据获取完成！")
        return samples
    
    # ========== 数据质量检查 ==========
    
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
            'match': ['match_id', 'radiant_win', 'duration', 'start_time'],
            'player': ['account_id', 'profile'],
            'team': ['team_id', 'name'],
            'hero': ['id', 'name']
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

# 使用示例和测试
if __name__ == "__main__":
    logger.info("OpenDota API 测试工具")
    logger.info("=" * 40)
    
    # 初始化服务（无需API密钥）
    opendota = OpenDotaService()
    
    # 运行测试
    test_results = opendota.test_api_access(debug=True)
    
    logger.info(f"测试完成! 服务状态: {test_results['service_status']}")
    logger.info(f"成功率: {test_results['success_rate']*100:.1f}%")
    
    # 询问是否获取样本数据
    try:
        user_input = input("\n是否获取样本数据？(y/N): ").strip().lower()
        if user_input in ['y', 'yes']:
            logger.info("开始获取样本数据...")
            samples = opendota.fetch_and_save_samples()
            
            logger.info("✅ 样本数据获取完成:")
            for data_type, info in samples.items():
                logger.info(f"  {data_type}: {info['count']} 条数据")
                logger.info(f"    文件: {info['filepath']}")
    
    except KeyboardInterrupt:
        logger.info("操作被取消")
    except Exception as e:
        logger.error(f"发生错误: {e}")