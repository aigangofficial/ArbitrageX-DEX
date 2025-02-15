import { Router } from 'express';
import { Trade } from '../../database/models';
import { ValidationError } from '../middleware/errorHandler';
import { logger } from '../utils/logger';

const router = Router();

// Get recent trades
router.get('/recent', async (req, res, next) => {
  try {
    const { limit = 50 } = req.query;

    const trades = await Trade.find().sort({ timestamp: -1 }).limit(Number(limit));

    res.json({
      success: true,
      data: trades,
    });
  } catch (error) {
    next(error);
  }
});

// Get trade statistics
router.get('/stats', async (req, res, next) => {
  try {
    const { timeframe = '24h' } = req.query;

    const stats = await Trade.getStatistics(timeframe as string);

    res.json({
      success: true,
      data: stats,
    });
  } catch (error) {
    next(error);
  }
});

// Get trade by ID
router.get('/:id', async (req, res, next) => {
  try {
    const trade = await Trade.findById(req.params.id);

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

// Create new trade record
router.post('/', async (req, res, next) => {
  try {
    const { tokenA, tokenB, amountA, amountB, type, status = 'pending' } = req.body;

    if (!tokenA || !tokenB || !amountA || !amountB || !type) {
      throw new ValidationError('Missing required trade parameters');
    }

    const trade = await Trade.create({
      tokenA,
      tokenB,
      amountA,
      amountB,
      type,
      status,
      timestamp: new Date(),
    });

    logger.info('New trade created:', {
      tradeId: trade._id,
      type,
      status,
    });

    res.status(201).json({
      success: true,
      data: trade,
    });
  } catch (error) {
    next(error);
  }
});

// Update trade status
router.patch('/:id/status', async (req, res, next) => {
  try {
    const { status } = req.body;

    if (!status) {
      throw new ValidationError('Status is required');
    }

    const trade = await Trade.findByIdAndUpdate(req.params.id, { status }, { new: true });

    if (!trade) {
      throw new ValidationError('Trade not found');
    }

    logger.info('Trade status updated:', {
      tradeId: trade._id,
      status,
    });

    res.json({
      success: true,
      data: trade,
    });
  } catch (error) {
    next(error);
  }
});

export default router;
