const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
const morgan = require('morgan');
const { PrismaClient } = require('@prisma/client');

const authRoutes = require('./routes/auth');
const matchRoutes = require('./routes/matches');
const commentRoutes = require('./routes/comments');
const userRoutes = require('./routes/users');
const annotationRoutes = require('./routes/annotations');

const app = express();
const prisma = new PrismaClient();

// 中间件
app.use(helmet());
app.use(cors());
app.use(compression());
app.use(morgan('combined'));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// 速率限制
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15分钟
  max: 100, // 限制每个IP 100个请求
  message: {
    error: '请求过于频繁，请稍后再试'
  }
});
app.use('/api/', limiter);

// 健康检查
app.get('/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

// API路由
app.use('/api/auth', authRoutes);
app.use('/api/matches', matchRoutes);
app.use('/api/comments', commentRoutes);
app.use('/api/users', userRoutes);
app.use('/api/annotations', annotationRoutes);

// 错误处理中间件
app.use((err, req, res, next) => {
  console.error(err.stack);
  
  if (err.name === 'ValidationError') {
    return res.status(400).json({
      error: '验证错误',
      details: err.message
    });
  }
  
  if (err.code === 'P2002') {
    return res.status(409).json({
      error: '数据已存在',
      details: '该记录已存在'
    });
  }
  
  if (err.code === 'P2025') {
    return res.status(404).json({
      error: '未找到',
      details: '请求的资源不存在'
    });
  }
  
  res.status(500).json({
    error: '服务器内部错误',
    message: process.env.NODE_ENV === 'development' ? err.message : '服务器处理请求时发生错误'
  });
});

// 404处理
app.use('*', (req, res) => {
  res.status(404).json({
    error: '未找到',
    message: '请求的接口不存在'
  });
});

// 优雅关闭
process.on('SIGTERM', async () => {
  console.log('收到SIGTERM信号，开始优雅关闭...');
  await prisma.$disconnect();
  process.exit(0);
});

process.on('SIGINT', async () => {
  console.log('收到SIGINT信号，开始优雅关闭...');
  await prisma.$disconnect();
  process.exit(0);
});

module.exports = { app, prisma };