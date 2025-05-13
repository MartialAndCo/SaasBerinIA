#!/usr/bin/env node
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');

// Create a WhatsApp client
const client = new Client({
  authStrategy: new LocalAuth({ clientId: 'berinia-list' }),
  puppeteer: {
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu'],
    headless: true
  }
});

// Handle QR code generation
client.on('qr', (qr) => {
  console.log('QR Code received. Scan it with your WhatsApp mobile app:');
  qrcode.generate(qr, { small: true });
});

// Authentication successful
client.on('authenticated', () => {
  console.log('WhatsApp authentication successful');
});

// Handle auth failure
client.on('auth_failure', (msg) => {
  console.error(`WhatsApp authentication failed: ${msg}`);
  process.exit(1);
});

// Once the client is ready, get and list all communities and groups
client.on('ready', async () => {
  console.log('WhatsApp client is ready');
  
  // Get all chats
  const chats = await client.getChats();
  console.log(`Found ${chats.length} total chats`);
  
  // Find and list communities
  const communities = chats.filter(chat => chat.isCommunity);
  console.log(`\n=== Communities (${communities.length}) ===`);
  for (const community of communities) {
    console.log(`- "${community.name}" (ID: ${community.id._serialized})`);
  }
  
  // Find and list groups
  const groups = chats.filter(chat => chat.isGroup);
  console.log(`\n=== Groups (${groups.length}) ===`);
  for (const group of groups) {
    try {
      const metadata = await client.getGroupMetadata(group.id._serialized);
      console.log(`- "${group.name}" (ID: ${group.id._serialized})`);
      console.log(`  Parent: ${metadata.parentGroupId || 'None'}`);
    } catch (error) {
      console.log(`- "${group.name}" (Error getting metadata: ${error.message})`);
    }
  }
  
  console.log('\nDone! You can now close this script with Ctrl+C');
});

// Start the client
client.initialize();
