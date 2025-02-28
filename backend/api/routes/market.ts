import { Router } from 'express';
import { logger } from '../utils/logger';

export function createMarketRouter() {
  const router = Router();

  router.get('/data', async (req, res) => {
    try {
      // For testing purposes, return some mock market data
      res.json({
        success: true,
        data: {
          timestamp: new Date().toISOString(),
          prices: {
            'ETH/USDC': '2500.00',
            'BTC/USDC': '50000.00',
            'ETH/BTC': '0.05'
          },
          volumes: {
            'ETH/USDC': '1000000',
            'BTC/USDC': '5000000',
            'ETH/BTC': '100'
          }
        }
      });
    } catch (error) {
      logger.error('Error fetching market data:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to fetch market data'
      });
    }
  });

  return router;
}
