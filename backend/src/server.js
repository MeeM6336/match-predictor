import app from './app.js';
import logger from './util/logger.js';
import { connectDb } from './config/db.js';
import startAllCronJobs from './cron/index.js';

const PORT = process.env.PORT || 3000;

connectDb();

app.listen(PORT, () => {
  logger.info(`Server is running on http://localhost:${PORT}`);
  logger.debug('Debug mode is active.');

  startAllCronJobs();
});