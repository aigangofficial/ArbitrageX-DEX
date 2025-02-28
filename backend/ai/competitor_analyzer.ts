import { ethers } from 'ethers';
import { Logger } from 'winston';
import { SimulationScenario } from '../api/config';
import { GANTrainer } from './gan_trainer';
import { LiquidityMonitor } from '../services/liquidity_monitor';
import { CrossChainRouter } from '../services/cross_chain_router';
import { QuantumValidator } from './quantum_validator';

interface ExtendedTransaction extends ethers.Transaction {
    timestamp?: number;
    status?: number;
}

export interface CompetitorPattern {
    address: string;
    chainId: number;
    successRate: number;
    avgGasPrice: bigint;
    lastSeen: number;
    transactionCount: number;
    knownSelectors: Set<string>;
    preferredTokens: Set<string>;
    avgProfitPerTrade: bigint;
    quantumSafetyScore: number;
    routingPreference: {
        chains: number[];
        dexes: string[];
        bridgePreference?: string;
    };
    patternStrength: number;
    timeConsistency: number;
}

interface CompetitorTrade {
    chainId: number;
    txHash: string;
    from: string;
    gasPrice: bigint;
    gasUsed: bigint;
    profit?: bigint;
    route: string[];
    timestamp: number;
    success: boolean;
}

interface DecodedInput {
    selector: string;
    params: {
        tokenIn?: string;
        tokenOut?: string;
        path?: string[];
        dex?: string;
    };
}

export class CompetitorAnalyzer {
    private competitors: Map<string, CompetitorPattern> = new Map();
    private recentTrades: CompetitorTrade[] = [];
    private ganTrainer: GANTrainer;
    private quantumValidator: QuantumValidator;
    
    constructor(
        private readonly logger: Logger,
        private readonly liquidityMonitor: LiquidityMonitor,
        private readonly crossChainRouter: CrossChainRouter,
        private readonly config: {
            minTransactionsForAnalysis: number;
            maxTrackingAge: number;
            updateInterval: number;
            quantumSecurity: {
                minLatticeSecurityLevel: number;
                postQuantumScheme: 'FALCON' | 'DILITHIUM' | 'SPHINCS+';
                challengeWindowMs: number;
            };
            minTransactions: number;
            maxPatternAge: number;
            minSuccessRate: number;
        }
    ) {
        this.ganTrainer = new GANTrainer(logger, {
            hiddenUnits: [32, 16, 8],
            learningRate: 0.001
        });
        
        this.quantumValidator = new QuantumValidator(logger, config.quantumSecurity);
    }

    async analyzeMempoolTransaction(tx: ethers.Transaction, chainId: number): Promise<void> {
        try {
            if (!this.isArbitrageTx(tx)) return;

            const pattern = await this.extractPattern(tx, chainId);
            if (!pattern) return;

            const competitor = this.getOrCreateCompetitor(tx.from || '', chainId);
            
            // Validate transaction with quantum-safe checks
            const validationResult = await this.quantumValidator.validateTransaction(tx, competitor);
            
            if (!validationResult.isValid) {
                this.logger.warn('Transaction failed quantum validation:', {
                    txHash: tx.hash,
                    threatLevel: validationResult.threatLevel,
                    recommendations: validationResult.recommendations
                });
                return;
            }

            // Update competitor stats with quantum safety score
            await this.updateCompetitorStats(competitor, {
                ...pattern,
                quantumSafetyScore: validationResult.quantumSafetyScore
            });

            // Generate adversarial scenario based on competitor pattern
            const scenario = this.generateAdversarialScenario(competitor);
            await this.simulateDefensiveStrategy(scenario);

        } catch (error) {
            this.logger.error('Error analyzing mempool transaction:', error);
        }
    }

    private async extractPattern(tx: ethers.Transaction, chainId: number): Promise<Partial<CompetitorPattern> | null> {
        try {
            if (!tx.from) return null;
            
            const decodedInput = this.decodeTransactionInput(tx.data || '0x');
            if (!decodedInput) return null;

            return {
                address: tx.from,
                chainId,
                avgGasPrice: tx.gasPrice || 0n,
                knownSelectors: new Set([decodedInput.selector]),
                preferredTokens: new Set(this.extractTokenAddresses(decodedInput)),
                routingPreference: await this.analyzeRouting(decodedInput, chainId)
            };
        } catch (error) {
            this.logger.error('Error extracting pattern:', error);
            return null;
        }
    }

