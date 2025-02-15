import { Router } from 'express';
import { AuthenticationError, ValidationError } from '../middleware/errorHandler';

const router = Router();

// Test validation error
router.get('/error/validation', (_req, res, next) => {
  try {
    throw new ValidationError('Test validation error', { field: 'test' });
  } catch (error) {
    next(error);
  }
});

// Test authentication error
router.get('/error/auth', (_req, res, next) => {
  try {
    throw new AuthenticationError('Test authentication error');
  } catch (error) {
    next(error);
  }
});

// Test unknown error
router.get('/error/unknown', (_req, res, next) => {
  try {
    throw new Error('Test unknown error');
  } catch (error) {
    next(error);
  }
});

// Test rate limiting
router.get('/test-rate-limit', (_req, res) => {
  res.json({ message: 'Rate limit test endpoint' });
});

export default router;
