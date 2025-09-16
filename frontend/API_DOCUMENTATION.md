# 刀塔情书 - 后端API接口文档

## 概述

本文档详细描述了刀塔情书技术交流平台所需的所有后端API接口。平台专注于技术分析和学习交流，不涉及任何预测或博彩功能。所有接口都使用RESTful设计，支持JSON格式的请求和响应。

## 平台理念

> **专注技术分析，促进学习交流，提升游戏理解**
> 
> 我们致力于打造一个纯粹的技术讨论社区，帮助玩家深入理解Dota2的游戏机制和战术精髓。

### 基础信息

- **Base URL**: `https://api.dotaanalysis.com/v1`
- **认证方式**: JWT Token
- **内容类型**: `application/json`
- **字符编码**: UTF-8

### 通用响应格式

```json
{
  "success": true,
  "data": {},
  "message": "操作成功",
  "timestamp": 1703123456789,
  "version": "1.0.0"
}
```

### 错误响应格式

```json
{
  "success": false,
  "error": {
    "code": "INVALID_PARAMS",
    "message": "参数无效",
    "details": {}
  },
  "timestamp": 1703123456789
}
```

---

## 1. 认证相关接口

### 1.1 用户注册
- **接口**: `POST /auth/register`
- **描述**: 用户注册新账号

**请求参数**:
```json
{
  "username": "string, required, 3-20字符",
  "email": "string, required, 有效邮箱格式",
  "password": "string, required, 6-50字符",
  "confirmPassword": "string, required, 必须与password一致"
}
```

**响应数据**:
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "number",
      "username": "string",
      "email": "string",
      "avatar": "string, 头像URL",
      "createdAt": "string, ISO日期"
    },
    "token": "string, JWT token",
    "expiresIn": "number, 过期时间戳"
  }
}
```

### 1.2 用户登录
- **接口**: `POST /auth/login`
- **描述**: 用户登录

**请求参数**:
```json
{
  "email": "string, required",
  "password": "string, required"
}
```

**响应数据**:
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "number",
      "username": "string",
      "email": "string",
      "avatar": "string",
      "role": "string, user|expert|admin",
      "tier": "string, bronze|silver|gold|platinum|diamond",
      "verified": "boolean",
      "reputation": "number",
      "lastLoginAt": "string, ISO日期"
    },
    "token": "string",
    "expiresIn": "number"
  }
}
```

### 1.3 Steam登录
- **接口**: `GET /auth/steam`
- **描述**: Steam OAuth登录重定向

### 1.4 Steam登录回调
- **接口**: `GET /auth/steam/callback`
- **描述**: Steam登录回调处理

### 1.5 登出
- **接口**: `POST /auth/logout`
- **描述**: 用户登出
- **认证**: 需要Token

### 1.6 刷新Token
- **接口**: `POST /auth/refresh`
- **描述**: 刷新访问令牌

---

## 2. 比赛相关接口

### 2.1 获取比赛列表
- **接口**: `GET /matches`
- **描述**: 获取比赛列表，支持筛选和分页

**查询参数**:
```
page: number, 页码, 默认1
pageSize: number, 每页数量, 默认12, 最大50
status: string, 比赛状态 (live|upcoming|finished)
league: string, 联赛筛选
team: string, 队伍名称筛选
dateFrom: string, 开始日期 (YYYY-MM-DD)
dateTo: string, 结束日期 (YYYY-MM-DD)
sort: string, 排序方式 (time_desc|time_asc|views_desc)
```

**响应数据**:
```json
{
  "success": true,
  "data": {
    "matches": [
      {
        "id": "string",
        "league": {
          "id": "number",
          "name": "string",
          "tier": "number, 1-3",
          "logo": "string, URL"
        },
        "radiant": {
          "id": "number",
          "name": "string",
          "tag": "string",
          "logo": "string, URL",
          "score": "number"
        },
        "dire": {
          "id": "number", 
          "name": "string",
          "tag": "string",
          "logo": "string, URL",
          "score": "number"
        },
        "duration": "number, 秒数",
        "startTime": "string, ISO日期",
        "endTime": "string, ISO日期",
        "status": "string, live|upcoming|finished",
        "radiantWin": "boolean|null",
        "analysisCount": "number",
        "expertReviews": "number",
        "viewCount": "number",
        "commentCount": "number"
      }
    ],
    "pagination": {
      "page": "number",
      "pageSize": "number", 
      "total": "number",
      "totalPages": "number"
    }
  }
}
```

