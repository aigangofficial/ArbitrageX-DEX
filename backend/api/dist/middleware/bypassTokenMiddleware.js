"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.createBypassTokenMiddleware = void 0;
const logger_1 = require("../utils/logger");
const errorHandler_1 = require("./errorHandler");
const createBypassTokenMiddleware = (tokenManager) => {
    return async (req, res, next) => {
        const token = req.headers['x-bypass-token'];
        if (!token || typeof token !== 'string') {
            return next();
        }
        try {
            // Get endpoint path for scope checking
            const endpoint = req.path;
            const clientIp = req.ip || req.connection.remoteAddress || 'unknown';
            const isValid = await tokenManager.verifyToken(token, endpoint);
            if (isValid) {
                // Mark request to bypass rate limit
                req.bypassRateLimit = true;
                logger_1.logger.debug('Rate limit bypassed with valid token', {
                    ip: clientIp,
                    path: endpoint
                });
            }
            else {
                // If token is invalid but exists, treat as auth error
                throw new errorHandler_1.AuthenticationError('Invalid or expired bypass token');
            }
            next();
        }
        catch (error) {
            logger_1.logger.error('Error validating bypass token', {
                error,
                path: req.path,
                ip: req.ip || req.connection.remoteAddress || 'unknown'
            });
            next(new errorHandler_1.AuthenticationError('Invalid bypass token'));
        }
    };
};
exports.createBypassTokenMiddleware = createBypassTokenMiddleware;
//# sourceMappingURL=bypassTokenMiddleware.js.map