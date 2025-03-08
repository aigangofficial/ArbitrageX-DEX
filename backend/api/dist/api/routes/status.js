"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.createStatusRouter = createStatusRouter;
const express_1 = require("express");
const BotStatus_1 = require("../models/BotStatus");
const logger_1 = require("../utils/logger");
function createStatusRouter() {
    const router = (0, express_1.Router)();
    router.get('/', async (req, res) => {
        try {
            const status = await BotStatus_1.BotStatus.findOne().sort({ lastHeartbeat: -1 });
            if (!status) {
                return res.status(404).json({
                    error: 'No bot status found'
                });
            }
            return res.json({
                isActive: status.isActive,
                lastHeartbeat: status.lastHeartbeat,
                totalTrades: status.totalTrades,
                successfulTrades: status.successfulTrades,
                failedTrades: status.failedTrades,
                totalProfit: status.totalProfit,
                averageGasUsed: status.averageGasUsed,
                memoryUsage: status.memoryUsage,
                cpuUsage: status.cpuUsage,
                pendingTransactions: status.pendingTransactions,
                network: status.network,
                version: status.version,
                uptime: status.uptime,
                isHealthy: status.isHealthy()
            });
        }
        catch (error) {
            logger_1.logger.error('Error fetching bot status:', error);
            return res.status(500).json({ error: 'Internal server error' });
        }
    });
    router.get('/health', async (req, res) => {
        try {
            const status = await BotStatus_1.BotStatus.findOne().sort({ lastHeartbeat: -1 });
            if (!status) {
                return res.status(503).json({
                    status: 'unhealthy',
                    message: 'No bot status available'
                });
            }
            const isHealthy = status.isHealthy();
            return res.status(isHealthy ? 200 : 503).json({
                status: isHealthy ? 'healthy' : 'unhealthy',
                lastHeartbeat: status.lastHeartbeat,
                uptime: status.uptime,
                memoryUsage: status.memoryUsage,
                cpuUsage: status.cpuUsage
            });
        }
        catch (error) {
            logger_1.logger.error('Error checking bot health:', error);
            return res.status(500).json({ error: 'Internal server error' });
        }
    });
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
    return router;
}
//# sourceMappingURL=status.js.map