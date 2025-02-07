import express from 'express';
import http from 'http';
import cors from 'cors';
import { ethers } from 'ethers';
import { connectDB } from '../database/db';
import { ArbitrageWebSocketService } from './websocket/arbitrageWebSocket';
import { ArbitrageScanner } from '../execution/arbitrageScanner';
import { FlashLoanService } from '../types/contracts';
import { ArbitrageTrade } from '../database/models';

const app = express();
const server = http.createServer(app);

// Middleware
app.use(cors());
app.use(express.json());

// Initialize WebSocket service
const wsService = new ArbitrageWebSocketService(server);

// Initialize blockchain provider
const provider = new ethers.JsonRpcProvider(process.env.ETH_RPC_URL);

// Initialize Flash Loan service
const flashLoanAddress = process.env.FLASH_LOAN_ADDRESS;
if (!flashLoanAddress) {
    throw new Error('FLASH_LOAN_ADDRESS environment variable is not set');
}

const flashLoanService = new FlashLoanService(flashLoanAddress, provider);

// Initialize arbitrage scanner
const scanner = new ArbitrageScanner(flashLoanService, wsService.getServer());

// API Routes
app.get('/api/health', (req, res) => {
    res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

app.get('/api/trades', async (req, res) => {
    try {
        const limit = Math.min(parseInt(req.query.limit as string) || 50, 100);
        const trades = await ArbitrageTrade.find()
            .sort({ timestamp: -1 })
            .limit(limit);
        res.json(trades);
    } catch (error) {
        res.status(500).json({ error: 'Failed to fetch trades' });
    }
});

app.get('/api/trades/:id', async (req, res) => {
    try {
        const trade = await ArbitrageTrade.findById(req.params.id);
        if (!trade) {
            return res.status(404).json({ error: 'Trade not found' });
        }
        res.json(trade);
    } catch (error) {
        res.status(500).json({ error: 'Failed to fetch trade' });
    }
});

app.post('/api/execute', async (req, res) => {
    try {
        const { tradeId } = req.body;
        const trade = await ArbitrageTrade.findById(tradeId);
        
        if (!trade) {
            return res.status(404).json({ error: 'Trade not found' });
        }

        if (trade.status !== 'pending') {
            return res.status(400).json({ error: 'Trade is not in pending state' });
        }

        // Execute the trade
        await scanner.executeArbitrage(trade);
        res.json({ message: 'Trade execution initiated' });
    } catch (error) {
        res.status(500).json({ error: 'Failed to execute trade' });
    }
});

// Start the server
const PORT = process.env.PORT || 3000;

async function startServer() {
    try {
        // Connect to MongoDB
        await connectDB();
        
        server.listen(PORT, () => {
            console.log(`Server running on port ${PORT}`);
        });
    } catch (error) {
        console.error('Failed to start server:', error);
        process.exit(1);
    }
}

startServer(); 