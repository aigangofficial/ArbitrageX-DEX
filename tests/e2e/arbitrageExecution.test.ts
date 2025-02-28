import { BigNumber } from '@ethersproject/bignumber';
import { JsonRpcProvider } from '@ethersproject/providers';
import { expect } from 'chai';
import { ethers } from 'ethers';
import { MonitoringService } from '../../backend/api/services/monitoringService';
import { ArbitrageScanner } from '../../backend/execution/arbitrageScanner';

describe('Arbitrage Execution E2E Tests', () => {
    let provider: JsonRpcProvider;
    let scanner: ArbitrageScanner;
    let monitoring: MonitoringService;

    const UNISWAP_ROUTER = '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D';
    const SUSHISWAP_ROUTER = '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F';
    const WETH = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2';
    const USDC = '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48';

    const scannerConfig = {
        minProfitThreshold: 1, // 1% minimum spread
        minNetProfit: 50, // 50 wei minimum profit
        gasLimit: 300000,
        scanInterval: 1000,
        maxGasPrice: 100, // 100 gwei
        gasMultiplier: 1.1
    };

    before(async () => {
        provider = new JsonRpcProvider('http://localhost:8545');
        scanner = new ArbitrageScanner(
            provider,
            UNISWAP_ROUTER,
            SUSHISWAP_ROUTER,
            scannerConfig,
            [{ tokenA: WETH, tokenB: USDC }]
        );
        monitoring = new MonitoringService();
    });

    it('should detect arbitrage opportunities with correct profit calculation', (done) => {
        let opportunityDetected = false;

        scanner.on('arbitrageOpportunity', (opportunity) => {
            try {
                expect(opportunity).to.have.property('pair');
                expect(opportunity).to.have.property('uniswapPrice');
                expect(opportunity).to.have.property('sushiswapPrice');
                expect(opportunity).to.have.property('spread');
                expect(opportunity).to.have.property('netProfit');
                expect(opportunity).to.have.property('gasPrice');
                expect(opportunity).to.have.property('estimatedGasCost');

                const spread = BigNumber.from(opportunity.spread);
                expect(spread.gte(scannerConfig.minProfitThreshold)).to.be.true;

                const netProfit = BigNumber.from(opportunity.netProfit);
                expect(netProfit.gte(scannerConfig.minNetProfit)).to.be.true;

                monitoring.recordArbitrageOpportunity(
                    netProfit,
                    BigNumber.from(opportunity.gasPrice)
                );

                const metrics = monitoring.getMetrics();
                expect(metrics.totalOpportunities).to.be.greaterThan(0);
                expect(metrics.systemHealth.isHealthy).to.be.true;

                opportunityDetected = true;
                scanner.stop();
                done();
            } catch (error) {
                done(error);
            }
        });

        scanner.start();

        // Timeout after 30 seconds if no opportunity is found
        setTimeout(() => {
            scanner.stop();
            if (!opportunityDetected) {
                done(new Error('No arbitrage opportunity detected within timeout'));
            }
        }, 30000);
    });

    it('should handle gas price spikes correctly', async () => {
        // Simulate high gas price
        const highGasPrice = BigNumber.from(ethers.parseUnits('150', 'gwei').toString());
        const mockProvider = new JsonRpcProvider('http://localhost:8545');

        // Override getGasPrice method
        mockProvider.getGasPrice = async () => Promise.resolve(highGasPrice);

        const testScanner = new ArbitrageScanner(
            mockProvider,
            UNISWAP_ROUTER,
            SUSHISWAP_ROUTER,
            scannerConfig,
            [{ tokenA: WETH, tokenB: USDC }]
        );

        let opportunityDetected = false;
        testScanner.on('arbitrageOpportunity', () => {
            opportunityDetected = true;
        });

        testScanner.start();
        await new Promise(resolve => setTimeout(resolve, 2000));
        testScanner.stop();

        expect(opportunityDetected).to.be.false;
    });

    it('should track system health metrics correctly', () => {
        const metrics = monitoring.getMetrics();

        expect(metrics).to.have.property('priceUpdateLatency');
        expect(metrics).to.have.property('totalOpportunities');
        expect(metrics).to.have.property('totalExecutedTrades');
        expect(metrics).to.have.property('systemHealth');
        expect(metrics.systemHealth.isHealthy).to.be.true;
    });
});
