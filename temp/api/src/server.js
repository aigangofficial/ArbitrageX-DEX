"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const cors_1 = __importDefault(require("cors"));
const express_1 = __importDefault(require("express"));
const mongoose_1 = __importDefault(require("mongoose"));
const ws_1 = __importDefault(require("ws"));
const config_1 = require("./config");
const app = (0, express_1.default)();
const port = process.env.PORT || 3001;
const wsPort = process.env.WS_PORT || 8080;
// Middleware
app.use((0, cors_1.default)());
app.use(express_1.default.json());
// MongoDB Connection
mongoose_1.default
    .connect(config_1.config.mongodbUri)
    .then(() => console.log('Connected to MongoDB'))
    .catch(err => console.error('MongoDB connection error:', err));
// Health check endpoint
app.get('/api/health', (_req, res) => {
    res.json({ status: 'ok', message: 'API is running' });
});
// Routes
app.post('/api/execute', async (req, res) => {
    try {
        // TODO: Implement trade execution logic
        res.json({ success: true, message: 'Trade executed successfully' });
    }
    catch (error) {
        console.error('Trade execution error:', error);
        res.status(500).json({ success: false, message: 'Failed to execute trade' });
    }
});
// WebSocket Server
const wss = new ws_1.default.Server({ port: Number(wsPort) });
wss.on('connection', ws => {
    console.log('Client connected to WebSocket');
    ws.on('message', message => {
        console.log('Received:', message);
    });
    ws.on('close', () => {
        console.log('Client disconnected');
    });
});
// Start Express Server
app.listen(port, () => {
    console.log(`Server running on port ${port}`);
    console.log(`WebSocket server running on port ${wsPort}`);
});
