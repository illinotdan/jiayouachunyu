# 刀塔情书 - Dota2专业解析社区

每个人优质意见都是宝贵的，这是我们给西恩刀塔的情书

## 项目简介

这是一个专为Dota2社区打造的专业比赛分析平台，通过资深解说的专业视角、社区智慧和AI技术，提供超越传统数据统计的深度游戏理解。我们致力于让每个玩家的声音都被听见，让每份热爱都能找到共鸣。

## 技术栈

### 前端
- **HTML5 + CSS3 + JavaScript ES6+** - 原生Web技术
- **Tailwind CSS** - 样式框架
- **ECharts + D3.js** - 数据可视化
- **原生Web Components** - 组件化开发

### 后端
- **Python Flask 3.0** - Web框架
- **PostgreSQL** - 主数据库
- **Redis** - 缓存层
- **SQLAlchemy** - ORM工具
- **Celery** - 任务队列

### AI/ML
- **Python** - 机器学习
- **DeepSeek API** - 大语言模型集成
- **Transformers** - 预训练模型
- **PyTorch** - 深度学习框架

### 基础设施
- **Docker** - 容器化
- **Nginx** - 反向代理
- **Gunicorn** - WSGI服务器

## 项目结构

```
dota2-analytics-community/
├── frontend/                 # 原生HTML前端应用
│   ├── *.html              # 页面文件（index.html, matches.html等）
│   ├── css/                # 样式文件
│   ├── js/                 # JavaScript脚本
│   │   ├── main.js          # 主功能文件
│   │   ├── analytics.js    # 数据分析功能
│   │   ├── charts.js       # 图表管理器
│   │   └── api.js          # API接口封装
│   └── images/             # 静态资源
├── backend/                 # Python Flask后端API
│   ├── python/             # Python Flask应用
│   │   ├── app.py          # 主应用文件
│   │   ├── routes/         # API路由
│   │   ├── services/       # 业务逻辑
│   │   ├── models/         # 数据模型
│   │   └── config/         # 配置文件
│   └── package.json        # Node.js依赖（已弃用）
├── ai-models/              # AI模型相关
│   ├── scripts/            # 训练脚本和工具
│   │   ├── ai_assistant_demo.py    # AI助手演示
│   │   ├── training_data_generator.py # 训练数据生成
│   │   └── deepseek_processor.py   # DeepSeek格式处理
│   ├── configs/            # 模型配置
│   ├── data/               # 训练数据
│   └── notebooks/          # Jupyter笔记本
├── database/               # 数据库相关
│   ├── migrations/        # 迁移文件
│   ├── schemas/           # 数据库模式
│   └── seeds/             # 种子数据
├── infrastructure/        # 基础设施配置
│   ├── docker/           # Docker配置
│   ├── nginx/            # Nginx配置
│   └── kubernetes/       # K8s配置
├── docs/                # 项目文档
├── scripts/             # 自动化脚本
└── deployment/          # 部署配置
```

## 快速开始

### 前置要求
- Python 3.9+
- PostgreSQL 14+
- Redis 6+
- Node.js 16+（仅用于开发工具）

### 安装步骤

1. **克隆项目**
   ```bash
   git clone [repository-url]
   cd dota2-analytics-community
   ```

2. **安装Python后端依赖**
   ```bash
   cd backend/python
   pip install -r requirements.txt
   ```

3. **环境配置**
   ```bash
   # 复制环境变量模板
   cp .env.example .env
   
   # 编辑 .env 文件，填入实际配置
   # 配置数据库连接、API密钥等
   ```

4. **数据库设置**
   ```bash
   # 初始化数据库
   python manage.py db init
   python manage.py db migrate
   python manage.py db upgrade
   
   # 填充种子数据（可选）
   python manage.py seed
   ```

