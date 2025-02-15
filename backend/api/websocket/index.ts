import { Server } from 'http';
import WebSocket from 'ws';
import { logger } from '../utils/logger';

interface WebSocketMessage {
  type: 'marketData' | 'trade' | 'opportunity';
  data: any;
}

class WebSocketService {
  private wss: WebSocket.Server;
  private clients: Set<WebSocket> = new Set();

  constructor(server: Server) {
    this.wss = new WebSocket.Server({ server });
    this.initialize();
  }

  private initialize() {
    this.wss.on('connection', (ws: WebSocket) => {
      logger.info('New WebSocket client connected');
      this.clients.add(ws);

      ws.on('message', (message: string) => {
        try {
          const parsedMessage = JSON.parse(message);
          logger.info('Received WebSocket message:', parsedMessage);
        } catch (error) {
          logger.error('Error parsing WebSocket message:', error);
        }
      });

      ws.on('close', () => {
        logger.info('WebSocket client disconnected');
        this.clients.delete(ws);
      });

      ws.on('error', error => {
        logger.error('WebSocket error:', error);
        this.clients.delete(ws);
      });

      // Send initial connection success message
      ws.send(
        JSON.stringify({
          type: 'connection',
          data: { status: 'connected' },
        })
      );
    });
  }

  public broadcast(message: WebSocketMessage) {
    const messageString = JSON.stringify(message);
    this.clients.forEach(client => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(messageString);
      }
    });
  }

  public sendToClient(client: WebSocket, message: WebSocketMessage) {
    if (client.readyState === WebSocket.OPEN) {
      client.send(JSON.stringify(message));
    }
  }
}

export default WebSocketService;
