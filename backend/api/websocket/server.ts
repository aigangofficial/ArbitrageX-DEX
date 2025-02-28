import { EventEmitter } from 'events';
import { Server } from 'http';
import WebSocket from 'ws';

interface Client extends WebSocket {
    id: string;
    subscriptions: Set<string>;
}

export class WebSocketServer extends EventEmitter {
    private wss: WebSocket.Server;
    private clients: Map<string, Client>;

    constructor(server: Server) {
        super();
        this.clients = new Map();
        this.wss = new WebSocket.Server({ server });
        this.initialize();
    }

    private initialize(): void {
        this.wss.on('connection', (ws: WebSocket) => {
            const client = this.setupClient(ws);

            // Send connection confirmation
            this.sendToClient(client, {
                type: 'connection',
                message: 'Connected to ArbitrageX WebSocket Server'
            });

            // Handle incoming messages
            client.on('message', (data: WebSocket.Data) => {
                try {
                    const message = JSON.parse(data.toString());
                    this.handleMessage(client, message);
                } catch (error) {
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

    private setupClient(ws: WebSocket): Client {
        const client = ws as Client;
        client.id = Math.random().toString(36).substring(7);
        client.subscriptions = new Set();
        this.clients.set(client.id, client);
        console.log(`New client connected: ${client.id}`);
        return client;
    }

    private handleMessage(client: Client, message: any): void {
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

    public broadcast(channel: string, data: any): void {
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

    private sendToClient(client: Client, data: any): void {
        if (client.readyState === WebSocket.OPEN) {
            client.send(JSON.stringify(data));
        }
    }

    public getConnectedClients(): number {
        return this.clients.size;
    }
}