### 2.2 获取比赛详情
- **接口**: `GET /matches/{matchId}`
- **描述**: 获取指定比赛的详细信息

**响应数据**:
```json
{
  "success": true,
  "data": {
    "match": {
      "id": "string",
      "league": {
        "id": "number",
        "name": "string",
        "tier": "number",
        "logo": "string"
      },
      "radiant": {
        "id": "number",
        "name": "string", 
        "tag": "string",
        "logo": "string",
        "score": "number"
      },
      "dire": {
        "id": "number",
        "name": "string",
        "tag": "string", 
        "logo": "string",
        "score": "number"
      },
      "duration": "number",
      "startTime": "string",
      "endTime": "string",
      "status": "string",
      "radiantWin": "boolean|null",
      "players": {
        "radiant": [
          {
            "accountId": "string",
            "name": "string",
            "hero": {
              "id": "number",
              "name": "string",
              "displayName": "string",
              "imageUrl": "string"
            },
            "kills": "number",
            "deaths": "number", 
            "assists": "number",
            "netWorth": "number",
            "gpm": "number",
            "xpm": "number",
            "items": ["number"],
            "level": "number"
          }
        ],
        "dire": "array, 同radiant结构"
      },
      "analysis": {
        "keyMoments": [
          {
            "time": "string, MM:SS",
            "event": "string",
            "description": "string"
          }
        ],
        "mvp": "string, 玩家名称",
        "turningPoint": "string",
        "prediction": {
          "confidence": "number, 0-100",
          "reasoning": "string"
        }
      },
      "stats": {
        "totalKills": "number",
        "gameMode": "string",
        "patch": "string",
        "region": "string"
      }
    }
  }
}
```

### 2.3 获取实时比赛
- **接口**: `GET /matches/live`
- **描述**: 获取当前正在进行的比赛

### 2.4 获取比赛统计
- **接口**: `GET /matches/{matchId}/stats`
- **描述**: 获取比赛的详细统计数据

---

## 3. 专家相关接口

### 3.1 获取专家列表
- **接口**: `GET /experts`
- **描述**: 获取专家列表

**查询参数**:
```
page: number, 页码
pageSize: number, 每页数量
tier: string, 专家等级 (diamond|platinum|gold|silver|bronze)
expertise: string, 专业领域筛选
sort: string, 排序 (accuracy_desc|followers_desc|articles_desc)
search: string, 搜索关键词
```

**响应数据**:
```json
{
  "success": true,
  "data": {
    "experts": [
      {
        "id": "number",
        "name": "string",
        "title": "string",
        "avatar": "string, URL",
        "tier": "string",
        "expertise": ["string"],
        "followers": "number",
        "articles": "number", 
        "accuracy": "number, 0-100",
        "bio": "string",
        "verified": "boolean",
        "joinDate": "string, ISO日期",
        "lastActive": "string, ISO日期",
        "reputation": "number"
      }
    ],
    "pagination": {
      "page": "number",
      "pageSize": "number",
      "total": "number", 
      "totalPages": "number"
    }
  }
}
```

### 3.2 获取专家详情
- **接口**: `GET /experts/{expertId}`
- **描述**: 获取专家详细信息

