"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const models_1 = require("../../database/models");
const router = express_1.default.Router();
// Get all arbitrage trades
router.get('/', async (req, res) => {
    try {
        const trades = await models_1.ArbitrageTrade.find().sort({ createdAt: -1 });
        res.json(trades);
    }
    catch (error) {
        console.error('Error fetching trades:', error);
        res.status(500).json({ error: 'Failed to fetch trades' });
    }
});
// Create new arbitrage trade
router.post('/execute', async (req, res) => {
    try {
        const { tokenA, tokenB, amount, exchangeA, exchangeB } = req.body;
        console.log('Creating trade with parameters:', {
            tokenA,
            tokenB,
            amount,
            exchangeA,
            exchangeB,
        });
        // Validate required fields
        if (!tokenA || !tokenB || !amount || !exchangeA?.path || !exchangeB?.path) {
            return res.status(400).json({
                error: 'Missing required fields',
                required: ['tokenA', 'tokenB', 'amount', 'exchangeA.path', 'exchangeB.path'],
            });
        }
        // Create trade with initial path
        const trade = await models_1.ArbitrageTrade.create({
            tokenA,
            tokenB,
            amount: Number(amount),
            exchangeA: exchangeA.path,
            exchangeB: exchangeB.path,
            path: [tokenA, tokenB],
            expectedProfit: 0, // Will be calculated by execution engine
            status: 'pending',
        });
        console.log('Trade created:', trade);
        // Return the created trade
        res.json(trade);
    }
    catch (error) {
        console.error('Error executing trade:', error);
        res.status(500).json({
            error: 'Failed to execute trade',
            details: error instanceof Error ? error.message : 'Unknown error',
        });
    }
});
// Get trade by ID
router.get('/:id', async (req, res) => {
    try {
        const trade = await models_1.ArbitrageTrade.findById(req.params.id);
        if (!trade) {
            return res.status(404).json({ error: 'Trade not found' });
        }
        res.json(trade);
    }
    catch (error) {
        console.error('Error fetching trade:', error);
        res.status(500).json({ error: 'Failed to fetch trade' });
    }
});
exports.default = router;
