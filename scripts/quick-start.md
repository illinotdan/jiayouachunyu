# 快速启动指南

## 环境要求
- Node.js 18+
- PostgreSQL 14+
- Redis 6+
- Docker (可选，用于容器化部署)

## 一键启动

### Windows
```bash
# 运行设置脚本
.\scripts\setup.bat

# 启动开发服务器
npm run dev
```

### macOS/Linux
```bash
# 运行设置脚本
chmod +x scripts/setup.sh
./scripts/setup.sh

# 启动开发服务器
npm run dev
```

## 手动启动步骤

### 1. 安装依赖
```bash
# 根目录依赖
npm install

# 前端依赖
cd frontend && npm install

# 后端依赖
cd ../backend && npm install
```

### 2. 配置环境变量
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入实际配置
# 必需配置：
# - DATABASE_URL
# - REDIS_URL
# - JWT_SECRET
```

### 3. 启动数据库
```bash
# 使用Docker启动PostgreSQL和Redis
docker-compose -f infrastructure/docker/docker-compose.yml up postgres redis -d

# 或者使用本地数据库
# 确保PostgreSQL和Redis已安装并运行
```

### 4. 数据库初始化
```bash
# 运行数据库迁移
cd backend
npx prisma migrate dev

# 种子数据（可选）
npm run db:seed
```

### 5. 启动应用
```bash
# 从项目根目录启动所有服务
npm run dev

# 或者分别启动：
# 前端：cd frontend && npm run dev
# 后端：cd backend && npm run dev
```

## 访问地址
- **前端应用**: http://localhost:3000
- **后端API**: http://localhost:3001
- **健康检查**: http://localhost:3001/health
- **Prisma Studio**: http://localhost:5555 (运行 `npx prisma studio`)

## 常用命令

### 开发命令
```bash
# 启动所有服务
npm run dev

# 仅启动前端
cd frontend && npm run dev

# 仅启动后端
cd backend && npm run dev
```

### 数据库命令
```bash
# 迁移数据库
cd backend && npx prisma migrate dev

# 重置数据库
cd backend && npm run db:reset

# 查看数据库
cd backend && npx prisma studio
```

### Docker命令
```bash
# 启动所有服务
docker-compose -f infrastructure/docker/docker-compose.yml up -d

# 停止所有服务
docker-compose -f infrastructure/docker/docker-compose.yml down

# 查看日志
docker-compose -f infrastructure/docker/docker-compose.yml logs -f
```

## 故障排查

### 端口冲突
如果端口被占用，可以修改环境变量：
```bash
# 修改 .env 文件
PORT=3002
NEXT_PUBLIC_API_URL=http://localhost:3002
```

### 数据库连接失败
1. 检查PostgreSQL是否运行
2. 确认DATABASE_URL配置正确
3. 检查防火墙设置

### 依赖安装失败
1. 确保Node.js版本18+
2. 清理npm缓存：`npm cache clean --force`
3. 删除node_modules重新安装

## 开发工具

### 推荐VS Code扩展
- ESLint
- Prettier
- Prisma
- Thunder Client (API测试)
- Docker

### 调试
```bash
# 后端调试
cd backend && npm run dev:debug

# 前端调试
cd frontend && npm run dev:debug
```

## 下一步

启动成功后，你可以：
1. 注册新用户账户
2. 浏览比赛数据
3. 创建比赛分析
4. 参与社区讨论
5. 查看API文档：http://localhost:3001/api/docs

如需更多帮助，请查看：
- [部署指南](docs/DEPLOYMENT.md)
- [API文档](docs/API.md)
- [README.md](README.md)