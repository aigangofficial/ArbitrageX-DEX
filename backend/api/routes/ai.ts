import { Router } from 'express';
import { AIService } from '../services/ai';
import { logger } from '../utils/logger';

const router = Router();

router.get('/status', async (_req, res) => {
    try {
        const status = await AIService.getStatus();
        return res.json({
            success: true,
            data: {
                status,
                model_version: process.env.AI_MODEL_VERSION || '1.0.0'
            }
        });
    } catch (error) {
        logger.error('Failed to get AI status:', error);
        return res.status(500).json({
            success: false,
            error: 'Failed to get AI status'
        });
    }
});

router.post('/predict', async (req, res) => {
    try {
        const { price, volume, timestamp } = req.body;

        if (!price || !volume || !timestamp) {
            return res.status(400).json({
                success: false,
                error: 'Missing required fields'
            });
        }

        if (isNaN(parseFloat(price))) {
            return res.status(400).json({
                success: false,
                error: 'Invalid price value'
            });
        }

        // Mock prediction for now
        return res.json({
            success: true,
            prediction: {
                direction: Math.random() > 0.5 ? 'up' : 'down',
                confidence: Math.random(),
                timestamp: new Date().toISOString()
            }
        });
    } catch (error) {
        logger.error('Failed to generate prediction:', error);
        return res.status(500).json({
            success: false,
            error: 'Failed to generate prediction'
        });
    }
});

export default router;