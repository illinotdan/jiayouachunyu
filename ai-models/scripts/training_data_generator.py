#!/usr/bin/env python3
"""
AI训练数据生成器
将比赛数据 + 社区评论转换为AI训练文本
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# 添加backend路径到sys.path
backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'backend', 'python')
sys.path.append(backend_path)

# 导入后端服务（如果可用）
try:
    from services.unified_data_service import UnifiedDataService
    from models.match import Match
    from models.comment import Comment
    from config.database import db
    BACKEND_AVAILABLE = True
except ImportError as e:
    print(f"后端模块导入失败: {e}")
    BACKEND_AVAILABLE = False

@dataclass
class MatchData:
    """比赛数据结构"""
    match_id: str
    teams: str
    duration: str
    winner: str
    game_mode: str
    lobby_type: str
    start_time: datetime
    first_blood_time: int
    game_version: str
    region: str
    series_id: Optional[str] = None
    series_type: Optional[str] = None
    league_id: Optional[str] = None
    
@dataclass
class CommentData:
    """评论数据结构"""
    id: str
    content: str
    author: str
    created_at: datetime
    likes: int
    is_featured: bool
    analysis_quality: Optional[str] = None

class AITrainingDataGenerator:
    """AI训练数据生成器"""
    
    def __init__(self, use_backend: bool = True):
        """初始化生成器
        
        Args:
            use_backend: 是否使用后端数据库，如果为False则使用模拟数据
        """
        self.use_backend = use_backend and BACKEND_AVAILABLE
        if self.use_backend:
            self.unified_service = UnifiedDataService()
    
    def get_match_comprehensive_data(self, match_id: str) -> Dict[str, Any]:
        """获取比赛的综合数据（四源数据聚合）"""
        if self.use_backend:
            return self._get_match_data_from_backend(match_id)
        else:
            return self._get_mock_match_data(match_id)
    
    def get_featured_comments(self, match_id: str, min_likes: int = 5) -> List[CommentData]:
        """获取比赛的精选评论"""
        if self.use_backend:
            return self._get_comments_from_backend(match_id, min_likes)
        else:
            return self._get_mock_comments(match_id)
    
    def generate_training_sample(self, match_id: str) -> str:
        """生成单个比赛的训练样本"""
        try:
            # 1. 获取比赛的四源数据
            match_data = self.get_match_comprehensive_data(match_id)
            
            # 2. 获取精选评论
            featured_comments = self.get_featured_comments(match_id)
            
            # 3. 生成训练文本
            training_text = self._format_training_text(match_data, featured_comments)
            
            return training_text
            
        except Exception as e:
            print(f"生成训练样本失败 {match_id}: {e}")
            return self._generate_error_sample(match_id, str(e))
    
    def generate_batch_training_data(self, match_ids: List[str], output_file: str = None) -> List[Dict[str, Any]]:
        """批量生成训练数据"""
        training_samples = []
        
        for i, match_id in enumerate(match_ids):
            print(f"处理比赛 {i+1}/{len(match_ids)}: {match_id}")
            
            try:
                sample_text = self.generate_training_sample(match_id)
                sample_data = {
                    'match_id': match_id,
                    'training_text': sample_text,
                    'metadata': {
                        'generated_at': datetime.now().isoformat(),
                        'data_sources': ['opendota', 'stratz', 'liquipedia', 'dem'],
                        'has_comments': len(self.get_featured_comments(match_id)) > 0
                    }
                }
                training_samples.append(sample_data)
                
            except Exception as e:
                print(f"跳过比赛 {match_id}: {e}")
                continue
        
        # 保存到文件
        if output_file:
            self._save_training_data(training_samples, output_file)
        
        return training_samples
    
    def _format_training_text(self, match_data: Dict[str, Any], comments: List[CommentData]) -> str:
        """格式化训练文本"""
        
        # 基础比赛信息
        base_info = self._format_match_base_info(match_data)
        
        # 英雄数据
        hero_analysis = self._format_hero_analysis(match_data)
        
        # 经济数据
        economy_analysis = self._format_economy_analysis(match_data)
        
        # 评论分析
        comments_analysis = self._format_comments_analysis(comments)
        
        # 生成训练文本
        training_text = f"""# 刀塔比赛深度分析 #{match_data['match_id']}

