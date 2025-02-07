import { ethers } from 'ethers';
import WebSocket from 'ws';
import { ArbitrageTrade } from '../database/models';
import { IUniswapV2Router02, FlashLoanService } from '../types/contracts';

export interface PriceData {
    exchange: string;
    tokenA: string;
    tokenB: string;
    price: number;
}

export interface ArbitrageOpportunity {
    tokenA: string;
    tokenB: string;
    exchangeA: string;
    exchangeB: string;
    expectedProfit: string;
    amountIn: string;
    _id?: string;
}

export class ArbitrageScanner {
    private providers: { [key: string]: ethers.Provider } = {};
    private dexRouters: { [key: string]: IUniswapV2Router02 } = {};
    private wsClients: { [key: string]: WebSocket } = {};
    private minProfitThreshold: number;

    constructor(
        private readonly flashLoanService: FlashLoanService,
        private readonly websocketServer: WebSocket.Server
    ) {
        this.minProfitThreshold = 0.5; // 0.5% minimum profit
        this.initializeConnections();
    }

    private async initializeConnections() {
        const ethRpcUrl = process.env.ETH_RPC_URL;
        const uniswapAddress = process.env.UNISWAP_ROUTER_ADDRESS;
        const sushiswapAddress = process.env.SUSHISWAP_ROUTER_ADDRESS;

        if (!ethRpcUrl) {
            throw new Error('ETH_RPC_URL environment variable is not set');
        }
        if (!uniswapAddress) {
            throw new Error('UNISWAP_ROUTER_ADDRESS environment variable is not set');
        }
        if (!sushiswapAddress) {
            throw new Error('SUSHISWAP_ROUTER_ADDRESS environment variable is not set');
        }

        // Initialize providers and contracts
        this.providers = {
            ethereum: new ethers.JsonRpcProvider(ethRpcUrl)
        };

        // Initialize DEX router contracts with ethers Contract
        this.dexRouters = {
            uniswap: new ethers.Contract(
                uniswapAddress,
                ['function getAmountsOut(uint amountIn, address[] memory path) external view returns (uint[] memory amounts)'],
                this.providers.ethereum
            ) as unknown as IUniswapV2Router02,
            sushiswap: new ethers.Contract(
                sushiswapAddress,
                ['function getAmountsOut(uint amountIn, address[] memory path) external view returns (uint[] memory amounts)'],
                this.providers.ethereum
            ) as unknown as IUniswapV2Router02
        };

        // Initialize WebSocket connections for CEX price feeds
        this.wsClients = {
            binance: new WebSocket('wss://stream.binance.com:9443/ws'),
            coinbase: new WebSocket('wss://ws-feed.pro.coinbase.com')
        };

        this.setupWebSocketListeners();
    }

    private setupWebSocketListeners() {
        // Setup Binance WebSocket
        this.wsClients.binance.on('open', () => {
            this.wsClients.binance.send(JSON.stringify({
                method: 'SUBSCRIBE',
                params: ['ethusdt@trade', 'btcusdt@trade'],
                id: 1
            }));
        });

        // Setup Coinbase WebSocket
        this.wsClients.coinbase.on('open', () => {
            this.wsClients.coinbase.send(JSON.stringify({
                type: 'subscribe',
                product_ids: ['ETH-USD', 'BTC-USD'],
                channels: ['ticker']
            }));
        });

        // Handle incoming price data
        Object.entries(this.wsClients).forEach(([exchange, client]) => {
            client.on('message', (data: string) => {
                const priceData = this.parsePriceData(exchange, data);
                if (priceData) {
                    this.checkArbitrageOpportunity(priceData);
                }
            });
        });
    }

