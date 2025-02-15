"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArbitrageWebSocket = void 0;
const ws_1 = __importDefault(require("ws"));
const ArbitrageTrade_1 = require("../../database/models/ArbitrageTrade");
class ArbitrageWebSocket {
    wss;
    clients;
    constructor(wss) {
        this.wss = wss;
        this.clients = new Set();
        this.initialize();
    }
    initialize() {
        this.wss.on('connection', (ws) => {
            console.log('New client connected');
            this.clients.add(ws);
            ws.on('close', () => {
                console.log('Client disconnected');
                this.clients.delete(ws);
            });
            // Send last 5 trades as initial data
            this.sendLastTrades(ws);
        });
    }
    async sendLastTrades(ws) {
        try {
            const lastTrades = await ArbitrageTrade_1.ArbitrageTrade.find().sort({ createdAt: -1 }).limit(5).lean();
            ws.send(JSON.stringify({
                type: 'history',
                data: lastTrades,
                timestamp: Date.now(),
            }));
        }
        catch (error) {
            console.error('Error fetching last trades:', error);
        }
    }
    broadcastOpportunity(tokenA, tokenB, expectedProfit, route) {
        const update = {
            type: 'opportunity',
            data: {
                tokenA,
                tokenB,
                expectedProfit: expectedProfit.toString(),
                route,
            },
            timestamp: Date.now(),
        };
        this.broadcast(update);
    }
    broadcastExecution(trade) {
        const update = {
            type: 'execution',
            data: trade,
            timestamp: Date.now(),
        };
        this.broadcast(update);
    }
    broadcastCompletion(trade) {
        const update = {
            type: 'completion',
            data: trade,
            timestamp: Date.now(),
        };
        this.broadcast(update);
    }
    broadcastError(error) {
        const update = {
            type: 'error',
            data: {
                message: error.message || 'Unknown error occurred',
                code: error.code,
                details: error.details,
            },
            timestamp: Date.now(),
        };
        this.broadcast(update);
    }
    broadcast(data) {
        const message = JSON.stringify(data);
        this.clients.forEach(client => {
            if (client.readyState === ws_1.default.OPEN) {
                client.send(message);
            }
        });
    }
}
exports.ArbitrageWebSocket = ArbitrageWebSocket;
