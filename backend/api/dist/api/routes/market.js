"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.createMarketRouter = createMarketRouter;
const express_1 = require("express");
const logger_1 = require("../utils/logger");
function createMarketRouter() {
    const router = (0, express_1.Router)();
    router.get('/data', async (req, res) => {
        try {
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
        }
        catch (error) {
            logger_1.logger.error('Error fetching market data:', error);
            res.status(500).json({
                success: false,
                error: 'Failed to fetch market data'
            });
        }
    });
    return router;
}
//# sourceMappingURL=market.js.map