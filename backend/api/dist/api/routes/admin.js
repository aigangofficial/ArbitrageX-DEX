"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.createAdminRouter = void 0;
const express_1 = require("express");
const errorHandler_1 = require("../middleware/errorHandler");
const router = (0, express_1.Router)();
const createAdminRouter = (tokenManager) => {
    router.post('/bypass-token', async (req, res, next) => {
        try {
            const token = await tokenManager.generateToken();
            res.json({
                success: true,
                token,
                details: {
                    expiresIn: '1h',
                    maxUsage: 1000
                }
            });
        }
        catch (error) {
            next(error);
        }
    });
    router.get('/bypass-token/check', async (req, res, next) => {
        try {
            const token = req.headers['x-bypass-token'];
            if (!token || typeof token !== 'string') {
                throw new errorHandler_1.AuthenticationError('Token is required');
            }
            const isValid = await tokenManager.validateToken(token);
            res.json({
                success: true,
                isValid
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