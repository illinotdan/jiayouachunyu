"""
OpenDota API 服务模块
用于获取Dota2比赛和选手数据（完全免费）
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
    """OpenDota API服务类"""
    
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
            print(f"🔍 OpenDota API 调试:")
            print(f"  URL: {url}")
            print(f"  Params: {final_params}")
        
        try:
            response = self.session.get(url, params=final_params, timeout=30)
            
            if debug:
                print(f"  状态码: {response.status_code}")
                print(f"  响应头: {dict(response.headers)}")
            
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
                print(f"  数据类型: {type(result)}")
                if isinstance(result, list):
                    print(f"  数组长度: {len(result)}")
                elif isinstance(result, dict):
                    print(f"  字典键: {list(result.keys())}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenDota API请求失败: {e}")
            if debug:
                print(f"  请求异常: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            if debug:
                print(f"  JSON解析异常: {e}")
            return None
    
    def test_api_access(self, debug: bool = True) -> Dict:
        """测试OpenDota API访问"""
        test_results = {
            'api_key_provided': bool(self.api_key),
            'endpoints_tested': {},
            'data_samples': {}
        }
        
        print("🧪 OpenDota API 访问测试...")
        
        # 测试各个端点
        endpoints_to_test = [
            ('heroes', '英雄数据'),
            ('proMatches', '职业比赛'),
            ('teams', '战队数据'),
            ('leagues', '联赛数据')
        ]
        
        for endpoint, description in endpoints_to_test:
            print(f"\n测试 {description} ({endpoint})...")
            
            try:
                data = self._make_request(endpoint, debug=debug)
                success = data is not None
                test_results['endpoints_tested'][endpoint] = success
                
                if success:
                    print(f"✅ {description}: 成功")
                    
                    # 保存样本数据
                    if isinstance(data, list) and len(data) > 0:
                        test_results['data_samples'][endpoint] = {
                            'count': len(data),
                            'sample': data[0] if data else None
                        }
                        print(f"   数据量: {len(data)} 条")
                    elif isinstance(data, dict):
                        test_results['data_samples'][endpoint] = {
                            'type': 'object',
                            'keys': list(data.keys()),
                            'sample': data
                        }
                        print(f"   数据键: {list(data.keys())}")
                else:
                    print(f"❌ {description}: 失败")
                    
            except Exception as e:
                test_results['endpoints_tested'][endpoint] = False
                print(f"❌ {description}: 异常 - {e}")
        
        # 测试特定比赛数据
        print(f"\n测试特定比赛数据...")
        test_match_id = 8464041509
        match_data = self._make_request(f"matches/{test_match_id}", debug=debug)
        test_results['endpoints_tested']['match_detail'] = match_data is not None
        
        if match_data:
            print(f"✅ 比赛详情: 成功")
            test_results['data_samples']['match_detail'] = {
                'match_id': match_data.get('match_id'),
                'duration': match_data.get('duration'),
                'radiant_win': match_data.get('radiant_win'),
                'start_time': match_data.get('start_time')
            }
        else:
            print(f"❌ 比赛详情: 失败")
        
        return test_results
    
    def get_pro_matches(self, limit: int = 100) -> List[Dict]:
        """获取职业比赛列表"""
        return self._make_request("proMatches") or []
    
    def get_match_details(self, match_id: int) -> Optional[Dict]:
        """获取比赛详情"""
        return self._make_request(f"matches/{match_id}")
    
    def get_heroes(self) -> List[Dict]:
        """获取英雄列表"""
        return self._make_request("heroes") or []
    
    def get_teams(self) -> List[Dict]:
        """获取战队列表"""
        return self._make_request("teams") or []
    
    def get_leagues(self) -> List[Dict]:
        """获取联赛列表"""
        return self._make_request("leagues") or []
    
    def get_player(self, account_id: int) -> Optional[Dict]:
        """获取选手信息"""
        return self._make_request(f"players/{account_id}")
    
    def get_player_matches(self, account_id: int, limit: int = 20) -> List[Dict]:
        """获取选手比赛历史"""
        params = {'limit': limit}
        return self._make_request(f"players/{account_id}/matches", params) or []
    
    def get_hero_stats(self) -> List[Dict]:
        """获取英雄统计数据"""
        return self._make_request("heroStats") or []
    
    def search_players(self, query: str) -> List[Dict]:
        """搜索选手"""
        params = {'q': query}
        return self._make_request("search", params) or []
    
    def get_live_matches(self) -> List[Dict]:
        """获取正在进行的比赛"""
        return self._make_request("live") or []
    
    def fetch_and_save_samples(self, sample_dir: str = "data/samples") -> Dict:
        """获取并保存OpenDota样本数据"""
        if not os.path.exists(sample_dir):
            os.makedirs(sample_dir)
        
        samples = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print("📥 开始获取OpenDota样本数据...")
        
        # 1. 英雄数据
        print("1. 获取英雄数据...")
        heroes = self.get_heroes()
        if heroes:
            filepath = os.path.join(sample_dir, f"opendota_heroes_{timestamp}.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(heroes, f, ensure_ascii=False, indent=2)
            
            samples['heroes'] = {
                'count': len(heroes),
                'filepath': filepath,
                'sample': heroes[:3]
            }
            print(f"   ✅ 获取到 {len(heroes)} 个英雄")
        
        # 2. 职业比赛数据
        print("2. 获取职业比赛数据...")
        pro_matches = self.get_pro_matches()
        if pro_matches:
            # 只保存前50场比赛
            limited_matches = pro_matches[:50]
            filepath = os.path.join(sample_dir, f"opendota_pro_matches_{timestamp}.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(limited_matches, f, ensure_ascii=False, indent=2)
            
            samples['pro_matches'] = {
                'count': len(limited_matches),
                'filepath': filepath,
                'sample': limited_matches[:2]
            }
            print(f"   ✅ 获取到 {len(limited_matches)} 场比赛")
        
        # 3. 战队数据
        print("3. 获取战队数据...")
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
                'sample': limited_teams[:3]
            }
            print(f"   ✅ 获取到 {len(limited_teams)} 个战队")
        
        # 4. 联赛数据
        print("4. 获取联赛数据...")
        leagues = self.get_leagues()
        if leagues:
            filepath = os.path.join(sample_dir, f"opendota_leagues_{timestamp}.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(leagues, f, ensure_ascii=False, indent=2)
            
            samples['leagues'] = {
                'count': len(leagues),
                'filepath': filepath,
                'sample': leagues[:3]
            }
            print(f"   ✅ 获取到 {len(leagues)} 个联赛")
        
        # 5. 获取1-2场比赛的详细数据
        print("5. 获取比赛详细数据...")
        if pro_matches:
            detailed_matches = []
            for match in pro_matches[:2]:  # 只获取前2场的详细数据
                match_id = match.get('match_id')
                if match_id:
                    print(f"   获取比赛 {match_id} 详情...")
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
                print(f"   ✅ 获取到 {len(detailed_matches)} 场详细比赛数据")
        
        print("📥 OpenDota样本数据获取完成！")
        return samples

# 使用示例和测试
if __name__ == "__main__":
    print("🎮 OpenDota API 测试工具")
    print("=" * 40)
    
    # 初始化服务（无需API密钥）
    opendota = OpenDotaService()
    
    # 运行测试
    test_results = opendota.test_api_access(debug=True)
    
    print(f"\n📊 测试完成!")
    
    # 询问是否获取样本数据
    try:
        user_input = input("\n是否获取样本数据？(y/N): ").strip().lower()
        if user_input in ['y', 'yes']:
            print("\n📥 开始获取样本数据...")
            samples = opendota.fetch_and_save_samples()
            
            print(f"\n✅ 样本数据获取完成:")
            for data_type, info in samples.items():
                print(f"  {data_type}: {info['count']} 条数据")
                print(f"    文件: {info['filepath']}")
    
    except KeyboardInterrupt:
        print("\n⏹️  操作被取消")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")