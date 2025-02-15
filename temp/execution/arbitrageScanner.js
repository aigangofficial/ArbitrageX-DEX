"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArbitrageScanner = void 0;
const ethers_1 = require("ethers");
const ws_1 = require("ws");
const ArbitrageTrade_1 = require("../database/models/ArbitrageTrade");
class ArbitrageScanner {
    provider;
    wsServer;
    uniswapRouter;
    sushiswapRouter;
    flashLoanAddress;
    arbitrageExecutor;
    minProfitThreshold;
    wethAddress;
    isScanning = false;
    constructor(provider, wsServer, flashLoanAddress, uniswapRouterAddress, sushiswapRouterAddress, wethAddress) {
        if (!ethers_1.ethers.isAddress(flashLoanAddress))
            throw new Error('Invalid FlashLoan address');
        if (!ethers_1.ethers.isAddress(uniswapRouterAddress))
            throw new Error('Invalid Uniswap address');
        if (!ethers_1.ethers.isAddress(sushiswapRouterAddress))
            throw new Error('Invalid Sushiswap address');
        this.provider = provider;
        this.wsServer = wsServer;
        this.flashLoanAddress = flashLoanAddress;
        this.minProfitThreshold = ethers_1.ethers.parseEther('0.01'); // 0.01 ETH minimum profit
        this.wethAddress = wethAddress;
        this.uniswapRouter = new ethers_1.ethers.Contract(uniswapRouterAddress || ethers_1.ethers.ZeroAddress, [
            'function getAmountsOut(uint amountIn, address[] memory path) view returns (uint[] memory amounts)',
        ], provider);
        this.sushiswapRouter = new ethers_1.ethers.Contract(sushiswapRouterAddress || ethers_1.ethers.ZeroAddress, [
            'function getAmountsOut(uint amountIn, address[] memory path) view returns (uint[] memory amounts)',
        ], provider);
        this.arbitrageExecutor = new ethers_1.ethers.Contract(this.flashLoanAddress, [
            'function executeArbitrage(address tokenA, address tokenB, uint256 amount) external returns (uint256)',
        ], this.provider);
    }
    async startScanning() {
        if (this.isScanning)
            return;
        this.isScanning = true;
        while (this.isScanning) {
            try {
                const trades = await ArbitrageTrade_1.ArbitrageTrade.find({ status: 'pending' })
                    .sort({ createdAt: -1 })
                    .limit(10)
                    .lean()
                    .exec();
                for (const trade of trades) {
                    if (!trade.route || !trade._id)
                        continue;
                    await this.processArbitrageOpportunity({
                        tokenA: trade.tokenA,
                        tokenB: trade.tokenB,
                        amountIn: BigInt(trade.amountIn),
                        expectedProfit: BigInt(trade.expectedProfit),
                        route: trade.route,
                        _id: trade._id.toString(),
                    });
                }
            }
            catch (error) {
                console.error('Error in scanning loop:', error);
            }
            await new Promise(resolve => setTimeout(resolve, 1000)); // 1 second delay
        }
    }
    stopScanning() {
        this.isScanning = false;
    }
    async processArbitrageOpportunity(opportunity) {
        try {
            const prices = await this.getPrices(opportunity.tokenA, opportunity.tokenB);
            if (!this.isProfitable(prices)) {
                return;
            }
            // Broadcast opportunity to connected clients
            this.wsServer.clients.forEach((client) => {
                if (client.readyState === ws_1.WebSocket.OPEN) {
                    client.send(JSON.stringify({
                        type: 'opportunity',
                        data: {
                            tokenA: opportunity.tokenA,
                            tokenB: opportunity.tokenB,
                            expectedProfit: opportunity.expectedProfit.toString(),
                            route: opportunity.route,
                        },
                    }));
                }
            });
            await this.executeArbitrage(opportunity);
        }
        catch (error) {
            console.error('Error processing arbitrage opportunity:', error);
            this.broadcastError(error);
        }
    }
    async executeArbitrage(opportunity) {
        const trade = await ArbitrageTrade_1.ArbitrageTrade.findById(opportunity._id).exec();
        if (!trade) {
            throw new Error('Trade not found');
        }
        try {
            trade.status = 'executing';
            await trade.save();
            this.broadcastExecution(trade);
            const tx = await this.arbitrageExecutor.executeArbitrage(opportunity.tokenA, opportunity.tokenB, opportunity.amountIn);
            const receipt = await tx.wait();
            if (receipt) {
                trade.txHash = receipt.hash;
                trade.gasUsed = receipt.gasUsed.toString();
                trade.gasPrice = receipt.gasPrice?.toString() || '0';
                trade.status = 'completed';
                await trade.save();
                this.broadcastCompletion(trade);
            }
        }
        catch (error) {
            trade.status = 'failed';
            trade.errorMessage = error instanceof Error ? error.message : 'Unknown error';
            await trade.save();
            this.broadcastError(error);
            throw error;
        }
    }
    async getPrices(tokenA, tokenB) {
        const [uniswapPrice, sushiswapPrice] = await Promise.all([
            this.getUniswapPrice(tokenA, tokenB),
            this.getSushiswapPrice(tokenA, tokenB),
        ]);
        return {
            tokenA,
            tokenB,
            uniswapPrice,
            sushiswapPrice,
        };
    }
    async getUniswapPrice(tokenA, tokenB) {
        const amountIn = ethers_1.ethers.parseEther('1');
        const amounts = await this.uniswapRouter.getAmountsOut(amountIn, [tokenA, tokenB]);
        return {
            price: amounts[1],
            liquidity: amounts[0],
        };
    }
    async getSushiswapPrice(tokenA, tokenB) {
        const amountIn = ethers_1.ethers.parseEther('1');
        const amounts = await this.sushiswapRouter.getAmountsOut(amountIn, [tokenA, tokenB]);
        return {
            price: amounts[1],
            liquidity: amounts[0],
        };
    }
    isProfitable(prices) {
        const uniswapPrice = prices.uniswapPrice.price;
        const sushiswapPrice = prices.sushiswapPrice.price;
        const priceDiff = uniswapPrice > sushiswapPrice ? uniswapPrice - sushiswapPrice : sushiswapPrice - uniswapPrice;
        return priceDiff >= this.minProfitThreshold;
    }
    broadcastExecution(trade) {
        this.wsServer.clients.forEach((client) => {
            if (client.readyState === ws_1.WebSocket.OPEN) {
                client.send(JSON.stringify({
                    type: 'execution',
                    data: trade,
                }));
            }
        });
    }
    broadcastCompletion(trade) {
        this.wsServer.clients.forEach((client) => {
            if (client.readyState === ws_1.WebSocket.OPEN) {
                client.send(JSON.stringify({
                    type: 'completion',
                    data: trade,
                }));
            }
        });
    }
    broadcastError(error) {
        this.wsServer.clients.forEach((client) => {
            if (client.readyState === ws_1.WebSocket.OPEN) {
                client.send(JSON.stringify({
                    type: 'error',
                    error: error.message,
                }));
            }
        });
    }
    getProvider() {
        return this.provider;
    }
}
exports.ArbitrageScanner = ArbitrageScanner;
