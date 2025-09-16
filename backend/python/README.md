# 刀塔解析 - Python Flask 后端

## 项目概述

这是刀塔解析平台的Python Flask后端实现，提供完整的RESTful API服务。

## 技术栈

- **框架**: Flask 3.0 + Flask扩展生态
- **数据库**: PostgreSQL 14+ (主数据库) + Redis (缓存)
- **ORM**: SQLAlchemy + Flask-SQLAlchemy
- **认证**: JWT (Flask-JWT-Extended)
- **任务队列**: Celery + Redis
- **API文档**: Swagger (Flasgger)
- **监控**: Prometheus + Sentry
- **部署**: Docker + Docker Compose

## 项目结构

```
backend/python/
├── app.py                  # Flask应用主文件
├── run.py                  # 开发环境启动脚本
├── wsgi.py                 # WSGI应用入口
├── requirements.txt        # Python依赖
├── Dockerfile             # Docker构建文件
├── docker-compose.yml     # Docker编排文件
├── env.example            # 环境变量示例
├── config/
│   ├── settings.py        # 应用配置
│   └── database.py        # 数据库配置
├── models/                # 数据模型
│   ├── user.py           # 用户相关模型
│   ├── match.py          # 比赛相关模型
│   ├── content.py        # 内容相关模型
│   ├── notification.py   # 通知模型
│   └── audit.py          # 审计日志模型
├── routes/               # API路由
│   ├── auth.py          # 认证API
│   ├── matches.py       # 比赛API
│   ├── experts.py       # 专家API
│   ├── discussions.py   # 讨论API
│   ├── stats.py         # 统计API
│   ├── upload.py        # 文件上传API
│   ├── notifications.py # 通知API
│   └── admin.py         # 管理员API
├── utils/               # 工具类
│   ├── response.py      # API响应工具
│   ├── decorators.py    # 装饰器
│   ├── validators.py    # 数据验证
│   ├── pagination.py    # 分页工具
│   ├── errors.py        # 错误处理
│   └── monitoring.py    # 系统监控
├── tasks/               # 后台任务
│   └── data_sync.py     # 数据同步任务
├── migrations/          # 数据库迁移
│   └── init_db.sql      # 初始化脚本
├── tests/               # 测试文件
└── logs/                # 日志文件
```

## 快速开始

### 1. 环境准备

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 数据库设置

```bash
# 安装PostgreSQL和Redis
# Ubuntu/Debian:
sudo apt install postgresql postgresql-contrib redis-server

# 创建数据库
sudo -u postgres createdb dota_analysis

# 复制环境配置
cp env.example .env
# 编辑.env文件，配置数据库连接等信息
```

### 3. 初始化数据库

```bash
# 初始化数据库
flask init-db

# 创建管理员用户
flask create-admin
```

### 4. 启动开发服务器

```bash
# 启动Flask应用
python run.py

# 启动Celery工作进程（新终端）
celery -A tasks.data_sync.celery worker --loglevel=info

# 启动Celery定时任务（新终端）
celery -A tasks.data_sync.celery beat --loglevel=info
```

### 5. 访问API

- **API文档**: http://localhost:5000/apidocs
- **健康检查**: http://localhost:5000/health
- **API信息**: http://localhost:5000/api/info

## Docker部署

### 开发环境

```bash
# 构建并启动所有服务
docker-compose up --build

# 后台运行
docker-compose up -d

# 查看日志
docker-compose logs -f api

# 停止服务
docker-compose down
```

### 生产环境

```bash
# 设置环境变量
export POSTGRES_PASSWORD=your_secure_password
export SECRET_KEY=your_secret_key
export JWT_SECRET_KEY=your_jwt_secret

# 启动生产环境
docker-compose -f docker-compose.prod.yml up -d
```

## API接口

### 认证接口
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/logout` - 用户登出
- `POST /api/auth/refresh` - 刷新Token
- `GET /api/auth/me` - 获取当前用户信息

### 比赛接口
- `GET /api/matches` - 获取比赛列表
- `GET /api/matches/{id}` - 获取比赛详情
- `GET /api/matches/live` - 获取直播比赛
- `POST /api/matches/{id}/predict` - 创建预测

### 专家接口
- `GET /api/experts` - 获取专家列表
- `GET /api/experts/{id}` - 获取专家详情
- `POST /api/experts/{id}/follow` - 关注/取消关注
- `POST /api/experts/apply` - 申请成为专家

### 社区接口
- `GET /api/discussions` - 获取讨论列表
- `POST /api/discussions` - 创建讨论
- `GET /api/discussions/{id}` - 获取讨论详情
- `POST /api/discussions/{id}/replies` - 回复讨论

### 统计接口
- `GET /api/stats/heroes` - 英雄统计
- `GET /api/stats/teams` - 战队统计
- `GET /api/stats/trends` - 趋势分析
- `GET /api/stats/predictions` - 预测统计

详细的API文档请参考 `../frontend_new/API_DOCUMENTATION.md`

## 数据库管理

### 迁移

```bash
# 生成迁移文件
flask db migrate -m "描述"

