import express from 'express';
import cors from 'cors';
import mysql from 'mysql2';
import cron from 'node-cron';
import path from 'path';
import { spawn } from 'child_process'
import { fileURLToPath } from 'url';
import 'dotenv/config';


const app = express();

app.use(cors());
app.use(express.json());

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const db = mysql.createConnection({
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
});

// Connect to the database
db.connect((err) => {
  if (err) {
    console.error("CS2_DB connection failed:", err);
    process.exit(1);
  }
  console.log("Connected to CS2_DB");
});

// Inserts today's matches into DB
cron.schedule('0 23 * * *', () => {
  const um_path = path.resolve(__dirname, 'scraper', 'upcomingMatches.py');
  const um_python = spawn('python', [um_path])

  um_python.stdout.on('data', (data) => {
    console.log(`Python stdout: ${data.toString()}`);
  });

  um_python.stderr.on('data', (data) => {
    console.error(`Python stderr: ${data.toString()}`);
  });

  um_python.on('close', (code) => {
    console.log(`Python script (upcomingMatches) exited with code ${code}`);

    const lrp_path = path.resolve(__dirname, 'ml_model', 'lr_predict.py');
    const lrp_python = spawn('python', [lrp_path])

    lrp_python.stdout.on('data', (data) => {
      console.log(`Python stdout: ${data.toString()}`);
    });

    lrp_python.stderr.on('data', (data) => {
      console.error(`Python stderr: ${data.toString()}`);
    });

    lrp_python.on('close', (code) => {
      console.log(`Python script (lr_predict) exited with code ${code}`);
    });
  });
});

cron.schedule('45 23 * * *', () => {
  const mo_path = path.resolve(__dirname, 'scraper', 'matchOutcome.py')
  const mo_python = spawn('python', [mo_path])

  mo_python.stdout.on('data', (data) => {
    console.log(`Python stdout: ${data.toString()}`);
  });

  mo_python.stderr.on('data', (data) => {
    console.error(`Python stderr: ${data}`);
  });

  mo_python.on('close', (code) => {
    console.log(`Python script (matchOutcome) exited with code ${code}`);
  });
});

cron.schedule('0 1 * * 1', () => {
  const tr_path = path.resolve(__dirname, 'scraper', 'teamRanking.py')
  const tr_python = spawn('python', [tr_path])

  tr_python.stdout.on('data', (data) => {
    console.log(`Python stdout: ${data.toString()}`);
  });

  tr_python.stderr.on('data', (data) => {
    console.error(`Python stderr: ${data}`);
  });

  tr_python.on('close', (code) => {
    console.log(`Python script (teamRanking) exited with code ${code}`);
  });
});

// Route to get machine learning model metrics
app.get('/metrics/:name', (req, res) => {
  const modelName = decodeURIComponent(req.params.name);
  const query = 'SELECT * FROM model WHERE model_name = ?';
  db.query(query, [modelName], (err, result) => {
    if (err){
      console.log(err);
      return res.status(500).send("Server error");

    } else {
      return res.json(result);
    };
  });
});

// Route to get all of dataset's feature vectors
app.get('/livefeaturevectors', (req, res) => {
  const query = `SELECT * FROM live_feature_vectors`;

  db.query(query, (err, result) => {
    if (err) {
      console.error(err);
      return res.status(500).send("Server error");
    }
    return res.json(result);
  });
});


// Route to get training dataset stats
app.get('/trainingdatasetstats', (req, res) => {
  const matchCountQuery = `SELECT
    (SELECT COUNT(*) FROM cs2_data.matches) AS match_row_count,
    (SELECT MIN(date) FROM cs2_data.matches) as min_date,
    (SELECT MAX(date) FROM CS2_data.matches) as max_date
    `;
  const featureStatsQuery = `SELECT
    (SELECT COUNT(*) FROM cs2_data.feature_vectors) AS feature_row_count,
    (SELECT COUNT(*) FROM information_schema.columns 
    WHERE table_schema = 'cs2_data' AND table_name = 'feature_vectors') AS feature_count
  `;
  db.query(matchCountQuery, (err, matchStatsResults) => {
    if (err) {
      console.error(err);
      return res.status(500).send("Server error");
    };

    db.query(featureStatsQuery, (err, featureStatsResults) => {
      if (err) {
        console.error(err);
        return res.status(500).send("Server error");
      };
      
      res.json({
        match_row_count: matchStatsResults[0].match_row_count,
        match_min_date: matchStatsResults[0].min_date,
        match_max_date: matchStatsResults[0].max_date,
        feature_row_count: featureStatsResults[0].feature_row_count,
        feature_count: featureStatsResults[0].feature_count
      });
    });
  });
});

// Route to get live dataset stats
app.get('/livedatasetstats', (req, res) => {
  const matchCountQuery = `SELECT
    (SELECT COUNT(*) FROM cs2_data.upcoming_matches) AS match_row_count,
    (SELECT MIN(date) FROM cs2_data.upcoming_matches) as min_date,
    (SELECT MAX(date) FROM CS2_data.upcoming_matches) as max_date
    `;
  const featureStatsQuery = `SELECT
    (SELECT COUNT(*) FROM cs2_data.live_feature_vectors) AS feature_row_count,
    (SELECT COUNT(*) FROM information_schema.columns 
    WHERE table_schema = 'cs2_data' AND table_name = 'live_feature_vectors') AS feature_count
  `;
  db.query(matchCountQuery, (err, matchStatsResults) => {
    if (err) {
      console.error(err);
      return res.status(500).send("Server error");
    };

    db.query(featureStatsQuery, (err, featureStatsResults) => {
      if (err) {
        console.error(err);
        return res.status(500).send("Server error");
      };
      
      res.json({
        match_row_count: matchStatsResults[0].match_row_count,
        match_min_date: matchStatsResults[0].min_date,
        match_max_date: matchStatsResults[0].max_date,
        feature_row_count: featureStatsResults[0].feature_row_count,
        feature_count: featureStatsResults[0].feature_count
      });
    });
  });
});

// Route to get recent matches
app.get('/upcoming', (req, res) => {
  const query = 'SELECT * FROM upcoming_matches ORDER BY date DESC'
  db.query(query, (err, result) => {
    if (err) {
      console.error(err);
      return res.status(500).send("Server error");
    } else {
      return res.json(result);
    }
  });
});

// Route to get stats for recent matches
app.get('/upcomingstats', (req, res) => {
  const query = 'SELECT outcome, actual_outcome, confidence FROM upcoming_matches WHERE outcome IS NOT NULL and actual_outcome IS NOT NULL'
  db.query(query, (err, result) => {
    if (err) {
      console.error(err);
      return res.status(500).send("Server error");
    } else {
      return res.json(result);
    }
  });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});