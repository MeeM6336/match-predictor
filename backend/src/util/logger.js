import pino from 'pino'

const level = process.env.NODE_ENV === 'production' ? 'info' : 'debug';

const logger = pino({
  level: level,
  base: {
    pid: process.pid,
  },
  messageKey: 'message',
  timestamp: pino.stdTimeFunctions.isoTime,
  transport: {
    target: 'pino-pretty',
    options: {
      colorize: true,
      translateTime: 'SYS:HH:MM:ss Z',
      ignore: 'pid,hostname',
    }
  }
});

export default logger;