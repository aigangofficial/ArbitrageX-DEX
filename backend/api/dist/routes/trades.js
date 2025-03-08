"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.createTradeRouter = void 0;
const express_1 = require("express");
const TradeHistory_1 = require("../models/TradeHistory");
const BotStatus_1 = require("../models/BotStatus");
const logger_1 = require("../utils/logger");
const router = (0, express_1.Router)();
const createTradeRouter = (wsService) => {
    // Get latest trades
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
    // Get trade by ID
    router.get('/:txHash', async (req, res) => {
        try {
            const trade = await TradeHistory_1.TradeHistory.findOne({ txHash: req.params.txHash });
            if (!trade) {
                return res.status(404).json({ success: false, error: 'Trade not found' });
            }
            res.json({ success: true, trade });
        }
        catch (error) {
            logger_1.logger.error('Error fetching trade:', error);
            res.status(500).json({ success: false, error: 'Failed to fetch trade' });
        }
    });
    // Execute new arbitrage trade
    router.post('/execute', async (req, res) => {
        try {
            const { tokenIn, tokenOut, amount, router } = req.body;
            // Validate input
            if (!tokenIn || !tokenOut || !amount || !router) {
                return res.status(400).json({
                    success: false,
                    error: 'Missing required parameters'
                });
            }
            // Create pending trade record
            const trade = new TradeHistory_1.TradeHistory({
                tokenIn,
                tokenOut,
                amountIn: amount,
                amountOut: '0', // Will be updated after execution
                profit: '0',
                gasUsed: 0,
                gasPrice: '0',
                txHash: '', // Will be updated after execution
                blockNumber: 0,
                timestamp: new Date(),
                router,
                status: 'pending'
            });
            await trade.save();
            // Broadcast trade initiation
            wsService.broadcastTradeUpdate({
                ...trade.toJSON(),
                event: 'trade_initiated'
            });
            // Return immediately with pending status
            res.json({
                success: true,
                message: 'Trade initiated',
                tradeId: trade._id
            });
            // Execute trade asynchronously
            // Note: Actual trade execution will be handled by the bot
            // This endpoint only initiates the process
        }
        catch (error) {
            logger_1.logger.error('Error executing trade:', error);
            res.status(500).json({
                success: false,
                error: 'Failed to execute trade'
            });
        }
    });
    // Get trade statistics
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
};
exports.createTradeRouter = createTradeRouter;
//# sourceMappingURL=trades.js.map