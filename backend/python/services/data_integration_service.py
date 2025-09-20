"""
数据整合服务模块 - 更新版
协调多个数据源，提供统一的数据获取接口
集成 OpenDota、STRATZ、Liquipedia 三个数据源
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from services.opendota_service import OpenDotaService
from services.stratz_service import StratzService
from services.liquipedia_service import LiquipediaService

logger = logging.getLogger(__name__)

class DataIntegrationService:
    """数据整合服务类 - 集成所有数据源"""

    def __init__(self, opendota_key: str = None, stratz_key: str = None):
        """
        初始化数据整合服务

        Args:
            opendota_key: OpenDota API密钥
            stratz_key: STRATZ API密钥
        """
        self.opendota_service = OpenDotaService(api_key=opendota_key)
        self.stratz_service = StratzService(api_key=stratz_key)
        self.liquipedia_service = LiquipediaService()

        self.sample_dir = "data/samples"
        self.combined_samples_dir = "data/combined_samples"

        # 创建样本数据目录
        os.makedirs(self.sample_dir, exist_ok=True)
        os.makedirs(self.combined_samples_dir, exist_ok=True)

    # ========== 团队数据整合 ==========

    def get_enhanced_team_data(self, team_name: str) -> Optional[Dict]:
        """
        获取增强版战队数据
        结合 Liquipedia 和其他数据源的战队信息

        Args:
            team_name: 战队名称

        Returns:
            整合的战队数据
        """
        logger.info(f"获取增强版战队数据: {team_name}")

        try:
            # 从 Liquipedia 获取详细战队信息
            liquipedia_team = self.liquipedia_service.get_team_info(team_name)

            # 从 OpenDota 获取战队信息（如果有team_id）
            opendota_team = None
            if liquipedia_team:
                # 这里可以根据战队名称搜索OpenDota中的战队
                opendota_teams = self.opendota_service.get_teams()
                if opendota_teams:
                    # 简单的名称匹配
                    for team in opendota_teams:
                        if team.get('name') and team_name.lower() in team['name'].lower():
                            opendota_team = team
                            break

            # 从 STRATZ 获取战队相关数据（如果支持）
            # STRATZ 主要是比赛和选手数据，团队数据较少
            stratz_team = None

            # 整合数据
            enhanced_team = {
                'team_name': team_name,
                'liquipedia_data': liquipedia_team,
                'opendota_data': opendota_team,
                'stratz_data': stratz_team,
                'integration_timestamp': datetime.now().isoformat(),
                'data_sources': {
                    'liquipedia': bool(liquipedia_team),
                    'opendota': bool(opendota_team),
                    'stratz': bool(stratz_team)
                }
            }

            # 数据质量评估
            enhanced_team['data_quality'] = self._assess_team_data_quality(enhanced_team)

            return enhanced_team

        except Exception as e:
            logger.error(f"获取增强版战队数据失败 {team_name}: {e}")
            return None

    def _assess_team_data_quality(self, team_data: Dict) -> Dict:
        """评估战队数据质量"""
        quality = {
            'completeness': 0.0,
            'source_coverage': 0,
            'information_richness': 0.0
        }

        # 数据源覆盖率
        sources_available = sum(1 for v in team_data['data_sources'].values() if v)
        total_sources = len(team_data['data_sources'])
        quality['source_coverage'] = sources_available / total_sources

        # 信息丰富度评估
        info_richness = 0
        liquipedia_data = team_data.get('liquipedia_data', {})

        if liquipedia_data:
            # 检查关键信息字段
            key_fields = ['logo_url', 'region', 'founded_date', 'total_earnings', 'current_roster']
            available_fields = sum(1 for field in key_fields if liquipedia_data.get(field))
            info_richness = available_fields / len(key_fields)

        quality['information_richness'] = info_richness
        quality['completeness'] = (quality['source_coverage'] + quality['information_richness']) / 2

        return quality

    # ========== 比赛数据整合 ==========

    def get_enhanced_match_data(self, match_id: int) -> Optional[Dict]:
        """
        获取增强版比赛数据
        结合OpenDota和STRATZ的数据
        """
        logger.info(f"获取增强版比赛数据: {match_id}")

        try:
            # 从OpenDota获取基础数据
            opendota_match = self.opendota_service.get_match_details(match_id)
            if not opendota_match:
                logger.warning(f"OpenDota未找到比赛: {match_id}")
                return None

            # 从STRATZ获取详细分析
            stratz_match = self.stratz_service.get_match(match_id, 'detailed')

            # 整合数据
            enhanced_data = {
                'match_id': match_id,
                'opendota_data': opendota_match,
                'stratz_data': stratz_match,
                'liquipedia_data': None,  # 比赛数据主要来自API，Liquipedia作为补充
                'integration_timestamp': datetime.now().isoformat(),
                'data_sources': {
                    'opendota': bool(opendota_match),
                    'stratz': bool(stratz_match),
                    'liquipedia': False
                }
            }

            # 数据质量评估
            enhanced_data['data_quality'] = self._assess_match_data_quality(enhanced_data)

            return enhanced_data

        except Exception as e:
            logger.error(f"获取增强版比赛数据失败 {match_id}: {e}")
            return None

    def _assess_match_data_quality(self, data: Dict) -> Dict:
        """评估比赛数据质量"""
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
        if stratz_data:
            stratz_fields = ['id', 'didRadiantWin', 'durationSeconds']
            for field in stratz_fields:
                if field in stratz_data and stratz_data[field] is not None:
                    stratz_completeness += 1

        stratz_completeness_score = stratz_completeness / len(stratz_fields) if stratz_fields else 0

        # 综合完整性
        quality['completeness'] = (opendota_completeness_score + stratz_completeness_score) / 2

        # 一致性检查
        if opendota_data and stratz_data:
            opendota_winner = opendota_data.get('radiant_win')
            stratz_winner = stratz_data.get('didRadiantWin')

            if opendota_winner is not None and stratz_winner is not None:
                quality['consistency'] = opendota_winner == stratz_winner

        quality['source_reliability'] = {
            'opendota': opendota_completeness_score,
            'stratz': stratz_completeness_score
        }

        return quality

    # ========== 选手数据整合 ==========

    def get_enhanced_player_profile(self, account_id: int, player_name: str = None) -> Optional[Dict]:
        """
        获取增强版选手档案
        结合多个数据源的信息

        Args:
            account_id: Steam账户ID
            player_name: 选手名称（用于Liquipedia搜索）
        """
        logger.info(f"获取增强版选手档案: {account_id}, name: {player_name}")

        try:
            # 从OpenDota获取基础数据
            opendota_player = self.opendota_service.get_player(account_id)
            opendota_matches = self.opendota_service.get_player_matches(account_id, limit=10)

            # 从STRATZ获取补充数据
            stratz_player = self.stratz_service.get_player(account_id, 'detailed')

            # 从Liquipedia获取选手信息（如果提供了选手名称）
            liquipedia_player = None
            if player_name:
                # 这里可以扩展Liquipedia服务来支持选手搜索
                # 目前主要是战队信息，选手信息作为战队的一部分
                pass

            # 整合数据
            enhanced_profile = {
                'account_id': account_id,
                'player_name': player_name,
                'opendota_profile': opendota_player,
                'opendota_matches': opendota_matches,
                'stratz_profile': stratz_player,
                'liquipedia_profile': liquipedia_player,
                'integration_timestamp': datetime.now().isoformat(),
                'data_sources': {
                    'opendota_player': bool(opendota_player),
                    'opendota_matches': bool(opendota_matches),
                    'stratz_player': bool(stratz_player),
                    'liquipedia_player': bool(liquipedia_player)
                }
            }

            # 生成综合分析
            enhanced_profile['analysis'] = self._analyze_player_profile(enhanced_profile)

            return enhanced_profile

        except Exception as e:
            logger.error(f"获取增强版选手档案失败 {account_id}: {e}")
            return None

    def _analyze_player_profile(self, profile: Dict) -> Dict:
        """分析选手档案"""
        analysis = {
            'profile_completeness': 0.0,
            'recent_performance': {},
            'data_consistency': True,
            'play_style_indicators': {}
        }

        # 档案完整性
        total_sources = len(profile['data_sources'])
        available_sources = sum(1 for v in profile['data_sources'].values() if v)
        analysis['profile_completeness'] = available_sources / total_sources

        # 近期表现分析
        opendota_matches = profile.get('opendota_matches', [])
        if opendota_matches:
            matches = opendota_matches[:10]  # 最近10场比赛
            if matches:
                wins = sum(1 for match in matches if match.get('radiant_win') == (match.get('player_slot', 0) < 128))

                analysis['recent_performance'] = {
                    'total_matches': len(matches),
                    'wins': wins,
                    'win_rate': wins / len(matches),
                    'avg_kills': sum(match.get('kills', 0) for match in matches) / len(matches),
                    'avg_deaths': sum(match.get('deaths', 0) for match in matches) / len(matches),
                    'avg_assists': sum(match.get('assists', 0) for match in matches) / len(matches)
                }

        return analysis

    # ========== 锦标赛数据整合 ==========

    def get_tournament_data(self, tournament_name: str = None, limit: int = 20) -> Optional[Dict]:
        """
        获取锦标赛数据
        主要来源是Liquipedia，补充OpenDota的联赛信息

        Args:
            tournament_name: 具体锦标赛名称
            limit: 获取数量限制
        """
        logger.info(f"获取锦标赛数据: {tournament_name}")

        try:
            # 从Liquipedia获取锦标赛信息
            if tournament_name:
                # 获取特定锦标赛信息（需要扩展Liquipedia服务）
                liquipedia_tournament = self.liquipedia_service.get_team_info(tournament_name)  # 这里需要新方法
            else:
                # 获取锦标赛列表
                liquipedia_tournaments = self.liquipedia_service.get_tournaments(limit=limit)

            # 从OpenDota获取联赛信息作为补充
            opendota_leagues = self.opendota_service.get_leagues()

            # 整合数据
            tournament_data = {
                'tournament_name': tournament_name,
                'liquipedia_tournaments': liquipedia_tournaments if not tournament_name else [liquipedia_tournament],
                'opendota_leagues': opendota_leagues,
                'integration_timestamp': datetime.now().isoformat(),
                'data_sources': {
                    'liquipedia': True,
                    'opendota': bool(opendota_leagues),
                    'stratz': False  # STRATZ 对锦标赛支持有限
                }
            }

            return tournament_data

        except Exception as e:
            logger.error(f"获取锦标赛数据失败: {e}")
            return None

    # ========== 样本数据收集 ==========

    def fetch_and_save_combined_samples(self, sample_size: int = 10) -> Dict:
        """获取并保存整合样本数据 - 包含所有数据源"""
        logger.info("开始获取整合样本数据（包含Liquipedia）...")

        samples = {}

        # 1. 获取增强版战队数据样本
        logger.info("获取增强版战队数据样本...")

        # 重点战队列表
        priority_teams = [
            'Team Spirit', 'PSG.LGD', 'OG', 'Team Secret',
            'Evil Geniuses', 'Virtus.pro', 'T1', 'Team Liquid'
        ]

        enhanced_teams = []
        for team_name in priority_teams:
            try:
                enhanced_team = self.get_enhanced_team_data(team_name)
                if enhanced_team:
                    enhanced_teams.append(enhanced_team)
                    logger.info(f"获取增强战队数据: {team_name}")

                import time
                time.sleep(2)  # 控制请求频率

            except Exception as e:
                logger.error(f"获取战队数据失败 {team_name}: {e}")

        if enhanced_teams:
            filepath = self._save_combined_sample("enhanced_teams", enhanced_teams)
            samples['enhanced_teams'] = {
                'count': len(enhanced_teams),
                'filepath': filepath,
                'quality_summary': self._summarize_team_data_quality(enhanced_teams)
            }

        # 2. 获取增强版比赛数据样本
        logger.info("获取增强版比赛数据样本...")

        # 从OpenDota获取一些公开比赛ID
        public_matches = self.opendota_service.get_pro_matches(limit=5)
        enhanced_matches = []

        for match in public_matches:
            try:
                match_id = match.get('match_id')
                if match_id:
                    enhanced_match = self.get_enhanced_match_data(match_id)
                    if enhanced_match:
                        enhanced_matches.append(enhanced_match)
                        logger.info(f"获取增强比赛数据: {match_id}")

                    import time
                    time.sleep(2)
            except Exception as e:
                logger.error(f"获取比赛数据失败 {match_id}: {e}")

        if enhanced_matches:
            filepath = self._save_combined_sample("enhanced_matches", enhanced_matches)
            samples['enhanced_matches'] = {
                'count': len(enhanced_matches),
                'filepath': filepath,
                'quality_summary': self._summarize_match_data_quality(enhanced_matches)
            }

        # 3. 获取锦标赛数据样本
        logger.info("获取锦标赛数据样本...")

        try:
            tournament_data = self.get_tournament_data(limit=10)
            if tournament_data:
                filepath = self._save_combined_sample("tournament_data", tournament_data)
                samples['tournament_data'] = {
                    'count': len(tournament_data.get('liquipedia_tournaments', [])),
                    'filepath': filepath
                }
        except Exception as e:
            logger.error(f"获取锦标赛数据失败: {e}")

        logger.info("整合样本数据获取完成（包含所有数据源）！")
        return samples

    def _save_combined_sample(self, data_type: str, data: Any) -> str:
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

    def _summarize_team_data_quality(self, teams: List[Dict]) -> Dict:
        """汇总战队数据质量"""
        if not teams:
            return {'avg_completeness': 0, 'total_teams': 0}

        qualities = [team.get('data_quality', {}) for team in teams]
        completeness_scores = [q.get('completeness', 0) for q in qualities]

        return {
            'avg_completeness': sum(completeness_scores) / len(completeness_scores),
            'source_coverage': sum(q.get('source_coverage', 0) for q in qualities) / len(qualities),
            'total_teams': len(teams)
        }

    def _summarize_match_data_quality(self, matches: List[Dict]) -> Dict:
        """汇总比赛数据质量"""
        if not matches:
            return {'avg_completeness': 0, 'total_matches': 0}

        qualities = [match.get('data_quality', {}) for match in matches]

        return {
            'avg_completeness': sum(q.get('completeness', 0) for q in qualities) / len(qualities),
            'consistency_rate': sum(1 for q in qualities if q.get('consistency', False)) / len(qualities),
            'total_matches': len(matches)
        }

    # ========== 服务状态检查 ==========

    def check_all_services_status(self) -> Dict:
        """检查所有服务的状态"""
        logger.info("检查所有数据源服务状态...")

        status = {
            'timestamp': datetime.now().isoformat(),
            'services': {}
        }

        # 检查OpenDota服务
        try:
            opendota_heroes = self.opendota_service.get_heroes()
            status['services']['opendota'] = {
                'available': bool(opendota_heroes),
                'data_count': len(opendota_heroes) if opendota_heroes else 0,
                'status': 'online' if opendota_heroes else 'offline'
            }
        except Exception as e:
            status['services']['opendota'] = {
                'available': False,
                'error': str(e),
                'status': 'error'
            }

        # 检查STRATZ服务
        try:
            stratz_connection = self.stratz_service.test_connection()
            status['services']['stratz'] = {
                'available': stratz_connection,
                'status': 'online' if stratz_connection else 'offline'
            }
        except Exception as e:
            status['services']['stratz'] = {
                'available': False,
                'error': str(e),
                'status': 'error'
            }

        # 检查Liquipedia服务
        try:
            # 尝试获取一个知名战队信息来测试服务
            test_team = self.liquipedia_service.get_team_info("OG")
            status['services']['liquipedia'] = {
                'available': bool(test_team),
                'status': 'online' if test_team else 'offline'
            }
        except Exception as e:
            status['services']['liquipedia'] = {
                'available': False,
                'error': str(e),
                'status': 'error'
            }

        # 计算总体状态
        online_services = sum(1 for s in status['services'].values() if s.get('status') == 'online')
        total_services = len(status['services'])

        status['overall'] = {
            'online_services': online_services,
            'total_services': total_services,
            'health_score': online_services / total_services if total_services > 0 else 0,
            'status': 'healthy' if online_services == total_services else 'partial' if online_services > 0 else 'down'
        }

        return status

# 使用示例
if __name__ == "__main__":
    # 初始化整合服务
    integration_service = DataIntegrationService()

    # 检查服务状态
    print("检查所有服务状态...")
    service_status = integration_service.check_all_services_status()
    print(f"服务状态: {service_status['overall']['status']}")
    print(f"在线服务: {service_status['overall']['online_services']}/{service_status['overall']['total_services']}")

    # 获取并保存整合样本数据
    print("\n获取整合样本数据...")
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