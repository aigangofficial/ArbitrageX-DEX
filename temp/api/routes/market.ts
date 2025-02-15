import { Router } from 'express';
import { MarketData } from '../../database/models';
import { WebSocketService } from '../../websocket/server';
import { ValidationError } from '../middleware/errorHandler';
import {
    marketDataLimiter,
    opportunitiesLimiter,
    volatilityLimiter,
    wsSubscriptionLimiter,
} from '../middleware/rateLimit';

const router = Router();
const wsService = new WebSocketService();

// Get latest market data for a token pair
router.get('/data/:tokenA/:tokenB', marketDataLimiter, async (req, res, next) => {
  try {
    const { tokenA, tokenB } = req.params;
    const limit = parseInt(req.query.limit as string) || 100;

    if (!tokenA || !tokenB) {
      throw new ValidationError('Token addresses are required');
    }

    const marketData = await MarketData.find({
      tokenA,
      tokenB,
    })
      .sort({ timestamp: -1 })
      .limit(limit)
      .lean();

    res.json({
      success: true,
      data: marketData,
    });
  } catch (error) {
    next(error);
  }
});

// Get market volatility for a token pair
router.get('/volatility/:tokenA/:tokenB', volatilityLimiter, async (req, res, next) => {
  try {
    const { tokenA, tokenB } = req.params;
    const timeframe = parseInt(req.query.timeframe as string) || 24; // hours

    if (!tokenA || !tokenB) {
      throw new ValidationError('Token addresses are required');
    }

    const since = new Date(Date.now() - timeframe * 60 * 60 * 1000);
    const pipeline = [
      {
        $match: {
          tokenA,
          tokenB,
          timestamp: { $gte: since },
        },
      },
      {
        $group: {
          _id: '$exchange',
          avgPrice: { $avg: '$price' },
          maxPrice: { $max: '$price' },
          minPrice: { $min: '$price' },
          priceStdDev: { $stdDevPop: '$price' },
          dataPoints: { $sum: 1 },
        },
      },
    ];

    const volatilityData = await MarketData.aggregate(pipeline);

    res.json({
      success: true,
      data: {
        timeframe,
        metrics: volatilityData,
      },
    });
  } catch (error) {
    next(error);
  }
});

// Get market summary
router.get('/summary', marketDataLimiter, async (req, res, next) => {
  try {
    const pipeline = [
      {
        $group: {
          _id: {
            tokenA: '$tokenA',
            tokenB: '$tokenB',
          },
          exchanges: { $addToSet: '$exchange' },
          maxSpread: { $max: '$spread' },
          avgSpread: { $avg: '$spread' },
          totalLiquidity: { $sum: '$liquidity' },
          lastUpdate: { $max: '$timestamp' },
        },
      },
      {
        $match: {
          'exchanges.1': { $exists: true }, // Only pairs available on multiple exchanges
        },
      },
      {
        $sort: {
          'maxSpread': -1 as const,
        },
      },
      {
        $limit: 10,
      },
    ] as const;

    const summary = await MarketData.aggregate(pipeline);

    res.json({
      success: true,
      data: summary,
    });
  } catch (error) {
    next(error);
  }
});

// Get market depth
router.get('/depth/:tokenA/:tokenB', marketDataLimiter, async (req, res, next) => {
  try {
    const { tokenA, tokenB } = req.params;
    const exchange = req.query.exchange as string;

    if (!tokenA || !tokenB) {
      throw new ValidationError('Token addresses are required');
    }

    const query: any = {
      tokenA,
      tokenB,
    };

    if (exchange) {
      query.exchange = exchange;
    }

    const depthData = await MarketData.find(query)
      .select('exchange liquidity price timestamp')
      .sort({ timestamp: -1 })
      .limit(1)
      .lean();

    res.json({
      success: true,
      data: depthData,
    });
  } catch (error) {
    next(error);
  }
});

// Get arbitrage opportunities
router.get('/opportunities', opportunitiesLimiter, async (req, res, next) => {
  try {
    const minSpread = parseFloat(req.query.minSpread as string) || 0.5;

    const opportunities = await MarketData.findArbitrageOpportunities(minSpread);

    res.json({
      success: true,
      data: opportunities,
    });
  } catch (error) {
    next(error);
  }
});

// Subscribe to real-time price updates
router.post('/subscribe', wsSubscriptionLimiter, async (req, res, next) => {
  try {
    const { pairs } = req.body;

    if (!pairs || !Array.isArray(pairs) || pairs.length === 0) {
      throw new ValidationError('At least one trading pair is required');
    }

    // Broadcast initial data for each pair
    for (const pair of pairs) {
      const latestData = await MarketData.findOne({ pair }).sort({ timestamp: -1 }).lean();

      if (latestData) {
        wsService.broadcast(
          {
            type: 'PRICE_UPDATE',
            data: latestData,
          },
          'prices'
        );
      }
    }

    res.json({
      success: true,
      message: 'Subscribed to price updates',
      subscribedPairs: pairs,
    });
  } catch (error) {
    next(error);
  }
});

export default router;
