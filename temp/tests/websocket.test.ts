/// <reference types="jest" />

import { createServer, Server } from 'http';
import WebSocket from 'ws';
import { ArbitrageWebSocketService } from '../api/websocket/arbitrageWebSocket';

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
    { id: '2', tokenA: 'BTC', tokenB: 'USDT' },
  ];

  beforeAll(async () => {
    server = createServer();
    wsService = new ArbitrageWebSocketService(server);
    await new Promise<void>(resolve => server.listen(0, () => resolve()));
  });

  afterAll(async () => {
    await new Promise<void>(resolve => {
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
      await new Promise<void>(resolve => {
        if (wsClient.readyState === WebSocket.OPEN) {
          wsClient.on('close', resolve);
          wsClient.close();
        } else {
          resolve();
        }
      });
    }
  });

  const createWebSocketConnection = async (port: number): Promise<WebSocket> => {
    const ws = new WebSocket(`ws://localhost:${port}`);

    await new Promise<void>((resolve, reject) => {
      const timeout = setTimeout(() => {
        ws.removeAllListeners();
        ws.close();
        reject(new Error('WebSocket connection timeout'));
      }, 10000);

      const errorHandler = (error: Error) => {
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

  const waitForMessage = async (ws: WebSocket): Promise<any> => {
    return new Promise(resolve => {
      ws.once('message', data => {
        resolve(JSON.parse(data.toString()));
      });
    });
  };

  it('should connect to WebSocket server', async () => {
    const port = (server.address() as { port: number }).port;
    wsClient = await createWebSocketConnection(port);
    expect(wsClient.readyState).toBe(WebSocket.OPEN);
  });

  it('should send recent trades on connection', async () => {
    const port = (server.address() as { port: number }).port;
    wsClient = await createWebSocketConnection(port);

    const message = await waitForMessage(wsClient);
    expect(message).toEqual({
      type: 'recentTrades',
      data: mockTrades,
    });
  });

  it('should handle trade history requests', async () => {
    const port = (server.address() as { port: number }).port;
    wsClient = await createWebSocketConnection(port);

    console.log('Waiting for initial trades message');
    await waitForMessage(wsClient);

    console.log('Sending trade history request');
    const sendPromise = new Promise<void>((resolve, reject) => {
      const message = JSON.stringify({
        type: 'getHistory',
        limit: 50,
      });
      console.log('Sending message:', message);
      wsClient.send(message, (err?: Error) => {
        if (err) {
          console.error('Error sending message:', err);
          reject(err);
        } else {
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
    const port = (server.address() as { port: number }).port;
    const clients: WebSocket[] = [];
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
    } finally {
      await Promise.all(
        clients.map(
          client =>
            new Promise<void>(resolve => {
              if (client.readyState === WebSocket.OPEN) {
                client.on('close', resolve);
                client.close();
              } else {
                resolve();
              }
            })
        )
      );
    }
  });
});
