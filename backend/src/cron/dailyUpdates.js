import cron from 'node-cron';
import path from 'path';
import { fileURLToPath } from 'url';
import runPythonScript from '../util/pyRunner.js';
import logger from '../util/logger.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const scheduleDailyUpdates = () => {
  cron.schedule('0 23 * * *', async () => {
    logger.info('Cron job initiated: Daily match updates and predictions');
    try {
      const um_path = path.resolve(__dirname, '..', '..', 'scraper', 'upcomingMatches.py');
      await runPythonScript(um_path, 'upcomingMatches.py');

      const lrp_path = path.resolve(__dirname, '..', '..', 'ml_model', 'lr_predict.py');
      await runPythonScript(lrp_path, 'lr_predict.py');

      const nnp_path = path.resolve(__dirname, '..', '..', 'ml_model', 'nn_predict.py');
      await runPythonScript(nnp_path, 'nn_predict.py');

      logger.info('All daily prediction scripts completed successfully.');
    } catch (error) {
      logger.error({ error: error.message, stack: error.stack }, 'An error occurred during daily cron job execution');
    }
  });
  logger.info('Daily match update cron job scheduled.');
};

export default scheduleDailyUpdates;