import { Server } from 'http';
import WebSocket from 'ws';
import { logger } from '../utils/logger';
import { validatePort, WS_CONFIG } from './config';

interface Client extends WebSocket {
  isAlive: boolean;
  subscriptions: Set<string>;
}

export class WebSocketServer {
  private wss!: WebSocket.Server;
  private clients: Set<Client> = new Set();
  private heartbeatInterval!: NodeJS.Timeout;

  constructor(server: Server) {
    this.initializeServer(server);
  }

  private async initializeServer(server: Server) {
    try {
      // Validate port before starting
      await validatePort();

      this.wss = new WebSocket.Server({
        server,
        maxPayload: 1024 * 1024, // 1MB max payload
      });

      this.setupServerHandlers();
      this.startHeartbeat();

      logger.info(`WebSocket server initialized on port ${WS_CONFIG.port}`);
    } catch (error) {
      logger.error('Failed to initialize WebSocket server:', error);
      throw error;
    }
  }

  private setupServerHandlers() {
    this.wss.on('connection', (ws: WebSocket) => {
      const client = ws as Client;
      client.isAlive = true;
      client.subscriptions = new Set();

      this.clients.add(client);
      logger.info(`New WebSocket client connected. Total clients: ${this.clients.size}`);

      this.setupClientHandlers(client);
      this.sendWelcomeMessage(client);
    });
  }

  private setupClientHandlers(client: Client) {
    client.on('pong', () => {
      client.isAlive = true;
    });

    client.on('message', (data: WebSocket.RawData) => {
      try {
        const message = JSON.parse(data.toString());
        this.handleClientMessage(client, message);
      } catch (error) {
        logger.error('Error handling client message:', error);
        this.sendError(client, 'Invalid message format');
      }
    });

    client.on('close', () => {
      this.clients.delete(client);
      logger.info(`Client disconnected. Remaining clients: ${this.clients.size}`);
    });

    client.on('error', error => {
      logger.error('WebSocket client error:', error);
      this.clients.delete(client);
    });
  }

  private startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      this.clients.forEach(client => {
        if (!client.isAlive) {
          client.terminate();
          this.clients.delete(client);
          return;
        }

        client.isAlive = false;
        client.ping();
      });
    }, WS_CONFIG.heartbeat.interval);
  }

  private handleClientMessage(client: Client, message: any) {
    switch (message.type) {
      case 'subscribe':
        this.handleSubscription(client, message.channels);
        break;
      case 'unsubscribe':
        this.handleUnsubscription(client, message.channels);
        break;
      default:
        this.sendError(client, 'Unknown message type');
    }
  }

  private handleSubscription(client: Client, channels: string[]) {
    channels.forEach(channel => {
      client.subscriptions.add(channel);
    });
    this.sendSuccess(client, 'Subscribed to channels', { channels });
  }

  private handleUnsubscription(client: Client, channels: string[]) {
    channels.forEach(channel => {
      client.subscriptions.delete(channel);
    });
    this.sendSuccess(client, 'Unsubscribed from channels', { channels });
  }

  public broadcast(channel: string, data: any) {
    const message = JSON.stringify({ channel, data });
    this.clients.forEach(client => {
      if (client.subscriptions.has(channel) && client.readyState === WebSocket.OPEN) {
        client.send(message);
      }
    });
  }

  private sendWelcomeMessage(client: Client) {
    this.sendSuccess(client, 'Connected to ArbitrageX WebSocket Server', {
      availableChannels: ['tradeUpdates', 'gasPrice', 'opportunityAlerts'],
    });
  }

  private sendSuccess(client: Client, message: string, data: any = {}) {
    if (client.readyState === WebSocket.OPEN) {
      client.send(
        JSON.stringify({
          type: 'success',
          message,
          data,
          timestamp: new Date().toISOString(),
        })
      );
    }
  }

  private sendError(client: Client, message: string) {
    if (client.readyState === WebSocket.OPEN) {
      client.send(
        JSON.stringify({
          type: 'error',
          message,
          timestamp: new Date().toISOString(),
        })
      );
    }
  }

  public cleanup() {
    clearInterval(this.heartbeatInterval);
    this.clients.forEach(client => {
      client.terminate();
    });
    this.clients.clear();
    this.wss.close();
  }
}
