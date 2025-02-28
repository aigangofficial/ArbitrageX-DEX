import { SimulationScenario, SimulationResult } from '../api/config';
import { Logger } from 'winston';
import mongoose from 'mongoose';
import { config } from '../api/config';

interface ISimulationResult {
    scenario: SimulationScenario;
    trades: Array<{
        success: boolean;
        error?: string;
        profit?: string;
        gasUsed?: string;
    }>;
    metrics: {
        successRate: number;
        averageProfit: string;
        totalGasUsed: string;
        executionTime: number;
    };
    timestamp: number;
}

const simulationResultSchema = new mongoose.Schema<ISimulationResult>({
    scenario: {
        liquidityShock: Number,
        gasPriceSpike: Number,
        competitorActivity: Number,
        marketVolatility: Number
    },
    trades: [{
        success: Boolean,
        error: String,
        profit: String,
        gasUsed: String
    }],
    metrics: {
        successRate: Number,
        averageProfit: String,
        totalGasUsed: String,
        executionTime: Number
    },
    timestamp: {
        type: Number,
        default: Date.now
    }
});

const SimulationResultModel = mongoose.model<ISimulationResult>('SimulationResult', simulationResultSchema);

export class MarketDataService {
    constructor(
        private readonly logger: Logger
    ) {}

    async getHistoricalScenarios(limit = 1000): Promise<SimulationScenario[]> {
        try {
            const results = await SimulationResultModel
                .find()
                .sort({ timestamp: -1 })
                .limit(limit)
                .lean();

            return results.map(result => result.scenario);
        } catch (error) {
            this.logger.error('Failed to fetch historical scenarios:', error);
            return [];
        }
    }

    async recordSimulationResult(result: SimulationResult): Promise<void> {
        try {
            await SimulationResultModel.create({
                scenario: result.scenario,
                trades: result.trades.map((trade: { success: boolean; error?: string; profit?: bigint; gasUsed?: bigint }) => ({
                    success: trade.success,
                    error: trade.error,
                    profit: trade.profit?.toString(),
                    gasUsed: trade.gasUsed?.toString()
                })),
                metrics: {
                    successRate: result.metrics.successRate,
                    averageProfit: result.metrics.averageProfit.toString(),
                    totalGasUsed: result.metrics.totalGasUsed.toString(),
                    executionTime: result.metrics.executionTime
                },
                timestamp: Date.now()
            });
        } catch (error) {
            this.logger.error('Failed to save simulation result:', error);
            throw error;
        }
    }

    async getPerformanceMetrics(days = 30): Promise<{
        successRate: number;
        avgProfit: string;
        commonFailures: string[];
    }> {
        try {
            const cutoffTime = Date.now() - days * 86400000;
            const results = await SimulationResultModel
                .find({ timestamp: { $gte: cutoffTime } })
                .lean();

            if (!results.length) {
                return {
                    successRate: 0,
                    avgProfit: '0',
                    commonFailures: []
                };
            }

            const successRate = results.reduce((sum, r) => 
                sum + r.metrics.successRate, 0) / results.length;

            const avgProfit = (results.reduce((sum, r) => 
                sum + BigInt(r.metrics.averageProfit), BigInt(0)) / BigInt(results.length)).toString();

            const failures = results.flatMap(r => 
                r.trades.filter(t => !t.success && t.error).map(t => t.error!)
            );
            const failureCounts = new Map<string, number>();
            failures.forEach(f => failureCounts.set(f, (failureCounts.get(f) || 0) + 1));
            
            const commonFailures = [...failureCounts.entries()]
                .sort((a, b) => b[1] - a[1])
                .slice(0, 5)
                .map(([error]) => error);

            return {
                successRate,
                avgProfit,
                commonFailures
            };
        } catch (error) {
            this.logger.error('Failed to calculate performance metrics:', error);
            return {
                successRate: 0,
                avgProfit: '0',
                commonFailures: []
            };
        }
    }
} 