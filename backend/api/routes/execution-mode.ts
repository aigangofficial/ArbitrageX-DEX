import { Router } from 'express';
import { logger } from '../utils/logger';
import { ExecutionMode } from '../../execution/tradeExecutor';
import ExecutionModeService from '../../services/executionModeService';

const router = Router();
const executionModeService = ExecutionModeService.getInstance();

/**
 * @route GET /api/v1/execution-mode
 * @desc Get the current execution mode
 * @access Public
 */
router.get('/', (req, res) => {
  try {
    const mode = executionModeService.getMode();
    
    return res.json({
      success: true,
      data: {
        mode
      }
    });
  } catch (error) {
    logger.error('Error getting execution mode:', error);
    return res.status(500).json({
      success: false,
      error: 'Failed to get execution mode'
    });
  }
});

/**
 * @route POST /api/v1/execution-mode
 * @desc Update the execution mode
 * @access Protected
 */
router.post('/', (req, res) => {
  try {
    const { mode } = req.body;

    // Validate the mode
    if (!mode || !Object.values(ExecutionMode).includes(mode as ExecutionMode)) {
      return res.status(400).json({
        success: false,
        error: `Invalid execution mode. Must be one of: ${Object.values(ExecutionMode).join(', ')}`
      });
    }

    // Update the execution mode
    const success = executionModeService.updateMode(
      mode as ExecutionMode, 
      req.body.updatedBy || 'api'
    );

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
  } catch (error) {
    logger.error('Error updating execution mode:', error);
    return res.status(500).json({
      success: false,
      error: 'Failed to update execution mode'
    });
  }
});

export default router; 