import { BigNumber } from '@ethersproject/bignumber';

export interface SimulationScenario {
    liquidityShock: number;
    gasPriceSpike: number;
    competitorActivity: number;
    marketVolatility: number;
}

export interface CrossChainRoute {
    sourceChain: number;
    targetChain: number;
    bridge: {
        chainId: number;
        bridgeAddress: string;
        tokenMappings: Map<string, string>;
        estimatedTime: number;
        fee: bigint;
    };
    sourceToken: string;
    targetToken: string;
    estimatedProfit: bigint;
    executionPath: string[];
    gasEstimate: bigint;
}

export interface AdversarialMetrics {
    quantumSafetyScore: number;
    threatLevel: 'LOW' | 'MEDIUM' | 'HIGH';
    recommendations: string[];
    gradientNorm: number;
    latencyOptimization: {
        sourceThreshold: number | undefined;
        targetThreshold: number | undefined;
        currentLatency: number;
    } | null;
}

export interface SimulationResult {
    scenario: SimulationScenario;
    trades: Array<{
        success: boolean;
        error?: string;
        profit?: bigint;
        gasUsed?: bigint;
        adversarialMetrics?: AdversarialMetrics;
    }>;
    metrics: {
        successRate: number;
        averageProfit: bigint;
        totalGasUsed: bigint;
        executionTime: number;
        competitorInteractions: number;
        failedTransactions: number;
    };
    timestamp: number;
    quantumMetrics: {
        safetyScore: number;
        threatLevel: 'LOW' | 'MEDIUM' | 'HIGH';
        recommendations: string[];
    };
}

export interface GANConfig {
    hiddenUnits: number[];
    learningRate: number;
    epochs: number;
    batchSize: number;
}

export interface AIConfig {
    modelPath: string;
    batchSize: number;
    learningRate: number;
    epochs: number;
    gan: GANConfig;
    quantum: {
        minLatticeSecurityLevel: number;
        challengeWindowMs: number;
    };
    adversarialTraining: {
        scenarios: SimulationScenario[];
        frequency: number;
        intensityRange: [number, number];
    };
} 