## 比赛概况
{base_info}

## 英雄分析
{hero_analysis}

## 经济走势
{economy_analysis}

## 社区洞察
{comments_analysis}

## AI综合分析
基于以上多维度数据和社区讨论，这场比赛的关键洞察：

### 战术层面
- 关键决策点：{match_data.get('key_decisions', '暂无数据')}
- 胜负手：{match_data.get('winning_factors', '暂无数据')}

### 技术层面
- 团队配合：{match_data.get('team_coordination', '中等水平')}
- 个人发挥：{match_data.get('individual_performance', '有待分析')}

### 社区观点总结
{self._summarize_community_views(comments)}

### 可学习的要点
1. {match_data.get('learning_point_1', '需要更多数据')}
2. {match_data.get('learning_point_2', '需要更多数据')}
3. {match_data.get('learning_point_3', '需要更多数据')}

### 类似比赛推荐
想要提升在这场比赛中学到的技能，建议观看：{match_data.get('similar_matches', '暂无推荐')}
---
训练标签: {match_data.get('tags', '经典比赛, 战术分析, 社区热议')}
"""
        
        return training_text.strip()
    
    def _format_match_base_info(self, match_data: Dict[str, Any]) -> str:
        """格式化比赛基础信息"""
        return f"""
- **比赛时长**: {match_data.get('duration', '未知')}
- **获胜方**: {match_data.get('winner', '未知')}
- **游戏模式**: {match_data.get('game_mode', '未知')}
- **开始时间**: {match_data.get('start_time', '未知')}
- **一血时间**: {match_data.get('first_blood_time', '未知')}秒
- **游戏版本**: {match_data.get('game_version', '未知')}
- **服务器区域**: {match_data.get('region', '未知')}
"""
    
    def _format_hero_analysis(self, match_data: Dict[str, Any]) -> str:
        """格式化英雄分析"""
        radiant_heroes = match_data.get('radiant_heroes', [])
        dire_heroes = match_data.get('dire_heroes', [])
        
        hero_info = f"""
**天辉方阵容**: {', '.join(radiant_heroes) if radiant_heroes else '暂无数据'}
**夜魇方阵容**: {', '.join(dire_heroes) if dire_heroes else '暂无数据'}
"""
        
        # 添加英雄克制分析
        if 'hero_matchups' in match_data:
            hero_info += f"\n**英雄克制关系**: {match_data['hero_matchups']}"
        
        return hero_info
    
    def _format_economy_analysis(self, match_data: Dict[str, Any]) -> str:
        """格式化经济分析"""
        return f"""
- **总经济差距**: {match_data.get('net_worth_lead', '未知')}
- **关键装备时机**: {match_data.get('key_item_timings', '未知')}
- **买活情况**: {match_data.get('buyback_status', '未知')}
- **肉山经济**: {match_data.get('roshan_economy', '未知')}
"""
    
    def _format_comments_analysis(self, comments: List[CommentData]) -> str:
        """格式化评论分析"""
        if not comments:
            return "暂无精选评论"
        
        analysis = ""
        for i, comment in enumerate(comments[:5]):  # 最多取5条评论
            analysis += f"""
