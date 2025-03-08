"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MonitoringService = void 0;
const bignumber_1 = require("@ethersproject/bignumber");
const events_1 = require("events");
const logger_1 = require("../../utils/logger");
class MonitoringService extends events_1.EventEmitter {
    constructor() {
        super();
        this.updateInterval = null;
        this.UPDATE_INTERVAL = 5000; // 5 seconds
        this.metrics = {
            priceUpdateLatency: 0,
            gasPrice: '0',
            lastArbitrageTimestamp: 0,
            totalOpportunities: 0,
            totalExecutedTrades: 0,
            averageProfit: '0',
            systemHealth: {
                isHealthy: true,
                lastCheck: Date.now(),
                errors: []
            }
        };
    }
    start() {
        if (this.updateInterval) {
            return;
        }
        this.updateInterval = setInterval(() => this.checkSystemHealth(), this.UPDATE_INTERVAL);
        logger_1.logger.info('Monitoring service started');
    }
    stop() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
        logger_1.logger.info('Monitoring service stopped');
    }
    updateMetrics(update) {
        this.metrics = { ...this.metrics, ...update };
        this.emit('metricsUpdate', this.metrics);
    }
    recordArbitrageOpportunity(profit, gasPrice) {
        const currentProfit = bignumber_1.BigNumber.from(this.metrics.averageProfit);
        const newTotalOpportunities = this.metrics.totalOpportunities + 1;
        const newAverageProfit = currentProfit.add(profit).div(newTotalOpportunities).toString();
        this.updateMetrics({
            totalOpportunities: newTotalOpportunities,
            lastArbitrageTimestamp: Date.now(),
            averageProfit: newAverageProfit,
            gasPrice: gasPrice.toString()
        });
    }
    recordExecutedTrade(success, error) {
        if (!success && error) {
            this.metrics.systemHealth.errors.push(error);
            if (this.metrics.systemHealth.errors.length > 10) {
                this.metrics.systemHealth.errors.shift(); // Keep last 10 errors
            }
        }
        this.updateMetrics({
            totalExecutedTrades: this.metrics.totalExecutedTrades + 1,
            systemHealth: {
                ...this.metrics.systemHealth,
                lastCheck: Date.now()
            }
        });
    }
    checkSystemHealth() {
        const now = Date.now();
        const healthyThreshold = 5 * 60 * 1000; // 5 minutes
        const isHealthy = now - this.metrics.lastArbitrageTimestamp < healthyThreshold &&
            this.metrics.systemHealth.errors.length === 0;
        this.updateMetrics({
            systemHealth: {
                ...this.metrics.systemHealth,
                isHealthy,
                lastCheck: now
            }
        });
    }
    getMetrics() {
        return { ...this.metrics };
    }
}
exports.MonitoringService = MonitoringService;
exports.default = MonitoringService;
//# sourceMappingURL=monitoringService.js.map