**响应数据**:
```json
{
  "success": true,
  "data": {
    "expert": {
      "id": "number",
      "name": "string",
      "title": "string",
      "avatar": "string",
      "tier": "string",
      "expertise": ["string"],
      "followers": "number",
      "following": "number",
      "articles": "number",
      "accuracy": "number",
      "bio": "string",
      "verified": "boolean",
      "joinDate": "string",
      "lastActive": "string",
      "reputation": "number",
      "achievements": ["string"],
      "socialLinks": {
        "twitter": "string",
        "youtube": "string", 
        "twitch": "string"
      },
      "stats": {
        "totalPredictions": "number",
        "correctPredictions": "number",
        "totalViews": "number",
        "totalLikes": "number"
      }
    }
  }
}
```

### 3.3 获取专家文章
- **接口**: `GET /experts/{expertId}/articles`
- **描述**: 获取专家发表的文章列表

### 3.4 获取专家预测记录
- **接口**: `GET /experts/{expertId}/predictions`
- **描述**: 获取专家的预测记录

### 3.5 关注/取消关注专家
- **接口**: `POST /experts/{expertId}/follow`
- **描述**: 关注或取消关注专家
- **认证**: 需要Token

---

## 4. 社区相关接口

### 4.1 获取讨论列表
- **接口**: `GET /discussions`
- **描述**: 获取社区讨论列表

**查询参数**:
```
page: number, 页码
pageSize: number, 每页数量
category: string, 分类 (analysis|prediction|strategy|news)
sort: string, 排序 (latest|hot|top)
search: string, 搜索关键词
```

**响应数据**:
```json
{
  "success": true,
  "data": {
    "discussions": [
      {
        "id": "number",
        "title": "string",
        "content": "string, 内容摘要",
        "author": {
          "id": "number",
          "name": "string", 
          "avatar": "string",
          "tier": "string",
          "reputation": "number"
        },
        "category": "string",
        "tags": ["string"],
        "createdAt": "string",
        "updatedAt": "string",
        "replies": "number",
        "views": "number",
        "likes": "number",
        "lastActivity": "string",
        "isHot": "boolean",
        "isPinned": "boolean"
      }
    ],
    "pagination": {
      "page": "number",
      "pageSize": "number",
      "total": "number",
      "totalPages": "number"
    }
  }
}
```

### 4.2 获取讨论详情
- **接口**: `GET /discussions/{discussionId}`
- **描述**: 获取讨论详细内容和回复

**响应数据**:
```json
{
  "success": true,
  "data": {
    "discussion": {
      "id": "number",
      "title": "string",
      "content": "string, 完整内容",
      "author": {
        "id": "number",
        "name": "string",
        "avatar": "string", 
        "tier": "string",
        "reputation": "number"
      },
      "category": "string",
      "tags": ["string"],
      "createdAt": "string",
      "updatedAt": "string",
      "views": "number",
      "likes": "number",
      "isHot": "boolean",
      "isPinned": "boolean"
    },
    "replies": [
      {
        "id": "number",
        "content": "string",
        "author": {
          "id": "number",
          "name": "string",
          "avatar": "string",
          "tier": "string", 
          "reputation": "number"
        },
        "createdAt": "string",
        "likes": "number",
        "parentId": "number|null, 回复的回复ID"
      }
    ]
  }
}
```

### 4.3 创建讨论
- **接口**: `POST /discussions`
- **描述**: 发布新讨论
- **认证**: 需要Token

**请求参数**:
```json
{
  "title": "string, required, 5-200字符",
  "content": "string, required, 最少50字符",
  "category": "string, required",
  "tags": ["string, 最多5个标签"]
}
```

### 4.4 回复讨论
- **接口**: `POST /discussions/{discussionId}/replies`
- **描述**: 回复讨论
- **认证**: 需要Token

**请求参数**:
```json
{
  "content": "string, required, 最少10字符",
  "parentId": "number, optional, 回复的回复ID"
}
```

### 4.5 点赞/取消点赞
- **接口**: `POST /discussions/{discussionId}/like`
- **接口**: `POST /discussions/{discussionId}/replies/{replyId}/like`
- **描述**: 点赞或取消点赞
- **认证**: 需要Token

---

## 5. 数据统计接口

### 5.1 获取英雄统计
- **接口**: `GET /stats/heroes`
- **描述**: 获取英雄胜率统计

