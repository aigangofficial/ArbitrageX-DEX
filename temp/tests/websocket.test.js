"use strict";
/// <reference types="jest" />
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const http_1 = require("http");
const ws_1 = __importDefault(require("ws"));
const arbitrageWebSocket_1 = require("../api/websocket/arbitrageWebSocket");
jest.mock('../database/models', () => ({
    ArbitrageTrade: {
        find: jest.fn().mockReturnValue({
            sort: jest.fn().mockReturnValue({
                limit: jest.fn().mockResolvedValue([
                    { id: '1', tokenA: 'ETH', tokenB: 'USDT' },
                    { id: '2', tokenA: 'BTC', tokenB: 'USDT' },
                ]),
            }),
        }),
    },
}));
describe('ArbitrageWebSocketService', () => {
    let server;
    let wsService;
    let wsClient;
    const mockTrades = [
        { id: '1', tokenA: 'ETH', tokenB: 'USDT' },
        { id: '2', tokenA: 'BTC', tokenB: 'USDT' },
    ];
    beforeAll(async () => {
        server = (0, http_1.createServer)();
        wsService = new arbitrageWebSocket_1.ArbitrageWebSocketService(server);
        await new Promise(resolve => server.listen(0, () => resolve()));
    });
    afterAll(async () => {
        await new Promise(resolve => {
            wsService.getServer().close(() => {
                server.close(() => resolve());
            });
        });
    });
    beforeEach(() => {
        jest.clearAllMocks();
    });
    afterEach(async () => {
        if (wsClient) {
            await new Promise(resolve => {
                if (wsClient.readyState === ws_1.default.OPEN) {
                    wsClient.on('close', resolve);
                    wsClient.close();
                }
                else {
                    resolve();
                }
            });
        }
    });
    const createWebSocketConnection = async (port) => {
        const ws = new ws_1.default(`ws://localhost:${port}`);
        await new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                ws.removeAllListeners();
                ws.close();
                reject(new Error('WebSocket connection timeout'));
            }, 10000);
            const errorHandler = (error) => {
                clearTimeout(timeout);
                ws.removeAllListeners();
                reject(error);
            };
            ws.once('error', errorHandler);
            ws.once('open', () => {
                clearTimeout(timeout);
                ws.removeAllListeners();
                setTimeout(resolve, 100);
            });
        });
        return ws;
    };
    const waitForMessage = async (ws) => {
        return new Promise(resolve => {
            ws.once('message', data => {
                resolve(JSON.parse(data.toString()));
            });
        });
    };
    it('should connect to WebSocket server', async () => {
        const port = server.address().port;
        wsClient = await createWebSocketConnection(port);
        expect(wsClient.readyState).toBe(ws_1.default.OPEN);
    });
    it('should send recent trades on connection', async () => {
        const port = server.address().port;
        wsClient = await createWebSocketConnection(port);
        const message = await waitForMessage(wsClient);
        expect(message).toEqual({
            type: 'recentTrades',
            data: mockTrades,
        });
    });
    it('should handle trade history requests', async () => {
        const port = server.address().port;
        wsClient = await createWebSocketConnection(port);
        console.log('Waiting for initial trades message');
        await waitForMessage(wsClient);
        console.log('Sending trade history request');
        const sendPromise = new Promise((resolve, reject) => {
            const message = JSON.stringify({
                type: 'getHistory',
                limit: 50,
            });
            console.log('Sending message:', message);
            wsClient.send(message, (err) => {
                if (err) {
                    console.error('Error sending message:', err);
                    reject(err);
                }
                else {
                    console.log('Message sent successfully');
                    setTimeout(resolve, 100);
                }
            });
        });
        console.log('Waiting for response');
        const [, message] = await Promise.all([sendPromise, waitForMessage(wsClient)]);
        console.log('Response received:', message);
        expect(message).toEqual({
            type: 'tradeHistory',
            data: mockTrades,
        });
    });
    it('should broadcast messages to all connected clients', async () => {
        const port = server.address().port;
        const clients = [];
        const expectedClients = 3;
        const broadcastData = { type: 'test', data: 'message' };
        try {
            for (let i = 0; i < expectedClients; i++) {
                const client = await createWebSocketConnection(port);
                clients.push(client);
                await waitForMessage(client);
            }
            await wsService.broadcast(broadcastData);
            const messagePromises = clients.map(client => waitForMessage(client));
            const messages = await Promise.all(messagePromises);
            messages.forEach(message => {
                expect(message).toEqual(broadcastData);
            });
        }
        finally {
            await Promise.all(clients.map(client => new Promise(resolve => {
                if (client.readyState === ws_1.default.OPEN) {
                    client.on('close', resolve);
                    client.close();
                }
                else {
                    resolve();
                }
            })));
        }
    });
});
