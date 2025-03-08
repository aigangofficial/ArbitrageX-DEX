"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.createBypassTokenMiddleware = createBypassTokenMiddleware;
const logger_1 = require("../utils/logger");
function createBypassTokenMiddleware(tokenManager) {
    return async (req, res, next) => {
        const token = req.headers['x-bypass-token'];
        if (!token) {
            return next();
        }
        try {
            const isValid = await tokenManager.validateToken(token);
            if (!isValid) {
                return res.status(401).json({
                    error: 'Invalid or expired bypass token'
                });
            }
            req.bypassToken = token;
            next();
        }
        catch (error) {
            logger_1.logger.error('Error validating bypass token:', error);
            return res.status(401).json({
                error: 'Failed to validate bypass token'
            });
        }
    };
}
//# sourceMappingURL=bypassTokenMiddleware.js.map