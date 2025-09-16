# 统一数据服务整合指南

## 概述

本指南说明如何将用户提供的统一数据服务代码整合到现有Dota2战队分析系统中。

## 新增功能

### 1. 统一数据服务 (UnifiedDataService)
- **文件位置**: `backend/python/services/unified_data_service.py`
- **功能**: 整合OpenDota、STRATZ等多个数据源
- **特性**: 
  - 支持批量数据同步
  - 智能速率限制
  - 错误重试机制
  - 数据去重和更新

### 2. 测试数据生成器 (TestDataGenerator)
- **文件位置**: `backend/python/scripts/init_test_data.py`
- **功能**: 生成完整的测试数据集
- **包含数据**:
  - 英雄数据 (Heroes)
  - 物品数据 (Items)
  - 战队数据 (Teams)
  - 选手数据 (Players)
  - 联赛数据 (Leagues)
  - 比赛数据 (Matches)
  - 比赛选手数据 (Match Players)
  - Pick/Ban数据 (Match Drafts)
  - 比赛分析数据 (Match Analyses)

### 3. API路由 (Unified Data API)
- **文件位置**: `backend/python/routes/unified_data.py`
- **端点**:
  - `POST /api/unified/sync` - 触发数据同步
  - `GET /api/unified/status` - 获取同步状态
  - `GET /api/unified/history` - 获取同步历史
  - `GET /api/unified/quality` - 获取数据质量报告
  - `GET /api/unified/sources` - 获取数据源信息
  - `POST /api/unified/sync/t1` - 同步T-1数据

## 使用方法

### 1. 初始化测试数据

```bash
# 使用Flask命令
flask init-test-data

# 或者直接运行脚本
python scripts/setup_test_data.py
```

### 2. 同步外部数据

```bash
# 使用Flask命令
flask sync-data

# 或者调用API
curl -X POST http://localhost:5000/api/unified/sync \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. 查看同步状态

```bash
curl http://localhost:5000/api/unified/status
```

## 配置说明

### 环境变量
- `OPENDOTA_API_KEY`: OpenDota API密钥
- `STRATZ_API_KEY`: STRATZ API密钥
- `ALIYUN_ACCESS_KEY_ID`: 阿里云OSS访问密钥ID
- `ALIYUN_ACCESS_KEY_SECRET`: 阿里云OSS访问密钥
- `ALIYUN_OSS_ENDPOINT`: 阿里云OSS端点
- `ALIYUN_OSS_BUCKET`: 阿里云OSS存储桶

### 应用配置
- `DATA_SYNC_BATCH_SIZE`: 批处理大小 (默认: 100)
- `DATA_SYNC_RATE_LIMIT`: 速率限制 (默认: 50)
- `DATA_SYNC_MAX_RETRIES`: 最大重试次数 (默认: 3)
- `DATA_SYNC_TIMEOUT`: 超时时间 (默认: 30)

## 数据库集成

### 现有表结构支持
- 完全兼容现有的 `matches`, `heroes`, `items`, `teams`, `players` 等表
- 支持 `data_sources` 字段记录数据来源
- 保留所有现有的约束和索引

### 数据模型
- 使用现有的SQLAlchemy模型
- 支持所有现有的关系和约束
- 与现有的用户系统完全集成

## Celery任务集成

### 定时任务
- `sync_all_data`: 完整数据同步
- `sync_match_data`: 比赛数据同步
- 支持T-1时间策略

### 任务状态
- 实时任务状态监控
- 详细的错误日志
- 失败重试机制

## API认证

### JWT认证
- 所有API端点需要JWT认证
- 支持角色权限控制
- 审计日志记录

### 使用示例
```bash
# 获取JWT令牌
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'

# 使用令牌调用API
curl -X POST http://localhost:5000/api/unified/sync \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 错误处理

### 错误代码
- `SYNC_IN_PROGRESS`: 同步正在进行中
- `NO_DATA_SOURCES`: 没有可用的数据源
- `SYNC_FAILED`: 同步失败
- `INVALID_PARAMETERS`: 参数无效

### 错误响应格式
```json
{
  "success": false,
  "error": "同步失败",
  "error_code": "SYNC_FAILED",
  "details": "详细的错误信息"
}
```

## 性能优化

### 批处理
- 支持大批量数据处理
- 可配置的批处理大小
- 内存使用优化

### 缓存
- 智能数据缓存
- 减少重复API调用
- 提高响应速度

### 并发控制
- 速率限制保护
- 并发请求管理
- 错误重试机制

## 监控和日志

### 日志记录
- 详细的操作日志
- 性能指标记录
- 错误追踪

### 监控指标
- 同步成功率
- 数据质量指标
- API响应时间

## 扩展性

### 新数据源支持
- 易于添加新的数据源
- 插件式架构设计
- 统一的数据接口

### 自定义配置
- 灵活的配置选项
- 环境特定的设置
- 运行时参数调整

## 测试

### 单元测试
```bash
# 运行测试
python -m pytest tests/test_unified_data_service.py
```

### 集成测试
```bash
# 测试数据同步
flask init-test-data
flask sync-data
```

## 故障排除

### 常见问题
1. **API密钥无效**: 检查环境变量配置
2. **数据库连接失败**: 验证数据库配置
3. **同步超时**: 调整超时时间和批处理大小
4. **内存不足**: 减小批处理大小

### 调试模式
```bash
# 启用调试模式
export FLASK_ENV=development
flask run
```

## 更新日志

### v1.0.0 (当前版本)
- ✅ 统一数据服务集成
- ✅ 测试数据生成器
- ✅ API路由实现
- ✅ Celery任务集成
- ✅ 数据库兼容性
- ✅ JWT认证支持