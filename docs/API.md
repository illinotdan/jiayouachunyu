# API文档

## 基础信息
- 后端API基础URL: `http://localhost:5000/api`
- Node.js API基础URL: `http://localhost:3001/api` (部分旧接口)
- 认证方式: JWT Token + Steam OAuth
- 数据格式: JSON
- API版本: v1 (支持版本控制)
- 限流策略: 100请求/分钟 (可配置)

## 认证

### Steam OAuth登录 (Python后端)
```http
GET /api/auth/steam/login
```

### Steam OAuth回调
```http
GET /api/auth/steam/callback
```

### JWT登录 (传统方式)
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "user",
  "password": "pass"
}
```

### 获取用户信息
```http
GET /api/auth/user
Authorization: Bearer <token>
```

### 刷新Token
```http
POST /api/auth/refresh
Authorization: Bearer <refresh_token>
```

## 比赛相关 (Python后端)

### 获取比赛列表
```http
GET /api/matches
Query参数:
- page: 页码 (默认: 1)
- limit: 每页数量 (默认: 20)
- tier: 比赛等级 (pro, premium, amateur)
- start_time: 开始时间戳
- end_time: 结束时间戳
- sort: 排序方式 (date, duration, mmr)
- order: 排序顺序 (asc, desc)
```

### 获取比赛详情
```http
GET /api/matches/:matchId
```

### 搜索比赛
```http
GET /api/matches/search
Query参数:
- team_name: 战队名称
- player_name: 选手名称
- hero: 英雄名称
- league: 联赛名称
- min_mmr: 最低MMR
- max_mmr: 最高MMR
```

### 同步比赛数据
```http
POST /api/matches/sync
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "source": "opendota",
  "match_ids": [1234567890, 0987654321]
}
```

## 评论系统 (Python后端)

### 获取比赛评论
```http
GET /api/matches/:matchId/comments
Query参数:
- page: 页码 (默认: 1)
- limit: 每页数量 (默认: 50)
- sort: 排序方式 (newest, oldest, popular, quality)
- event_type: 事件类型过滤 (team_fight, roshan, gank, etc.)
- game_time: 游戏时间过滤 (秒)
- tier: 评论等级 (1-5)
```

### 创建评论
```http
POST /api/matches/:matchId/comments
Authorization: Bearer <token>
Content-Type: application/json

{
  "gameTime": 1200,
  "eventType": "team_fight",
  "content": "团战分析内容",
  "importance": 4,
  "tags": ["roshan", "smoke"],
  "position": "position_1"
}
```

### 更新评论
```http
PUT /api/comments/:commentId
Authorization: Bearer <token>
Content-Type: application/json

{
  "content": "更新后的内容",
  "importance": 5
}
```

### 删除评论
```http
DELETE /api/comments/:commentId
Authorization: Bearer <token>
```

### 点赞/踩评论
```http
POST /api/comments/:commentId/vote
Authorization: Bearer <token>
Content-Type: application/json

{
  "type": "like"  // like 或 dislike
}
```

## 专家标注 (Python后端)

### 获取专家标注
```http
GET /api/matches/:matchId/expert-annotations
Query参数:
- page: 页码 (默认: 1)
- limit: 每页数量 (默认: 20)
- expert_level: 专家等级过滤 (bronze, silver, gold, platinum, diamond)
- verified: 是否只显示认证专家 (true/false)
```

### 创建专家标注
```http
POST /api/matches/:matchId/expert-annotations
Authorization: Bearer <token>
Content-Type: application/json

{
  "timestamp": 1800,
  "analysis": "专业分析内容",
  "decisionContext": {
    "context": "决策上下文",
    "alternatives": ["选择1", "选择2"],
    "outcome": "结果验证"
  },
  "confidence": 0.85,
  "tags": ["strategy", "draft", "team_composition"]
}
```

### 获取专家列表
```http
GET /api/experts
Query参数:
- level: 专家等级 (bronze, silver, gold, platinum, diamond)
- specialization: 专业领域 (draft, strategy, mechanics, etc.)
- verified: 认证状态 (true/false)
- min_accuracy: 最低准确率 (0.0-1.0)
```

## 用户相关 (Python后端)

### 获取用户资料
```http
GET /api/users/:userId
```

### 更新用户资料
```http
PUT /api/users/profile
Authorization: Bearer <token>
Content-Type: application/json

{
  "nickname": "新昵称",
  "avatar": "avatar_url",
  "bio": "个人简介",
  "specialization": ["draft", "strategy"]
}
```

### 获取用户评论
```http
GET /api/users/:userId/comments
Query参数:
- page: 页码 (默认: 1)
- limit: 每页数量 (默认: 20)
- sort: 排序方式 (newest, oldest, popular)
```

### 获取用户专家标注
```http
GET /api/users/:userId/expert-annotations
Query参数:
- page: 页码 (默认: 1)
- limit: 每页数量 (默认: 20)
- verified: 是否只显示认证标注 (true/false)
```

### 获取用户学习进度
```http
GET /api/users/:userId/learning-progress
Authorization: Bearer <token>
```

### 更新学习进度
```http
POST /api/users/learning-progress
Authorization: Bearer <token>
Content-Type: application/json

