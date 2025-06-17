import express from 'express';
import logger from '../util/logger.js';
import { db } from '../config/db.js';

const router = express.Router();

// Route to get machine learning model metrics
router.get('/metrics/:name', (req, res) => {
  const modelName = decodeURIComponent(req.params.name);
  const query = 'SELECT * FROM model WHERE model_name = ?';
  db.query(query, [modelName], (err, result) => {
    if (err) {
      logger.error({ requestId: req.id, error: err.message, stack: err.stack, modelName }, 'Error fetching model metrics');
      return res.status(500).send("Server error");
    } else {
      return res.json(result);
    }
  });
});

// Route to get all of dataset's feature vectors
router.get('/livefeaturevectors', (req, res) => {
  const query = `SELECT * FROM live_feature_vectors`;
  db.query(query, (err, result) => {
    if (err) {
      logger.error({ requestId: req.id, error: err.message, stack: err.stack }, 'Error fetching live feature vectors');
      return res.status(500).send("Server error");
    }
    return res.json(result);
  });
});

// Route to get training dataset stats
router.get('/trainingdatasetstats/:model_id', (req, res) => {
  const model_id = decodeURIComponent(req.params.model_id);
  const matchCountQuery = `SELECT
    (SELECT COUNT(*) FROM cs2_data.matches) AS match_row_count,
    (SELECT MIN(date) FROM cs2_data.matches) as min_date,
    (SELECT MAX(date) FROM CS2_data.matches) as max_date
    `;
  const featureStatsQuery = `SELECT
    (SELECT COUNT(*) FROM cs2_data.feature_vectors WHERE model_id = ?) AS feature_row_count`;

  const firstRowQuery = `SELECT * FROM cs2_data.feature_vectors WHERE model_id = ? LIMIT 1`;

  // Use Promise.all for parallel queries and better error handling
  Promise.all([
    new Promise((resolve, reject) => db.query(matchCountQuery, (err, res) => err ? reject(err) : resolve(res))),
    new Promise((resolve, reject) => db.query(featureStatsQuery, [model_id], (err, res) => err ? reject(err) : resolve(res))),
    new Promise((resolve, reject) => db.query(firstRowQuery, [model_id], (err, res) => err ? reject(err) : resolve(res)))
  ])
  .then(([matchStatsResults, featureStatsResults, firstRowResults]) => {
    const firstRow = firstRowResults[0];
    let count = 0;
    if (firstRow) {
      count = Object.keys(firstRow).reduce((acc, key) => {
        // Exclude 'id' and 'model_id' columns from the feature count if they are not features
        if (key !== 'id' && key !== 'model_id' && firstRow[key] !== null && firstRow[key] !== undefined) {
          return acc + 1;
        }
        return acc;
      }, 0);
    }

    res.json({
      match_row_count: matchStatsResults[0]?.match_row_count || 0,
      match_min_date: matchStatsResults[0]?.min_date || null,
      match_max_date: matchStatsResults[0]?.max_date || null,
      feature_row_count: featureStatsResults[0]?.feature_row_count || 0,
      feature_count: count
    });
  })
  .catch(err => {
    logger.error({ requestId: req.id, error: err.message, stack: err.stack, model_id }, 'Error fetching training dataset stats');
    res.status(500).send("Server error");
  });
});

// Route to get live dataset stats
router.get('/livedatasetstats/:model_id', (req, res) => {
  const model_id = decodeURIComponent(req.params.model_id);
  const matchCountQuery = `SELECT
    (SELECT COUNT(*) FROM cs2_data.upcoming_matches) AS match_row_count,
    (SELECT MIN(date) FROM cs2_data.upcoming_matches) as min_date,
    (SELECT MAX(date) FROM CS2_data.upcoming_matches) as max_date
    `;
  const featureStatsQuery = `SELECT
    (SELECT COUNT(*) FROM cs2_data.live_feature_vectors WHERE model_id = ?) AS feature_row_count`;

  const firstRowQuery = `SELECT * FROM cs2_data.live_feature_vectors WHERE model_id = ? LIMIT 1`;

  Promise.all([
    new Promise((resolve, reject) => db.query(matchCountQuery, (err, res) => err ? reject(err) : resolve(res))),
    new Promise((resolve, reject) => db.query(featureStatsQuery, [model_id], (err, res) => err ? reject(err) : resolve(res))),
    new Promise((resolve, reject) => db.query(firstRowQuery, [model_id], (err, res) => err ? reject(err) : resolve(res)))
  ])
  .then(([matchStatsResults, featureStatsResults, firstRowResults]) => {
    const firstRow = firstRowResults[0];
    let count = 0;
    if (firstRow) {
      count = Object.keys(firstRow).reduce((acc, key) => {
        // Exclude 'id' and 'model_id' columns from the feature count if they are not features
        if (key !== 'id' && key !== 'model_id' && firstRow[key] !== null && firstRow[key] !== undefined) {
          return acc + 1;
        }
        return acc;
      }, 0);
    }

    res.json({
      match_row_count: matchStatsResults[0]?.match_row_count || 0,
      match_min_date: matchStatsResults[0]?.min_date || null,
      match_max_date: matchStatsResults[0]?.max_date || null,
      feature_row_count: featureStatsResults[0]?.feature_row_count || 0,
      feature_count: count
    });
  })
  .catch(err => {
    logger.error({ requestId: req.id, error: err.message, stack: err.stack, model_id }, 'Error fetching live dataset stats');
    res.status(500).send("Server error");
  });
});

export default router;