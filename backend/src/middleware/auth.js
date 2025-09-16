const jwt = require('jsonwebtoken');
const { PrismaClient } = require('@prisma/client');

const prisma = new PrismaClient();

const auth = async (req, res, next) => {
  try {
    const token = req.header('Authorization')?.replace('Bearer ', '');
    
    if (!token) {
      return res.status(401).json({ error: '访问被拒绝，请提供有效的token' });
    }

    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    const user = await prisma.user.findUnique({
      where: { id: decoded.userId },
      select: {
        id: true,
        username: true,
        email: true,
        role: true,
        avatar: true,
        reputation: true,
        createdAt: true
      }
    });

    if (!user) {
      return res.status(401).json({ error: '用户不存在' });
    }

    req.user = user;
    next();
  } catch (error) {
    console.error('认证错误:', error);
    res.status(401).json({ error: '无效的token' });
  }
};

const optionalAuth = async (req, res, next) => {
  try {
    const token = req.header('Authorization')?.replace('Bearer ', '');
    
    if (token) {
      const decoded = jwt.verify(token, process.env.JWT_SECRET);
      const user = await prisma.user.findUnique({
        where: { id: decoded.userId },
        select: {
          id: true,
          username: true,
          email: true,
          role: true,
          avatar: true,
          reputation: true,
          createdAt: true
        }
      });
      
      if (user) {
        req.user = user;
      }
    }
    
    next();
  } catch (error) {
    // 可选认证，token无效时继续
    next();
  }
};

const adminAuth = async (req, res, next) => {
  try {
    const token = req.header('Authorization')?.replace('Bearer ', '');
    
    if (!token) {
      return res.status(401).json({ error: '访问被拒绝，请提供有效的token' });
    }

    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    const user = await prisma.user.findUnique({
      where: { id: decoded.userId },
      select: {
        id: true,
        username: true,
        email: true,
        role: true
      }
    });

    if (!user) {
      return res.status(401).json({ error: '用户不存在' });
    }

    if (user.role !== 'ADMIN' && user.role !== 'MODERATOR') {
      return res.status(403).json({ error: '权限不足' });
    }

    req.user = user;
    next();
  } catch (error) {
    console.error('管理员认证错误:', error);
    res.status(401).json({ error: '无效的token' });
  }
};

module.exports = { auth, optionalAuth, adminAuth };