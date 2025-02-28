import { EventEmitter } from 'events';
export interface PriceUpdate {
    exchange: string;
    symbol: string;
    price: string;
    timestamp: number;
    volume24h?: string;
}
export declare class CEXPriceFeed extends EventEmitter {
    private readonly symbols;
    private connections;
    private reconnectAttempts;
    private readonly MAX_RECONNECT_ATTEMPTS;
    private readonly RECONNECT_INTERVAL;
    private readonly exchanges;
    constructor(symbols: string[]);
    private setupErrorHandling;
    start(): Promise<void>;
    private connectToExchange;
    private handleReconnect;
    stop(): void;
    getConnectedExchanges(): string[];
}
export default CEXPriceFeed;
