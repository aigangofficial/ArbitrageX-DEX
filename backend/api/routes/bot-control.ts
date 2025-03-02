import { Router } from 'express';
import { spawn, ChildProcess } from 'child_process';
import path from 'path';
import { logger } from '../utils/logger';

const router = Router();

// Store the bot process
let botProcess: ChildProcess | null = null;

/**
 * @route POST /api/v1/bot-control/start
 * @desc Start the arbitrage bot
 * @access Protected
 */
router.post('/start', (req, res) => {
  try {
    if (botProcess) {
      return res.status(400).json({
        success: false,
        error: 'Bot is already running'
      });
    }

    const { 
      runTime = 600, 
      tokens = 'WETH,USDC,DAI', 
      dexes = 'uniswap_v3,curve,balancer', 
      gasStrategy = 'dynamic' 
    } = req.body;

    // Get the absolute path to the execution directory
    const executionDir = path.join(__dirname, '../../../backend/execution');
    
    // Start the bot process using npm run bot:start
    botProcess = spawn('npm', [
      'run',
      'bot:start',
      '--',
      '--run-time', runTime.toString(),
      '--tokens', tokens,
      '--dexes', dexes,
      '--gas-strategy', gasStrategy
    ], { cwd: executionDir });

    // Log output
    botProcess.stdout?.on('data', (data) => {
      logger.info(`Bot stdout: ${data}`);
    });

    botProcess.stderr?.on('data', (data) => {
      logger.error(`Bot stderr: ${data}`);
    });

    // Handle process exit
    botProcess.on('close', (code) => {
      logger.info(`Bot process exited with code ${code}`);
      botProcess = null;
    });

    return res.json({
      success: true,
      message: 'Bot started successfully'
    });
  } catch (error) {
    logger.error('Error starting bot:', error);
    return res.status(500).json({
      success: false,
      error: 'Failed to start bot'
    });
  }
});

/**
 * @route POST /api/v1/bot-control/stop
 * @desc Stop the arbitrage bot
 * @access Protected
 */
router.post('/stop', (req, res) => {
  try {
    if (!botProcess) {
      return res.status(400).json({
        success: false,
        error: 'Bot is not running'
      });
    }

    // Kill the bot process
    botProcess.kill();
    botProcess = null;

    return res.json({
      success: true,
      message: 'Bot stopped successfully'
    });
  } catch (error) {
    logger.error('Error stopping bot:', error);
    return res.status(500).json({
      success: false,
      error: 'Failed to stop bot'
    });
  }
});

/**
 * @route GET /api/v1/bot-control/status
 * @desc Get the current bot status
 * @access Public
 */
router.get('/status', (req, res) => {
  return res.json({
    success: true,
    data: {
      isRunning: botProcess !== null
    }
  });
});

export default router; 