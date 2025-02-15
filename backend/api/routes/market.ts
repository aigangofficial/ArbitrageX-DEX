import { Router } from 'express';
import { MarketData } from '../../database/models';
import { ValidationError } from '../middleware/errorHandler';
import { marketDataLimiter, opportunitiesLimiter, volatilityLimiter } from '../middleware/rateLimit';

const router = Router();

// Get recent market data for a token pair
router.get('/data', marketDataLimiter, async (req, res, next) => {
  try {
    const { tokenA, tokenB, limit = 100 } = req.query;

    if (!tokenA || !tokenB) {
      throw new ValidationError('Token addresses are required');
    }

    const data = await MarketData.find({
      tokenA,
      tokenB,
    })
      .sort({ timestamp: -1 })
      .limit(Number(limit));

    res.json({
      success: true,
      data,
    });
  } catch (error) {
    next(error);
  }
});

// Get market volatility for a token pair
router.get('/volatility', volatilityLimiter, async (req, res, next) => {
  try {
    const { tokenA, tokenB, hours = 24 } = req.query;

    if (!tokenA || !tokenB) {
      throw new ValidationError('Token addresses are required');
    }

    const volatility = await MarketData.getVolatility(
      `${tokenA}-${tokenB}`,
      Number(hours)
    );

    res.json({
      success: true,
      data: volatility,
    });
  } catch (error) {
    next(error);
  }
});

// Get arbitrage opportunities
router.get('/opportunities', opportunitiesLimiter, async (req, res, next) => {
  try {
    const { minSpread = 0.5 } = req.query;

    const opportunities = await MarketData.findArbitrageOpportunities(
      Number(minSpread)
    );

    res.json({
      success: true,
      data: opportunities,
    });
  } catch (error) {
    next(error);
  }
});

export default router;
