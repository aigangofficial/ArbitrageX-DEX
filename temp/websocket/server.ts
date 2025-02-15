import { WebSocket, WebSocketServer } from 'ws';
import { logger } from '../api/utils/logger';
import { CustomWebSocket } from '../types/websocket';

export class WebSocketService {
  private wss: WebSocketServer;
  private readonly pingInterval: number = 30000; // 30 seconds

  constructor() {
    this.wss = new WebSocketServer({ noServer: true });
    this.initialize();
  }

  private initialize(): void {
    this.wss.on('connection', (ws: WebSocket) => {
      const customWs = ws as CustomWebSocket;
      customWs.isAlive = true;
      customWs.subscriptions = new Set();

      customWs.on('pong', () => {
        customWs.isAlive = true;
      });

      customWs.on('message', (message: string) => {
        try {
          const data = JSON.parse(message);
          this.handleMessage(customWs, data);
        } catch (error) {
          logger.error('Error handling WebSocket message:', error);
          customWs.send(JSON.stringify({
            type: 'ERROR',
            message: 'Invalid message format',
          }));
        }
      });

      customWs.on('error', (error) => {
        logger.error('WebSocket error:', error);
      });

      customWs.on('close', () => {
        logger.info('Client disconnected');
      });

      // Send welcome message
      customWs.send(JSON.stringify({
        type: 'CONNECTED',
        message: 'Connected to ArbitrageX WebSocket server',
        timestamp: new Date().toISOString(),
      }));
    });

    // Start heartbeat
    this.startHeartbeat();
  }

  private startHeartbeat(): void {
    setInterval(() => {
      this.wss.clients.forEach((ws: WebSocket) => {
        const customWs = ws as CustomWebSocket;
        if (customWs.isAlive === false) {
          logger.warn('Terminating inactive WebSocket connection');
          return customWs.terminate();
        }

        customWs.isAlive = false;
        customWs.ping();
      });
    }, this.pingInterval);
  }

  private handleMessage(ws: CustomWebSocket, data: any): void {
    switch (data.type) {
      case 'SUBSCRIBE':
        this.handleSubscribe(ws, data);
        break;
      case 'UNSUBSCRIBE':
        this.handleUnsubscribe(ws, data);
        break;
      default:
        ws.send(JSON.stringify({
          type: 'ERROR',
          message: 'Unknown message type',
        }));
    }
  }

  private handleSubscribe(ws: CustomWebSocket, data: any): void {
    if (!data.channels || !Array.isArray(data.channels)) {
      ws.send(JSON.stringify({
        type: 'ERROR',
        message: 'Invalid subscription format',
      }));
      return;
    }

    data.channels.forEach((channel: string) => {
      ws.subscriptions.add(channel);
    });

    ws.send(JSON.stringify({
      type: 'SUBSCRIBED',
      channels: Array.from(ws.subscriptions),
    }));
  }

  private handleUnsubscribe(ws: CustomWebSocket, data: any): void {
    if (!data.channels || !Array.isArray(data.channels)) {
      ws.send(JSON.stringify({
        type: 'ERROR',
        message: 'Invalid unsubscribe format',
      }));
      return;
    }

    data.channels.forEach((channel: string) => {
      ws.subscriptions.delete(channel);
    });

    ws.send(JSON.stringify({
      type: 'UNSUBSCRIBED',
      channels: Array.from(ws.subscriptions),
    }));
  }

  public broadcast(data: any, channel?: string): void {
    const message = JSON.stringify(data);
    this.wss.clients.forEach((ws: WebSocket) => {
      const customWs = ws as CustomWebSocket;
      if (
        customWs.readyState === WebSocket.OPEN &&
        (!channel || customWs.subscriptions.has(channel))
      ) {
        customWs.send(message);
      }
    });
  }

  public getServer(): WebSocketServer {
    return this.wss;
  }

  public close(): void {
    this.wss.close();
  }
}
