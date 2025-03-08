"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.WebSocketServer = void 0;
const events_1 = require("events");
const ws_1 = __importDefault(require("ws"));
class WebSocketServer extends events_1.EventEmitter {
    constructor(server) {
        super();
        this.clients = new Map();
        this.wss = new ws_1.default.Server({ server });
        this.initialize();
    }
    initialize() {
        this.wss.on('connection', (ws) => {
            const client = this.setupClient(ws);
            // Send connection confirmation
            this.sendToClient(client, {
                type: 'connection',
                message: 'Connected to ArbitrageX WebSocket Server'
            });
            // Handle incoming messages
            client.on('message', (data) => {
                try {
                    const message = JSON.parse(data.toString());
                    this.handleMessage(client, message);
                }
                catch (error) {
                    console.error('Error parsing message:', error);
                }
            });
            // Handle client disconnect
            client.on('close', () => {
                this.clients.delete(client.id);
                console.log(`Client ${client.id} disconnected`);
            });
        });
    }
    setupClient(ws) {
        const client = ws;
        client.id = Math.random().toString(36).substring(7);
        client.subscriptions = new Set();
        this.clients.set(client.id, client);
        console.log(`New client connected: ${client.id}`);
        return client;
    }
    handleMessage(client, message) {
        switch (message.type) {
            case 'subscribe':
                if (message.channel) {
                    client.subscriptions.add(message.channel);
                    this.sendToClient(client, {
                        type: 'subscribed',
                        channel: message.channel
                    });
                }
                break;
            case 'unsubscribe':
                if (message.channel) {
                    client.subscriptions.delete(message.channel);
                    this.sendToClient(client, {
                        type: 'unsubscribed',
                        channel: message.channel
                    });
                }
                break;
            default:
                this.emit('message', {
                    clientId: client.id,
                    message: message
                });
        }
    }
    broadcast(channel, data) {
        this.clients.forEach(client => {
            if (client.subscriptions.has(channel)) {
                this.sendToClient(client, {
                    type: 'broadcast',
                    channel: channel,
                    data: data
                });
            }
        });
    }
    sendToClient(client, data) {
        if (client.readyState === ws_1.default.OPEN) {
            client.send(JSON.stringify(data));
        }
    }
    getConnectedClients() {
        return this.clients.size;
    }
}
exports.WebSocketServer = WebSocketServer;
//# sourceMappingURL=server.js.map