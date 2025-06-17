import cron from 'node-cron';
import path from 'path';
import { fileURLToPath } from 'url';
import runPythonScript from '../util/pyRunner.js';
import logger from '../util/logger.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const scheduleTeamRanking = () => {
  cron.schedule('0 1 * * 1', async () => {
    logger.info('Cron job initiated: Team Ranking Scraper');
    try {
      const tr_path = path.resolve(__dirname, '..', '..', 'scraper', 'teamRanking.py');
      await runPythonScript(tr_path, 'teamRanking.py');
      logger.info('Team Ranking script completed successfully.');
    } catch (error) {
      logger.error({ error: error.message, stack: error.stack }, 'An error occurred during team ranking cron job execution');
    }
  });
  logger.info('Team ranking cron job scheduled.');
};

export default scheduleTeamRanking;