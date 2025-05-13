#!/usr/bin/env node
/**
 * BerinIA WhatsApp Management Utility
 * This script provides utilities to help manage the WhatsApp integration.
 * 
 * Usage:
 *  node manage-whatsapp.js <command> [options]
 *
 * Commands:
 *  list    - List all communities and groups
 *  connect - Connect to WhatsApp and stay running
 *  send    - Send a message to a group
 *  status  - Show the status of the WhatsApp integration
 *  fix     - Fix common configuration issues
 */

const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const fs = require('fs');
const path = require('path');
const axios = require('axios');

// Parse command line arguments
const args = process.argv.slice(2);
const command = args[0] || 'help';

// Show help if requested
if (['help', '-h', '--help'].includes(command)) {
  console.log(`
BerinIA WhatsApp Management Utility

Usage:
  node manage-whatsapp.js <command> [options]

Commands:
  list                       List all communities and groups
  connect                    Connect to WhatsApp and stay running
  send <group> <message>     Send a message to a group
  status                     Show the status of the WhatsApp integration
  fix                        Fix common configuration issues
  
Examples:
  node manage-whatsapp.js list
  node manage-whatsapp.js send "Logs techniques" "Test message"
  node manage-whatsapp.js status
  `);
  process.exit(0);
}

// Function to create a WhatsApp client
function createClient(clientId = 'berinia-manage') {
  const client = new Client({
    authStrategy: new LocalAuth({ clientId }),
    puppeteer: {
      args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu'],
      headless: true
    }
  });

  // Set up event listeners
  client.on('qr', (qr) => {
    console.log('QR Code received. Scan it with your WhatsApp mobile app:');
    qrcode.generate(qr, { small: true });
  });

  client.on('authenticated', () => {
    console.log('WhatsApp authentication successful');
  });

  client.on('auth_failure', (msg) => {
    console.error(`WhatsApp authentication failed: ${msg}`);
    process.exit(1);
  });

  return client;
}

// Command: list - List all communities and groups
async function listCommand() {
  const client = createClient('berinia-list');
  
  client.on('ready', async () => {
    console.log('WhatsApp client is ready');
    
    try {
      // Get all chats
      const chats = await client.getChats();
      console.log(`Found ${chats.length} total chats`);
      
      // Find and list communities
      const communities = chats.filter(chat => chat.isCommunity);
      console.log(`\n=== Communities (${communities.length}) ===`);
      for (const community of communities) {
        console.log(`- "${community.name}" (ID: ${community.id._serialized})`);
        
        // Find and log community groups
        const communityGroups = [];
        for (const group of chats.filter(chat => chat.isGroup)) {
          try {
            const metadata = await client.getGroupMetadata(group.id._serialized);
            if (metadata.parentGroupId === community.id._serialized) {
              communityGroups.push({
                name: group.name,
                id: group.id._serialized,
                participants: metadata.participants.length
              });
            }
          } catch (error) {
            // Ignore errors
          }
        }
        
        if (communityGroups.length > 0) {
          console.log(`  Groups in this community (${communityGroups.length}):`);
          for (const group of communityGroups) {
            console.log(`  - "${group.name}" (${group.participants} members)`);
          }
        } else {
          console.log('  No groups found in this community');
        }
      }
      
      // List standalone groups
      const standaloneGroups = [];
      for (const group of chats.filter(chat => chat.isGroup)) {
        try {
          const metadata = await client.getGroupMetadata(group.id._serialized);
          if (!metadata.parentGroupId) {
            standaloneGroups.push({
              name: group.name,
              id: group.id._serialized,
              participants: metadata.participants.length
            });
          }
        } catch (error) {
          standaloneGroups.push({
            name: group.name,
            id: group.id._serialized,
            participants: 'unknown'
          });
        }
      }
      
      if (standaloneGroups.length > 0) {
        console.log(`\n=== Standalone Groups (${standaloneGroups.length}) ===`);
        for (const group of standaloneGroups) {
          console.log(`- "${group.name}" (${group.participants} members)`);
        }
      }
      
      console.log('\nDone! You can now close this script with Ctrl+C');
    } catch (error) {
      console.error(`Error listing chats: ${error.message}`);
      process.exit(1);
    }
  });
  
  client.initialize();
}

// Command: connect - Connect to WhatsApp and stay running
async function connectCommand() {
  const client = createClient('berinia-bot');
  
  client.on('ready', async () => {
    console.log('WhatsApp client is ready');
    console.log('Connected to WhatsApp. Press Ctrl+C to disconnect.');
  });
  
  client.initialize();
  
  // Keep the script running
  process.on('SIGINT', () => {
    console.log('Shutting down...');
    process.exit(0);
  });
}

