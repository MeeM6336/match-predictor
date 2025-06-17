import cron from 'node-cron';
import path from 'path';
import { fileURLToPath } from 'url';
import runPythonScript from '../util/pyRunner.js';
import logger from '../util/logger.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const scheduleMatchOutcome = () => {
  cron.schedule('55 23 * * *', async () => {
    logger.info('Cron job initiated: Match Outcome Scraper');
    try {
      const mo_path = path.resolve(__dirname, '..', '..', 'scraper', 'matchOutcome.py');
      await runPythonScript(mo_path, 'matchOutcome.py');
      logger.info('Match Outcome script completed successfully.');
    } catch (error) {
      logger.error({ error: error.message, stack: error.stack }, 'An error occurred during match outcome cron job execution');
    }
  });
  logger.info('Match outcome cron job scheduled.');
};

export default scheduleMatchOutcome;