    private getOrCreateCompetitor(address: string, chainId: number): CompetitorPattern {
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
        return this.competitors.get(key)!;
    }

    private async updateCompetitorStats(
        competitor: CompetitorPattern,
        newPattern: Partial<CompetitorPattern>
    ): Promise<void> {
        competitor.lastSeen = Date.now();
        competitor.transactionCount++;

        // Update gas price moving average
        competitor.avgGasPrice = this.calculateMovingAverage(
            competitor.avgGasPrice,
            newPattern.avgGasPrice || 0n,
            competitor.transactionCount
        );

        // Update known selectors and tokens
        if (newPattern.knownSelectors) {
            newPattern.knownSelectors.forEach(s => competitor.knownSelectors.add(s));
        }
        if (newPattern.preferredTokens) {
            newPattern.preferredTokens.forEach(t => competitor.preferredTokens.add(t));
        }

        // Update routing preferences
        if (newPattern.routingPreference) {
            competitor.routingPreference = {
                ...competitor.routingPreference,
                chains: [...new Set([...competitor.routingPreference.chains, ...newPattern.routingPreference.chains])],
                dexes: [...new Set([...competitor.routingPreference.dexes, ...newPattern.routingPreference.dexes])]
            };
        }

        // Update quantum safety score
        competitor.quantumSafetyScore = newPattern.quantumSafetyScore || 0;

        // Update pattern strength and time consistency
        if (newPattern.patternStrength) {
            competitor.patternStrength = newPattern.patternStrength;
        }
        if (newPattern.timeConsistency) {
            competitor.timeConsistency = newPattern.timeConsistency;
        }
    }

    private generateAdversarialScenario(competitor: CompetitorPattern): SimulationScenario {
        const activityLevel = Math.min(competitor.transactionCount / this.config.minTransactionsForAnalysis, 1);
        const gasPriceImpact = this.calculateGasPriceImpact(competitor.avgGasPrice);
        
        return {
            competitorActivity: activityLevel,
            gasPriceSpike: gasPriceImpact,
            liquidityShock: this.estimateLiquidityImpact(competitor),
            marketVolatility: this.calculateVolatilityImpact(competitor)
        };
    }

    private async simulateDefensiveStrategy(scenario: SimulationScenario): Promise<void> {
        try {
            // Train GAN with new scenario
            await this.ganTrainer.trainGAN([scenario], 1, 1);

            // Generate defensive scenarios
            const defensiveScenarios = this.ganTrainer.generateScenarios(5);
            
            // Analyze and prepare defensive measures
            for (const defScenario of defensiveScenarios) {
                await this.prepareMitigationStrategy(defScenario);
            }
        } catch (error) {
            this.logger.error('Error simulating defensive strategy:', error);
        }
    }

    private async prepareMitigationStrategy(scenario: SimulationScenario): Promise<void> {
        const affectedTokens = this.getMostAffectedTokens();
        if (affectedTokens.size === 0) return;

        // Monitor liquidity across affected chains
        const liquidityDepth = await this.liquidityMonitor.getLiquidityDepth(
            scenario.liquidityShock,
            Array.from(affectedTokens)[0] // Use first token as reference
        );

        // Prepare alternative routes
        const alternativeRoutes = await this.crossChainRouter.findArbitrageRoutes(
            Array.from(affectedTokens)[0], // Use first token as reference
            liquidityDepth
        );

        // Update routing preferences based on competitor activity
        this.updateRoutingStrategy(alternativeRoutes, scenario.competitorActivity);
    }

    private calculateGasPriceImpact(avgGasPrice: bigint): number {
        const baseGasPrice = 50n * 10n ** 9n; // 50 gwei
        const impact = Number((avgGasPrice - baseGasPrice) * 100n / baseGasPrice);
        return Math.max(0, Math.min(1, impact / 200)); // Normalize to 0-1
    }

    private estimateLiquidityImpact(competitor: CompetitorPattern): number {
        const recentActivity = this.recentTrades.filter(t => 
            t.from === competitor.address &&
            Date.now() - t.timestamp < this.config.maxTrackingAge
        );

        const totalVolume = recentActivity.reduce((sum, trade) => sum + (trade.profit || 0n), 0n);
        return Math.min(1, Number(totalVolume) / 1e18); // Normalize to 0-1
    }

    private calculateVolatilityImpact(competitor: CompetitorPattern): number {
        const successRate = competitor.successRate;
        const activity = competitor.transactionCount / this.config.minTransactionsForAnalysis;
        return Math.min(1, (successRate * activity) / 2);
    }

