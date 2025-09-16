"""
数据整合服务模块
协调多个数据源，提供统一的数据获取接口
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from .opendota_service import OpenDotaService
from .stratz_service import StratzService

logger = logging.getLogger(__name__)

class DataIntegrationService:
    """数据整合服务类"""
    
    def __init__(self, opendota_key: str = None, stratz_key: str = None):
        self.opendota_service = OpenDotaService(api_key=opendota_key)
        self.stratz_service = StratzService(api_key=stratz_key)
        self.sample_dir = "data/samples"
        self.combined_samples_dir = "data/combined_samples"
        
        # 创建样本数据目录
        os.makedirs(self.sample_dir, exist_ok=True)
        os.makedirs(self.combined_samples_dir, exist_ok=True)
    
    def get_enhanced_match_data(self, match_id: int) -> Optional[Dict]:
        """
        获取增强版比赛数据
        结合OpenDota和STRATZ的数据
        """
        logger.info(f"获取增强版比赛数据: {match_id}")
        
        # 从OpenDota获取基础数据
        opendota_match = self.opendota_service.get_match_detail(match_id)
        if not opendota_match:
            logger.warning(f"OpenDota未找到比赛: {match_id}")
            return None
        
        # 从STRATZ获取详细分析
        stratz_analysis = self.stratz_service.get_detailed_match_analysis(match_id)
        
        # 整合数据
        enhanced_data = {
            'match_id': match_id,
            'opendota_data': opendota_match,
            'stratz_data': stratz_analysis,
            'integration_timestamp': datetime.now().isoformat(),
            'data_sources': {
                'opendota': bool(opendota_match),
                'stratz': bool(stratz_analysis)
            }
        }
        
        # 数据质量评估
        enhanced_data['data_quality'] = self._assess_data_quality(enhanced_data)
        
        return enhanced_data
    
    def _assess_data_quality(self, data: Dict) -> Dict:
        """评估数据质量"""
        quality = {
            'completeness': 0.0,
            'consistency': True,
            'source_reliability': {}
        }
        
        # 完整性评估
        opendota_data = data.get('opendota_data', {})
        stratz_data = data.get('stratz_data', {})
        
        # OpenDota数据完整性
        opendota_completeness = 0
        opendota_fields = ['match_id', 'radiant_win', 'duration', 'start_time', 'players']
        for field in opendota_fields:
            if field in opendota_data and opendota_data[field] is not None:
                opendota_completeness += 1
        
        opendota_completeness_score = opendota_completeness / len(opendota_fields)
        
        # STRATZ数据完整性
        stratz_completeness = 0
        if stratz_data:  # 确保stratz_data不是None
            stratz_fields = ['match', 'players', 'performance']
            for field in stratz_fields:
                if field in stratz_data and stratz_data[field] is not None:
                    stratz_completeness += 1
        
        stratz_completeness_score = stratz_completeness / len(stratz_fields)
        
        # 综合完整性
        quality['completeness'] = (opendota_completeness_score + stratz_completeness_score) / 2
        
        # 一致性检查
        if opendota_data and stratz_data:
            # 检查关键字段是否一致
            opendota_winner = opendota_data.get('radiant_win')
            stratz_match = stratz_data.get('match', {})
            stratz_winner = stratz_match.get('radiantWin') if stratz_match else None
            
            if opendota_winner is not None and stratz_winner is not None:
                quality['consistency'] = opendota_winner == stratz_winner
        
        quality['source_reliability'] = {
            'opendota': opendota_completeness_score,
            'stratz': stratz_completeness_score
        }
        
        return quality
    
    def get_player_enhanced_profile(self, account_id: int) -> Optional[Dict]:
        """
        获取增强版选手档案
        结合多个数据源的信息
        """
        logger.info(f"获取增强版选手档案: {account_id}")
        
        # 从OpenDota获取基础数据
        opendota_player = self.opendota_service.get_player(account_id)
        opendota_matches = self.opendota_service.get_player_recent_matches(account_id)
        
        # 从STRATZ获取补充数据
        stratz_player = self.stratz_service.get_player(account_id)
        stratz_matches = self.stratz_service.get_player_matches(account_id, limit=10)
        stratz_heroes = self.stratz_service.get_player_heroes(account_id)
        
        # 整合数据
        enhanced_profile = {
            'account_id': account_id,
            'opendota_profile': opendota_player,
            'opendota_matches': opendota_matches,
            'stratz_profile': stratz_player,
            'stratz_matches': stratz_matches,
            'stratz_heroes': stratz_heroes,
            'integration_timestamp': datetime.now().isoformat(),
            'data_sources': {
                'opendota_player': bool(opendota_player),
                'opendota_matches': bool(opendota_matches),
                'stratz_player': bool(stratz_player),
                'stratz_matches': bool(stratz_matches),
                'stratz_heroes': bool(stratz_heroes)
            }
        }
        
        # 生成综合分析
        enhanced_profile['analysis'] = self._analyze_player_profile(enhanced_profile)
        
        return enhanced_profile
    
    def _analyze_player_profile(self, profile: Dict) -> Dict:
        """分析选手档案"""
        analysis = {
            'profile_completeness': 0.0,
            'recent_performance': {},
            'hero_diversity': 0,
            'play_style_indicators': {}
        }
        
        # 档案完整性
        total_sources = len(profile['data_sources'])
        available_sources = sum(1 for v in profile['data_sources'].values() if v)
        analysis['profile_completeness'] = available_sources / total_sources
        
        # 近期表现分析
        if profile['opendota_matches']:
            matches = profile['opendota_matches'][:10]  # 最近10场比赛
            wins = sum(1 for match in matches if match.get('radiant_win') == (match.get('player_slot') < 128))
            
            analysis['recent_performance'] = {
                'total_matches': len(matches),
                'wins': wins,
                'win_rate': wins / len(matches) if matches else 0,
                'avg_kills': sum(match.get('kills', 0) for match in matches) / len(matches),
                'avg_deaths': sum(match.get('deaths', 0) for match in matches) / len(matches),
                'avg_assists': sum(match.get('assists', 0) for match in matches) / len(matches)
            }
        
        # 英雄多样性
        if profile['stratz_heroes']:
            heroes = profile['stratz_heroes']
            unique_heroes = len(set(hero.get('heroId') for hero in heroes if hero.get('heroId')))
            analysis['hero_diversity'] = unique_heroes
        
        return analysis
    
    def fetch_and_save_combined_samples(self, sample_size: int = 10):
        """获取并保存整合样本数据"""
        logger.info("开始获取整合样本数据...")
        
        samples = {}
        
        # 1. 获取增强版比赛数据样本
        logger.info("获取增强版比赛数据样本...")
        # 从OpenDota获取一些公开比赛ID
        public_matches = self.opendota_service.get_public_matches(limit=5)
        enhanced_matches = []
        
        for match in public_matches:
            match_id = match.get('match_id')
            if match_id:
                enhanced_match = self.get_enhanced_match_data(match_id)
                if enhanced_match:
                    enhanced_matches.append(enhanced_match)
                    logger.info(f"获取增强比赛数据: {match_id}")
                    
                    # 控制请求频率
                    import time
                    time.sleep(2)
        
        if enhanced_matches:
            filepath = self._save_combined_sample("enhanced_matches", enhanced_matches)
            samples['enhanced_matches'] = {
                'count': len(enhanced_matches),
                'filepath': filepath,
                'quality_summary': self._summarize_data_quality(enhanced_matches)
            }
        
        # 2. 获取增强版选手档案样本
        logger.info("获取增强版选手档案样本...")
        # 从一些知名选手开始
        sample_account_ids = [
            88367253,   # Miracle-
            41231571,   # Arteezy
            86745912,   # Somnus
            89758170,   # Paparazi
            87278757    # Ame
        ]
        
        enhanced_profiles = []
        for account_id in sample_account_ids:
            profile = self.get_player_enhanced_profile(account_id)
            if profile:
                enhanced_profiles.append(profile)
                logger.info(f"获取增强选手档案: {account_id}")
                
                import time
                time.sleep(3)  # 避免速率限制
        
        if enhanced_profiles:
            filepath = self._save_combined_sample("enhanced_profiles", enhanced_profiles)
            samples['enhanced_profiles'] = {
                'count': len(enhanced_profiles),
                'filepath': filepath,
                'completeness_summary': self._summarize_profile_completeness(enhanced_profiles)
            }
        
        # 3. 获取英雄数据对比
        logger.info("获取英雄数据对比...")
        opendota_heroes = self.opendota_service.get_heroes()
        stratz_heroes = self.stratz_service.get_heroes()
        
        hero_comparison = {
            'opendota_heroes': opendota_heroes,
            'stratz_heroes': stratz_heroes,
            'comparison': self._compare_hero_data(opendota_heroes, stratz_heroes)
        }
        
        filepath = self._save_combined_sample("hero_comparison", hero_comparison)
        samples['hero_comparison'] = {
            'opendota_count': len(opendota_heroes) if opendota_heroes else 0,
            'stratz_count': len(stratz_heroes) if stratz_heroes else 0,
            'filepath': filepath
        }
        
        logger.info("整合样本数据获取完成！")
        return samples
    
    def _save_combined_sample(self, data_type: str, data: Dict or List) -> str:
        """保存整合样本数据"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"combined_{data_type}_{timestamp}.json"
        filepath = os.path.join(self.combined_samples_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"整合样本数据已保存: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"保存整合样本数据失败: {e}")
            return None
    
    def _summarize_data_quality(self, matches: List[Dict]) -> Dict:
        """汇总数据质量"""
        qualities = [match.get('data_quality', {}) for match in matches]
        
        return {
            'avg_completeness': sum(q.get('completeness', 0) for q in qualities) / len(qualities) if qualities else 0,
            'consistency_rate': sum(1 for q in qualities if q.get('consistency', False)) / len(qualities) if qualities else 0,
            'total_matches': len(matches)
        }
    
    def _summarize_profile_completeness(self, profiles: List[Dict]) -> Dict:
        """汇总档案完整性"""
        completeness_scores = [profile.get('analysis', {}).get('profile_completeness', 0) for profile in profiles]
        
        return {
            'avg_completeness': sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0,
            'min_completeness': min(completeness_scores) if completeness_scores else 0,
            'max_completeness': max(completeness_scores) if completeness_scores else 0,
            'total_profiles': len(profiles)
        }
    
    def _compare_hero_data(self, opendota_heroes: List[Dict], stratz_heroes: List[Dict]) -> Dict:
        """对比英雄数据"""
        comparison = {
            'opendota_unique': len(opendota_heroes) if opendota_heroes else 0,
            'stratz_unique': len(stratz_heroes) if stratz_heroes else 0,
            'field_differences': {}
        }
        
        if opendota_heroes and stratz_heroes:
            # 简单的字段对比
            opendota_fields = set(opendota_heroes[0].keys()) if opendota_heroes else set()
            stratz_fields = set(stratz_heroes[0].keys()) if stratz_heroes else set()
            
            comparison['field_differences'] = {
                'opendota_only': list(opendota_fields - stratz_fields),
                'stratz_only': list(stratz_fields - opendota_fields),
                'common_fields': list(opendota_fields & stratz_fields)
            }
        
        return comparison

# 使用示例
if __name__ == "__main__":
    # 初始化整合服务
    integration_service = DataIntegrationService()
    
    # 获取并保存整合样本数据
    samples = integration_service.fetch_and_save_combined_samples(sample_size=5)
    
    # 打印样本统计
    print("\n=== 整合样本数据获取结果 ===")
    for data_type, info in samples.items():
        print(f"\n{data_type}:")
        if 'count' in info:
            print(f"  数量: {info['count']}")
        if 'filepath' in info:
            print(f"  保存路径: {info['filepath']}")
        if 'quality_summary' in info:
            print(f"  质量摘要: {info['quality_summary']}")
        if 'completeness_summary' in info:
            print(f"  完整性摘要: {info['completeness_summary']}")