/**
 * Script pour capturer le code QR de WhatsApp et l'afficher correctement
 * Utilise le client WhatsApp existant mais intercepte le code QR
 */
const fs = require('fs');
const qrcode = require('qrcode');
const { Client, LocalAuth } = require('whatsapp-web.js');
const logger = require('./src/utils/logger');

// Créer une instance temporaire du client WhatsApp
logger.info('Démarrage du service de capture QR...');

// Configuration identique à celle dans whatsapp-client.js pour partager la session
const client = new Client({
  authStrategy: new LocalAuth({ clientId: 'berinia-bot-new-account' }),
  puppeteer: {
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-gpu',
      '--disable-dev-shm-usage',
      '--window-size=1280,800'
    ],
    headless: true,
    timeout: 120000  // Augmenter le timeout à 2 minutes
  }
});

// Variable pour suivre si le QR a été capturé
let qrCaptured = false;

// Intercepter le code QR généré
client.on('qr', async (qrData) => {
  if (qrCaptured) return;
  qrCaptured = true;
  
  logger.info('Code QR capturé!');
  
  try {
    // Générer une image QR de haute qualité
    await qrcode.toFile('/tmp/whatsapp-qr.png', qrData, {
      scale: 15,
      margin: 4,
      color: {
        dark: '#000000',
        light: '#ffffff'
      }
    });
    
    // Afficher les instructions
    console.log('\n\n');
    console.log('='.repeat(80));
    console.log('CODE QR WHATSAPP CAPTURÉ AVEC SUCCÈS');
    console.log('='.repeat(80));
    console.log('\n');
    console.log('Le code QR a été enregistré dans /tmp/whatsapp-qr.png');
    console.log('\nPour scanner le code QR:');
    console.log('1. Ouvrez WhatsApp sur votre téléphone');
    console.log('2. Allez dans Paramètres > Appareils liés > Lier un appareil');
    console.log('3. Utilisez une des méthodes suivantes:');
    console.log('   a. Ouvrez /tmp/whatsapp-qr.png dans un navigateur et scannez-le');
    console.log('   b. Scannez directement le code QR ci-dessous');
    console.log('\n');

    // Générer le QR pour le terminal
    console.log('QR Code à scanner:');
    console.log('\n');
    
    // Utiliser la bibliothèque qrcode pour générer l'ASCII art du QR
    qrcode.toString(qrData, { type: 'terminal', small: true }, function(err, qrAscii) {
      if (err) {
        console.error('Erreur lors de la génération du QR ASCII:', err);
      } else {
        console.log(qrAscii);
      }
      
      console.log('\n');
      console.log('='.repeat(80));
      console.log('Appuyez sur Ctrl+C pour terminer et redémarrer le service WhatsApp');
      console.log('='.repeat(80));
    });
    
  } catch (error) {
    console.error('Erreur lors de la génération du QR:', error);
  }
});

// Gérer l'authentification réussie
client.on('authenticated', () => {
  logger.info('WhatsApp authentifié avec succès!');
  logger.info('Vous pouvez maintenant utiliser le service WhatsApp normalement');
  process.exit(0);
});

// Gérer les erreurs d'authentification
client.on('auth_failure', (msg) => {
  logger.error(`Échec de l'authentification WhatsApp: ${msg}`);
  process.exit(1);
});

// Quitter proprement lorsque l'utilisateur appuie sur Ctrl+C
process.on('SIGINT', () => {
  logger.info('Arrêt du programme de capture QR...');
  process.exit(0);
});

// Initialiser le client WhatsApp
client.initialize();

logger.info('En attente du code QR...');
logger.info('(Le code QR apparaîtra dans quelques secondes)');
