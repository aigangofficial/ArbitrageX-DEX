import WebSocket from 'ws';
import { Server } from 'http';
import { ArbitrageTrade } from '../../database/models';

interface BroadcastMessage {
  type: string;
  data: unknown;
}

export class ArbitrageWebSocketService {
  private wss: WebSocket.Server;

  constructor(server: Server) {
    this.wss = new WebSocket.Server({ server });
    this.initialize();
  }

  private initialize() {
    this.wss.on('connection', async (ws: WebSocket) => {
      console.log('New WebSocket client connected');

      // Wait for a small delay to ensure the connection is fully established
      await new Promise(resolve => setTimeout(resolve, 100));

      // Send last 10 trades immediately on connection
      try {
        const recentTrades = await ArbitrageTrade.find().sort({ timestamp: -1 }).limit(10);

        // Ensure client is still connected before sending
        if (ws.readyState === WebSocket.OPEN) {
          await this.sendMessage(ws, {
            type: 'recentTrades',
            data: recentTrades,
          });
        }
      } catch (error) {
        console.error('Error sending recent trades:', error);
        if (ws.readyState === WebSocket.OPEN) {
          ws.close(1011, 'Internal Server Error');
        }
      }

      ws.on('message', async (message: string) => {
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
              if (ws.readyState === WebSocket.OPEN) {
                await this.sendMessage(ws, {
                  type: 'error',
                  data: { message: 'Unknown message type' },
                });
              }
          }
        } catch (error) {
          console.error('Error processing WebSocket message:', error);
          if (ws.readyState === WebSocket.OPEN) {
            await this.sendMessage(ws, {
              type: 'error',
              data: { message: 'Invalid message format' },
            });
          }
        }
      });

      ws.on('error', error => {
        console.error('WebSocket error:', error);
        if (ws.readyState === WebSocket.OPEN) {
          ws.close(1011, 'Internal Server Error');
        }
      });

      ws.on('close', () => {
        console.log('Client disconnected');
      });
    });
  }

  private async sendMessage(ws: WebSocket, message: unknown): Promise<void> {
    return new Promise((resolve, reject) => {
      if (ws.readyState !== WebSocket.OPEN) {
        console.log('WebSocket not open, readyState:', ws.readyState);
        reject(new Error('WebSocket is not open'));
        return;
      }

      console.log('Sending WebSocket message:', JSON.stringify(message));
      ws.send(JSON.stringify(message), error => {
        if (error) {
          console.error('Error sending WebSocket message:', error);
          reject(error);
        } else {
          console.log('WebSocket message sent successfully');
          resolve();
        }
      });
    });
  }

  private async sendTradeHistory(ws: WebSocket, limit: number) {
    try {
      const trades = await ArbitrageTrade.find()
        .sort({ timestamp: -1 })
        .limit(Math.min(limit, 100));

      // Ensure client is still connected before sending
      if (ws.readyState === WebSocket.OPEN) {
        await this.sendMessage(ws, {
          type: 'tradeHistory',
          data: trades,
        });
      }
    } catch (error) {
      console.error('Error sending trade history:', error);
      if (ws.readyState === WebSocket.OPEN) {
        await this.sendMessage(ws, {
          type: 'error',
          data: { message: 'Failed to fetch trade history' },
        });
      }
    }
  }

  public async broadcast(message: BroadcastMessage): Promise<void> {
    const promises = Array.from(this.wss.clients)
      .filter(client => client.readyState === WebSocket.OPEN)
      .map(client => this.sendMessage(client, message));

    await Promise.all(promises);
  }

  public getServer(): WebSocket.Server {
    return this.wss;
  }
}
