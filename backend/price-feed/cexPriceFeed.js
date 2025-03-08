'use strict';
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, '__esModule', { value: true });
exports.CEXPriceFeed = void 0;
const events_1 = require('events');
const ws_1 = __importDefault(require('ws'));
const logger_1 = require('../utils/logger');
class CEXPriceFeed extends events_1.EventEmitter {
  constructor(symbols) {
    super();
    this.symbols = symbols;
    this.connections = new Map();
    this.reconnectAttempts = new Map();
    this.MAX_RECONNECT_ATTEMPTS = 5;
    this.RECONNECT_INTERVAL = 5000;
    this.exchanges = [
      {
        name: 'binance',
        wsUrl: 'wss://stream.binance.com:9443/ws',
        subscribeMsg: symbol =>
          JSON.stringify({
            method: 'SUBSCRIBE',
            params: [`${symbol.toLowerCase()}@trade`],
            id: Date.now(),
          }),
        parseMessage: msg => {
          try {
            const data = JSON.parse(msg);
            if (data.e === 'trade') {
              return {
                exchange: 'binance',
                symbol: data.s,
                price: data.p,
                timestamp: data.T,
                volume24h: data.q,
              };
            }
          } catch (error) {
            return null;
          }
          return null;
        },
      },
      {
        name: 'coinbase',
        wsUrl: 'wss://ws-feed.pro.coinbase.com',
        subscribeMsg: symbol =>
          JSON.stringify({
            type: 'subscribe',
            product_ids: [symbol],
            channels: ['ticker'],
          }),
        parseMessage: msg => {
          try {
            const data = JSON.parse(msg);
            if (data.type === 'ticker') {
              return {
                exchange: 'coinbase',
                symbol: data.product_id,
                price: data.price,
                timestamp: new Date(data.time).getTime(),
                volume24h: data.volume_24h,
              };
            }
          } catch (error) {
            return null;
          }
          return null;
        },
      },
    ];
    this.setupErrorHandling();
  }
  setupErrorHandling() {
    this.on('error', error => {
      logger_1.logger.error(`CEX Price Feed error: ${error}`);
    });
  }
  async start() {
    logger_1.logger.info('Starting CEX price feeds...');
    for (const exchange of this.exchanges) {
      for (const symbol of this.symbols) {
        await this.connectToExchange(exchange, symbol);
      }
    }
  }
  async connectToExchange(exchange, symbol) {
    const connectionId = `${exchange.name}-${symbol}`;
    try {
      const ws = new ws_1.default(exchange.wsUrl);
      ws.on('open', () => {
        logger_1.logger.info(`Connected to ${exchange.name} for ${symbol}`);
        ws.send(exchange.subscribeMsg(symbol));
        this.reconnectAttempts.set(connectionId, 0);
      });
      ws.on('message', data => {
        const update = exchange.parseMessage(data);
        if (update) {
          this.emit('priceUpdate', update);
        }
      });
      ws.on('error', error => {
        logger_1.logger.error(`WebSocket error for ${connectionId}: ${error.message}`);
        this.emit('error', error);
      });
      ws.on('close', () => {
        logger_1.logger.warn(`Connection closed for ${connectionId}`);
        this.handleReconnect(exchange, symbol);
      });
      this.connections.set(connectionId, ws);
    } catch (error) {
      logger_1.logger.error(`Failed to connect to ${connectionId}: ${error}`);
      this.handleReconnect(exchange, symbol);
    }
  }
  async handleReconnect(exchange, symbol) {
    const connectionId = `${exchange.name}-${symbol}`;
    const attempts = this.reconnectAttempts.get(connectionId) || 0;
    if (attempts < this.MAX_RECONNECT_ATTEMPTS) {
      logger_1.logger.info(
        `Attempting to reconnect to ${connectionId} (Attempt ${attempts + 1}/${this.MAX_RECONNECT_ATTEMPTS})`
      );
      this.reconnectAttempts.set(connectionId, attempts + 1);
      setTimeout(() => {
        this.connectToExchange(exchange, symbol);
      }, this.RECONNECT_INTERVAL);
    } else {
      logger_1.logger.error(`Max reconnection attempts reached for ${connectionId}`);
      this.emit(
        'error',
        new Error(
          `Failed to connect to ${connectionId} after ${this.MAX_RECONNECT_ATTEMPTS} attempts`
        )
      );
    }
  }
  stop() {
    logger_1.logger.info('Stopping CEX price feeds...');
    for (const [connectionId, ws] of this.connections) {
      try {
        ws.close();
        logger_1.logger.info(`Closed connection for ${connectionId}`);
      } catch (error) {
        logger_1.logger.error(`Error closing connection for ${connectionId}: ${error}`);
      }
    }
    this.connections.clear();
    this.reconnectAttempts.clear();
  }
  getConnectedExchanges() {
    return Array.from(this.connections.keys());
  }
}
exports.CEXPriceFeed = CEXPriceFeed;
exports.default = CEXPriceFeed;
//# sourceMappingURL=cexPriceFeed.js.map
