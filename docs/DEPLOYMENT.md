# 部署指南

## 环境要求

### 开发环境
- Node.js 18+ 和 npm
- Python 3.9+ 和 pip
- PostgreSQL 14+
- Redis 6+
- Git
- Git LFS (用于AI模型文件)

### 生产环境
- Docker 20.10+
- Docker Compose 2.0+
- 域名和SSL证书
- 云服务提供商账户
- Kubernetes (可选，用于大规模部署)
- Git LFS (用于AI模型文件)
- GPU支持 (可选，用于AI模型加速)

### AI模型环境要求
- TensorFlow 2.8+ 或 PyTorch 1.12+
- CUDA 11.7+ (GPU加速)
- 模型文件存储空间: 2GB+
- 内存要求: 4GB+ (CPU模式) / 8GB+ (GPU模式)

## 本地开发部署

### 1. 克隆项目
```bash
git clone <repository-url>
cd dota2-analyzer
```

### 2. 环境准备
```bash
# 初始化Git LFS
git lfs install
git lfs pull

# 安装前端依赖
cd frontend
npm install

# 安装后端依赖
cd ../backend/nodejs
npm install

# 安装Python依赖
cd ../python
pip install -r requirements.txt

# 安装AI模型依赖
cd ../../ai-models
pip install -r requirements.txt
```

### 3. 数据库设置
```bash
# 创建数据库
createdb dota2_analyzer

# 运行Node.js后端迁移
cd ../backend/nodejs
npm run migrate

# 运行Python后端迁移
cd ../python
python manage.py migrate

# 导入初始数据
npm run seed
```

### 4. 配置环境变量
```bash
# 前端配置
cd ../../frontend
cp .env.example .env
# 编辑 .env 文件，设置相关配置

# Node.js后端配置
cd ../backend/nodejs
cp .env.example .env
# 编辑 .env 文件，设置数据库、Redis等配置

# Python后端配置
cd ../python
cp .env.example .env
# 编辑 .env 文件，设置数据库、AI模型等配置

# AI模型配置
cd ../../ai-models
cp .env.example .env
# 编辑 .env 文件，设置模型路径、GPU配置等
```

### 5. 下载AI模型
```bash
cd ai-models
python scripts/download_models.py
```

### 6. 启动服务
```bash
# 启动Node.js后端服务
cd ../backend/nodejs
npm run dev

# 启动Python后端服务
cd ../python
python app.py

# 启动前端服务
cd ../../frontend
npm run dev

# 启动AI模型服务
cd ../ai-models
python app.py

# 启动定时任务服务
cd ../backend/python
python scheduler.py
```

## Docker部署

### 1. 构建镜像
```bash
# 构建所有服务镜像
docker-compose build

# 构建特定服务
docker-compose build frontend
docker-compose build backend-nodejs
docker-compose build backend-python
docker-compose build ai-models
```

### 2. 启动服务
```bash
# 开发环境
docker-compose up -d

# 生产环境
docker-compose -f docker-compose.prod.yml up -d

# 仅启动基础设施服务
docker-compose -f infrastructure/docker/docker-compose.yml up -d postgres redis

# 启动特定服务
docker-compose up -d frontend
docker-compose up -d backend-nodejs
docker-compose up -d backend-python
docker-compose up -d ai-models
```

### 3. 停止服务
```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v

# 停止特定服务
docker-compose stop frontend
docker-compose stop backend-python
```

### 4. 查看日志
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend-python
docker-compose logs -f ai-models

# 查看特定服务最近100行日志
docker-compose logs --tail=100 ai-models
```

## 云部署

### AWS部署
1. 创建EC2实例 (推荐t3.large或更高配置)
2. 配置安全组 (开放端口: 80, 443, 5000, 3001)
3. 安装Docker和Docker Compose
4. 克隆项目代码
5. 配置环境变量
6. 运行部署脚本

```bash
# AWS部署脚本
#!/bin/bash
yum update -y
yum install -y docker docker-compose git
service docker start
usermod -a -G docker ec2-user

# 克隆代码
git clone <repository-url>
cd dota2-analyzer

# 配置环境变量
cp .env.example .env
# 编辑.env文件