// Command: send - Send a message to a group
async function sendCommand(args) {
  if (args.length < 2) {
    console.error('Error: Missing group or message parameter');
    console.log('Usage: node manage-whatsapp.js send "Group Name" "Your message"');
    process.exit(1);
  }

  const groupName = args[0];
  const message = args[1];
  
  try {
    // Try to send via the API first (faster if already running)
    console.log(`Attempting to send message to "${groupName}" via API...`);
    const response = await axios.post('http://localhost:3030/send', {
      group: groupName,
      message: message
    });
    
    console.log('Message sent successfully via API');
    process.exit(0);
  } catch (error) {
    console.log('API not available or returned an error. Falling back to direct client...');
    
    // Fall back to direct client
    const client = createClient('berinia-sender');
    
    client.on('ready', async () => {
      console.log('WhatsApp client is ready');
      
      try {
        // Find the group
        const chats = await client.getChats();
        let targetChat = null;
        let communityId = null;
        
        // First find BerinIA community
        for (const chat of chats) {
          if (chat.isCommunity && (chat.name === 'BerinIA' || chat.name.toLowerCase().includes('berinia'))) {
            communityId = chat.id._serialized;
            console.log(`Found BerinIA community (${chat.name})`);
            break;
          }
        }
        
        // Then find the group
        for (const chat of chats) {
          if (chat.isGroup) {
            if (chat.name === groupName || chat.name.includes(groupName)) {
              try {
                if (communityId) {
                  const metadata = await client.getGroupMetadata(chat.id._serialized);
                  if (metadata.parentGroupId === communityId) {
                    console.log(`Found community group "${chat.name}"`);
                    targetChat = chat;
                    break;
                  }
                } else {
                  console.log(`Found group "${chat.name}" (not in community)`);
                  targetChat = chat;
                  break;
                }
              } catch (err) {
                // Continue searching
              }
            }
          }
        }
        
        if (!targetChat) {
          console.error(`Group "${groupName}" not found`);
          process.exit(1);
        }
        
        // Send the message
        console.log(`Sending message to "${targetChat.name}"...`);
        await client.sendMessage(targetChat.id._serialized, message);
        console.log('Message sent successfully');
        process.exit(0);
      } catch (error) {
        console.error(`Error sending message: ${error.message}`);
        process.exit(1);
      }
    });
    
    client.initialize();
  }
}

// Command: status - Show the status of the WhatsApp integration
async function statusCommand() {
  try {
    console.log('Checking WhatsApp service status...');
    
    // Check systemd service status
    const { exec } = require('child_process');
    exec('systemctl is-active berinia-whatsapp.service', (error, stdout, stderr) => {
      const serviceStatus = stdout.trim();
      console.log(`Service status: ${serviceStatus}`);
      
      // Check API health
      axios.get('http://localhost:3030/health')
        .then(response => {
          console.log(`API health: ${response.data.status}`);
          
          // Check community info
          axios.get('http://localhost:3030/community-info')
            .then(response => {
              console.log(`Community ID: ${response.data.communityId}`);
              console.log(`Groups: ${response.data.groups.length}`);
              
              console.log('\nGroups in community:');
              for (const group of response.data.groups) {
                console.log(`- "${group.name}" (${group.participants} members)`);
              }
              
              console.log('\nStatus: READY');
            })
            .catch(error => {
              if (error.response && error.response.data && error.response.data.error === 'BerinIA community not found') {
                console.log('Community not found. Try restarting the service or checking WhatsApp on your phone.');
                console.log('\nStatus: NOT READY - Community not found');
              } else {
                console.log('Error getting community info:', error.message);
                console.log('\nStatus: NOT READY - API error');
              }
            });
        })
        .catch(error => {
          console.log('API not available:', error.message);
          console.log('\nStatus: NOT READY - API not available');
        });
    });
  } catch (error) {
    console.error('Error checking status:', error.message);
  }
}

// Command: fix - Fix common configuration issues
async function fixCommand() {
  console.log('Running diagnostic checks...');
  
  // Check .env file
  try {
    let envContent = fs.readFileSync(path.join(__dirname, '.env'), 'utf8');
    let updated = false;
    
    // Check API port
    if (!envContent.includes('API_PORT=')) {
      envContent += '\nAPI_PORT=3030';
      updated = true;
    }
    
    // Check API host
    if (!envContent.includes('API_HOST=')) {
      envContent += '\nAPI_HOST=0.0.0.0';
      updated = true;
    }
    
    if (updated) {
      fs.writeFileSync(path.join(__dirname, '.env'), envContent);
      console.log('✅ Updated .env file with missing configuration');
    } else {
      console.log('✅ .env file looks good');
    }
  } catch (error) {
    console.error('❌ Error checking .env file:', error.message);
  }
  
  // Check systemd service
  try {
    const { exec } = require('child_process');
    exec('systemctl status berinia-whatsapp.service', (error, stdout, stderr) => {
      if (error) {
        console.error('❌ Service not properly configured:', error.message);
        console.log('To fix, run: sudo systemctl enable --now berinia-whatsapp.service');
      } else {
        console.log('✅ Service is properly configured');
      }
    });
  } catch (error) {
    console.error('❌ Error checking service:', error.message);
  }
  
  console.log('\nFix completed. You may need to restart the service:');
  console.log('sudo systemctl restart berinia-whatsapp.service');
}

// Execute the requested command
switch (command) {
  case 'list':
    listCommand();
    break;
  case 'connect':
    connectCommand();
    break;
  case 'send':
    sendCommand(args.slice(1));
    break;
  case 'status':
    statusCommand();
    break;
  case 'fix':
    fixCommand();
    break;
  default:
    console.error(`Unknown command: ${command}`);
    console.log('Run with --help for usage information');
    process.exit(1);
}
