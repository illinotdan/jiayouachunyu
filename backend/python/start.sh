#!/bin/bash

# 刀塔解析后端快速启动脚本

echo "🎮 启动刀塔解析后端服务..."

# 检查Python版本
python_version=$(python3 --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ 需要Python 3.8或更高版本，当前版本: $python_version"
    exit 1
fi

# 检查虚拟环境
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  建议在虚拟环境中运行"
    echo "创建虚拟环境: python3 -m venv venv"
    echo "激活虚拟环境: source venv/bin/activate"
    read -p "是否继续？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 检查依赖
echo "📦 检查依赖..."
if [ ! -f "requirements.txt" ]; then
    echo "❌ 找不到requirements.txt文件"
    exit 1
fi

# 安装依赖
echo "📥 安装Python依赖..."
pip install -r requirements.txt

# 检查环境配置
if [ ! -f ".env" ]; then
    echo "⚙️  创建环境配置文件..."
    cp env.example .env
    echo "✅ 已创建.env文件，请编辑其中的配置"
fi

# 检查数据库连接
echo "🗄️  检查数据库连接..."
python3 -c "
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/dota_analysis')

try:
    # 解析数据库URL
    import re
    match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', db_url)
    if match:
        user, password, host, port, dbname = match.groups()
        
        # 测试连接
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=dbname
        )
        conn.close()
        print('✅ 数据库连接正常')
    else:
        print('❌ 数据库URL格式错误')
        exit(1)
        
except Exception as e:
    print(f'❌ 数据库连接失败: {e}')
    print('请检查PostgreSQL是否已安装并运行')
    print('创建数据库: sudo -u postgres createdb dota_analysis')
    exit(1)
"

if [ $? -ne 0 ]; then
    exit 1
fi

# 检查Redis连接
echo "🔴 检查Redis连接..."
python3 -c "
import os
from dotenv import load_dotenv
import redis

load_dotenv()
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

try:
    r = redis.from_url(redis_url)
    r.ping()
    print('✅ Redis连接正常')
except Exception as e:
    print(f'❌ Redis连接失败: {e}')
    print('请检查Redis是否已安装并运行')
    exit(1)
"

if [ $? -ne 0 ]; then
    exit 1
fi

# 初始化数据库
echo "🏗️  初始化数据库..."
python3 -c "
from app import create_app
from config.settings import DevelopmentConfig
from config.database import init_database

app, _ = create_app(DevelopmentConfig)
with app.app_context():
    init_database(app)
    print('✅ 数据库初始化完成')
"

# 启动服务
echo "🚀 启动Flask应用..."
echo "访问地址: http://localhost:5000"
echo "API文档: http://localhost:5000/apidocs"
echo "健康检查: http://localhost:5000/health"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

# 启动开发服务器
python3 run.py
