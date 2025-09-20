#!/usr/bin/env python3
"""
DEM解析功能演示脚本
展示完整的DEM解析流程：OpenDota获取比赛ID -> 下载DEM -> 解析为JSON
"""

import os
import sys
import asyncio
import json
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ..services.dem_parser_service import DEMParserService
from ..services.opendota_service import OpenDotaService

def print_banner():
    """打印横幅"""
    print("=" * 80)
    print("🎮 Dota2 DEM解析功能演示")
    print("=" * 80)
    print("功能流程：")
    print("1. 从OpenDota API获取职业比赛match_id列表")
    print("2. 下载DEM文件到本地/OSS")
    print("3. 使用Java clarity工具解析DEM文件为JSON")
    print("4. 保存解析结果到数据库")
    print("=" * 80)
    print()

async def demo_get_professional_matches():
    """演示获取职业比赛ID"""
    print("📋 步骤1: 获取职业比赛ID列表")
    print("-" * 40)
    
    try:
        # 初始化OpenDota服务
        opendota = OpenDotaService()
        
        # 获取最近的职业比赛
        print("正在从OpenDota获取职业比赛数据...")
        pro_matches = opendota.get_pro_matches(limit=20)
        
        if not pro_matches:
            print("❌ 未获取到职业比赛数据")
            return []
        
        print(f"✅ 成功获取到 {len(pro_matches)} 场职业比赛")
        
        # 显示前5场比赛信息
        print("\n📊 最近5场职业比赛:")
        for i, match in enumerate(pro_matches[:5]):
            match_id = match.get('match_id')
            league_name = match.get('league_name', '未知联赛')
            radiant_team = match.get('radiant_team_name', '未知队伍')
            dire_team = match.get('dire_team_name', '未知队伍')
            duration = match.get('duration', 0)
            duration_min = duration // 60
            
            print(f"  {i+1}. 比赛ID: {match_id}")
            print(f"     联赛: {league_name}")
            print(f"     对阵: {radiant_team} vs {dire_team}")
            print(f"     时长: {duration_min}分钟")
            print()
        
        # 返回match_id列表
        match_ids = [match.get('match_id') for match in pro_matches[:10] if match.get('match_id')]
        return match_ids
        
    except Exception as e:
        print(f"❌ 获取职业比赛失败: {e}")
        return []

async def demo_dem_download_and_parse(match_ids):
    """演示DEM下载和解析"""
    if not match_ids:
        print("⚠️  没有可用的比赛ID，跳过DEM解析演示")
        return
    
    print("📥 步骤2: DEM文件下载和解析")
    print("-" * 40)
    
    try:
        # 初始化DEM解析服务
        parser = DEMParserService()
        
        # 检查服务状态
        print("🔧 检查DEM解析服务状态...")
        print(f"Java工具路径: {parser.clarity_jar_path}")
        print(f"Java工具存在: {'✅' if parser.clarity_jar_path.exists() else '❌'}")
        print(f"工作目录: {parser.work_dir}")
        print(f"OSS配置: {'✅' if parser.oss_bucket else '❌'}")
        
        if not parser.clarity_jar_path.exists():
            print("❌ Java解析工具不存在，无法继续演示")
            print(f"请确保文件存在: {parser.clarity_jar_path}")
            return
        
        # 选择第一场比赛进行演示
        demo_match_id = match_ids[0]
        print(f"\n🎯 选择比赛 {demo_match_id} 进行DEM解析演示")
        
        # 步骤1: 获取DEM下载链接
        print("\n1️⃣ 获取DEM下载链接...")
        download_url = await parser.get_dem_download_url(demo_match_id)
        
        if not download_url:
            print(f"❌ 比赛 {demo_match_id} 没有可用的DEM下载链接")
            print("💡 提示: 只有部分职业比赛提供DEM文件下载")
            return
        
        print(f"✅ 获取到DEM下载链接")
        print(f"   URL: {download_url}")
        
        # 步骤2: 下载DEM文件（演示模式，不实际下载大文件）
        print(f"\n2️⃣ 下载DEM文件（演示模式）...")
        print(f"   正常情况下会下载: {download_url}")
        print(f"   文件大小通常: 50-200MB")
        print(f"   保存位置: {parser.work_dir}/match_{demo_match_id}.dem")
        print("   ⏳ 实际下载可能需要5-15分钟...")
        
        # 在实际环境中取消注释以下行来真正下载和解析
        # local_dem_path = await parser.download_dem_file(demo_match_id, download_url)
        # if local_dem_path:
        #     print(f"✅ DEM文件下载完成: {local_dem_path}")
        #     
        #     # 步骤3: 解析DEM文件
        #     print(f"\n3️⃣ 解析DEM文件为JSON...")
        #     parsed_data = parser.parse_dem_with_java(local_dem_path, demo_match_id)
        #     
        #     if parsed_data:
        #         print(f"✅ DEM解析完成")
        #         print(f"   解析结果包含 {len(parsed_data)} 个数据字段")
        #         print(f"   主要数据: 选手表现、技能释放、物品使用、移动轨迹等")
        #     else:
        #         print(f"❌ DEM解析失败")
        
        print("\n💡 演示说明:")
        print("   - 实际使用时会下载完整的DEM文件")
        print("   - Java工具会解析出详细的游戏数据")
        print("   - 解析结果保存为JSON格式")
        print("   - 数据可用于深度分析和AI训练")
        
    except Exception as e:
        print(f"❌ DEM解析演示失败: {e}")

