const winston = require('winston');
const path = require('path');
const fs = require('fs');
require('dotenv').config();

// Ensure logs directory exists
const logDir = path.dirname(process.env.LOG_FILE || 'logs/whatsapp-bot.log');
if (!fs.existsSync(logDir)) {
  fs.mkdirSync(logDir, { recursive: true });
}

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  defaultMeta: { service: 'whatsapp-bot' },
  transports: [
    // Write to console
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.timestamp(),
        winston.format.printf(({ timestamp, level, message, ...meta }) => {
          return `${timestamp} ${level}: ${message} ${Object.keys(meta).length ? JSON.stringify(meta, null, 2) : ''}`;
        })
      )
    }),
    // Write to log file
    new winston.transports.File({ 
      filename: process.env.LOG_FILE || 'logs/whatsapp-bot.log'
    })
  ]
});

module.exports = logger;
