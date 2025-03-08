"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AIService = void 0;
const logger_1 = require("../utils/logger");
class AIService {
    static async getStatus() {
        try {
            return process.env.AI_MODEL_PATH ? 'ready' : 'not_loaded';
        }
        catch (error) {
            logger_1.logger.error('Error checking AI model status:', error);
            return 'error';
        }
    }
}
exports.AIService = AIService;
//# sourceMappingURL=ai.js.map