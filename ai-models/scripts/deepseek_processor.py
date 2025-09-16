#!/usr/bin/env python3
"""
DeepSeek 微调数据处理器
将训练数据转换为DeepSeek API格式
"""

import json
import os
from typing import Dict, List, Any
from datetime import datetime

class DeepSeekDataProcessor:
    """DeepSeek微调数据处理器"""
    
    def __init__(self, model_name: str = "deepseek-chat"):
        """初始化处理器
        
        Args:
            model_name: 使用的DeepSeek模型名称
        """
        self.model_name = model_name
    
    def process_training_data(self, input_file: str, output_file: str) -> Dict[str, Any]:
        """处理训练数据为DeepSeek格式
        
        Args:
            input_file: 输入的训练数据文件路径
            output_file: 输出的DeepSeek格式文件路径
            
        Returns:
            处理统计信息
        """
        print(f"📖 读取训练数据: {input_file}")
        
        # 读取训练数据
        with open(input_file, 'r', encoding='utf-8') as f:
            training_samples = json.load(f)
        
        print(f"📊 共读取 {len(training_samples)} 个训练样本")
        
        # 转换为DeepSeek格式
        deepseek_samples = []
        for i, sample in enumerate(training_samples):
            if i % 100 == 0:
                print(f"🔄 处理进度: {i}/{len(training_samples)}")
            
            deepseek_sample = self._convert_to_deepseek_format(sample)
            if deepseek_sample:
                deepseek_samples.append(deepseek_sample)
        
        # 保存处理后的数据
        self._save_deepseek_data(deepseek_samples, output_file)
        
        # 生成统计信息
        stats = {
            'total_samples': len(training_samples),
            'processed_samples': len(deepseek_samples),
            'skipped_samples': len(training_samples) - len(deepseek_samples),
            'avg_input_length': sum(len(s['messages'][0]['content']) for s in deepseek_samples) / len(deepseek_samples) if deepseek_samples else 0,
            'avg_output_length': sum(len(s['messages'][1]['content']) for s in deepseek_samples) / len(deepseek_samples) if deepseek_samples else 0,
            'processing_time': datetime.now().isoformat()
        }
        
        print(f"✅ 处理完成!")
        print(f"   - 总样本数: {stats['total_samples']}")
        print(f"   - 成功处理: {stats['processed_samples']}")
        print(f"   - 跳过的样本: {stats['skipped_samples']}")
        print(f"   - 平均输入长度: {stats['avg_input_length']:.0f} 字符")
        print(f"   - 平均输出长度: {stats['avg_output_length']:.0f} 字符")
        
        return stats
    
    def _convert_to_deepseek_format(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """将单个样本转换为DeepSeek格式"""
        try:
            training_text = sample.get('training_text', '')
            match_id = sample.get('match_id', 'unknown')
            metadata = sample.get('metadata', {})
            
            # 提取关键信息用于构建提示
            lines = training_text.split('\n')
            
            # 构建用户提示 (问题)
            user_prompt = self._build_user_prompt(training_text, match_id, metadata)
            
            # 构建助手回复 (答案)
            assistant_response = self._build_assistant_response(training_text, match_id, metadata)
            
            # 构建DeepSeek格式的对话
            deepseek_sample = {
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个专业的刀塔2比赛分析师和智能助手。你将基于比赛数据、社区讨论和战术分析，为用户提供深度的比赛洞察和学习建议。"
                    },
                    {
                        "role": "user", 
                        "content": user_prompt
                    },
                    {
                        "role": "assistant",
                        "content": assistant_response
                    }
                ],
                "metadata": {
                    "match_id": match_id,
                    "data_sources": metadata.get('data_sources', []),
                    "has_comments": metadata.get('has_comments', False),
                    "generated_at": metadata.get('generated_at', datetime.now().isoformat())
                }
            }
            
            return deepseek_sample
            
        except Exception as e:
            print(f"转换样本失败 {sample.get('match_id', 'unknown')}: {e}")
            return None
    
    def _build_user_prompt(self, training_text: str, match_id: str, metadata: Dict[str, Any]) -> str:
        """构建用户提示"""
        
        # 从训练文本中提取关键信息
        lines = training_text.split('\n')
        
        # 提取基础信息
        duration = self._extract_info_from_text(lines, "比赛时长")
        winner = self._extract_info_from_text(lines, "获胜方")
        teams = self._extract_info_from_text(lines, "## 比赛数据分析")
        
        # 构建用户问题
        user_prompt = f"""请作为刀塔2专家分析师，基于以下比赛信息为我提供深度分析：

**比赛基本信息：**
- 比赛ID: {match_id}
- 对阵双方: {teams}
- 比赛时长: {duration}
- 获胜方: {winner}
- 数据来源: {', '.join(metadata.get('data_sources', ['opendota', 'stratz', 'liquipedia', 'dem']))}

**我的需求：**
1. 分析这场比赛的关键战术要点
2. 指出可以学习的技巧和策略
3. 基于社区讨论总结玩家观点
4. 推荐类似的比赛进行进一步学习

请提供详细的专业分析，包括具体的游戏机制解释和实战建议。"""
        
        return user_prompt.strip()
    
    def _build_assistant_response(self, training_text: str, match_id: str, metadata: Dict[str, Any]) -> str:
        """构建助手回复"""
        
        # 直接使用训练文本作为回复，但重新格式化使其更适合对话
        
        # 提取各个部分
        lines = training_text.split('\n')
        
        # 构建结构化的回复
        response = f"""我来为你深度分析这场精彩的刀塔比赛 #{match_id}：

## 📊 比赛概况分析
{self._extract_section(lines, "比赛概况")}

## ⚔️ 英雄阵容与战术分析  
{self._extract_section(lines, "英雄分析")}

## 💰 经济与装备分析
{self._extract_section(lines, "经济走势")}

## 💬 社区观点总结
{self._extract_section(lines, "社区洞察")}

## 🎯 关键洞察与学习要点

基于数据和社区讨论，这场比赛的核心要点：

{self._extract_section(lines, "AI综合分析")}

## 📚 实战建议

**立即可应用的技巧：**
1. 关注肉山的控制时机，特别是在20分钟左右的timing
2. 核心英雄的装备timing对团战结果有决定性影响
3. 高地推进需要谨慎选择时机，避免被反打

**进阶学习方向：**
- 研究职业比赛的团战站位和技能释放顺序
- 分析不同英雄的经济曲线和装备选择
- 理解地图控制和视野布控的重要性

## 🔗 进一步学习

{self._extract_info_from_text(lines, "类似比赛推荐")}

---
*分析基于 {metadata.get('data_sources', ['多数据源'])} 数据和社区讨论*"""
        
        return response.strip()
    
    def _extract_info_from_text(self, lines: List[str], keyword: str) -> str:
        """从文本中提取特定信息"""
        for line in lines:
            if keyword in line and ':' in line:
                return line.split(':', 1)[1].strip()
        return "暂无相关信息"
    
    def _extract_section(self, lines: List[str], section_title: str) -> str:
        """提取特定章节的内容"""
        try:
            start_idx = None
            end_idx = None
            
            for i, line in enumerate(lines):
                if f"## {section_title}" in line:
                    start_idx = i + 1
                elif start_idx and line.startswith("## "):
                    end_idx = i
                    break
            
            if start_idx is not None:
                if end_idx is None:
                    end_idx = len(lines)
                
                section_lines = lines[start_idx:end_idx]
                return '\n'.join(line.strip() for line in section_lines if line.strip())
            
            return "该部分内容暂缺"
            
        except Exception as e:
            print(f"提取章节失败 {section_title}: {e}")
            return "章节提取失败"
    
    def _save_deepseek_data(self, samples: List[Dict[str, Any]], output_file: str):
        """保存DeepSeek格式的数据"""
        try:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # 保存为JSONL格式（每行一个JSON对象）
            if output_file.endswith('.jsonl'):
                with open(output_file, 'w', encoding='utf-8') as f:
                    for sample in samples:
                        json.dump(sample, f, ensure_ascii=False)
                        f.write('\n')
            else:
                # 保存为标准JSON格式
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(samples, f, ensure_ascii=False, indent=2)
            
            print(f"💾 DeepSeek格式数据已保存: {output_file}")
            
        except Exception as e:
            print(f"保存DeepSeek数据失败: {e}")
            raise


