import cors from 'cors';
import express from 'express';
import mongoose from 'mongoose';
import WebSocket from 'ws';
import { config } from './config';

const app = express();
const port = process.env.PORT || 3001;
const wsPort = process.env.WS_PORT || 8080;

// Middleware
app.use(cors());
app.use(express.json());

// MongoDB Connection
mongoose
  .connect(config.mongodbUri)
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
  } catch (error) {
    console.error('Trade execution error:', error);
    res.status(500).json({ success: false, message: 'Failed to execute trade' });
  }
});

// WebSocket Server
const wss = new WebSocket.Server({ port: Number(wsPort) });

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
