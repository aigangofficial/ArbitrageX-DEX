import express, { Request, Response } from 'express';
import { WebSocketService } from '../websocket/WebSocketService';
import fs from 'fs';
import path from 'path';
import { exec } from 'child_process';
import { logger } from '../utils/logger';

// Define execution modes
export enum ExecutionMode {
  MAINNET = 'mainnet',
  FORK = 'fork'
}

interface ExecutionModeConfig {
  mode: ExecutionMode;
  lastUpdated: string;
  updatedBy: string;
}

// Default config
const defaultConfig: ExecutionModeConfig = {
  mode: ExecutionMode.FORK, // Default to safer FORK mode
  lastUpdated: new Date().toISOString(),
  updatedBy: 'system'
};

// Config file path
const configFilePath = path.join(__dirname, '../../config/execution-mode.json');

// Helper to read current execution mode
const readExecutionMode = (): ExecutionModeConfig => {
  try {
    if (fs.existsSync(configFilePath)) {
      const configData = fs.readFileSync(configFilePath, 'utf8');
      return JSON.parse(configData);
    }
  } catch (error) {
    logger.error('Error reading execution mode config:', error);
  }
  
  // If file doesn't exist or error occurs, create with default
  fs.writeFileSync(configFilePath, JSON.stringify(defaultConfig, null, 2));
  return defaultConfig;
};

// Helper to write execution mode
const writeExecutionMode = (config: ExecutionModeConfig): void => {
  try {
    fs.writeFileSync(configFilePath, JSON.stringify(config, null, 2));
  } catch (error) {
    logger.error('Error writing execution mode config:', error);
    throw new Error('Failed to update execution mode');
  }
};

// Helper to update environment variables
const updateEnvironmentVariables = (mode: ExecutionMode): Promise<void> => {
  return new Promise((resolve, reject) => {
    const envFilePath = path.join(__dirname, '../../../.env');
    
    // Read current .env file
    fs.readFile(envFilePath, 'utf8', (err, data) => {
      if (err) {
        logger.error('Error reading .env file:', err);
        reject(err);
        return;
      }
      
      // Update EXECUTION_MODE variable
      let updatedData: string;
      if (data.includes('EXECUTION_MODE=')) {
        updatedData = data.replace(/EXECUTION_MODE=\w+/g, `EXECUTION_MODE=${mode}`);
      } else {
        updatedData = `${data}\nEXECUTION_MODE=${mode}`;
      }
      
      // Write updated .env file
      fs.writeFile(envFilePath, updatedData, 'utf8', (writeErr) => {
        if (writeErr) {
          logger.error('Error writing .env file:', writeErr);
          reject(writeErr);
          return;
        }
        
        // Execute script based on mode
        const scriptPath = mode === ExecutionMode.FORK 
          ? path.join(__dirname, '../../../scripts/start-fork.ts')
          : path.join(__dirname, '../../../scripts/switch-network.ts');
        
        const command = mode === ExecutionMode.FORK
          ? `npx ts-node ${scriptPath}`
          : `npx ts-node ${scriptPath} mainnet`;
        
        exec(command, (execErr, stdout, stderr) => {
          if (execErr) {
            logger.error(`Error executing script: ${execErr.message}`);
            logger.error(`stderr: ${stderr}`);
            reject(execErr);
            return;
          }
          
          logger.info(`Script output: ${stdout}`);
          resolve();
        });
      });
    });
  });
};

// Create router
export const createNetworkExecutionRouter = (wsService?: WebSocketService) => {
  const router = express.Router();
  
  // Get current execution mode
  router.get('/', async (req: Request, res: Response): Promise<any> => {
    try {
      const config = readExecutionMode();
      return res.json({
        success: true,
        data: config
      });
    } catch (error) {
      logger.error('Error getting execution mode:', error);
      return res.status(500).json({
        success: false,
        error: 'Failed to get execution mode'
      });
    }
  });
  
  // Update execution mode
  router.post('/', async (req: Request, res: Response): Promise<any> => {
    try {
      const { mode, updatedBy } = req.body;
      
      // Validate mode
      if (!Object.values(ExecutionMode).includes(mode)) {
        return res.status(400).json({
          success: false,
          error: `Invalid execution mode. Must be one of: ${Object.values(ExecutionMode).join(', ')}`
        });
      }
      
      // Update config
      const config: ExecutionModeConfig = {
        mode,
        lastUpdated: new Date().toISOString(),
        updatedBy: updatedBy || 'api'
      };
      
      // Write config to file
      writeExecutionMode(config);
      
      // Update environment variables and execute appropriate script
      await updateEnvironmentVariables(mode);
      
      // Notify connected clients via WebSocket if available
      if (wsService) {
        wsService.broadcast('executionModeChanged', {
          mode,
          timestamp: config.lastUpdated
        });
      }
      
      return res.json({
        success: true,
        data: config,
        message: `Execution mode updated to ${mode}`
      });
    } catch (error) {
      logger.error('Error updating execution mode:', error);
      return res.status(500).json({
        success: false,
        error: 'Failed to update execution mode'
      });
    }
  });
  
  return router;
};

export default createNetworkExecutionRouter; 