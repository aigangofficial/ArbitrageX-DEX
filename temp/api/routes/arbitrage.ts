import { ethers } from 'ethers';
import { Router } from 'express';
import { Trade } from '../../database/models';
import { ArbitrageScanner } from '../../execution/arbitrageScanner';
import { config } from '../config';
import { ValidationError } from '../middleware/errorHandler';
import { logger } from '../utils/logger';

const router = Router();

// Initialize provider and scanner
const provider = new ethers.JsonRpcProvider(config.network.rpc);
const scanner = new ArbitrageScanner(
  provider,
  null as any, // WebSocket server will be initialized in server.ts
  config.contracts.flashLoanService,
  config.contracts.quickswapRouter,
  config.contracts.sushiswapRouter,
  config.contracts.wmatic
);

// Start scanning for arbitrage opportunities
router.post('/start', async (_req, res, next) => {
  try {
    if (scanner.getIsScanning()) {
      return res.json({
        success: true,
        message: 'Scanner is already running',
      });
    }

    await scanner.startScanning();
    res.json({
      success: true,
      message: 'Arbitrage scanner started',
    });
  } catch (error) {
    next(error);
  }
});

// Stop scanning for arbitrage opportunities
router.post('/stop', (_req, res) => {
  scanner.stopScanning();
  res.json({
    success: true,
    message: 'Arbitrage scanner stopped',
  });
});

// Get scanner status
router.get('/status', (_req, res) => {
  res.json({
    success: true,
    isScanning: scanner.getIsScanning(),
  });
});

// Execute arbitrage trade
router.post('/execute', async (req, res, next) => {
  try {
    const { tokenA, tokenB, amount, route } = req.body;

    if (!tokenA || !tokenB || !amount || !route) {
      throw new ValidationError('Missing required parameters');
    }

    // Validate addresses
    if (!ethers.isAddress(tokenA) || !ethers.isAddress(tokenB)) {
      throw new ValidationError('Invalid token addresses');
    }

    // Validate route
    if (!['UNIV2_TO_SUSHI', 'SUSHI_TO_UNIV2'].includes(route)) {
      throw new ValidationError('Invalid route');
    }

    // Create trade record
    const trade = await Trade.create({
      tokenA,
      tokenB,
      amountIn: amount,
      route,
      status: 'pending',
      timestamp: new Date(),
      network: config.network.name,
    });

    // Execute trade asynchronously
    executeTradeAsync(trade._id, tokenA, tokenB, amount, route === 'UNIV2_TO_SUSHI')
      .then(() => {
        logger.info(`Trade ${trade._id} execution started`);
      })
      .catch(error => {
        logger.error(`Trade ${trade._id} execution failed:`, error);
      });

    res.json({
      success: true,
      message: 'Trade execution started',
      tradeId: trade._id,
    });
  } catch (error) {
    next(error);
  }
});

// Get trade status
router.get('/trade/:id', async (req, res, next) => {
  try {
    const trade = await Trade.findById(req.params.id);
    if (!trade) {
      throw new ValidationError('Trade not found');
    }

    res.json({
      success: true,
      trade,
    });
  } catch (error) {
    next(error);
  }
});

// Get recent trades
router.get('/trades', async (req, res, next) => {
  try {
    const page = parseInt(req.query.page as string) || 1;
    const limit = parseInt(req.query.limit as string) || 10;
    const skip = (page - 1) * limit;

    const trades = await Trade.find()
      .sort({ timestamp: -1 })
      .skip(skip)
      .limit(limit)
      .lean();

    const total = await Trade.countDocuments();

    res.json({
      success: true,
      trades,
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

async function executeTradeAsync(
  tradeId: string,
  tokenA: string,
  tokenB: string,
  amount: string,
  useUniswapFirst: boolean
): Promise<void> {
  try {
    // Update trade status to executing
    await Trade.findByIdAndUpdate(tradeId, { status: 'executing' });

    // Execute trade logic here
    // This would involve calling the smart contract functions

    // Update trade status to completed
    await Trade.findByIdAndUpdate(tradeId, { status: 'completed' });
  } catch (error) {
    // Update trade status to failed
    await Trade.findByIdAndUpdate(tradeId, {
      status: 'failed',
      errorMessage: error instanceof Error ? error.message : 'Unknown error',
    });
    throw error;
  }
}

export default router;
