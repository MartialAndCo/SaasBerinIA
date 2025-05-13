const express = require('express');
const logger = require('../utils/logger');
const whatsappClient = require('./whatsapp-client');

class ApiService {
  constructor() {
    this.app = express();
    this.port = process.env.API_PORT || 3000;
    this.host = process.env.API_HOST || '127.0.0.1';
    this.setupMiddleware();
    this.setupRoutes();
  }

  setupMiddleware() {
    this.app.use(express.json());
    
    // Logging middleware
    this.app.use((req, res, next) => {
      logger.info(`${req.method} ${req.url}`);
      next();
    });

    // Error handler
    this.app.use((err, req, res, next) => {
      logger.error(`API error: ${err.message}`);
      res.status(500).json({ error: 'Internal server error' });
    });
  }

  setupRoutes() {
    // Health check endpoint
    this.app.get('/health', (req, res) => {
      res.status(200).json({ status: 'ok' });
    });

    // Send message to a group endpoint
    this.app.post('/send', async (req, res) => {
      try {
        const { group, message } = req.body;
        
        if (!group || !message) {
          return res.status(400).json({ error: 'Missing group or message parameter' });
        }

        logger.info(`Request to send message to group: ${group}`);
        
        // Find the group in the community
        const groupId = await whatsappClient.findGroupInCommunity(group);
        
        if (!groupId) {
          return res.status(404).json({ error: `Group "${group}" not found (checked both in communities and standalone groups)` });
        }
        
        // Send the message
        await whatsappClient.sendMessage(groupId, message);
        
        return res.status(200).json({ success: true, message: 'Message sent successfully' });
      } catch (error) {
        logger.error(`Error sending message: ${error.message}`);
        return res.status(500).json({ error: error.message });
      }
    });

    // Get community and groups info
    this.app.get('/community-info', async (req, res) => {
      try {
        const communityId = whatsappClient.communityId;
        
        if (!communityId) {
          return res.status(404).json({ error: 'BerinIA community not found' });
        }
        
        const chats = await whatsappClient.client.getChats();
        const groups = [];
        
        for (const chat of chats) {
          if (chat.isGroup) {
            try {
              const metadata = await whatsappClient.client.getGroupMetadata(chat.id._serialized);
              if (metadata.parentGroupId === communityId) {
                groups.push({
                  id: chat.id._serialized,
                  name: chat.name,
                  participants: metadata.participants.length
                });
              }
            } catch (err) {
              logger.error(`Error getting metadata for group ${chat.name}: ${err.message}`);
            }
          }
        }
        
        return res.status(200).json({
          communityId: communityId,
          groups: groups
        });
      } catch (error) {
        logger.error(`Error fetching community info: ${error.message}`);
        return res.status(500).json({ error: error.message });
      }
    });
    
    // Get all groups info (including standalone groups)
    this.app.get('/all-groups', async (req, res) => {
      try {
        const chats = await whatsappClient.client.getChats();
        const allGroups = [];
        const communities = [];
        
        // Identify communities
        for (const chat of chats) {
          if (chat.isCommunity) {
            communities.push({
              id: chat.id._serialized,
              name: chat.name
            });
          }
        }
        
        // Identify all groups and their metadata
        for (const chat of chats) {
          if (chat.isGroup) {
            try {
              const metadata = await whatsappClient.client.getGroupMetadata(chat.id._serialized);
              const groupInfo = {
                id: chat.id._serialized,
                name: chat.name,
                participants: metadata.participants ? metadata.participants.length : 'unknown',
                isInCommunity: !!metadata.parentGroupId,
                communityId: metadata.parentGroupId || null
              };
              
              // Try to find community name if it belongs to a community
              if (metadata.parentGroupId) {
                const community = communities.find(c => c.id === metadata.parentGroupId);
                groupInfo.communityName = community ? community.name : 'unknown';
              }
              
              allGroups.push(groupInfo);
            } catch (err) {
              // If we can't get metadata, still include the group with basic info
              allGroups.push({
                id: chat.id._serialized,
                name: chat.name,
                error: err.message,
                isInCommunity: false
              });
              logger.error(`Error getting metadata for group ${chat.name}: ${err.message}`);
            }
          }
        }
        
        return res.status(200).json({
          communities: communities,
          groups: allGroups,
          communityId: whatsappClient.communityId
        });
      } catch (error) {
        logger.error(`Error fetching community info: ${error.message}`);
        return res.status(500).json({ error: error.message });
      }
    });
  }

  start() {
    this.server = this.app.listen(this.port, this.host, () => {
      logger.info(`API server listening on http://${this.host}:${this.port}`);
    });
  }

  stop() {
    if (this.server) {
      this.server.close();
      logger.info('API server stopped');
    }
  }
}

const apiService = new ApiService();
module.exports = apiService;
