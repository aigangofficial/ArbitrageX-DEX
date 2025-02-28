import { Router } from 'express';
import arbitrageRoutes from './arbitrage';
import healthRoutes from './health';
import alertRoutes from './alert';

const router = Router();

// Mount routes
router.use('/health', healthRoutes);
router.use('/arbitrage', arbitrageRoutes);
router.use('/alerts', alertRoutes);

export default router;
