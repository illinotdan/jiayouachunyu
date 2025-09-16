# 刀塔情书 - 部署指南

## 概述

本文档提供了刀塔情书平台的完整部署指南，包括前端和后端的部署配置。

---

## 1. 前端部署

### 1.1 静态文件部署

#### 选项1: Nginx部署
```nginx
server {
    listen 80;
    server_name dotaanalysis.com www.dotaanalysis.com;
    
    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name dotaanalysis.com www.dotaanalysis.com;
    
    # SSL配置
    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    
    # 网站根目录
    root /var/www/dota-analysis;
    index index.html;
    
    # 静态文件缓存
    location ~* \.(css|js|png|jpg|jpeg|gif|svg|ico|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header Vary Accept-Encoding;
        gzip_static on;
    }
    
    # HTML文件缓存
    location ~* \.html$ {
        expires 1h;
        add_header Cache-Control "public, must-revalidate";
    }
    
    # API代理
    location /api/ {
        proxy_pass http://backend:3000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # WebSocket代理
    location /ws/ {
        proxy_pass http://backend:3000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
    
    # SPA路由支持
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
}
```

#### 选项2: CDN部署 (推荐)
```bash
# 使用阿里云OSS + CDN
# 1. 上传静态文件到OSS
ossutil cp -r frontend/ oss://your-bucket/

# 2. 配置CDN加速
# 3. 设置缓存规则:
#    - HTML文件: 1小时
#    - CSS/JS文件: 1年
#    - 图片文件: 1年
```

### 1.2 Docker部署

```dockerfile
# Dockerfile.frontend
FROM nginx:alpine

# 复制静态文件
COPY frontend_new/ /usr/share/nginx/html/

# 复制Nginx配置
COPY nginx.conf /etc/nginx/nginx.conf

# 暴露端口
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

---

## 2. 后端部署

### 2.1 Node.js后端部署

#### 环境要求
- Node.js 18+
- PostgreSQL 14+
- Redis 6+
- PM2 (进程管理)

#### 部署脚本
```bash
#!/bin/bash
# deploy.sh

# 1. 更新代码
git pull origin main

# 2. 安装依赖
npm ci --production

# 3. 数据库迁移
npm run migrate

# 4. 构建项目
npm run build

# 5. 重启服务
pm2 restart dota-analysis-api

# 6. 健康检查
sleep 10
curl -f http://localhost:3000/health || exit 1

echo "部署完成!"
```

#### PM2配置文件
```json
{
  "name": "dota-analysis-api",
  "script": "dist/server.js",
  "instances": "max",
  "exec_mode": "cluster",
  "env": {
    "NODE_ENV": "production",
    "PORT": 3000
  },
  "log_date_format": "YYYY-MM-DD HH:mm:ss Z",
  "error_file": "logs/error.log",
  "out_file": "logs/access.log",
  "log_file": "logs/combined.log",
  "time": true
}
```

### 2.2 Docker部署

```dockerfile
# Dockerfile.backend
FROM node:18-alpine

WORKDIR /app

# 复制package文件
COPY package*.json ./

# 安装依赖
RUN npm ci --only=production && npm cache clean --force

# 复制源代码
COPY . .

# 构建项目
RUN npm run build

# 创建非root用户
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nodejs -u 1001

# 切换用户
USER nodejs

# 暴露端口
EXPOSE 3000

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

# 启动命令
CMD ["node", "dist/server.js"]
```

### 2.3 Docker Compose配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  # 前端服务
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./ssl:/etc/ssl/certs:ro
    depends_on:
      - backend
    restart: unless-stopped

  # 后端服务
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://user:password@db:5432/dota_analysis
      - REDIS_URL=redis://redis:6379
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      - db
      - redis
    restart: unless-stopped
    volumes:
      - ./uploads:/app/uploads

  # 数据库服务
  db:
    image: postgres:14-alpine
    environment:
      - POSTGRES_DB=dota_analysis
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    restart: unless-stopped

  # Redis缓存
  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    command: redis-server --appendonly yes

  # 监控服务 (可选)
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    restart: unless-stopped

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  grafana_data:
```

---

## 3. 环境配置

### 3.1 环境变量配置

