# API文档

## 基础信息
- 基础URL: `http://localhost:3001/api`
- 认证方式: JWT Token
- 数据格式: JSON

## 认证

### Steam登录
```http
GET /api/auth/steam
```

### 获取用户信息
```http
GET /api/auth/user
Authorization: Bearer <token>
```

## 比赛相关

### 获取比赛列表
```http
GET /api/matches
Query参数:
- page: 页码 (默认: 1)
- limit: 每页数量 (默认: 20)
- tier: 比赛等级 (pro, premium, amateur)
- start_time: 开始时间戳
- end_time: 结束时间戳
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
```

## 评论系统

### 获取比赛评论
```http
GET /api/matches/:matchId/comments
Query参数:
- page: 页码 (默认: 1)
- limit: 每页数量 (默认: 50)
- sort: 排序方式 (newest, oldest, popular, quality)
- event_type: 事件类型过滤
- game_time: 游戏时间过滤
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
  "tags": ["roshan", "smoke"]
}
```

### 更新评论
```http
PUT /api/comments/:commentId
Authorization: Bearer <token>
```

### 删除评论
```http
DELETE /api/comments/:commentId
Authorization: Bearer <token>
```

## 专家标注

### 获取专家标注
```http
GET /api/matches/:matchId/expert-annotations
```

### 创建专家标注
```http
POST /api/matches/:matchId/expert-annotations
Authorization: Bearer <token>

{
  "timestamp": 1800,
  "analysis": "专业分析内容",
  "decisionContext": {
    "context": "决策上下文",
    "alternatives": ["选择1", "选择2"],
    "outcome": "结果验证"
  }
}
```

## 用户相关

### 获取用户资料
```http
GET /api/users/:userId
```

### 更新用户资料
```http
PUT /api/users/profile
Authorization: Bearer <token>
```

### 获取用户评论
```http
GET /api/users/:userId/comments
```

### 获取用户专家标注
```http
GET /api/users/:userId/expert-annotations
```

## 搜索和过滤

### 全局搜索
```http
GET /api/search
Query参数:
- q: 搜索关键词
- type: 搜索类型 (matches, comments, users)
- page: 页码
- limit: 每页数量
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
    "duration_range": [1800, 3600]
  },
  "sort": "duration",
  "order": "desc"
}
```

## 数据导出

### 导出比赛数据
```http
GET /api/matches/:matchId/export
Query参数:
- format: 导出格式 (json, csv, xml)
- include: 包含数据类型 (comments, annotations, raw_data)
```

## WebSocket事件

### 实时更新
连接: `ws://localhost:3001`

#### 事件类型
- `match:update` - 比赛更新
- `comment:new` - 新评论
- `comment:update` - 评论更新
- `expert:annotation` - 新专家标注

### 订阅示例
```javascript
const socket = new WebSocket('ws://localhost:3001');

socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  switch(data.type) {
    case 'match:update':
      handleMatchUpdate(data.payload);
      break;
    case 'comment:new':
      handleNewComment(data.payload);
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