# 执行迁移
flask db upgrade

# 回滚迁移
flask db downgrade
```

### 数据管理

```bash
# 清理过期数据
flask cleanup-data

# 更新英雄统计
flask update-hero-stats

# 备份数据库
pg_dump dota_analysis > backup_$(date +%Y%m%d).sql
```

## 监控和日志

### 日志配置

日志文件位置：
- `logs/dota_analysis.log` - 应用日志
- `logs/celery.log` - Celery任务日志
- `logs/error.log` - 错误日志

### 监控指标

- **系统指标**: CPU、内存、磁盘使用率
- **应用指标**: 请求数量、响应时间、错误率
- **业务指标**: 用户活跃度、内容创建量、预测准确率

### Prometheus指标

访问 `http://localhost:5000/metrics` 获取Prometheus格式的监控指标。

## 性能优化

### 数据库优化

1. **索引优化**: 为常用查询创建合适的索引
2. **查询优化**: 使用explain分析慢查询
3. **连接池**: 配置合适的数据库连接池大小
4. **分区表**: 对大数据量表进行分区

### 缓存策略

1. **Redis缓存**: 缓存热门数据和计算结果
2. **应用缓存**: 使用Flask-Caching缓存函数结果
3. **CDN缓存**: 静态资源使用CDN加速

### 异步任务

使用Celery处理耗时操作：
- 数据同步
- 邮件发送
- 统计计算
- 文件处理

## 安全配置

### 认证安全

- JWT Token认证
- 密码哈希存储
- 会话管理
- 权限控制

### 数据安全

- SQL注入防护
- XSS防护
- CSRF防护
- 输入验证

### 系统安全

- 限流保护
- 文件上传安全
- 错误信息脱敏
- 审计日志

## 测试

```bash
# 运行所有测试
pytest

# 运行指定测试
pytest tests/test_auth.py

# 生成覆盖率报告
pytest --cov=. --cov-report=html
```

## 部署

### 生产环境部署

1. **服务器准备**
   ```bash
   # 安装Docker和Docker Compose
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   
   # 安装Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

2. **配置环境变量**
   ```bash
   # 创建生产环境配置
   cp env.example .env.production
   # 编辑配置文件
   ```

3. **启动服务**
   ```bash
   # 构建并启动
   docker-compose -f docker-compose.prod.yml up -d
   
   # 初始化数据库
   docker-compose exec api flask init-db
   
   # 创建管理员
   docker-compose exec api flask create-admin
   ```

### 监控部署

```bash
# 启动监控服务
docker-compose -f docker-compose.monitoring.yml up -d

# 访问监控面板
# Grafana: http://localhost:3001
# Prometheus: http://localhost:9090
# Flower: http://localhost:5555
```

## 故障排除

### 常见问题

1. **数据库连接失败**
   ```bash
   # 检查数据库状态
   docker-compose exec db pg_isready
   
   # 查看数据库日志
   docker-compose logs db
   ```

2. **Redis连接失败**
   ```bash
   # 测试Redis连接
   docker-compose exec redis redis-cli ping
   ```

3. **应用启动失败**
   ```bash
   # 查看应用日志
   docker-compose logs api
   
   # 进入容器调试
   docker-compose exec api bash
   ```

### 性能问题

1. **慢查询分析**
   ```sql
   -- 查看慢查询
   SELECT query, calls, total_time, mean_time 
   FROM pg_stat_statements 
   ORDER BY total_time DESC 
   LIMIT 10;
   ```

2. **内存使用分析**
   ```bash
   # 查看内存使用
   docker stats
   
   # 查看进程内存
   docker-compose exec api ps aux
   ```

## 开发指南

### 添加新的API接口

1. 在`models/`中定义数据模型
2. 在`routes/`中创建API路由
3. 添加数据验证和错误处理
4. 编写单元测试
5. 更新API文档

### 代码规范

```bash
# 代码格式化
black .

# 导入排序
isort .

# 代码检查
flake8 .

# 类型检查
mypy .
```

### 提交规范

- feat: 新功能
- fix: 修复bug
- docs: 文档更新
- style: 代码格式调整
- refactor: 代码重构
- test: 测试相关
- chore: 构建/工具相关

## 许可证

MIT License

## 联系方式

- 项目仓库: https://github.com/your-org/dota-analysis
- 问题反馈: https://github.com/your-org/dota-analysis/issues
- 邮箱: dev@dotaanalysis.com

---

*为每一个热爱Dota2的玩家而构建* 🎮
