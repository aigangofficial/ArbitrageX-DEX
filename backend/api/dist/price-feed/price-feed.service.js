"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (this && this.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.PriceFeedService = void 0;
const common_1 = require("@nestjs/common");
const ws_1 = __importDefault(require("ws"));
const winston_1 = require("winston");
let PriceFeedService = class PriceFeedService {
    constructor(logger) {
        this.logger = logger;
        this.ws = null;
        this.endpoints = {
            binance: 'wss://stream.binance.com:9443/ws',
            uniswap: 'wss://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3'
        };
    }
    async start() {
        try {
            await this.connectToBinance();
            await this.connectToUniswap();
            this.logger.info('Price feed service started successfully');
        }
        catch (error) {
            this.logger.error('Failed to start price feed service', { error });
            throw error;
        }
    }
    async stop() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.logger.info('Price feed service stopped');
    }
    async connectToBinance() {
        return new Promise((resolve, reject) => {
            this.ws = new ws_1.default(this.endpoints.binance);
            this.ws.on('open', () => {
                this.logger.info('Connected to Binance WebSocket');
                this.subscribeToPairs();
                resolve();
            });
            this.ws.on('error', (error) => {
                this.logger.error('Binance WebSocket error', { error });
                reject(error);
            });
            this.ws.on('message', (data) => {
                this.handlePriceUpdate(data);
            });
        });
    }
    async connectToUniswap() {
    }
    subscribeToPairs() {
        if (!this.ws)
            return;
        const pairs = [
            'btcusdt@trade',
            'ethusdt@trade',
            'bnbusdt@trade'
        ];
        const subscribeMsg = {
            method: 'SUBSCRIBE',
            params: pairs,
            id: 1
        };
        this.ws.send(JSON.stringify(subscribeMsg));
    }
    handlePriceUpdate(data) {
        try {
            const update = JSON.parse(data.toString());
            if (update.e === 'trade') {
                this.logger.info(`Price update for ${update.s}: ${update.p}`);
            }
        }
        catch (error) {
            this.logger.error('Failed to parse price update', { error });
        }
    }
};
exports.PriceFeedService = PriceFeedService;
exports.PriceFeedService = PriceFeedService = __decorate([
    (0, common_1.Injectable)(),
    __metadata("design:paramtypes", [winston_1.Logger])
], PriceFeedService);
//# sourceMappingURL=price-feed.service.js.map