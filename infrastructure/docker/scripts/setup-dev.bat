@echo off
:: Dota2专业解析社区 - 开发环境完整设置脚本
:: 适用于Windows环境

echo 🚀 Dota2专业解析社区 开发环境设置开始...

:: 检查Node.js
echo 🔍 检查Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js未安装
    echo 请访问 https://nodejs.org/ 安装Node.js 18+
    pause
    exit /b 1
)

:: 检查Docker
echo 🔍 检查Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker未安装
    echo 请访问 https://docker.com 安装Docker
    pause
    exit /b 1
)

:: 检查Docker Compose
echo 🔍 检查Docker Compose...
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose未安装
    echo 请安装Docker Compose
    pause
    exit /b 1
)

:: 检查Python
echo 🔍 检查Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Python未安装
    echo 建议安装Python 3.9+用于AI模块
)

:: 创建环境变量文件
echo ⚙️  设置环境变量...
if not exist .env (
    echo 📄 创建.env配置文件...
    copy .env.example .env
    echo ⚠️  请编辑 .env 文件填入实际配置
)

if not exist backend\python\.env (
    echo 📄 创建Python环境变量文件...
    copy backend\python\env.example backend\python\.env
    echo ⚠️  请编辑 backend\python\.env 文件填入实际配置
)

:: 生成SSL证书
echo 🔐 设置SSL证书...
cd infrastructure\docker

if not exist ssl\cert.pem if not exist ssl\key.pem (
    echo 📄 生成自签名SSL证书...
    if exist ssl\generate_ssl.bat (
        call ssl\generate_ssl.bat
    ) else (
        echo ⚠️  SSL生成脚本不存在，跳过SSL配置
    )
) else (
    echo ✅ SSL证书已存在
)

cd ..\..\..

:: 安装依赖
echo 📦 安装依赖...

:: 根依赖
echo 📦 安装根依赖...
call npm install
if errorlevel 1 (
    echo ❌ 根依赖安装失败
    pause
    exit /b 1
)

:: 前端依赖
echo 📦 安装前端依赖...
cd frontend
call npm install
if errorlevel 1 (
    echo ❌ 前端依赖安装失败
    pause
    exit /b 1
)
cd ..

:: 后端依赖
echo 📦 安装后端依赖...
cd backend
call npm install
if errorlevel 1 (
    echo ❌ 后端依赖安装失败
    pause
    exit /b 1
)
cd ..

:: Python依赖
echo 📦 安装Python依赖...
cd backend\python
if not exist venv (
    echo 📦 创建Python虚拟环境...
    python -m venv venv
)
echo 📦 激活虚拟环境并安装依赖...
call venv\Scripts\activate
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Python依赖安装失败
    pause
    exit /b 1
)
deactivate
cd ..\..\..

:: 启动基础设施
echo 🐳 启动基础设施...
docker-compose -f infrastructure\docker\docker-compose.yml up -d postgres redis
if errorlevel 1 (
    echo ❌ 基础设施启动失败
    pause
    exit /b 1
)

echo ⏳ 等待数据库启动...
timeout /t 15 /nobreak >nul

:: 运行数据库迁移
echo 🔄 运行数据库迁移...
cd backend
call npx prisma migrate dev
if errorlevel 1 (
    echo ⚠️  数据库迁移失败，可能需要手动处理
)
cd ..

:: 初始化Python数据库
echo 🔄 初始化Python数据库...
cd backend\python
call venv\Scripts\activate
flask init-db
if errorlevel 1 (
    echo ⚠️  Python数据库初始化失败，可能需要手动处理
)
deactivate
cd ..\..\..

:: 完成
echo ✅ 开发环境设置完成！
echo.
echo 下一步:
echo 1. 编辑 .env 文件填入实际配置
echo 2. 运行: npm run dev 启动开发服务器
echo 3. 访问: http://localhost:3000
echo 4. API文档: http://localhost:3001/api/docs
echo 5. Flask API: http://localhost:5000/apidocs
echo.
echo 可用命令:
echo - npm run dev: 启动所有服务
echo - docker-compose -f infrastructure/docker/docker-compose.yml up -d: 启动基础设施
echo - cd backend/python ^&^& venv\Scripts\activate ^&^& flask run: 启动Python服务
pause