@echo off
:: Dota2专业解析社区 - 项目设置脚本
:: 适用于Windows环境

echo 🚀 Dota2专业解析社区 项目设置开始...

:: 检查Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js未安装
    echo 请访问 https://nodejs.org/ 安装Node.js 18+
    pause
    exit /b 1
)

:: 检查Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Docker未安装
    echo 建议安装Docker用于数据库和容器化部署
)

:: 创建.env文件
if not exist .env (
    echo 📄 创建.env配置文件...
    copy .env.example .env
    echo ⚠️  请编辑.env文件填入实际配置
)

:: 安装根依赖
echo 📦 安装根依赖...
call npm install
if errorlevel 1 (
    echo ❌ 根依赖安装失败
    pause
    exit /b 1
)

:: 安装前端依赖
echo 📦 安装前端依赖...
cd frontend
call npm install
if errorlevel 1 (
    echo ❌ 前端依赖安装失败
    pause
    exit /b 1
)
cd ..

:: 安装后端依赖
echo 📦 安装后端依赖...
cd backend
call npm install
if errorlevel 1 (
    echo ❌ 后端依赖安装失败
    pause
    exit /b 1
)
cd ..

:: 启动数据库（如果已安装Docker）
docker --version >nul 2>&1
if not errorlevel 1 (
    echo 🐳 启动数据库服务...
    docker-compose -f infrastructure\docker\docker-compose.yml up postgres redis -d
    
    :: 等待数据库启动
    echo ⏳ 等待数据库启动...
    timeout /t 10 /nobreak >nul
    
    :: 运行数据库迁移
    if exist backend\prisma\schema.prisma (
        echo 🔄 运行数据库迁移...
        cd backend
        call npx prisma migrate dev
        cd ..
    )
)

echo ✅ 项目设置完成！
echo.
echo 下一步:
echo 1. 编辑 .env 文件填入实际配置
echo 2. 运行: npm run dev 启动开发服务器
echo 3. 访问: http://localhost:3000
echo.
echo API文档: http://localhost:3001/api/docs
pause