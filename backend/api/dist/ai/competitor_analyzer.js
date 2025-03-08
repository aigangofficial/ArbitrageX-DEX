"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.CompetitorAnalyzer = void 0;
const gan_trainer_1 = require("./gan_trainer");
const quantum_validator_1 = require("./quantum_validator");
class CompetitorAnalyzer {
    constructor(logger, liquidityMonitor, crossChainRouter, config, alertService) {
        this.logger = logger;
        this.liquidityMonitor = liquidityMonitor;
        this.crossChainRouter = crossChainRouter;
        this.config = config;
        this.alertService = alertService;
        this.competitors = new Map();
        this.recentTrades = [];
        this.ganTrainer = new gan_trainer_1.GANTrainer(logger, {
            hiddenUnits: [32, 16, 8],
            learningRate: 0.001
        });
        this.quantumValidator = new quantum_validator_1.QuantumValidator(logger, config.quantumSecurity, alertService);
    }
    async analyzeMempoolTransaction(tx, chainId) {
        try {
            if (!this.isArbitrageTx(tx))
                return;
            const pattern = await this.extractPattern(tx, chainId);
            if (!pattern)
                return;
            const competitor = this.getOrCreateCompetitor(tx.from || '', chainId);
            const validationResult = await this.quantumValidator.validateTransaction(tx, competitor);
            if (!validationResult.isValid) {
                this.logger.warn('Transaction failed quantum validation:', {
                    txHash: tx.hash,
                    threatLevel: validationResult.threatLevel,
                    recommendations: validationResult.recommendations
                });
                return;
            }
            await this.updateCompetitorStats(competitor, {
                ...pattern,
                quantumSafetyScore: validationResult.quantumSafetyScore
            });
            const scenario = this.generateAdversarialScenario(competitor);
            await this.simulateDefensiveStrategy(scenario);
        }
        catch (error) {
            this.logger.error('Error analyzing mempool transaction:', error);
        }
    }
    async extractPattern(tx, chainId) {
        try {
            if (!tx.from)
                return null;
            const decodedInput = this.decodeTransactionInput(tx.data || '0x');
            if (!decodedInput)
                return null;
            return {
                address: tx.from,
                chainId,
                avgGasPrice: tx.gasPrice || 0n,
                knownSelectors: new Set([decodedInput.selector]),
                preferredTokens: new Set(this.extractTokenAddresses(decodedInput)),
                routingPreference: await this.analyzeRouting(decodedInput, chainId)
            };
        }
        catch (error) {
            this.logger.error('Error extracting pattern:', error);
            return null;
        }
    }
    getOrCreateCompetitor(address, chainId) {
        const key = `${chainId}-${address}`;
        if (!this.competitors.has(key)) {
            this.competitors.set(key, {
                address,
                chainId,
                successRate: 0,
                avgGasPrice: 0n,
                lastSeen: Date.now(),
                transactionCount: 0,
                knownSelectors: new Set(),
                preferredTokens: new Set(),
                avgProfitPerTrade: 0n,
                routingPreference: {
                    chains: [chainId],
                    dexes: []
                },
                quantumSafetyScore: 0,
                patternStrength: 0,
                timeConsistency: 0
            });
        }
        return this.competitors.get(key);
    }
    async updateCompetitorStats(competitor, newPattern) {
        competitor.lastSeen = Date.now();
        competitor.transactionCount++;
        competitor.avgGasPrice = this.calculateMovingAverage(competitor.avgGasPrice, newPattern.avgGasPrice || 0n, competitor.transactionCount);
        if (newPattern.knownSelectors) {
            newPattern.knownSelectors.forEach(s => competitor.knownSelectors.add(s));
        }
        if (newPattern.preferredTokens) {
            newPattern.preferredTokens.forEach(t => competitor.preferredTokens.add(t));
        }
        if (newPattern.routingPreference) {
            competitor.routingPreference = {
                ...competitor.routingPreference,
                chains: [...new Set([...competitor.routingPreference.chains, ...newPattern.routingPreference.chains])],
                dexes: [...new Set([...competitor.routingPreference.dexes, ...newPattern.routingPreference.dexes])]
            };
        }
        competitor.quantumSafetyScore = newPattern.quantumSafetyScore || 0;
        if (newPattern.patternStrength) {
            competitor.patternStrength = newPattern.patternStrength;
        }
        if (newPattern.timeConsistency) {
            competitor.timeConsistency = newPattern.timeConsistency;
        }
    }
    generateAdversarialScenario(competitor) {
        const activityLevel = Math.min(competitor.transactionCount / this.config.minTransactionsForAnalysis, 1);
        const gasPriceImpact = this.calculateGasPriceImpact(competitor.avgGasPrice);
        return {
            competitorActivity: activityLevel,
            gasPriceSpike: gasPriceImpact,
            liquidityShock: this.estimateLiquidityImpact(competitor),
            marketVolatility: this.calculateVolatilityImpact(competitor)
        };
    }
    async simulateDefensiveStrategy(scenario) {
        try {
            await this.ganTrainer.trainGAN([scenario], 1, 1);
            const defensiveScenarios = this.ganTrainer.generateScenarios(5);
            for (const defScenario of defensiveScenarios) {
                await this.prepareMitigationStrategy(defScenario);
            }
        }
        catch (error) {
            this.logger.error('Error simulating defensive strategy:', error);
        }
    }
    async prepareMitigationStrategy(scenario) {
        const affectedTokens = this.getMostAffectedTokens();
        if (affectedTokens.size === 0)
            return;
        const liquidityDepth = await this.liquidityMonitor.getLiquidityDepth(scenario.liquidityShock, Array.from(affectedTokens)[0]);
        const alternativeRoutes = await this.crossChainRouter.findArbitrageRoutes(Array.from(affectedTokens)[0], liquidityDepth);
        this.updateRoutingStrategy(alternativeRoutes, scenario.competitorActivity);
    }
    calculateGasPriceImpact(avgGasPrice) {
        const baseGasPrice = 50n * 10n ** 9n;
        const impact = Number((avgGasPrice - baseGasPrice) * 100n / baseGasPrice);
        return Math.max(0, Math.min(1, impact / 200));
    }
    estimateLiquidityImpact(competitor) {
        const recentActivity = this.recentTrades.filter(t => t.from === competitor.address &&
            Date.now() - t.timestamp < this.config.maxTrackingAge);
        const totalVolume = recentActivity.reduce((sum, trade) => sum + (trade.profit || 0n), 0n);
        return Math.min(1, Number(totalVolume) / 1e18);
    }
    calculateVolatilityImpact(competitor) {
        const successRate = competitor.successRate;
        const activity = competitor.transactionCount / this.config.minTransactionsForAnalysis;
        return Math.min(1, (successRate * activity) / 2);
    }
    getMostAffectedTokens() {
        const tokenCounts = new Map();
        for (const competitor of this.competitors.values()) {
            competitor.preferredTokens.forEach(token => {
                tokenCounts.set(token, (tokenCounts.get(token) || 0) + 1);
            });
        }
        return new Set(Array.from(tokenCounts.entries())
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5)
            .map(([token]) => token));
    }
    calculateMovingAverage(current, new_value, count) {
        return (current * BigInt(count - 1) + new_value) / BigInt(count);
    }
    isArbitrageTx(tx) {
        if (!tx.data || tx.data.length < 10)
            return false;
        const selector = tx.data.slice(0, 10);
        return this.isKnownArbitrageSelector(selector);
    }
    isKnownArbitrageSelector(selector) {
        const knownSelectors = new Set([
            '0x3b663803',
            '0x6af479b2',
            '0x9f9a3a7a'
        ]);
        return knownSelectors.has(selector);
    }
    decodeTransactionInput(data) {
        try {
            const selector = data.slice(0, 10);
            const params = this.decodeParams(data.slice(10));
            return { selector, params };
        }
        catch {
            return null;
        }
    }
    decodeParams(data) {
        return {};
    }
    extractTokenAddresses(decodedInput) {
        const addresses = [];
        if (decodedInput.params.tokenIn)
            addresses.push(decodedInput.params.tokenIn);
        if (decodedInput.params.tokenOut)
            addresses.push(decodedInput.params.tokenOut);
        if (decodedInput.params.path)
            addresses.push(...decodedInput.params.path);
        return [...new Set(addresses)];
    }
    async analyzeRouting(decodedInput, chainId) {
        return {
            chains: [chainId],
            dexes: decodedInput.params.dex ? [decodedInput.params.dex] : []
        };
    }
    updateRoutingStrategy(routes, competitorActivity) {
    }
    analyzeCompetitor(address, transactions) {
        try {
            const pattern = {
                address,
                chainId: 0,
                successRate: this.calculateSuccessRate(transactions),
                avgGasPrice: this.calculateAverageGasPrice(transactions),
                lastSeen: this.getLastSeen(transactions),
                transactionCount: transactions.length,
                knownSelectors: this.extractSelectors(transactions),
                preferredTokens: this.extractPreferredTokens(transactions),
                avgProfitPerTrade: BigInt(0),
                quantumSafetyScore: 0,
                routingPreference: {
                    chains: [0],
                    dexes: []
                },
                patternStrength: this.calculatePatternStrength(transactions),
                timeConsistency: this.calculateTimeConsistency(transactions)
            };
            return pattern;
        }
        catch (error) {
            this.logger.error('Error analyzing competitor:', error);
            return {
                address,
                chainId: 0,
                successRate: 0,
                avgGasPrice: BigInt(0),
                lastSeen: Date.now(),
                transactionCount: 0,
                knownSelectors: new Set(),
                preferredTokens: new Set(),
                avgProfitPerTrade: BigInt(0),
                quantumSafetyScore: 0,
                routingPreference: {
                    chains: [0],
                    dexes: []
                },
                patternStrength: 0,
                timeConsistency: 0
            };
        }
    }
    getLastSeen(transactions) {
        if (transactions.length === 0)
            return Date.now();
        const timestamps = transactions.map(tx => tx.timestamp || 0);
        return Math.max(...timestamps) * 1000;
    }
    calculateSuccessRate(transactions) {
        if (transactions.length === 0)
            return 0;
        const successful = transactions.filter(tx => tx.status === 1).length;
        return successful / transactions.length;
    }
    calculateAverageGasPrice(transactions) {
        if (transactions.length === 0)
            return BigInt(0);
        const total = transactions.reduce((sum, tx) => sum + (tx.gasPrice || BigInt(0)), BigInt(0));
        return total / BigInt(transactions.length);
    }
    extractSelectors(transactions) {
        const selectors = new Set();
        for (const tx of transactions) {
            if (tx.data && tx.data.length >= 10) {
                selectors.add(tx.data.slice(0, 10));
            }
        }
        return selectors;
    }
    extractPreferredTokens(transactions) {
        const tokens = new Set();
        for (const tx of transactions) {
            if (tx.to) {
                tokens.add(tx.to);
            }
        }
        return tokens;
    }
    calculatePatternStrength(transactions) {
        if (transactions.length < this.config.minTransactions)
            return 0;
        const gasPriceVariance = this.calculateGasPriceVariance(transactions);
        const timingRegularity = this.calculateTimingRegularity(transactions);
        const interactionRepetition = this.calculateInteractionRepetition(transactions);
        return (gasPriceVariance * 0.3 +
            timingRegularity * 0.4 +
            interactionRepetition * 0.3);
    }
    calculateTimeConsistency(transactions) {
        if (transactions.length < 2)
            return 0;
        const sortedTx = [...transactions].sort((a, b) => (a.timestamp || 0) - (b.timestamp || 0));
        let totalDeviation = 0;
        const intervals = [];
        for (let i = 1; i < sortedTx.length; i++) {
            const interval = (sortedTx[i].timestamp || 0) - (sortedTx[i - 1].timestamp || 0);
            intervals.push(interval);
        }
        const avgInterval = intervals.reduce((sum, val) => sum + val, 0) / intervals.length;
        for (const interval of intervals) {
            totalDeviation += Math.pow(interval - avgInterval, 2);
        }
        const stdDev = Math.sqrt(totalDeviation / intervals.length);
        const maxAcceptableStdDev = avgInterval * 0.5;
        return Math.max(0, 1 - (stdDev / maxAcceptableStdDev));
    }
    calculateGasPriceVariance(transactions) {
        if (transactions.length < 2)
            return 0;
        const gasPrices = transactions.map(tx => Number(tx.gasPrice || 0));
        const avg = gasPrices.reduce((sum, val) => sum + val, 0) / gasPrices.length;
        const variance = gasPrices.reduce((sum, val) => sum + Math.pow(val - avg, 2), 0) / gasPrices.length;
        const maxAcceptableVariance = avg * 0.25;
        return Math.max(0, 1 - (Math.sqrt(variance) / maxAcceptableVariance));
    }
    calculateTimingRegularity(transactions) {
        if (transactions.length < 2)
            return 0;
        const timestamps = transactions.map(tx => tx.timestamp || 0);
        const intervals = [];
        for (let i = 1; i < timestamps.length; i++) {
            intervals.push(timestamps[i] - timestamps[i - 1]);
        }
        const avgInterval = intervals.reduce((sum, val) => sum + val, 0) / intervals.length;
        const variance = intervals.reduce((sum, val) => sum + Math.pow(val - avgInterval, 2), 0) / intervals.length;
        const maxAcceptableVariance = avgInterval * 0.5;
        return Math.max(0, 1 - (Math.sqrt(variance) / maxAcceptableVariance));
    }
    calculateInteractionRepetition(transactions) {
        const interactions = new Map();
        for (const tx of transactions) {
            const key = `${tx.to}-${tx.data?.slice(0, 10)}`;
            interactions.set(key, (interactions.get(key) || 0) + 1);
        }
        let entropy = 0;
        const total = transactions.length;
        for (const count of interactions.values()) {
            const probability = count / total;
            entropy -= probability * Math.log2(probability);
        }
        const maxEntropy = Math.log2(interactions.size || 1);
        return Math.max(0, 1 - (entropy / maxEntropy));
    }
}
exports.CompetitorAnalyzer = CompetitorAnalyzer;
//# sourceMappingURL=competitor_analyzer.js.map