```bash
# .env.production
NODE_ENV=production
PORT=3000

# 数据库配置
DATABASE_URL=postgresql://username:password@localhost:5432/dota_analysis
DB_POOL_SIZE=20
DB_TIMEOUT=30000

# Redis配置
REDIS_URL=redis://localhost:6379
REDIS_PREFIX=dota_analysis:

# JWT配置
JWT_SECRET=your-super-secret-jwt-key
JWT_EXPIRES_IN=7d
REFRESH_TOKEN_EXPIRES_IN=30d

# 外部API配置
OPENDOTA_API_KEY=your-opendota-api-key
STRATZ_API_KEY=your-stratz-api-key
STEAM_API_KEY=your-steam-api-key

# 文件上传配置
UPLOAD_MAX_SIZE=5242880
UPLOAD_ALLOWED_TYPES=image/jpeg,image/png,image/gif

# 邮件配置
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password

# 监控配置
SENTRY_DSN=your-sentry-dsn
LOG_LEVEL=info

# 限流配置
RATE_LIMIT_WINDOW=60000
RATE_LIMIT_MAX_REQUESTS=100
```

### 3.2 Nginx配置优化

```nginx
# /etc/nginx/sites-available/dota-analysis
server {
    listen 443 ssl http2;
    server_name dotaanalysis.com;
    
    # SSL配置
    ssl_certificate /etc/ssl/certs/dotaanalysis.com.crt;
    ssl_certificate_key /etc/ssl/private/dotaanalysis.com.key;
    
    # 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;
    
    # 压缩配置
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # 网站根目录
    root /var/www/dota-analysis;
    index index.html;
    
    # 静态资源优化
    location ~* \.(css|js|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header Vary Accept-Encoding;
        
        # 启用Brotli压缩 (如果可用)
        brotli on;
        brotli_comp_level 6;
        brotli_types text/plain text/css application/javascript text/xml application/xml application/xml+rss text/javascript;
    }
    
    # API代理配置
    location /api/ {
        proxy_pass http://127.0.0.1:3000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # 超时配置
        proxy_connect_timeout 5s;
        proxy_send_timeout 10s;
        proxy_read_timeout 10s;
    }
    
    # 文件上传代理
    location /upload/ {
        proxy_pass http://127.0.0.1:3000/upload/;
        client_max_body_size 10M;
        proxy_request_buffering off;
    }
    
    # WebSocket代理
    location /ws/ {
        proxy_pass http://127.0.0.1:3000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # SPA路由支持
    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache";
    }
    
    # 错误页面
    error_page 404 /404.html;
    error_page 500 502 503 504 /50x.html;
    
    location = /50x.html {
        root /usr/share/nginx/html;
    }
}
```

#### 选项2: CDN部署
```bash
# 使用阿里云CDN部署脚本
#!/bin/bash

# 1. 构建优化
echo "优化静态资源..."
npm run optimize

# 2. 上传到OSS
echo "上传文件到OSS..."
ossutil cp -r dist/ oss://dota-analysis-cdn/ --update

# 3. 刷新CDN缓存
echo "刷新CDN缓存..."
aliyun cdn RefreshObjectCaches --ObjectPath https://cdn.dotaanalysis.com/

echo "CDN部署完成!"
```

---

## 2. 后端部署

### 2.1 生产环境配置

#### 系统要求
- Ubuntu 20.04+ / CentOS 8+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+
- 内存: 最少4GB，推荐8GB+
- 存储: 最少50GB SSD

#### 安装脚本
```bash
#!/bin/bash
# install.sh

# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# 安装PostgreSQL
sudo apt install postgresql postgresql-contrib -y
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 安装Redis
sudo apt install redis-server -y
sudo systemctl start redis-server
sudo systemctl enable redis-server

# 安装PM2
sudo npm install -g pm2

# 安装Nginx
sudo apt install nginx -y
sudo systemctl start nginx
sudo systemctl enable nginx

# 创建应用目录
sudo mkdir -p /var/www/dota-analysis
sudo chown -R $USER:$USER /var/www/dota-analysis

echo "环境安装完成!"
```

### 2.2 数据库初始化

```bash
#!/bin/bash
# init-database.sh

# 创建数据库用户
sudo -u postgres createuser --interactive --pwprompt dota_analysis_user

# 创建数据库
sudo -u postgres createdb -O dota_analysis_user dota_analysis

# 导入初始化脚本
psql -U dota_analysis_user -d dota_analysis -f database/init.sql

# 运行迁移
npm run migrate:prod

echo "数据库初始化完成!"
```

### 2.3 应用部署

