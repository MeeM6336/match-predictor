import logger from '../util/logger.js';

const errorHandler = (err, req, res, next) => {
  const statusCode = err.statusCode || 500;
  logger.error(
    {
      requestId: req.id,
      error: err.message,
      stack: err.stack,
      statusCode: statusCode,
      path: req.originalUrl,
      method: req.method
    },
    'Unhandled error in application'
  );
  res.status(statusCode).send('An unexpected error occurred.');
};

export default errorHandler;