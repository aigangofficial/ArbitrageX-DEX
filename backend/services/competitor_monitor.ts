import { TransactionResponse } from 'ethers';
import { Logger } from 'winston';
import { getConfig } from '../api/config';

interface CompetitorPattern {
    address: string;
    successRate: number;
    avgGasPrice: bigint;
    lastSeen: number;
    transactionCount: number;
    knownSelectors: Set<string>;
}

export class CompetitorMonitor {
    private config = getConfig();
    private logger: Logger;
    private patterns: Map<string, CompetitorPattern> = new Map();
    private anomalyThreshold: number;
    private checkInterval: number;

    constructor(logger: Logger) {
        this.logger = logger;
        this.anomalyThreshold = this.config.flashbots.monitoring.anomalyThreshold;
        this.checkInterval = this.config.flashbots.monitoring.checkInterval;

        // Start periodic pattern analysis
        setInterval(() => this._analyzePatterns(), this.checkInterval);
    }

    public analyzeTransaction(tx: TransactionResponse): boolean {
        try {
            // Skip if transaction is from a known safe address
            if (this._isKnownSafeAddress(tx.from)) {
                return false;
            }

            // Extract transaction details
            const pattern = this._getOrCreatePattern(tx.from);
            const selector = tx.data.slice(0, 10); // First 4 bytes of calldata

            // Update pattern data
            pattern.lastSeen = Date.now();
            pattern.transactionCount++;
            pattern.knownSelectors.add(selector);
            pattern.avgGasPrice = this._updateAvgGasPrice(pattern.avgGasPrice, tx.gasPrice);

            // Check for suspicious patterns
            return this._isCompetitorActivity(pattern, tx);
        } catch (error) {
            this.logger.error('Error analyzing transaction:', error);
            return false;
        }
    }

    private _isKnownSafeAddress(address: string): boolean {
        return this.config.flashbots.protection.whitelistedCallers.includes(address);
    }

    private _getOrCreatePattern(address: string): CompetitorPattern {
        if (!this.patterns.has(address)) {
            this.patterns.set(address, {
                address,
                successRate: 0,
                avgGasPrice: BigInt(0),
                lastSeen: Date.now(),
                transactionCount: 0,
                knownSelectors: new Set()
            });
        }
        return this.patterns.get(address)!;
    }

    private _updateAvgGasPrice(currentAvg: bigint, newPrice: bigint | null): bigint {
        if (!newPrice) return currentAvg;
        
        const weight = 0.7; // Weight for exponential moving average
        return BigInt(Math.floor(
            Number(currentAvg) * weight + Number(newPrice) * (1 - weight)
        ));
    }

    private _isCompetitorActivity(pattern: CompetitorPattern, tx: TransactionResponse): boolean {
        // Check for high frequency trading patterns
        const isHighFrequency = pattern.transactionCount > 100 && 
            (Date.now() - pattern.lastSeen) < 3600000; // 1 hour

        // Check for gas price manipulation
        const isGasManipulated = tx.gasPrice ? 
            Number(tx.gasPrice) > Number(pattern.avgGasPrice) * 2 : false;

        // Check for known competitive selectors
        const usesCompetitiveSelectors = Array.from(pattern.knownSelectors)
            .some(selector => this.config.flashbots.monitoring.knownSelectors.includes(selector));

        // Combine signals
        return (isHighFrequency && isGasManipulated) || 
               (isHighFrequency && usesCompetitiveSelectors) ||
               (isGasManipulated && usesCompetitiveSelectors);
    }

    private _analyzePatterns() {
        try {
            const now = Date.now();
            const staleThreshold = now - (24 * 3600 * 1000); // 24 hours

            // Clean up stale patterns
            for (const [address, pattern] of this.patterns.entries()) {
                if (pattern.lastSeen < staleThreshold) {
                    this.patterns.delete(address);
                    continue;
                }

                // Detect anomalies
                if (this._detectAnomaly(pattern)) {
                    this.logger.warn('Anomaly detected for address:', {
                        address: pattern.address,
                        transactionCount: pattern.transactionCount,
                        avgGasPrice: pattern.avgGasPrice.toString(),
                        selectorCount: pattern.knownSelectors.size
                    });
                }
            }
        } catch (error) {
            this.logger.error('Error analyzing patterns:', error);
        }
    }

    private _detectAnomaly(pattern: CompetitorPattern): boolean {
        const avgGasPrice = this.config.flashbots.monitoring.avgGasPrice;
        
        // Check for significant deviations
        return pattern.transactionCount > 1000 || // High volume
            Number(pattern.avgGasPrice) > Number(avgGasPrice) * 3 || // High gas price
            pattern.knownSelectors.size > 20; // Too many different function calls
    }
} 