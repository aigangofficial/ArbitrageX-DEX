import { spawn } from 'child_process';
import path from 'path';
import { logger } from '../utils/logger';

interface AIModelResponse {
  success: boolean;
  predictions?: any;
  error?: string;
}

export class AIService {
  private readonly pythonPath: string;
  private readonly aiModulesPath: string;

  constructor() {
    this.pythonPath = process.env.PYTHON_PATH || 'python3';
    this.aiModulesPath = path.resolve(__dirname, '../../ai');
  }

  public async getPredictions(marketData: any): Promise<AIModelResponse> {
    try {
      const result = await this.runPythonScript('strategy_optimizer.py', [
        '--market-data',
        JSON.stringify(marketData),
      ]);
      return { success: true, predictions: JSON.parse(result) };
    } catch (error) {
      logger.error('Error getting AI predictions:', error);
      return { success: false, error: String(error) };
    }
  }

  public async analyzeTrade(tradeData: any): Promise<AIModelResponse> {
    try {
      const result = await this.runPythonScript('trade_analyzer.py', [
        '--trade-data',
        JSON.stringify(tradeData),
      ]);
      return { success: true, predictions: JSON.parse(result) };
    } catch (error) {
      logger.error('Error analyzing trade:', error);
      return { success: false, error: String(error) };
    }
  }

  public async runBacktest(config: any): Promise<AIModelResponse> {
    try {
      const result = await this.runPythonScript('backtesting.py', [
        '--config',
        JSON.stringify(config),
      ]);
      return { success: true, predictions: JSON.parse(result) };
    } catch (error) {
      logger.error('Error running backtest:', error);
      return { success: false, error: String(error) };
    }
  }

  private runPythonScript(scriptName: string, args: string[]): Promise<string> {
    return new Promise((resolve, reject) => {
      const scriptPath = path.join(this.aiModulesPath, scriptName);
      const process = spawn(this.pythonPath, [scriptPath, ...args]);

      let output = '';
      let errorOutput = '';

      process.stdout.on('data', data => {
        output += data.toString();
      });

      process.stderr.on('data', data => {
        errorOutput += data.toString();
      });

      process.on('close', code => {
        if (code !== 0) {
          reject(new Error(`Python script error: ${errorOutput}`));
        } else {
          resolve(output.trim());
        }
      });

      process.on('error', error => {
        reject(error);
      });
    });
  }

  public async validateAIModules(): Promise<boolean> {
    try {
      // Check if Python is available
      await this.runPythonScript('strategy_optimizer.py', ['--version']);

      // Verify all required modules exist
      const requiredModules = ['strategy_optimizer.py', 'trade_analyzer.py', 'backtesting.py'];

      for (const module of requiredModules) {
        const modulePath = path.join(this.aiModulesPath, module);
        if (!require('fs').existsSync(modulePath)) {
          throw new Error(`Missing AI module: ${module}`);
        }
      }

      return true;
    } catch (error) {
      logger.error('AI module validation failed:', error);
      return false;
    }
  }
}
