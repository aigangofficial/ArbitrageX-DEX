import { BigNumber } from '@ethersproject/bignumber';
import { EventEmitter } from 'events';
import { logger } from '../../utils/logger';

interface MonitoringMetrics {
    priceUpdateLatency: number;
    gasPrice: string;
    lastArbitrageTimestamp: number;
    totalOpportunities: number;
    totalExecutedTrades: number;
    averageProfit: string;
    systemHealth: {
        isHealthy: boolean;
        lastCheck: number;
        errors: string[];
    };
}

export class MonitoringService extends EventEmitter {
    private metrics: MonitoringMetrics;
    private updateInterval: NodeJS.Timeout | null = null;
    private readonly UPDATE_INTERVAL = 5000; // 5 seconds

    constructor() {
        super();
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

    start(): void {
        if (this.updateInterval) {
            return;
        }

        this.updateInterval = setInterval(() => this.checkSystemHealth(), this.UPDATE_INTERVAL);
        logger.info('Monitoring service started');
    }

    stop(): void {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
        logger.info('Monitoring service stopped');
    }

    updateMetrics(update: Partial<MonitoringMetrics>): void {
        this.metrics = { ...this.metrics, ...update };
        this.emit('metricsUpdate', this.metrics);
    }

    recordArbitrageOpportunity(profit: BigNumber, gasPrice: BigNumber): void {
        const currentProfit = BigNumber.from(this.metrics.averageProfit);
        const newTotalOpportunities = this.metrics.totalOpportunities + 1;
        const newAverageProfit = currentProfit.add(profit).div(newTotalOpportunities).toString();

        this.updateMetrics({
            totalOpportunities: newTotalOpportunities,
            lastArbitrageTimestamp: Date.now(),
            averageProfit: newAverageProfit,
            gasPrice: gasPrice.toString()
        });
    }

    recordExecutedTrade(success: boolean, error?: string): void {
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

    private checkSystemHealth(): void {
        const now = Date.now();
        const healthyThreshold = 5 * 60 * 1000; // 5 minutes

        const isHealthy =
            now - this.metrics.lastArbitrageTimestamp < healthyThreshold &&
            this.metrics.systemHealth.errors.length === 0;

        this.updateMetrics({
            systemHealth: {
                ...this.metrics.systemHealth,
                isHealthy,
                lastCheck: now
            }
        });
    }

    getMetrics(): MonitoringMetrics {
        return { ...this.metrics };
    }
}

export default MonitoringService;
