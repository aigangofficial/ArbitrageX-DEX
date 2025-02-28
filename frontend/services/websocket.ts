import { EventEmitter } from 'events';

export interface Trade {
  tokenIn: string;
  tokenOut: string;
  amountIn: string;
  amountOut: string;
  profit: string;
  gasUsed: number;
  gasPrice: string;
  txHash: string;
  blockNumber: number;
  timestamp: Date;
  router: string;
  status: 'pending' | 'completed' | 'failed';
  error?: string;
}

export interface BotStatus {
  isActive: boolean;
  lastHeartbeat: Date;
  totalTrades: number;
  successfulTrades: number;
  failedTrades: number;
  totalProfit: string;
  averageGasUsed: number;
  memoryUsage: {
    heapUsed: number;
    heapTotal: number;
    external: number;
  };
  cpuUsage: number;
  pendingTransactions: number;
  network: string;
  version: string;
  uptime: number;
  isHealthy: boolean;
}

export class WebSocketService extends EventEmitter {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private baseReconnectTimeout = 1000;
  private maxReconnectTimeout = 30000;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private pingInterval: NodeJS.Timeout | null = null;
  private subscribedChannels: Set<string> = new Set();
  private connectionState: 'connecting' | 'connected' | 'disconnected' | 'error' = 'disconnected';

  constructor(private readonly wsUrl: string = 'ws://localhost:3000/ws') {
    super();
    this.connect();
  }

  private connect(): void {
    if (this.connectionState === 'connecting') return;

    this.connectionState = 'connecting';
    this.ws = new WebSocket(this.wsUrl);
    this.setupEventHandlers();
    this.setupPing();
  }

  private setupEventHandlers(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      this.connectionState = 'connected';
      this.reconnectAttempts = 0;
      this.emit('connected');
      this.resubscribeToChannels();
      
      this.requestBotStatus();
    };

    this.ws.onclose = () => {
      this.connectionState = 'disconnected';
      this.emit('disconnected');
      this.cleanup();
      this.handleReconnect();
    };

    this.ws.onerror = (error) => {
      this.connectionState = 'error';
      this.emit('error', new Error('WebSocket connection error'));
      console.error('WebSocket error:', error);
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        switch (data.type) {
          case 'trade_update':
            this.emit('trade', data.data);
            break;
          case 'bot_status':
            this.emit('status', data.data);
            break;
          case 'error':
            this.emit('error', new Error(data.message || 'Unknown WebSocket error'));
            break;
          default:
            console.warn('Unknown message type:', data.type);
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
        this.emit('error', new Error('Invalid message format'));
      }
    };
  }

  private setupPing(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
    }

    this.pingInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);
  }

  private handleReconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this.emit('error', new Error('Maximum reconnection attempts reached'));
      return;
    }

    const timeout = Math.min(
      this.baseReconnectTimeout * Math.pow(2, this.reconnectAttempts),
      this.maxReconnectTimeout
    );

    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempts++;
      this.emit('reconnecting', {
        attempt: this.reconnectAttempts,
        maxAttempts: this.maxReconnectAttempts
      });
      this.connect();
    }, timeout);
  }

  public subscribe(channel: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'subscribe',
        channels: [channel]
      }));
      this.subscribedChannels.add(channel);
    }
  }

  public unsubscribe(channel: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'unsubscribe',
        channels: [channel]
      }));
      this.subscribedChannels.delete(channel);
    }
  }

  private resubscribeToChannels(): void {
    if (this.subscribedChannels.size > 0) {
      this.ws?.send(JSON.stringify({
        type: 'subscribe',
        channels: Array.from(this.subscribedChannels)
      }));
    }
  }

  public requestBotStatus(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'get_status' }));
    }
  }

  public cleanup(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  public disconnect(): void {
    this.cleanup();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  public getConnectionState(): string {
    return this.connectionState;
  }

  public getReconnectAttempts(): number {
    return this.reconnectAttempts;
  }

  public forceReconnect(): void {
    this.cleanup();
    this.reconnectAttempts = 0;
    this.connect();
  }
} 