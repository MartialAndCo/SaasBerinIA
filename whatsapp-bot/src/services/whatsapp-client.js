const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');
const logger = require('../utils/logger');
const transcriptionService = require('./transcription-service');

class WhatsAppClient {
  constructor() {
    this.client = null;
    this.communityId = null;
    this.initialize();
  }

  initialize() {
    logger.info('Initializing WhatsApp client');
    
    this.client = new Client({
      authStrategy: new LocalAuth({ clientId: 'berinia-bot-new-account' }),
      puppeteer: {
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu', '--disable-dev-shm-usage'],
        headless: true,
        timeout: 120000  // Augmenter le timeout à 2 minutes
      }
    });

    // Register event handlers
    this.registerEventHandlers();
    
    // Start the client
    this.client.initialize();
  }

  registerEventHandlers() {
    // Handle QR code generation
    this.client.on('qr', (qr) => {
      logger.info('QR Code received. Scan it with your WhatsApp mobile app:');
      qrcode.generate(qr, { small: true });
    });

    // Authentication successful
    this.client.on('authenticated', () => {
      logger.info('WhatsApp authentication successful');
    });

    // Handle auth failure
    this.client.on('auth_failure', (msg) => {
      logger.error(`WhatsApp authentication failed: ${msg}`);
    });

    // Ready event
    this.client.on('ready', () => {
      logger.info('WhatsApp client is ready');
      this.identifyCommunity();
    });

    // Système de suivi des messages déjà traités pour éviter les doublons
    this.processedMessages = new Set();
    
    // Handle incoming messages
    this.client.on('message', async (msg) => {
      try {
        // Éviter les doublons en vérifiant si le message a déjà été traité
        if (this.processedMessages.has(msg.id.id)) {
          logger.info(`Ignoring duplicate message with ID: ${msg.id.id}`);
          return;
        }
        
        logger.info(`Message event received - ID: ${msg.id.id}, From: ${msg.from}, Body: ${msg.body.substring(0, 50)}...`);
        
        // Marquer le message comme traité
        this.processedMessages.add(msg.id.id);
        
        // Limiter la taille du Set pour éviter les fuites de mémoire
        if (this.processedMessages.size > 1000) {
          const entriesToDelete = [...this.processedMessages].slice(0, 100);
          entriesToDelete.forEach(entry => this.processedMessages.delete(entry));
        }
        
        await this.handleIncomingMessage(msg);
      } catch (error) {
        logger.error(`Error handling incoming message: ${error.message}`);
      }
    });
    
    // Also handle message_create event (for messages sent from the same account)
    this.client.on('message_create', async (msg) => {
      try {
        // Éviter les doublons en vérifiant si le message a déjà été traité
        if (this.processedMessages.has(msg.id.id)) {
          logger.info(`Ignoring duplicate message with ID: ${msg.id.id}`);
          return;
        }
        
        logger.info(`Message create event received - ID: ${msg.id.id}, From: ${msg.from}, Body: ${msg.body.substring(0, 50)}...`);
        
        // Ignore messages sent by the bot itself to prevent loops
        if (msg.fromMe) {
          logger.info(`Ignoring message sent by me`);
          return;
        }
        
        // Marquer le message comme traité
        this.processedMessages.add(msg.id.id);
        
        await this.handleIncomingMessage(msg);
      } catch (error) {
        logger.error(`Error handling message_create: ${error.message}`);
      }
    });

    // Disconnected
    this.client.on('disconnected', (reason) => {
      logger.warn(`WhatsApp client disconnected: ${reason}`);
      // Attempt to reconnect after a delay
      setTimeout(() => {
        logger.info('Attempting to reconnect WhatsApp client');
        this.client.initialize();
      }, 10000);
    });
  }

  async identifyCommunity() {
    try {
      logger.info('Searching for BerinIA community');
      const chats = await this.client.getChats();
      
      logger.info(`Found ${chats.length} total chats`);
      
      // Log all communities found
      const communities = chats.filter(chat => chat.isCommunity);
      logger.info(`Found ${communities.length} communities: ${communities.map(c => c.name).join(', ')}`);
      
      // Log all groups found
      const groups = chats.filter(chat => chat.isGroup);
      logger.info(`Found ${groups.length} groups: ${groups.map(g => g.name).join(', ')}`);
      
      // First try exact match
      for (const chat of chats) {
        if ((chat.name === 'BerinIA' || chat.name.includes('BerinIA')) && chat.isCommunity) {
          this.communityId = chat.id._serialized;
          logger.info(`Found BerinIA community with ID: ${this.communityId}`);
          return;
        }
      }
      
      // If nothing found, try case-insensitive
      for (const chat of chats) {
        if (chat.name.toLowerCase().includes('berinia') && chat.isCommunity) {
          this.communityId = chat.id._serialized;
          logger.info(`Found BerinIA community using case-insensitive match with ID: ${this.communityId}`);
          return;
        }
      }
      
      // If still not found, check for any community
      if (communities.length > 0) {
        this.communityId = communities[0].id._serialized;
        logger.info(`Using first available community "${communities[0].name}" with ID: ${this.communityId}`);
        return;
      }
      
      logger.warn('No community found. Please create a WhatsApp community named "BerinIA".');
    } catch (error) {
      logger.error(`Failed to identify community: ${error.message}`);
    }
  }

