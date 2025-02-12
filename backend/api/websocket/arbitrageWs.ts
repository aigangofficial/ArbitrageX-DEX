import WebSocket, { Server } from 'ws';
import { ArbitrageTrade, IArbitrageTrade } from '../../database/models/ArbitrageTrade';

interface ArbitrageUpdate {
  type: 'opportunity' | 'execution' | 'completion' | 'error';
  data: any;
  timestamp: number;
}

export class ArbitrageWebSocket {
  private wss: Server;
  private clients: Set<WebSocket>;

  constructor(wss: Server) {
    this.wss = wss;
    this.clients = new Set();
    this.initialize();
  }

  private initialize() {
    this.wss.on('connection', (ws: WebSocket) => {
      console.log('New client connected');
      this.clients.add(ws);

      ws.on('close', () => {
        console.log('Client disconnected');
        this.clients.delete(ws);
      });

      // Send last 5 trades as initial data
      this.sendLastTrades(ws);
    });
  }

  private async sendLastTrades(ws: WebSocket) {
    try {
      const lastTrades = await ArbitrageTrade.find().sort({ createdAt: -1 }).limit(5).lean();

      ws.send(
        JSON.stringify({
          type: 'history',
          data: lastTrades,
          timestamp: Date.now(),
        })
      );
    } catch (error) {
      console.error('Error fetching last trades:', error);
    }
  }

  public broadcastOpportunity(
    tokenA: string,
    tokenB: string,
    expectedProfit: bigint,
    route: { sourceExchange: string; targetExchange: string; path: string[] }
  ) {
    const update: ArbitrageUpdate = {
      type: 'opportunity',
      data: {
        tokenA,
        tokenB,
        expectedProfit: expectedProfit.toString(),
        route,
      },
      timestamp: Date.now(),
    };

    this.broadcast(update);
  }

  public broadcastExecution(trade: IArbitrageTrade) {
    const update: ArbitrageUpdate = {
      type: 'execution',
      data: trade,
      timestamp: Date.now(),
    };

    this.broadcast(update);
  }

  public broadcastCompletion(trade: IArbitrageTrade) {
    const update: ArbitrageUpdate = {
      type: 'completion',
      data: trade,
      timestamp: Date.now(),
    };

    this.broadcast(update);
  }

  public broadcastError(error: Error) {
    const update: ArbitrageUpdate = {
      type: 'error',
      data: {
        message: error.message || 'Unknown error occurred',
        code: (error as any).code,
        details: (error as any).details,
      },
      timestamp: Date.now(),
    };

    this.broadcast(update);
  }

  private broadcast(data: ArbitrageUpdate) {
    const message = JSON.stringify(data);
    this.clients.forEach(client => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(message);
      }
    });
  }
}
