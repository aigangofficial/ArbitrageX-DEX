/// <reference types="jest" />

import { Server } from 'http';
import WebSocket from 'ws';
import { ArbitrageWebSocketService } from '../api/websocket/arbitrageWebSocket';
import { ArbitrageTrade } from '../database/models';
import { createServer } from 'http';

jest.mock('../database/models');

interface MockTrade {
    id: string;
    tokenA: string;
    tokenB: string;
}

describe('ArbitrageWebSocketService', () => {
    let server: Server;
    let wsService: ArbitrageWebSocketService;
    let wsClient: WebSocket;
    const mockTrades: MockTrade[] = [
        { id: '1', tokenA: 'ETH', tokenB: 'USDT' },
        { id: '2', tokenA: 'BTC', tokenB: 'USDT' }
    ];

    beforeAll(() => {
        server = createServer();
        wsService = new ArbitrageWebSocketService(server);
        server.listen(0);
    });

    afterAll(async () => {
        await new Promise<void>((resolve) => server.close(() => resolve()));
    });

    beforeEach(() => {
        jest.clearAllMocks();
    });

    afterEach(async () => {
        if (wsClient) {
            await new Promise<void>((resolve) => {
                wsClient.on('close', () => resolve());
                wsClient.close();
            });
        }
    });

    const createWebSocketConnection = async (port: number): Promise<WebSocket> => {
        const ws = new WebSocket(`ws://localhost:${port}`);
        await new Promise<void>((resolve) => ws.on('open', () => resolve()));
        return ws;
    };

    const waitForMessage = async (ws: WebSocket): Promise<unknown> => {
        const message = await new Promise((resolve) => {
            ws.once('message', (data: string) => resolve(JSON.parse(data)));
        });
        return message;
    };

    it('should connect to WebSocket server', async () => {
        const port = (server.address() as { port: number }).port;
        wsClient = await createWebSocketConnection(port);
        expect(wsClient.readyState).toBe(WebSocket.OPEN);
    });

    it('should send recent trades on connection', async () => {
        (ArbitrageTrade.find as jest.Mock).mockReturnValue({
            sort: jest.fn().mockReturnValue({
                limit: jest.fn().mockResolvedValue(mockTrades)
            })
        });

        const port = (server.address() as { port: number }).port;
        wsClient = await createWebSocketConnection(port);
        
        const message = await waitForMessage(wsClient);
        expect(message).toEqual({
            type: 'recentTrades',
            data: mockTrades
        });
    });

    it('should handle trade history requests', async () => {
        (ArbitrageTrade.find as jest.Mock).mockReturnValue({
            sort: jest.fn().mockReturnValue({
                limit: jest.fn().mockResolvedValue(mockTrades)
            })
        });

        const port = (server.address() as { port: number }).port;
        wsClient = await createWebSocketConnection(port);
        
        // Skip the initial trades message
        await waitForMessage(wsClient);

        wsClient.send(JSON.stringify({
            type: 'getHistory',
            limit: 50
        }));

        const message = await waitForMessage(wsClient);
        expect(message).toEqual({
            type: 'tradeHistory',
            data: mockTrades
        });
    });

    it('should broadcast messages to all connected clients', async () => {
        const port = (server.address() as { port: number }).port;
        const clients: WebSocket[] = [];
        const expectedClients = 3;
        const broadcastData = { type: 'test', data: 'message' };

        // Create multiple clients
        for (let i = 0; i < expectedClients; i++) {
            const client = await createWebSocketConnection(port);
            clients.push(client);
            // Skip the initial trades message
            await waitForMessage(client);
        }

        // Broadcast message
        wsService.broadcast(broadcastData);

        // Wait for all clients to receive the message
        const messages = await Promise.all(
            clients.map(client => waitForMessage(client))
        );

        // Verify all messages
        messages.forEach(message => {
            expect(message).toEqual(broadcastData);
        });

        // Cleanup
        await Promise.all(
            clients.map(client => new Promise<void>(resolve => {
                client.on('close', () => resolve());
                client.close();
            }))
        );
    });
}); 