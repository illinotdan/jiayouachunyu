"""
DEM解析服务 - 完整流程
从OpenDota获取职业比赛match_id -> 下载DEM文件到OSS -> 使用Java工具解析 -> 输出JSON
"""

import os
import json
import asyncio
import aiohttp
import subprocess
import tempfile
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import hashlib
import time

import oss2
from flask import current_app
from aiohttp_socks import ProxyConnector

from services.opendota_service import OpenDotaService

import sys, os
# 把 backend/python 加入 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# -------------- 下面保持原样 --------------
from config.database import db
from models.match import Match, MatchAnalysis
from utils.response import ApiResponse

logger = logging.getLogger(__name__)

class DEMParserService:
    """DEM解析服务类"""
    
    def __init__(self, 
                 opendota_key: str = None,
                 oss_access_key_id: str = None,
                 oss_access_key_secret: str = None,
                 oss_endpoint: str = None,
                 oss_bucket: str = None):
        """
        初始化DEM解析服务
        
        Args:
            opendota_key: OpenDota API密钥
            oss_access_key_id: 阿里云OSS访问密钥ID
            oss_access_key_secret: 阿里云OSS访问密钥Secret
            oss_endpoint: OSS端点
            oss_bucket: OSS存储桶名称
        """
        # OpenDota服务
        self.opendota = OpenDotaService(api_key=opendota_key)
        
        # OSS配置
        self.oss_access_key_id = oss_access_key_id or current_app.config.get('ALIYUN_ACCESS_KEY_ID')
        self.oss_access_key_secret = oss_access_key_secret or current_app.config.get('ALIYUN_ACCESS_KEY_SECRET')
        self.oss_endpoint = oss_endpoint or current_app.config.get('ALIYUN_OSS_ENDPOINT')
        self.oss_bucket_name = oss_bucket or current_app.config.get('ALIYUN_OSS_BUCKET')
        
        # 初始化OSS客户端
        if all([self.oss_access_key_id, self.oss_access_key_secret, self.oss_endpoint]):
            auth = oss2.Auth(self.oss_access_key_id, self.oss_access_key_secret)
            self.oss_bucket = oss2.Bucket(auth, self.oss_endpoint, self.oss_bucket_name)
            logger.info("OSS客户端初始化成功")
        else:
            self.oss_bucket = None
            logger.warning("OSS配置不完整，将跳过OSS上传")
        
        # Java工具路径
        self.java_tool_dir = Path(__file__).parent.parent.parent / "dem2json" / "java"
        self.clarity_jar_path = self.java_tool_dir / "clarity_dem2json.jar"
        
        # 验证Java工具
        if not self.clarity_jar_path.exists():
            logger.error(f"Java解析工具不存在: {self.clarity_jar_path}")
            raise FileNotFoundError(f"Java解析工具不存在: {self.clarity_jar_path}")
        
        # 工作目录
        self.work_dir = Path(current_app.config.get('UPLOAD_FOLDER', '/tmp')) / "dem_parser"
        self.work_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"DEM解析服务初始化完成")
        logger.info(f"Java工具路径: {self.clarity_jar_path}")
        logger.info(f"工作目录: {self.work_dir}")
    
    async def get_professional_match_ids(self, 
                                       days_back: int = 7, 
                                       limit: int = 100) -> List[int]:
        """
        从OpenDota获取职业比赛的match_id列表
        
        Args:
            days_back: 获取多少天前的比赛
            limit: 最大获取数量
            
        Returns:
            List[int]: match_id列表
        """
        logger.info(f"获取最近{days_back}天的职业比赛ID，限制{limit}场")
        
        try:
            # 获取职业比赛列表
            pro_matches = self.opendota.get_pro_matches(limit=limit * 2)  # 多获取一些以便筛选
            
            if not pro_matches:
                logger.warning("未获取到职业比赛数据")
                return []
            
            # 计算时间范围
            cutoff_time = datetime.utcnow() - timedelta(days=days_back)
            cutoff_timestamp = int(cutoff_time.timestamp())
            
            # 筛选时间范围内的比赛
            filtered_matches = []
            for match in pro_matches:
                start_time = match.get('start_time', 0)
                if start_time >= cutoff_timestamp:
                    match_id = match.get('match_id')
                    if match_id:
                        filtered_matches.append(match_id)
                        
                        # 达到限制数量就停止
                        if len(filtered_matches) >= limit:
                            break
            
            logger.info(f"筛选出{len(filtered_matches)}场符合条件的职业比赛")
            return filtered_matches
            
        except Exception as e:
            logger.error(f"获取职业比赛ID失败: {e}")
            return []
    
    async def get_dem_download_url(self, match_id: int) -> Optional[str]:
        """
        获取DEM文件下载链接
        
        Args:
            match_id: 比赛ID
            
        Returns:
            Optional[str]: DEM文件下载URL，如果不存在返回None
        """
        try:
            # 从OpenDota获取比赛详情
            match_details = self.opendota.get_match_details(match_id)
            
            if not match_details:
                logger.warning(f"无法获取比赛{match_id}的详情")
                return None
            
            # 检查是否有replay_url
            replay_url = match_details.get('replay_url')
            if not replay_url:
                logger.warning(f"比赛{match_id}没有可用的replay_url")
                return None
            
            # OpenDota的replay_url通常是这种格式：
            # http://replay{cluster}.valve.net/570/{match_id}_{replay_salt}.dem.bz2
            logger.info(f"比赛{match_id}的DEM下载链接: {replay_url}")
            return replay_url
            
        except Exception as e:
            logger.error(f"获取比赛{match_id}的DEM下载链接失败: {e}")
            return None
    
    async def download_dem_file(self, match_id: int, download_url: str) -> Optional[Path]:
        """
        下载DEM文件到本地临时目录
        
        Args:
            match_id: 比赛ID
            download_url: DEM文件下载URL
            
        Returns:
            Optional[Path]: 本地DEM文件路径，失败返回None
        """
        logger.info(f"开始下载比赛{match_id}的DEM文件")
        
        try:
            # 生成本地文件路径
            dem_filename = f"match_{match_id}.dem"
            local_path = self.work_dir / dem_filename
            
            # 如果文件已存在且不为空，跳过下载
            if local_path.exists() and local_path.stat().st_size > 0:
                logger.info(f"DEM文件已存在，跳过下载: {local_path}")
                return local_path
            
            # 使用aiohttp下载文件
            timeout = aiohttp.ClientTimeout(total=1800)  # 30分钟超时
            
            # 创建代理连接器
            connector = ProxyConnector.from_url('socks5://127.0.0.1:10808')

            async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                logger.info(f"开始下载: {download_url}")
                
                async with session.get(download_url) as response:
                    if response.status != 200:
                        logger.error(f"下载失败，HTTP状态码: {response.status}")
                        return None
                    
                    # 获取文件大小
                    content_length = response.headers.get('Content-Length')
                    if content_length:
                        file_size_mb = int(content_length) / (1024 * 1024)
                        logger.info(f"文件大小: {file_size_mb:.2f} MB")
                    
                    # 写入文件
                    with open(local_path, 'wb') as f:
                        downloaded = 0
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            # 每10MB打印一次进度
                            if downloaded % (10 * 1024 * 1024) == 0:
                                progress_mb = downloaded / (1024 * 1024)
                                logger.info(f"已下载: {progress_mb:.2f} MB")
            
            # 验证文件
            if not local_path.exists() or local_path.stat().st_size == 0:
                logger.error(f"下载的文件无效: {local_path}")
                return None
            
            file_size = local_path.stat().st_size / (1024 * 1024)
            logger.info(f"DEM文件下载完成: {local_path}, 大小: {file_size:.2f} MB")
            return local_path
            
        except Exception as e:
            logger.error(f"下载DEM文件失败: {e}")
            return None
    
    async def upload_dem_to_oss(self, local_path: Path, match_id: int) -> Optional[str]:
        """
        上传DEM文件到阿里云OSS
        
        Args:
            local_path: 本地DEM文件路径
            match_id: 比赛ID
            
        Returns:
            Optional[str]: OSS对象键，失败返回None
        """
        if not self.oss_bucket:
            logger.warning("OSS未配置，跳过上传")
            return None
        
        logger.info(f"开始上传DEM文件到OSS: {local_path}")
        
        try:
            # 生成OSS对象键
            timestamp = datetime.now().strftime("%Y%m%d")
            oss_key = f"dem_files/{timestamp}/match_{match_id}.dem"
            
            # 检查文件是否已存在
            try:
                self.oss_bucket.head_object(oss_key)
                logger.info(f"文件已存在于OSS，跳过上传: {oss_key}")
                return oss_key
            except oss2.exceptions.NoSuchKey:
                pass  # 文件不存在，继续上传
            
            # 上传文件
            logger.info(f"上传到OSS: {oss_key}")
            result = self.oss_bucket.put_object_from_file(oss_key, str(local_path))
            
            if result.status == 200:
                logger.info(f"OSS上传成功: {oss_key}")
                return oss_key
            else:
                logger.error(f"OSS上传失败，状态码: {result.status}")
                return None
                
        except Exception as e:
            logger.error(f"上传DEM文件到OSS失败: {e}")
            return None
    
    def parse_dem_with_java(self, dem_file_path: Path, match_id: int) -> Optional[Dict]:
        """
        使用Java工具解析DEM文件
        
        Args:
            dem_file_path: DEM文件路径
            match_id: 比赛ID
            
        Returns:
            Optional[Dict]: 解析结果JSON，失败返回None
        """
        logger.info(f"开始使用Java工具解析DEM文件: {dem_file_path}")
        
        try:
            # 生成输出文件路径
            output_filename = f"match_{match_id}_parsed.json"
            output_path = self.work_dir / output_filename
            
            # 构建Java命令
            java_cmd = [
                "java", 
                "-jar", 
                str(self.clarity_jar_path),
                str(dem_file_path)
            ]
            
            logger.info(f"执行Java命令: {' '.join(java_cmd)}")
            
            # 执行Java命令
            start_time = time.time()
            result = subprocess.run(
                java_cmd,
                capture_output=True,
                text=True,
                timeout=3600,  # 1小时超时
                cwd=str(self.work_dir)
            )
            
            execution_time = time.time() - start_time
            logger.info(f"Java解析完成，耗时: {execution_time:.2f}秒")
            
            # 检查执行结果
            if result.returncode != 0:
                logger.error(f"Java解析失败，返回码: {result.returncode}")
                logger.error(f"错误输出: {result.stderr}")
                return None
            
            # 查找输出的JSON文件
            # clarity工具可能会生成不同名称的输出文件，我们需要查找
            json_files = list(self.work_dir.glob("*.json"))
            
            # 找到最新的JSON文件
            if not json_files:
                logger.error("未找到Java工具生成的JSON文件")
                return None
            
            # 按修改时间排序，取最新的
            latest_json = max(json_files, key=lambda p: p.stat().st_mtime)
            logger.info(f"找到解析结果文件: {latest_json}")
            
            # 读取JSON结果
            with open(latest_json, 'r', encoding='utf-8') as f:
                parsed_data = json.load(f)
            
            # 添加元数据
            parsed_data['_metadata'] = {
                'match_id': match_id,
                'parsed_at': datetime.utcnow().isoformat(),
                'execution_time': execution_time,
                'dem_file_path': str(dem_file_path),
                'parser_version': 'clarity_dem2json'
            }
            
            # 保存带元数据的结果
            final_output_path = self.work_dir / f"match_{match_id}_final.json"
            with open(final_output_path, 'w', encoding='utf-8') as f:
                json.dump(parsed_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"DEM解析成功，结果已保存: {final_output_path}")
            return parsed_data
            
        except subprocess.TimeoutExpired:
            logger.error(f"Java解析超时: {dem_file_path}")
            return None
        except Exception as e:
            logger.error(f"Java解析DEM文件失败: {e}")
            return None
    
    async def process_single_match(self, match_id: int) -> Dict:
        """
        处理单场比赛的完整流程
        
        Args:
            match_id: 比赛ID
            
        Returns:
            Dict: 处理结果
        """
        result = {
            'match_id': match_id,
            'success': False,
            'steps': {},
            'errors': [],
            'start_time': datetime.utcnow().isoformat()
        }
        
        try:
            logger.info(f"开始处理比赛{match_id}的DEM解析流程")
            
            # 步骤1: 获取DEM下载链接
            logger.info(f"步骤1: 获取比赛{match_id}的DEM下载链接")
            download_url = await self.get_dem_download_url(match_id)
            result['steps']['get_download_url'] = download_url is not None
            
            if not download_url:
                result['errors'].append("无法获取DEM下载链接")
                return result
            
            # 步骤2: 下载DEM文件
            logger.info(f"步骤2: 下载DEM文件")
            local_dem_path = await self.download_dem_file(match_id, download_url)
            result['steps']['download_dem'] = local_dem_path is not None
            
            if not local_dem_path:
                result['errors'].append("DEM文件下载失败")
                return result
            
            # 步骤3: 上传到OSS（可选）
            logger.info(f"步骤3: 上传DEM文件到OSS")
            oss_key = await self.upload_dem_to_oss(local_dem_path, match_id)
            result['steps']['upload_to_oss'] = oss_key is not None
            result['oss_key'] = oss_key
            
            # 步骤4: 使用Java工具解析
            logger.info(f"步骤4: 使用Java工具解析DEM文件")
            parsed_data = self.parse_dem_with_java(local_dem_path, match_id)
            result['steps']['parse_with_java'] = parsed_data is not None
            
            if not parsed_data:
                result['errors'].append("Java解析失败")
                return result
            
            # 步骤5: 保存解析结果到数据库
            logger.info(f"步骤5: 保存解析结果到数据库")
            saved = await self.save_parsed_data_to_db(match_id, parsed_data)
            result['steps']['save_to_db'] = saved
            
            # 清理临时文件
            try:
                if local_dem_path.exists():
                    local_dem_path.unlink()
                    logger.info(f"清理临时DEM文件: {local_dem_path}")
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")
            
            result['success'] = True
            result['end_time'] = datetime.utcnow().isoformat()
            logger.info(f"比赛{match_id}的DEM解析流程完成")
            
        except Exception as e:
            logger.error(f"处理比赛{match_id}失败: {e}")
            result['errors'].append(str(e))
        
        return result
    
    async def save_parsed_data_to_db(self, match_id: int, parsed_data: Dict) -> bool:
        """
        保存解析结果到数据库
        
        Args:
            match_id: 比赛ID
            parsed_data: 解析的JSON数据
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 查找或创建比赛记录
            match = Match.query.filter_by(match_id=match_id).first()
            if not match:
                logger.warning(f"比赛{match_id}不存在于数据库中，创建新记录")
                match = Match(match_id=match_id)
                db.session.add(match)
            
            # 查找或创建分析记录
            analysis = MatchAnalysis.query.filter_by(match_id=match_id).first()
            if not analysis:
                analysis = MatchAnalysis(match_id=match_id)
                db.session.add(analysis)
            
            # 更新分析数据
            analysis.dem_data = parsed_data
            analysis.dem_parsed_at = datetime.utcnow()
            analysis.data_sources = analysis.data_sources or {}
            analysis.data_sources['dem'] = True
            analysis.updated_at = datetime.utcnow()
            
            db.session.commit()
            logger.info(f"比赛{match_id}的DEM解析结果已保存到数据库")
            return True
            
        except Exception as e:
            logger.error(f"保存解析结果到数据库失败: {e}")
            db.session.rollback()
            return False
    
    async def batch_process_matches(self, 
                                  match_ids: List[int], 
                                  max_concurrent: int = 3) -> Dict:
        """
        批量处理多场比赛
        
        Args:
            match_ids: 比赛ID列表
            max_concurrent: 最大并发数
            
        Returns:
            Dict: 批量处理结果
        """
        logger.info(f"开始批量处理{len(match_ids)}场比赛的DEM解析")
        
        batch_result = {
            'total_matches': len(match_ids),
            'successful': 0,
            'failed': 0,
            'results': [],
            'start_time': datetime.utcnow().isoformat()
        }
        
        # 使用信号量控制并发数
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_semaphore(match_id: int):
            async with semaphore:
                return await self.process_single_match(match_id)
        
        # 并发处理所有比赛
        tasks = [process_with_semaphore(match_id) for match_id in match_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 统计结果
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"处理比赛{match_ids[i]}时发生异常: {result}")
                batch_result['failed'] += 1
                batch_result['results'].append({
                    'match_id': match_ids[i],
                    'success': False,
                    'error': str(result)
                })
            else:
                batch_result['results'].append(result)
                if result['success']:
                    batch_result['successful'] += 1
                else:
                    batch_result['failed'] += 1
        
        batch_result['end_time'] = datetime.utcnow().isoformat()
        
        logger.info(f"批量处理完成: 成功{batch_result['successful']}场，失败{batch_result['failed']}场")
        return batch_result
    
    async def start_dem_parsing_workflow(self, 
                                       days_back: int = 7, 
                                       limit: int = 50,
                                       max_concurrent: int = 3) -> Dict:
        """
        启动完整的DEM解析工作流程
        
        Args:
            days_back: 获取多少天前的比赛
            limit: 最大处理数量
            max_concurrent: 最大并发数
            
        Returns:
            Dict: 工作流程结果
        """
        logger.info("启动DEM解析工作流程")
        
        workflow_result = {
            'success': False,
            'workflow_steps': {},
            'start_time': datetime.utcnow().isoformat()
        }
        
        try:
            # 步骤1: 获取职业比赛ID
            logger.info("步骤1: 获取职业比赛ID列表")
            match_ids = await self.get_professional_match_ids(days_back, limit)
            workflow_result['workflow_steps']['get_match_ids'] = len(match_ids) > 0
            workflow_result['match_ids_count'] = len(match_ids)
            
            if not match_ids:
                workflow_result['error'] = "未获取到职业比赛ID"
                return workflow_result
            
            # 步骤2: 批量处理比赛
            logger.info("步骤2: 批量处理比赛DEM解析")
            batch_result = await self.batch_process_matches(match_ids, max_concurrent)
            workflow_result['workflow_steps']['batch_process'] = batch_result['successful'] > 0
            workflow_result['batch_result'] = batch_result
            
            workflow_result['success'] = batch_result['successful'] > 0
            workflow_result['end_time'] = datetime.utcnow().isoformat()
            
            logger.info(f"DEM解析工作流程完成，成功处理{batch_result['successful']}场比赛")
            
        except Exception as e:
            logger.error(f"DEM解析工作流程失败: {e}")
            workflow_result['error'] = str(e)
        
        return workflow_result

# 使用示例
if __name__ == "__main__":
    async def main():
        # 初始化服务
        parser = DEMParserService()
        
        # 启动完整工作流程
        result = await parser.start_dem_parsing_workflow(
            days_back=3,
            limit=10,
            max_concurrent=2
        )
        
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    asyncio.run(main())
