"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.createAdminRouter = void 0;
const express_1 = require("express");
const errorHandler_1 = require("../middleware/errorHandler");
const router = (0, express_1.Router)();
const createAdminRouter = (tokenManager) => {
    // Generate a new bypass token
    router.post('/bypass-token', async (req, res, next) => {
        try {
            const { subject, scope } = req.body;
            if (!subject) {
                throw new errorHandler_1.AuthenticationError('Subject is required');
            }
            // Validate scope format if provided
            if (scope && !Array.isArray(scope)) {
                throw new errorHandler_1.AuthenticationError('Scope must be an array of endpoint patterns');
            }
            // Generate token with scope
            const token = await tokenManager.generateToken(subject, scope || ['*'] // Default to full access if no scope provided
            );
            res.json({
                success: true,
                token,
                details: {
                    subject,
                    scope: scope || ['*'],
                    expiresIn: '1h',
                    maxUsage: 1000
                }
            });
        }
        catch (error) {
            next(error);
        }
    });
    // Revoke a bypass token
    router.delete('/bypass-token', async (req, res, next) => {
        try {
            const { token } = req.body;
            if (!token) {
                throw new errorHandler_1.AuthenticationError('Token is required');
            }
            const success = await tokenManager.revokeToken(token);
            if (!success) {
                throw new errorHandler_1.AuthenticationError('Failed to revoke token');
            }
            res.json({
                success: true,
                message: 'Token revoked successfully'
            });
        }
        catch (error) {
            next(error);
        }
    });
    // Get token usage statistics
    router.get('/bypass-token/stats', async (req, res, next) => {
        try {
            const token = req.headers['x-bypass-token'];
            if (!token || typeof token !== 'string') {
                throw new errorHandler_1.AuthenticationError('Token is required');
            }
            const stats = await tokenManager.getTokenStats(token);
            // Add breach detection info to stats
            const breachRisk = stats.uniqueIPs > 2 ? 'high' :
                stats.uniqueIPs > 1 ? 'medium' :
                    'low';
            res.json({
                success: true,
                stats: {
                    ...stats,
                    securityMetrics: {
                        breachRisk,
                        activeIPCount: stats.uniqueIPs,
                        unusualActivityDetected: breachRisk === 'high'
                    }
                }
            });
        }
        catch (error) {
            next(error);
        }
    });
    // List all active tokens (admin only)
    router.get('/bypass-tokens', async (_req, res, next) => {
        try {
            const tokens = await tokenManager.listActiveTokens();
            res.json({
                success: true,
                tokens
            });
        }
        catch (error) {
            next(error);
        }
    });
    return router;
};
exports.createAdminRouter = createAdminRouter;
//# sourceMappingURL=admin.js.map