**查询参数**:
```
period: string, 时间周期 (week|month|all)
tier: string, 段位筛选 (pro|immortal|divine|all)
patch: string, 版本筛选
```

**响应数据**:
```json
{
  "success": true,
  "data": {
    "heroes": [
      {
        "id": "number",
        "name": "string",
        "displayName": "string",
        "primaryAttribute": "string",
        "roles": ["string"],
        "imageUrl": "string",
        "stats": {
          "winRate": "number, 0-100",
          "pickRate": "number, 0-100", 
          "banRate": "number, 0-100",
          "averageKDA": "number",
          "averageGPM": "number",
          "averageXPM": "number",
          "totalMatches": "number"
        }
      }
    ],
    "lastUpdated": "string, ISO日期"
  }
}
```

### 5.2 获取战队统计
- **接口**: `GET /stats/teams`
- **描述**: 获取战队排行和统计

**响应数据**:
```json
{
  "success": true,
  "data": {
    "teams": [
      {
        "id": "number",
        "name": "string",
        "tag": "string",
        "logo": "string",
        "region": "string",
        "stats": {
          "wins": "number",
          "losses": "number",
          "winRate": "number",
          "points": "number",
          "ranking": "number",
          "trend": "string, up|down|stable"
        },
        "recentMatches": "number",
        "lastMatchDate": "string"
      }
    ]
  }
}
```

### 5.3 获取趋势分析
- **接口**: `GET /stats/trends`
- **描述**: 获取版本趋势和Meta分析

### 5.4 获取预测统计
- **接口**: `GET /stats/predictions`
- **描述**: 获取平台预测统计数据

---

## 6. 搜索接口

### 6.1 全局搜索
- **接口**: `GET /search`
- **描述**: 全局搜索功能

**查询参数**:
```
q: string, required, 搜索关键词
type: string, 搜索类型 (all|matches|experts|discussions)
page: number, 页码
pageSize: number, 每页数量
```

**响应数据**:
```json
{
  "success": true,
  "data": {
    "results": {
      "matches": [
        {
          "id": "string",
          "title": "string",
          "type": "match",
          "relevance": "number, 0-100"
        }
      ],
      "experts": ["object"],
      "discussions": ["object"]
    },
    "total": "number",
    "searchTime": "number, 毫秒"
  }
}
```

---

## 7. 文件上传接口

### 7.1 上传头像
- **接口**: `POST /upload/avatar`
- **描述**: 上传用户头像
- **认证**: 需要Token
- **格式**: multipart/form-data

**请求参数**:
```
file: File, required, 图片文件 (jpg|png|gif, 最大2MB)
```

### 7.2 上传图片
- **接口**: `POST /upload/image`
- **描述**: 上传讨论中的图片
- **认证**: 需要Token

---

## 8. 通知接口

### 8.1 获取通知列表
- **接口**: `GET /notifications`
- **描述**: 获取用户通知
- **认证**: 需要Token

**响应数据**:
```json
{
  "success": true,
  "data": {
    "notifications": [
      {
        "id": "number",
        "type": "string, like|reply|follow|system",
        "title": "string",
        "content": "string",
        "data": "object, 相关数据",
        "read": "boolean",
        "createdAt": "string"
      }
    ],
    "unreadCount": "number"
  }
}
```

### 8.2 标记通知已读
- **接口**: `PUT /notifications/{notificationId}/read`
- **描述**: 标记通知为已读
- **认证**: 需要Token

---

## 9. 管理员接口

### 9.1 获取平台统计
- **接口**: `GET /admin/stats`
- **描述**: 获取平台整体统计数据
- **认证**: 需要管理员权限

### 9.2 专家认证管理
- **接口**: `GET /admin/expert-applications`
- **接口**: `PUT /admin/expert-applications/{applicationId}`
- **描述**: 专家认证申请管理

### 9.3 内容管理
- **接口**: `GET /admin/content/reports`
- **接口**: `PUT /admin/content/{contentId}/moderate`
- **描述**: 内容举报和审核管理

---

## 10. 学习相关接口