async def demo_batch_processing(match_ids):
    """演示批量处理"""
    if len(match_ids) < 2:
        print("⚠️  比赛数量不足，跳过批量处理演示")
        return
    
    print("🔄 步骤3: 批量处理演示")
    print("-" * 40)
    
    try:
        parser = DEMParserService()
        
        # 选择前3场比赛进行批量处理演示
        batch_match_ids = match_ids[:3]
        print(f"📝 批量处理比赛ID: {batch_match_ids}")
        
        # 演示批量处理的配置
        print("\n⚙️  批量处理配置:")
        print(f"   并发数: 2 (避免服务器过载)")
        print(f"   重试次数: 3")
        print(f"   超时时间: 30分钟/文件")
        
        # 在实际环境中取消注释以下行来真正执行批量处理
        # print(f"\n🚀 开始批量处理...")
        # batch_result = await parser.batch_process_matches(batch_match_ids, max_concurrent=2)
        # 
        # print(f"✅ 批量处理完成:")
        # print(f"   总计: {batch_result['total_matches']} 场")
        # print(f"   成功: {batch_result['successful']} 场")
        # print(f"   失败: {batch_result['failed']} 场")
        
        print("\n💡 批量处理说明:")
        print("   - 支持并发处理多场比赛")
        print("   - 自动重试失败的任务")
        print("   - 实时进度跟踪")
        print("   - 错误日志记录")
        
    except Exception as e:
        print(f"❌ 批量处理演示失败: {e}")

async def demo_workflow():
    """演示完整工作流程"""
    print("🔄 步骤4: 完整工作流程演示")
    print("-" * 40)
    
    try:
        parser = DEMParserService()
        
        print("⚙️  工作流程配置:")
        print("   获取时间范围: 最近3天")
        print("   最大处理数量: 10场比赛")
        print("   并发数: 2")
        
        # 在实际环境中取消注释以下行来真正执行工作流程
        # print(f"\n🚀 启动完整工作流程...")
        # workflow_result = await parser.start_dem_parsing_workflow(
        #     days_back=3,
        #     limit=10,
        #     max_concurrent=2
        # )
        # 
        # if workflow_result['success']:
        #     batch_result = workflow_result.get('batch_result', {})
        #     print(f"✅ 工作流程执行成功:")
        #     print(f"   获取比赛: {workflow_result['match_ids_count']} 场")
        #     print(f"   处理成功: {batch_result.get('successful', 0)} 场")
        #     print(f"   处理失败: {batch_result.get('failed', 0)} 场")
        # else:
        #     print(f"❌ 工作流程执行失败: {workflow_result.get('error', 'Unknown error')}")
        
        print("\n💡 完整工作流程说明:")
        print("   - 自动获取最新职业比赛")
        print("   - 批量下载和解析DEM文件")
        print("   - 上传到OSS云存储")
        print("   - 保存结果到数据库")
        print("   - 支持定时任务调度")
        
    except Exception as e:
        print(f"❌ 完整工作流程演示失败: {e}")

