import cors from 'cors';
import { ethers } from 'ethers';
import express from 'express';
import mongoose from 'mongoose';
import path from 'path';
import { WebSocketServer } from 'ws';
import connectDB from '../database/connection';
import ArbitrageScanner from '../execution/arbitrageScanner';
import { config } from './config';
import { errorHandler } from './middleware/errorHandler';
import { marketDataLimiter } from './middleware/rateLimit';
import arbitrageRoutes from './routes/arbitrage';
import marketRoutes from './routes/market';
import testRoutes from './routes/test';
import tradeRoutes from './routes/trade';
import { requestLogger } from './utils/logger';

const app = express();
const port = config.api.port;

// Middleware
app.use(
  cors({
    origin: config.api.corsOrigin,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization'],
  })
);
app.use(express.json());
app.use(requestLogger);

// Initialize provider and contracts
const provider = new ethers.JsonRpcProvider(config.network.rpc);

// Initialize WebSocket server
const wss = new WebSocketServer({ port: config.api.wsPort });

// Initialize scanner
const scanner = new ArbitrageScanner(
  provider,
  config.contracts.quickswapRouter,
  config.contracts.sushiswapRouter,
  config.contracts.aavePool,
  {
    minProfitThreshold: config.security.minProfitThreshold,
    minNetProfit: 0.01,
    gasLimit: config.security.gasPriceLimit,
    scanInterval: 15000
  },
  [
    { tokenA: config.contracts.wmatic, tokenB: config.contracts.usdc },
    { tokenA: config.contracts.wmatic, tokenB: config.contracts.usdt }
  ]
);

// Serve static files from the frontend build directory
app.use(express.static(path.join(__dirname, '../../../frontend-new/build')));

// Test rate limiting
app.use('/api/test', marketDataLimiter, testRoutes);

// Routes
app.use('/api/arbitrage', arbitrageRoutes);
app.use('/api/market', marketRoutes);
app.use('/api/trades', tradeRoutes);

// Health check endpoint
app.get('/api/health', (_req, res) => {
  const wsStatus = wss.clients.size > 0 ? 'connected' : 'waiting';
  const scannerStatus = scanner.getIsScanning() ? 'running' : 'stopped';
  const dbStatus = mongoose.connection.readyState === 1 ? 'connected' : 'disconnected';

  const services = {
    api: 'healthy',
    websocket: wsStatus,
    scanner: scannerStatus,
    database: dbStatus,
  };

  const isHealthy = Object.values(services).every(
    status => status === 'healthy' || status === 'connected' || status === 'running'
  );

  return res.status(isHealthy ? 200 : 503).json({
    status: isHealthy ? 'ok' : 'degraded',
    services,
    timestamp: new Date().toISOString(),
  });
});

// Catch-all route to serve the React app
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../../../frontend-new/build', 'index.html'));
});

// Error handling middleware (must be last)
app.use(errorHandler);

// Start the server
async function startServer() {
  try {
    // Connect to MongoDB
    await connectDB();

    // Create logs directory if it doesn't exist
    const fs = require('fs');
    const logDir = config.logging.directory || 'logs';
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }

    // Start the server
    app.listen(port, () => {
      console.log(`Server is running on port ${port}`);
      console.log(`WebSocket server running on port ${config.api.wsPort}`);
      console.log(`Environment: ${process.env.NODE_ENV || 'development'}`);
    });

    // Start the scanner
    await scanner.start();
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

startServer();

export default app;
