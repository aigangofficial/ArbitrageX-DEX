import express from 'express';
import cors from 'cors';
import { config } from './config';
import { WebSocketServer } from 'ws';

const app = express();
const port = config.port || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Health check endpoint
app.get('/api/health', (req, res) => {
    res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// WebSocket setup for real-time trade updates
const wss = new WebSocketServer({ port: config.wsPort || 3001 });

wss.on('connection', (ws) => {
    console.log('New WebSocket client connected');
    
    ws.on('message', (message) => {
        console.log('Received:', message);
    });
});

// Start server
app.listen(port, () => {
    console.log(`ArbitrageX API server running on port ${port}`);
    console.log(`WebSocket server running on port ${config.wsPort || 3001}`);
}); 