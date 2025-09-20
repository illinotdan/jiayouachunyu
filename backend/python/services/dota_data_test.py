#!/usr/bin/env python3
"""
Dota2 数据源综合测试脚本 - 修正版
正确从配置文件读取API密钥，使用实际的服务类
"""

import os
import sys
import json
import yaml
import time
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 添加项目根目录和services目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)  # 添加backend/python目录
sys.path.insert(0, current_dir)  # 添加services目录

# 现在使用绝对导入
from opendota_service import OpenDotaService
from stratz_service import StratzService
from liquipedia_service import LiquipediaService
from data_integration_service import DataIntegrationService
from dem_parser_service import DEMParserService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DataSourceTester:
    """数据源测试器 - 改进版"""

    def __init__(self):
        self.test_results = {}
        self.data_dir = Path("test_data_output")
        self.data_dir.mkdir(exist_ok=True)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 加载配置文件
        self.config = self._load_config()

        # 从配置文件获取API密钥
        self.opendota_key = self.config.get('external_apis', {}).get('opendota', {}).get('api_key')
        self.stratz_key = self.config.get('external_apis', {}).get('stratz', {}).get('api_key')

        # 如果配置文件中没有，尝试从环境变量获取
        if not self.stratz_key:
            self.stratz_key = os.getenv('STRATZ_API_KEY')
        if not self.opendota_key:
            self.opendota_key = os.getenv('OPENDOTA_API_KEY')

        logger.info(
            f"配置加载完成 - OpenDota: {'已配置' if self.opendota_key else '未配置'}, STRATZ: {'已配置' if self.stratz_key else '未配置'}")

    def _load_config(self):
        """加载配置文件"""
        config_path = Path("config.yaml")
        if not config_path.exists():
            # 尝试其他可能的路径
            config_path = Path("../config.yaml")
            if not config_path.exists():
                config_path = Path("../../config.yaml")

        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        else:
            logger.warning("未找到配置文件，使用默认配置")
            return {}

    def save_data(self, data, filename, description=""):
        """保存数据到文件"""
        filepath = self.data_dir / f"{self.session_id}_{filename}.json"
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            logger.info(f"数据已保存: {filepath} ({description})")
            return str(filepath)
        except Exception as e:
            logger.error(f"保存数据失败: {e}")
            return None

    def test_opendota_service(self):
        """测试OpenDota服务 - 使用实际服务类"""
        logger.info("=" * 50)
        logger.info("测试OpenDota API服务")
        logger.info("=" * 50)

        try:
            # 使用实际的OpenDota服务类
            service = OpenDotaService(api_key=self.opendota_key)

            # 测试连接
            if not service.test_connection():
                logger.error("OpenDota连接测试失败")
                self.test_results['opendota'] = {'success': False, 'error': '连接测试失败'}
                return {}

            results = {}

            # 1. 获取英雄数据
            logger.info("获取英雄数据...")
            heroes = service.get_heroes()
            if heroes:
                results['heroes'] = heroes
                self.save_data(heroes, "opendota_heroes", "OpenDota英雄数据")
                logger.info(f"获取到 {len(heroes)} 个英雄")

            # 2. 获取职业比赛
            logger.info("获取职业比赛...")
            pro_matches = service.get_pro_matches(limit=20)
            if pro_matches:
                results['pro_matches'] = pro_matches
                self.save_data(pro_matches, "opendota_pro_matches", "OpenDota职业比赛")
                logger.info(f"获取到 {len(pro_matches)} 场比赛")

                # 3. 获取比赛详情
                if pro_matches:
                    match_id = pro_matches[0].get('match_id')
                    match_details = service.get_match_details(match_id)
                    if match_details:
                        results['match_details'] = match_details
                        results['sample_match_id'] = match_id
                        self.save_data(match_details, "opendota_match_details", f"比赛详情({match_id})")
                        logger.info(f"获取到比赛详情: {match_id}")

            self.test_results['opendota'] = {
                'success': True,
                'data_types': list(results.keys()),
                'sample_match_id': results.get('sample_match_id')
            }

            return results

        except Exception as e:
            logger.error(f"OpenDota测试失败: {e}")
            self.test_results['opendota'] = {'success': False, 'error': str(e)}
            return {}

    def test_stratz_service(self):
        """测试STRATZ服务 - 使用实际服务类"""
        logger.info("=" * 50)
        logger.info("测试STRATZ API服务")
        logger.info("=" * 50)

        if not self.stratz_key:
            logger.error("STRATZ API密钥未配置")
            self.test_results['stratz'] = {'success': False, 'error': 'API密钥未配置'}
            return {}

        try:
            # 使用实际的STRATZ服务类
            service = StratzService(api_key=self.stratz_key)

            # 测试连接
            if not service.test_connection():
                logger.error("STRATZ连接测试失败")
                self.test_results['stratz'] = {'success': False, 'error': '连接测试失败'}
                return {}

            results = {}

            # 1. 获取英雄数据
            logger.info("获取STRATZ英雄数据...")
            heroes = service.get_heroes('basic')
            if heroes:
                results['heroes'] = heroes
                self.save_data(heroes, "stratz_heroes", "STRATZ英雄数据")
                logger.info(f"获取到 {len(heroes)} 个英雄")

            # 2. 获取直播比赛
            logger.info("获取直播比赛...")
            live_matches = service.get_live_matches()
            if live_matches:
                results['live_matches'] = live_matches
                self.save_data(live_matches, "stratz_live_matches", "STRATZ直播比赛")
                logger.info(f"获取到 {len(live_matches)} 场直播比赛")

            self.test_results['stratz'] = {
                'success': True,
                'data_types': list(results.keys())
            }

            return results

        except Exception as e:
            logger.error(f"STRATZ测试失败: {e}")
            self.test_results['stratz'] = {'success': False, 'error': str(e)}
            return {}

    def test_liquipedia_service(self):
        """测试Liquipedia服务 - 使用实际服务类（Playwright）"""
        logger.info("=" * 50)
        logger.info("测试Liquipedia爬虫服务")
        logger.info("=" * 50)

        try:
            # 使用实际的Liquipedia服务类（包含Playwright）
            with LiquipediaService(headless=True, debug=True) as service:
                # 测试连接
                if not service.test_connection():
                    logger.error("Liquipedia连接测试失败")
                    self.test_results['liquipedia'] = {'success': False, 'error': '连接测试失败'}
                    return {}

                results = {}

                # 1. 获取战队信息
                logger.info("获取战队信息...")
                teams_to_test = ['Team Spirit', 'OG', 'Team Secret']
                teams_data = []

                for team_name in teams_to_test:
                    logger.info(f"获取战队: {team_name}")
                    team_info = service.get_team_info(team_name)
                    if team_info:
                        teams_data.append(team_info)
                    time.sleep(2)  # 礼貌爬取

                if teams_data:
                    results['teams'] = teams_data
                    self.save_data(teams_data, "liquipedia_teams", "Liquipedia战队数据")
                    logger.info(f"获取到 {len(teams_data)} 个战队信息")

                # 2. 获取锦标赛信息
                logger.info("获取锦标赛信息...")
                tournaments = service.get_tournaments(limit=10)
                if tournaments:
                    results['tournaments'] = tournaments
                    self.save_data(tournaments, "liquipedia_tournaments", "Liquipedia锦标赛")
                    logger.info(f"获取到 {len(tournaments)} 个锦标赛")

                self.test_results['liquipedia'] = {
                    'success': True,
                    'data_types': list(results.keys())
                }

                return results

        except Exception as e:
            logger.error(f"Liquipedia测试失败: {e}")
            self.test_results['liquipedia'] = {'success': False, 'error': str(e)}
            return {}

    def test_data_integration_service(self):
        """测试数据整合服务"""
        logger.info("=" * 50)
        logger.info("测试数据整合服务")
        logger.info("=" * 50)

        try:
            # 使用数据整合服务
            service = DataIntegrationService(
                opendota_key=self.opendota_key,
                stratz_key=self.stratz_key
            )

            # 检查服务状态
            status = service.check_all_services_status()
            logger.info(f"服务状态: {status['overall']['status']}")

            results = {
                'service_status': status,
                'overall_health': status['overall']['health_score']
            }

            self.save_data(status, "integration_service_status", "数据整合服务状态")

            self.test_results['integration'] = {
                'success': True,
                'health_score': status['overall']['health_score']
            }

            return results

        except Exception as e:
            logger.error(f"数据整合服务测试失败: {e}")
            self.test_results['integration'] = {'success': False, 'error': str(e)}
            return {}

    def run_comprehensive_test(self):
        """运行综合测试"""
        logger.info("开始Dota2数据源综合测试")
        logger.info(f"测试会话ID: {self.session_id}")

        start_time = time.time()
        all_results = {}

        # 1. 测试OpenDota
        all_results['opendota'] = self.test_opendota_service()
        time.sleep(2)

        # 2. 测试STRATZ
        all_results['stratz'] = self.test_stratz_service()
        time.sleep(2)

        # 3. 测试Liquipedia
        all_results['liquipedia'] = self.test_liquipedia_service()
        time.sleep(2)

        # 4. 测试数据整合服务
        all_results['integration'] = self.test_data_integration_service()

        # 生成测试报告
        execution_time = time.time() - start_time
        test_summary = {
            'session_id': self.session_id,
            'execution_time': execution_time,
            'test_results': self.test_results,
            'timestamp': datetime.now().isoformat()
        }

        self.save_data(test_summary, "test_summary", "测试摘要")

        logger.info("=" * 60)
        logger.info("测试完成!")
        logger.info(f"执行时间: {execution_time:.2f} 秒")
        logger.info(f"数据文件保存在: {self.data_dir}")
        logger.info("=" * 60)

        return test_summary


def main():
    """主测试函数"""
    tester = DataSourceTester()
    tester.run_comprehensive_test()


if __name__ == "__main__":
    main()