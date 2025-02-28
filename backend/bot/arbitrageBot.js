const ethers = require('ethers');
const WebSocket = require('ws');
const axios = require('axios');
const { getContractAddresses } = require('../config/addresses');
const ArbitrageExecutor = require('../../artifacts/contracts/ArbitrageExecutor.sol/ArbitrageExecutor.json');
const IERC20 = require('../../artifacts/contracts/interfaces/IERC20.sol/IERC20.json');
const IUniswapV2Router02 = require('../../artifacts/contracts/interfaces/IUniswapV2Router02.sol/IUniswapV2Router02.json');
const { spawn } = require('child_process');
const path = require('path');
require('dotenv').config();

class PriceMonitor {
    constructor() {
        this.priceFeeds = {
            uniswap: new WebSocket('wss://api.uniswap.org/v2'),
            sushiswap: new WebSocket('wss://api.sushi.com/v2')
        };
        this.prices = {};
        this.setupWebSockets();
    }

    setupWebSockets() {
        Object.entries(this.priceFeeds).forEach(([dex, ws]) => {
            ws.on('message', (data) => {
                this.handlePriceUpdate(dex, JSON.parse(data));
            });

            ws.on('error', (error) => {
                console.error(`WebSocket error for ${dex}:`, error);
                this.reconnect(dex);
            });
        });
    }

    handlePriceUpdate(dex, data) {
        // Update price data
        if (!this.prices[dex]) this.prices[dex] = {};
        this.prices[dex] = {
            ...this.prices[dex],
            ...data
        };
    }

    reconnect(dex) {
        setTimeout(() => {
            this.priceFeeds[dex] = new WebSocket(this.priceFeeds[dex].url);
            this.setupWebSockets();
        }, 5000);
    }

    async getPrices(tokenPair) {
        return {
            uniswap: this.prices.uniswap?.[tokenPair] || await this.fetchPrice('uniswap', tokenPair),
            sushiswap: this.prices.sushiswap?.[tokenPair] || await this.fetchPrice('sushiswap', tokenPair)
        };
    }

    async fetchPrice(dex, tokenPair) {
        // Fallback REST API call if WebSocket fails
        try {
            const response = await axios.get(`${this.getApiUrl(dex)}/prices/${tokenPair}`);
            return response.data;
        } catch (error) {
            console.error(`Error fetching ${dex} price:`, error);
            return null;
        }
    }

    getApiUrl(dex) {
        return {
            uniswap: 'https://api.uniswap.org/v2',
            sushiswap: 'https://api.sushi.com/v2'
        }[dex];
    }
}

class ArbitrageBot {
    constructor() {
        this.provider = new ethers.JsonRpcProvider(process.env.RPC_URL);
        this.wallet = new ethers.Wallet(process.env.PRIVATE_KEY, this.provider);
        this.addresses = getContractAddresses();
        this.priceMonitor = new PriceMonitor();
        this.aiProcess = null;
        this.lastPrediction = null;
        this.performanceMetrics = {
            totalTrades: 0,
            successfulTrades: 0,
            totalProfit: ethers.parseEther("0"),
            averageGasUsed: 0
        };

        this.setupAI();
    }

    async initialize() {
        console.log('🤖 Initializing Arbitrage Bot...');

        try {
            // Setup and verify contracts
            await this.setupContracts();
            console.log('✅ Contract connections verified');

            // Initialize price monitoring
            await this.initializePriceMonitoring();
            console.log('✅ Price monitoring initialized');

            // Load historical data for AI
            await this.loadHistoricalData();
            console.log('✅ Historical data loaded');

            console.log('✨ Bot initialization complete!\n');
        } catch (error) {
            console.error('❌ Initialization failed:', error);
            process.exit(1);
        }
    }

    async setupContracts() {
        // Initialize contract instances
        this.executor = new ethers.Contract(
            this.addresses.arbitrageExecutor,
            ArbitrageExecutor.abi,
            this.wallet
        );

        this.uniswapRouter = new ethers.Contract(
            this.addresses.uniswapRouter,
            IUniswapV2Router02.abi,
            this.wallet
        );

        this.sushiswapRouter = new ethers.Contract(
            this.addresses.sushiswapRouter,
            IUniswapV2Router02.abi,
            this.wallet
        );

        // Initialize token contracts
        this.tokens = {
            USDC: new ethers.Contract(this.addresses.usdc, IERC20.abi, this.wallet),
            WETH: new ethers.Contract(this.addresses.weth, IERC20.abi, this.wallet)
        };

        // Verify all contract connections and permissions
        await Promise.all([
            this.executor.minProfitBps(),
            this.uniswapRouter.factory(),
            this.sushiswapRouter.factory()
        ]);

        // Verify token approvals
        for (const [symbol, token] of Object.entries(this.tokens)) {
            const allowance = await token.allowance(
                this.wallet.address,
                this.addresses.arbitrageExecutor
            );
            if (allowance.lt(ethers.MaxUint256.div(2))) {
                console.log(`Approving ${symbol}...`);
                await token.approve(this.addresses.arbitrageExecutor, ethers.MaxUint256);
            }
        }
    }

    setupAI() {
        // Start AI strategy optimizer process
        this.aiProcess = spawn('python', [
            path.join(__dirname, '../ai/strategy_optimizer.py'),
            '--mode=production'
        ]);

        this.aiProcess.stdout.on('data', (data) => {
            try {
                const prediction = JSON.parse(data);
                this.lastPrediction = prediction;
            } catch (error) {
                console.error('Error parsing AI prediction:', error);
            }
        });

        this.aiProcess.stderr.on('data', (data) => {
            console.error('AI Error:', data.toString());
        });
    }

