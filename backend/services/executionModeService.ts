import fs from 'fs';
import path from 'path';
import { EventEmitter } from 'events';
import { logger } from '../api/utils/logger';
import { ExecutionMode } from '../execution/tradeExecutor';

// Interface for execution mode config
interface ExecutionModeConfig {
  mode: ExecutionMode;
  lastUpdated: string;
  updatedBy: string;
}

/**
 * Service to manage execution mode across the application
 * Uses the Singleton pattern to ensure only one instance exists
 */
class ExecutionModeService extends EventEmitter {
  private static instance: ExecutionModeService;
  private currentMode: ExecutionMode = ExecutionMode.FORK; // Default to safer FORK mode
  private configFilePath: string;

  private constructor() {
    super();
    this.configFilePath = path.join(__dirname, '../../config/execution-mode.json');
    this.loadExecutionMode();
  }

  /**
   * Get the singleton instance of the service
   */
  public static getInstance(): ExecutionModeService {
    if (!ExecutionModeService.instance) {
      ExecutionModeService.instance = new ExecutionModeService();
    }
    return ExecutionModeService.instance;
  }

  /**
   * Load the execution mode from the config file
   */
  private loadExecutionMode(): void {
    try {
      if (fs.existsSync(this.configFilePath)) {
        const configData = fs.readFileSync(this.configFilePath, 'utf8');
        const config: ExecutionModeConfig = JSON.parse(configData);
        this.currentMode = config.mode;
        logger.info(`ExecutionModeService loaded mode: ${this.currentMode}`);
      } else {
        logger.warn('Execution mode config file not found, using default: FORK');
        this.saveExecutionMode(this.currentMode, 'system-initialization');
      }
    } catch (error) {
      logger.error('Error loading execution mode config:', error);
    }
  }

  /**
   * Save the execution mode to the config file
   */
  private saveExecutionMode(mode: ExecutionMode, updatedBy: string): void {
    try {
      // Create the config directory if it doesn't exist
      const configDir = path.dirname(this.configFilePath);
      if (!fs.existsSync(configDir)) {
        fs.mkdirSync(configDir, { recursive: true });
      }

      // Update the execution mode config
      const config: ExecutionModeConfig = {
        mode,
        lastUpdated: new Date().toISOString(),
        updatedBy
      };

      // Write the updated config to the file
      fs.writeFileSync(this.configFilePath, JSON.stringify(config, null, 2));
      logger.info(`Execution mode saved to ${mode} by ${updatedBy}`);
    } catch (error) {
      logger.error('Error saving execution mode config:', error);
    }
  }

  /**
   * Get the current execution mode
   */
  public getMode(): ExecutionMode {
    return this.currentMode;
  }

  /**
   * Update the execution mode
   * @param mode The new execution mode
   * @param updatedBy Who or what updated the mode
   */
  public updateMode(mode: ExecutionMode, updatedBy: string): boolean {
    try {
      if (mode === this.currentMode) {
        logger.info(`Execution mode already set to ${mode}`);
        return true;
      }

      // Update the current mode
      this.currentMode = mode;
      
      // Save to config file
      this.saveExecutionMode(mode, updatedBy);
      
      // Emit event to notify all listeners
      this.emit('modeChanged', { mode, updatedBy });
      
      logger.info(`Execution mode updated to ${mode} by ${updatedBy}`);
      return true;
    } catch (error) {
      logger.error('Error updating execution mode:', error);
      return false;
    }
  }
}

export default ExecutionModeService; 