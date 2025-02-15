import { Router } from 'express';
import { marketDataLimiter } from '../middleware/rateLimit';
import arbitrageRoutes from './arbitrage';
import marketRoutes from './market';
import testRoutes from './test';
import tradeRoutes from './trade';

const router = Router();

// Health check endpoint
router.get('/health', (_req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: process.env.npm_package_version || '1.0.0',
  });
});

// API Routes with versioning
router.use('/v1/arbitrage', arbitrageRoutes);
router.use('/v1/market', marketDataLimiter, marketRoutes);
router.use('/v1/trades', tradeRoutes);

// Test routes (only in development)
if (process.env.NODE_ENV === 'development') {
  router.use('/test', testRoutes);
}

export default router;
