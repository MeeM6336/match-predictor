import express from 'express';
import logger from '../util/logger.js';
import { db } from '../config/db.js';

const router = express.Router();

// Route to get recent matches
router.get('/upcoming/:model_id', (req, res) => {
  const modelId = decodeURIComponent(req.params.model_id);
  const query = `
    SELECT
      um.match_id,
      um.team_a,
      um.team_b,
      um.date,
      um.tournament_name,
      um.tournament_type,
      um.best_of,
      um.actual_outcome,
      mp.prediction,
      mp.confidence,
      mp.model_id
    FROM upcoming_matches um
    LEFT JOIN match_predictions mp ON um.match_id = mp.match_id
    WHERE mp.model_id = ? OR mp.model_id IS NULL
    ORDER BY um.date DESC`;

  db.query(query, [modelId], (err, result) => {
    if (err) {
      logger.error({ requestId: req.id, error: err.message, stack: err.stack, modelId }, 'Error fetching upcoming matches');
      return res.status(500).send("Server error");
    } else {
      return res.json(result);
    }
  });
});

// Route to get stats for recent matches
router.get('/upcomingstats/:model_id', (req, res) => {
  const model_id = decodeURIComponent(req.params.model_id);
  const query = `
    SELECT
      mp.prediction,
      um.actual_outcome,
      mp.confidence
    FROM upcoming_matches um
    JOIN match_predictions mp ON um.match_id = mp.match_id
    WHERE um.actual_outcome IS NOT NULL AND mp.model_id = ?`;

  db.query(query, [model_id], (err, result) => {
    if (err) {
      logger.error({ requestId: req.id, error: err.message, stack: err.stack, model_id }, 'Error fetching upcoming match stats');
      return res.status(500).send("Server error");
    } else {
      return res.json(result);
    }
  });
});

// Route to get models
router.get('/models', (req, res) => {
  const query = 'SELECT model_name, model_id FROM model';
  db.query(query, (err, result) => {
    if (err) {
      logger.error({ requestId: req.id, error: err.message, stack: err.stack }, 'Error fetching models');
      return res.status(500).send("Server error");
    } else {
      return res.json(result);
    }
  });
});

export default router;