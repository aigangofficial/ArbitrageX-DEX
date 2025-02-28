import { Router } from 'express';
import { TradeHistory } from '../models/TradeHistory';
import { BotStatus } from '../models/BotStatus';
import { WebSocketService } from '../websocket/WebSocketService';
import { logger } from '../utils/logger';

const router = Router();

export function createTradeRouter(wsService: WebSocketService) {
  // Get latest trades
  router.get('/', async (req, res) => {
    try {
      const limit = parseInt(req.query.limit as string) || 10;
      const trades = await TradeHistory.find()
        .sort({ timestamp: -1 })
        .limit(limit);
      res.json({ success: true, trades });
    } catch (error) {
      logger.error('Error fetching trades:', error);
      res.status(500).json({ success: false, error: 'Failed to fetch trades' });
    }
  });

  // Get trade by ID
  router.get('/:txHash', async (req, res) => {
    try {
      const { txHash } = req.params;

      if (!txHash || typeof txHash !== 'string') {
        return res.status(400).json({ error: 'Invalid transaction hash' });
      }

      // TODO: Implement trade lookup from database
      const trade = await findTradeByTxHash(txHash);

      if (!trade) {
        return res.status(404).json({ error: 'Trade not found' });
      }

      return res.json(trade);
    } catch (error) {
      logger.error('Error fetching trade:', error);
      return res.status(500).json({ error: 'Internal server error' });
    }
  });

  // Execute new arbitrage trade
  router.post('/execute', async (req, res) => {
    try {
      const { trade } = req.body;

      if (!trade) {
        return res.status(400).json({ error: 'Missing trade data' });
      }

      // Validate trade parameters
      if (!validateTradeParams(trade)) {
        return res.status(400).json({ error: 'Invalid trade parameters' });
      }

      // Execute trade
      const result = await executeTrade(trade);

      // Notify connected clients via WebSocket
      wsService.broadcast('trade_executed', {
        txHash: result.txHash,
        status: result.status,
        timestamp: new Date()
      });

      return res.json(result);
    } catch (error) {
      logger.error('Error executing trade:', error);
      return res.status(500).json({ error: 'Internal server error' });
    }
  });

  // Get trade statistics
  router.get('/stats', async (req, res) => {
    try {
      const [stats, botStatus] = await Promise.all([
        TradeHistory.aggregate([
          {
            $group: {
              _id: null,
              totalTrades: { $sum: 1 },
              successfulTrades: {
                $sum: { $cond: [{ $eq: ['$status', 'completed'] }, 1, 0] }
              },
              failedTrades: {
                $sum: { $cond: [{ $eq: ['$status', 'failed'] }, 1, 0] }
              },
              totalProfit: { $sum: { $toDecimal: '$profit' } },
              avgGasUsed: { $avg: '$gasUsed' }
            }
          }
        ]),
        BotStatus.findOne().sort({ lastHeartbeat: -1 })
      ]);

      res.json({
        success: true,
        stats: stats[0] || {
          totalTrades: 0,
          successfulTrades: 0,
          failedTrades: 0,
          totalProfit: '0',
          avgGasUsed: 0
        },
        botStatus: botStatus || { isActive: false }
      });
    } catch (error) {
      logger.error('Error fetching trade stats:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to fetch trade statistics'
      });
    }
  });

  return router;
}

// Helper functions (to be implemented)
async function findTradeByTxHash(txHash: string) {
  // TODO: Implement database lookup
  return null;
}

function validateTradeParams(trade: any) {
  // TODO: Implement trade validation
  return true;
}

async function executeTrade(trade: any) {
  // TODO: Implement trade execution
  return {
    txHash: '0x...',
    status: 'pending'
  };
} 