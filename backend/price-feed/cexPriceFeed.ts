import { EventEmitter } from 'events';
import WebSocket from 'ws';
import { logger } from '../utils/logger';

export interface PriceUpdate {
    exchange: string;
    symbol: string;
    price: string;
    timestamp: number;
    volume24h?: string;
}

interface ExchangeConfig {
    name: string;
    wsUrl: string;
    subscribeMsg: (symbol: string) => any;
    parseMessage: (msg: any) => PriceUpdate | null;
}

export class CEXPriceFeed extends EventEmitter {
    private connections: Map<string, WebSocket> = new Map();
    private reconnectAttempts: Map<string, number> = new Map();
    private readonly MAX_RECONNECT_ATTEMPTS = 5;
    private readonly RECONNECT_INTERVAL = 5000;

    private readonly exchanges: ExchangeConfig[] = [
        {
            name: 'binance',
            wsUrl: 'wss://stream.binance.com:9443/ws',
            subscribeMsg: (symbol) => JSON.stringify({
                method: 'SUBSCRIBE',
                params: [`${symbol.toLowerCase()}@trade`],
                id: Date.now()
            }),
            parseMessage: (msg) => {
                try {
                    const data = JSON.parse(msg);
                    if (data.e === 'trade') {
                        return {
                            exchange: 'binance',
                            symbol: data.s,
                            price: data.p,
                            timestamp: data.T,
                            volume24h: data.q
                        };
                    }
                } catch (error) {
                    return null;
                }
                return null;
            }
        },
        {
            name: 'coinbase',
            wsUrl: 'wss://ws-feed.pro.coinbase.com',
            subscribeMsg: (symbol) => JSON.stringify({
                type: 'subscribe',
                product_ids: [symbol],
                channels: ['ticker']
            }),
            parseMessage: (msg) => {
                try {
                    const data = JSON.parse(msg);
                    if (data.type === 'ticker') {
                        return {
                            exchange: 'coinbase',
                            symbol: data.product_id,
                            price: data.price,
                            timestamp: new Date(data.time).getTime(),
                            volume24h: data.volume_24h
                        };
                    }
                } catch (error) {
                    return null;
                }
                return null;
            }
        }
    ];

    constructor(private readonly symbols: string[]) {
        super();
        this.setupErrorHandling();
    }

    private setupErrorHandling(): void {
        this.on('error', (error) => {
            logger.error(`CEX Price Feed error: ${error}`);
        });
    }

    async start(): Promise<void> {
        logger.info('Starting CEX price feeds...');

        for (const exchange of this.exchanges) {
            for (const symbol of this.symbols) {
                await this.connectToExchange(exchange, symbol);
            }
        }
    }

    private async connectToExchange(exchange: ExchangeConfig, symbol: string): Promise<void> {
        const connectionId = `${exchange.name}-${symbol}`;

        try {
            const ws = new WebSocket(exchange.wsUrl);

            ws.on('open', () => {
                logger.info(`Connected to ${exchange.name} for ${symbol}`);
                ws.send(exchange.subscribeMsg(symbol));
                this.reconnectAttempts.set(connectionId, 0);
            });

            ws.on('message', (data: WebSocket.Data) => {
                const update = exchange.parseMessage(data);
                if (update) {
                    this.emit('priceUpdate', update);
                }
            });

            ws.on('error', (error) => {
                logger.error(`WebSocket error for ${connectionId}: ${error.message}`);
                this.emit('error', error);
            });

            ws.on('close', () => {
                logger.warn(`Connection closed for ${connectionId}`);
                this.handleReconnect(exchange, symbol);
            });

            this.connections.set(connectionId, ws);
        } catch (error) {
            logger.error(`Failed to connect to ${connectionId}: ${error}`);
            this.handleReconnect(exchange, symbol);
        }
    }

    private async handleReconnect(exchange: ExchangeConfig, symbol: string): Promise<void> {
        const connectionId = `${exchange.name}-${symbol}`;
        const attempts = this.reconnectAttempts.get(connectionId) || 0;

        if (attempts < this.MAX_RECONNECT_ATTEMPTS) {
            logger.info(`Attempting to reconnect to ${connectionId} (Attempt ${attempts + 1}/${this.MAX_RECONNECT_ATTEMPTS})`);
            this.reconnectAttempts.set(connectionId, attempts + 1);

            setTimeout(() => {
                this.connectToExchange(exchange, symbol);
            }, this.RECONNECT_INTERVAL);
        } else {
            logger.error(`Max reconnection attempts reached for ${connectionId}`);
            this.emit('error', new Error(`Failed to connect to ${connectionId} after ${this.MAX_RECONNECT_ATTEMPTS} attempts`));
        }
    }

    stop(): void {
        logger.info('Stopping CEX price feeds...');

        for (const [connectionId, ws] of this.connections) {
            try {
                ws.close();
                logger.info(`Closed connection for ${connectionId}`);
            } catch (error) {
                logger.error(`Error closing connection for ${connectionId}: ${error}`);
            }
        }

        this.connections.clear();
        this.reconnectAttempts.clear();
    }

    getConnectedExchanges(): string[] {
        return Array.from(this.connections.keys());
    }
}

export default CEXPriceFeed;
