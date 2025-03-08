"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.MonitoringSocket = void 0;
const ws_1 = __importDefault(require("ws"));
const logger_1 = require("../../utils/logger");
class MonitoringSocket {
    constructor(port, monitoring, priceAggregator) {
        this.port = port;
        this.monitoring = monitoring;
        this.priceAggregator = priceAggregator;
        this.clients = new Set();
        this.HEARTBEAT_INTERVAL = 30000;
        this.wss = new ws_1.default.Server({ port });
        this.setupWebSocketServer();
        this.setupEventHandlers();
    }
    setupWebSocketServer() {
        this.wss.on('connection', (ws) => {
            this.handleConnection(ws);
        });
        logger_1.logger.info(`WebSocket server started on port ${this.port}`);
    }
    setupEventHandlers() {
        this.monitoring.on('metricsUpdate', (metrics) => {
            this.broadcast('metrics', metrics);
        });
        this.priceAggregator.on('priceUpdate', (prices) => {
            this.broadcast('prices', prices);
        });
        this.priceAggregator.on('arbitrageOpportunity', (opportunities) => {
            this.broadcast('arbitrage', opportunities);
        });
    }
    handleConnection(ws) {
        this.clients.add(ws);
        logger_1.logger.info(`New WebSocket client connected. Total clients: ${this.clients.size}`);
        this.sendInitialData(ws);
        const pingInterval = setInterval(() => {
            if (ws.readyState === ws_1.default.OPEN) {
                ws.ping();
            }
        }, this.HEARTBEAT_INTERVAL);
        ws.on('pong', () => {
        });
        ws.on('close', () => {
            this.clients.delete(ws);
            clearInterval(pingInterval);
            logger_1.logger.info(`WebSocket client disconnected. Total clients: ${this.clients.size}`);
        });
        ws.on('error', (error) => {
            logger_1.logger.error(`WebSocket error: ${error}`);
            this.clients.delete(ws);
            clearInterval(pingInterval);
        });
    }
    async sendInitialData(ws) {
        try {
            const metrics = this.monitoring.getMetrics();
            this.sendToClient(ws, 'metrics', metrics);
            const prices = this.priceAggregator.getPrices();
            this.sendToClient(ws, 'prices', prices);
            const opportunities = this.priceAggregator.getArbitrageOpportunities();
            this.sendToClient(ws, 'arbitrage', opportunities);
        }
        catch (error) {
            logger_1.logger.error(`Error sending initial data: ${error}`);
        }
    }
    broadcast(type, data) {
        const message = JSON.stringify({ type, data });
        this.clients.forEach((client) => {
            if (client.readyState === ws_1.default.OPEN) {
                client.send(message);
            }
        });
    }
    sendToClient(ws, type, data) {
        if (ws.readyState === ws_1.default.OPEN) {
            ws.send(JSON.stringify({ type, data }));
        }
    }
    stop() {
        this.clients.forEach((client) => {
            client.close();
        });
        this.wss.close(() => {
            logger_1.logger.info('WebSocket server stopped');
        });
    }
}
exports.MonitoringSocket = MonitoringSocket;
exports.default = MonitoringSocket;
//# sourceMappingURL=monitoringSocket.js.map