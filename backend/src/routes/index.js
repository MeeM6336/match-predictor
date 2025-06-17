import express from 'express';
import metricsRoutes from './metricsRoutes.js';
import matchRoutes from './matchRoutes.js';

const router = express.Router();

router.use('/', metricsRoutes);
router.use('/', matchRoutes); 

export default router;