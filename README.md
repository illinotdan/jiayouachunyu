# Dota2专业解析社区

基于专业解说视角的智能比赛分析平台

## 项目简介

这是一个专为Dota2社区打造的专业比赛分析平台，通过资深解说的专业视角、社区智慧和AI技术，提供超越传统数据统计的深度游戏理解。

## 技术栈

### 前端
- **Next.js 14** - React框架
- **TypeScript** - 类型安全
- **Tailwind CSS** - 样式框架
- **ShadCN/UI** - 组件库

### 后端
- **Node.js** + **Express.js** - 服务器
- **PostgreSQL** - 主数据库
- **Redis** - 缓存层
- **Prisma** - ORM工具

### AI/ML
- **Python** - 机器学习
- **PyTorch** - 深度学习框架
- **Transformers** - 预训练模型

### 基础设施
- **Docker** - 容器化
- **Kubernetes** - 容器编排
- **Terraform** - 基础设施即代码
- **Nginx** - 反向代理

## 项目结构

```
dota2-analytics-community/
├── frontend/                 # Next.js前端应用
│   ├── src/
│   │   ├── app/             # App Router
│   │   ├── components/      # 可复用组件
│   │   ├── lib/            # 工具库
│   │   └── types/          # TypeScript类型
│   ├── public/             # 静态资源
│   └── package.json
├── backend/                 # Express.js后端API
│   ├── src/
│   │   ├── controllers/    # 控制器
│   │   ├── models/        # 数据模型
│   │   ├── routes/        # 路由定义
│   │   ├── services/      # 业务逻辑
│   │   └── middleware/    # 中间件
│   └── package.json
├── database/               # 数据库相关
│   ├── migrations/        # 迁移文件
│   ├── seeds/            # 种子数据
│   └── schemas/          # 数据库模式
├── ai-models/             # AI模型相关
│   ├── training/          # 训练脚本
│   ├── models/           # 模型文件
│   └── data/             # 训练数据
├── infrastructure/        # 基础设施配置
│   ├── docker/           # Docker配置
│   ├── kubernetes/       # K8s配置
│   └── terraform/        # 基础设施代码
├── mobile-app/           # 移动应用
├── docs/                # 项目文档
├── scripts/             # 自动化脚本
├── tests/               # 测试文件
└── deployment/          # 部署配置
```

## 快速开始

### 前置要求
- Node.js 18+
- PostgreSQL 14+
- Redis 6+
- Python 3.9+

### 安装步骤

1. **克隆项目**
   ```bash
   git clone [repository-url]
   cd dota2-analytics-community
   ```

2. **安装依赖**
   ```bash
   # 安装根依赖
   npm install

   # 安装前端依赖
   cd frontend && npm install

   # 安装后端依赖
   cd ../backend && npm install
   ```

3. **环境配置**
   ```bash
   # 复制环境变量模板
   cp .env.example .env
   
   # 编辑 .env 文件，填入实际配置
   ```

4. **数据库设置**
   ```bash
   # 运行数据库迁移
   cd backend
   npx prisma migrate dev
   
   # 填充种子数据
   npm run db:seed
   ```

5. **启动开发服务器**
   ```bash
   # 从项目根目录启动所有服务
   npm run dev
   ```

### 访问应用
- 前端: http://localhost:3000
- 后端API: http://localhost:3001
- API文档: http://localhost:3001/api/docs

## 开发指南

### 代码规范
- 使用ESLint进行代码检查
- 使用Prettier进行代码格式化
- 提交前必须运行测试

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

## API文档

详细的API文档可在开发服务器运行时访问：
- Swagger UI: http://localhost:3001/api/docs
- OpenAPI JSON: http://localhost:3001/api/docs.json

## 部署

### 开发环境
```bash
npm run dev
```

### 生产环境
```bash
# 构建应用
npm run build

# 启动生产服务
npm start
```

### Docker部署
```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d
```

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系我们

- 邮箱: team@dota2analytics.com
- Discord: [加入社区](https://discord.gg/dota2analytics)
- 微信: Dota2Analytics