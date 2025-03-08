"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.createStatusRouter = void 0;
const express_1 = require("express");
const BotStatus_1 = require("../models/BotStatus");
const logger_1 = require("../utils/logger");
const router = (0, express_1.Router)();
const createStatusRouter = () => {
    // Get current bot status
    router.get('/', async (req, res) => {
        try {
            const status = await BotStatus_1.BotStatus.findOne().sort({ lastHeartbeat: -1 });
            if (!status) {
                return res.status(404).json({
                    success: false,
                    error: 'Bot status not found'
                });
            }
            // Check if bot is healthy
            const isHealthy = status.isHealthy();
            res.json({
                success: true,
                status: {
                    ...status.toJSON(),
                    isHealthy,
                    lastHeartbeatAgo: Date.now() - status.lastHeartbeat.getTime()
                }
            });
        }
        catch (error) {
            logger_1.logger.error('Error fetching bot status:', error);
            res.status(500).json({
                success: false,
                error: 'Failed to fetch bot status'
            });
        }
    });
    // Update bot status (internal use only)
    router.post('/update', async (req, res) => {
        try {
            const { memoryUsage, cpuUsage, pendingTransactions, network, version } = req.body;
            let status = await BotStatus_1.BotStatus.findOne().sort({ lastHeartbeat: -1 });
            if (!status) {
                status = new BotStatus_1.BotStatus({
                    isActive: true,
                    lastHeartbeat: new Date(),
                    totalTrades: 0,
                    successfulTrades: 0,
                    failedTrades: 0,
                    totalProfit: '0',
                    averageGasUsed: 0,
                    memoryUsage,
                    cpuUsage,
                    pendingTransactions,
                    network,
                    version,
                    uptime: process.uptime()
                });
            }
            else {
                status.updateHeartbeat();
                status.memoryUsage = memoryUsage;
                status.cpuUsage = cpuUsage;
                status.pendingTransactions = pendingTransactions;
                status.network = network;
                status.version = version;
                status.uptime = process.uptime();
            }
            await status.save();
            res.json({
                success: true,
                status
            });
        }
        catch (error) {
            logger_1.logger.error('Error updating bot status:', error);
            res.status(500).json({
                success: false,
                error: 'Failed to update bot status'
            });
        }
    });
    // Get health metrics
    router.get('/health', async (req, res) => {
        try {
            const status = await BotStatus_1.BotStatus.findOne().sort({ lastHeartbeat: -1 });
            if (!status) {
                return res.status(503).json({
                    status: 'error',
                    message: 'Bot status not available'
                });
            }
            const isHealthy = status.isHealthy();
            const memoryThreshold = 90; // 90% memory usage threshold
            const memoryUsagePercent = (status.memoryUsage.heapUsed / status.memoryUsage.heapTotal) * 100;
            res.json({
                status: isHealthy ? 'ok' : 'error',
                checks: {
                    uptime: {
                        status: 'ok',
                        value: status.uptime
                    },
                    memory: {
                        status: memoryUsagePercent < memoryThreshold ? 'ok' : 'warning',
                        value: memoryUsagePercent,
                        threshold: memoryThreshold
                    },
                    lastHeartbeat: {
                        status: isHealthy ? 'ok' : 'error',
                        value: status.lastHeartbeat,
                        threshold: '30s'
                    },
                    pendingTransactions: {
                        status: status.pendingTransactions < 10 ? 'ok' : 'warning',
                        value: status.pendingTransactions
                    }
                },
                timestamp: new Date().toISOString()
            });
        }
        catch (error) {
            logger_1.logger.error('Error fetching health metrics:', error);
            res.status(500).json({
                status: 'error',
                error: 'Failed to fetch health metrics'
            });
        }
    });
    return router;
};
exports.createStatusRouter = createStatusRouter;
//# sourceMappingURL=status.js.map