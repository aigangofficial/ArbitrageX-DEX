"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = require("express");
const logger_1 = require("../utils/logger");
const tradeExecutor_1 = require("../../execution/tradeExecutor");
const executionModeService_1 = __importDefault(require("../../services/executionModeService"));
const router = (0, express_1.Router)();
const executionModeService = executionModeService_1.default.getInstance();
router.get('/', (req, res) => {
    try {
        const mode = executionModeService.getMode();
        return res.json({
            success: true,
            data: {
                mode
            }
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
router.post('/', (req, res) => {
    try {
        const { mode } = req.body;
        if (!mode || !Object.values(tradeExecutor_1.ExecutionMode).includes(mode)) {
            return res.status(400).json({
                success: false,
                error: `Invalid execution mode. Must be one of: ${Object.values(tradeExecutor_1.ExecutionMode).join(', ')}`
            });
        }
        const success = executionModeService.updateMode(mode, req.body.updatedBy || 'api');
        if (!success) {
            return res.status(500).json({
                success: false,
                error: 'Failed to update execution mode'
            });
        }
        return res.json({
            success: true,
            data: {
                mode: executionModeService.getMode()
            }
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
exports.default = router;
//# sourceMappingURL=execution-mode.js.map