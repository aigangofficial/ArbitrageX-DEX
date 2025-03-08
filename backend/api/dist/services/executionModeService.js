"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const fs_1 = __importDefault(require("fs"));
const path_1 = __importDefault(require("path"));
const events_1 = require("events");
const logger_1 = require("../api/utils/logger");
const tradeExecutor_1 = require("../execution/tradeExecutor");
class ExecutionModeService extends events_1.EventEmitter {
    constructor() {
        super();
        this.currentMode = tradeExecutor_1.ExecutionMode.FORK;
        this.configFilePath = path_1.default.join(__dirname, '../../config/execution-mode.json');
        this.loadExecutionMode();
    }
    static getInstance() {
        if (!ExecutionModeService.instance) {
            ExecutionModeService.instance = new ExecutionModeService();
        }
        return ExecutionModeService.instance;
    }
    loadExecutionMode() {
        try {
            if (fs_1.default.existsSync(this.configFilePath)) {
                const configData = fs_1.default.readFileSync(this.configFilePath, 'utf8');
                const config = JSON.parse(configData);
                this.currentMode = config.mode;
                logger_1.logger.info(`ExecutionModeService loaded mode: ${this.currentMode}`);
            }
            else {
                logger_1.logger.warn('Execution mode config file not found, using default: FORK');
                this.saveExecutionMode(this.currentMode, 'system-initialization');
            }
        }
        catch (error) {
            logger_1.logger.error('Error loading execution mode config:', error);
        }
    }
    saveExecutionMode(mode, updatedBy) {
        try {
            const configDir = path_1.default.dirname(this.configFilePath);
            if (!fs_1.default.existsSync(configDir)) {
                fs_1.default.mkdirSync(configDir, { recursive: true });
            }
            const config = {
                mode,
                lastUpdated: new Date().toISOString(),
                updatedBy
            };
            fs_1.default.writeFileSync(this.configFilePath, JSON.stringify(config, null, 2));
            logger_1.logger.info(`Execution mode saved to ${mode} by ${updatedBy}`);
        }
        catch (error) {
            logger_1.logger.error('Error saving execution mode config:', error);
        }
    }
    getMode() {
        return this.currentMode;
    }
    updateMode(mode, updatedBy) {
        try {
            if (mode === this.currentMode) {
                logger_1.logger.info(`Execution mode already set to ${mode}`);
                return true;
            }
            this.currentMode = mode;
            this.saveExecutionMode(mode, updatedBy);
            this.emit('modeChanged', { mode, updatedBy });
            logger_1.logger.info(`Execution mode updated to ${mode} by ${updatedBy}`);
            return true;
        }
        catch (error) {
            logger_1.logger.error('Error updating execution mode:', error);
            return false;
        }
    }
}
exports.default = ExecutionModeService;
//# sourceMappingURL=executionModeService.js.map