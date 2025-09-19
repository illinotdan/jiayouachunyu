#!/bin/bash

# Dota2专业解析社区 - 开发环境完整设置脚本
# 适用于Linux/macOS环境

echo "🚀 Dota2专业解析社区 开发环境设置开始..."

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查依赖
check_dependencies() {
    echo -e "${BLUE}🔍 检查依赖...${NC}"
    
    local missing_deps=()
    
    # 检查Node.js
    if ! command -v node &> /dev/null; then
        missing_deps+=("nodejs")
    fi
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        missing_deps+=("docker")
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        missing_deps+=("docker-compose")
    fi
    
    # 检查Python（用于AI模块）
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        echo -e "${RED}❌ 缺少依赖: ${missing_deps[*]}${NC}"
        echo -e "${YELLOW}请安装缺失的依赖后继续${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ 所有依赖检查通过${NC}"
}

# 创建环境变量文件
setup_environment() {
    echo -e "${BLUE}⚙️  设置环境变量...${NC}"
    
    # 创建.env文件（如果不存在）
    if [ ! -f .env ]; then
        cp .env.example .env
        echo -e "${YELLOW}⚠️  请编辑 .env 文件填入实际配置${NC}"
    fi
    
    # 创建Python环境变量
    if [ ! -f backend/python/.env ]; then
        cp backend/python/env.example backend/python/.env
        echo -e "${YELLOW}⚠️  请编辑 backend/python/.env 文件填入实际配置${NC}"
    fi
}

# 生成SSL证书
setup_ssl() {
    echo -e "${BLUE}🔐 设置SSL证书...${NC}"
    
    cd infrastructure/docker
    
    if [ ! -f ssl/cert.pem ] || [ ! -f ssl/key.pem ]; then
        echo -e "${YELLOW}生成自签名SSL证书...${NC}"
        chmod +x ssl/generate_ssl.sh
        ./ssl/generate_ssl.sh
    else
        echo -e "${GREEN}✅ SSL证书已存在${NC}"
    fi
    
    cd ../../
}

# 安装依赖
install_dependencies() {
    echo -e "${BLUE}📦 安装依赖...${NC}"
    
    # 根依赖
    echo -e "${BLUE}安装根依赖...${NC}"
    npm install
    
    # 前端依赖
    echo -e "${BLUE}安装前端依赖...${NC}"
    cd frontend
    npm install
    cd ..
    
    # 后端依赖
    echo -e "${BLUE}安装后端依赖...${NC}"
    cd backend
    npm install
    cd ..
    
    # Python依赖
    echo -e "${BLUE}安装Python依赖...${NC}"
    cd backend/python
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    deactivate
    cd ../../
}

# 启动基础设施
start_infrastructure() {
    echo -e "${BLUE}🐳 启动基础设施...${NC}"
    
    # 启动数据库和缓存
    docker-compose -f infrastructure/docker/docker-compose.yml up -d postgres redis
    
    echo -e "${BLUE}⏳ 等待数据库启动...${NC}"
    sleep 15
    
    # 运行数据库迁移
    echo -e "${BLUE}🔄 运行数据库迁移...${NC}"
    cd backend
    npx prisma migrate dev
    cd ..
    
    # 初始化Python数据库
    echo -e "${BLUE}🔄 初始化Python数据库...${NC}"
    cd backend/python
    source venv/bin/activate
    flask init-db
    deactivate
    cd ../../
}

# 启动开发服务
start_dev_services() {
    echo -e "${BLUE}🚀 启动开发服务...${NC}"
    
    echo -e "${GREEN}✅ 开发环境设置完成！${NC}"
    echo ""
    echo -e "${BLUE}下一步:${NC}"
    echo "1. 编辑 .env 文件填入实际配置"
    echo "2. 运行: npm run dev 启动开发服务器"
    echo "3. 访问: http://localhost:3000"
    echo "4. API文档: http://localhost:3001/api/docs"
    echo "5. Flask API: http://localhost:5000/apidocs"
    echo ""
    echo -e "${YELLOW}可用命令:${NC}"
    echo "- npm run dev: 启动所有服务"
    echo "- docker-compose -f infrastructure/docker/docker-compose.yml up -d: 启动基础设施"
    echo "- cd backend/python && source venv/bin/activate && flask run: 启动Python服务"
}

# 主函数
main() {
    check_dependencies
    setup_environment
    setup_ssl
    install_dependencies
    start_infrastructure
    start_dev_services
}

# 运行主函数
main