"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.createTradeRouter = createTradeRouter;
const express_1 = require("express");
const TradeHistory_1 = require("../models/TradeHistory");
const BotStatus_1 = require("../models/BotStatus");
const logger_1 = require("../utils/logger");
const router = (0, express_1.Router)();
function createTradeRouter(wsService) {
    router.get('/', async (req, res) => {
        try {
            const limit = parseInt(req.query.limit) || 10;
            const trades = await TradeHistory_1.TradeHistory.find()
                .sort({ timestamp: -1 })
                .limit(limit);
            res.json({ success: true, trades });
        }
        catch (error) {
            logger_1.logger.error('Error fetching trades:', error);
            res.status(500).json({ success: false, error: 'Failed to fetch trades' });
        }
    });
    router.get('/:txHash', async (req, res) => {
        try {
            const { txHash } = req.params;
            if (!txHash || typeof txHash !== 'string') {
                return res.status(400).json({ error: 'Invalid transaction hash' });
            }
            const trade = await findTradeByTxHash(txHash);
            if (!trade) {
                return res.status(404).json({ error: 'Trade not found' });
            }
            return res.json(trade);
        }
        catch (error) {
            logger_1.logger.error('Error fetching trade:', error);
            return res.status(500).json({ error: 'Internal server error' });
        }
    });
    router.post('/execute', async (req, res) => {
        try {
            const { trade } = req.body;
            if (!trade) {
                return res.status(400).json({ error: 'Missing trade data' });
            }
            if (!validateTradeParams(trade)) {
                return res.status(400).json({ error: 'Invalid trade parameters' });
            }
            const result = await executeTrade(trade);
            wsService.broadcast('trade_executed', {
                txHash: result.txHash,
                status: result.status,
                timestamp: new Date()
            });
            return res.json(result);
        }
        catch (error) {
            logger_1.logger.error('Error executing trade:', error);
            return res.status(500).json({ error: 'Internal server error' });
        }
    });
    router.get('/stats', async (req, res) => {
        try {
            const [stats, botStatus] = await Promise.all([
                TradeHistory_1.TradeHistory.aggregate([
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
                BotStatus_1.BotStatus.findOne().sort({ lastHeartbeat: -1 })
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
        }
        catch (error) {
            logger_1.logger.error('Error fetching trade stats:', error);
            res.status(500).json({
                success: false,
                error: 'Failed to fetch trade statistics'
            });
        }
    });
    return router;
}
async function findTradeByTxHash(txHash) {
    return null;
}
function validateTradeParams(trade) {
    return true;
}
async function executeTrade(trade) {
    return {
        txHash: '0x...',
        status: 'pending'
    };
}
//# sourceMappingURL=trades.js.map