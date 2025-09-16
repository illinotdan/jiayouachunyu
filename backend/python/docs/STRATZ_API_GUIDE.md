# STRATZ API 使用指南

## 概述
STRATZ API 是一个专业的Dota 2数据服务，提供比OpenDota更详细和专业的数据。但大多数API需要API密钥才能访问。

## 认证要求
- **REST API**: 需要Bearer Token认证
- **GraphQL API**: 需要Bearer Token认证

## 免费vs付费功能

### 免费功能（无需认证）
- 基础英雄信息
- 基础联赛信息
- 部分公开比赛数据

### 需要认证的功能
- 详细比赛数据
- 选手表现分析
- 高级统计数据
- 实时数据更新

## 获取API密钥
1. 访问 https://stratz.com/api
2. 注册账户
3. 申请API访问权限
4. 获取API密钥

## 配置方法
在 `stratz_service.py` 中配置API密钥：

```python
# 方法1：直接设置
stratz_service = StratzService(api_key="your_api_key_here")

# 方法2：环境变量
# 设置环境变量 STRATZ_API_KEY=your_api_key_here
stratz_service = StratzService()
```

## 可用数据接口

### 比赛数据
- `get_match(match_id)` - 获取比赛详细信息
- `get_match_players(match_id)` - 获取比赛选手数据
- `get_match_performance(match_id)` - 获取比赛表现数据
- `get_detailed_match_analysis(match_id)` - 获取完整比赛分析

### 选手数据
- `get_player(account_id)` - 获取选手信息
- `get_player_matches(account_id, limit)` - 获取选手比赛历史
- `get_player_heroes(account_id)` - 获取选手英雄数据

### 英雄数据
- `get_heroes()` - 获取所有英雄
- `get_hero(hero_id)` - 获取英雄详细信息
- `get_hero_matchups(hero_id)` - 获取英雄克制关系
- `get_hero_performance(hero_id)` - 获取英雄表现统计

### 联赛数据
- `get_league(league_id)` - 获取联赛信息
- `get_league_matches(league_id, limit)` - 获取联赛比赛

### 高级查询
- `get_explorer_matches(filters)` - 使用GraphQL进行高级筛选

## 数据结构示例

### 比赛数据包含：
- 基础信息：比赛ID、开始时间、持续时间、胜负结果
- 队伍信息：天辉/夜魇队伍ID、得分
- 游戏设置：游戏模式、大厅类型、服务器集群
- 高级数据：平均天梯等级、人类玩家数量

### 选手数据包含：
- 基础信息：账户ID、昵称、排名等级
- 表现数据：KDA、GPM、XPM、伤害、治疗
- 英雄数据：使用英雄、英雄表现、英雄统计
- 对比数据：与同级别选手的对比百分位

## 使用建议
1. **优先使用OpenDota**: 对于基础数据，OpenDota免费且无需认证
2. **STRATZ用于补充**: 当需要更详细的专业数据时使用STRATZ
3. **缓存数据**: 避免重复API调用，提高性能
4. **错误处理**: 处理API限制和认证失败情况

## 下一步计划
1. 获取STRATZ API密钥
2. 测试认证后的数据访问
3. 对比OpenDota和STRATZ数据结构
4. 设计数据整合策略