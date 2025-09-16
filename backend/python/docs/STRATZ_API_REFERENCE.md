# STRATZ API 参考文档

## 官方文档网站
- **主要文档**: https://docs.stratz.com/
- **API浏览器**: https://api.stratz.com/
- **GraphQL Playground**: https://api.stratz.com/graphql

## API端点结构

### Base URL
```
https://api.stratz.com/api/v1/
```

### 认证方式
```http
Authorization: Bearer YOUR_API_TOKEN
```

## 主要端点

### 比赛数据 (Match)
```
GET /api/v1/Match/{matchId}           # 比赛详情
GET /api/v1/Match/{matchId}/players   # 比赛选手
GET /api/v1/Match/{matchId}/performance # 比赛表现
GET /api/v1/Match/{matchId}/vision    # 视野数据
GET /api/v1/Match/{matchId}/breakdown # 详细分析
```

### 选手数据 (Player)
```
GET /api/v1/Player/{accountId}        # 选手信息
GET /api/v1/Player/{accountId}/matches # 比赛历史
GET /api/v1/Player/{accountId}/heroes # 英雄统计
GET /api/v1/Player/{accountId}/performance # 表现数据
```

### 英雄数据 (Hero)
```
GET /api/v1/Hero                      # 所有英雄
GET /api/v1/Hero/{heroId}             # 英雄详情
GET /api/v1/Hero/{heroId}/matchUp     # 克制关系
GET /api/v1/Hero/{heroId}/performance # 表现统计
```

### 联赛数据 (League)
```
GET /api/v1/League/{leagueId}         # 联赛信息
GET /api/v1/League/{leagueId}/matches # 联赛比赛
GET /api/v1/League/{leagueId}/teams   # 参赛队伍
```

### 队伍数据 (Team)
```
GET /api/v1/Team/{teamId}             # 队伍信息
GET /api/v1/Team/{teamId}/matches     # 队伍比赛
GET /api/v1/Team/{teamId}/players     # 队伍成员
```

## GraphQL端点
```
POST /graphql                          # GraphQL查询
```

## 重要说明

### 1. 大小写敏感
STRATZ API的端点是**大小写敏感**的：
- ✅ 正确: `/api/v1/Match/123456`
- ❌ 错误: `/api/v1/match/123456`

### 2. 数据格式
- 响应格式: JSON
- 编码: UTF-8
- 时间戳: Unix时间戳（秒）

### 3. 限制说明
您的token限制：
- **20 调用/秒**
- **250 调用/分钟** 
- **2,000 调用/小时**
- **10,000 调用/日**

### 4. 常见状态码
- `200`: 成功
- `403`: 认证失败或权限不足
- `429`: 速率限制
- `404`: 数据不存在

## 快速测试

### 浏览器测试
```
https://api.stratz.com/api/v1/Hero
```

### curl测试
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://api.stratz.com/api/v1/Match/8464041509
```

### Python测试
```python
import requests

headers = {'Authorization': 'Bearer YOUR_TOKEN'}
response = requests.get(
    'https://api.stratz.com/api/v1/Hero',
    headers=headers
)
print(response.json())
```

## 数据结构对比

### STRATZ vs OpenDota

| 特性 | STRATZ | OpenDota |
|------|--------|----------|
| 认证要求 | 需要Token | 免费访问 |
| 数据详细度 | 非常详细 | 中等 |
| 实时性 | 实时更新 | 有延迟 |
| 专业数据 | 有 | 有限 |
| 速率限制 | 严格 | 宽松 |

## 建议

1. **先测试简单端点**: 用 `/Hero` 端点测试认证是否成功
2. **注意大小写**: 确保端点大小写正确
3. **监控速率**: 注意调用频率，避免触发限制
4. **错误处理**: 做好异常处理和重试机制

---

您现在可以去官方文档网站查看详细的API说明，然后告诉我您想获取哪些具体的数据！