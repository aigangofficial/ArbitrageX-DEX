"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = require("express");
const config_1 = require("../config");
const errorHandler_1 = require("../middleware/errorHandler");
const models_1 = require("../models");
const router = (0, express_1.Router)();
router.get('/opportunities', async (req, res) => {
    try {
        res.json({
            opportunities: [],
            timestamp: new Date().toISOString()
        });
    }
    catch (error) {
        res.status(500).json({
            error: 'Failed to fetch arbitrage opportunities',
            message: error instanceof Error ? error.message : 'Unknown error'
        });
    }
});
router.get('/history', async (req, res) => {
    try {
        res.json({
            trades: [],
            timestamp: new Date().toISOString()
        });
    }
    catch (error) {
        res.status(500).json({
            error: 'Failed to fetch trade history',
            message: error instanceof Error ? error.message : 'Unknown error'
        });
    }
});
router.post('/execute', async (req, res) => {
    try {
        const { tokenA, tokenB, amount } = req.body;
        res.json({
            status: 'pending',
            trade: {
                tokenA,
                tokenB,
                amount,
                timestamp: new Date().toISOString()
            }
        });
    }
    catch (error) {
        res.status(500).json({
            error: 'Failed to execute trade',
            message: error instanceof Error ? error.message : 'Unknown error'
        });
    }
});
router.get('/opportunities', async (req, res, next) => {
    try {
        const { minSpread = 0.5, tokenA, tokenB, exchanges = ['uniswap', 'sushiswap'] } = req.query;
        const latestPrices = await models_1.PriceData.find({
            token: { $in: [tokenA, tokenB] },
            exchange: { $in: exchanges },
            timestamp: { $gte: new Date(Date.now() - 5 * 60 * 1000) }
        }).sort({ timestamp: -1 });
        const opportunities = [];
        for (const exchange1 of exchanges) {
            for (const exchange2 of exchanges) {
                if (exchange1 === exchange2)
                    continue;
                const price1 = latestPrices.find(p => p.exchange === exchange1 && p.token === tokenA);
                const price2 = latestPrices.find(p => p.exchange === exchange2 && p.token === tokenB);
                if (price1 && price2) {
                    const spread = Math.abs((Number(price1.price) / Number(price2.price) - 1) * 100);
                    if (spread >= Number(minSpread)) {
                        opportunities.push({
                            tokenA,
                            tokenB,
                            exchange1,
                            exchange2,
                            price1: price1.price,
                            price2: price2.price,
                            spread,
                            timestamp: new Date(),
                            estimatedProfit: spread - config_1.config.security.maxSlippage
                        });
                    }
                }
            }
        }
        res.json({
            success: true,
            data: opportunities,
        });
    }
    catch (error) {
        next(error);
    }
});
router.get('/stats', async (req, res, next) => {
    try {
        const { timeframe = '24h' } = req.query;
        const timeframeMs = timeframe === '24h' ? 24 * 60 * 60 * 1000 : 7 * 24 * 60 * 60 * 1000;
        const trades = await models_1.Trade.find({
            timestamp: { $gte: new Date(Date.now() - timeframeMs) }
        });
        const stats = {
            totalTrades: trades.length,
            successfulTrades: trades.filter(t => t.status === 'completed').length,
            failedTrades: trades.filter(t => t.status === 'failed').length,
            totalProfit: trades.reduce((sum, t) => sum + Number(t.actualProfit), 0).toString(),
            averageProfit: trades.length > 0
                ? (trades.reduce((sum, t) => sum + Number(t.actualProfit), 0) / trades.length).toString()
                : '0',
            totalGasUsed: trades.reduce((sum, t) => sum + Number(t.gasUsed), 0).toString(),
            averageGasUsed: trades.length > 0
                ? (trades.reduce((sum, t) => sum + Number(t.gasUsed), 0) / trades.length).toString()
                : '0'
        };
        res.json({
            success: true,
            data: stats,
        });
    }
    catch (error) {
        next(error);
    }
});
router.get('/trade/:tradeId', async (req, res, next) => {
    try {
        const { tradeId } = req.params;
        const trade = await models_1.Trade.findById(tradeId);
        if (!trade) {
            throw new errorHandler_1.ValidationError('Trade not found');
        }
        res.json({
            success: true,
            data: trade
        });
    }
    catch (error) {
        next(error);
    }
});
router.get('/strategies', async (req, res, next) => {
    try {
        const strategies = await models_1.Strategy.find({ isActive: true });
        res.json({
            success: true,
            data: strategies
        });
    }
    catch (error) {
        next(error);
    }
});
exports.default = router;
//# sourceMappingURL=arbitrage.js.map