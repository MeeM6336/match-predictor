import express from 'express';
import cors from 'cors';
import pinoHttp from 'pino-http';
import 'dotenv/config';
import logger from './util/logger.js';
import routes from './routes/index.js';
import errorHandler from './middleware/errorHandler.js';

const app = express();

app.use(cors());
app.use(express.json());

app.use((req, res, next) => {
  req.id = Math.random().toString(36).substring(2, 15);
  next();
});

app.use(pinoHttp({
  logger: logger,
  genReqId: (req) => req.id,
  customProps: (req, res) => ({
    requestId: req.id,
    userAgent: req.headers['user-agent'],
  }),
  customSuccessMessage: function (req, res) {
    if (res.statusCode === 404) return 'Resource not found';
    return `${req.method} request completed`;
  },
  customErrorMessage: function (req, res, error) {
    return `${req.method} request errored with ${error.message}`;
  },
}));

app.use('/', routes);

app.use(errorHandler);

export default app;