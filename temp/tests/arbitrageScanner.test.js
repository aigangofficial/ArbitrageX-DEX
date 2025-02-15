"use strict";
/// <reference types="jest" />
Object.defineProperty(exports, "__esModule", { value: true });
const ethers_1 = require("ethers");
const arbitrageScanner_1 = require("../execution/arbitrageScanner");
// Mock environment variables
process.env.ETH_RPC_URL = 'http://localhost:8545';
process.env.UNISWAP_ROUTER_ADDRESS = '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D';
process.env.SUSHISWAP_ROUTER_ADDRESS = '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F';
jest.mock('ethers', () => {
    const originalModule = jest.requireActual('ethers');
    return {
        ...originalModule,
        Contract: jest.fn().mockImplementation(() => ({
            getAmountsOut: jest.fn().mockResolvedValue([BigInt(1000000), BigInt(2000000)]),
            interface: {
                encodeFunctionData: jest.fn(),
            },
        })),
        JsonRpcProvider: jest.fn().mockImplementation(() => ({
            getNetwork: jest.fn().mockResolvedValue({ chainId: 1 }),
            getGasPrice: jest.fn().mockResolvedValue(BigInt(20000000000)),
        })),
        parseEther: jest.fn().mockImplementation(value => BigInt(value) * BigInt(10 ** 18)),
        formatEther: jest.fn().mockImplementation(value => Number(value) / 10 ** 18),
    };
});
jest.mock('ws');
// Create a test class that exposes protected methods
class TestableArbitrageScanner extends arbitrageScanner_1.ArbitrageScanner {
    async testGetPrices(tokenA, tokenB) {
        return this.getPrices(tokenA, tokenB);
    }
    async testIsProfitable(prices) {
        return this.isProfitable(prices);
    }
}
describe('ArbitrageScanner', () => {
    let scanner;
    let mockProvider;
    let mockWsServer;
    beforeEach(() => {
        mockProvider = new ethers_1.ethers.JsonRpcProvider();
        mockWsServer = {
            clients: new Set(),
            on: jest.fn(),
        };
        scanner = new TestableArbitrageScanner(mockProvider, mockWsServer, '0xFlashLoan', '0xUniswap', '0xSushiswap');
    });
    afterEach(() => {
        jest.clearAllMocks();
    });
    it('should initialize with correct configuration', () => {
        expect(scanner).toBeDefined();
        expect(scanner.getProvider()).toBe(mockProvider);
    });
    it('should detect price differences between DEXs', async () => {
        const tokenA = '0xTokenA';
        const tokenB = '0xTokenB';
        const prices = await scanner.testGetPrices(tokenA, tokenB);
        expect(prices).toBeDefined();
        expect(prices.tokenA).toBe(tokenA);
        expect(prices.tokenB).toBe(tokenB);
        expect(prices.uniswapPrice).toBeDefined();
        expect(prices.sushiswapPrice).toBeDefined();
    });
    it('should determine profitability correctly', async () => {
        const mockPrices = {
            tokenA: '0xTokenA',
            tokenB: '0xTokenB',
            uniswapPrice: {
                price: BigInt(2000000),
                liquidity: BigInt(1000000),
            },
            sushiswapPrice: {
                price: BigInt(2100000),
                liquidity: BigInt(1000000),
            },
        };
        const isProfitable = await scanner.testIsProfitable(mockPrices);
        expect(isProfitable).toBe(true);
    });
    it('should not consider small price differences profitable', async () => {
        const mockPrices = {
            tokenA: '0xTokenA',
            tokenB: '0xTokenB',
            uniswapPrice: {
                price: BigInt(2000000),
                liquidity: BigInt(1000000),
            },
            sushiswapPrice: {
                price: BigInt(2000100),
                liquidity: BigInt(1000000),
            },
        };
        const isProfitable = await scanner.testIsProfitable(mockPrices);
        expect(isProfitable).toBe(false);
    });
});
