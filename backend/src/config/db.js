import mysql from 'mysql2';
import logger from '../util/logger.js';

const db = mysql.createConnection({
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
});

const connectDb = () => {
  db.connect((err) => {
    if (err) {
      logger.fatal({ error: err }, "CS2_DB connection failed"); 
      process.exit(1);
    }
    logger.info("Connected to CS2_DB");
  });
};

export { db, connectDb };