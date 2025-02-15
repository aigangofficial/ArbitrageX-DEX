import { Router } from 'express';
import { Trade } from '../../database/models';
import { ValidationError } from '../middleware/errorHandler';
import { marketDataLimiter } from '../middleware/rateLimit';

interface TradeStats {
  _id: string;
  count: number;
  totalProfit: number;
  avgGasUsed: number;
}

const router = Router();

// Get trade history with pagination
router.get('/', marketDataLimiter, async (req, res, next) => {
  try {
    const page = parseInt(req.query.page as string) || 1;
    const limit = parseInt(req.query.limit as string) || 10;
    const status = req.query.status as string;
    const network = req.query.network as string;

    const query: any = {};
    if (status) query.status = status;
    if (network) query.network = network;

    const skip = (page - 1) * limit;
    const trades = await Trade.find(query)
      .sort({ timestamp: -1 })
      .skip(skip)
      .limit(limit)
      .lean();

    const total = await Trade.countDocuments(query);

    res.json({
      success: true,
      data: trades,
      pagination: {
        page,
        limit,
        total,
        pages: Math.ceil(total / limit),
      },
    });
  } catch (error) {
    next(error);
  }
});

// Get trade by ID
router.get('/:id', marketDataLimiter, async (req, res, next) => {
  try {
    const trade = await Trade.findById(req.params.id).lean();
    if (!trade) {
      throw new ValidationError('Trade not found');
    }

    res.json({
      success: true,
      data: trade,
    });
  } catch (error) {
    next(error);
  }
});

// Get trade statistics
router.get('/stats/:network', marketDataLimiter, async (req, res, next) => {
  try {
    const { network } = req.params;
    const timeframe = (req.query.timeframe as 'day' | 'week' | 'month') || 'day';

    // Use aggregation pipeline directly since static method is not defined
    const since = new Date();
    switch (timeframe) {
      case 'week':
        since.setDate(since.getDate() - 7);
        break;
      case 'month':
        since.setMonth(since.getMonth() - 1);
        break;
      default:
        since.setDate(since.getDate() - 1);
    }

    const stats = await Trade.aggregate([
      {
        $match: {
          network,
          timestamp: { $gte: since },
        },
      },
      {
        $group: {
          _id: '$status',
          count: { $sum: 1 },
          totalProfit: {
            $sum: {
              $cond: [
                { $eq: ['$status', 'completed'] },
                { $toDouble: { $ifNull: ['$profit', '0'] } },
                0,
              ],
            },
          },
          avgGasUsed: {
            $avg: {
              $cond: [
                { $eq: ['$status', 'completed'] },
                { $toDouble: { $ifNull: ['$gasUsed', '0'] } },
                0,
              ],
            },
          },
        },
      },
    ]);

    res.json({
      success: true,
      data: {
        timeframe,
        stats,
      },
    });
  } catch (error) {
    next(error);
  }
});

// Get recent successful trades
router.get('/successful/recent', marketDataLimiter, async (req, res, next) => {
  try {
    const limit = parseInt(req.query.limit as string) || 10;
    const trades = await Trade.find({ status: 'completed' })
      .sort({ timestamp: -1 })
      .limit(limit)
      .lean();

    res.json({
      success: true,
      data: trades,
    });
  } catch (error) {
    next(error);
  }
});

// Get trades by token pair
router.get('/pair/:tokenA/:tokenB', marketDataLimiter, async (req, res, next) => {
  try {
    const { tokenA, tokenB } = req.params;
    const limit = parseInt(req.query.limit as string) || 10;

    if (!tokenA || !tokenB) {
      throw new ValidationError('Token addresses are required');
    }

    const trades = await Trade.find({
      tokenA,
      tokenB,
    })
      .sort({ timestamp: -1 })
      .limit(limit)
      .lean();

    res.json({
      success: true,
      data: trades,
    });
  } catch (error) {
    next(error);
  }
});

// Get trade performance metrics
router.get('/performance/:network', marketDataLimiter, async (req, res, next) => {
  try {
    const { network } = req.params;
    const timeframe = (req.query.timeframe as 'day' | 'week' | 'month') || 'day';

    // Use aggregation pipeline directly since static method is not defined
    const since = new Date();
    switch (timeframe) {
      case 'week':
        since.setDate(since.getDate() - 7);
        break;
      case 'month':
        since.setMonth(since.getMonth() - 1);
        break;
      default:
        since.setDate(since.getDate() - 1);
    }

    const stats = await Trade.aggregate<TradeStats>([
      {
        $match: {
          network,
          timestamp: { $gte: since },
        },
      },
      {
        $group: {
          _id: '$status',
          count: { $sum: 1 },
          totalProfit: {
            $sum: {
              $cond: [
                { $eq: ['$status', 'completed'] },
                { $toDouble: { $ifNull: ['$profit', '0'] } },
                0,
              ],
            },
          },
          avgGasUsed: {
            $avg: {
              $cond: [
                { $eq: ['$status', 'completed'] },
                { $toDouble: { $ifNull: ['$gasUsed', '0'] } },
                0,
              ],
            },
          },
        },
      },
    ]);

    // Calculate success rate and other metrics
    const totalTrades = stats.reduce((sum: number, stat: TradeStats) => sum + stat.count, 0);
    const completedTrades = stats.find((stat: TradeStats) => stat._id === 'completed');
    const failedTrades = stats.find((stat: TradeStats) => stat._id === 'failed');

    const metrics = {
      totalTrades,
      successRate: completedTrades
        ? (completedTrades.count / totalTrades) * 100
        : 0,
      failureRate: failedTrades ? (failedTrades.count / totalTrades) * 100 : 0,
      totalProfit: completedTrades ? completedTrades.totalProfit : 0,
      avgGasUsed: completedTrades ? completedTrades.avgGasUsed : 0,
    };

    res.json({
      success: true,
      data: {
        timeframe,
        metrics,
        details: stats,
      },
    });
  } catch (error) {
    next(error);
  }
});

export default router;
