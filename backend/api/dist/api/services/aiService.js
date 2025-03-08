"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.AIService = void 0;
const child_process_1 = require("child_process");
const path_1 = __importDefault(require("path"));
const logger_1 = require("../utils/logger");
class AIService {
    constructor() {
        this.pythonPath = process.env.PYTHON_PATH || 'python3';
        this.aiModulesPath = path_1.default.resolve(__dirname, '../../ai');
    }
    async getPredictions(marketData) {
        try {
            const result = await this.runPythonScript('strategy_optimizer.py', [
                '--market-data',
                JSON.stringify(marketData),
            ]);
            return { success: true, predictions: JSON.parse(result) };
        }
        catch (error) {
            logger_1.logger.error('Error getting AI predictions:', error);
            return { success: false, error: String(error) };
        }
    }
    async analyzeTrade(tradeData) {
        try {
            const result = await this.runPythonScript('trade_analyzer.py', [
                '--trade-data',
                JSON.stringify(tradeData),
            ]);
            return { success: true, predictions: JSON.parse(result) };
        }
        catch (error) {
            logger_1.logger.error('Error analyzing trade:', error);
            return { success: false, error: String(error) };
        }
    }
    async runBacktest(config) {
        try {
            const result = await this.runPythonScript('backtesting.py', [
                '--config',
                JSON.stringify(config),
            ]);
            return { success: true, predictions: JSON.parse(result) };
        }
        catch (error) {
            logger_1.logger.error('Error running backtest:', error);
            return { success: false, error: String(error) };
        }
    }
    runPythonScript(scriptName, args) {
        return new Promise((resolve, reject) => {
            const scriptPath = path_1.default.join(this.aiModulesPath, scriptName);
            const process = (0, child_process_1.spawn)(this.pythonPath, [scriptPath, ...args]);
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
                }
                else {
                    resolve(output.trim());
                }
            });
            process.on('error', error => {
                reject(error);
            });
        });
    }
    async validateAIModules() {
        try {
            await this.runPythonScript('strategy_optimizer.py', ['--version']);
            const requiredModules = ['strategy_optimizer.py', 'trade_analyzer.py', 'backtesting.py'];
            for (const module of requiredModules) {
                const modulePath = path_1.default.join(this.aiModulesPath, module);
                if (!require('fs').existsSync(modulePath)) {
                    throw new Error(`Missing AI module: ${module}`);
                }
            }
            return true;
        }
        catch (error) {
            logger_1.logger.error('AI module validation failed:', error);
            return false;
        }
    }
}
exports.AIService = AIService;
//# sourceMappingURL=aiService.js.map