{
  "content_id": 123,
  "progress": 0.75,
  "completed": false,
  "skill_assessments": {
    "draft_knowledge": 85,
    "mechanics": 90
  }
}
```

## 搜索和过滤 (Python后端)

### 全局搜索
```http
GET /api/search
Query参数:
- q: 搜索关键词
- type: 搜索类型 (matches, comments, users, experts)
- page: 页码 (默认: 1)
- limit: 每页数量 (默认: 20)
- time_range: 时间范围 (7d, 30d, 90d, 1y)
```

### 高级搜索
```http
POST /api/search/advanced
Content-Type: application/json

{
  "type": "matches",
  "filters": {
    "min_mmr": 5000,
    "league": "TI12",
    "duration_range": [1800, 3600],
    "patch": "7.34c",
    "region": "china"
  },
  "sort": "duration",
  "order": "desc",
  "page": 1,
  "limit": 50
}
```

## 数据导出 (Python后端)

### 导出比赛数据
```http
GET /api/matches/:matchId/export
Query参数:
- format: 导出格式 (json, csv, xml, xlsx)
- include: 包含数据类型 (comments, annotations, raw_data, statistics)
- language: 导出语言 (zh, en, ru)
```

### 批量导出统计数据
```http
POST /api/export/batch-statistics
Authorization: Bearer <token>
Content-Type: application/json

{
  "type": "hero_winrate",
  "filters": {
    "time_range": "30d",
    "tier": "pro"
  },
  "format": "csv"
}
```

## 统计分析API (Python后端)

### 英雄统计
```http
GET /api/stats/heroes/winrate-ranking
Query参数:
- time_range: 时间范围 (7d, 30d, 90d, 1y)
- tier: 段位 (all, immortal, divine, ancient, legend, archon, crusader, guardian, herald)
- limit: 返回数量 (默认: 50)
```

### 比赛统计
```http
GET /api/stats/matches/duration-distribution
Query参数:
- time_range: 时间范围
- tier: 段位
- patch: 游戏版本
```

### 选手统计
```http
GET /api/stats/players/kda-distribution
Query参数:
- position: 位置 (1-5)
- time_range: 时间范围
- min_matches: 最少比赛场次
```

### 实时数据
```http
GET /api/stats/realtime/summary
```

## AI分析API (Python后端)

### 请求AI分析
```http
POST /api/learning/ai-analysis
Authorization: Bearer <token>
Content-Type: application/json

{
  "targetId": 123456,
  "type": "match",
  "analysis_type": "strategy",
  "context": {
    "focus_areas": ["draft", "team_fight", "objective_control"]
  }
}
```

### 获取AI分析结果
```http
GET /api/learning/ai-analysis/:requestId
Authorization: Bearer <token>
```

### 获取AI分析状态
```http
GET /api/learning/ai-analysis/:requestId/status
Authorization: Bearer <token>
```

## 学习中心API (Python后端)

### 获取学习内容
```http
GET /api/learning/content
Query参数:
- category: 内容分类 (strategy, mechanics, draft, etc.)
- difficulty: 难度等级 (beginner, intermediate, advanced)
- language: 语言 (zh, en, ru)
```

### 获取学习内容详情
```http
GET /api/learning/content/:contentId
```

### 更新学习进度
```http
POST /api/learning/progress
Authorization: Bearer <token>
Content-Type: application/json

{
  "content_id": 123,
  "progress": 0.75,
  "completed": false,
  "skill_assessments": {
    "draft_knowledge": 85,
    "mechanics": 90,
    "game_sense": 78
  }
}
```

## WebSocket事件

### 实时更新
连接: `ws://localhost:5000` (Python后端) / `ws://localhost:3001` (Node.js)

#### 事件类型
- `match:update` - 比赛更新
- `comment:new` - 新评论
- `comment:update` - 评论更新
- `expert:annotation` - 新专家标注
- `ai:analysis:complete` - AI分析完成
- `learning:progress` - 学习进度更新
- `user:notification` - 用户通知

### 订阅示例
```javascript
const socket = new WebSocket('ws://localhost:5000');

socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  switch(data.type) {
    case 'match:update':
      handleMatchUpdate(data.payload);
      break;
    case 'comment:new':
      handleNewComment(data.payload);
      break;
    case 'ai:analysis:complete':
      handleAIAnalysisComplete(data.payload);
      break;
  }
};

// 订阅特定比赛
socket.send(JSON.stringify({
  type: 'subscribe',
  channel: 'match:12345'
}));
```

## 错误处理

### 错误响应格式
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数验证失败",
    "details": {
      "field": "gameTime",
      "issue": "必须是正整数"
    }
  }
}
```

### 错误码说明
- `400` Bad Request - 请求参数错误
- `401` Unauthorized - 未认证
- `403` Forbidden - 权限不足
- `404` Not Found - 资源不存在
- `429` Too Many Requests - 请求频率限制
- `500` Internal Server Error - 服务器错误

## 速率限制

- 未认证用户: 100请求/15分钟
- 认证用户: 1000请求/15分钟
- 专家用户: 5000请求/15分钟

## 分页信息

所有列表API都支持分页:
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "pages": 5
  }
}
```