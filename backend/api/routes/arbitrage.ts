import { Router } from 'express';
import { MarketData } from '../../database/models';
import { ValidationError } from '../middleware/errorHandler';
import { logger } from '../utils/logger';

const router = Router();

// Get active arbitrage opportunities
router.get('/opportunities', async (req, res, next) => {
  try {
    const { minSpread = 0.5 } = req.query;

    const opportunities = await MarketData.findArbitrageOpportunities(Number(minSpread));

    res.json({
      success: true,
      data: opportunities,
    });
  } catch (error) {
    next(error);
  }
});

// Get arbitrage statistics
router.get('/stats', async (req, res, next) => {
  try {
    const { timeframe = '24h' } = req.query;
    const stats = await MarketData.getVolatility(`arbitrage-${timeframe}`);

    res.json({
      success: true,
      data: stats,
    });
  } catch (error) {
    next(error);
  }
});

// Execute arbitrage trade
router.post('/execute', async (req, res, next) => {
  try {
    const { tokenA, tokenB, amount, route } = req.body;

    if (!tokenA || !tokenB || !amount || !route) {
      throw new ValidationError('Missing required parameters');
    }

    // Log the trade attempt
    logger.info('Arbitrage trade execution requested:', {
      tokenA,
      tokenB,
      amount,
      route,
    });

    // For now, just return a mock response
    res.json({
      success: true,
      data: {
        status: 'pending',
        tokenA,
        tokenB,
        amount,
        route,
        timestamp: new Date(),
      },
    });
  } catch (error) {
    next(error);
  }
});

export default router;