# 启动服务
docker-compose -f docker-compose.prod.yml up -d
```

### 阿里云部署
1. 创建ECS实例 (推荐ecs.c5.large或更高配置)
2. 配置安全组规则
3. 安装Docker和Docker Compose
4. 克隆项目代码
5. 配置环境变量
6. 运行部署脚本

```bash
# 阿里云部署脚本
#!/bin/bash
yum update -y
yum install -y docker docker-compose git
systemctl start docker
systemctl enable docker

# 克隆代码
git clone <repository-url>
cd dota2-analyzer

# 配置环境变量
cp .env.example .env
# 编辑.env文件

# 启动服务
docker-compose -f docker-compose.prod.yml up -d
```

### 腾讯云部署
1. 创建CVM实例 (推荐标准型S4或更高配置)
2. 配置安全组规则
3. 安装Docker和Docker Compose
4. 克隆项目代码
5. 配置环境变量
6. 运行部署脚本

```bash
# 腾讯云部署脚本
#!/bin/bash
apt-get update
apt-get install -y docker.io docker-compose git
systemctl start docker
systemctl enable docker

# 克隆代码
git clone <repository-url>
cd dota2-analyzer

# 配置环境变量
cp .env.example .env
# 编辑.env文件

# 启动服务
docker-compose -f docker-compose.prod.yml up -d
```

### 云数据库配置
```bash
# 创建RDS实例 (PostgreSQL 14+)
# 配置数据库参数
max_connections = 200
shared_buffers = 256MB
effective_cache_size = 1GB

# 创建Redis实例
# 配置Redis参数
maxmemory = 1GB
maxmemory-policy = allkeys-lru
```

## Kubernetes部署

### 1. 创建命名空间
```bash
kubectl create namespace dota2-analyzer
kubectl config set-context --current --namespace=dota2-analyzer
```

### 2. 创建ConfigMap和Secret
```bash
# 创建配置文件
kubectl create configmap app-config --from-file=config/app.yaml
kubectl create configmap nginx-config --from-file=config/nginx.conf

# 创建密钥文件
kubectl create secret generic app-secrets \
  --from-literal=database-url=postgresql://user:pass@postgres:5432/dota2_analyzer \
  --from-literal=redis-url=redis://redis:6379/0 \
  --from-literal=jwt-secret=your-jwt-secret-key \
  --from-literal=steam-api-key=your-steam-api-key
```

### 3. 应用部署配置
```bash
# 部署基础设施
kubectl apply -f infrastructure/kubernetes/postgres/
kubectl apply -f infrastructure/kubernetes/redis/

# 部署应用服务
kubectl apply -f infrastructure/kubernetes/frontend/
kubectl apply -f infrastructure/kubernetes/backend-nodejs/
kubectl apply -f infrastructure/kubernetes/backend-python/
kubectl apply -f infrastructure/kubernetes/ai-models/

# 部署负载均衡器
kubectl apply -f infrastructure/kubernetes/nginx/
kubectl apply -f infrastructure/kubernetes/ingress/
```

### 4. 检查部署状态
```bash
# 查看Pod状态
kubectl get pods -n dota2-analyzer
kubectl get services -n dota2-analyzer
kubectl get ingress -n dota2-analyzer

# 查看部署详情
kubectl describe deployment backend-python -n dota2-analyzer
kubectl describe service frontend -n dota2-analyzer

# 查看日志
kubectl logs -f deployment/backend-python -n dota2-analyzer
kubectl logs -f deployment/ai-models -n dota2-analyzer
```

### 5. 扩展和更新
```bash
# 扩展副本数
kubectl scale deployment backend-python --replicas=3 -n dota2-analyzer
kubectl scale deployment ai-models --replicas=2 -n dota2-analyzer

# 滚动更新
kubectl set image deployment/backend-python backend-python=myrepo/dota2-python-backend:v2.0 -n dota2-analyzer
kubectl rollout status deployment/backend-python -n dota2-analyzer

# 回滚更新
kubectl rollout undo deployment/backend-python -n dota2-analyzer
```

### 6. 资源限制配置
```yaml
# 示例：资源限制配置
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-models
spec:
  template:
    spec:
      containers:
      - name: ai-models
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
          # GPU配置 (如需要)
          nvidia.com/gpu: 1
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

### Prometheus监控
```bash
# 添加Prometheus仓库
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# 安装Prometheus和Grafana
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace

# 配置自定义监控规则
kubectl apply -f infrastructure/monitoring/prometheus-rules.yaml

# 访问Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
# 默认用户名: admin, 密码: prom-operator
```

