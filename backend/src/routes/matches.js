const express = require('express');
const { PrismaClient } = require('@prisma/client');
const { body, validationResult } = require('express-validator');
const auth = require('../middleware/auth');

const router = express.Router();
const prisma = new PrismaClient();

// 获取比赛列表
router.get('/', async (req, res) => {
  try {
    const { 
      page = 1, 
      limit = 20, 
      tournament, 
      team, 
      dateFrom, 
      dateTo 
    } = req.query;

    const skip = (page - 1) * limit;
    const where = {};

    if (tournament) {
      where.tournament = { contains: tournament };
    }

    if (team) {
      where.OR = [
        { radiantTeam: { contains: team } },
        { direTeam: { contains: team } }
      ];
    }

    if (dateFrom || dateTo) {
      where.startTime = {};
      if (dateFrom) where.startTime.gte = new Date(dateFrom);
      if (dateTo) where.startTime.lte = new Date(dateTo);
    }

    const matches = await prisma.match.findMany({
      where,
      skip: parseInt(skip),
      take: parseInt(limit),
      orderBy: { startTime: 'desc' },
      include: {
        comments: {
          select: {
            id: true,
            _count: true
          }
        },
        expertAnnotations: {
          select: {
            id: true,
            analystName: true
          }
        }
      }
    });

    const total = await prisma.match.count({ where });

    res.json({
      matches,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total,
        pages: Math.ceil(total / limit)
      }
    });
  } catch (error) {
    console.error('获取比赛列表错误:', error);
    res.status(500).json({ error: '获取比赛列表失败' });
  }
});

// 获取单个比赛详情
router.get('/:id', async (req, res) => {
  try {
    const { id } = req.params;

    const match = await prisma.match.findUnique({
      where: { id },
      include: {
        comments: {
          include: {
            user: {
              select: {
                id: true,
                username: true,
                avatar: true
              }
            },
            qualityVotes: true
          },
          orderBy: { createdAt: 'desc' }
        },
        expertAnnotations: {
          include: {
            analyst: {
              select: {
                id: true,
                username: true,
                avatar: true
              }
            }
          }
        }
      }
    });

    if (!match) {
      return res.status(404).json({ error: '比赛不存在' });
    }

    res.json(match);
  } catch (error) {
    console.error('获取比赛详情错误:', error);
    res.status(500).json({ error: '获取比赛详情失败' });
  }
});

// 创建比赛
router.post('/', [
  auth,
  body('matchId').isString().notEmpty(),
  body('title').isString().notEmpty(),
  body('radiantTeam').isString().notEmpty(),
  body('direTeam').isString().notEmpty(),
  body('duration').isInt({ min: 0 }),
  body('winner').isIn(['radiant', 'dire']),
  body('tournament').optional().isString()
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const {
      matchId,
      title,
      radiantTeam,
      direTeam,
      duration,
      winner,
      tournament,
      ...otherData
    } = req.body;

    const match = await prisma.match.create({
      data: {
        matchId,
        title,
        radiantTeam,
        direTeam,
        duration,
        winner,
        tournament,
        ...otherData,
        createdBy: req.user.id
      }
    });

    res.status(201).json(match);
  } catch (error) {
    console.error('创建比赛错误:', error);
    res.status(500).json({ error: '创建比赛失败' });
  }
});

// 更新比赛
router.put('/:id', [
  auth,
  body('title').optional().isString().notEmpty(),
  body('duration').optional().isInt({ min: 0 }),
  body('winner').optional().isIn(['radiant', 'dire'])
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { id } = req.params;
    const updateData = req.body;

    const match = await prisma.match.update({
      where: { id },
      data: updateData
    });

    res.json(match);
  } catch (error) {
    console.error('更新比赛错误:', error);
    res.status(500).json({ error: '更新比赛失败' });
  }
});

// 删除比赛
router.delete('/:id', auth, async (req, res) => {
  try {
    const { id } = req.params;

    await prisma.match.delete({
      where: { id }
    });

    res.json({ message: '比赛删除成功' });
  } catch (error) {
    console.error('删除比赛错误:', error);
    res.status(500).json({ error: '删除比赛失败' });
  }
});

module.exports = router;