    private getMostAffectedTokens(): Set<string> {
        const tokenCounts = new Map<string, number>();
        
        for (const competitor of this.competitors.values()) {
            competitor.preferredTokens.forEach(token => {
                tokenCounts.set(token, (tokenCounts.get(token) || 0) + 1);
            });
        }

        return new Set(
            Array.from(tokenCounts.entries())
                .sort((a, b) => b[1] - a[1])
                .slice(0, 5)
                .map(([token]) => token)
        );
    }

    private calculateMovingAverage(current: bigint, new_value: bigint, count: number): bigint {
        return (current * BigInt(count - 1) + new_value) / BigInt(count);
    }

    private isArbitrageTx(tx: ethers.Transaction): boolean {
        if (!tx.data || tx.data.length < 10) return false;
        const selector = tx.data.slice(0, 10);
        return this.isKnownArbitrageSelector(selector);
    }

    private isKnownArbitrageSelector(selector: string): boolean {
        const knownSelectors = new Set([
            '0x3b663803', // executeArbitrage
            '0x6af479b2', // flashArbitrage
            '0x9f9a3a7a'  // multiDexTrade
        ]);
        return knownSelectors.has(selector);
    }

    private decodeTransactionInput(data: string): DecodedInput | null {
        try {
            // Basic decoding of known function selectors
            const selector = data.slice(0, 10);
            const params = this.decodeParams(data.slice(10));
            return { selector, params };
        } catch {
            return null;
        }
    }

    private decodeParams(data: string): DecodedInput['params'] {
        // Implement parameter decoding based on known function layouts
        return {};
    }

    private extractTokenAddresses(decodedInput: DecodedInput): string[] {
        const addresses: string[] = [];
        if (decodedInput.params.tokenIn) addresses.push(decodedInput.params.tokenIn);
        if (decodedInput.params.tokenOut) addresses.push(decodedInput.params.tokenOut);
        if (decodedInput.params.path) addresses.push(...decodedInput.params.path);
        return [...new Set(addresses)];
    }

    private async analyzeRouting(decodedInput: DecodedInput, chainId: number): Promise<CompetitorPattern['routingPreference']> {
        return {
            chains: [chainId],
            dexes: decodedInput.params.dex ? [decodedInput.params.dex] : []
        };
    }

    private updateRoutingStrategy(routes: any[], competitorActivity: number): void {
        // Implement routing strategy updates
    }

