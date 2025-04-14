import express from 'express';
import cors from 'cors';
import mysql from 'mysql2';
import cron from 'node-cron';
import { spawn } from 'child_process'
import 'dotenv/config';


const app = express();

app.use(cors());
app.use(express.json());

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
cron.schedule('0 2 * * *', () => {
  const python = spawn('python3', ['scraper/upcomingMatches.py'])

  python.stderr.on('data', (data) => {
    console.error(`Python stderr: ${data}`);
  });

  python.on('close', (code) => {
    console.log(`Python script (upcomingMatches) exited with code ${code}`);
  });
})

app.get('/evaluate_model')

// Route to get recent matches
app.get('/upcoming', (req, res) => {
  const query = 'SELECT * FROM upcoming_matches'
  db.query(query, (err, result) => {
    if (err) {
      console.error(err);
      res.status(500).send("Server error");
    } else {
      res.json(result);
    }
  });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});