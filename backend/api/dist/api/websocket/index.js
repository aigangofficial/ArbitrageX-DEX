"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const ws_1 = __importDefault(require("ws"));
const logger_1 = require("../utils/logger");
class WebSocketService {
    constructor(server) {
        this.clients = new Set();
        this.wss = new ws_1.default.Server({ server });
        this.initialize();
    }
    initialize() {
        this.wss.on('connection', (ws) => {
            logger_1.logger.info('New WebSocket client connected');
            this.clients.add(ws);
            ws.on('message', (message) => {
                try {
                    const parsedMessage = JSON.parse(message);
                    logger_1.logger.info('Received WebSocket message:', parsedMessage);
                }
                catch (error) {
                    logger_1.logger.error('Error parsing WebSocket message:', error);
                }
            });
            ws.on('close', () => {
                logger_1.logger.info('WebSocket client disconnected');
                this.clients.delete(ws);
            });
            ws.on('error', error => {
                logger_1.logger.error('WebSocket error:', error);
                this.clients.delete(ws);
            });
            ws.send(JSON.stringify({
                type: 'connection',
                data: { status: 'connected' },
            }));
        });
    }
    broadcast(message) {
        const messageString = JSON.stringify(message);
        this.clients.forEach(client => {
            if (client.readyState === ws_1.default.OPEN) {
                client.send(messageString);
            }
        });
    }
    sendToClient(client, message) {
        if (client.readyState === ws_1.default.OPEN) {
            client.send(JSON.stringify(message));
        }
    }
}
exports.default = WebSocketService;
//# sourceMappingURL=index.js.map