def main():
    """主函数 - 测试DeepSeek数据处理器"""
    print("🚀 启动DeepSeek数据处理器...")
    
    # 创建处理器
    processor = DeepSeekDataProcessor(model_name="deepseek-chat")
    
    # 输入输出文件路径
    input_file = "c:/Users/yb/PycharmProjects/PythonProject/ai-models/data/training_samples.json"
    output_file = "c:/Users/yb/PycharmProjects/PythonProject/ai-models/data/deepseek_training_data.json"
    
    # 处理数据
    stats = processor.process_training_data(input_file, output_file)
    
    # 显示示例
    print("\n📋 显示处理后的示例数据:")
    print("="*60)
    
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            samples = json.load(f)
        
        if samples:
            sample = samples[0]
            print(f"样本ID: {sample['metadata']['match_id']}")
            print(f"用户问题: {sample['messages'][1]['content'][:200]}...")
            print(f"助手回复: {sample['messages'][2]['content'][:200]}...")
            print(f"元数据: {sample['metadata']}")
    
    except Exception as e:
        print(f"显示示例失败: {e}")
    
    print("\n✅ DeepSeek数据处理完成！")
    print("\n下一步:")
    print("1. 使用deepseek API上传数据进行微调")
    print("2. 在应用中集成微调后的模型")
    print("3. 创建智能助手接口")


if __name__ == '__main__':
    main()