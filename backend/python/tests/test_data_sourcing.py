import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from unittest.mock import patch


project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from ..services.opendota_service import OpenDotaService
from ..services.stratz_service import StratzService
from ..services.liquipedia_service import LiquipediaService
from ..services.dem_parser_service import DEMParserService

# --- 配置 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("test_data_sourcing")

# Stratz API密钥 (从stratz_service.py示例中获取的公共测试密钥)
STRATZ_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJTdWJqZWN0IjoiYzM1OGY4N2YtYjI3Ny00MTZiLTliOTQtNjQxNDUyZmVhZTdlIiwiU3RlYW1JZCI6IjE2NDgzNDU1NyIsIkFQSVVzZXIiOiJ0cnVlIiwibmJmIjoxNzU3OTk4MjE0LCJleHAiOjE3ODk1MzQyMTQsImlhdCI6MTc1Nzk5ODIxNCwiaXNzIjoiaHR0cHM6Ly9hcGkuc3RyYXR6LmNvbSJ9.r_3s8lSC3uXd7v0LhnP2cvYRByQf56EtUONikFS_x_4"

# 输出目录
OUTPUT_DIR = Path(__file__).resolve().parent / "test_data_output"


# --- 辅助函数和类 ---

def save_json(data: dict, filename: str):
    """将字典保存为JSON文件"""
    OUTPUT_DIR.mkdir(exist_ok=True)
    filepath = OUTPUT_DIR / filename
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.info(f"✅ 数据成功保存到: {filepath}")
    except Exception as e:
        logger.error(f"❌ 保存文件 {filepath} 失败: {e}")

class MockFlaskApp:
    """一个模拟的Flask App对象，用于提供DEM解析服务所需的配置"""
    def __init__(self, upload_dir):
        self.config = {
            'UPLOAD_FOLDER': str(upload_dir),
            'ALIYUN_ACCESS_KEY_ID': os.getenv('ALIYUN_ACCESS_KEY_ID'),
            'ALIYUN_ACCESS_KEY_SECRET': os.getenv('ALIYUN_ACCESS_KEY_SECRET'),
            'ALIYUN_OSS_ENDPOINT': os.getenv('ALIYUN_OSS_ENDPOINT'),
            'ALIYUN_OSS_BUCKET': os.getenv('ALIYUN_OSS_BUCKET'),
        }

