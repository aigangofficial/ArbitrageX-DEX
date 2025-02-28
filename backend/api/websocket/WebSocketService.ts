import WebSocket from 'ws';
import { Server } from 'http';
import { logger } from '../utils/logger';
import { BotStatus } from '../models/BotStatus';
import { TradeHistory } from '../models/TradeHistory';
import { EventEmitter } from 'events';

// Define custom WebSocket interface with our additional properties
interface CustomWebSocket extends WebSocket {
  isAlive: boolean;
  subscribedChannels: Set<string>;
}

export class WebSocketService extends EventEmitter {
  private wss: WebSocket.Server;
  private statusInterval: NodeJS.Timeout | null = null;
  private readonly HEARTBEAT_INTERVAL = 30000;
  private readonly STATUS_BROADCAST_INTERVAL = 5000;

  constructor(server: Server) {
    super();
    this.wss = new WebSocket.Server({ server });
    this.setupWebSocketServer();
    this.startStatusBroadcast();
  }

  private setupWebSocketServer(): void {
    this.wss.on('connection', (ws: WebSocket) => {
      const customWs = ws as CustomWebSocket;
      customWs.isAlive = true;
      customWs.subscribedChannels = new Set();

      customWs.on('pong', () => {
        customWs.isAlive = true;
      });

      customWs.on('message', async (data: WebSocket.Data) => {
        try {
          await this.handleIncomingMessage(customWs, JSON.parse(data.toString()));
        } catch (error) {
          logger.error('Error handling WebSocket message:', error);
          customWs.send(JSON.stringify({ error: 'Invalid message format' }));
        }
      });
    });

    // Set up heartbeat interval
    this.statusInterval = setInterval(() => {
      this.wss.clients.forEach((ws: WebSocket) => {
        const customWs = ws as CustomWebSocket;
        if (customWs.isAlive === false) {
          customWs.terminate();
          return;
        }
        customWs.isAlive = false;
        customWs.ping();
      });
    }, this.HEARTBEAT_INTERVAL);
  }

  private async handleIncomingMessage(ws: CustomWebSocket, data: any): Promise<void> {
    switch (data.type) {
      case 'subscribe':
        this.handleSubscription(ws, data.channels);
        break;
      case 'unsubscribe':
        this.handleUnsubscription(ws, data.channels);
        break;
      case 'get_status':
        await this.sendBotStatus(ws);
        break;
      default:
        ws.send(JSON.stringify({ error: 'Unknown message type' }));
    }
  }

  private handleSubscription(ws: CustomWebSocket, channels: string[]): void {
    channels.forEach(channel => ws.subscribedChannels.add(channel));
    ws.send(JSON.stringify({ type: 'subscribed', channels }));
  }

  private handleUnsubscription(ws: CustomWebSocket, channels: string[]): void {
    channels.forEach(channel => ws.subscribedChannels.delete(channel));
    ws.send(JSON.stringify({ type: 'unsubscribed', channels }));
  }

  private async sendBotStatus(ws: CustomWebSocket): Promise<void> {
    try {
      const status = await BotStatus.findOne().sort({ lastHeartbeat: -1 });
      if (status && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
          type: 'bot_status',
          data: status
        }));
      }
    } catch (error) {
      logger.error('Error sending bot status:', error);
    }
  }

  private startStatusBroadcast(): void {
    setInterval(() => {
      this.broadcast('status_update', {
        timestamp: new Date().toISOString()
      });
    }, this.STATUS_BROADCAST_INTERVAL);
  }

  public broadcast(type: string, data: any): void {
    const message = JSON.stringify({ type, data });
    this.wss.clients.forEach((ws: WebSocket) => {
      const customWs = ws as CustomWebSocket;
      if (customWs.readyState === WebSocket.OPEN &&
          (!customWs.subscribedChannels || customWs.subscribedChannels.has(type))) {
        customWs.send(message);
      }
    });
  }

  public async broadcastTradeUpdate(trade: any): Promise<void> {
    this.broadcast('trade_update', trade);
  }

  public getConnectionCount(): number {
    return this.wss.clients.size;
  }

  public cleanup(): void {
    if (this.statusInterval) {
      clearInterval(this.statusInterval);
      this.statusInterval = null;
    }
    this.wss.close();
  }
}

// Extend WebSocket interface to include custom properties
declare module 'ws' {
  interface WebSocket {
    isAlive: boolean;
    subscribedChannels: Set<string>;
  }
} 