### ELK Stack日志收集
```bash
# 添加Elastic仓库
helm repo add elastic https://helm.elastic.co
helm repo update

# 安装Elasticsearch
helm install elasticsearch elastic/elasticsearch \
  --namespace logging --create-namespace \
  --set replicas=1,minimumMasterNodes=1

# 安装Kibana
helm install kibana elastic/kibana \
  --namespace logging \
  --set service.type=LoadBalancer

# 安装Filebeat
helm install filebeat elastic/filebeat \
  --namespace logging \
  --set daemonset.enabled=true

# 访问Kibana
kubectl get svc -n logging kibana-kibana
# 使用EXTERNAL-IP访问Kibana
```

### 应用性能监控
```bash
# 安装Jaeger (分布式追踪)
helm repo add jaegertracing https://jaegertracing.github.io/helm-charts
helm install jaeger jaegertracing/jaeger \
  --namespace monitoring

# 安装应用指标收集器
kubectl apply -f infrastructure/monitoring/app-metrics.yaml
```

### 告警配置
```yaml
# 示例：告警规则配置
groups:
- name: dota2-analyzer
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
      description: "Error rate is above 10% for 5 minutes"
  
  - alert: HighMemoryUsage
    expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage"
      description: "Memory usage is above 90%"
```

## 备份策略

### 数据库备份
```bash
#!/bin/bash
# 数据库备份脚本
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups"
RETENTION_DAYS=30

# 创建备份目录
mkdir -p $BACKUP_DIR

# PostgreSQL备份
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > $BACKUP_DIR/postgres_backup_$DATE.sql

# 压缩备份文件
gzip $BACKUP_DIR/postgres_backup_$DATE.sql

# 上传到AWS S3
aws s3 cp $BACKUP_DIR/postgres_backup_$DATE.sql.gz s3://your-backup-bucket/postgres/

# 上传到阿里云OSS
ossutil cp $BACKUP_DIR/postgres_backup_$DATE.sql.gz oss://your-backup-bucket/postgres/

# 删除本地过期备份
find $BACKUP_DIR -name "postgres_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete

# 记录备份日志
echo "$(date): Database backup completed" >> /var/log/backup.log
```

### 应用数据备份
```bash
#!/bin/bash
# 应用数据备份脚本
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups"
APP_DATA_DIR="/app/data"

# 创建应用数据备份
tar -czf $BACKUP_DIR/app_data_$DATE.tar.gz $APP_DATA_DIR

# 上传备份到云存储
aws s3 cp $BACKUP_DIR/app_data_$DATE.tar.gz s3://your-backup-bucket/app-data/

# 清理过期备份
find $BACKUP_DIR -name "app_data_*.tar.gz" -mtime +$RETENTION_DAYS -delete
```

### AI模型备份
```bash
#!/bin/bash
# AI模型备份脚本
DATE=$(date +%Y%m%d_%H%M%S)
MODEL_DIR="/app/models"
BACKUP_DIR="/opt/backups"

# 创建模型备份
tar -czf $BACKUP_DIR/ai_models_$DATE.tar.gz $MODEL_DIR

# 上传模型备份
aws s3 cp $BACKUP_DIR/ai_models_$DATE.tar.gz s3://your-backup-bucket/models/

# 记录模型版本信息
echo "Model backup: $DATE" >> $BACKUP_DIR/model_versions.log
```

### 设置定时任务
```bash
# 编辑crontab
crontab -e

# 添加定时任务
# 数据库备份 - 每天凌晨2点
0 2 * * * /opt/scripts/db_backup.sh

# 应用数据备份 - 每天凌晨3点
0 3 * * * /opt/scripts/app_backup.sh

# AI模型备份 - 每周日凌晨4点
0 4 * * 0 /opt/scripts/model_backup.sh

# 备份验证 - 每天凌晨5点
0 5 * * * /opt/scripts/verify_backups.sh
```

