#!/bin/bash

# Dota2专业解析社区 - 项目设置脚本
# 适用于Linux/macOS环境

echo "🚀 Dota2专业解析社区 项目设置开始..."

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js未安装${NC}"
    echo "请访问 https://nodejs.org/ 安装Node.js 18+"
    exit 1
fi

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker未安装${NC}"
    echo "建议安装Docker用于数据库和容器化部署"
fi

# 创建.env文件
if [ ! -f .env ]; then
    echo -e "${GREEN}📄 创建.env配置文件...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  请编辑.env文件填入实际配置${NC}"
fi

# 安装根依赖
echo -e "${GREEN}📦 安装根依赖...${NC}"
npm install

# 安装前端依赖
echo -e "${GREEN}📦 安装前端依赖...${NC}"
cd frontend
npm install
cd ..

# 安装后端依赖
echo -e "${GREEN}📦 安装后端依赖...${NC}"
cd backend
npm install
cd ..

# 启动数据库（如果已安装Docker）
if command -v docker &> /dev/null; then
    echo -e "${GREEN}🐳 启动数据库服务...${NC}"
    docker-compose -f infrastructure/docker/docker-compose.yml up postgres redis -d
    
    # 等待数据库启动
    echo -e "${GREEN}⏳ 等待数据库启动...${NC}"
    sleep 10
    
    # 运行数据库迁移
    if [ -f backend/prisma/schema.prisma ]; then
        echo -e "${GREEN}🔄 运行数据库迁移...${NC}"
        cd backend
        npx prisma migrate dev
        cd ..
    fi
fi

echo -e "${GREEN}✅ 项目设置完成！${NC}"
echo ""
echo "下一步:"
echo "1. 编辑 .env 文件填入实际配置"
echo "2. 运行: npm run dev 启动开发服务器"
echo "3. 访问: http://localhost:3000"
echo ""
echo "API文档: http://localhost:3001/api/docs"