**用户{comment.author}** ({comment.likes}👍):
"{comment.content}"
"""
        
        return analysis
    
    def _summarize_community_views(self, comments: List[CommentData]) -> str:
        """总结社区观点"""
        if not comments:
            return "社区讨论较少，需要更多用户参与"
        
        total_likes = sum(comment.likes for comment in comments)
        avg_quality = '高质量' if any(c.analysis_quality == 'high' for c in comments) else '中等质量'
        
        return f"社区讨论活跃({len(comments)}条评论，{total_likes}个点赞)，整体质量{avg_quality}，观点多元"
    
    def _get_match_data_from_backend(self, match_id: str) -> Dict[str, Any]:
        """从后端数据库获取比赛数据"""
        try:
            # 查询比赛基础信息
            match = Match.query.filter_by(match_id=match_id).first()
            if not match:
                raise ValueError(f"比赛 {match_id} 不存在")
            
            # 构建综合数据
            match_data = {
                'match_id': match_id,
                'teams': f"{match.radiant_name} vs {match.dire_name}" if match.radiant_name and match.dire_name else "未知队伍",
                'duration': f"{match.duration // 60}:{match.duration % 60:02d}" if match.duration else "未知",
                'winner': "天辉" if match.radiant_win else "夜魇" if match.radiant_win is not None else "未知",
                'game_mode': match.game_mode or "未知",
                'start_time': match.start_time.isoformat() if match.start_time else "未知",
                'first_blood_time': match.first_blood_time or 0,
                'game_version': match.game_version or "未知",
                'region': match.region or "未知",
                'radiant_heroes': self._get_match_heroes(match_id, True),
                'dire_heroes': self._get_match_heroes(match_id, False),
                'net_worth_lead': self._get_economy_analysis(match_id),
                'key_decisions': self._analyze_key_decisions(match),
                'tags': self._generate_match_tags(match)
            }
            
            return match_data
            
        except Exception as e:
            print(f"从后端获取比赛数据失败 {match_id}: {e}")
            return self._get_mock_match_data(match_id)
    
    def _get_comments_from_backend(self, match_id: str, min_likes: int) -> List[CommentData]:
        """从后端数据库获取精选评论"""
        try:
            # 查询精选评论
            comments = Comment.query.filter_by(
                match_id=match_id,
                is_featured=True
            ).filter(Comment.likes >= min_likes).order_by(Comment.likes.desc()).limit(10).all()
            
            comment_data = []
            for comment in comments:
                comment_data.append(CommentData(
                    id=str(comment.id),
                    content=comment.content,
                    author=comment.author.username if comment.author else "匿名用户",
                    created_at=comment.created_at,
                    likes=comment.likes or 0,
                    is_featured=comment.is_featured or False,
                    analysis_quality=comment.analysis_quality
                ))
            
            return comment_data
            
        except Exception as e:
            print(f"从后端获取评论失败 {match_id}: {e}")
            return self._get_mock_comments(match_id)
    
    def _get_mock_match_data(self, match_id: str) -> Dict[str, Any]:
        """获取模拟比赛数据（用于测试）"""
        return {
            'match_id': match_id,
            'teams': 'Team Secret vs OG',
            'duration': '45:30',
            'winner': '天辉',
            'game_mode': '队长模式',
            'start_time': '2024-01-15T14:30:00Z',
            'first_blood_time': 120,
            'game_version': '7.34e',
            'region': '欧洲西部',
            'radiant_heroes': ['斧王', '影魔', '帕克', '水晶室女', '复仇之魂'],
            'dire_heroes': ['幽鬼', '祈求者', '潮汐猎人', '天怒法师', '撼地者'],
            'net_worth_lead': '15000金币优势',
            'key_item_timings': '影魔15分钟黑皇杖，斧王18分钟跳刀',
            'buyback_status': '夜魇方买活CD，天辉方买活就绪',
            'roshan_economy': '天辉方控制肉山，获得不朽盾和奶酪',
            'key_decisions': '20分钟肉山团战争夺，35分钟高地推进',
            'winning_factors': '优秀的团战配合和关键装备时机',
            'team_coordination': '优秀',
            'individual_performance': '影魔完美发挥',
            'learning_point_1': '控制肉山时机的重要性',
            'learning_point_2': '核心装备timing对团战的影响',
            'learning_point_3': '高地推进的时机选择',
            'similar_matches': '推荐观看TI10总决赛',
            'tags': '经典比赛, 战术分析, 团战配合, 装备timing'
        }
    
    def _get_mock_comments(self, match_id: str) -> List[CommentData]:
        """获取模拟评论数据（用于测试）"""
        return [
            CommentData(
                id='1',
                content='这场比赛的团战配合太精彩了！影魔的完美发挥是关键。',
                author='刀塔分析师',
                created_at=datetime.now(),
                likes=25,
                is_featured=True,
                analysis_quality='high'
            ),
            CommentData(
                id='2',
                content='斧王的跳刀时机把握得非常好，每次都能抓到关键人物。',
                author='战术大师',
                created_at=datetime.now(),
                likes=18,
                is_featured=True,
                analysis_quality='high'
            ),
            CommentData(
                id='3',
                content='OG这边的幽鬼发育太慢了，没能及时参团。',
                author='carry玩家',
                created_at=datetime.now(),
                likes=12,
                is_featured=True,
                analysis_quality='medium'
            )
        ]
    
    def _get_match_heroes(self, match_id: str, is_radiant: bool) -> List[str]:
        """获取比赛英雄数据（模拟实现）"""
        # 这里应该从数据库获取实际英雄数据
        if is_radiant:
            return ['斧王', '影魔', '帕克', '水晶室女', '复仇之魂']
        else:
            return ['幽鬼', '祈求者', '潮汐猎人', '天怒法师', '撼地者']
    
    def _get_economy_analysis(self, match_id: str) -> str:
        """获取经济分析（模拟实现）"""
        return "15000金币优势"
    
    def _analyze_key_decisions(self, match) -> str:
        """分析关键决策点（模拟实现）"""
        return "20分钟肉山团战争夺，35分钟高地推进"
    
    def _generate_match_tags(self, match) -> str:
        """生成比赛标签（模拟实现）"""
        return "经典比赛, 战术分析, 团战配合, 装备timing"
    
    def _generate_error_sample(self, match_id: str, error_msg: str) -> str:
        """生成错误样本"""
        return f"""# 比赛数据分析 #{match_id}