### 备份监控和告警
```bash
#!/bin/bash
# 备份验证脚本
BACKUP_DIR="/opt/backups"
LOG_FILE="/var/log/backup-verify.log"

# 检查最新备份文件
latest_backup=$(find $BACKUP_DIR -name "postgres_backup_*.sql.gz" -mtime -1)

if [ -z "$latest_backup" ]; then
    echo "$(date): ERROR - No recent backup found" >> $LOG_FILE
    # 发送告警
    curl -X POST "$WEBHOOK_URL" -H "Content-Type: application/json" \
        -d '{"text": "🚨 Backup verification failed - No recent backup found"}'
else
    echo "$(date): SUCCESS - Backup verification passed" >> $LOG_FILE
fi

# 检查磁盘空间
disk_usage=$(df -h $BACKUP_DIR | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $disk_usage -gt 80 ]; then
    echo "$(date): WARNING - Backup disk usage: ${disk_usage}%" >> $LOG_FILE
fi
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

## AI模型部署

### 模型下载和配置
```bash
#!/bin/bash
# AI模型下载脚本
MODEL_DIR="/app/models"
MODEL_VERSION="v2.1.0"

# 创建模型目录
mkdir -p $MODEL_DIR

# 下载预训练模型
echo "Downloading AI models..."
wget -O $MODEL_DIR/dota_strategy_model.pb "https://models.dota2-analyzer.com/strategy-model-$MODEL_VERSION.pb"
wget -O $MODEL_DIR/draft_predictor.pkl "https://models.dota2-analyzer.com/draft-predictor-$MODEL_VERSION.pkl"
wget -O $MODEL_DIR/match_analyzer.onnx "https://models.dota2-analyzer.com/match-analyzer-$MODEL_VERSION.onnx"

# 验证模型文件
for model in $MODEL_DIR/*; do
    if [ -f "$model" ]; then
        echo "✓ $(basename $model) downloaded successfully"
    else
        echo "✗ $(basename $model) download failed"
    fi
done

# 设置模型权限
chmod 644 $MODEL_DIR/*
```

### GPU配置
```bash
# NVIDIA GPU驱动安装
sudo apt-get update
sudo apt-get install -y nvidia-driver-470 nvidia-dkms-470

# NVIDIA Docker支持
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker

# 验证GPU支持
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

### 模型服务配置
```yaml
# docker-compose.yml中的AI模型服务配置
services:
  ai-models:
    build: ./ai-models
    environment:
      - MODEL_PATH=/app/models
      - GPU_ENABLED=true
      - GPU_MEMORY_LIMIT=4096
      - BATCH_SIZE=32
      - MAX_WORKERS=4
    volumes:
      - ./models:/app/models
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

## 故障排查

### 1. 查看日志
```bash
# Docker日志
docker logs [container-name]
docker logs -f --tail=100 [container-id]

# Kubernetes日志
kubectl logs -f [pod-name] -n dota2-analyzer
kubectl logs -f deployment/backend-python -n dota2-analyzer
kubectl logs -f deployment/ai-models -n dota2-analyzer --tail=200

# 系统日志
journalctl -u docker.service -f
tail -f /var/log/syslog | grep -i error
```

### 2. 健康检查
```bash
# 检查服务状态
curl http://localhost:3001/health

# 检查数据库连接
kubectl exec -it [postgres-pod] -- psql -U dota2_user -d dota2_analyzer -c "SELECT 1"
```

### 3. 性能监控
- 使用Prometheus + Grafana
- 设置关键指标告警
- 监控API响应时间和错误率

### 4. 常见问题
1. **数据库连接失败**
   - 检查数据库配置
   - 验证网络连接
   - 查看数据库日志
   - 检查连接池配置

2. **Redis连接失败**
   - 检查Redis配置
   - 验证端口是否开放
   - 重启Redis服务
   - 检查Redis内存使用

3. **前端构建失败**
   - 检查Node.js版本
   - 清理npm缓存
   - 重新安装依赖
   - 检查内存限制

4. **AI模型加载失败**
   - 检查模型文件完整性
   - 验证模型文件权限
   - 检查GPU驱动和CUDA版本
   - 查看模型服务日志

5. **Python后端启动失败**
   - 检查Python版本和依赖
   - 验证数据库连接
   - 检查环境变量配置
   - 查看详细错误日志

### 5. 性能调优
```bash
# 数据库性能优化
# 1. 连接池优化
# 2. 索引优化
# 3. 查询优化

# Redis性能优化
# 1. 内存优化
# 2. 持久化配置
# 3. 集群配置

# 应用性能优化
# 1. 负载均衡配置
# 2. 缓存策略
# 3. 异步处理
```

### 6. 获取帮助
- 查看日志: `docker-compose logs -f [service-name]`
- 查看系统状态: `docker system df`
- 查看资源使用: `docker stats`
- 联系支持: support@dota2-analyzer.com

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