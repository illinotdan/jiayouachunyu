#!/usr/bin/env python3
"""
测试数据初始化脚本
用于初始化数据库并生成测试数据
"""

import sys
import os
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='初始化测试数据')
    parser.add_argument('--clean', action='store_true', help='清理现有数据')
    parser.add_argument('--heroes-only', action='store_true', help='只生成英雄数据')
    parser.add_argument('--items-only', action='store_true', help='只生成物品数据')
    parser.add_argument('--verbose', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    try:
        # 导入初始化函数
        from scripts.init_test_data import init_test_database
        
        print("开始初始化测试数据...")
        
        # 调用初始化函数
        result = init_test_database(
            clean_existing=args.clean,
            heroes_only=args.heroes_only,
            items_only=args.items_only,
            verbose=args.verbose
        )
        
        if result:
            print("✅ 测试数据初始化成功!")
            print(f"生成了 {result.get('heroes', 0)} 个英雄")
            print(f"生成了 {result.get('items', 0)} 个物品")
            print(f"生成了 {result.get('teams', 0)} 个战队")
            print(f"生成了 {result.get('players', 0)} 个选手")
            print(f"生成了 {result.get('matches', 0)} 场比赛")
            print(f"生成了 {result.get('match_players', 0)} 条比赛选手数据")
            print(f"生成了 {result.get('match_drafts', 0)} 条Pick/Ban数据")
            print(f"生成了 {result.get('match_analyses', 0)} 条比赛分析数据")
        else:
            print("❌ 测试数据初始化失败!")
            return 1
            
    except Exception as e:
        print(f"❌ 初始化过程出错: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())