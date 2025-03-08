"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
var __metadata = (this && this.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.AdversarialSimulator = void 0;
const common_1 = require("@nestjs/common");
const winston_1 = require("winston");
const arbitrageScanner_1 = require("../execution/arbitrageScanner");
const liquidity_monitor_1 = require("../services/liquidity_monitor");
const cross_chain_router_1 = require("../services/cross_chain_router");
const market_data_1 = require("../services/market_data");
const gan_trainer_1 = require("./gan_trainer");
const quantum_validator_1 = require("./quantum_validator");
const tf = __importStar(require("@tensorflow/tfjs-node"));
const config_1 = require("../api/config");
const alert_service_1 = require("../services/alert.service");
let AdversarialSimulator = class AdversarialSimulator {
    constructor(scanner, liquidityMonitor, crossChainRouter, logger, config, alertService) {
        this.scanner = scanner;
        this.liquidityMonitor = liquidityMonitor;
        this.crossChainRouter = crossChainRouter;
        this.logger = logger;
        this.config = config;
        this.alertService = alertService;
        this.config = (0, config_1.getConfig)();
        this.simulationStartTime = 0;
        this.crossChainOpportunities = new Map();
        this.chainLatencies = new Map();
        this.chainLatencyHistory = new Map();
        this.optimalLatencyThresholds = new Map();
        this.competitorTransactions = new Map();
        this.quantumValidator = new quantum_validator_1.QuantumValidator(logger, {
            minLatticeSecurityLevel: this.config.ai.quantum.minLatticeSecurityLevel,
            postQuantumScheme: this.config.ai.quantum.postQuantumScheme,
            challengeWindowMs: this.config.ai.quantum.challengeWindowMs
        }, alertService);
        this.ganTrainer = new gan_trainer_1.GANTrainer(logger, {
            batchSize: 32,
            epochs: 100,
            learningRate: 0.0002
        });
        this.marketDataService = new market_data_1.MarketDataService(logger);
        Object.keys(this.config.chains).forEach(chainId => {
            this.chainLatencies.set(Number(chainId), 0);
        });
    }
    async dailyTrainingCycle() {
        try {
            const historicalData = await this.marketDataService.getHistoricalScenarios();
            const performance = await this.marketDataService.getPerformanceMetrics();
            this.logger.info('Starting daily training cycle', { performance });
            const validatedData = await this.validateHistoricalData(historicalData);
            await this.runTrainingCycle(validatedData);
            const newScenarios = await this.generateQuantumSafeScenarios(50);
            for (const scenario of newScenarios) {
                const result = await this.runSimulation(scenario);
                await this.marketDataService.recordSimulationResult(result);
            }
            this.logger.info('Completed daily training cycle');
        }
        catch (error) {
            this.logger.error('Daily training cycle failed:', error);
            throw error;
        }
    }
    async validateHistoricalData(scenarios) {
        const validatedScenarios = [];
        for (const scenario of scenarios) {
            const modelState = await this.ganTrainer.getModelState();
            const validation = await this.quantumValidator.validateModelState(modelState);
            if (validation.isValid && validation.quantumSafetyScore >= 0.8) {
                validatedScenarios.push(scenario);
            }
            else {
                this.logger.warn('Scenario failed quantum validation', {
                    threatLevel: validation.threatLevel,
                    recommendations: validation.recommendations
                });
            }
        }
        return validatedScenarios;
    }
    async generateQuantumSafeScenarios(count) {
        const scenarios = [];
        let attempts = 0;
        const maxAttempts = count * 2;
        while (scenarios.length < count && attempts < maxAttempts) {
            const newScenarios = this.ganTrainer.generateScenarios(5);
            for (const scenario of newScenarios) {
                const modelState = await this.ganTrainer.getModelState();
                const validation = await this.quantumValidator.validateModelState(modelState);
                if (validation.isValid && validation.quantumSafetyScore >= 0.8) {
                    scenarios.push(scenario);
                    if (scenarios.length >= count)
                        break;
                }
            }
            attempts++;
        }
        if (scenarios.length < count) {
            this.logger.warn(`Generated only ${scenarios.length}/${count} quantum-safe scenarios`);
        }
        return scenarios;
    }
    async runSimulation(scenario) {
        this.simulationStartTime = Date.now();
        const trades = [];
        try {
            const modelState = await this.ganTrainer.getModelState();
            const validation = await this.quantumValidator.validateModelState(modelState);
            if (!validation.isValid) {
                throw new Error('Scenario failed quantum validation');
            }
            await this.simulateCrossChainConditions(scenario);
            const opportunities = await this.detectCrossChainOpportunities();
            for (const opportunity of opportunities) {
                const trade = await this.executeQuantumSafeCrossChainTrade(opportunity, scenario);
                trades.push(trade);
            }
            const metrics = this.calculateCrossChainMetrics(trades);
            return {
                scenario,
                trades,
                metrics,
                timestamp: Date.now(),
                quantumMetrics: {
                    safetyScore: validation.quantumSafetyScore,
                    threatLevel: validation.threatLevel,
                    recommendations: validation.recommendations
                }
            };
        }
        catch (error) {
            this.logger.error('Cross-chain simulation failed:', error);
            throw error;
        }
        finally {
            this.resetSimulation();
        }
    }
    async simulateCrossChainConditions(scenario) {
        const chains = Object.keys(this.config.chains).map(Number);
        await Promise.all(chains.map(async (chainId) => {
            this.chainLatencies.set(chainId, Math.floor(50 + scenario.marketVolatility * 200));
            await Promise.all([
                this.simulateLiquidityChanges(chainId, scenario.liquidityShock),
                this.simulateGasPriceSpikes(chainId, scenario.gasPriceSpike),
                this.simulateCompetitorActivity(chainId, scenario.competitorActivity),
                this.simulateMarketVolatility(chainId, scenario.marketVolatility)
            ]);
        }));
    }
    async detectCrossChainOpportunities() {
        const opportunities = [];
        const chains = Object.keys(this.config.chains).map(Number);
        for (const sourceChain of chains) {
            const pools = (await this.liquidityMonitor.getTrackedPools())
                .filter(pool => pool.chainId === sourceChain && this.isPoolViable(pool));
            for (const pool of pools) {
                const modelState = await this.ganTrainer.getModelState();
                const validation = await this.quantumValidator.validateModelState(modelState);
                if (validation.quantumSafetyScore < this.config.ai.quantum.minLatticeSecurityLevel) {
                    this.logger.warn(`Insufficient quantum safety score for pool ${pool.address}`);
                    continue;
                }
                const routes = await this.crossChainRouter.findArbitrageRoutes(pool.tokenA, pool.reserve0, 2);
                for (const route of routes) {
                    const estimatedLatency = await this.estimateCrossChainLatency(route);
                    const sourceThreshold = this.optimalLatencyThresholds.get(route.sourceChain);
                    const targetThreshold = this.optimalLatencyThresholds.get(route.targetChain);
                    if (sourceThreshold && targetThreshold &&
                        estimatedLatency > (sourceThreshold + targetThreshold)) {
                        this.logger.warn(`Latency threshold exceeded for route`, {
                            sourceChain: route.sourceChain,
                            targetChain: route.targetChain,
                            estimatedLatency,
                            threshold: sourceThreshold + targetThreshold
                        });
                        continue;
                    }
                    opportunities.push({
                        ...route,
                        bridge: {
                            chainId: pool.chainId,
                            bridgeAddress: this.config.contracts.bridge,
                            tokenMappings: new Map(),
                            estimatedTime: estimatedLatency,
                            fee: this.calculateBridgeFee(route)
                        }
                    });
                }
            }
        }
        return opportunities;
    }
    calculateBridgeFee(route) {
        const baseFee = route.estimatedProfit * 10n / 10000n;
        const gasCost = route.gasEstimate * this.getGasPrice(route.sourceChain);
        return baseFee + gasCost;
    }
    getGasPrice(chainId) {
        return 50000000000n;
    }
    isPoolViable(pool) {
        const competitorCount = this.competitorTransactions.get(pool.address) || 0;
        const hasAdequateLiquidity = pool.reserve0 > 0n && pool.reserve1 > 0n;
        const priceIsFresh = pool.lastPrice > 0n;
        const recentUpdate = Date.now() - pool.lastUpdate < 300000;
        return hasAdequateLiquidity &&
            priceIsFresh &&
            recentUpdate &&
            competitorCount < 5 &&
            pool.fee < 0.01;
    }
    async executeQuantumSafeCrossChainTrade(route, scenario) {
        try {
            const modelState = await this.ganTrainer.getModelState();
            const validation = await this.quantumValidator.validateModelState(modelState);
            if (validation.quantumSafetyScore < 0.9) {
                throw new Error(`Insufficient quantum safety score: ${validation.quantumSafetyScore}`);
            }
            const sourceThreshold = this.optimalLatencyThresholds.get(route.sourceChain);
            const targetThreshold = this.optimalLatencyThresholds.get(route.targetChain);
            if (sourceThreshold && targetThreshold) {
                const estimatedLatency = await this.estimateCrossChainLatency(route);
                if (estimatedLatency > (sourceThreshold + targetThreshold)) {
                    throw new Error('Estimated latency exceeds optimal thresholds');
                }
            }
            await this.simulateNetworkLatency(route.sourceChain, route.targetChain);
            const success = await this.crossChainRouter.executeRoute(route);
            if (!success) {
                throw new Error('Cross-chain trade execution failed');
            }
            const ganImpact = this.ganTrainer.predictAdversarialImpact({
                success: true,
                profit: route.estimatedProfit,
                gasUsed: route.gasEstimate
            });
            const gradients = await this.ganTrainer.getGradients();
            const gradientNorm = await this.calculateGradientNorm(gradients);
            return {
                success: true,
                profit: route.estimatedProfit,
                gasUsed: route.gasEstimate,
                adversarialMetrics: {
                    quantumSafetyScore: validation.quantumSafetyScore,
                    threatLevel: validation.threatLevel,
                    recommendations: validation.recommendations,
                    gradientNorm,
                    latencyOptimization: {
                        sourceThreshold,
                        targetThreshold,
                        currentLatency: await this.estimateCrossChainLatency(route)
                    }
                }
            };
        }
        catch (error) {
            this.logger.error('Quantum-safe cross-chain trade execution failed:', error);
            return {
                success: false,
                error: error instanceof Error ? error.message : 'Unknown error',
                adversarialMetrics: {
                    quantumSafetyScore: 0,
                    threatLevel: 'HIGH',
                    recommendations: ['Trade failed - retry with higher safety margin'],
                    gradientNorm: 0,
                    latencyOptimization: null
                }
            };
        }
    }
    async simulateNetworkLatency(sourceChain, targetChain) {
        const sourceLatency = this.chainLatencies.get(sourceChain) || 0;
        const targetLatency = this.chainLatencies.get(targetChain) || 0;
        const totalLatency = sourceLatency + targetLatency;
        if (!this.chainLatencyHistory.has(sourceChain)) {
            this.chainLatencyHistory.set(sourceChain, []);
        }
        if (!this.chainLatencyHistory.has(targetChain)) {
            this.chainLatencyHistory.set(targetChain, []);
        }
        this.chainLatencyHistory.get(sourceChain).push(sourceLatency);
        this.chainLatencyHistory.get(targetChain).push(targetLatency);
        const sourceThreshold = this.optimalLatencyThresholds.get(sourceChain);
        const targetThreshold = this.optimalLatencyThresholds.get(targetChain);
        if (sourceThreshold && sourceLatency > sourceThreshold) {
            this.logger.warn(`Source chain ${sourceChain} latency exceeds optimal threshold`, {
                actual: sourceLatency,
                threshold: sourceThreshold
            });
        }
        if (targetThreshold && targetLatency > targetThreshold) {
            this.logger.warn(`Target chain ${targetChain} latency exceeds optimal threshold`, {
                actual: targetLatency,
                threshold: targetThreshold
            });
        }
        await new Promise(resolve => setTimeout(resolve, totalLatency));
        if (this.chainLatencyHistory.get(sourceChain).length >= 10 ||
            this.chainLatencyHistory.get(targetChain).length >= 10) {
            await this.optimizeChainLatencies();
        }
    }
    calculateCrossChainMetrics(trades) {
        const successfulTrades = trades.filter(t => t.success);
        const failedTrades = trades.filter(t => !t.success);
        const successRate = trades.length > 0 ? successfulTrades.length / trades.length : 0;
        const averageProfit = successfulTrades.length > 0
            ? successfulTrades.reduce((sum, t) => sum + (t.profit || 0n), 0n) / BigInt(successfulTrades.length)
            : 0n;
        const totalGasUsed = trades.reduce((sum, t) => sum + (t.gasUsed || 0n), 0n);
        const competitorInteractions = trades.filter(t => {
            if (!t.profit)
                return false;
            const ganImpact = this.ganTrainer.predictAdversarialImpact({
                success: t.success,
                profit: t.profit,
                gasUsed: t.gasUsed
            });
            return t.error?.includes('competitor') || t.profit < (t.profit * BigInt(100 - ganImpact) / 100n);
        }).length;
        return {
            successRate,
            averageProfit,
            totalGasUsed,
            executionTime: Date.now() - this.simulationStartTime,
            competitorInteractions,
            failedTransactions: failedTrades.length
        };
    }
    async calculateGradientNorm(gradients) {
        return tf.tidy(() => {
            const flattenedGradients = gradients.map(g => g.reshape([-1]));
            const concatenated = tf.concat(flattenedGradients);
            return tf.norm(concatenated).dataSync()[0];
        });
    }
    resetSimulation() {
        this.simulationStartTime = 0;
        this.crossChainOpportunities.clear();
        this.chainLatencies.clear();
        this.chainLatencyHistory.clear();
        this.optimalLatencyThresholds.clear();
        Object.keys(this.config.chains).forEach(chainId => {
            this.chainLatencies.set(Number(chainId), 0);
        });
    }
    async runTrainingCycle(historicalScenarios) {
        try {
            await this.ganTrainer.trainGAN(historicalScenarios, this.config.ai.gan.epochs, this.config.ai.gan.batchSize);
            const newScenarios = await this.generateQuantumSafeScenarios(5);
            for (const scenario of newScenarios) {
                const result = await this.runSimulation(scenario);
                await this.marketDataService.recordSimulationResult(result);
            }
            await this.ganTrainer.saveModel(this.config.ai.modelPath);
            await this.optimizeChainLatencies();
        }
        catch (error) {
            this.logger.error('Training cycle failed:', error);
            throw error;
        }
    }
    async optimizeChainLatencies() {
        for (const [chainId, latencies] of this.chainLatencyHistory.entries()) {
            if (latencies.length >= 10) {
                const windowSize = Math.min(100, latencies.length);
                const recentLatencies = latencies.slice(-windowSize);
                const sortedLatencies = [...recentLatencies].sort((a, b) => a - b);
                const medianLatency = sortedLatencies[Math.floor(recentLatencies.length / 2)];
                const variance = this.calculateVariance(recentLatencies);
                const stdDev = Math.sqrt(variance);
                const p95Index = Math.floor(recentLatencies.length * 0.95);
                const p95Latency = sortedLatencies[p95Index];
                const networkLoad = this.calculateNetworkLoad(chainId);
                const quantumNoiseThreshold = stdDev * this.config.ai.quantum.minLatticeSecurityLevel *
                    (1 + networkLoad);
                const validationResult = await this.validateLatencyWithQuantumProof(chainId, medianLatency, p95Latency);
                if (!validationResult.isValid) {
                    this.logger.warn(`Quantum validation failed for chain ${chainId}`, {
                        metrics: validationResult.quantumMetrics
                    });
                    continue;
                }
                const alpha = Math.max(0.1, Math.min(0.3, 1 / (1 + networkLoad)));
                const currentThreshold = this.optimalLatencyThresholds.get(chainId) || medianLatency;
                const quantumSafetyFactor = validationResult.quantumMetrics.latticeScore;
                const newThreshold = Math.min(p95Latency, alpha * (medianLatency + quantumNoiseThreshold * quantumSafetyFactor) +
                    (1 - alpha) * currentThreshold);
                this.optimalLatencyThresholds.set(chainId, newThreshold);
                this.updateLatencyMetrics(chainId, {
                    median: medianLatency,
                    stdDev,
                    p95: p95Latency,
                    threshold: newThreshold,
                    quantumMetrics: validationResult.quantumMetrics
                });
                const safetyAdjustedWindow = Math.min(1000, Math.max(100, Math.floor(1 / (networkLoad * (2 - quantumSafetyFactor)) * 200)));
                this.chainLatencyHistory.set(chainId, latencies.slice(-safetyAdjustedWindow));
                this.logger.info('Chain latency optimization completed', {
                    chainId,
                    newThreshold,
                    quantumSafetyScore: validationResult.quantumMetrics.latticeScore,
                    temporalConsistency: validationResult.quantumMetrics.temporalConsistency,
                    networkLoadProof: validationResult.quantumMetrics.networkLoadProof
                });
            }
        }
    }
    calculateNetworkLoad(chainId) {
        const recentLatencies = this.chainLatencyHistory.get(chainId) || [];
        if (recentLatencies.length < 2)
            return 0.5;
        const latencyChanges = recentLatencies.slice(1).map((lat, i) => Math.abs(lat - recentLatencies[i]) / recentLatencies[i]);
        const avgChange = latencyChanges.reduce((sum, val) => sum + val, 0) / latencyChanges.length;
        return 1 / (1 + Math.exp(-10 * (avgChange - 0.5)));
    }
    updateLatencyMetrics(chainId, metrics) {
        const timestamp = Date.now();
        this.logger.info('Updated chain latency metrics', {
            chainId,
            timestamp,
            metrics,
            optimizationRound: this.chainLatencyHistory.get(chainId)?.length || 0,
            quantumSafetyMetrics: {
                latticeScore: metrics.quantumMetrics.latticeScore,
                temporalConsistency: metrics.quantumMetrics.temporalConsistency,
                networkLoadProof: metrics.quantumMetrics.networkLoadProof
            }
        });
    }
    async simulateLiquidityChanges(chainId, shock) {
        const pools = await this.liquidityMonitor.getTrackedPools();
        for (const pool of pools) {
            const variationFactor = 1 + (Math.random() * shock * 2 - shock);
            pool.reserve0 = BigInt(Math.floor(Number(pool.reserve0) * variationFactor));
            pool.reserve1 = BigInt(Math.floor(Number(pool.reserve1) * variationFactor));
        }
        this.logger.info(`Simulated liquidity changes on chain ${chainId} with shock ${shock}`);
    }
    async simulateGasPriceSpikes(chainId, spike) {
        const provider = this.crossChainRouter.getProvider(chainId);
        const baseGasPrice = await provider.getFeeData()
            .then(data => data.gasPrice || 0n);
        const newGasPrice = baseGasPrice * BigInt(Math.floor(1 + spike * 2));
        this.logger.info(`Simulated gas price spike on chain ${chainId} to ${newGasPrice}`);
    }
    async simulateCompetitorActivity(chainId, intensity) {
        const pools = await this.liquidityMonitor.getTrackedPools();
        const competitorCount = Math.floor(pools.length * intensity);
        for (let i = 0; i < competitorCount; i++) {
            const pool = pools[Math.floor(Math.random() * pools.length)];
            this.competitorTransactions.set(`${chainId}-${pool.address}`, Date.now());
        }
        this.logger.info(`Simulated ${competitorCount} competitor transactions on chain ${chainId}`);
    }
    async simulateMarketVolatility(chainId, volatility) {
        const pools = await this.liquidityMonitor.getTrackedPools();
        for (const pool of pools) {
            const priceVariation = 1 + (Math.random() * volatility * 2 - volatility);
            pool.lastPrice = pool.lastPrice * BigInt(Math.floor(priceVariation * 1000)) / 1000n;
        }
        this.logger.info(`Simulated market volatility on chain ${chainId} with intensity ${volatility}`);
    }
    calculateVariance(values) {
        const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
        return values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
    }
    async estimateCrossChainLatency(route) {
        const sourceLatencyHistory = this.chainLatencyHistory.get(route.sourceChain) || [];
        const targetLatencyHistory = this.chainLatencyHistory.get(route.targetChain) || [];
        const predictedSourceLatency = await this.predictLatencyTrend(route.sourceChain, sourceLatencyHistory);
        const predictedTargetLatency = await this.predictLatencyTrend(route.targetChain, targetLatencyHistory);
        const sourceThreshold = this.optimalLatencyThresholds.get(route.sourceChain);
        const targetThreshold = this.optimalLatencyThresholds.get(route.targetChain);
        const estimatedLatency = this.calculateConfidenceWeightedLatency(predictedSourceLatency, predictedTargetLatency, sourceThreshold, targetThreshold);
        return estimatedLatency;
    }
    async predictLatencyTrend(chainId, history) {
        if (history.length < 2)
            return 0;
        const shortTermMA = await this.calculateQuantumSafeMA(history.slice(-10));
        const mediumTermMA = await this.calculateQuantumSafeMA(history.slice(-30));
        const longTermMA = await this.calculateQuantumSafeMA(history);
        const trendStrength = await this.calculateQuantumTrendStrength(shortTermMA, mediumTermMA, longTermMA);
        const networkLoad = this.calculateNetworkLoad(chainId);
        const prediction = await this.generateQuantumSafePrediction(history, trendStrength, networkLoad);
        return Math.max(prediction, 50);
    }
    async calculateQuantumSafeMA(values) {
        if (values.length === 0)
            return 0;
        const quantumNoiseThreshold = this.config.ai.quantum.minLatticeSecurityLevel;
        const filteredValues = values.filter(val => {
            const noise = Math.random() * quantumNoiseThreshold;
            return val > noise;
        });
        const weights = filteredValues.map((_, i) => Math.exp(-i / filteredValues.length));
        const weightedSum = filteredValues.reduce((sum, val, i) => sum + val * weights[i], 0);
        const weightSum = weights.reduce((sum, weight) => sum + weight, 0);
        return weightedSum / weightSum;
    }
    async calculateQuantumTrendStrength(shortTerm, mediumTerm, longTerm) {
        const shortVsMedium = (shortTerm - mediumTerm) / mediumTerm;
        const mediumVsLong = (mediumTerm - longTerm) / longTerm;
        const trendData = Buffer.from(JSON.stringify({ shortVsMedium, mediumVsLong, timestamp: Date.now() }));
        const validation = await this.quantumValidator.validateModelState([
            [shortVsMedium],
            [mediumVsLong]
        ]);
        const quantumSafetyFactor = validation.quantumSafetyScore;
        const trendStrength = Math.abs(shortVsMedium * 0.7 + mediumVsLong * 0.3);
        return trendStrength * quantumSafetyFactor;
    }
    async generateQuantumSafePrediction(history, trendStrength, networkLoad) {
        const recentValues = history.slice(-5);
        const basePredictor = await this.calculateQuantumSafeMA(recentValues);
        const temporalHash = await this.generateTemporalHash(history[history.length - 1], history);
        const predictionData = Buffer.from(JSON.stringify({
            basePredictor,
            trendStrength,
            networkLoad,
            temporalHash
        }));
        const signature = await this.quantumValidator.generateQuantumSignature(predictionData);
        const latticeScore = await this.calculateLatticeSecurityScore(signature);
        const quantumAdjustment = (1 + networkLoad * trendStrength * latticeScore);
        const prediction = basePredictor * quantumAdjustment;
        this.logger.debug('Generated quantum-safe latency prediction', {
            basePredictor,
            trendStrength,
            networkLoad,
            latticeScore,
            finalPrediction: prediction
        });
        return prediction;
    }
    calculateConfidenceWeightedLatency(sourceLatency, targetLatency, sourceThreshold, targetThreshold) {
        const sourceConfidence = sourceThreshold
            ? Math.max(0, 1 - Math.abs(sourceLatency - sourceThreshold) / sourceThreshold)
            : 0.5;
        const targetConfidence = targetThreshold
            ? Math.max(0, 1 - Math.abs(targetLatency - targetThreshold) / targetThreshold)
            : 0.5;
        const totalConfidence = sourceConfidence + targetConfidence;
        const weightedLatency = ((sourceLatency * sourceConfidence + targetLatency * targetConfidence) /
            totalConfidence);
        return weightedLatency;
    }
    async updateLatencyThresholds() {
        for (const [chainId, history] of this.chainLatencyHistory.entries()) {
            if (history.length < 10)
                continue;
            const sortedLatencies = [...history].sort((a, b) => a - b);
            const median = sortedLatencies[Math.floor(sortedLatencies.length / 2)];
            const p95 = sortedLatencies[Math.floor(sortedLatencies.length * 0.95)];
            const mean = this.calculateMovingAverage(history);
            const variance = this.calculateVariance(history);
            const stdDev = Math.sqrt(variance);
            const networkLoad = this.calculateNetworkLoad(chainId);
            const adaptiveThreshold = median + (stdDev * (1 + networkLoad));
            const minThreshold = 50;
            const maxThreshold = 1000;
            const boundedThreshold = Math.min(Math.max(adaptiveThreshold, minThreshold), maxThreshold);
            const validationResult = await this.validateLatencyWithQuantumProof(chainId, median, boundedThreshold);
            this.optimalLatencyThresholds.set(chainId, boundedThreshold);
            this.updateLatencyMetrics(chainId, {
                median,
                stdDev,
                p95,
                threshold: boundedThreshold,
                quantumMetrics: {
                    latticeScore: validationResult.quantumMetrics.temporalConsistency,
                    temporalConsistency: validationResult.quantumMetrics.temporalConsistency,
                    networkLoadProof: validationResult.quantumMetrics.networkLoadProof
                }
            });
        }
    }
    async validateLatencyWithQuantumProof(chainId, latency, threshold) {
        const temporalHash = await this.generateTemporalHash(latency, this.chainLatencyHistory.get(chainId) || []);
        const latticeSig = await this.quantumValidator.generateQuantumSignature(Buffer.from(temporalHash + latency.toString()));
        const temporalConsistency = await this.validateTemporalConsistency(chainId, latency, threshold);
        const networkLoadProof = await this.generateNetworkLoadProof(chainId);
        const latticeScore = await this.calculateLatticeSecurityScore(latticeSig);
        const signature = await this.aggregateQuantumProofs({
            temporalHash,
            latticeSig,
            networkLoadProof,
            latticeScore
        });
        return {
            isValid: temporalConsistency >= 0.8 && latticeScore >= 0.85,
            signature,
            quantumMetrics: {
                temporalConsistency,
                latticeScore,
                networkLoadProof
            }
        };
    }
    async validateTemporalConsistency(chainId, currentLatency, threshold) {
        const history = this.chainLatencyHistory.get(chainId) || [];
        if (history.length < 2)
            return 1.0;
        const recentLatencies = history.slice(-5);
        const variance = this.calculateVariance(recentLatencies);
        const normalizedVariance = Math.min(variance / threshold, 1);
        const anomalyScore = this.detectTemporalAnomalies(currentLatency, recentLatencies);
        return Math.max(0, 1 - (normalizedVariance * 0.6 + anomalyScore * 0.4));
    }
    async generateNetworkLoadProof(chainId) {
        const networkLoad = this.calculateNetworkLoad(chainId);
        const timestamp = Date.now();
        const commitment = await this.quantumValidator.createCommitment(Buffer.from(JSON.stringify({
            chainId,
            networkLoad,
            timestamp
        })));
        return commitment;
    }
    async calculateLatticeSecurityScore(signature) {
        const latticeParams = await this.quantumValidator.getLatticeParams(signature);
        const securityLevel = await this.quantumValidator.calculateLatticeSecurity(latticeParams);
        return Math.min(securityLevel / this.config.ai.quantum.minLatticeSecurityLevel, 1);
    }
    detectTemporalAnomalies(currentLatency, history) {
        if (history.length === 0)
            return 0;
        const mean = this.calculateMovingAverage(history);
        const stdDev = Math.sqrt(this.calculateVariance(history));
        const zScore = Math.abs(currentLatency - mean) / (stdDev || 1);
        return Math.min(zScore / 3, 1);
    }
    async aggregateQuantumProofs(proofs) {
        const aggregatedProof = await this.quantumValidator.aggregateSignatures([
            Buffer.from(proofs.temporalHash),
            proofs.latticeSig,
            Buffer.from(proofs.networkLoadProof)
        ]);
        return JSON.stringify({
            proof: aggregatedProof,
            timestamp: Date.now(),
            latticeScore: proofs.latticeScore
        });
    }
    calculateMovingAverage(values) {
        if (values.length === 0)
            return 0;
        const sum = values.reduce((acc, val) => acc + val, 0);
        return sum / values.length;
    }
    async generateTemporalHash(latency, historicalData) {
        const timestamp = Date.now();
        const previousHash = historicalData.length > 0 ? historicalData[historicalData.length - 1].toString() : '0';
        const temporalData = Buffer.from(`${latency}-${historicalData.join(',')}-${timestamp}-${previousHash}`);
        return await this.quantumValidator.generateHash(temporalData);
    }
};
exports.AdversarialSimulator = AdversarialSimulator;
exports.AdversarialSimulator = AdversarialSimulator = __decorate([
    (0, common_1.Injectable)(),
    __metadata("design:paramtypes", [arbitrageScanner_1.ArbitrageScanner,
        liquidity_monitor_1.LiquidityMonitor,
        cross_chain_router_1.CrossChainRouter,
        winston_1.Logger, Object, alert_service_1.AlertService])
], AdversarialSimulator);
//# sourceMappingURL=adversarial_simulator.js.map