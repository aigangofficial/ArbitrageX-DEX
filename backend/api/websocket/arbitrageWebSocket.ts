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
        this.wss.on('connection', (ws: WebSocket) => {
            console.log('New WebSocket client connected');

            // Send last 10 trades on connection
            this.sendRecentTrades(ws);

            ws.on('message', async (message: string) => {
                try {
                    const data = JSON.parse(message);
                    
                    switch (data.type) {
                        case 'subscribe':
                            // Handle subscription requests
                            break;
                        case 'getHistory':
                            await this.sendTradeHistory(ws, data.limit || 50);
                            break;
                        default:
                            console.log('Unknown message type:', data.type);
                    }
                } catch (error) {
                    console.error('Error processing WebSocket message:', error);
                }
            });

            ws.on('close', () => {
                console.log('Client disconnected');
            });
        });
    }

    private async sendRecentTrades(ws: WebSocket) {
        try {
            const recentTrades = await ArbitrageTrade.find()
                .sort({ timestamp: -1 })
                .limit(10);

            ws.send(JSON.stringify({
                type: 'recentTrades',
                data: recentTrades
            }));
        } catch (error) {
            console.error('Error sending recent trades:', error);
        }
    }

    private async sendTradeHistory(ws: WebSocket, limit: number) {
        try {
            const trades = await ArbitrageTrade.find()
                .sort({ timestamp: -1 })
                .limit(Math.min(limit, 100));

            ws.send(JSON.stringify({
                type: 'tradeHistory',
                data: trades
            }));
        } catch (error) {
            console.error('Error sending trade history:', error);
        }
    }

    public broadcast(message: BroadcastMessage) {
        this.wss.clients.forEach(client => {
            if (client.readyState === WebSocket.OPEN) {
                client.send(JSON.stringify(message));
            }
        });
    }

    public getServer(): WebSocket.Server {
        return this.wss;
    }
} 