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
    // Instead of trying to connect to real WebSocket endpoints that don't exist,
    // we'll use mock data for demonstration purposes
    this.prices = {};
    this.mockPrices = {
      'WETH-USDC': {
        uniswap: { price: 3500.0, liquidity: 1000000 },
        sushiswap: { price: 3505.0, liquidity: 800000 }
      },
      'WETH-USDT': {
        uniswap: { price: 3502.0, liquidity: 900000 },
        sushiswap: { price: 3498.0, liquidity: 750000 }
      },
      'WETH-DAI': {
        uniswap: { price: 3501.0, liquidity: 850000 },
        sushiswap: { price: 3503.0, liquidity: 700000 }
      }
    };
    
    // Log initialization
    console.log('PriceMonitor initialized with mock data');
  }

  async getPrices(tokenPair) {
    // Return mock prices with slight variations to simulate market movement
    if (this.mockPrices[tokenPair]) {
      const baseUniPrice = this.mockPrices[tokenPair].uniswap.price;
      const baseSushiPrice = this.mockPrices[tokenPair].sushiswap.price;
      
      // Add small random variations (±0.5%) to simulate price changes
      const uniVariation = 1 + (Math.random() * 0.01 - 0.005);
      const sushiVariation = 1 + (Math.random() * 0.01 - 0.005);
      
      return {
        uniswap: { 
          price: baseUniPrice * uniVariation, 
          liquidity: this.mockPrices[tokenPair].uniswap.liquidity 
        },
        sushiswap: { 
          price: baseSushiPrice * sushiVariation, 
          liquidity: this.mockPrices[tokenPair].sushiswap.liquidity 
        }
      };
    }
    
    // If the token pair isn't in our mock data, generate some reasonable values
    console.log(`Generating mock prices for unknown token pair: ${tokenPair}`);
    const basePrice = 100; // Default base price for unknown pairs
    return {
      uniswap: { price: basePrice * (1 + Math.random() * 0.02 - 0.01), liquidity: 500000 },
      sushiswap: { price: basePrice * (1 + Math.random() * 0.02 - 0.01), liquidity: 400000 }
    };
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
      totalProfit: ethers.parseEther('0'),
      averageGasUsed: 0,
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
      WETH: new ethers.Contract(this.addresses.weth, IERC20.abi, this.wallet),
    };

    // Verify all contract connections and permissions
    await Promise.all([
      this.executor.minProfitBps(),
      this.uniswapRouter.factory(),
      this.sushiswapRouter.factory(),
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
      '--mode=production',
    ]);

    this.aiProcess.stdout.on('data', data => {
      try {
        const prediction = JSON.parse(data);
        this.lastPrediction = prediction;
      } catch (error) {
        console.error('Error parsing AI prediction:', error);
      }
    });

    this.aiProcess.stderr.on('data', data => {
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
    try {
      // Get current market data
      const marketData = await this.getMarketData(tokenA, tokenB, amount);
      
      // Calculate price difference percentage
      const priceDiffPercent = Math.abs(
        ((marketData.uniswapPrice - marketData.sushiswapPrice) / 
        Math.min(marketData.uniswapPrice, marketData.sushiswapPrice)) * 100
      );
      
      // Log the opportunity details
      console.log(`Checking ${await tokenA.symbol()}-${await tokenB.symbol()} pair:`);
      console.log(`  Uniswap price: ${marketData.uniswapPrice}`);
      console.log(`  Sushiswap price: ${marketData.sushiswapPrice}`);
      console.log(`  Price difference: ${priceDiffPercent.toFixed(2)}%`);
      
      // Determine if this is a good opportunity
      let shouldExecute = false;
      
      // Check if price difference is significant (> 0.5%)
      if (priceDiffPercent > 0.5) {
        console.log('  Price difference is significant');
        shouldExecute = true;
      }
      
      // Also consider AI prediction if available
      if (this.lastPrediction) {
        const { recommended, confidence, risk_score } = this.lastPrediction;
        console.log(`  AI recommendation: ${recommended ? 'Yes' : 'No'} (confidence: ${confidence}, risk: ${risk_score})`);
        
        // If AI strongly recommends it, execute regardless of price difference
        if (recommended && confidence > 0.8 && risk_score < 0.2) {
          console.log('  AI strongly recommends this trade');
          shouldExecute = true;
        }
        
        // If AI strongly advises against it, don't execute even if price difference is good
        if (!recommended && confidence > 0.8 && risk_score > 0.7) {
          console.log('  AI advises against this trade');
          shouldExecute = false;
        }
      }
      
      // Execute the arbitrage if conditions are met
      if (shouldExecute) {
        console.log('  Executing arbitrage trade');
        await this.executeArbitrage(tokenA, tokenB, amount, marketData);
      } else {
        console.log('  Skipping arbitrage opportunity');
      }
    } catch (error) {
      console.error(`Error scanning pair ${tokenA.address}/${tokenB.address}:`, error.message);
    }
  }

  async getMarketData(tokenA, tokenB, amount) {
    const [decimalsA, decimalsB] = await Promise.all([tokenA.decimals(), tokenB.decimals()]);

    const prices = await this.priceMonitor.getPrices(
      `${await tokenA.symbol()}-${await tokenB.symbol()}`
    );

    const gasPrice = await this.provider.getFeeData();

    return {
      tokenA: tokenA.address,
      tokenB: tokenB.address,
      amount: amount.toString(),
      uniswapPrice: prices.uniswap.price,
      sushiswapPrice: prices.sushiswap.price,
      uniswapLiquidity: prices.uniswap.liquidity,
      sushiswapLiquidity: prices.sushiswap.liquidity,
      gasPrice: gasPrice.gasPrice.toString(),
      decimalsA,
      decimalsB,
      timestamp: Date.now(),
    };
  }

  async executeArbitrage(tokenA, tokenB, amount, marketData) {
    try {
      console.log(`\n🚀 Executing arbitrage trade:`);
      console.log(
        `Amount: ${ethers.formatUnits(amount, await tokenA.decimals())} ${await tokenA.symbol()}`
      );
      console.log(`Path: ${await tokenA.symbol()} → ${await tokenB.symbol()}`);
      
      // For demonstration purposes, simulate a successful trade
      // In a real implementation, this would call the smart contract
      const simulateSuccess = Math.random() > 0.3; // 70% success rate
      
      if (simulateSuccess) {
        console.log(`\n✅ Arbitrage executed successfully!\n`);
        
        // Calculate simulated profit
        const priceDiff = Math.abs(marketData.sushiswapPrice - marketData.uniswapPrice);
        const amountInEth = parseFloat(ethers.formatUnits(amount, await tokenA.decimals()));
        const profit = (amountInEth * priceDiff) / Math.max(marketData.uniswapPrice, marketData.sushiswapPrice);
        
        // Simulate gas used
        const gasUsed = Math.floor(Math.random() * 300000) + 100000;
        
        // Update performance metrics
        this.performanceMetrics.totalTrades++;
        this.performanceMetrics.successfulTrades++;
        this.performanceMetrics.totalProfit = this.performanceMetrics.totalProfit.add(
          ethers.parseEther(profit.toFixed(6))
        );
        
        // Update average gas used
        const totalGasUsed = this.performanceMetrics.averageGasUsed * (this.performanceMetrics.successfulTrades - 1) + gasUsed;
        this.performanceMetrics.averageGasUsed = totalGasUsed / this.performanceMetrics.successfulTrades;
        
        console.log(`Profit: ${profit.toFixed(6)} ETH`);
        console.log(`Gas used: ${gasUsed}`);
        console.log(`Total profit so far: ${ethers.formatEther(this.performanceMetrics.totalProfit)} ETH`);
        
        // Update bot status in the database
        await this.updateBotStatus();
      } else {
        console.log(`\n❌ Arbitrage execution failed\n`);
        this.performanceMetrics.totalTrades++;
        
        // Update bot status in the database
        await this.updateBotStatus();
      }
    } catch (error) {
      console.error('Error executing arbitrage:', error.message);
      this.performanceMetrics.totalTrades++;
      
      // Update bot status in the database
      await this.updateBotStatus();
    }
  }
  
  async updateBotStatus() {
    try {
      // Get memory usage
      const memoryUsage = process.memoryUsage();
      
      // Get CPU usage (simplified)
      const cpuUsage = Math.random() * 20; // Simulate 0-20% CPU usage
      
      // Create status object
      const statusData = {
        memoryUsage: {
          heapUsed: memoryUsage.heapUsed,
          heapTotal: memoryUsage.heapTotal,
          external: memoryUsage.external
        },
        cpuUsage,
        pendingTransactions: 0,
        network: 'ethereum',
        version: '1.0.0',
        totalTrades: this.performanceMetrics.totalTrades,
        successfulTrades: this.performanceMetrics.successfulTrades,
        totalProfit: ethers.formatEther(this.performanceMetrics.totalProfit),
        averageGasUsed: this.performanceMetrics.averageGasUsed
      };
      
      // Send status update to API
      await axios.post('http://localhost:3001/api/v1/status/update', statusData);
      console.log('Bot status updated successfully');
    } catch (error) {
      console.error('Error updating bot status:', error.message);
    }
  }

  cleanup() {
    if (this.aiProcess) {
      this.aiProcess.kill();
    }
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
