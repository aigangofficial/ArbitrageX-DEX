"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = require("express");
const child_process_1 = require("child_process");
const path_1 = __importDefault(require("path"));
const logger_1 = require("../utils/logger");
const router = (0, express_1.Router)();
let botProcess = null;
router.post('/start', (req, res) => {
    try {
        if (botProcess) {
            return res.status(400).json({
                success: false,
                error: 'Bot is already running'
            });
        }
        const { runTime = 600, tokens = 'WETH,USDC,DAI', dexes = 'uniswap_v3,curve,balancer', gasStrategy = 'dynamic' } = req.body;
        const executionDir = path_1.default.join(__dirname, '../../../backend/execution');
        botProcess = (0, child_process_1.spawn)('npm', [
            'run',
            'bot:start',
            '--',
            '--run-time', runTime.toString(),
            '--tokens', tokens,
            '--dexes', dexes,
            '--gas-strategy', gasStrategy
        ], { cwd: executionDir });
        botProcess.stdout?.on('data', (data) => {
            logger_1.logger.info(`Bot stdout: ${data}`);
        });
        botProcess.stderr?.on('data', (data) => {
            logger_1.logger.error(`Bot stderr: ${data}`);
        });
        botProcess.on('close', (code) => {
            logger_1.logger.info(`Bot process exited with code ${code}`);
            botProcess = null;
        });
        return res.json({
            success: true,
            message: 'Bot started successfully'
        });
    }
    catch (error) {
        logger_1.logger.error('Error starting bot:', error);
        return res.status(500).json({
            success: false,
            error: 'Failed to start bot'
        });
    }
});
router.post('/stop', (req, res) => {
    try {
        if (!botProcess) {
            return res.status(400).json({
                success: false,
                error: 'Bot is not running'
            });
        }
        botProcess.kill();
        botProcess = null;
        return res.json({
            success: true,
            message: 'Bot stopped successfully'
        });
    }
    catch (error) {
        logger_1.logger.error('Error stopping bot:', error);
        return res.status(500).json({
            success: false,
            error: 'Failed to stop bot'
        });
    }
});
router.get('/status', (req, res) => {
    return res.json({
        success: true,
        data: {
            isRunning: botProcess !== null
        }
    });
});
exports.default = router;
//# sourceMappingURL=bot-control.js.map