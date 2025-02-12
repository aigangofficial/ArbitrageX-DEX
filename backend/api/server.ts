import cors from 'cors';
import { ethers } from 'ethers';
import express from 'express';
import mongoose from 'mongoose';
import { WebSocketServer } from 'ws';
import { ArbitrageTrade } from '../database/models';
import { ArbitrageScanner } from '../execution/arbitrageScanner';
import { config } from './config';

const app = express();
const port = config.api.port;

// Middleware
app.use(
  cors({
    origin: config.api.corsOrigin,
  })
);
app.use(express.json());

// Initialize provider and contracts
const provider = new ethers.JsonRpcProvider(config.network.rpc);

// Initialize WebSocket server
const wss = new WebSocketServer({ port: config.api.wsPort });

// Initialize scanner
const scanner = new ArbitrageScanner(
  provider,
  wss,
  config.contracts.flashLoanService,
  config.contracts.quickswapRouter,
  config.contracts.sushiswapRouter
);

// Health check endpoint
app.get('/api/health', (_req, res) => {
  return res.json({ status: 'ok' });
});

// Get all trades
app.get('/api/trades', async (_req, res) => {
  try {
    const trades = await ArbitrageTrade.find().sort({ createdAt: -1 }).limit(10);
    return res.json(trades);
  } catch (error) {
    return res.status(500).json({ error: 'Failed to fetch trades' });
  }
});

// Get trade by ID
app.get('/api/trades/:id', async (req, res) => {
  try {
    const trade = await ArbitrageTrade.findById(req.params.id);
    if (!trade) {
      return res.status(404).json({ error: 'Trade not found' });
    }
    return res.json(trade);
  } catch (error) {
    return res.status(500).json({ error: 'Failed to fetch trade' });
  }
});

// Execute arbitrage trade
app.post('/api/arbitrage/execute', async (req, res) => {
  try {
    const { tokenA, tokenB, amount, exchangeA, exchangeB } = req.body;

    if (!tokenA || !tokenB || !amount || !exchangeA || !exchangeB) {
      return res.status(400).json({
        error: 'Missing required fields',
        required: ['tokenA', 'tokenB', 'amount', 'exchangeA', 'exchangeB'],
      });
    }

    console.log('Creating trade with parameters:', {
      tokenA,
      tokenB,
      amount,
      exchangeA,
      exchangeB,
    });

    const trade = await ArbitrageTrade.create({
      tokenA,
      tokenB,
      amount: Number(amount),
      exchangeA,
      exchangeB,
      path: [tokenA, tokenB],
      expectedProfit: 0, // Will be calculated during scanning
      status: 'pending',
    });

    console.log('Trade created:', trade);

    // Start scanning for this trade
    scanner.startScanning();

    return res.json({
      message: 'Trade initiated',
      tradeId: trade._id,
      trade,
    });
  } catch (error: unknown) {
    console.error('Error executing trade:', error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
    return res.status(500).json({ error: 'Failed to execute trade', details: errorMessage });
  }
});

// Connect to MongoDB
mongoose
  .connect(config.database.uri, config.database.options)
  .then(() => {
    console.log('Connected to MongoDB');

    // Start the server
    app.listen(port, () => {
      console.log(`Server is running on port ${port}`);
      console.log(`WebSocket server running on port ${config.api.wsPort}`);
    });
  })
  .catch(error => {
    console.error('MongoDB connection error:', error);
    process.exit(1);
  });

export default app;
