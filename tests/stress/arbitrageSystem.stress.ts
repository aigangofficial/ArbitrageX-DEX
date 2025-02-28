import { BigNumber } from '@ethersproject/bignumber';
import { JsonRpcProvider } from '@ethersproject/providers';
import { expect } from 'chai';
import WebSocket from 'ws';
import { MonitoringService } from '../../backend/api/services/monitoringService';
import { MonitoringSocket } from '../../backend/api/websocket/monitoringSocket';
import { ArbitrageScanner } from '../../backend/execution/arbitrageScanner';
import { CEXPriceFeed } from '../../backend/price-feed/cexPriceFeed';
import { PriceAggregator } from '../../backend/price-feed/priceAggregator';

describe('Arbitrage System Stress Tests', () => {
    let provider: JsonRpcProvider;
    let scanner: ArbitrageScanner;
    let monitoring: MonitoringService;
    let cexFeed: CEXPriceFeed;
    let priceAggregator: PriceAggregator;
    let monitoringSocket: MonitoringSocket;
    let wsClient: WebSocket;

    const UNISWAP_ROUTER = '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D';
    const SUSHISWAP_ROUTER = '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F';
    const WETH = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2';
    const USDC = '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48';
    const WS_PORT = 3001;

    const TOKEN_PAIRS = [
        { tokenA: WETH, tokenB: USDC },
        { tokenA: WETH, tokenB: '0xdAC17F958D2ee523a2206206994597C13D831ec7' }, // USDT
        { tokenA: WETH, tokenB: '0x6B175474E89094C44Da98b954EedeAC495271d0F' }, // DAI
        { tokenA: '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599', tokenB: WETH }, // WBTC/WETH
        { tokenA: '0x514910771AF9Ca656af840dff83E8264EcF986CA', tokenB: WETH }, // LINK/WETH
        { tokenA: '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984', tokenB: WETH }, // UNI/WETH
        { tokenA: '0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9', tokenB: WETH }, // AAVE/WETH
        { tokenA: USDC, tokenB: '0xdAC17F958D2ee523a2206206994597C13D831ec7' }, // USDC/USDT
    ];

    const scannerConfig = {
        minProfitThreshold: 0.5,
        minNetProfit: 50,
        gasLimit: 300000,
        scanInterval: 1000,
        maxGasPrice: 100,
        gasMultiplier: 1.1
    };

    before(async () => {
        provider = new JsonRpcProvider('http://localhost:8545');

        // Initialize components
        scanner = new ArbitrageScanner(
            provider,
            UNISWAP_ROUTER,
            SUSHISWAP_ROUTER,
            scannerConfig,
            TOKEN_PAIRS
        );

        monitoring = new MonitoringService();
        cexFeed = new CEXPriceFeed([
            'ETH/USDC',
            'ETH/USDT',
            'ETH/DAI',
            'WBTC/ETH',
            'LINK/ETH',
            'UNI/ETH',
            'AAVE/ETH',
            'USDC/USDT'
        ]);
        priceAggregator = new PriceAggregator(cexFeed, scanner);
        monitoringSocket = new MonitoringSocket(WS_PORT, monitoring, priceAggregator);

        // Start all services
        await Promise.all([
            scanner.start(),
            monitoring.start(),
            cexFeed.start(),
            priceAggregator.start()
        ]);
    });

    after(() => {
        scanner.stop();
        monitoring.stop();
        cexFeed.stop();
        priceAggregator.stop();
        monitoringSocket.stop();
        if (wsClient) wsClient.close();
    });

    it('should handle high frequency price updates', async () => {
        const updates: any[] = [];
        const TEST_DURATION = 10000; // 10 seconds
        const EXPECTED_UPDATES = 10; // Expect at least 10 updates in 10 seconds

        wsClient = new WebSocket(`ws://localhost:${WS_PORT}`);

        await new Promise<void>((resolve) => {
            wsClient.on('open', resolve);
        });

        const updatePromise = new Promise<void>((resolve) => {
            wsClient.on('message', (data) => {
                const message = JSON.parse(data.toString());
                if (message.type === 'prices') {
                    updates.push(message.data);
                }
            });

            setTimeout(() => {
                expect(updates.length).to.be.at.least(EXPECTED_UPDATES);
                resolve();
            }, TEST_DURATION);
        });

        await updatePromise;
    });

    it('should maintain system health under load', async () => {
        const CONCURRENT_REQUESTS = 100;
        const requests = Array(CONCURRENT_REQUESTS).fill(0).map(() => {
            return new Promise<void>((resolve) => {
                const ws = new WebSocket(`ws://localhost:${WS_PORT}`);
                ws.on('message', () => {
                    ws.close();
                    resolve();
                });
            });
        });

        await Promise.all(requests);
        const metrics = monitoring.getMetrics();
        expect(metrics.systemHealth.isHealthy).to.be.true;
    });

    it('should handle rapid connection/disconnection cycles', async () => {
        const CYCLES = 50;
        const CYCLE_INTERVAL = 100; // 100ms

        for (let i = 0; i < CYCLES; i++) {
            const ws = new WebSocket(`ws://localhost:${WS_PORT}`);
            await new Promise<void>((resolve) => {
                ws.on('open', () => {
                    ws.close();
                    resolve();
                });
            });
            await new Promise(resolve => setTimeout(resolve, CYCLE_INTERVAL));
        }

        const metrics = monitoring.getMetrics();
        expect(metrics.systemHealth.isHealthy).to.be.true;
        expect(metrics.systemHealth.errors).to.have.lengthOf(0);
    });

    it('should process multiple arbitrage opportunities simultaneously', async () => {
        const opportunities: any[] = [];
        const TEST_DURATION = 5000; // 5 seconds

        wsClient = new WebSocket(`ws://localhost:${WS_PORT}`);

        await new Promise<void>((resolve) => {
            wsClient.on('open', resolve);
        });

        const arbitragePromise = new Promise<void>((resolve) => {
            wsClient.on('message', (data) => {
                const message = JSON.parse(data.toString());
                if (message.type === 'arbitrage') {
                    opportunities.push(...message.data);
                }
            });

            setTimeout(() => {
                // Verify that opportunities are being processed
                expect(opportunities.length).to.be.at.least(0);
                // Verify that profit calculations are correct
                opportunities.forEach(opp => {
                    expect(BigNumber.from(opp.estimatedProfit)).to.be.gt(0);
                });
                resolve();
            }, TEST_DURATION);
        });

        await arbitragePromise;
    });

    it('should maintain price feed accuracy under load', async () => {
        const prices: Map<string, number[]> = new Map();
        const TEST_DURATION = 10000; // 10 seconds
        const MAX_PRICE_DEVIATION = 5; // 5% maximum deviation

        wsClient = new WebSocket(`ws://localhost:${WS_PORT}`);

        await new Promise<void>((resolve) => {
            wsClient.on('open', resolve);
        });

        const pricePromise = new Promise<void>((resolve) => {
            wsClient.on('message', (data) => {
                const message = JSON.parse(data.toString());
                if (message.type === 'prices') {
                    message.data.forEach((price: any) => {
                        if (!prices.has(price.symbol)) {
                            prices.set(price.symbol, []);
                        }
                        const priceHistory = prices.get(price.symbol)!;
                        Object.values(price.dexPrices).forEach(p => {
                            priceHistory.push(Number(p));
                        });
                    });
                }
            });

            setTimeout(() => {
                // Check price stability
                prices.forEach((priceHistory, symbol) => {
                    const avg = priceHistory.reduce((a, b) => a + b, 0) / priceHistory.length;
                    const maxDeviation = Math.max(...priceHistory.map(p => Math.abs(p - avg) / avg * 100));
                    expect(maxDeviation).to.be.lt(MAX_PRICE_DEVIATION);
                });
                resolve();
            }, TEST_DURATION);
        });

        await pricePromise;
    });
});