```bash
#!/bin/bash
# deploy-backend.sh

# 设置变量
APP_DIR="/var/www/dota-analysis-api"
REPO_URL="https://github.com/your-username/dota-analysis-backend.git"

# 创建目录
sudo mkdir -p $APP_DIR
sudo chown -R $USER:$USER $APP_DIR

# 克隆代码
git clone $REPO_URL $APP_DIR
cd $APP_DIR

# 安装依赖
npm ci --production

# 复制环境配置
cp .env.example .env.production
# 编辑 .env.production 填入实际配置

# 构建项目
npm run build

# 配置PM2
pm2 start ecosystem.config.js --env production

# 保存PM2配置
pm2 save
pm2 startup

echo "后端部署完成!"
```

---

## 3. 监控和日志

### 3.1 日志配置

```javascript
// logger.js
const winston = require('winston');

const logger = winston.createLogger({
    level: process.env.LOG_LEVEL || 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json()
    ),
    defaultMeta: { service: 'dota-analysis-api' },
    transports: [
        new winston.transports.File({ 
            filename: 'logs/error.log', 
            level: 'error' 
        }),
        new winston.transports.File({ 
            filename: 'logs/combined.log' 
        })
    ]
});

if (process.env.NODE_ENV !== 'production') {
    logger.add(new winston.transports.Console({
        format: winston.format.simple()
    }));
}

module.exports = logger;
```

### 3.2 监控配置

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'dota-analysis-api'
    static_configs:
      - targets: ['localhost:3000']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'nginx'
    static_configs:
      - targets: ['localhost:9113']

  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']
```

---

## 4. 性能优化

### 4.1 前端优化

```bash
# 构建优化脚本
#!/bin/bash
# optimize.sh

echo "开始优化前端资源..."

# 1. 压缩HTML
html-minifier --input-dir . --output-dir dist --file-ext html --remove-comments --collapse-whitespace --minify-css --minify-js

# 2. 压缩CSS
cleancss -o dist/css/styles.min.css css/styles.css