## 错误信息
无法获取比赛数据: {error_msg}

## 建议
请检查比赛ID是否正确，或稍后重试。
"""
    
    def _save_training_data(self, training_samples: List[Dict[str, Any]], output_file: str):
        """保存训练数据到文件"""
        try:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(training_samples, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"训练数据已保存到: {output_file}")
            print(f"共生成 {len(training_samples)} 个训练样本")
            
        except Exception as e:
            print(f"保存训练数据失败: {e}")


def main():
    """主函数 - 测试训练数据生成器"""
    print("🚀 启动AI训练数据生成器测试...")
    
    # 创建生成器实例（使用模拟数据）
    generator = AITrainingDataGenerator(use_backend=False)
    
    # 测试单个比赛
    test_match_id = "1234567890"
    print(f"\n📊 生成比赛 {test_match_id} 的训练文本...")
    
    training_text = generator.generate_training_sample(test_match_id)
    print("\n" + "="*50)
    print("生成的训练文本:")
    print("="*50)
    print(training_text)
    print("="*50)
    
    # 测试批量生成
    print("\n📚 批量生成训练数据...")
    test_match_ids = ["1234567890", "0987654321", "1122334455"]
    
    output_file = "c:/Users/yb/PycharmProjects/PythonProject/ai-models/data/training_samples.json"
    training_samples = generator.generate_batch_training_data(test_match_ids, output_file)
    
    print(f"\n✅ 批量生成完成！共生成 {len(training_samples)} 个训练样本")
    
    # 显示统计信息
    total_chars = sum(len(sample['training_text']) for sample in training_samples)
    avg_chars = total_chars / len(training_samples) if training_samples else 0
    
    print(f"📈 统计信息:")
    print(f"   - 总字符数: {total_chars:,}")
    print(f"   - 平均字符数: {avg_chars:.0f}")
    print(f"   - 包含评论的样本: {sum(1 for s in training_samples if s['metadata']['has_comments'])}/{len(training_samples)}")


if __name__ == '__main__':
    main()