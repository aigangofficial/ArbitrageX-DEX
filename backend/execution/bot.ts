import { ethers } from 'ethers';
import { FlashLoanService } from '../types/contracts';
import { ArbitrageScanner } from './arbitrageScanner';
import { WebSocketServer } from 'ws';

interface BotConfig {
    provider: ethers.Provider;
    flashLoanAddress: string;
    minProfitThreshold: number;
}

interface TradeResult {
    success: boolean;
    txHash?: string;
    error?: string;
    profit?: string;
    gasUsed?: string;
}

export class ArbitrageBot {
    private readonly flashLoanService: FlashLoanService;
    private readonly scanner: ArbitrageScanner;
    private isRunning: boolean;
    private readonly mockWsServer: WebSocketServer;

    constructor(config: BotConfig) {
        this.flashLoanService = new FlashLoanService(
            config.flashLoanAddress,
            config.provider
        );

        // Create a mock WebSocket server for testing
        this.mockWsServer = new WebSocketServer({ noServer: true });
        this.mockWsServer.clients = new Set();

        this.scanner = new ArbitrageScanner(
            this.flashLoanService,
            this.mockWsServer
        );
        this.isRunning = false;
    }

    public async start(): Promise<void> {
        if (this.isRunning) {
            throw new Error('Bot is already running');
        }

        this.isRunning = true;
        console.log('ArbitrageBot started');

        try {
            // Start monitoring for opportunities
            await this.monitorOpportunities();
        } catch (error) {
            console.error('Error in bot:', error);
            this.isRunning = false;
            throw error;
        }
    }

    public stop(): void {
        this.isRunning = false;
        this.mockWsServer.close();
        console.log('ArbitrageBot stopped');
    }

    private async monitorOpportunities(): Promise<void> {
        while (this.isRunning) {
            try {
                // Monitor prices and execute trades
                await new Promise(resolve => setTimeout(resolve, 1000));
            } catch (error) {
                console.error('Error monitoring opportunities:', error);
            }
        }
    }

    private async executeTrade(params: {
        tokenA: string;
        tokenB: string;
        amount: bigint;
        minProfit: bigint;
    }): Promise<TradeResult> {
        try {
            const tx = await this.flashLoanService.executeArbitrage(
                params.tokenA,
                params.tokenB,
                'Uniswap', // Default exchange A
                'SushiSwap', // Default exchange B
                params.amount
            );

            const receipt = await tx.wait();

            return {
                success: true,
                txHash: receipt.hash,
                profit: params.minProfit.toString(),
                gasUsed: receipt.gasUsed?.toString()
            };
        } catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : 'Unknown error'
            };
        }
    }
} 