def demo_api_usage():
    """演示API使用方法"""
    print("🌐 步骤5: API使用演示")
    print("-" * 40)
    
    print("📋 可用的API端点:")
    print()
    
    api_examples = [
        {
            "name": "启动完整工作流程",
            "method": "POST",
            "url": "/api/dem/start-workflow",
            "body": {
                "days_back": 7,
                "limit": 50,
                "max_concurrent": 3
            },
            "description": "自动获取并处理最近的职业比赛DEM文件"
        },
        {
            "name": "处理单场比赛",
            "method": "POST", 
            "url": "/api/dem/process-match/123456",
            "body": {},
            "description": "处理指定比赛ID的DEM解析"
        },
        {
            "name": "批量处理比赛",
            "method": "POST",
            "url": "/api/dem/batch-process",
            "body": {
                "match_ids": [123456, 123457, 123458],
                "max_concurrent": 3
            },
            "description": "批量处理多场比赛的DEM解析"
        },
        {
            "name": "获取职业比赛ID",
            "method": "GET",
            "url": "/api/dem/get-pro-matches?days_back=7&limit=100",
            "body": {},
            "description": "获取最近的职业比赛ID列表"
        },
        {
            "name": "检查服务状态",
            "method": "GET",
            "url": "/api/dem/status",
            "body": {},
            "description": "检查DEM解析服务的运行状态"
        }
    ]
    
    for i, api in enumerate(api_examples, 1):
        print(f"{i}. {api['name']}")
        print(f"   {api['method']} {api['url']}")
        if api['body']:
            print(f"   请求体: {json.dumps(api['body'], indent=6)}")
        print(f"   说明: {api['description']}")
        print()
    
    print("💡 使用提示:")
    print("   - 所有API都需要JWT认证")
    print("   - 管理员和分析师角色可以执行解析任务")
    print("   - 支持异步任务，可通过任务ID查询进度")
    print("   - 建议在低峰时段执行大批量处理")

def demo_configuration():
    """演示配置说明"""
    print("⚙️  步骤6: 配置说明")
    print("-" * 40)
    
    print("📋 必需的环境变量:")
    required_env = [
        ("OPENDOTA_API_KEY", "OpenDota API密钥（可选，提高请求限制）"),
        ("ALIYUN_ACCESS_KEY_ID", "阿里云OSS访问密钥ID"),
        ("ALIYUN_ACCESS_KEY_SECRET", "阿里云OSS访问密钥Secret"),
        ("ALIYUN_OSS_ENDPOINT", "阿里云OSS端点地址"),
        ("ALIYUN_OSS_BUCKET", "阿里云OSS存储桶名称")
    ]
    
    for env_var, description in required_env:
        current_value = os.getenv(env_var)
        status = "✅ 已配置" if current_value else "❌ 未配置"
        print(f"   {env_var}: {status}")
        print(f"     说明: {description}")
        if current_value:
            # 只显示前几个字符，保护敏感信息
            masked_value = current_value[:8] + "..." if len(current_value) > 8 else current_value
            print(f"     当前值: {masked_value}")
        print()
    
    print("🔧 Java环境要求:")
    print("   - Java 8 或更高版本")
    print("   - clarity_dem2json.jar 工具")
    print("   - 足够的内存空间（建议4GB+）")
    print()
    
    print("💾 存储要求:")
    print("   - 临时存储: 每个DEM文件50-200MB")
    print("   - OSS存储: 用于长期保存DEM和JSON文件")
    print("   - 数据库: 存储解析结果的元数据")

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="DEM解析功能演示")
    parser.add_argument("--skip-download", action="store_true", 
                       help="跳过实际下载演示（默认行为）")
    parser.add_argument("--real-demo", action="store_true",
                       help="执行真实的DEM下载和解析（需要较长时间）")
    
    args = parser.parse_args()
    
    print_banner()
    
    # 步骤1: 获取职业比赛ID
    match_ids = await demo_get_professional_matches()
    
    if match_ids:
        # 步骤2: DEM下载和解析演示
        await demo_dem_download_and_parse(match_ids)
        
        # 步骤3: 批量处理演示
        await demo_batch_processing(match_ids)
        
        # 步骤4: 完整工作流程演示
        await demo_workflow()
    
    # 步骤5: API使用演示
    demo_api_usage()
    
    # 步骤6: 配置说明
    demo_configuration()
    
    print("=" * 80)
    print("🎉 DEM解析功能演示完成！")
    print("=" * 80)
    print()
    print("📝 后续步骤:")
    print("1. 配置必要的环境变量（OSS、API密钥等）")
    print("2. 确保Java环境和clarity工具可用")
    print("3. 通过API或脚本启动DEM解析任务")
    print("4. 监控解析进度和结果")
    print("5. 使用解析后的数据进行分析或AI训练")
    print()
    
    if not args.real_demo:
        print("💡 提示: 使用 --real-demo 参数可执行真实的DEM下载和解析")

if __name__ == "__main__":
    asyncio.run(main())