5. **启动开发服务器**
   ```bash
   # 启动Flask后端
   python run.py
   
   # 或使用Gunicorn（生产环境）
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

### 访问应用
- 前端: http://localhost:5000
- 后端API: http://localhost:5000/api
- API文档: http://localhost:5000/api/docs
- 数据分析: http://localhost:5000/analytics.html

## 开发指南

### 代码规范
- **Python**: 使用Black进行代码格式化，Flake8进行代码检查
- **JavaScript**: 使用ESLint进行代码检查
- **提交前**: 必须运行测试和代码质量检查

### 分支策略
- `main` - 生产分支
- `develop` - 开发分支
- `feature/*` - 功能分支
- `hotfix/*` - 热修复分支

### 提交规范
使用Conventional Commits规范：
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具

### Python代码规范
```bash
# 格式化代码
black backend/python/

# 代码检查
flake8 backend/python/

# 运行测试
pytest backend/python/tests/
```

## AI智能助手

本项目集成了基于DeepSeek的AI智能助手，提供以下功能：

### 核心能力
- **比赛分析**: 基于多源数据的智能比赛洞察
- **学习推荐**: 个性化学习内容推荐
- **社区问答**: 智能回答用户问题
- **数据解读**: 专业的数据分析和建议

### 训练数据
- **多数据源整合**: OpenDota + STRATZ + Liquipedia + 社区评论
- **T-1数据策略**: 每天同步前一天的比赛数据
- **社区智慧**: 整合用户精选评论和点赞数据

### 使用示例
```python
from ai_assistant_demo import Dota2AIAssistant

# 创建AI助手
assistant = Dota2AIAssistant(api_key="your-api-key")

# 分析比赛
analysis = assistant.analyze_match("1234567890", match_data)

# 获取学习推荐
recommendations = assistant.get_learning_recommendations("intermediate")

# 回答社区问题
answer = assistant.answer_community_question("如何提高补刀效率？")
```

更多详情查看 `ai-models/README.md`

## 部署

### 开发环境
```bash
# 启动Flask开发服务器
cd backend/python
python run.py
```

### 生产环境
```bash
# 使用Gunicorn启动生产服务器
cd backend/python
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 app:app

# 或使用Docker
docker-compose -f infrastructure/docker/docker-compose.yml up -d
```

### Docker部署
```bash
# 构建镜像
cd infrastructure/docker
docker-compose build

# 启动服务
docker-compose up -d

# 查看状态
docker-compose ps
```

### 环境变量配置
```bash
# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/dota2_analytics

# Redis配置
REDIS_URL=redis://localhost:6379/0

# API密钥
DEEPSEEK_API_KEY=your-deepseek-api-key
OPENDOTA_API_KEY=your-opendota-api-key
STRATZ_API_KEY=your-stratz-api-key

# 其他配置
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
```

## 项目进度总览

### 📊 整体完成度: **约35%**

> ⚠️ **重要提示**: 本项目目前处于早期开发阶段，核心功能框架已搭建，但许多细节功能仍在开发中。以下进度表展示了各模块的具体完成情况。

### 🔍 详细进度表

| 模块类别 | 子模块 | 完成状态 | 完成度 | 备注 |
|---------|--------|----------|--------|------|
| **🏗️ 基础架构** | 项目结构搭建 | ✅ 完成 | 100% | 前后端分离架构已确立 |
| | 开发环境配置 | ✅ 完成 | 90% | Docker配置基本完成 |
| | 数据库设计 | ⚠️ 部分 | 60% | 核心表结构完成，需优化 |
| | API接口框架 | ✅ 完成 | 85% | Flask路由和中间件就绪 |
| **🎯 数据层** | 多源数据获取 | ✅ 完成 | 80% | OpenDota/STRATZ/Liquipedia API集成 |
| | 数据同步机制 | ⚠️ 部分 | 50% | T-1策略框架搭建完成 |
| | 数据清洗处理 | ⚠️ 部分 | 40% | 基础数据清洗逻辑实现 |
| | 数据存储优化 | ❌ 未开始 | 10% | 仅基础存储，需性能优化 |
| **📊 统计分析** | 基础统计功能 | ⚠️ 部分 | 45% | 英雄胜率、KDA等基础统计 |
| | 实时数据更新 | ❌ 未开始 | 20% | WebSocket框架搭建 |
| | 数据可视化 | ⚠️ 部分 | 35% | ECharts基础图表实现 |
| **🤖 AI智能助手** | DeepSeek API集成 | ✅ 完成 | 75% | 基础API调用功能就绪 |
| | 训练数据生成 | ⚠️ 部分 | 30% | 数据格式处理脚本完成 |
| | AI模型训练 | ❌ 未开始 | 0% | 等待训练数据积累 |
| | 智能推荐算法 | ❌ 未开始 | 10% | 算法原型设计阶段 |
| **👥 社区功能** | 用户注册登录 | ⚠️ 部分 | 40% | 基础JWT认证实现 |
| | 比赛讨论系统 | ⚠️ 部分 | 25% | 评论功能基础框架 |
| | 点赞收藏功能 | ❌ 未开始 | 15% | 数据库设计完成 |
| | 内容审核机制 | ❌ 未开始 | 0% | 待设计 |
| **📱 前端界面** | 响应式布局 | ✅ 完成 | 80% | Tailwind CSS框架应用 |
| | 页面基础结构 | ⚠️ 部分 | 60% | 主要页面HTML完成 |
| | 交互功能实现 | ⚠️ 部分 | 35% | JavaScript基础交互完成 |
| | 移动端适配 | ⚠️ 部分 | 50% | 基础适配完成 |
| **🔧 运维部署** | Docker容器化 | ✅ 完成 | 85% | 基础Dockerfile完成 |
| | 生产环境部署 | ⚠️ 部分 | 30% | Gunicorn配置完成 |
| | 监控告警 | ❌ 未开始 | 5% | 日志系统基础搭建 |
| | 自动化测试 | ❌ 未开始 | 10% | 测试框架选择完成 |

### 🎯 下一阶段重点 (近期目标)

#### 🚨 高优先级 (计划2-3周内完成)
1. **数据存储优化** - 完成数据库索引优化和查询性能调优
2. **用户认证系统** - 完善注册登录流程，增加密码重置功能
3. **基础社区功能** - 实现比赛评论和专家观点展示

#### ⚡ 中优先级 (计划1-2个月内完成)
1. **高级统计分析** - 实现英雄搭配分析、胜率预测等算法
2. **AI训练数据积累** - 收集和整理足够的训练数据样本
3. **实时数据更新** - 完善WebSocket实时推送机制

#### 🔮 长期规划 (3-6个月展望)
1. **AI模型训练** - 基于积累的数据训练专属Dota2分析模型
2. **智能推荐系统** - 实现个性化内容推荐算法
3. **移动端APP** - 开发配套的移动应用

### 💡 当前可用功能

虽然项目整体完成度为35%，但以下功能已经可以体验：

✅ **立即体验**:
- 基础数据展示和统计图表
- 简单的比赛列表和详情查看
- AI助手基础问答功能（需要API密钥）
- 响应式网页界面浏览

⚠️ **体验限制**:
- 数据更新可能有1天延迟（T-1策略）
- 用户功能需要注册登录（待完善）
- AI分析功能依赖外部API配额
- 部分高级功能仍在开发中

---

## 核心功能规划

### 🎯 数据分析
- **多源数据整合**: OpenDota + STRATZ + Liquipedia
- **T-1数据策略**: 每日凌晨同步前一天数据
- **统计分析**: 英雄胜率、比赛时长、KDA分布等
- **可视化展示**: ECharts图表、交互式控制面板

### 🤖 AI智能助手
- **比赛分析**: 基于多源数据的深度洞察
- **学习推荐**: 个性化内容推荐
- **社区问答**: 智能回答用户问题
- **训练数据生成**: 自动化的AI训练数据准备

### 👥 社区功能
- **比赛讨论**: 用户可参与比赛分析和讨论
- **技术交流**: 分享游戏技巧和心得
- **学习中心**: 新手指导和进阶教程
- **专家观点**: 专业解说和分析师观点

### 📱 响应式设计
- **移动端适配**: 完美支持手机和平板
- **现代UI**: Tailwind CSS + Dota2主题色彩
- **流畅交互**: 原生JavaScript优化性能

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 开发建议
- 遵循Python代码规范（PEP 8）
- 编写单元测试
- 更新相关文档
- 保持代码注释清晰

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系我们

- 项目维护: 刀塔情书团队.samchez
- 社区支持: 通过GitHub Issues
- 技术讨论: VX+：SuyzeGodai

---

**刀塔情书** - 每个人优质意见都是宝贵的，这是我们给西恩刀塔的情书 ❤️