### 10.1 获取学习内容列表
- **接口**: `GET /learning/content`
- **描述**: 获取学习内容列表

**查询参数**:
```
page: number, 页码
pageSize: number, 每页数量
type: string, 内容类型 (guide|analysis|tips|qa)
difficulty: string, 难度级别 (beginner|intermediate|advanced|expert)
category: string, 分类筛选 (basics|heroes|tactics|advanced)
search: string, 搜索关键词
```

### 10.2 获取学习内容详情
- **接口**: `GET /learning/content/{contentId}`
- **描述**: 获取学习内容详细信息

### 10.3 AI分析请求
- **接口**: `POST /learning/ai-analysis`
- **描述**: 请求AI技术分析
- **认证**: 需要Token

**请求参数**:
```json
{
  "analysisType": "string, required, replay_analysis|match_analysis|skill_assessment",
  "inputData": "object, 分析输入数据",
  "fileUrl": "string, optional, 文件URL"
}
```

### 10.4 获取AI分析结果
- **接口**: `GET /learning/ai-analysis/{requestId}`
- **描述**: 获取AI分析结果
- **认证**: 需要Token

### 10.5 比赛讨论版接口
- **接口**: `GET /learning/match-discussions/{matchId}`
- **描述**: 获取指定比赛的讨论列表

**查询参数**:
```
category: string, 讨论分类 (general|tactics|highlights|learning|qa)
page: number, 页码
pageSize: number, 每页数量
```

### 10.6 创建比赛讨论
- **接口**: `POST /learning/match-discussions`
- **描述**: 在比赛讨论版发帖
- **认证**: 需要Token

**请求参数**:
```json
{
  "matchId": "string, required, 比赛ID",
  "title": "string, required, 5-200字符",
  "content": "string, required, 最少20字符",
  "category": "string, required, 讨论分类",
  "tags": ["string, 最多5个标签"],
  "isQuestion": "boolean, 是否为求助问题"
}
```

### 10.7 学习进度管理
- **接口**: `GET /learning/progress`
- **接口**: `POST /learning/content/{contentId}/progress`
- **描述**: 获取和更新用户学习进度
- **认证**: 需要Token

### 10.8 技能评估
- **接口**: `POST /learning/assessment`
- **描述**: 创建或更新用户技能评估
- **认证**: 需要Token

## 11. WebSocket接口

### 11.1 实时讨论
- **接口**: `WS /ws/discussions/{discussionId}`
- **描述**: 实时讨论功能

### 11.2 比赛讨论版
- **接口**: `WS /ws/match-discussions/{matchId}`
- **描述**: 比赛讨论版实时交流

---

## 错误代码说明

| 错误代码 | HTTP状态码 | 说明 |
|---------|-----------|------|
| INVALID_PARAMS | 400 | 请求参数无效 |
| UNAUTHORIZED | 401 | 未授权访问 |
| FORBIDDEN | 403 | 权限不足 |
| NOT_FOUND | 404 | 资源不存在 |
| CONFLICT | 409 | 资源冲突 |
| RATE_LIMITED | 429 | 请求频率限制 |
| INTERNAL_ERROR | 500 | 服务器内部错误 |
| SERVICE_UNAVAILABLE | 503 | 服务不可用 |

## 认证说明

### JWT Token格式
```
Authorization: Bearer <token>
```

### Token包含信息
```json
{
  "userId": "number",
  "username": "string",
  "role": "string",
  "tier": "string",
  "iat": "number, 签发时间",
  "exp": "number, 过期时间"
}
```

## 限流说明

- **普通用户**: 100 requests/minute
- **认证用户**: 200 requests/minute  
- **专家用户**: 500 requests/minute
- **管理员**: 1000 requests/minute

## 缓存策略

- **比赛列表**: 5分钟
- **比赛详情**: 1分钟（直播中）/ 30分钟（已结束）
- **专家列表**: 10分钟
- **统计数据**: 15分钟
- **讨论列表**: 2分钟

---

*该API文档会随着功能开发持续更新*
