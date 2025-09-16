# 部署指南

## 环境要求

### 开发环境
- Node.js 18+
- PostgreSQL 14+
- Redis 6+
- Python 3.9+ (AI模型)

### 生产环境
- Docker 20.10+
- Docker Compose 2.0+
- 域名和SSL证书
- 云服务提供商账户

## 本地开发部署

### 1. 环境准备
```bash
# 安装依赖
npm install
cd frontend && npm install
cd ../backend && npm install

# 复制环境变量
cp .env.example .env
# 编辑 .env 文件填入实际值
```

### 2. 数据库设置
```bash
# 启动PostgreSQL和Redis
docker-compose -f infrastructure/docker/docker-compose.yml up postgres redis -d

# 运行数据库迁移
cd backend
npx prisma migrate dev
npm run db:seed
```

### 3. 启动开发服务
```bash
# 从项目根目录启动所有服务
npm run dev
```

## Docker部署

### 1. 构建镜像
```bash
# 构建所有服务
docker-compose -f infrastructure/docker/docker-compose.yml build

# 或者分别构建
docker build -t dota2-frontend ./frontend
docker build -t dota2-backend ./backend
```

### 2. 启动服务
```bash
# 启动所有服务
docker-compose -f infrastructure/docker/docker-compose.yml up -d

# 查看日志
docker-compose -f infrastructure/docker/docker-compose.yml logs -f
```

### 3. 停止服务
```bash
docker-compose -f infrastructure/docker/docker-compose.yml down

# 同时删除卷
docker-compose -f infrastructure/docker/docker-compose.yml down -v
```

## 云部署

### AWS部署

#### 1. 准备AWS CLI
```bash
aws configure
```

#### 2. 使用ECS部署
```bash
# 构建并推送镜像到ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin [account-id].dkr.ecr.us-west-2.amazonaws.com

# 推送镜像
docker tag dota2-frontend:latest [account-id].dkr.ecr.us-west-2.amazonaws.com/dota2-frontend:latest
docker push [account-id].dkr.ecr.us-west-2.amazonaws.com/dota2-frontend:latest
```

#### 3. 使用Terraform部署
```bash
cd infrastructure/terraform/aws
terraform init
terraform plan
terraform apply
```

### 阿里云部署

#### 1. 准备阿里云CLI
```bash
aliyun configure
```

#### 2. 使用容器服务ACK
```bash
# 登录阿里云容器镜像服务
docker login --username=[username] registry.cn-hangzhou.aliyuncs.com

# 推送镜像
docker tag dota2-frontend:latest registry.cn-hangzhou.aliyuncs.com/[namespace]/dota2-frontend:latest
docker push registry.cn-hangzhou.aliyuncs.com/[namespace]/dota2-frontend:latest
```

### 腾讯云部署

#### 1. 使用TKE部署
```bash
# 登录腾讯云容器镜像服务
docker login --username=[username] ccr.ccs.tencentyun.com

# 推送镜像
docker tag dota2-frontend:latest ccr.ccs.tencentyun.com/[namespace]/dota2-frontend:latest
docker push ccr.ccs.tencentyun.com/[namespace]/dota2-frontend:latest
```

## Kubernetes部署

### 1. 创建命名空间
```bash
kubectl create namespace dota2-analytics
```

### 2. 部署应用
```bash
# 应用配置
kubectl apply -f infrastructure/kubernetes/

# 检查状态
kubectl get pods -n dota2-analytics
kubectl get services -n dota2-analytics
```

### 3. 配置Ingress
```bash
# 安装nginx-ingress
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

# 应用Ingress配置
kubectl apply -f infrastructure/kubernetes/ingress.yaml
```

## SSL证书配置

### 1. Let's Encrypt证书
```bash
# 使用cert-manager
kubectl apply -f infrastructure/kubernetes/cert-manager/
```

### 2. 阿里云SSL证书
```bash
# 在阿里云SSL证书服务申请证书
# 下载证书文件到 infrastructure/ssl/
```

## 监控和日志

### 1. 安装Prometheus
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack
```

### 2. 配置日志收集
```bash
# 使用ELK Stack
kubectl apply -f infrastructure/kubernetes/logging/
```

## 备份策略

### 1. 数据库备份
```bash
# 创建备份脚本
./scripts/backup-database.sh

# 设置定时任务
crontab -e
# 添加: 0 2 * * * /path/to/backup-database.sh
```

### 2. 应用数据备份
```bash
# 使用Velero进行K8s备份
velero install --provider aws --bucket [bucket-name] --secret-file ./credentials-velero
```

## 性能优化

### 1. CDN配置
- 使用阿里云CDN或腾讯云CDN
- 配置静态资源缓存策略

### 2. 数据库优化
```sql
-- 创建索引
CREATE INDEX idx_matches_start_time ON matches(start_time);
CREATE INDEX idx_comments_match_id ON comments(match_id);
CREATE INDEX idx_comments_user_id ON comments(user_id);
```

### 3. Redis缓存策略
```bash
# 设置合理的TTL
redis-cli CONFIG SET maxmemory 1gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

## 故障排查

### 1. 查看日志
```bash
# Docker日志
docker logs [container-name]

# Kubernetes日志
kubectl logs -f [pod-name] -n dota2-analytics
```

### 2. 健康检查
```bash
# 检查服务状态
curl http://localhost:3001/health

# 检查数据库连接
kubectl exec -it [postgres-pod] -- psql -U dota2_user -d dota2_analytics -c "SELECT 1"
```

### 3. 性能监控
- 使用Prometheus + Grafana
- 设置关键指标告警
- 监控API响应时间和错误率

## 安全建议

### 1. 网络安全
- 使用HTTPS
- 配置防火墙规则
- 限制数据库访问IP

### 2. 应用安全
- 定期更新依赖
- 使用Helmet.js
- 输入验证和SQL注入防护

### 3. 访问控制
- 实施RBAC
- 使用最小权限原则
- 定期审计用户权限

## 扩展部署

### 1. 水平扩展
```bash
# 扩展后端副本
kubectl scale deployment dota2-backend --replicas=3 -n dota2-analytics

# 扩展前端副本
kubectl scale deployment dota2-frontend --replicas=2 -n dota2-analytics
```

### 2. 自动扩缩容
```bash
# 配置HPA
kubectl apply -f infrastructure/kubernetes/hpa.yaml
```

### 3. 数据库读写分离
- 使用PostgreSQL主从复制
- 配置读写分离中间件
- 使用连接池优化性能