import { SimulationScenario } from '../../api/config';

export interface SimulatedTrade {
    timestamp: number;
    tokenA: string;
    tokenB: string;
    amount: bigint;
    expectedProfit: bigint;
    actualProfit: bigint;
    gasUsed: bigint;
    success: boolean;
    error?: string;
}

export interface SimulationResult {
    metrics: {
        successRate: number;
        averageProfit: bigint;
        totalGasUsed: bigint;
        executionTime: number;
        competitorInteractions: number;
        failedTransactions: number;
        networkLatency?: number;
        liquidityImpact?: number;
    };
    scenario: SimulationScenario;
    trades: SimulatedTrade[];
    timestamp: number;
}

export interface LiquidityPool {
    address: string;
    chainId: number;
    token0: string;
    token1: string;
    reserve0: bigint;
    reserve1: bigint;
    fee: number;
    lastPrice: bigint;
    tokenA: string;
    tokenB: string;
    lastUpdate: number;
}

export interface ArbitrageOpportunity {
    pair: string;
    amount: bigint;
    expectedProfit: bigint;
    gasEstimate: bigint;
}

export interface SimulatedTradeResult {
    success: boolean;
    error?: string;
    profit?: bigint;
    gasUsed?: bigint;
} 