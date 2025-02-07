/// <reference types="jest" />

import { ArbitrageScanner, PriceData } from '../execution/arbitrageScanner';
import { FlashLoanService, IUniswapV2Router02 } from '../types/contracts';
import { WebSocketServer } from 'ws';

jest.mock('../types/contracts');
jest.mock('ws');

// Create a test class that exposes protected methods
class TestableArbitrageScanner extends ArbitrageScanner {
    public async testCheckArbitrageOpportunity(priceData: PriceData): Promise<void> {
        return this.checkArbitrageOpportunity(priceData);
    }

    public async testGetDexPrice(router: IUniswapV2Router02, tokenA: string, tokenB: string): Promise<number> {
        return this.getDexPrice(router, tokenA, tokenB);
    }
}

describe('ArbitrageScanner', () => {
    let scanner: TestableArbitrageScanner;
    let mockFlashLoanService: jest.Mocked<FlashLoanService>;
    let mockWsServer: WebSocketServer;

    beforeEach(() => {
        mockFlashLoanService = {
            executeArbitrage: jest.fn()
        } as unknown as jest.Mocked<FlashLoanService>;

        mockWsServer = {
            clients: new Set(),
            on: jest.fn()
        } as unknown as WebSocketServer;

        scanner = new TestableArbitrageScanner(mockFlashLoanService, mockWsServer);
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    it('should initialize with correct configuration', () => {
        expect(scanner).toBeDefined();
    });

    it('should detect price differences between DEXs', async () => {
        const mockPriceData: PriceData = {
            exchange: 'binance',
            tokenA: 'ETH',
            tokenB: 'USDT',
            price: 2000
        };

        // Mock the getDexPrice method
        const getDexPriceSpy = jest.spyOn(scanner, 'testGetDexPrice')
            .mockImplementation(async () => 2000);

        await scanner.testCheckArbitrageOpportunity(mockPriceData);

        // Verify that the price difference was detected and processed
        expect(getDexPriceSpy).toHaveBeenCalledTimes(2);
    });

    it('should not execute trades below profit threshold', async () => {
        const mockPriceData: PriceData = {
            exchange: 'binance',
            tokenA: 'ETH',
            tokenB: 'USDT',
            price: 2000
        };

        // Mock getDexPrice to return similar prices (no arbitrage opportunity)
        jest.spyOn(scanner, 'testGetDexPrice')
            .mockImplementation(async () => 2000);

        await scanner.testCheckArbitrageOpportunity(mockPriceData);

        // Verify that no trade was executed
        expect(mockFlashLoanService.executeArbitrage).not.toHaveBeenCalled();
    });
}); 