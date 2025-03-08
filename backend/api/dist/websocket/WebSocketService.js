"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.WebSocketService = void 0;
const ws_1 = __importDefault(require("ws"));
const logger_1 = require("../utils/logger");
const BotStatus_1 = require("../models/BotStatus");
const events_1 = require("events");
class WebSocketService extends events_1.EventEmitter {
    constructor(server) {
        super();
        this.statusInterval = null;
        this.HEARTBEAT_INTERVAL = 30000;
        this.STATUS_BROADCAST_INTERVAL = 5000;
        this.wss = new ws_1.default.Server({ server });
        this.setupWebSocketServer();
        this.startStatusBroadcast();
    }
    setupWebSocketServer() {
        this.wss.on('connection', (ws) => {
            const customWs = ws;
            customWs.isAlive = true;
            customWs.subscribedChannels = new Set();
            customWs.on('pong', () => {
                customWs.isAlive = true;
            });
            customWs.on('message', async (data) => {
                try {
                    await this.handleIncomingMessage(customWs, JSON.parse(data.toString()));
                }
                catch (error) {
                    logger_1.logger.error('Error handling WebSocket message:', error);
                    customWs.send(JSON.stringify({ error: 'Invalid message format' }));
                }
            });
        });
        // Set up heartbeat interval
        this.statusInterval = setInterval(() => {
            this.wss.clients.forEach((ws) => {
                const customWs = ws;
                if (customWs.isAlive === false) {
                    customWs.terminate();
                    return;
                }
                customWs.isAlive = false;
                customWs.ping();
            });
        }, this.HEARTBEAT_INTERVAL);
    }
    async handleIncomingMessage(ws, data) {
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
    handleSubscription(ws, channels) {
        channels.forEach(channel => ws.subscribedChannels.add(channel));
        ws.send(JSON.stringify({ type: 'subscribed', channels }));
    }
    handleUnsubscription(ws, channels) {
        channels.forEach(channel => ws.subscribedChannels.delete(channel));
        ws.send(JSON.stringify({ type: 'unsubscribed', channels }));
    }
    async sendBotStatus(ws) {
        try {
            const status = await BotStatus_1.BotStatus.findOne().sort({ lastHeartbeat: -1 });
            if (status && ws.readyState === ws_1.default.OPEN) {
                ws.send(JSON.stringify({
                    type: 'bot_status',
                    data: status
                }));
            }
        }
        catch (error) {
            logger_1.logger.error('Error sending bot status:', error);
        }
    }
    startStatusBroadcast() {
        setInterval(() => {
            this.broadcast('status_update', {
                timestamp: new Date().toISOString()
            });
        }, this.STATUS_BROADCAST_INTERVAL);
    }
    broadcast(type, data) {
        const message = JSON.stringify({ type, data });
        this.wss.clients.forEach((ws) => {
            const customWs = ws;
            if (customWs.readyState === ws_1.default.OPEN &&
                (!customWs.subscribedChannels || customWs.subscribedChannels.has(type))) {
                customWs.send(message);
            }
        });
    }
    async broadcastTradeUpdate(trade) {
        this.broadcast('trade_update', trade);
    }
    getConnectionCount() {
        return this.wss.clients.size;
    }
    cleanup() {
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
            this.statusInterval = null;
        }
        this.wss.close();
    }
}
exports.WebSocketService = WebSocketService;
//# sourceMappingURL=WebSocketService.js.map