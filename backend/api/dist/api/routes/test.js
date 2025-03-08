"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = require("express");
const errorHandler_1 = require("../middleware/errorHandler");
const router = (0, express_1.Router)();
router.get('/error/validation', (_req, res, next) => {
    try {
        throw new errorHandler_1.ValidationError('Test validation error');
    }
    catch (error) {
        next(error);
    }
});
router.get('/error/auth', (_req, res, next) => {
    try {
        throw new errorHandler_1.AuthenticationError('Test authentication error');
    }
    catch (error) {
        next(error);
    }
});
router.get('/error/unknown', (_req, res, next) => {
    try {
        throw new Error('Test unknown error');
    }
    catch (error) {
        next(error);
    }
});
router.get('/test-rate-limit', (_req, res) => {
    res.json({ message: 'Rate limit test endpoint' });
});
router.get('/test', (_req, res) => {
    res.json({ message: 'Test route working' });
});
exports.default = router;
//# sourceMappingURL=test.js.map