  async handleIncomingMessage(msg) {
    try {
      const chat = await msg.getChat();
      logger.info(`Handling message - Chat type: ${chat.isGroup ? 'Group' : 'Private'}, Name: ${chat.name || 'Direct'}, From: ${msg.author || msg.from}`);
      
      // Vérifier si c'est un message vocal
      let content = msg.body;
      let isVoiceMessage = false;
      
      if (msg.hasMedia && (msg.type === 'audio' || msg.type === 'ptt')) {
        logger.info('Message vocal détecté, téléchargement...');
        try {
          // Télécharger le média
          const media = await msg.downloadMedia();
          logger.info('Message vocal téléchargé, transcription en cours...');
          
          // Transcrire l'audio
          const transcription = await transcriptionService.transcribeAudio(media);
          
          if (transcription.success) {
            content = transcription.text;
            isVoiceMessage = true;
            logger.info(`Transcription réussie: "${content}"`);
          } else {
            logger.error('Échec de transcription:', transcription.error);
          }
        } catch (error) {
          logger.error(`Erreur lors du traitement du message vocal: ${error.message}`);
        }
      }
      
      // Format the message data (process both group and direct messages)
      const messageData = {
        source: 'whatsapp',
        type: chat.isGroup ? 'group' : 'direct',
        group: chat.isGroup ? chat.name : 'Direct Message',
        author: msg.author || msg.from,
        content: content,
        isVoiceMessage: isVoiceMessage,
        timestamp: new Date().toISOString(),
        messageId: msg.id.id
      };

      // Send to BerinIA webhook and get response
      logger.info(`Sending message to webhook: ${JSON.stringify(messageData)}`);
      const webhookResponse = await this.forwardToWebhook(messageData);
      
      // Send response back to user if provided
      if (webhookResponse && webhookResponse.response) {
        logger.info(`Sending webhook response back to chat: ${webhookResponse.response}`);
        await this.sendMessage(msg.from, webhookResponse.response);
      } else {
        logger.warn(`No response received from webhook or response is empty`);
      }
    } catch (error) {
      logger.error(`Error in message handler: ${error.message}`);
    }
  }

  async forwardToWebhook(messageData) {
    try {
      const webhookUrl = process.env.BERINIA_WEBHOOK_URL;
      logger.debug(`Forwarding message to webhook: ${webhookUrl}`, { messageData });

      const response = await axios.post(webhookUrl, messageData);
      logger.info(`Message forwarded to BerinIA webhook. Status: ${response.status}`);
      
      // Log the response data to help with debugging
      logger.debug(`Webhook response data: ${JSON.stringify(response.data)}`);

      return response.data;
    } catch (error) {
      logger.error(`Failed to forward message to webhook: ${error.message}`);
      throw error;
    }
  }

  async sendMessage(chatId, message) {
    try {
      logger.info(`Sending message to ${chatId}`);
      const response = await this.client.sendMessage(chatId, message);
      logger.info('Message sent successfully');
      return response;
    } catch (error) {
      logger.error(`Failed to send message: ${error.message}`);
      throw error;
    }
  }

  async findGroupInCommunity(groupName) {
    try {
      const chats = await this.client.getChats();
      logger.info(`Searching for group "${groupName}" among ${chats.length} chats`);
      
      const groups = chats.filter(chat => chat.isGroup);
      logger.info(`Found ${groups.length} groups: ${groups.map(g => g.name).join(', ')}`);
      
      // Simplified group search without checking for community membership
      // First try exact match
      for (const chat of groups) {
        if (chat.name === groupName) {
          logger.info(`Found group "${groupName}" with exact match`);
          return chat.id._serialized;
        }
      }
      
      // Try includes match
      for (const chat of groups) {
        if (chat.name.includes(groupName) || groupName.includes(chat.name)) {
          logger.info(`Found group "${chat.name}" via partial match for "${groupName}"`);
          return chat.id._serialized;
        }
      }
      
      // Try case-insensitive match
      for (const chat of groups) {
        if (chat.name.toLowerCase().includes(groupName.toLowerCase()) || 
            groupName.toLowerCase().includes(chat.name.toLowerCase())) {
          logger.info(`Found group "${chat.name}" via case-insensitive match for "${groupName}"`);
          return chat.id._serialized;
        }
      }
      
      logger.warn(`Group "${groupName}" not found in any available groups`);
      return null;
    } catch (error) {
      logger.error(`Error finding group: ${error.message}`);
      return null;
    }
  }
}

// Create and export a singleton instance
const whatsappClient = new WhatsAppClient();
module.exports = whatsappClient;