    public analyzeCompetitor(
        address: string,
        transactions: ExtendedTransaction[]
    ): CompetitorPattern {
        try {
            const pattern: CompetitorPattern = {
                address,
                chainId: 0, // Assuming default chainId
                successRate: this.calculateSuccessRate(transactions),
                avgGasPrice: this.calculateAverageGasPrice(transactions),
                lastSeen: this.getLastSeen(transactions),
                transactionCount: transactions.length,
                knownSelectors: this.extractSelectors(transactions),
                preferredTokens: this.extractPreferredTokens(transactions),
                avgProfitPerTrade: BigInt(0), // Assuming default avgProfitPerTrade
                quantumSafetyScore: 0, // Assuming default quantumSafetyScore
                routingPreference: {
                    chains: [0], // Assuming default chain
                    dexes: []
                },
                patternStrength: this.calculatePatternStrength(transactions),
                timeConsistency: this.calculateTimeConsistency(transactions)
            };

            return pattern;
        } catch (error) {
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

    private getLastSeen(transactions: ExtendedTransaction[]): number {
        if (transactions.length === 0) return Date.now();
        const timestamps = transactions.map(tx => tx.timestamp || 0);
        return Math.max(...timestamps) * 1000; // Convert to milliseconds
    }

    private calculateSuccessRate(transactions: ExtendedTransaction[]): number {
        if (transactions.length === 0) return 0;
        const successful = transactions.filter(tx => tx.status === 1).length;
        return successful / transactions.length;
    }

    private calculateAverageGasPrice(transactions: ExtendedTransaction[]): bigint {
        if (transactions.length === 0) return BigInt(0);
        const total = transactions.reduce((sum, tx) => sum + (tx.gasPrice || BigInt(0)), BigInt(0));
        return total / BigInt(transactions.length);
    }

    private extractSelectors(transactions: ExtendedTransaction[]): Set<string> {
        const selectors = new Set<string>();
        for (const tx of transactions) {
            if (tx.data && tx.data.length >= 10) {
                selectors.add(tx.data.slice(0, 10));
            }
        }
        return selectors;
    }

    private extractPreferredTokens(transactions: ExtendedTransaction[]): Set<string> {
        const tokens = new Set<string>();
        for (const tx of transactions) {
            if (tx.to) {
                tokens.add(tx.to);
            }
        }
        return tokens;
    }

    private calculatePatternStrength(transactions: ExtendedTransaction[]): number {
        if (transactions.length < this.config.minTransactions) return 0;
        
        // Calculate pattern strength based on:
        // 1. Consistency in gas price strategy
        // 2. Regularity in transaction timing
        // 3. Repetition in contract interactions
        
        const gasPriceVariance = this.calculateGasPriceVariance(transactions);
        const timingRegularity = this.calculateTimingRegularity(transactions);
        const interactionRepetition = this.calculateInteractionRepetition(transactions);
        
        // Weight the factors (can be adjusted based on importance)
        return (
            gasPriceVariance * 0.3 +
            timingRegularity * 0.4 +
            interactionRepetition * 0.3
        );
    }

    private calculateTimeConsistency(transactions: ExtendedTransaction[]): number {
        if (transactions.length < 2) return 0;
        
        // Sort transactions by timestamp
        const sortedTx = [...transactions].sort((a, b) => 
            (a.timestamp || 0) - (b.timestamp || 0)
        );
        
        // Calculate average time between transactions
        let totalDeviation = 0;
        const intervals: number[] = [];
        
        for (let i = 1; i < sortedTx.length; i++) {
            const interval = (sortedTx[i].timestamp || 0) - (sortedTx[i-1].timestamp || 0);
            intervals.push(interval);
        }
        
        const avgInterval = intervals.reduce((sum, val) => sum + val, 0) / intervals.length;
        
        // Calculate standard deviation of intervals
        for (const interval of intervals) {
            totalDeviation += Math.pow(interval - avgInterval, 2);
        }
        const stdDev = Math.sqrt(totalDeviation / intervals.length);
        
        // Convert to a 0-1 score (lower deviation = higher consistency)
        const maxAcceptableStdDev = avgInterval * 0.5; // 50% of average interval
        return Math.max(0, 1 - (stdDev / maxAcceptableStdDev));
    }

    private calculateGasPriceVariance(transactions: ExtendedTransaction[]): number {
        if (transactions.length < 2) return 0;
        
        const gasPrices = transactions.map(tx => Number(tx.gasPrice || 0));
        const avg = gasPrices.reduce((sum, val) => sum + val, 0) / gasPrices.length;
        const variance = gasPrices.reduce((sum, val) => sum + Math.pow(val - avg, 2), 0) / gasPrices.length;
        
        // Convert to a 0-1 score (lower variance = higher consistency)
        const maxAcceptableVariance = avg * 0.25; // 25% of average gas price
        return Math.max(0, 1 - (Math.sqrt(variance) / maxAcceptableVariance));
    }

    private calculateTimingRegularity(transactions: ExtendedTransaction[]): number {
        if (transactions.length < 2) return 0;
        
        const timestamps = transactions.map(tx => tx.timestamp || 0);
        const intervals = [];
        
        for (let i = 1; i < timestamps.length; i++) {
            intervals.push(timestamps[i] - timestamps[i-1]);
        }
        
        const avgInterval = intervals.reduce((sum, val) => sum + val, 0) / intervals.length;
        const variance = intervals.reduce((sum, val) => sum + Math.pow(val - avgInterval, 2), 0) / intervals.length;
        
        // Convert to a 0-1 score (lower variance = higher regularity)
        const maxAcceptableVariance = avgInterval * 0.5; // 50% of average interval
        return Math.max(0, 1 - (Math.sqrt(variance) / maxAcceptableVariance));
    }

    private calculateInteractionRepetition(transactions: ExtendedTransaction[]): number {
        const interactions = new Map<string, number>();
        
        for (const tx of transactions) {
            const key = `${tx.to}-${tx.data?.slice(0, 10)}`;
            interactions.set(key, (interactions.get(key) || 0) + 1);
        }
        
        // Calculate entropy of interaction distribution
        let entropy = 0;
        const total = transactions.length;
        
        for (const count of interactions.values()) {
            const probability = count / total;
            entropy -= probability * Math.log2(probability);
        }
        
        // Convert entropy to a 0-1 score (lower entropy = higher repetition)
        const maxEntropy = Math.log2(interactions.size || 1);
        return Math.max(0, 1 - (entropy / maxEntropy));
    }
} 