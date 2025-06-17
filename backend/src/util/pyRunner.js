import { spawn } from 'child_process';
import logger from './logger.js';


/**
 * Runs python scripts
 *
 * @param {string} scriptPath - Absolute path of script.
 * @param {string} scriptName - Name of script.
 */
function runPythonScript(scriptPath, scriptName) {
  return new Promise((resolve, reject) => {
    logger.info(`Starting Python script: ${scriptName} (${scriptPath})`);
    const pythonProcess = spawn('python', [scriptPath]);

    pythonProcess.stdout.on('data', (data) => {
      logger.info(`${scriptName} (stdout): ${data.toString().trim()}`);
    });

    pythonProcess.stderr.on('data', (data) => {
      logger.error(`${scriptName} (stderr): ${data.toString().trim()}`);
    });

    pythonProcess.on('close', (code) => {
      logger.info(`${scriptName} exited with code ${code}`);
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`${scriptName} exited with non-zero code ${code}`));
      }
    });

    pythonProcess.on('error', (err) => {
      logger.error(`${scriptName} failed to start or encountered an error:`, err);
      reject(err);
    });
  });
}

export default runPythonScript;