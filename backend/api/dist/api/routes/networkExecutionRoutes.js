"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.createNetworkExecutionRouter = exports.ExecutionMode = void 0;
const express_1 = __importDefault(require("express"));
const fs_1 = __importDefault(require("fs"));
const path_1 = __importDefault(require("path"));
const child_process_1 = require("child_process");
const logger_1 = require("../utils/logger");
var ExecutionMode;
(function (ExecutionMode) {
    ExecutionMode["MAINNET"] = "mainnet";
    ExecutionMode["FORK"] = "fork";
})(ExecutionMode || (exports.ExecutionMode = ExecutionMode = {}));
const defaultConfig = {
    mode: ExecutionMode.FORK,
    lastUpdated: new Date().toISOString(),
    updatedBy: 'system'
};
const configFilePath = path_1.default.join(__dirname, '../../config/execution-mode.json');
const readExecutionMode = () => {
    try {
        if (fs_1.default.existsSync(configFilePath)) {
            const configData = fs_1.default.readFileSync(configFilePath, 'utf8');
            return JSON.parse(configData);
        }
    }
    catch (error) {
        logger_1.logger.error('Error reading execution mode config:', error);
    }
    fs_1.default.writeFileSync(configFilePath, JSON.stringify(defaultConfig, null, 2));
    return defaultConfig;
};
const writeExecutionMode = (config) => {
    try {
        fs_1.default.writeFileSync(configFilePath, JSON.stringify(config, null, 2));
    }
    catch (error) {
        logger_1.logger.error('Error writing execution mode config:', error);
        throw new Error('Failed to update execution mode');
    }
};
const updateEnvironmentVariables = (mode) => {
    return new Promise((resolve, reject) => {
        const envFilePath = path_1.default.join(__dirname, '../../../.env');
        fs_1.default.readFile(envFilePath, 'utf8', (err, data) => {
            if (err) {
                logger_1.logger.error('Error reading .env file:', err);
                reject(err);
                return;
            }
            let updatedData;
            if (data.includes('EXECUTION_MODE=')) {
                updatedData = data.replace(/EXECUTION_MODE=\w+/g, `EXECUTION_MODE=${mode}`);
            }
            else {
                updatedData = `${data}\nEXECUTION_MODE=${mode}`;
            }
            fs_1.default.writeFile(envFilePath, updatedData, 'utf8', (writeErr) => {
                if (writeErr) {
                    logger_1.logger.error('Error writing .env file:', writeErr);
                    reject(writeErr);
                    return;
                }
                const scriptPath = mode === ExecutionMode.FORK
                    ? path_1.default.join(__dirname, '../../../scripts/start-fork.ts')
                    : path_1.default.join(__dirname, '../../../scripts/switch-network.ts');
                const command = mode === ExecutionMode.FORK
                    ? `npx ts-node ${scriptPath}`
                    : `npx ts-node ${scriptPath} mainnet`;
                (0, child_process_1.exec)(command, (execErr, stdout, stderr) => {
                    if (execErr) {
                        logger_1.logger.error(`Error executing script: ${execErr.message}`);
                        logger_1.logger.error(`stderr: ${stderr}`);
                        reject(execErr);
                        return;
                    }
                    logger_1.logger.info(`Script output: ${stdout}`);
                    resolve();
                });
            });
        });
    });
};
const createNetworkExecutionRouter = (wsService) => {
    const router = express_1.default.Router();
    router.get('/', async (req, res) => {
        try {
            const config = readExecutionMode();
            return res.json({
                success: true,
                data: config
            });
        }
        catch (error) {
            logger_1.logger.error('Error getting execution mode:', error);
            return res.status(500).json({
                success: false,
                error: 'Failed to get execution mode'
            });
        }
    });
    router.post('/', async (req, res) => {
        try {
            const { mode, updatedBy } = req.body;
            if (!Object.values(ExecutionMode).includes(mode)) {
                return res.status(400).json({
                    success: false,
                    error: `Invalid execution mode. Must be one of: ${Object.values(ExecutionMode).join(', ')}`
                });
            }
            const config = {
                mode,
                lastUpdated: new Date().toISOString(),
                updatedBy: updatedBy || 'api'
            };
            writeExecutionMode(config);
            await updateEnvironmentVariables(mode);
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
        }
        catch (error) {
            logger_1.logger.error('Error updating execution mode:', error);
            return res.status(500).json({
                success: false,
                error: 'Failed to update execution mode'
            });
        }
    });
    return router;
};
exports.createNetworkExecutionRouter = createNetworkExecutionRouter;
exports.default = exports.createNetworkExecutionRouter;
//# sourceMappingURL=networkExecutionRoutes.js.map