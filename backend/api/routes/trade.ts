import { ethers } from 'ethers';
import { Router } from 'express';
import { ValidationError } from '../middleware/errorHandler';
import { Trade } from '../models';
import { logger } from '../utils/logger';

const router = Router();

// Get recent trades with filtering
router.get('/recent', async (req, res, next) => {
  try {
    const {
      limit = 50,
      status,
      tokenA,
      tokenB,
      minProfit,
      maxGasUsed
    } = req.query;

    const query: any = {};

    if (status) query.status = status;
    if (tokenA) query.tokenA = tokenA;
    if (tokenB) query.tokenB = tokenB;
    if (minProfit) query.actualProfit = { $gte: minProfit };
    if (maxGasUsed) query.gasUsed = { $lte: maxGasUsed };

    const trades = await Trade.find(query)
      .sort({ createdAt: -1 })
      .limit(Number(limit));

    res.json({
      success: true,
      data: trades,
    });
  } catch (error) {
    next(error);
  }
});

// Get trade statistics with detailed metrics
router.get('/stats', async (req, res, next) => {
  try {
    const { timeframe = '24h' } = req.query;
    const timeframeMs = timeframe === '24h' ? 24 * 60 * 60 * 1000 : 7 * 24 * 60 * 60 * 1000;

    const trades = await Trade.find({
      createdAt: { $gte: new Date(Date.now() - timeframeMs) }
    });

    // Calculate detailed statistics
    const stats = {
      totalTrades: trades.length,
      successfulTrades: trades.filter(t => t.status === 'completed').length,
      failedTrades: trades.filter(t => t.status === 'failed').length,
      pendingTrades: trades.filter(t => t.status === 'pending').length,
      profitMetrics: {
        totalProfit: trades.reduce((sum, t) => sum + Number(t.actualProfit), 0).toString(),
        averageProfit: trades.length > 0
          ? (trades.reduce((sum, t) => sum + Number(t.actualProfit), 0) / trades.length).toString()
          : '0',
        maxProfit: trades.length > 0
          ? Math.max(...trades.map(t => Number(t.actualProfit))).toString()
          : '0',
        minProfit: trades.length > 0
          ? Math.min(...trades.map(t => Number(t.actualProfit))).toString()
          : '0'
      },
      gasMetrics: {
        totalGasUsed: trades.reduce((sum, t) => sum + Number(t.gasUsed), 0).toString(),
        averageGasUsed: trades.length > 0
          ? (trades.reduce((sum, t) => sum + Number(t.gasUsed), 0) / trades.length).toString()
          : '0',
        totalGasCost: trades.reduce((sum, t) =>
          sum + (Number(t.gasUsed) * Number(t.gasPrice)), 0).toString()
      },
      successRate: trades.length > 0
        ? ((trades.filter(t => t.status === 'completed').length / trades.length) * 100).toFixed(2)
        : '0',
      timeMetrics: {
        firstTradeTime: trades.length > 0
          ? Math.min(...trades.map(t => t.createdAt.getTime()))
          : null,
        lastTradeTime: trades.length > 0
          ? Math.max(...trades.map(t => t.createdAt.getTime()))
          : null,
        averageTradesPerHour: trades.length > 0
          ? (trades.length / (timeframeMs / (60 * 60 * 1000))).toFixed(2)
          : '0'
      }
    };

    res.json({
      success: true,
      data: stats,
    });
  } catch (error) {
    next(error);
  }
});

// Get trade by ID with detailed information
router.get('/:id', async (req, res, next) => {
  try {
    const trade = await Trade.findById(req.params.id);

    if (!trade) {
      throw new ValidationError('Trade not found');
    }

    // Calculate additional metrics
    const gasCost = (Number(trade.gasUsed) * Number(trade.gasPrice)).toString();
    const netProfit = (Number(trade.actualProfit) - Number(gasCost)).toString();

    res.json({
      success: true,
      data: {
        ...trade.toObject(),
        gasCost,
        netProfit,
        profitability: {
          roi: ((Number(netProfit) / Number(trade.amountIn)) * 100).toFixed(2) + '%',
          profitAfterGas: ethers.formatUnits(netProfit, 18)
        }
      },
    });
  } catch (error) {
    next(error);
  }
});

// Update trade details
router.patch('/:id', async (req, res, next) => {
  try {
    const {
      status,
      amountOut,
      actualProfit,
      gasUsed,
      gasPrice,
      error
    } = req.body;

    const updateData: any = {};
    if (status) updateData.status = status;
    if (amountOut) updateData.amountOut = amountOut;
    if (actualProfit) updateData.actualProfit = actualProfit;
    if (gasUsed) updateData.gasUsed = gasUsed;
    if (gasPrice) updateData.gasPrice = gasPrice;
    if (error) updateData.error = error;

    const trade = await Trade.findByIdAndUpdate(
      req.params.id,
      updateData,
      { new: true }
    );

    if (!trade) {
      throw new ValidationError('Trade not found');
    }

    logger.info('Trade updated:', {
      tradeId: trade._id,
      ...updateData
    });

    res.json({
      success: true,
      data: trade,
    });
  } catch (error) {
    next(error);
  }
});

// Get trade analytics
router.get('/analytics/summary', async (req, res, next) => {
  try {
    const { timeframe = '24h' } = req.query;
    const timeframeMs = timeframe === '24h' ? 24 * 60 * 60 * 1000 : 7 * 24 * 60 * 60 * 1000;

    // Get trades grouped by token pairs
    const tokenPairStats = await Trade.aggregate([
      {
        $match: {
          createdAt: { $gte: new Date(Date.now() - timeframeMs) }
        }
      },
      {
        $group: {
          _id: { tokenA: '$tokenA', tokenB: '$tokenB' },
          totalTrades: { $sum: 1 },
          successfulTrades: {
            $sum: { $cond: [{ $eq: ['$status', 'completed'] }, 1, 0] }
          },
          totalProfit: { $sum: { $toDouble: '$actualProfit' } },
          averageProfit: { $avg: { $toDouble: '$actualProfit' } },
          totalGasUsed: { $sum: { $toDouble: '$gasUsed' } }
        }
      },
      {
        $project: {
          tokenPair: '$_id',
          totalTrades: 1,
          successfulTrades: 1,
          totalProfit: 1,
          averageProfit: 1,
          totalGasUsed: 1,
          successRate: {
            $multiply: [
              { $divide: ['$successfulTrades', '$totalTrades'] },
              100
            ]
          }
        }
      },
      { $sort: { totalProfit: -1 } }
    ]);

    res.json({
      success: true,
      data: tokenPairStats,
    });
  } catch (error) {
    next(error);
  }
});

export default router;
