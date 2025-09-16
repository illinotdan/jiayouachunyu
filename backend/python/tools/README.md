# 🎯 比赛数据收集工具 (Match Data Collector)

这个工具专门用于收集Dota2比赛数据，为AI模型训练提供高质量的数据集。

## 🚀 功能特性

### 📊 数据收集功能
- **批量比赛ID获取**: 按时间范围获取所有比赛ID
- **多条件搜索**: 支持战队、选手、英雄、联赛等多维度搜索
- **复合条件搜索**: 支持多个条件组合的精确搜索
- **批量详情获取**: 高效批量获取比赛详细信息
- **数据自动保存**: JSON格式保存，便于后续处理

### 🔍 搜索条件
- **战队搜索**: 按战队名称搜索比赛
- **选手搜索**: 按选手名称或Steam ID搜索
- **英雄搜索**: 按英雄名称搜索相关比赛
- **联赛搜索**: 按联赛名称搜索职业比赛
- **时间范围**: 指定开始和结束日期
- **游戏模式**: 支持不同游戏模式过滤
- **复合条件**: 多个条件组合的精确搜索

## 📦 安装和使用

### 1. 基本使用
```python
from tools.match_data_collector import MatchDataCollector

# 初始化收集器
collector = MatchDataCollector(api_key='your_api_key')

# 获取最近的比赛ID
match_ids = collector.get_all_match_ids(
    start_date='2024-09-01',
    end_date='2024-09-16',
    max_matches=100
)

# 搜索特定英雄的比赛
pudge_matches = collector.search_matches_by_hero('Pudge', limit=50)

# 复合条件搜索
complex_matches = collector.complex_search(
    hero='Invoker',
    league='DPC',
    start_date='2024-08-01',
    limit=30
)
```

### 2. AI训练数据收集
```python
# 一键收集AI训练数据
training_data = collector.collect_training_data(
    hero='Anti-Mage',
    start_date='2024-08-01',
    end_date='2024-09-16',
    limit=100
)

print(f"数据文件: {training_data['filepath']}")
print(f"比赛数量: {training_data['stats']['total_matches']}")
```

### 3. 使用示例脚本
```bash
# 运行完整的数据收集示例
python tools/collect_ai_data.py

# 选择收集模式
1. 完整AI训练数据收集 - 收集多个英雄和联赛的数据
2. 快速数据收集 - 快速收集小规模测试数据
```

## 📋 数据格式

### 比赛基本信息
```json
{
    "id": 1234567890,
    "startDateTime": "2024-09-16T12:30:00Z",
    "duration": 1800,
    "gameMode": "Ranked",
    "lobbyType": "Public",
    "players": [
        {
            "heroId": 1,
            "steamAccountId": 164834557,
            "isVictory": true,
            "kills": 10,
            "deaths": 2,
            "assists": 15
        }
    ]
}
```

### 搜索统计信息
```python
{
    'success': True,
    'filepath': 'data/match_data/training_matches_20240916_143022.json',
    'stats': {
        'total_matches': 100,
        'collection_time': 45.2,
        'average_match_duration': 2100,
        'game_modes': {
            'Ranked': 80,
            'Captain\'s Mode': 20
        },
        'date_range': {
            'earliest': '2024-08-01T00:00:00Z',
            'latest': '2024-09-16T23:59:59Z'
        }
    }
}
```

## 🎯 使用场景

### 1. AI模型训练数据准备
```python
# 收集热门英雄数据
popular_heroes = ['Pudge', 'Invoker', 'Anti-Mage']
for hero in popular_heroes:
    collector.collect_training_data(
        hero=hero,
        limit=200  # 每个英雄200场比赛
    )
```

### 2. 职业比赛分析
```python
# 收集职业联赛数据
leagues = ['The International', 'DPC', 'ESL']
for league in leagues:
    matches = collector.search_matches_by_league(league, limit=500)
    collector.save_match_data(matches, f"{league}_matches")
```

### 3. 特定选手研究
```python
# 收集知名选手数据
pro_players = ['Miracle-', 'Ana', 'Somnus']
for player in pro_players:
    matches = collector.search_matches_by_player(player, limit=100)
    collector.save_match_data(matches, f"{player}_matches")
```

### 4. 复合条件精确搜索
```python
# 搜索特定条件下的比赛
matches = collector.complex_search(
    hero='Invoker',
    league='DPC',
    start_date='2024-06-01',
    end_date='2024-09-01',
    limit=50
)
```

## ⚡ 性能优化

### 批量处理
- 支持批量获取比赛详情
- 多线程并发处理
- 智能限流避免API限制

### 数据缓存
- 自动保存已收集的数据
- 支持断点续传
- 避免重复收集相同数据

### 错误处理
- 完善的异常处理机制
- 自动重试失败请求
- 详细的错误日志记录

## 📁 文件结构
```
backend/python/tools/
├── match_data_collector.py    # 主要收集器类
├── collect_ai_data.py         # 使用示例脚本
└── README.md                  # 本文档

backend/python/data/match_data/
├── training_matches_*.json    # 训练数据文件
├── hero_matches_*.json        # 英雄相关比赛
├── league_matches_*.json      # 联赛相关比赛
└── player_matches_*.json      # 选手相关比赛
```

## 🔧 配置参数

### 收集器配置
```python
collector = MatchDataCollector(api_key)
collector.batch_size = 100      # 批量大小
collector.max_workers = 5     # 并发线程数
```

### 搜索限制
- 单次搜索最大返回1000场比赛
- 批量处理每批100场比赛
- 支持最大5个并发线程
- 自动1秒延迟避免API限流

## 🚨 注意事项

1. **API限制**: 注意STRATZ API的调用频率限制
2. **数据量**: 大量数据收集可能需要较长时间
3. **存储空间**: 确保有足够的磁盘空间保存数据
4. **网络连接**: 稳定的网络连接以保证数据收集完整性

## 📞 问题反馈

如果在使用过程中遇到问题，请检查：
- API密钥是否有效
- 网络连接是否正常
- 搜索条件是否合理
- 磁盘空间是否充足

## 🎉 开始使用

现在你可以开始使用这个工具来收集Dota2比赛数据，为你的AI模型训练提供高质量的数据集！