# 3. 压缩JavaScript
terser js/*.js --compress --mangle -o dist/js/bundle.min.js

# 4. 优化图片
imagemin images/* --out-dir=dist/images

# 5. 生成Gzip文件
find dist -type f \( -name "*.html" -o -name "*.css" -o -name "*.js" \) -exec gzip -k {} \;

echo "前端优化完成!"
```

### 4.2 数据库优化

```sql
-- 性能优化查询
-- 1. 创建必要的索引
CREATE INDEX CONCURRENTLY idx_matches_performance ON matches(status, start_time DESC) WHERE status IN ('live', 'upcoming');

-- 2. 分析表统计信息
ANALYZE;

-- 3. 清理过期数据
DELETE FROM user_activity_logs WHERE created_at < NOW() - INTERVAL '90 days';
DELETE FROM content_views WHERE created_at < NOW() - INTERVAL '30 days';

-- 4. 重建索引
REINDEX DATABASE dota_analysis;
```

---

## 5. 安全配置

### 5.1 防火墙配置

```bash
# UFW防火墙配置
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 5.2 SSL证书配置

```bash
# Let's Encrypt SSL证书
sudo apt install certbot python3-certbot-nginx -y

# 获取证书
sudo certbot --nginx -d dotaanalysis.com -d www.dotaanalysis.com

# 自动续期
sudo crontab -e
# 添加: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 5.3 安全头配置

```nginx
# 安全头配置
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' cdn.tailwindcss.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:;" always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
```

---

## 6. 备份和恢复

### 6.1 数据库备份

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/dota-analysis"
DB_NAME="dota_analysis"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 数据库备份
pg_dump -U postgres -h localhost $DB_NAME | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Redis备份
redis-cli SAVE
cp /var/lib/redis/dump.rdb $BACKUP_DIR/redis_backup_$DATE.rdb

# 上传文件备份
tar -czf $BACKUP_DIR/uploads_backup_$DATE.tar.gz /var/www/dota-analysis/uploads/

# 清理旧备份 (保留30天)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.rdb" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "备份完成: $DATE"
```

### 6.2 恢复脚本

```bash
#!/bin/bash
# restore.sh

if [ -z "$1" ]; then
    echo "用法: ./restore.sh backup_date"
    echo "例如: ./restore.sh 20250101_120000"
    exit 1
fi

BACKUP_DATE=$1
BACKUP_DIR="/var/backups/dota-analysis"

# 恢复数据库
echo "恢复数据库..."
gunzip -c $BACKUP_DIR/db_backup_$BACKUP_DATE.sql.gz | psql -U postgres -d dota_analysis

# 恢复Redis
echo "恢复Redis..."
sudo systemctl stop redis-server
sudo cp $BACKUP_DIR/redis_backup_$BACKUP_DATE.rdb /var/lib/redis/dump.rdb
sudo chown redis:redis /var/lib/redis/dump.rdb
sudo systemctl start redis-server

# 恢复上传文件
echo "恢复上传文件..."
tar -xzf $BACKUP_DIR/uploads_backup_$BACKUP_DATE.tar.gz -C /

echo "恢复完成!"
```

---

## 7. 维护脚本

### 7.1 健康检查

```bash
#!/bin/bash
# health-check.sh

# 检查服务状态
services=("nginx" "postgresql" "redis-server")

for service in "${services[@]}"; do
    if systemctl is-active --quiet $service; then
        echo "✅ $service 运行正常"
    else
        echo "❌ $service 服务异常"
        sudo systemctl restart $service
    fi
done

# 检查应用健康
if curl -f http://localhost:3000/health > /dev/null 2>&1; then
    echo "✅ API服务正常"
else
    echo "❌ API服务异常"
    pm2 restart dota-analysis-api
fi

# 检查磁盘空间
disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $disk_usage -gt 80 ]; then
    echo "⚠️  磁盘使用率过高: ${disk_usage}%"
fi

# 检查内存使用
memory_usage=$(free | awk 'NR==2{printf "%.2f", $3*100/$2}')
if (( $(echo "$memory_usage > 80" | bc -l) )); then
    echo "⚠️  内存使用率过高: ${memory_usage}%"
fi
```

### 7.2 日志清理

```bash
#!/bin/bash
# cleanup-logs.sh

# 清理应用日志 (保留30天)
find /var/www/dota-analysis-api/logs -name "*.log" -mtime +30 -delete

# 清理Nginx日志 (保留7天)
find /var/log/nginx -name "*.log" -mtime +7 -delete

# 清理系统日志
sudo journalctl --vacuum-time=30d

echo "日志清理完成"
```

---

## 8. CI/CD配置

### 8.1 GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Run tests
      run: npm test
    
    - name: Build application
      run: npm run build
    
    - name: Deploy to server
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{ secrets.HOST }}
        username: ${{ secrets.USERNAME }}
        key: ${{ secrets.SSH_KEY }}
        script: |
          cd /var/www/dota-analysis-api
          git pull origin main
          npm ci --production
          npm run build
          pm2 restart dota-analysis-api
```

---

## 9. 故障排除

### 9.1 常见问题

#### 问题1: 数据库连接失败
```bash
# 检查数据库状态
sudo systemctl status postgresql

# 检查连接配置
sudo -u postgres psql -c "\l"

# 重启数据库
sudo systemctl restart postgresql
```

#### 问题2: Redis连接失败
```bash
# 检查Redis状态
sudo systemctl status redis-server

# 测试连接
redis-cli ping

# 重启Redis
sudo systemctl restart redis-server
```

#### 问题3: 应用无响应
```bash
# 检查PM2状态
pm2 status

# 查看日志
pm2 logs dota-analysis-api

# 重启应用
pm2 restart dota-analysis-api
```

### 9.2 性能问题诊断

```bash
# 检查系统资源
htop
iotop
free -h
df -h

# 检查数据库性能
sudo -u postgres psql dota_analysis -c "
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 10;"

# 检查慢查询
tail -f /var/log/postgresql/postgresql-14-main.log | grep "slow query"
```

---

## 10. 扩展部署

### 10.1 负载均衡配置

```nginx
# upstream配置
upstream backend {
    least_conn;
    server 127.0.0.1:3000 weight=3;
    server 127.0.0.1:3001 weight=2;
    server 127.0.0.1:3002 weight=1;
    
    # 健康检查
    keepalive 32;
}

server {
    location /api/ {
        proxy_pass http://backend/api/;
        # ... 其他配置
    }
}
```

### 10.2 Redis集群配置

```bash
# Redis Cluster配置
redis-server --port 7000 --cluster-enabled yes --cluster-config-file nodes-7000.conf --cluster-node-timeout 5000 --appendonly yes
redis-server --port 7001 --cluster-enabled yes --cluster-config-file nodes-7001.conf --cluster-node-timeout 5000 --appendonly yes
redis-server --port 7002 --cluster-enabled yes --cluster-config-file nodes-7002.conf --cluster-node-timeout 5000 --appendonly yes

# 创建集群
redis-cli --cluster create 127.0.0.1:7000 127.0.0.1:7001 127.0.0.1:7002 --cluster-replicas 0
```

---

*该部署指南会随着项目发展持续更新*