async def main():
    """主执行函数"""
    logger.info("======= 开始数据源获取测试 =======")
    OUTPUT_DIR.mkdir(exist_ok=True)

    # --- 1. OpenDota 数据获取 ---
    logger.info("\n--- 步骤 1: 从 OpenDota 获取比赛数据 ---")
    opendota_service = OpenDotaService()
    pro_matches = opendota_service.get_pro_matches(limit=10)
    
    if not pro_matches:
        logger.error("❌ 从OpenDota获取职业比赛列表失败。脚本终止。")
        return

    target_match = pro_matches[0]
    match_id = target_match['match_id']
    logger.info(f"🎯 选定目标比赛 ID: {match_id}")

    opendota_match_details = opendota_service.get_match_details(match_id)
    if opendota_match_details:
        save_json(opendota_match_details, f"opendota_match_{match_id}.json")
    else:
        logger.error(f"❌ 获取 OpenDota 比赛 {match_id} 详情失败。")
        return

    # --- 2. Stratz 数据获取 ---
    logger.info("\n--- 步骤 2: 从 Stratz 获取比赛数据 ---")
    stratz_service = StratzService(api_key=STRATZ_API_KEY)
    stratz_match_details = stratz_service.get_match_detailed(match_id)
    if stratz_match_details:
        save_json(stratz_match_details, f"stratz_match_{match_id}.json")
    else:
        logger.warning(f"⚠️ 从 Stratz 获取比赛 {match_id} 详情失败。")

    # --- 3. Liquipedia 数据获取 ---
    logger.info("\n--- 步骤 3: 从 Liquipedia 获取战队数据 ---")
    radiant_team_name = opendota_match_details.get('radiant_team', {}).get('name')
    dire_team_name = opendota_match_details.get('dire_team', {}).get('name')

    if not radiant_team_name or not dire_team_name:
        logger.warning("⚠️ OpenDota数据中缺少战队名称，跳过Liquipedia查询。")
    else:
        logger.info(f"查询战队: '{radiant_team_name}' vs '{dire_team_name}'")
        # Liquipedia 服务是同步的，在异步函数中我们使用 to_thread 来运行它
        # 这是一个耗时操作，因为它需要启动一个浏览器
        def get_team_data_sync(team_name):
            with LiquipediaService(headless=True) as service:
                return service.get_team_info(team_name)

        try:
            loop = asyncio.get_running_loop()
            logger.info("正在获取天辉战队数据...")
            radiant_team_info = await loop.run_in_executor(None, get_team_data_sync, radiant_team_name)
            if radiant_team_info:
                save_json(radiant_team_info, f"liquipedia_team_{radiant_team_name.replace(' ', '_')}.json")
            else:
                logger.warning(f"⚠️ 未能从 Liquipedia 获取 '{radiant_team_name}' 的信息。")
            
            logger.info("正在获取夜魇战队数据...")
            dire_team_info = await loop.run_in_executor(None, get_team_data_sync, dire_team_name)
            if dire_team_info:
                save_json(dire_team_info, f"liquipedia_team_{dire_team_name.replace(' ', '_')}.json")
            else:
                logger.warning(f"⚠️ 未能从 Liquipedia 获取 '{dire_team_name}' 的信息。")
        except Exception as e:
            logger.error(f"❌ 在获取Liquipedia数据时发生错误: {e}")


    # --- 4. DEM 文件下载和解析 ---
    logger.info("\n--- 步骤 4: 下载并解析 DEM 录像文件 ---")
    
    # DEMParserService 依赖 Flask 的 current_app，我们需要模拟它
    mock_app = MockFlaskApp(OUTPUT_DIR)
    
    # 使用 patch 来在 DEMParserService 的上下文中模拟 current_app
    try:
        with patch('services.dem_parser_service.current_app', mock_app):
            dem_service = DEMParserService()
            
            # process_single_match 是一个异步方法
            # 它会处理下载、(可选的OSS上传)、和Java解析的全过程
            result = await dem_service.process_single_match(match_id)

            if result.get('success'):
                logger.info(f"✅ DEM 文件处理成功 for match {match_id}.")
                # 解析后的文件保存在 'UPLOAD_FOLDER' / dem_parser / match_{match_id}_final.json
                # 我们将它复制到我们的主输出目录
                parsed_json_path = Path(dem_service.work_dir) / f"match_{match_id}_final.json"
                if parsed_json_path.exists():
                    with open(parsed_json_path, 'r', encoding='utf-8') as f:
                        dem_data = json.load(f)
                    save_json(dem_data, f"dem_parsed_{match_id}.json")
                else:
                    logger.warning(f"⚠️ 解析成功但未找到最终的JSON文件: {parsed_json_path}")
            else:
                logger.error(f"❌ DEM 文件处理失败 for match {match_id}. 错误: {result.get('errors')}")

    except FileNotFoundError as e:
        logger.error(f"❌ DEM解析失败：找不到必要文件。请检查dem2json/java/clarity_dem2json.jar是否存在。")
        logger.error(f"详细错误: {e}")
    except Exception as e:
        logger.error(f"❌ 在处理DEM文件时发生未知错误: {e}")

    logger.info("\n======= 数据源获取测试完成 =======")
    logger.info(f"所有输出文件都保存在: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    # 确保 Playwright 的浏览器驱动已安装
    # 在第一次运行时，这可能会花费一些时间
    logger.info("正在检查并安装浏览器驱动 (如果需要)...")
    try:
        import subprocess
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True, capture_output=True)
        logger.info("浏览器驱动检查完毕。")
    except Exception as e:
        logger.error("安装 Playwright 浏览器驱动失败。请手动运行 'playwright install chromium'")
        logger.error(f"错误: {e.stderr.decode() if hasattr(e, 'stderr') else e}")

    asyncio.run(main())
