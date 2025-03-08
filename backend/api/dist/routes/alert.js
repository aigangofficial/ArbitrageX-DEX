"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = require("express");
const errorHandler_1 = require("../middleware/errorHandler");
const logger_1 = require("../utils/logger");
const rateLimit_1 = require("../middleware/rateLimit");
const router = (0, express_1.Router)();
// Trigger manual cleanup with options
router.post('/cleanup', rateLimit_1.alertCleanupLimiter, async (req, res, next) => {
    try {
        const { dryRun = false, retentionDays, severity, metric, startTime, endTime } = req.body;
        const alertService = req.app.get('alertService');
        // Set dry run mode if requested
        alertService.setDryRun(dryRun);
        // Build cleanup options
        const cleanupOptions = {
            retentionDays: retentionDays ? Number(retentionDays) : undefined,
            severity,
            metric,
            startTime: startTime ? new Date(startTime).getTime() : undefined,
            endTime: endTime ? new Date(endTime).getTime() : undefined
        };
        // Validate options
        if (retentionDays && (isNaN(retentionDays) || retentionDays < 0)) {
            throw new errorHandler_1.ValidationError('Invalid retention days value');
        }
        if (startTime && isNaN(new Date(startTime).getTime())) {
            throw new errorHandler_1.ValidationError('Invalid start time');
        }
        if (endTime && isNaN(new Date(endTime).getTime())) {
            throw new errorHandler_1.ValidationError('Invalid end time');
        }
        // Log cleanup request
        logger_1.logger.info('Manual cleanup requested', {
            dryRun,
            options: cleanupOptions
        });
        // Trigger cleanup
        await alertService.scheduleCleanup(cleanupOptions);
        res.json({
            success: true,
            message: dryRun ? 'Dry run cleanup completed' : 'Cleanup scheduled successfully',
            options: cleanupOptions
        });
    }
    catch (error) {
        next(error);
    }
});
// Get cleanup metrics
router.get('/metrics', rateLimit_1.alertMetricsLimiter, async (req, res, next) => {
    try {
        const alertService = req.app.get('alertService');
        const metrics = await alertService.getCleanupMetrics();
        res.json({
            success: true,
            data: metrics
        });
    }
    catch (error) {
        next(error);
    }
});
exports.default = router;
//# sourceMappingURL=alert.js.map