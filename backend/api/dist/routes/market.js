"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = require("express");
const config_1 = require("../config");
const errorHandler_1 = require("../middleware/errorHandler");
const rateLimit_1 = require("../middleware/rateLimit");
const models_1 = require("../models");
const router = (0, express_1.Router)();
// Get recent market data for a token
router.get('/data', rateLimit_1.marketDataLimiter, async (req, res, next) => {
    try {
        const { token, exchange, limit = 100, startTime, endTime } = req.query;
        if (!token) {
            throw new errorHandler_1.ValidationError('Token address is required');
        }
        const query = { token };
        if (exchange)
            query.exchange = exchange;
        if (startTime)
            query.timestamp = { $gte: new Date(Number(startTime)) };
        if (endTime)
            query.timestamp = { ...query.timestamp, $lte: new Date(Number(endTime)) };
        const data = await models_1.PriceData.find(query)
            .sort({ timestamp: -1 })
            .limit(Number(limit));
        // Calculate additional metrics
        const enrichedData = data.map(item => ({
            ...item.toObject(),
            liquidityUSD: Number(item.liquidity) * Number(item.price),
            timestamp: item.timestamp.getTime()
        }));
        res.json({
            success: true,
            data: enrichedData,
        });
    }
    catch (error) {
        next(error);
    }
});
// Get market volatility for a token
router.get('/volatility', rateLimit_1.volatilityLimiter, async (req, res, next) => {
    try {
        const { token, exchange, hours = 24 } = req.query;
        if (!token) {
            throw new errorHandler_1.ValidationError('Token address is required');
        }
        const timeframeMs = Number(hours) * 60 * 60 * 1000;
        const startTime = new Date(Date.now() - timeframeMs);
        const priceData = await models_1.PriceData.find({
            token,
            ...(exchange && { exchange }),
            timestamp: { $gte: startTime }
        }).sort({ timestamp: 1 });
        if (priceData.length < 2) {
            throw new errorHandler_1.ValidationError('Insufficient data for volatility calculation');
        }
        // Calculate volatility metrics
        const prices = priceData.map(d => Number(d.price));
        const returns = prices.slice(1).map((price, i) => Math.log(price / prices[i]));
        const volatility = {
            standardDeviation: Math.sqrt(returns.reduce((sum, r) => sum + r * r, 0) / returns.length) * Math.sqrt(24 * 60 * 60 / (timeframeMs / priceData.length)),
            priceChange: ((prices[prices.length - 1] - prices[0]) / prices[0]) * 100,
            highestPrice: Math.max(...prices),
            lowestPrice: Math.min(...prices),
            averagePrice: prices.reduce((a, b) => a + b) / prices.length,
            priceRange: Math.max(...prices) - Math.min(...prices)
        };
        res.json({
            success: true,
            data: {
                token,
                exchange,
                timeframe: `${hours}h`,
                volatility,
                sampleSize: priceData.length,
                startTime: priceData[0].timestamp,
                endTime: priceData[priceData.length - 1].timestamp
            },
        });
    }
    catch (error) {
        next(error);
    }
});
// Get market opportunities across exchanges
router.get('/opportunities', rateLimit_1.opportunitiesLimiter, async (req, res, next) => {
    try {
        const { minSpread = 0.5, minLiquidity, exchanges = ['uniswap', 'sushiswap'], maxResults = 10 } = req.query;
        // Get latest price data
        const latestPrices = await models_1.PriceData.find({
            exchange: { $in: exchanges },
            timestamp: { $gte: new Date(Date.now() - 5 * 60 * 1000) } // Last 5 minutes
        }).sort({ timestamp: -1 });
        // Group prices by token
        const pricesByToken = latestPrices.reduce((acc, price) => {
            if (!acc[price.token])
                acc[price.token] = [];
            acc[price.token].push(price);
            return acc;
        }, {});
        // Find opportunities
        const opportunities = [];
        for (const [token, prices] of Object.entries(pricesByToken)) {
            if (prices.length < 2)
                continue;
            for (let i = 0; i < prices.length; i++) {
                for (let j = i + 1; j < prices.length; j++) {
                    const price1 = prices[i];
                    const price2 = prices[j];
                    const spread = Math.abs((Number(price1.price) / Number(price2.price) - 1) * 100);
                    if (spread >= Number(minSpread)) {
                        const minLiq = Math.min(Number(price1.liquidity) * Number(price1.price), Number(price2.liquidity) * Number(price2.price));
                        if (!minLiquidity || minLiq >= Number(minLiquidity)) {
                            opportunities.push({
                                token,
                                exchange1: price1.exchange,
                                exchange2: price2.exchange,
                                price1: price1.price,
                                price2: price2.price,
                                spread,
                                liquidity: minLiq,
                                timestamp: new Date(),
                                estimatedProfit: spread - config_1.config.security.maxSlippage,
                                volume24h: Math.min(Number(price1.volume24h), Number(price2.volume24h)).toString()
                            });
                        }
                    }
                }
            }
        }
        // Sort by spread and limit results
        opportunities.sort((a, b) => b.spread - a.spread);
        const limitedOpportunities = opportunities.slice(0, Number(maxResults));
        res.json({
            success: true,
            data: limitedOpportunities,
        });
    }
    catch (error) {
        next(error);
    }
});
// Get market summary
router.get('/summary', rateLimit_1.marketDataLimiter, async (req, res, next) => {
    try {
        const { exchanges = ['uniswap', 'sushiswap'] } = req.query;
        // Get latest price data
        const latestPrices = await models_1.PriceData.find({
            exchange: { $in: exchanges },
            timestamp: { $gte: new Date(Date.now() - 24 * 60 * 60 * 1000) }
        }).sort({ timestamp: -1 });
        // Calculate market summary
        const summary = {
            totalTokens: new Set(latestPrices.map(p => p.token)).size,
            totalVolume24h: latestPrices.reduce((sum, p) => sum + Number(p.volume24h), 0),
            averagePriceChange24h: latestPrices.reduce((sum, p) => sum + Number(p.priceChange24h), 0) / latestPrices.length,
            exchangeMetrics: {}
        };
        // Calculate per-exchange metrics
        for (const exchange of exchanges) {
            const exchangePrices = latestPrices.filter(p => p.exchange === exchange);
            summary.exchangeMetrics[exchange] = {
                tokenCount: new Set(exchangePrices.map(p => p.token)).size,
                volume24h: exchangePrices.reduce((sum, p) => sum + Number(p.volume24h), 0),
                averagePriceChange24h: exchangePrices.reduce((sum, p) => sum + Number(p.priceChange24h), 0) / exchangePrices.length,
                totalLiquidityUSD: exchangePrices.reduce((sum, p) => sum + Number(p.liquidity) * Number(p.price), 0)
            };
        }
        res.json({
            success: true,
            data: summary,
        });
    }
    catch (error) {
        next(error);
    }
});
exports.default = router;
//# sourceMappingURL=market.js.map