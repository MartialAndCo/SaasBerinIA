/**
 * BerinIA WhatsApp Integration
 * Main entry point for the WhatsApp bot
 */

// Load environment variables
require('dotenv').config();

const logger = require('./src/utils/logger');
const whatsappClient = require('./src/services/whatsapp-client');
const apiService = require('./src/services/api-service');
const groupConfig = require('./src/config/groups');

logger.info('Starting BerinIA WhatsApp Integration');
logger.info(`Environment: ${process.env.NODE_ENV}`);

// Log loaded configuration
logger.info(`Community name: ${groupConfig.COMMUNITY_NAME}`);
logger.info(`Configured groups: ${Object.keys(groupConfig.GROUPS).length}`);

// Start the API service
apiService.start();

// Handle process events for graceful shutdown
process.on('SIGTERM', gracefulShutdown);
process.on('SIGINT', gracefulShutdown);

function gracefulShutdown() {
  logger.info('Received shutdown signal');
  
  // Stop API service
  apiService.stop();
  
  // Log final message
  logger.info('BerinIA WhatsApp Integration shut down gracefully');
  process.exit(0);
}

// Log startup complete
logger.info('BerinIA WhatsApp Integration initialization complete');