    // Exposed for testing
    protected async checkArbitrageOpportunity(priceData: PriceData) {
        try {
            // Get prices from different DEXs
            const prices = await Promise.all([
                this.getDexPrice(this.dexRouters.uniswap, priceData.tokenA, priceData.tokenB),
                this.getDexPrice(this.dexRouters.sushiswap, priceData.tokenA, priceData.tokenB)
            ]);

            const [uniswapPrice, sushiswapPrice] = prices;
            const priceDifference = Math.abs(uniswapPrice - sushiswapPrice) / Math.min(uniswapPrice, sushiswapPrice) * 100;

            if (priceDifference > this.minProfitThreshold) {
                const opportunity: ArbitrageOpportunity = {
                    tokenA: priceData.tokenA,
                    tokenB: priceData.tokenB,
                    exchangeA: uniswapPrice < sushiswapPrice ? 'Uniswap' : 'SushiSwap',
                    exchangeB: uniswapPrice < sushiswapPrice ? 'SushiSwap' : 'Uniswap',
                    expectedProfit: priceDifference.toString(),
                    amountIn: ethers.parseEther('1').toString() // 1 ETH as test amount
                };

                // Save to MongoDB
                const trade = new ArbitrageTrade(opportunity);
                await trade.save();

                // Broadcast to WebSocket clients
                this.websocketServer.clients.forEach(client => {
                    if (client.readyState === WebSocket.OPEN) {
                        client.send(JSON.stringify({
                            type: 'arbitrageOpportunity',
                            data: opportunity
                        }));
                    }
                });

                // Execute trade if auto-execution is enabled
                if (process.env.AUTO_EXECUTE === 'true') {
                    await this.executeArbitrage(trade);
                }
            }
        } catch (error) {
            console.error('Error checking arbitrage opportunity:', error);
        }
    }

    // Exposed for testing
    protected async getDexPrice(router: IUniswapV2Router02, tokenA: string, tokenB: string): Promise<number> {
        const amountIn = ethers.parseEther('1');
        const [, amountOut] = await router.getAmountsOut(amountIn, [tokenA, tokenB]);
        return parseFloat(ethers.formatEther(amountOut));
    }

    public async executeArbitrage(opportunity: ArbitrageOpportunity) {
        try {
            const tx = await this.flashLoanService.executeArbitrage(
                opportunity.tokenA,
                opportunity.tokenB,
                opportunity.exchangeA,
                opportunity.exchangeB,
                ethers.parseEther(opportunity.amountIn)
            );

            const receipt = await tx.wait();
            
            // Update trade status in MongoDB
            if (opportunity._id) {
                await ArbitrageTrade.findByIdAndUpdate(opportunity._id, {
                    status: 'executed',
                    txHash: receipt.hash,
                    gasUsed: receipt.gasUsed?.toString()
                });

                // Broadcast execution result
                this.websocketServer.clients.forEach(client => {
                    if (client.readyState === WebSocket.OPEN) {
                        client.send(JSON.stringify({
                            type: 'tradeExecuted',
                            data: {
                                id: opportunity._id,
                                txHash: receipt.hash,
                                status: 'executed'
                            }
                        }));
                    }
                });
            }
        } catch (error: unknown) {
            console.error('Error executing arbitrage:', error);
            
            // Update trade status on failure
            if (opportunity._id) {
                await ArbitrageTrade.findByIdAndUpdate(opportunity._id, {
                    status: 'failed',
                    errorMessage: error instanceof Error ? error.message : 'Unknown error'
                });

                // Broadcast failure
                this.websocketServer.clients.forEach(client => {
                    if (client.readyState === WebSocket.OPEN) {
                        client.send(JSON.stringify({
                            type: 'tradeFailed',
                            data: {
                                id: opportunity._id,
                                error: error instanceof Error ? error.message : 'Unknown error'
                            }
                        }));
                    }
                });
            }
        }
    }

    private parsePriceData(exchange: string, data: string): PriceData | null {
        try {
            const parsed = JSON.parse(data);
            
            switch (exchange) {
                case 'binance':
                    return {
                        exchange: 'binance',
                        tokenA: parsed.s.replace('USDT', ''),
                        tokenB: 'USDT',
                        price: parseFloat(parsed.p)
                    };
                case 'coinbase':
                    return {
                        exchange: 'coinbase',
                        tokenA: parsed.product_id.split('-')[0],
                        tokenB: parsed.product_id.split('-')[1],
                        price: parseFloat(parsed.price)
                    };
                default:
                    return null;
            }
        } catch (error) {
            console.error('Error parsing price data:', error);
            return null;
        }
    }
} 