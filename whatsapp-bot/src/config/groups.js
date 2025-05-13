/**
 * Configuration of WhatsApp community groups
 * Maps logical group names to specific purposes
 */

module.exports = {
  GROUPS: {
    // Official announcements from BerinIA
    ANNOUNCEMENTS: {
      name: 'Annonces officielles',
      readOnly: true,
      description: 'Annonces stratégiques du système BerinIA'
    },
    
    // Performance and statistics
    STATS: {
      name: 'Performances & Stats',
      readOnly: true,
      description: 'Résumés automatiques des performances du système'
    },
    
    // Technical logs
    LOGS: {
      name: 'Logs techniques',
      readOnly: true,
      description: 'Logs automatiques (erreurs, exécution)'
    },
    
    // AI Support and chatbot interactions
    SUPPORT: {
      name: 'Support IA / Chatbot',
      readOnly: false,
      description: 'Questions et retours sur les agents IA'
    },
    
    // Strategic testing and pivots
    STRATEGY: {
      name: 'Tactiques & Tests',
      readOnly: false,
      description: 'Tests stratégiques, pivots, brainstorm'
    },
    
    // Open discussion
    GENERAL: {
      name: 'Discussion libre',
      readOnly: false,
      description: 'Espace libre pour retours et idées'
    }
  },
  
  // Default community name
  COMMUNITY_NAME: 'BerinIA',
  
  // Message types that get forwarded to BerinIA
  PROCESS_MESSAGE_TYPES: ['chat', 'image', 'video', 'document', 'audio']
};
