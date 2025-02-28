import WebSocket from 'ws';
import { PriceAggregator } from '../../price-feed/priceAggregator';
import { logger } from '../../utils/logger';
import { MonitoringService } from '../services/monitoringService';

export class MonitoringSocket {
    private wss: WebSocket.Server;
    private clients: Set<WebSocket> = new Set();
    private readonly HEARTBEAT_INTERVAL = 30000; // 30 seconds

    constructor(
        private readonly port: number,
        private readonly monitoring: MonitoringService,
        private readonly priceAggregator: PriceAggregator
    ) {
        this.wss = new WebSocket.Server({ port });
        this.setupWebSocketServer();
        this.setupEventHandlers();
    }

    private setupWebSocketServer(): void {
        this.wss.on('connection', (ws: WebSocket) => {
            this.handleConnection(ws);
        });

        logger.info(`WebSocket server started on port ${this.port}`);
    }

    private setupEventHandlers(): void {
        // Monitor metrics updates
        this.monitoring.on('metricsUpdate', (metrics) => {
            this.broadcast('metrics', metrics);
        });

        // Price updates
        this.priceAggregator.on('priceUpdate', (prices) => {
            this.broadcast('prices', prices);
        });

        // Arbitrage opportunities
        this.priceAggregator.on('arbitrageOpportunity', (opportunities) => {
            this.broadcast('arbitrage', opportunities);
        });
    }

    private handleConnection(ws: WebSocket): void {
        this.clients.add(ws);
        logger.info(`New WebSocket client connected. Total clients: ${this.clients.size}`);

        // Send initial data
        this.sendInitialData(ws);

        // Setup ping-pong for connection health check
        const pingInterval = setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
                ws.ping();
            }
        }, this.HEARTBEAT_INTERVAL);

        ws.on('pong', () => {
            // Client is alive
        });

        ws.on('close', () => {
            this.clients.delete(ws);
            clearInterval(pingInterval);
            logger.info(`WebSocket client disconnected. Total clients: ${this.clients.size}`);
        });

        ws.on('error', (error) => {
            logger.error(`WebSocket error: ${error}`);
            this.clients.delete(ws);
            clearInterval(pingInterval);
        });
    }

    private async sendInitialData(ws: WebSocket): Promise<void> {
        try {
            // Send current system metrics
            const metrics = this.monitoring.getMetrics();
            this.sendToClient(ws, 'metrics', metrics);

            // Send current prices
            const prices = this.priceAggregator.getPrices();
            this.sendToClient(ws, 'prices', prices);

            // Send current arbitrage opportunities
            const opportunities = this.priceAggregator.getArbitrageOpportunities();
            this.sendToClient(ws, 'arbitrage', opportunities);
        } catch (error) {
            logger.error(`Error sending initial data: ${error}`);
        }
    }

    private broadcast(type: string, data: any): void {
        const message = JSON.stringify({ type, data });
        this.clients.forEach((client) => {
            if (client.readyState === WebSocket.OPEN) {
                client.send(message);
            }
        });
    }

    private sendToClient(ws: WebSocket, type: string, data: any): void {
        if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type, data }));
        }
    }

    stop(): void {
        this.clients.forEach((client) => {
            client.close();
        });
        this.wss.close(() => {
            logger.info('WebSocket server stopped');
        });
    }
}

export default MonitoringSocket;