    async initializePriceMonitoring() {
        // Initialize price feeds
        await this.priceMonitor.getPrices('WETH-USDC');
    }

    async loadHistoricalData() {
        // Load and preprocess historical trading data for AI
        // Implementation for historical data loading
    }

    monitorArbitrageOpportunities() {
        console.log('👀 Monitoring for arbitrage opportunities...\n');

        // Monitor price differences between DEXes
        const checkOpportunities = async () => {
            try {
                await this.checkAllPairs();
            } catch (error) {
                console.error('Error in monitoring loop:', error);
            }
        };

        // Initial check
        checkOpportunities();

        // Set up interval for continuous monitoring
        setInterval(checkOpportunities, 1000); // Check every second
    }

    async checkAllPairs() {
        for (const tokenA of Object.values(this.tokens)) {
            for (const tokenB of Object.values(this.tokens)) {
                if (tokenA.address === tokenB.address) continue;

                // Check various trade amounts
                const decimals = await tokenA.decimals();
                const amounts = [1000, 5000, 10000].map(amount =>
                    ethers.parseUnits(amount.toString(), decimals)
                );

                for (const amount of amounts) {
                    await this.checkArbitrageOpportunity(tokenA, tokenB, amount);
                }
            }
        }
    }

    async checkArbitrageOpportunity(tokenA, tokenB, amount) {
        // Get current market data
        const marketData = await this.getMarketData(tokenA, tokenB, amount);

        // Get AI prediction
        if (this.lastPrediction) {
            const { recommended, confidence, risk_score } = this.lastPrediction;

            if (recommended && confidence > 0.8 && risk_score < 0.2) {
                await this.executeArbitrage(tokenA, tokenB, amount, marketData);
            }
        }
    }

    async getMarketData(tokenA, tokenB, amount) {
        const [decimalsA, decimalsB] = await Promise.all([
            tokenA.decimals(),
            tokenB.decimals()
        ]);

        const prices = await this.priceMonitor.getPrices(
            `${await tokenA.symbol()}-${await tokenB.symbol()}`
        );

        const gasPrice = await this.provider.getFeeData();

        return {
            tokenA: tokenA.address,
            tokenB: tokenB.address,
            amount: amount.toString(),
            uniswapPrice: prices.uniswap,
            sushiswapPrice: prices.sushiswap,
            gasPrice: gasPrice.gasPrice.toString(),
            decimalsA,
            decimalsB,
            timestamp: Date.now()
        };
    }

    async executeArbitrage(tokenA, tokenB, amount, marketData) {
        try {
            console.log(`\n🚀 Executing arbitrage trade:`);
            console.log(`Amount: ${ethers.formatUnits(amount, await tokenA.decimals())} ${await tokenA.symbol()}`);
            console.log(`Path: ${await tokenA.symbol()} → ${await tokenB.symbol()}`);

            const tx = await this.executor.executeArbitrage(
                tokenA.address,
                tokenB.address,
                amount,
                [tokenA.address, tokenB.address],
                marketData.sushiswapPrice > marketData.uniswapPrice
            );

            console.log(`\n⏳ Waiting for transaction: ${tx.hash}`);
            const receipt = await tx.wait();

            if (receipt.status === 1) {
                console.log('✅ Arbitrage executed successfully!\n');
                await this.updatePerformanceMetrics(receipt, true);
            } else {
                console.log('❌ Arbitrage execution failed\n');
                await this.updatePerformanceMetrics(receipt, false);
            }
        } catch (error) {
            console.error('Error executing arbitrage:', error);
            await this.updatePerformanceMetrics(null, false);
        }
    }

    async updatePerformanceMetrics(receipt, success) {
        this.performanceMetrics.totalTrades++;
        if (success) {
            this.performanceMetrics.successfulTrades++;
            if (receipt) {
                this.performanceMetrics.averageGasUsed = (
                    (this.performanceMetrics.averageGasUsed * (this.performanceMetrics.successfulTrades - 1) +
                        receipt.gasUsed) /
                    this.performanceMetrics.successfulTrades
                );
            }
        }

        // Log metrics every 100 trades
        if (this.performanceMetrics.totalTrades % 100 === 0) {
            console.log('\n📊 Performance Metrics:');
            console.log(`Total Trades: ${this.performanceMetrics.totalTrades}`);
            console.log(`Success Rate: ${(this.performanceMetrics.successfulTrades / this.performanceMetrics.totalTrades * 100).toFixed(2)}%`);
            console.log(`Average Gas Used: ${Math.round(this.performanceMetrics.averageGasUsed)}`);
            console.log(`Total Profit: ${ethers.formatEther(this.performanceMetrics.totalProfit)} ETH\n`);
        }
    }

    cleanup() {
        if (this.aiProcess) {
            this.aiProcess.kill();
        }
        Object.values(this.priceMonitor.priceFeeds).forEach(ws => ws.close());
    }
}

// Start the bot
async function main() {
    const bot = new ArbitrageBot();
    await bot.initialize();
    await bot.monitorArbitrageOpportunities();

    // Handle cleanup on exit
    process.on('SIGINT', () => {
        console.log('\n🛑 Shutting down bot...');
        bot.cleanup();
        process.exit();
    });
}

main().catch(console.error);
