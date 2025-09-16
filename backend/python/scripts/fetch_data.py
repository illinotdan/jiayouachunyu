#!/usr/bin/env python
"""
数据获取脚本
用于获取OpenDota和STRATZ API的样本数据
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.opendota_service import OpenDotaService
from services.stratz_service import StratzService
from services.data_integration_service import DataIntegrationService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_directories():
    """创建必要的目录"""
    directories = [
        "data/samples",
        "data/combined_samples",
        "data/raw/opendota",
        "data/raw/stratz",
        "logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"创建目录: {directory}")

def fetch_opendota_samples(api_key=None, sample_size=10):
    """获取OpenDota样本数据"""
    logger.info("=== 开始获取OpenDota样本数据 ===")
    
    service = OpenDotaService(api_key=api_key)
    
    # 获取各种样本数据
    samples = service.fetch_and_save_samples(sample_size=sample_size)
    
    logger.info("=== OpenDota样本数据获取完成 ===")
    return samples

def fetch_stratz_samples(api_key=None, sample_size=10):
    """获取STRATZ样本数据"""
    logger.info("=== 开始获取STRATZ样本数据 ===")
    
    service = StratzService(api_key=api_key)
    
    # 获取各种样本数据
    samples = service.fetch_and_save_samples(sample_size=sample_size)
    
    logger.info("=== STRATZ样本数据获取完成 ===")
    return samples

def fetch_combined_samples(opendota_key=None, stratz_key=None, sample_size=5):
    """获取整合样本数据"""
    logger.info("=== 开始获取整合样本数据 ===")
    
    service = DataIntegrationService(
        opendota_key=opendota_key,
        stratz_key=stratz_key
    )
    
    # 获取整合样本数据
    samples = service.fetch_and_save_combined_samples(sample_size=sample_size)
    
    logger.info("=== 整合样本数据获取完成 ===")
    return samples

def analyze_sample_data(samples_dir="data/samples"):
    """分析样本数据"""
    logger.info("=== 开始分析样本数据 ===")
    
    sample_stats = {}
    
    # 遍历样本目录
    for filename in os.listdir(samples_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(samples_dir, filename)
            
            try:
                import json
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 基本统计
                stats = {
                    'file_size': os.path.getsize(filepath),
                    'record_count': len(data) if isinstance(data, list) else 1,
                    'data_structure': type(data).__name__
                }
                
                sample_stats[filename] = stats
                logger.info(f"分析文件: {filename} - {stats['record_count']} 条记录")
                
            except Exception as e:
                logger.error(f"分析文件失败 {filename}: {e}")
    
    # 保存分析结果
    analysis_file = os.path.join("data", "sample_analysis.json")
    try:
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(sample_stats, f, ensure_ascii=False, indent=2)
        logger.info(f"分析结果已保存: {analysis_file}")
    except Exception as e:
        logger.error(f"保存分析结果失败: {e}")
    
    return sample_stats

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Dota2数据获取脚本")
    parser.add_argument("--opendota-key", help="OpenDota API密钥")
    parser.add_argument("--stratz-key", help="STRATZ API密钥")
    parser.add_argument("--sample-size", type=int, default=10, help="样本大小")
    parser.add_argument("--only-opendota", action="store_true", help="仅获取OpenDota数据")
    parser.add_argument("--only-stratz", action="store_true", help="仅获取STRATZ数据")
    parser.add_argument("--only-combined", action="store_true", help="仅获取整合数据")
    parser.add_argument("--analyze-only", action="store_true", help="仅分析现有数据")
    
    args = parser.parse_args()
    
    # 创建目录
    setup_directories()
    
    # 如果仅分析现有数据
    if args.analyze_only:
        analyze_sample_data()
        return
    
    # 获取数据
    if args.only_opendota:
        fetch_opendota_samples(api_key=args.opendota_key, sample_size=args.sample_size)
    elif args.only_stratz:
        fetch_stratz_samples(api_key=args.stratz_key, sample_size=args.sample_size)
    elif args.only_combined:
        fetch_combined_samples(
            opendota_key=args.opendota_key,
            stratz_key=args.stratz_key,
            sample_size=args.sample_size
        )
    else:
        # 获取所有数据
        logger.info("=== 开始完整数据获取流程 ===")
        
        # 1. 获取OpenDota数据
        opendota_samples = fetch_opendota_samples(
            api_key=args.opendota_key,
            sample_size=args.sample_size
        )
        
        # 2. 获取STRATZ数据
        stratz_samples = fetch_stratz_samples(
            api_key=args.stratz_key,
            sample_size=args.sample_size
        )
        
        # 3. 获取整合数据
        combined_samples = fetch_combined_samples(
            opendota_key=args.opendota_key,
            stratz_key=args.stratz_key,
            sample_size=min(5, args.sample_size // 2)
        )
        
        # 4. 分析数据
        sample_stats = analyze_sample_data()
        
        # 5. 生成报告
        report = {
            'timestamp': datetime.now().isoformat(),
            'opendota_samples': len(opendota_samples) if opendota_samples else 0,
            'stratz_samples': len(stratz_samples) if stratz_samples else 0,
            'combined_samples': len(combined_samples) if combined_samples else 0,
            'sample_stats': sample_stats,
            'total_files': len(sample_stats)
        }
        
        report_file = os.path.join("data", "data_collection_report.json")
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            logger.info(f"数据获取报告已保存: {report_file}")
        except Exception as e:
            logger.error(f"保存报告失败: {e}")
        
        logger.info("=== 完整数据获取流程完成 ===")
        logger.info(f"总共获取了 {len(sample_stats)} 个样本文件")

if __name__ == "__main__":
    from datetime import datetime
    main()