# DEM解析功能使用指南

## 概述

DEM解析功能是Dota2战队分析系统的核心组件之一，它可以：

1. 从OpenDota API获取职业比赛的match_id列表
2. 下载对应的DEM回放文件
3. 使用Java clarity工具解析DEM文件为JSON格式
4. 将解析结果保存到阿里云OSS和数据库中

## 架构设计

### 核心组件

- **DEMParserService** (`services/dem_parser_service.py`): 核心解析服务
- **DEM解析API** (`routes/dem_parser.py`): HTTP API接口
- **异步任务** (`tasks/dem_parsing_tasks.py`): Celery异步任务处理
- **统一数据服务集成**: 与现有数据流程的整合

### 数据流程

```
OpenDota API → 获取职业比赛ID → 下载DEM文件 → Java解析 → JSON输出 → OSS存储 → 数据库保存
```

## 环境配置

### 必需的环境变量

```bash
# OpenDota API（可选，提高请求限制）
OPENDOTA_API_KEY=your_opendota_api_key

# 阿里云OSS配置
ALIYUN_ACCESS_KEY_ID=your_access_key_id
ALIYUN_ACCESS_KEY_SECRET=your_access_key_secret
ALIYUN_OSS_ENDPOINT=https://oss-cn-hangzhou.aliyuncs.com
ALIYUN_OSS_BUCKET=dota-analysis

# 数据同步配置
DATA_SYNC_BATCH_SIZE=100
DATA_SYNC_RATE_LIMIT=10
DATA_SYNC_MAX_RETRIES=3
DATA_SYNC_TIMEOUT=30
```

### Java环境要求

1. **Java版本**: Java 8 或更高版本
2. **解析工具**: `dem2json/java/clarity_dem2json.jar`
3. **内存要求**: 建议4GB+可用内存
4. **存储空间**: 每个DEM文件需要50-200MB临时存储

### Python依赖

```bash
pip install oss2 aiohttp playwright beautifulsoup4
```

## API使用

### 1. 启动完整工作流程

**POST** `/api/dem/start-workflow`

```json
{
    "days_back": 7,
    "limit": 50,
    "max_concurrent": 3
}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "workflow_steps": {
            "get_match_ids": true,
            "batch_process": true
        },
        "match_ids_count": 25,
        "batch_result": {
            "total_matches": 25,
            "successful": 20,
            "failed": 5
        }
    }
}
```

### 2. 处理单场比赛

**POST** `/api/dem/process-match/{match_id}`

```json
{
    "success": true,
    "data": {
        "match_id": 123456,
        "steps": {
            "get_download_url": true,
            "download_dem": true,
            "upload_to_oss": true,
            "parse_with_java": true,
            "save_to_db": true
        }
    }
}
```

### 3. 批量处理比赛

**POST** `/api/dem/batch-process`

```json
{
    "match_ids": [123456, 123457, 123458],
    "max_concurrent": 3
}
```

### 4. 获取职业比赛ID

**GET** `/api/dem/get-pro-matches?days_back=7&limit=100`

```json
{
    "success": true,
    "data": {
        "match_ids": [123456, 123457, 123458],
        "count": 3,
        "days_back": 7,
        "limit": 100
    }
}
```

### 5. 检查服务状态

**GET** `/api/dem/status`

```json
{
    "success": true,
    "data": {
        "service_available": true,
        "java_tool_available": true,
        "java_tool_path": "/path/to/clarity_dem2json.jar",
        "oss_configured": true,
        "work_directory": "/tmp/dem_parser",
        "work_directory_writable": true,
        "java_available": true,
        "java_version": "openjdk version \"11.0.16\""
    }
}
```

## 异步任务

### Celery任务

所有DEM解析操作都支持异步执行：

```python
from tasks.dem_parsing_tasks import parse_single_match_task, batch_parse_matches_task

# 异步解析单场比赛
task = parse_single_match_task.delay(match_id=123456, user_id=1)

# 异步批量解析
task = batch_parse_matches_task.delay(
    match_ids=[123456, 123457], 
    max_concurrent=2, 
    user_id=1
)

# 查询任务状态
from tasks.dem_parsing_tasks import get_task_status
status = get_task_status(task.id)
```

### 定时任务

系统自动配置了以下定时任务：

- **每小时**: 自动解析最新的职业比赛DEM文件
- **每天**: 清理7天前的临时文件

## 使用示例

### 1. 命令行演示

```bash
# 运行演示脚本
python scripts/demo_dem_parsing.py

# 执行真实解析（需要较长时间）
python scripts/demo_dem_parsing.py --real-demo
```

### 2. Python代码示例

