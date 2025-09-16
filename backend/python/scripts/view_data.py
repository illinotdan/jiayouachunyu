#!/usr/bin/env python
"""
数据查看和分析工具
用于查看和分析获取的样本数据
"""

import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(project_root))

class DataViewer:
    """数据查看器类"""
    
    def __init__(self, data_dir: str = "data/samples"):
        self.data_dir = data_dir
        self.samples = {}
    
    def load_samples(self, pattern: str = "*.json"):
        """加载样本数据"""
        import glob
        
        sample_files = glob.glob(os.path.join(self.data_dir, pattern))
        
        for filepath in sample_files:
            filename = os.path.basename(filepath)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.samples[filename] = {
                    'filepath': filepath,
                    'data': data,
                    'size': os.path.getsize(filepath),
                    'record_count': len(data) if isinstance(data, list) else 1
                }
                
            except Exception as e:
                print(f"加载文件失败 {filename}: {e}")
    
    def list_samples(self):
        """列出所有样本"""
        if not self.samples:
            print("没有找到样本数据")
            return
        
        print("\n=== 样本数据列表 ===")
        for filename, info in self.samples.items():
            print(f"\n文件名: {filename}")
            print(f"  文件大小: {info['size']:,} 字节")
            print(f"  记录数量: {info['record_count']}")
            print(f"  数据类型: {type(info['data']).__name__}")
    
    def show_sample_content(self, filename: str, max_items: int = 5):
        """显示样本内容"""
        if filename not in self.samples:
            print(f"文件 {filename} 不存在")
            return
        
        sample = self.samples[filename]
        data = sample['data']
        
        print(f"\n=== {filename} 内容预览 ===")
        print(f"记录数量: {sample['record_count']}")
        
        if isinstance(data, list):
            print(f"显示前 {min(max_items, len(data))} 条记录:")
            for i, item in enumerate(data[:max_items]):
                print(f"\n--- 记录 {i+1} ---")
                self._print_item_summary(item)
        else:
            print("数据内容:")
            self._print_item_summary(data)
    
    def _print_item_summary(self, item: Dict, indent: int = 0):
        """打印项目摘要"""
        prefix = "  " * indent
        
        for key, value in item.items():
            if isinstance(value, dict):
                print(f"{prefix}{key}:")
                self._print_item_summary(value, indent + 1)
            elif isinstance(value, list):
                print(f"{prefix}{key}: [列表，{len(value)} 项]")
                if len(value) > 0 and isinstance(value[0], dict):
                    # 显示列表中第一个项目的结构
                    print(f"{prefix}  示例项目:")
                    self._print_item_summary(value[0], indent + 2)
            else:
                # 截断长字符串
                if isinstance(value, str) and len(value) > 100:
                    value_str = value[:100] + "..."
                else:
                    value_str = str(value)
                
                print(f"{prefix}{key}: {value_str}")
    
    def analyze_data_structure(self, filename: str):
        """分析数据结构"""
        if filename not in self.samples:
            print(f"文件 {filename} 不存在")
            return
        
        data = self.samples[filename]['data']
        
        print(f"\n=== {filename} 数据结构分析 ===")
        
        if isinstance(data, list):
            print(f"数据类型: 列表 ({len(data)} 项)")
            if data:
                self._analyze_dict_structure(data[0], "列表项结构")
        else:
            self._analyze_dict_structure(data, "字典结构")
    
    def _analyze_dict_structure(self, data: Dict, title: str, indent: int = 0):
        """分析字典结构"""
        prefix = "  " * indent
        print(f"\n{prefix}{title}:")
        
        for key, value in data.items():
            value_type = type(value).__name__
            
            if isinstance(value, dict):
                print(f"{prefix}  {key}: {value_type}")
                self._analyze_dict_structure(value, f"{key} 结构", indent + 2)
            elif isinstance(value, list):
                if value:
                    item_type = type(value[0]).__name__
                    print(f"{prefix}  {key}: {value_type} [{item_type}, {len(value)} 项]")
                    
                    if isinstance(value[0], dict):
                        self._analyze_dict_structure(value[0], f"{key} 示例项结构", indent + 2)
                else:
                    print(f"{prefix}  {key}: {value_type} [空列表]")
            else:
                print(f"{prefix}  {key}: {value_type} = {str(value)[:50]}")
    
    def compare_data_sources(self):
        """对比不同数据源"""
        # 分类样本文件
        opendota_files = [f for f in self.samples.keys() if 'opendota' in f.lower()]
        stratz_files = [f for f in self.samples.keys() if 'stratz' in f.lower()]
        combined_files = [f for f in self.samples.keys() if 'combined' in f.lower()]
        
        print("\n=== 数据源对比 ===")
        
        if opendota_files:
            print(f"\nOpenDota 数据文件 ({len(opendota_files)} 个):")
            for filename in opendota_files[:3]:  # 显示前3个
                info = self.samples[filename]
                print(f"  {filename}: {info['record_count']} 条记录")
        
        if stratz_files:
            print(f"\nSTRATZ 数据文件 ({len(stratz_files)} 个):")
            for filename in stratz_files[:3]:  # 显示前3个
                info = self.samples[filename]
                print(f"  {filename}: {info['record_count']} 条记录")
        
        if combined_files:
            print(f"\n整合数据文件 ({len(combined_files)} 个):")
            for filename in combined_files[:3]:  # 显示前3个
                info = self.samples[filename]
                print(f"  {filename}: {info['record_count']} 条记录")
    
    def generate_summary_report(self):
        """生成数据摘要报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_files': len(self.samples),
            'total_records': sum(info['record_count'] for info in self.samples.values()),
            'total_size': sum(info['size'] for info in self.samples.values()),
            'file_breakdown': {}
        }
        
        # 按数据源分类
        for filename, info in self.samples.items():
            if 'opendota' in filename.lower():
                category = 'opendota'
            elif 'stratz' in filename.lower():
                category = 'stratz'
            elif 'combined' in filename.lower():
                category = 'combined'
            else:
                category = 'other'
            
            if category not in report['file_breakdown']:
                report['file_breakdown'][category] = {
                    'files': 0,
                    'records': 0,
                    'size': 0
                }
            
            report['file_breakdown'][category]['files'] += 1
            report['file_breakdown'][category]['records'] += info['record_count']
            report['file_breakdown'][category]['size'] += info['size']
        
        # 保存报告
        report_file = "data/data_summary_report.json"
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"\n数据摘要报告已保存: {report_file}")
        except Exception as e:
            print(f"保存报告失败: {e}")
        
        # 显示报告
        print("\n=== 数据摘要报告 ===")
        print(f"总文件数: {report['total_files']}")
        print(f"总记录数: {report['total_records']:,}")
        print(f"总大小: {report['total_size']:,} 字节 ({report['total_size']/1024/1024:.2f} MB)")
        
        print("\n按数据源分类:")
        for category, stats in report['file_breakdown'].items():
            print(f"\n{category.upper()}:")
            print(f"  文件数: {stats['files']}")
            print(f"  记录数: {stats['records']:,}")
            print(f"  大小: {stats['size']:,} 字节 ({stats['size']/1024:.2f} KB)")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Dota2数据查看工具")
    parser.add_argument("--data-dir", default="data/samples", help="数据目录")
    parser.add_argument("--pattern", default="*.json", help="文件匹配模式")
    parser.add_argument("--list", action="store_true", help="列出所有样本")
    parser.add_argument("--show", help="显示指定文件内容")
    parser.add_argument("--max-items", type=int, default=5, help="显示的最大项目数")
    parser.add_argument("--analyze", help="分析指定文件结构")
    parser.add_argument("--compare", action="store_true", help="对比不同数据源")
    parser.add_argument("--summary", action="store_true", help="生成摘要报告")
    
    args = parser.parse_args()
    
    # 创建查看器
    viewer = DataViewer(data_dir=args.data_dir)
    
    # 加载样本数据
    print(f"正在从 {args.data_dir} 加载样本数据...")
    viewer.load_samples(pattern=args.pattern)
    
    if not viewer.samples:
        print("没有找到样本数据文件")
        return
    
    # 执行指定操作
    if args.list:
        viewer.list_samples()
    
    if args.show:
        viewer.show_sample_content(args.show, max_items=args.max_items)
    
    if args.analyze:
        viewer.analyze_data_structure(args.analyze)
    
    if args.compare:
        viewer.compare_data_sources()
    
    if args.summary:
        viewer.generate_summary_report()
    
    # 如果没有指定操作，显示帮助
    if not any([args.list, args.show, args.analyze, args.compare, args.summary]):
        print("\n可用操作:")
        print("  --list           列出所有样本")
        print("  --show 文件名    显示文件内容")
        print("  --analyze 文件名 分析文件结构")
        print("  --compare        对比数据源")
        print("  --summary        生成摘要报告")
        print("\n示例:")
        print("  python view_data.py --list")
        print("  python view_data.py --show opendota_matches_*.json")
        print("  python view_data.py --analyze stratz_heroes_*.json")

if __name__ == "__main__":
    main()