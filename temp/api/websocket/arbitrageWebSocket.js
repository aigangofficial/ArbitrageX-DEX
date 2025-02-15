"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArbitrageWebSocketService = void 0;
const ws_1 = __importDefault(require("ws"));
const models_1 = require("../../database/models");
class ArbitrageWebSocketService {
    wss;
    constructor(server) {
        this.wss = new ws_1.default.Server({ server });
        this.initialize();
    }
    initialize() {
        this.wss.on('connection', async (ws) => {
            console.log('New WebSocket client connected');
            // Wait for a small delay to ensure the connection is fully established
            await new Promise(resolve => setTimeout(resolve, 100));
            // Send last 10 trades immediately on connection
            try {
                const recentTrades = await models_1.ArbitrageTrade.find().sort({ timestamp: -1 }).limit(10);
                // Ensure client is still connected before sending
                if (ws.readyState === ws_1.default.OPEN) {
                    await this.sendMessage(ws, {
                        type: 'recentTrades',
                        data: recentTrades,
                    });
                }
            }
            catch (error) {
                console.error('Error sending recent trades:', error);
                if (ws.readyState === ws_1.default.OPEN) {
                    ws.close(1011, 'Internal Server Error');
                }
            }
            ws.on('message', async (message) => {
                try {
                    console.log('WebSocket received message:', message);
                    const data = JSON.parse(message);
                    switch (data.type) {
                        case 'subscribe':
                            // Handle subscription requests
                            break;
                        case 'getHistory':
                            console.log('Processing getHistory request with limit:', data.limit);
                            await this.sendTradeHistory(ws, data.limit || 50);
                            break;
                        default:
                            console.log('Unknown message type:', data.type);
                            if (ws.readyState === ws_1.default.OPEN) {
                                await this.sendMessage(ws, {
                                    type: 'error',
                                    data: { message: 'Unknown message type' },
                                });
                            }
                    }
                }
                catch (error) {
                    console.error('Error processing WebSocket message:', error);
                    if (ws.readyState === ws_1.default.OPEN) {
                        await this.sendMessage(ws, {
                            type: 'error',
                            data: { message: 'Invalid message format' },
                        });
                    }
                }
            });
            ws.on('error', error => {
                console.error('WebSocket error:', error);
                if (ws.readyState === ws_1.default.OPEN) {
                    ws.close(1011, 'Internal Server Error');
                }
            });
            ws.on('close', () => {
                console.log('Client disconnected');
            });
        });
    }
    async sendMessage(ws, message) {
        return new Promise((resolve, reject) => {
            if (ws.readyState !== ws_1.default.OPEN) {
                console.log('WebSocket not open, readyState:', ws.readyState);
                reject(new Error('WebSocket is not open'));
                return;
            }
            console.log('Sending WebSocket message:', JSON.stringify(message));
            ws.send(JSON.stringify(message), error => {
                if (error) {
                    console.error('Error sending WebSocket message:', error);
                    reject(error);
                }
                else {
                    console.log('WebSocket message sent successfully');
                    resolve();
                }
            });
        });
    }
    async sendTradeHistory(ws, limit) {
        try {
            const trades = await models_1.ArbitrageTrade.find()
                .sort({ timestamp: -1 })
                .limit(Math.min(limit, 100));
            // Ensure client is still connected before sending
            if (ws.readyState === ws_1.default.OPEN) {
                await this.sendMessage(ws, {
                    type: 'tradeHistory',
                    data: trades,
                });
            }
        }
        catch (error) {
            console.error('Error sending trade history:', error);
            if (ws.readyState === ws_1.default.OPEN) {
                await this.sendMessage(ws, {
                    type: 'error',
                    data: { message: 'Failed to fetch trade history' },
                });
            }
        }
    }
    async broadcast(message) {
        const promises = Array.from(this.wss.clients)
            .filter(client => client.readyState === ws_1.default.OPEN)
            .map(client => this.sendMessage(client, message));
        await Promise.all(promises);
    }
    getServer() {
        return this.wss;
    }
}
exports.ArbitrageWebSocketService = ArbitrageWebSocketService;
