"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.createAIRouter = void 0;
const express_1 = require("express");
const child_process_1 = require("child_process");
const logger_1 = require("../utils/logger");
const path_1 = __importDefault(require("path"));
const router = (0, express_1.Router)();
const createAIRouter = () => {
    // Predict trade profitability
    router.post('/predict_trade', async (req, res) => {
        try {
            const { trade_data } = req.body;
            if (!trade_data || !Array.isArray(trade_data)) {
                return res.status(400).json({
                    success: false,
                    error: 'Invalid trade data. Expected array of features'
                });
            }
            // Spawn Python process to run prediction
            const pythonProcess = (0, child_process_1.spawn)('python3', [
                path_1.default.join(__dirname, '../../../ml_bot/ai_trading_model.py'),
                '--predict',
                JSON.stringify(trade_data)
            ]);
            let result = '';
            let error = '';
            pythonProcess.stdout.on('data', (data) => {
                result += data.toString();
            });
            pythonProcess.stderr.on('data', (data) => {
                error += data.toString();
            });
            pythonProcess.on('close', (code) => {
                if (code !== 0) {
                    logger_1.logger.error(`AI prediction failed with code ${code}: ${error}`);
                    return res.status(500).json({
                        success: false,
                        error: 'Failed to predict trade profitability'
                    });
                }
                try {
                    const prediction = JSON.parse(result);
                    res.json({
                        success: true,
                        prediction: {
                            profitability_score: prediction,
                            timestamp: new Date().toISOString()
                        }
                    });
                }
                catch (e) {
                    logger_1.logger.error('Failed to parse AI prediction result:', e);
                    res.status(500).json({
                        success: false,
                        error: 'Invalid prediction result format'
                    });
                }
            });
        }
        catch (error) {
            logger_1.logger.error('Error in AI prediction:', error);
            res.status(500).json({
                success: false,
                error: 'Internal server error'
            });
        }
    });
    // Get AI model status
    router.get('/status', async (_req, res) => {
        try {
            const modelPath = path_1.default.join(__dirname, '../../../ml_bot/datasets/trading_ai.pth');
            const modelExists = require('fs').existsSync(modelPath);
            res.json({
                success: true,
                status: {
                    model_loaded: modelExists,
                    last_training: modelExists ?
                        new Date(require('fs').statSync(modelPath).mtime).toISOString() :
                        null,
                    version: '1.0.0'
                }
            });
        }
        catch (error) {
            logger_1.logger.error('Error checking AI model status:', error);
            res.status(500).json({
                success: false,
                error: 'Failed to check AI model status'
            });
        }
    });
    return router;
};
exports.createAIRouter = createAIRouter;
//# sourceMappingURL=ai.js.map