import { MarketDataService } from '../market_data';
import { Logger } from 'winston';
import mongoose from 'mongoose';
import { SimulationScenario } from '../../api/config';

describe('MarketDataService', () => {
    let service: MarketDataService;
    let mockLogger: jest.Mocked<Logger>;

    const mockMongoUri = process.env.MONGO_URI || 'mongodb://localhost:27017/test';

    beforeAll(async () => {
        mockLogger = {
            info: jest.fn(),
            error: jest.fn(),
            warn: jest.fn()
        } as unknown as jest.Mocked<Logger>;

        service = new MarketDataService(mockLogger, mockMongoUri);
        await mongoose.connect(mockMongoUri);
    });

    afterAll(async () => {
        await mongoose.connection.dropDatabase();
        await mongoose.connection.close();
    });

    beforeEach(async () => {
        await mongoose.connection.dropDatabase();
    });

    describe('getHistoricalScenarios', () => {
        it('should return empty array when no scenarios exist', async () => {
            const scenarios = await service.getHistoricalScenarios();
            expect(scenarios).toEqual([]);
        });

        it('should return scenarios in descending timestamp order', async () => {
            const mockScenarios: SimulationScenario[] = [
                {
                    liquidityShock: 0.3,
                    gasPriceSpike: 0.5,
                    competitorActivity: 0.8,
                    marketVolatility: 0.4
                },
                {
                    liquidityShock: 0.5,
                    gasPriceSpike: 0.7,
                    competitorActivity: 0.9,
                    marketVolatility: 0.6
                }
            ];

            await service['ScenarioModel'].create(mockScenarios);
            const scenarios = await service.getHistoricalScenarios();
            
            expect(scenarios).toHaveLength(2);
            expect(scenarios[0].liquidityShock).toBe(0.5);
            expect(scenarios[1].liquidityShock).toBe(0.3);
        });
    });

    describe('recordSimulationResult', () => {
        it('should successfully record a simulation result', async () => {
            const mockResult = {
                scenario: {
                    liquidityShock: 0.3,
                    gasPriceSpike: 0.5,
                    competitorActivity: 0.8,
                    marketVolatility: 0.4
                },
                trades: [{
                    success: true,
                    error: undefined,
                    profit: '1000',
                    gasUsed: '50000'
                }],
                metrics: {
                    successRate: 1,
                    averageProfit: '1000',
                    totalGasUsed: '50000'
                },
                timestamp: Date.now(),
                duration: 1000
            };

            await service.recordSimulationResult(mockResult);
            
            const savedResults = await service['ResultModel'].find().lean();
            expect(savedResults).toHaveLength(1);
            expect(savedResults[0]?.metrics?.successRate).toBe(1);
        });
    });

    describe('getPerformanceMetrics', () => {
        it('should return default metrics when no results exist', async () => {
            const metrics = await service.getPerformanceMetrics();
            
            expect(metrics).toEqual({
                successRate: 0,
                avgProfit: '0',
                commonFailures: []
            });
        });

        it('should calculate correct metrics from results', async () => {
            const mockResults = [
                {
                    scenario: {
                        liquidityShock: 0.3,
                        gasPriceSpike: 0.5,
                        competitorActivity: 0.8,
                        marketVolatility: 0.4
                    },
                    trades: [{
                        success: true,
                        profit: '1000',
                        gasUsed: '50000'
                    }],
                    metrics: {
                        successRate: 1,
                        averageProfit: '1000',
                        totalGasUsed: '50000'
                    },
                    timestamp: Date.now(),
                    duration: 1000
                },
                {
                    scenario: {
                        liquidityShock: 0.5,
                        gasPriceSpike: 0.7,
                        competitorActivity: 0.9,
                        marketVolatility: 0.6
                    },
                    trades: [{
                        success: false,
                        error: 'Insufficient liquidity',
                        profit: '0',
                        gasUsed: '40000'
                    }],
                    metrics: {
                        successRate: 0,
                        averageProfit: '0',
                        totalGasUsed: '40000'
                    },
                    timestamp: Date.now(),
                    duration: 1000
                }
            ];

            await service['ResultModel'].create(mockResults);
            const metrics = await service.getPerformanceMetrics();
            
            expect(metrics.successRate).toBe(0.5);
            expect(metrics.avgProfit).toBe('500');
            expect(metrics.commonFailures).toContain('Insufficient liquidity');
        });
    });
}); 