```python
import asyncio
from services.dem_parser_service import DEMParserService

async def example_usage():
    # 初始化服务
    parser = DEMParserService()
    
    # 获取最近3天的职业比赛
    match_ids = await parser.get_professional_match_ids(days_back=3, limit=10)
    
    # 处理单场比赛
    if match_ids:
        result = await parser.process_single_match(match_ids[0])
        print(f"处理结果: {result}")
    
    # 批量处理
    batch_result = await parser.batch_process_matches(match_ids[:5], max_concurrent=2)
    print(f"批量处理: 成功{batch_result['successful']}场，失败{batch_result['failed']}场")

# 运行示例
asyncio.run(example_usage())
```

## 数据输出格式

### 解析后的JSON结构

```json
{
    "_metadata": {
        "match_id": 123456,
        "parsed_at": "2025-09-19T10:30:00Z",
        "execution_time": 180.5,
        "dem_file_path": "/tmp/dem_parser/match_123456.dem",
        "parser_version": "clarity_dem2json"
    },
    "match_info": {
        "duration": 2847,
        "winner": "radiant",
        "game_mode": 22
    },
    "players": [
        {
            "account_id": 123456789,
            "hero_id": 1,
            "slot": 0,
            "kills": 8,
            "deaths": 3,
            "assists": 15,
            "last_hits": 245,
            "denies": 12,
            "gold_per_min": 456,
            "xp_per_min": 589
        }
    ],
    "events": [
        {
            "type": "DOTA_COMBATLOG_KILL",
            "time": 125,
            "killer": 0,
            "victim": 5,
            "position": [1234, 5678]
        }
    ]
}
```

### 数据库存储

解析结果保存在 `match_analyses` 表中：

```sql
-- 查看DEM解析结果
SELECT 
    match_id,
    dem_parsed_at,
    JSON_EXTRACT(dem_data, '$._metadata.execution_time') as parse_time,
    JSON_EXTRACT(dem_data, '$.players') as player_data
FROM match_analyses 
WHERE dem_data IS NOT NULL;
```

## 性能优化

### 并发控制

- **默认并发数**: 2-3个任务同时执行
- **内存使用**: 每个任务约1-2GB内存
- **网络带宽**: 下载速度取决于网络条件

### 存储优化

- **临时文件**: 解析完成后自动清理
- **OSS存储**: 长期保存原始DEM和JSON文件
- **数据库**: 只存储元数据和关键统计信息

### 错误处理

- **自动重试**: 失败任务自动重试3次
- **超时控制**: 单个任务最长执行1小时
- **错误日志**: 详细记录所有错误信息

## 监控和维护

### 日志监控

```bash
# 查看DEM解析日志
tail -f logs/dota_analysis.log | grep "DEM"

# 查看Celery任务日志
tail -f logs/celery.log
```

### 健康检查

```bash
# 检查服务状态
curl http://localhost:5000/api/dem/status

# 检查活跃任务
curl http://localhost:5000/api/dem/tasks/active
```

### 清理维护

```bash
# 手动清理临时文件
python -c "
from tasks.dem_parsing_tasks import cleanup_old_dem_files_task
result = cleanup_old_dem_files_task.delay(days_old=7)
print(result.get())
"
```

## 故障排除

### 常见问题

1. **Java工具不存在**
   - 检查 `dem2json/java/clarity_dem2json.jar` 是否存在
   - 验证Java环境是否正确安装

2. **OSS上传失败**
   - 检查阿里云OSS配置是否正确
   - 验证网络连接和权限设置

3. **DEM下载失败**
   - 某些比赛可能不提供DEM文件
   - 检查网络连接和OpenDota服务状态

4. **内存不足**
   - 减少并发任务数量
   - 增加服务器内存配置

### 调试模式

```python
# 启用详细日志
import logging
logging.getLogger('services.dem_parser_service').setLevel(logging.DEBUG)

# 单步调试
parser = DEMParserService()
result = await parser.process_single_match(match_id, debug=True)
```

## 扩展开发

### 自定义解析器

```python
class CustomDEMParser(DEMParserService):
    def parse_dem_with_custom_tool(self, dem_file_path, match_id):
        # 实现自定义解析逻辑
        pass
```

### 新增数据源

```python
# 扩展获取比赛ID的方法
async def get_custom_match_ids(self):
    # 从其他数据源获取比赛ID
    pass
```

## 更新历史

- **v1.0** (2025-09-19): 初始版本，支持基本DEM解析功能
- 计划添加更多解析工具支持
- 计划添加实时解析功能
- 计划添加数据可视化界面

---

如有问题或建议，请联系开发团队或查看项目文档。
