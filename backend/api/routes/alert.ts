import { Router } from 'express';
import { ValidationError } from '../middleware/errorHandler';
import { AlertService } from '../services/alertService';
import { logger } from '../utils/logger';
import { alertCleanupLimiter, alertMetricsLimiter } from '../middleware/rateLimit';

const router = Router();

// Trigger manual cleanup with options
router.post('/cleanup', alertCleanupLimiter, async (req, res, next) => {
  try {
    const {
      dryRun = false,
      retentionDays,
      severity,
      metric,
      startTime,
      endTime
    } = req.body;

    const alertService = req.app.get('alertService') as AlertService;
    
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
      throw new ValidationError('Invalid retention days value');
    }

    if (startTime && isNaN(new Date(startTime).getTime())) {
      throw new ValidationError('Invalid start time');
    }

    if (endTime && isNaN(new Date(endTime).getTime())) {
      throw new ValidationError('Invalid end time');
    }

    // Log cleanup request
    logger.info('Manual cleanup requested', {
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
  } catch (error) {
    next(error);
  }
});

// Get cleanup metrics
router.get('/metrics', alertMetricsLimiter, async (req, res, next) => {
  try {
    const alertService = req.app.get('alertService') as AlertService;
    
    const metrics = await alertService.getCleanupMetrics();
    
    res.json({
      success: true,
      data: metrics
    });
  } catch (error) {
    next(error);
  }
});

export default router; 