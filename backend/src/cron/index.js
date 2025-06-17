import logger from '../util/logger.js';
import scheduleDailyUpdates from './dailyUpdates.js';
import scheduleMatchOutcome from './matchOutcome.js';
import scheduleTeamRanking from './teamRanking.js';

const startAllCronJobs = () => {
  logger.info('Starting all scheduled cron jobs...');
  scheduleDailyUpdates();
  scheduleMatchOutcome();
  scheduleTeamRanking();
  logger.info('All cron jobs initialized.');
};

export default startAllCronJobs;